#!/usr/bin/env python3
"""Inventory license evidence of pinned Goose, ESP-IDF and the Xtensa toolchain.

Offline and read-only: it never fetches, builds, flashes or modifies inputs.
Text classification only identifies which well-known license text a file
starts with (or "unclassified"); it is not a legal conclusion, a compatibility
clearance or a statement about which files reach a particular binary.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from esp_idf_baseline import PIN, digest, verify_sdk  # noqa: E402

UPSTREAM = ROOT / 'research/upstream.json'
PYTHON_LOCK = ROOT / 'tools/esp-idf-python.lock'
SCALAR_RESULTS = ROOT / 'research/esp32s3-scalar-results.json'
LICENSE_NAME = re.compile(r'^(licen[cs]e|copying|notice|relicensing|unlicense|copyright)',
                          re.IGNORECASE)
SPDX = re.compile(r'SPDX-License-Identifier:[ \t]*([A-Za-z0-9.+()\- ]*[A-Za-z0-9.+)])')
# Ordered: the first matching rule wins. Patterns run on whitespace-normalized text.
RULES = (
    ('Apache-2.0 OR GPL-2.0-or-later', ('dual [apache-2.0]', 'or [gpl-2.0-or-later]')),
    ('GCC-exception-3.1 text', ('gcc runtime library exception',)),
    ('LGPL-2.1 text', ('gnu lesser general public license', 'version 2.1')),
    ('LGPL-3.0 text', ('gnu lesser general public license', 'version 3')),
    ('LGPL-2.0 text', ('gnu library general public license', 'version 2')),
    ('GPL-3.0 text', ('gnu general public license', 'version 3')),
    ('GPL-2.0 text', ('gnu general public license', 'version 2')),
    ('AGPL-3.0 text', ('gnu affero general public license',)),
    ('Apache-2.0 text', ('apache license', 'version 2.0')),
    ('multi-license manifest (Debian copyright format)',
     ('debian.org/doc/packaging-manuals/copyright-format',)),
    ('partial relicensing statement (listed authors only)',
     ('hereby confirm their agreement to relicense',)),
    ('Unlicense text', ('this is free and unencumbered software',)),
    ('MIT-style permission', ('permission is hereby granted, free of charge',)),
    ('BSD-style permission', ('redistribution and use in source and binary forms',)),
    ('ISC-style permission', ('permission to use, copy, modify, and/or distribute',)),
    ('zlib-style permission', ('permission is granted to anyone to use this software',)),
    ('Boost-1.0 text', ('boost software license',)),
)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def classify(data):
    """Name the recognizable license text at the start of data, else unclassified."""
    text = ' '.join(data[:6000].decode('utf-8', 'replace').lower().split())
    for name, needles in RULES:
        if all(n in text for n in needles):
            return name
    return 'unclassified'


def evidence(path=None, data=None):
    data = path.read_bytes() if data is None else data
    return {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data),
            'classification': classify(data)}


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True)


def tracked(repo):
    """Tracked regular files, excluding gitlinks (submodules are inventoried separately)."""
    files = []
    for line in git(repo, 'ls-files', '-s', '-z').split('\0'):
        if line:
            meta, path = line.split('\t', 1)
            if not meta.startswith('160000'):
                files.append(path)
    return files


def license_files(repo, files):
    return {p: evidence(repo / p) for p in sorted(files) if LICENSE_NAME.match(Path(p).name)}


def spdx_census(repo, files, prefix='components/'):
    """Count SPDX expressions per component; record files without an identifier."""
    census = {}
    for p in files:
        if not p.startswith(prefix):
            continue
        component = p[len(prefix):].split('/', 1)[0]
        with open(repo / p, 'rb') as f:
            head = f.read(4096).decode('utf-8', 'replace')
        found = sorted({m.strip() for m in SPDX.findall(head)})
        key = ' + '.join(found) if found else '(none)'
        bucket = census.setdefault(component, {})
        bucket[key] = bucket.get(key, 0) + 1
    return {c: dict(sorted(v.items())) for c, v in sorted(census.items())}


def debian_licenses(text):
    """Summarize a Debian-format copyright file: license name -> file patterns."""
    result, files, in_files = {}, [], False
    for line in text.splitlines():
        if line.startswith('Files:'):
            files, in_files = line[6:].split(), True
        elif in_files and line.startswith((' ', '\t')):
            files.extend(line.split())
        else:
            in_files = False
            if line.startswith('License:'):
                result.setdefault(line[8:].strip(), []).extend(files)
                files = []
    return {k: sorted(set(v)) for k, v in sorted(result.items())}


def inspect_goose(goose, pin):
    require(git(goose, 'rev-parse', 'HEAD').strip() == pin, 'Goose is not at the pinned commit')
    require(not git(goose, 'status', '--porcelain', '--untracked-files=all'),
            'Goose checkout is dirty')
    files = tracked(goose)
    third = sorted({p.split('/')[1] for p in files if p.startswith('third_party/')})
    return {
        'commit': pin, 'license_files': license_files(goose, files),
        'third_party_dirs': third,
        'third_party_readmes': {p: evidence(goose / p) for p in files
                                if re.fullmatch(r'third_party/[^/]+/README(\.md)?', p)},
        'build_sources': {p: evidence(goose / p) for p in ('CMakeLists.txt', 'cmake/libtcc.cmake')},
    }


def inspect_sdk(sdk, pin):
    status = verify_sdk(sdk, pin)
    recorded = json.loads(SCALAR_RESULTS.read_text()).get('submodules', [])
    if recorded:
        require([' '.join(s.split()[:2]) for s in status] == [' '.join(s.split()[:2]) for s in recorded],
                'ESP-IDF submodule commits differ from the recorded scalar build evidence')
    files = tracked(sdk)
    subs = []
    for line in status:
        commit, path = line.split()[:2]
        sub = sdk / path
        root = [p.name for p in sub.iterdir() if p.is_file() and LICENSE_NAME.match(p.name)]
        subs.append({'path': path, 'commit': commit,
                     'root_license_files': {n: evidence(sub / n) for n in sorted(root)}})
    tools = json.loads((sdk / 'tools/tools.json').read_text())['tools']
    declared = []
    for t in tools:
        targets = t.get('supported_targets', [])
        if 'all' in targets or 'esp32s3' in targets:
            rec = [v['name'] for v in t['versions'] if v.get('status') == 'recommended']
            declared.append({'name': t['name'], 'declared_license': t.get('license'),
                             'install': t.get('install'), 'recommended': rec})
    sbom = {p: (sdk / p).read_text() for p in files if re.search(r'(^|/)sbom[^/]*\.yml$', p)}
    return {
        'commit': pin['commit'], 'release': pin['release'],
        'tools_json_sha256': pin['tools_json_sha256'],
        'root_license': evidence(sdk / 'LICENSE'),
        'submodules': subs,
        'in_tree_spdx_by_component': spdx_census(sdk, files),
        'libc_kconfig_sha256': digest(sdk / 'components/esp_libc/Kconfig'),
        'sbom_files': {p: hashlib.sha256(t.encode()).hexdigest() for p, t in sorted(sbom.items())},
        'tools_json_declared_licenses_esp32s3_or_all': declared,
    }


def inspect_toolchain(archive, pin):
    require(digest(archive) == pin['linux_amd64_xtensa_archive_sha256'],
            'toolchain archive differs from the pinned sha256')
    found, picolibc = {}, None
    with tarfile.open(archive, 'r|xz') as tar:
        for m in tar:
            parts = m.name.split('/')
            if not (m.isfile() and len(parts) > 3 and parts[1:3] == ['share', 'licenses']):
                continue
            data = tar.extractfile(m).read()
            rel = '/'.join(parts[3:])
            found[rel] = evidence(None, data)
            if rel == 'picolibc/COPYING.picolibc':
                picolibc = debian_licenses(data.decode('utf-8', 'replace'))
    require(found, 'no share/licenses members found in toolchain archive')
    restrictive = {k: v for k, v in (picolibc or {}).items()
                   if re.match(r'(A?GPL|LGPL)', k)}
    return {
        'archive_sha256': pin['linux_amd64_xtensa_archive_sha256'],
        'version': pin['xtensa_toolchain'],
        'license_packages': sorted({k.split('/')[0] for k in found}),
        'license_files': dict(sorted(found.items())),
        'picolibc_license_stanza_count': len(picolibc or {}),
        'picolibc_copyleft_stanzas': restrictive,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--goose', type=Path, default=ROOT / '.cache/goose')
    p.add_argument('--sdk', type=Path, default=ROOT / '.cache/esp-idf-v6.0.2')
    p.add_argument('--toolchain-archive', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if out.exists():
        p.error('--output must not exist; use a fresh path to preserve evidence')
    pin = json.loads(PIN.read_text())
    goose_pin = json.loads(UPSTREAM.read_text())['goose']['commit']
    try:
        result = {
            'status': 'inventory-collected',
            'scope': 'license text evidence only; no legal conclusion or binary membership claim',
            'goose': inspect_goose(a.goose.resolve(), goose_pin),
            'esp_idf': inspect_sdk(a.sdk.resolve(), pin),
            'xtensa_toolchain': inspect_toolchain(a.toolchain_archive.resolve(), pin),
            'python_lock': {'sha256': digest(PYTHON_LOCK),
                            'packages': sum(1 for l in PYTHON_LOCK.read_text().splitlines()
                                            if '==' in l),
                            'licenses': 'not inspected'},
            'project_upstream_notices': {
                'patches/goose/LICENSE.upstream': evidence(ROOT / 'patches/goose/LICENSE.upstream')},
        }
    except (ValueError, RuntimeError, subprocess.CalledProcessError, OSError) as e:
        print(f'license inventory refused: {e}', file=sys.stderr)
        return 1
    out.mkdir(parents=True)
    (out / 'results.json').write_text(json.dumps(result, indent=1, sort_keys=True) + '\n')
    unclassified = sorted(
        [f'goose:{k}' for k, v in result['goose']['license_files'].items()
         if v['classification'] == 'unclassified'] +
        [f"{s['path']}/{n}" for s in result['esp_idf']['submodules']
         for n, v in s['root_license_files'].items() if v['classification'] == 'unclassified'])
    print(json.dumps({'output': str(out / 'results.json'),
                      'submodules': len(result['esp_idf']['submodules']),
                      'toolchain_license_files': len(result['xtensa_toolchain']['license_files']),
                      'unclassified_needing_review': unclassified}, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
