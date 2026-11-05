"""Disassembly extraction must preserve unknown frames and symbol boundaries."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from audit_scalar_fatal import inspect


class AuditTests(unittest.TestCase):
    def test_frame_and_calls(self):
        text = ('00000010 <example>:\n'
                '  10: 004136 entry a1, 32\n'
                '  13: 000005 call8 80 <callee>\n'
                '  16: 0008e0 callx8 a8\n'
                '  19: 000046 j 19 <example+0x9>\n')
        r = inspect(text, 'example')
        self.assertEqual(r['entry_frame_bytes'], 32)
        self.assertEqual(r['direct_calls'], ['callee'])
        self.assertEqual(r['indirect_call_count'], 1)

    def test_assembly_without_entry_is_unknown(self):
        r = inspect('00000010 <assembly>:\n  10: 000000 ill\n', 'assembly')
        self.assertIsNone(r['entry_frame_bytes'])

    def test_do_not_consume_next_symbol(self):
        text = ('00000010 <assembly>:\n  10: 000000 ill\n\n'
                '00000020 <next>:\n  20: 004136 entry a1, 32\n')
        self.assertIsNone(inspect(text, 'assembly')['entry_frame_bytes'])

    def test_absent_or_offset_label_is_not_function(self):
        for text in ('', '00000010 <example+0x4>:\n 10: 004136 entry a1, 32\n'):
            with self.subTest(text=text), self.assertRaises(ValueError): inspect(text, 'example')

    def test_multiple_entries_need_manual_review(self):
        text = '00000010 <example>:\n 10: 004136 entry a1, 32\n 20: 004136 entry a1, 48\n'
        with self.assertRaises(ValueError): inspect(text, 'example')
