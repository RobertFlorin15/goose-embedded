"""License inventory helpers must classify conservatively and refuse unpinned inputs."""
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from license_inventory import classify, debian_licenses, spdx_census, inspect_goose  # noqa: E402


class ClassifyTests(unittest.TestCase):
    def test_known_texts(self):
        self.assertEqual(classify(b'  Apache License\n  Version 2.0, January 2004'), 'Apache-2.0 text')
        self.assertEqual(classify(b'GNU LESSER GENERAL PUBLIC LICENSE\n Version 2.1, February'),
                         'LGPL-2.1 text')
        self.assertEqual(classify(b'GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007'),
                         'GPL-3.0 text')
        self.assertEqual(classify(b'GCC RUNTIME LIBRARY EXCEPTION\nVersion 3.1'),
                         'GCC-exception-3.1 text')

    def test_dual_license_is_not_reduced_to_one_side(self):
        text = (b'Mbed TLS files are provided under a dual [Apache-2.0](x) '
                b'OR [GPL-2.0-or-later](y) license.')
        self.assertEqual(classify(text), 'Apache-2.0 OR GPL-2.0-or-later')

    def test_partial_relicensing_is_not_called_mit(self):
        text = (b'The authors listed below hereby confirm their agreement to relicense\n'
                b'Permission is hereby granted, free of charge, to any person')
        self.assertEqual(classify(text), 'partial relicensing statement (listed authors only)')

    def test_unknown_text_needs_review(self):
        self.assertEqual(classify(b'This product includes software developed at Example.'),
                         'unclassified')
        self.assertEqual(classify(b''), 'unclassified')


class ParserTests(unittest.TestCase):
    def test_debian_continuation_lines(self):
        text = ('Files: a.c\n b.c\nCopyright: 2020 X\nLicense: BSD3-1\n\n'
                'Files: test/t.c\nCopyright: Y\nLicense: GPL2-1\n text of license\n'
                'License: BSD3-1\n body\n')
        self.assertEqual(debian_licenses(text), {'BSD3-1': ['a.c', 'b.c'], 'GPL2-1': ['test/t.c']})

    def test_spdx_census_counts_missing_identifiers(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'components/a').mkdir(parents=True)
            (root / 'components/a/x.c').write_text('/* SPDX-License-Identifier: MIT */\n')
            (root / 'components/a/y.c').write_text('# SPDX-License-Identifier: Apache-2.0 OR MIT\n')
            (root / 'components/a/z.txt').write_text('no identifier\n')
            (root / 'other.c').write_text('/* SPDX-License-Identifier: GPL-2.0 */\n')
            files = ['components/a/x.c', 'components/a/y.c', 'components/a/z.txt', 'other.c']
            self.assertEqual(spdx_census(root, files),
                             {'a': {'(none)': 1, 'Apache-2.0 OR MIT': 1, 'MIT': 1}})


class RefusalTests(unittest.TestCase):
    def test_wrong_goose_pin_refused(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(['git', 'init', '-q', d], check=True)
            subprocess.run(['git', '-C', d, '-c', 'user.name=t', '-c', 'user.email=t@invalid',
                            'commit', '-q', '--allow-empty', '-m', 'x'], check=True)
            with self.assertRaisesRegex(ValueError, 'pinned commit'):
                inspect_goose(Path(d), '0' * 40)

    def test_existing_output_refused(self):
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([sys.executable, str(ROOT / 'tools/license_inventory.py'),
                                '--toolchain-archive', '/nonexistent', '--output', d],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
            self.assertIn('must not exist', r.stderr)


if __name__ == '__main__':
    unittest.main()
