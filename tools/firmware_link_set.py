#!/usr/bin/env python3
"""List which objects reach a scalar firmware image and what licenses their sources state.

Offline and read-only: it never builds, flashes or modifies inputs. An object
counts only when the linker map gives it nonzero bytes in an ELF section with
SHF_ALLOC, so garbage-collected and debug-only members do not count. Source
licenses are the SPDX identifiers the source file states. Inline code from
headers, prebuilt archives and ROM code are not attributed to a license. This
is notice evidence, not a legal conclusion, and no execution claim.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from license_inventory import SPDX, classify, git  # noqa: E402

LEVELS = ('O0', 'O2')
SHF_ALLOC = 2
INPUT = re.compile(r'^\s+(?:(\S+)\s+)?0x([0-9a-f]+)\s+0x([0-9a-f]+)\s+(\S.*?)\s*$')
FILL = re.compile(r'^\s+\*fill\*\s+0x[0-9a-f]+\s+0x([0-9a-f]+)')
OUTPUT_SECTION = re.compile(r'^([^\s*][^\s]*)(?:\s|$)')
MEMBER = re.compile(r'^(.*)\(([^()]+)\)$')
LIBC_CONFIG = re.compile(r'^(?:# )?(CONFIG_LIBC_(?:PICOLIBC|NEWLIB))(=y| is not set)$', re.M)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def alloc_sections(elf):
    """Map SHF_ALLOC section names to sizes from a little-endian ELF32 file."""
    data = elf.read_bytes()
    require(data[:6] == b'\x7fELF\x01\x01', f'{elf} is not a little-endian ELF32 file')
    shoff = struct.unpack_from('<I', data, 32)[0]
    shentsize, shnum, shstrndx = struct.unpack_from('<HHH', data, 46)
    require(shentsize == 40 and 0 < shnum and shstrndx < shnum, f'{elf} has no usable section table')
    headers = [struct.unpack_from('<10I', data, shoff + i * shentsize) for i in range(shnum)]
    strings = data[headers[shstrndx][4]:headers[shstrndx][4] + headers[shstrndx][5]]
    sections = {}
    for h in headers:
        if h[2] & SHF_ALLOC:
            name = strings[h[0]:strings.index(b'\0', h[0])].decode()
            sections[name] = h[5]
    return sections


def map_inputs(text, sections):
    """Sum input bytes per object and linker fill, counting only the given output sections."""
    marker = 'Linker script and memory map'
    require(marker in text, 'map has no memory map section')
    body = text.split(marker, 1)[1].split('Cross Reference Table', 1)[0]
    objects, fill, current = {}, 0, None
    for line in body.splitlines():
        if not line.startswith(' '):
            m = OUTPUT_SECTION.match(line)
            if m:
                current = m.group(1)
            continue
        m = INPUT.match(line)
        if current not in sections:
            continue
        if FILL.match(line):
            fill += int(FILL.match(line).group(1), 16)
        elif m and int(m.group(3), 16):
            objects[m.group(4)] = objects.get(m.group(4), 0) + int(m.group(3), 16)
    return objects, fill


def object_key(path):
    """Normalize an object or object-in-archive map name to (group directory, basename)."""
    m = MEMBER.match(path)
    if m:
        return str(Path(m.group(1)).parent), m.group(2)
    return str(Path(path).parent), Path(path).name


def compile_index(firmware):
    """Map (component directory, object basename) to candidate source paths."""
    index = {}
    for entry in json.loads((firmware / 'compile_commands.json').read_text()):
        output = (Path(entry['directory']) / entry['output']).resolve()
        rel = output.relative_to(firmware.resolve()).as_posix()
        group = rel.split('/CMakeFiles/', 1)[0] if '/CMakeFiles/' in rel else '.'
        if rel.startswith('CMakeFiles/'):
            group = 'CMakeFiles/' + rel.split('/')[1]
        index.setdefault((group, output.name), []).append(Path(entry['file']))
    return index


def source_origin(source, firmware, sdk):
    source = source.resolve()
    for label, base in (('esp-idf', sdk), ('generated', firmware), ('project', ROOT)):
        if source.is_relative_to(base):
            return f'{label}:{source.relative_to(base).as_posix()}'
    return f'external:{source}'


def source_license(source):
    data = source.read_bytes()
    stated = sorted({m.strip() for m in SPDX.findall(data[:4096].decode('utf-8', 'replace'))})
    if stated:
        return ' + '.join(stated)
    kind = classify(data)
    return 'none stated' if kind == 'unclassified' else f'no SPDX; {kind}'


def object_origin(path, firmware, sdk):
    """Name where an object without compile evidence came from, by its link path."""
    m = MEMBER.match(path)
    target = Path(m.group(1) if m else path)
    resolved = (firmware / target).resolve()
    if resolved.is_relative_to(sdk):
        return f'esp-idf prebuilt:{resolved.relative_to(sdk).as_posix()}'
    if resolved.is_relative_to(firmware.resolve()):
        return f'build product:{resolved.relative_to(firmware.resolve()).as_posix()}'
    return f'toolchain:{resolved.name}'


def inspect_image(firmware, stem, sdk):
    elf, map_path = firmware / f'{stem}.elf', firmware / f'{stem}.map'
    for path in (elf, map_path, firmware / 'compile_commands.json', firmware / 'project_description.json'):
        require(path.is_file(), f'missing {path}')
    sections = alloc_sections(elf)
    objects, fill = map_inputs(map_path.read_text(), sections)
    require(objects, f'{map_path} attributes no bytes to allocated sections')
    require(sum(objects.values()) + fill == sum(sections.values()),
            f'{map_path} does not account for every allocated byte of {elf}')
    index = compile_index(firmware)
    linked, licenses, unattributed = [], {}, {}
    for name, size in sorted(objects.items()):
        sources = index.get(object_key(name), [])
        record = {'object': name, 'bytes': size}
        if sources:
            record['sources'] = [{'path': source_origin(s, firmware, sdk), 'license': source_license(s)}
                                 for s in sources]
            for key in sorted({s['license'] for s in record['sources']}):
                item = licenses.setdefault(key, {'objects': 0, 'bytes': 0, 'sources': set()})
                item['objects'] += 1
                item['bytes'] += size
                item['sources'].update(s['path'] for s in record['sources'] if s['license'] == key)
        else:
            origin = object_origin(name, firmware, sdk)
            record['origin'] = origin
            item = unattributed.setdefault(origin, {'objects': [], 'bytes': 0})
            item['objects'].append(MEMBER.match(name).group(2) if MEMBER.match(name) else Path(name).name)
            item['bytes'] += size
        linked.append(record)
    description = json.loads((firmware / 'project_description.json').read_text())
    groups = {}
    for record in linked:
        group, _ = object_key(record['object'])
        group = group if not Path(group).is_absolute() else record['origin']
        groups[group] = groups.get(group, 0) + record['bytes']
    return {
        'elf_sha256': sha256(elf), 'map_sha256': sha256(map_path),
        'allocated_bytes': sum(sections.values()), 'object_bytes': sum(objects.values()),
        'linker_fill_bytes': fill,
        'linked_objects': len(linked),
        'declared_build_components': sorted(c for c in description['build_components'] if c),
        'linked_groups': dict(sorted(groups.items())),
        'licenses_stated_by_linked_sources': {
            k: {'objects': v['objects'], 'bytes': v['bytes'], 'sources': sorted(v['sources'])}
            for k, v in sorted(licenses.items())},
        'without_source_evidence': dict(sorted(unattributed.items())),
    }


def effective_libc(sdkconfig):
    found = {name: value == '=y' for name, value in LIBC_CONFIG.findall(sdkconfig.read_text())}
    require(sum(found.values()) == 1, f'{sdkconfig} does not select exactly one known libc')
    return next(name for name, selected in found.items() if selected)


def inspect_build(build, sdk):
    results = json.loads((build / 'results.json').read_text())
    require(results.get('status') == 'pass', f'{build} is not a passing scalar build')
    require(not git(sdk, 'status', '--porcelain').strip(), f'{sdk} has local changes')
    levels = {}
    for level in LEVELS:
        base = build / level
        manifest = json.loads((base / 'run-manifest.json').read_text())
        firmware = base / 'firmware'
        require(git(sdk, 'rev-parse', 'HEAD').strip() == manifest['sdk_commit'],
                f'{sdk} is not the commit {level} was built from')
        require(sha256(firmware / 'goose_scalar.elf') == manifest['elf_sha256'],
                f'{level} ELF differs from its run manifest')
        require(sha256(base / 'sdkconfig') == manifest['artifacts']['sdkconfig'],
                f'{level} sdkconfig differs from its run manifest')
        levels[level] = {
            'optimization': manifest['optimization'], 'case': manifest['case'],
            'configuration': manifest['configuration'], 'sdk_commit': manifest['sdk_commit'],
            'effective_libc': effective_libc(base / 'sdkconfig'),
            'application': inspect_image(firmware, 'goose_scalar', sdk),
            'bootloader': inspect_image(firmware / 'bootloader', 'bootloader', sdk),
        }
    return levels


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True, help='passing test_esp_idf_scalar.py output')
    p.add_argument('--sdk', type=Path, default=ROOT / '.cache/esp-idf-v6.0.2')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if out.exists():
        p.error('--output must not exist; use a fresh path to preserve evidence')
    try:
        levels = inspect_build(a.build.resolve(), a.sdk.resolve())
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as e:
        print(f'firmware link set refused: {e}', file=sys.stderr)
        return 1
    result = {'status': 'link-set-collected',
              'scope': 'linked-object and stated-license evidence; no legal conclusion, no execution claim',
              'levels': levels}
    out.mkdir(parents=True)
    (out / 'results.json').write_text(json.dumps(result, indent=1, sort_keys=True) + '\n')
    print(json.dumps({'output': str(out / 'results.json'), 'levels': {
        level: {image: {'objects': data[image]['linked_objects'],
                        'licenses': sorted(data[image]['licenses_stated_by_linked_sources']),
                        'without_source_evidence': sorted(data[image]['without_source_evidence'])}
                for image in ('application', 'bootloader')}
        for level, data in levels.items()}}, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
