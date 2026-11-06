"""Link-set evidence must count only image bytes and refuse unverifiable builds."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from firmware_link_set import (alloc_sections, effective_libc, inspect_build, inspect_image,  # noqa: E402
                               map_inputs, source_license)

MAP = """Archive member included to satisfy reference by file (symbol)

Linker script and memory map

.text           0x40000000       0x20
 .text.used     0x40000000       0x10 esp-idf/a/liba.a(used.c.obj)
 .text.zero     0x40000010        0x0 esp-idf/a/liba.a(zero.c.obj)
 *fill*         0x40000010        0x4 
 .text.a_very_long_name_that_wraps
                0x40000014        0xc /opt/tool/lib/libc.a(libc_x.c.o)
.debug_info     0x00000000      0x100
 .debug_info    0x00000000      0x100 esp-idf/a/liba.a(debugonly.c.obj)
/DISCARD/
 .text.gone     0x00000000       0x40 esp-idf/a/liba.a(gone.c.obj)

Cross Reference Table
"""


def write_elf(path, sections):
    """Write a minimal ELF32 section table; values are (name, flags, size)."""
    names = b'\0' + b''.join(n.encode() + b'\0' for n, _, _ in sections) + b'.shstrtab\0'
    headers, offset = [struct.pack('<10I', *[0] * 10)], 1
    for name, flags, size in sections:
        headers.append(struct.pack('<10I', offset, 1, flags, 0, 0, size, 0, 0, 0, 0))
        offset += len(name) + 1
    headers.append(struct.pack('<10I', offset, 3, 0, 0, 52, len(names), 0, 0, 0, 0))
    shoff = 52 + len(names)
    header = bytearray(52)
    header[:6] = b'\x7fELF\x01\x01'
    struct.pack_into('<I', header, 32, shoff)
    struct.pack_into('<HHH', header, 46, 40, len(headers), len(headers) - 1)
    path.write_bytes(bytes(header) + names + b''.join(headers))


def write_image(firmware, stem, source_text='/* SPDX-License-Identifier: MIT */\n', size=0x20):
    firmware.mkdir(parents=True)
    write_elf(firmware / f'{stem}.elf', [('.text', 2, size), ('.debug_info', 0, 0x100)])
    (firmware / f'{stem}.map').write_text(MAP)
    source = firmware / 'used.c'
    source.write_text(source_text)
    (firmware / 'compile_commands.json').write_text(json.dumps([{
        'directory': str(firmware), 'file': str(source),
        'output': 'esp-idf/a/CMakeFiles/__idf_a.dir/used.c.obj'}]))
    (firmware / 'project_description.json').write_text(json.dumps({'build_components': ['a', 'b', '']}))


class MapTests(unittest.TestCase):
    def test_only_allocated_nonzero_bytes_count(self):
        objects, fill = map_inputs(MAP, {'.text': 0x20})
        self.assertEqual(objects, {'esp-idf/a/liba.a(used.c.obj)': 0x10,
                                   '/opt/tool/lib/libc.a(libc_x.c.o)': 0xc})
        self.assertEqual(fill, 4)

    def test_map_without_memory_map_refused(self):
        with self.assertRaisesRegex(ValueError, 'no memory map'):
            map_inputs('nothing here', {})


class ElfTests(unittest.TestCase):
    def test_only_alloc_sections_returned(self):
        with tempfile.TemporaryDirectory() as d:
            elf = Path(d) / 'x.elf'
            write_elf(elf, [('.text', 2, 16), ('.debug_info', 0, 99)])
            self.assertEqual(alloc_sections(elf), {'.text': 16})

    def test_non_elf_refused(self):
        with tempfile.TemporaryDirectory() as d:
            elf = Path(d) / 'x.elf'
            elf.write_bytes(b'not an elf')
            with self.assertRaisesRegex(ValueError, 'ELF32'):
                alloc_sections(elf)


class LicenseTests(unittest.TestCase):
    def check(self, text, expected):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / 's.c'
            source.write_text(text)
            self.assertEqual(source_license(source), expected)

    def test_every_stated_identifier_is_kept(self):
        self.check('// SPDX-License-Identifier: MIT\n// SPDX-License-Identifier: Apache-2.0\n',
                   'Apache-2.0 + MIT')

    def test_text_without_spdx_is_labelled(self):
        self.check('Permission is hereby granted, free of charge, to any person',
                   'no SPDX; MIT-style permission')

    def test_silence_is_not_a_license(self):
        self.check('int x;\n', 'none stated')


class ImageTests(unittest.TestCase):
    def test_sources_resolved_and_unknown_objects_reported(self):
        with tempfile.TemporaryDirectory() as d:
            firmware = Path(d).resolve() / 'fw'
            write_image(firmware, 'app')
            image = inspect_image(firmware, 'app', Path(d).resolve() / 'sdk')
            self.assertEqual(image['licenses_stated_by_linked_sources']['MIT']['bytes'], 0x10)
            self.assertEqual(image['without_source_evidence'],
                             {'toolchain:libc.a': {'objects': ['libc_x.c.o'], 'bytes': 0xc}})
            self.assertEqual((image['object_bytes'], image['linker_fill_bytes']), (0x1c, 4))
            self.assertNotIn(str(firmware), json.dumps(image['linked_groups']))

    def test_unaccounted_bytes_refused(self):
        with tempfile.TemporaryDirectory() as d:
            firmware = Path(d).resolve() / 'fw'
            write_image(firmware, 'app', size=0x21)
            with self.assertRaisesRegex(ValueError, 'every allocated byte'):
                inspect_image(firmware, 'app', Path(d).resolve() / 'sdk')


class BuildTests(unittest.TestCase):
    def make(self, root, status='pass'):
        sdk = root / 'sdk'
        subprocess.run(['git', 'init', '-q', str(sdk)], check=True)
        subprocess.run(['git', '-C', str(sdk), '-c', 'user.name=t', '-c', 'user.email=t@invalid',
                        'commit', '-q', '--allow-empty', '-m', 'x'], check=True)
        commit = subprocess.check_output(['git', '-C', str(sdk), 'rev-parse', 'HEAD'], text=True).strip()
        build = root / 'build'
        build.mkdir()
        (build / 'results.json').write_text(json.dumps({'status': status}))
        for level in ('O0', 'O2'):
            base = build / level
            write_image(base / 'firmware', 'goose_scalar')
            write_image(base / 'firmware/bootloader', 'bootloader')
            (base / 'sdkconfig').write_text('# CONFIG_LIBC_NEWLIB is not set\nCONFIG_LIBC_PICOLIBC=y\n')
            digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731
            (base / 'run-manifest.json').write_text(json.dumps({
                'optimization': int(level[1]), 'case': 'success', 'configuration': 'control',
                'sdk_commit': commit, 'elf_sha256': digest(base / 'firmware/goose_scalar.elf'),
                'artifacts': {'sdkconfig': digest(base / 'sdkconfig')}}))
        return build, sdk

    def test_passing_build_collected(self):
        with tempfile.TemporaryDirectory() as d:
            build, sdk = self.make(Path(d).resolve())
            levels = inspect_build(build, sdk)
            self.assertEqual(levels['O2']['effective_libc'], 'CONFIG_LIBC_PICOLIBC')
            self.assertEqual(levels['O0']['bootloader']['linked_objects'], 2)

    def test_failed_build_refused(self):
        with tempfile.TemporaryDirectory() as d:
            build, sdk = self.make(Path(d).resolve(), status='failed')
            with self.assertRaisesRegex(ValueError, 'not a passing'):
                inspect_build(build, sdk)

    def test_tampered_elf_refused(self):
        with tempfile.TemporaryDirectory() as d:
            build, sdk = self.make(Path(d).resolve())
            with (build / 'O2/firmware/goose_scalar.elf').open('ab') as f:
                f.write(b'x')
            with self.assertRaisesRegex(ValueError, 'differs from its run manifest'):
                inspect_build(build, sdk)

    def test_dirty_sdk_refused(self):
        with tempfile.TemporaryDirectory() as d:
            build, sdk = self.make(Path(d).resolve())
            (sdk / 'untracked').write_text('x')
            with self.assertRaisesRegex(ValueError, 'local changes'):
                inspect_build(build, sdk)

    def test_ambiguous_libc_refused(self):
        with tempfile.TemporaryDirectory() as d:
            config = Path(d) / 'sdkconfig'
            config.write_text('CONFIG_LIBC_NEWLIB=y\nCONFIG_LIBC_PICOLIBC=y\n')
            with self.assertRaisesRegex(ValueError, 'exactly one'):
                effective_libc(config)

    def test_existing_output_refused(self):
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([sys.executable, str(ROOT / 'tools/firmware_link_set.py'),
                                '--build', '/nonexistent', '--output', d],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
            self.assertIn('must not exist', r.stderr)


if __name__ == '__main__':
    unittest.main()
