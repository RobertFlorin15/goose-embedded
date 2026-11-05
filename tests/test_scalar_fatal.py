"""Fatal-log rejection tests use synthetic files only; no SDK/device required."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_scalar_tools as fixtures
from scalar_config import sha256
from validate_scalar_run import validate as normal
from validate_scalar_fatal import validate, MESSAGES


class FatalTests(unittest.TestCase):
    def setUp(self):
        fixture = fixtures.ScalarRunTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.root, self.m, self.c = fixture.root, fixture.m, fixture.c
        self.set_case('overflow')

    def set_case(self, case):
        self.m['case'] = self.c['case'] = case
        self.lines = [f"goose-embedded identity-v1: elf_sha256={self.m['elf_sha256']}",
                      f'goose-embedded case-v1: {case}', MESSAGES[case],
                      'Backtrace: synthetic placeholder', 'CPU halted.']

    def write(self, lines=None):
        (self.root / 'manifest.json').write_text(json.dumps(self.m))
        (self.root / 'serial.log').write_text('\n'.join(self.lines if lines is None else lines) + '\n')
        self.c.update(manifest_sha256=sha256(self.root / 'manifest.json'), log_sha256=sha256(self.root / 'serial.log'))
        (self.root / 'capture.json').write_text(json.dumps(self.c))
        return self.root / 'manifest.json', self.root / 'capture.json'

    def test_both_cases_consistent_only(self):
        for case in MESSAGES:
            self.set_case(case)
            r = validate(*self.write())
            self.assertEqual(r['case'], case)
            for key in ('hardware_execution_proven', 'halt_proven', 'stack_bound_proven'):
                self.assertFalse(r[key])

    def test_normal_validator_rejects_fatal_build(self):
        with self.assertRaises(ValueError): normal(*self.write())

    def test_fatal_validator_rejects_success_build(self):
        self.m['case'] = self.c['case'] = 'success'
        with self.assertRaises(ValueError): validate(*self.write())

    def test_explicit_case_required_and_matched(self):
        for value in ('cold-export', 'success', '', None, [], 1):
            self.c['case'] = value
            with self.subTest(value=value), self.assertRaises(ValueError): validate(*self.write())
        del self.c['case']
        with self.assertRaises(ValueError): validate(*self.write())
        del self.m['case']
        with self.assertRaises(ValueError): validate(*self.write())

    def test_missing_duplicate_wrong_order_or_details(self):
        variants = [self.lines[:i] + self.lines[i+1:] for i in (0, 1, 2, 4)]
        variants += [self.lines + [self.lines[i]] for i in (0, 1, 2, 4)]
        variants += [[self.lines[0], self.lines[2], self.lines[1], *self.lines[3:]],
                     [self.lines[0], self.lines[1], self.lines[4], self.lines[2]],
                     [*self.lines[:2], MESSAGES['cold-export'], *self.lines[3:]],
                     [self.lines[0], 'goose-embedded case-v1: cold-export', *self.lines[2:]]]
        for lines in variants:
            with self.subTest(lines=lines), self.assertRaises(ValueError): validate(*self.write(lines))

    def test_unrelated_faults_resets_and_normal_telemetry(self):
        for cue in ('Guru Meditation Error', "Core panic'ed", 'abort() was called', 'Brownout detector',
                    'stack canary', 'Stack smashing', 'stack overflow', 'assert failed:', 'Task watchdog',
                    'Rebooting...', 'fatal case unexpectedly returned', 'invalid initialization arguments',
                    'unreachable scalar code', 'rst:0x1', 'ESP-ROM:second',
                    'goose-embedded scalar-v0: 42', 'goose-embedded completed-v1'):
            with self.subTest(cue=cue), self.assertRaises(ValueError):
                validate(*self.write([*self.lines[:3], cue, *self.lines[3:]]))

    def test_backtrace_before_expected_failure(self):
        with self.assertRaises(ValueError):
            validate(*self.write(['Backtrace: earlier failure', *self.lines]))

    def test_no_content_after_halt(self):
        with self.assertRaises(ValueError): validate(*self.write([*self.lines, 'continued']))

    def test_identity_and_artifact_tamper(self):
        lines = self.lines.copy(); lines[0] = 'goose-embedded identity-v1: elf_sha256=' + '0' * 64
        with self.assertRaises(ValueError): validate(*self.write(lines))
        paths = self.write(); (self.root / 'firmware/goose_scalar.elf').write_bytes(b'changed')
        with self.assertRaises(ValueError): validate(*paths)

    def test_debugger_normal_record_rejected(self):
        self.c['debugger'] = {'completed': 1}
        with self.assertRaises(ValueError): validate(*self.write())

    def test_boot_crlf_and_declared_physical_not_proof(self):
        self.c['evidence_type'] = 'physical'
        r = validate(*self.write(['ESP-ROM:synthetic', 'rst:0x1', *[x+'\r' for x in self.lines]]))
        self.assertFalse(r['hardware_execution_proven']); self.assertFalse(r['halt_proven'])

    def test_cli_exit_codes(self):
        manifest, capture = self.write()
        command = [sys.executable, str(Path(__file__).resolve().parents[1] / 'tools/validate_scalar_fatal.py'),
                   '--manifest', str(manifest), '--capture', str(capture)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0); self.assertEqual(json.loads(result.stdout)['status'], 'consistent')
        self.write(self.lines[:-1])
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1); self.assertEqual(json.loads(result.stdout)['status'], 'rejected')
