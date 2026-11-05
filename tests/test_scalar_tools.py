"""Synthetic saved-file tests. No SDK, downloads, hardware or real telemetry."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import subprocess

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from scalar_config import defaults_inputs, snapshot_defaults, verify_defaults, validate_effective_config, sha256
from validate_scalar_run import validate, read_json


class ScalarRunTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        files = {'sdkconfig': b'CONFIG_IDF_TARGET="esp32s3"\nCONFIG_ESP_MAIN_TASK_STACK_SIZE=3584\nCONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y\n',
                 'firmware/goose_scalar.elf': b'synthetic elf', 'firmware/goose_scalar.bin': b'synthetic image',
                 'firmware/bootloader/bootloader.bin': b'synthetic boot',
                 'firmware/partition_table/partition-table.bin': b'synthetic partitions'}
        for name, content in files.items():
            p = self.root / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(content)
        self.m = {'schema_version': 1, 'kind': 'scalar-v0-build', 'configuration': 'test-control',
                  'optimization': 0, 'main_stack_bytes': 3584,
                  'sdk_commit': 'a' * 40, 'compiler_sha256': 'b' * 64,
                  'artifacts': {p: sha256(self.root / p) for p in files},
                  'elf_sha256': sha256(self.root / 'firmware/goose_scalar.elf')}
        self.lines = [f"goose-embedded identity-v1: elf_sha256={self.m['elf_sha256']}",
                      'goose-embedded scalar-v0: 42',
                      'goose-embedded stack-v1: before=3000 after_goose=2800 after_result_print=2400 bytes',
                      'goose-embedded completed-v1']
        self.c = {'schema_version': 1, 'kind': 'scalar-v0-capture', 'evidence_type': 'synthetic',
                  'configuration': 'test-control', 'optimization': 0, 'log': 'serial.log'}

    def check(self, lines=None, debugger=None):
        (self.root / 'manifest.json').write_text(json.dumps(self.m))
        (self.root / 'serial.log').write_text('\n'.join(self.lines if lines is None else lines) + '\n')
        c = copy.deepcopy(self.c)
        c.update(manifest_sha256=sha256(self.root / 'manifest.json'), log_sha256=sha256(self.root / 'serial.log'))
        if debugger is not None: c['debugger'] = debugger
        (self.root / 'capture.json').write_text(json.dumps(c))
        return validate(self.root / 'manifest.json', self.root / 'capture.json')

    def test_complete_synthetic_capture_is_only_consistent(self):
        r = self.check(); self.assertEqual(r['status'], 'consistent')
        self.assertFalse(r['hardware_execution_proven']); self.assertFalse(r['stack_bound_proven'])
        self.assertIsNone(r['debugger_samples'])

    def test_debugger_complete(self):
        d = dict(before=3000, after_goose=2800, after_result_print=2400, after_report=2300, completed=4)
        self.assertEqual(self.check(debugger=d)['debugger_samples'], d)

    def test_partial_or_wrong_debugger(self):
        d = dict(before=3000, after_goose=2800, after_result_print=2400, after_report=2300, completed=4)
        for key, value in [('completed', 3), ('before', 3001), ('after_report', 2401),
                           ('completed', True), ('after_report', -1)]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.check(debugger={**d, key: value})

    def test_missing_or_duplicate_protocol(self):
        for lines in [self.lines[:-1], self.lines[1:], self.lines + [self.lines[-1]], self.lines * 2]:
            with self.subTest(lines=lines), self.assertRaises(ValueError): self.check(lines)

    def test_order_and_unknown_protocol(self):
        for lines in [[self.lines[0], self.lines[2], self.lines[1], self.lines[3]],
                      self.lines + ['goose-embedded unknown-v1'],
                      ['timestamp: ' + self.lines[0], *self.lines[1:]]]:
            with self.subTest(lines=lines), self.assertRaises(ValueError): self.check(lines)

    def test_wrong_firmware_and_result(self):
        for index, line in [(0, 'goose-embedded identity-v1: elf_sha256=' + '0' * 64),
                            (1, 'goose-embedded scalar-v0: 41')]:
            lines = self.lines.copy(); lines[index] = line
            with self.subTest(index=index), self.assertRaises(ValueError): self.check(lines)

    def test_mismatched_configuration_or_level(self):
        for key, value in [('configuration', 'different'), ('optimization', 2), ('optimization', False)]:
            old = self.c[key]; self.c[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): self.check()
            self.c[key] = old

    def test_missing_evidence_classification(self):
        del self.c['evidence_type']
        with self.assertRaises(ValueError): self.check()

    def test_declared_physical_is_not_authenticated(self):
        self.c['evidence_type'] = 'physical'
        self.assertFalse(self.check()['hardware_execution_proven'])

    def test_stack_values(self):
        for values in ['-1 2800 2400', '4000 2800 2400', '3000 3100 2400', '3000 2800 2900',
                       'NaN 2800 2400', '99999999999999999999999 2800 2400']:
            a, b, c = values.split(); lines = self.lines.copy()
            lines[2] = f'goose-embedded stack-v1: before={a} after_goose={b} after_result_print={c} bytes'
            with self.subTest(values=values), self.assertRaises(ValueError): self.check(lines)

    def test_zero_not_a_safety_certificate(self):
        lines = self.lines.copy()
        lines[2] = 'goose-embedded stack-v1: before=0 after_goose=0 after_result_print=0 bytes'
        r = self.check(lines); self.assertTrue(r['zero_reading_present']); self.assertFalse(r['stack_bound_proven'])

    def test_boot_noise_and_crlf(self):
        lines = ['ESP-ROM:synthetic', 'rst:0x1', 'I (1) main_task: Calling app_main()', *self.lines]
        self.assertEqual(self.check([x + '\r' for x in lines])['status'], 'consistent')

    def test_reset_or_panic_even_after_completion(self):
        for extra in ['ESP-ROM:new', 'rst:0x1', 'Guru Meditation Error', 'abort() was called',
                      "panic'ed", 'Backtrace:', 'CPU halted.', 'Brownout detector was triggered',
                      'Stack smashing protect failure!', 'stack overflow in task main',
                      'assert failed: test', 'Task watchdog got triggered.']:
            with self.subTest(extra=extra), self.assertRaises(ValueError): self.check(self.lines + [extra])

    def test_artifact_tampering(self):
        (self.root / 'firmware/goose_scalar.bin').write_bytes(b'tampered')
        with self.assertRaises(ValueError): self.check()

    def test_capture_hash_tampering(self):
        self.check(); path = self.root / 'capture.json'; c = read_json(path); c['manifest_sha256'] = '0' * 64
        path.write_text(json.dumps(c))
        with self.assertRaises(ValueError): validate(self.root / 'manifest.json', path)
        self.check(); (self.root / 'serial.log').write_text('changed')
        with self.assertRaises(ValueError): validate(self.root / 'manifest.json', path)

    def test_manifest_stack_or_schema_mismatch(self):
        for key, value in [('main_stack_bytes', 4096), ('main_stack_bytes', True), ('schema_version', True),
                           ('elf_sha256', '0' * 64), ('optimization', False)]:
            old = self.m[key]; self.m[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): self.check()
            self.m[key] = old

    def test_manifest_identity_fields(self):
        for key in ['sdk_commit', 'compiler_sha256']:
            old = self.m.pop(key)
            with self.subTest(key=key), self.assertRaises(ValueError): self.check()
            self.m[key] = old

    def test_effective_panic_policy_checked_offline(self):
        p = self.root / 'sdkconfig'; p.write_text(p.read_text() + 'CONFIG_ESP_DEBUG_OCDAWARE=y\n')
        self.m['artifacts']['sdkconfig'] = sha256(p)
        with self.assertRaises(ValueError): self.check()

    def test_log_path_escape(self):
        self.c['log'] = '../outside.log'
        with self.assertRaises(ValueError): self.check()

    def test_symlink_escape(self):
        with tempfile.TemporaryDirectory() as other:
            target = Path(other) / 'image'; target.write_bytes(b'synthetic image')
            p = self.root / 'firmware/goose_scalar.bin'; p.unlink(); p.symlink_to(target)
            with self.assertRaises(ValueError): self.check()

    def test_duplicate_json_keys(self):
        p = self.root / 'duplicate.json'; p.write_text('{"a":1,"a":2}')
        with self.assertRaises(ValueError): read_json(p)

    def test_cli_exit_status(self):
        self.check()
        command = [sys.executable, str(Path(__file__).resolve().parents[1] / 'tools/validate_scalar_run.py'),
                   '--manifest', str(self.root / 'manifest.json'), '--capture', str(self.root / 'capture.json')]
        result = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0); self.assertEqual(json.loads(result.stdout)['status'], 'consistent')
        (self.root / 'serial.log').write_text('tampered')
        result = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(result.returncode, 1); self.assertEqual(json.loads(result.stdout)['status'], 'rejected')

    def test_oversize_log_is_not_truncated(self):
        self.check()
        p = self.root / 'serial.log'; p.write_bytes(b'x' * (16 * 1024 * 1024 + 1))
        c = read_json(self.root / 'capture.json'); c['log_sha256'] = sha256(p)
        (self.root / 'capture.json').write_text(json.dumps(c))
        with self.assertRaisesRegex(ValueError, 'exceeds 16 MiB'):
            validate(self.root / 'manifest.json', self.root / 'capture.json')

    def test_invalid_utf8_log(self):
        self.check()
        p = self.root / 'serial.log'; p.write_bytes(p.read_bytes() + b'\xff')
        c = read_json(self.root / 'capture.json'); c['log_sha256'] = sha256(p)
        (self.root / 'capture.json').write_text(json.dumps(c))
        with self.assertRaises(ValueError): validate(self.root / 'manifest.json', self.root / 'capture.json')


class ConfigInputTests(unittest.TestCase):
    def test_symlink_defaults_target_suffix_uses_supplied_path(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); real = root / 'real'; real.write_text('base')
            link = root / 'link'; link.symlink_to(real)
            Path(str(link) + '.esp32s3').write_text('wanted')
            Path(str(real) + '.esp32s3').write_text('not-selected')
            inputs = defaults_inputs(link, [], 'test-link'); out = root / 'out'; out.mkdir()
            paths = snapshot_defaults(out, inputs)
            self.assertEqual(Path(paths[0] + '.esp32s3').read_text(), 'wanted')
            self.assertFalse(Path(paths[0]).is_symlink())

    def test_snapshot_order_target_suffix_and_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); base = root / 'base'; overlay = root / 'overlay'
            base.write_text('CONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y\n'); overlay.write_text('CONFIG_ESPTOOLPY_FLASHSIZE_4MB=y\n')
            Path(str(overlay) + '.esp32s3').write_text('CONFIG_ESP_MAIN_TASK_STACK_SIZE=4096\n')
            inputs = defaults_inputs(base, [overlay], 'test-4mb'); out = root / 'out'; out.mkdir()
            paths = snapshot_defaults(out, inputs); self.assertEqual(len(paths), 2)
            self.assertTrue(Path(paths[1] + '.esp32s3').is_file()); verify_defaults(out, inputs)
            overlay.write_text('changed')
            with self.assertRaises(ValueError): verify_defaults(out, inputs)

    def test_bad_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp) / 'base'; base.write_text('')
            for overlays, label in [([], '../board'), ([], 'Uppercase'), ([base], 'test'), ([base.parent/'missing'], 'test')]:
                with self.subTest(label=label, overlays=overlays), self.assertRaises(ValueError):
                    defaults_inputs(base, overlays, label)

    def test_effective_policy_rejection(self):
        base = 'CONFIG_IDF_TARGET="esp32s3"\nCONFIG_ESP_SYSTEM_PANIC_PRINT_HALT=y\n'
        validate_effective_config(base)
        for extra in ['CONFIG_ESP_DEBUG_OCDAWARE=y', 'CONFIG_ESP_TRACE_ENABLE=y', 'CONFIG_COMPILER_LTO=y',
                      'CONFIG_ESP_SYSTEM_GDBSTUB_RUNTIME=y', 'CONFIG_ESP_COREDUMP_ENABLE=y']:
            with self.subTest(extra=extra), self.assertRaises(ValueError): validate_effective_config(base + extra)
        with self.assertRaises(ValueError): validate_effective_config(base.replace('esp32s3', 'esp32'))


if __name__ == '__main__': unittest.main()
