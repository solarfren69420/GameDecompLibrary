"""Method labels need evidence and remain independent of numerical progress."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from catalog import load_projects, validate
from accept_submission import entry_from_issue
from test_catalog import BODY


class MethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = {p['id']: p for p in load_projects()}

    def test_pseudocode_does_not_become_completion(self):
        entry = self.entries['nicoruedaa--project-arceus']
        self.assertEqual({t['id'] for t in entry['method_tags']}, {'ghidra-pseudocode', 'experimental-port'})
        self.assertIsNone(entry['progress']['decompiled'])
        self.assertIsNone(entry['progress']['linked'])

    def test_matching_and_pseudocode_may_coexist(self):
        tags = {t['id'] for t in self.entries['charlieduzstuf--pokesword']['method_tags']}
        self.assertTrue({'matching-decompilation', 'ghidra-pseudocode', 'generated-code'}.issubset(tags))

    def test_incomplete_matching_project_keeps_its_percentage(self):
        entry = self.entries['khasinski--parasite-eve-decomp']
        self.assertIn('matching-decompilation', {t['id'] for t in entry['method_tags']})
        self.assertEqual(entry['progress']['decompiled'], 96.8)

    def test_missing_unknown_duplicate_or_unsupported_evidence_is_rejected(self):
        original = self.entries['nicoruedaa--project-arceus']
        for field, value in [('source', ''), ('source', 'javascript:alert(1)'), ('note', ''), ('id', '100-percent-complete'), ('checked_at', '2026-02-30')]:
            entry = copy.deepcopy(original)
            entry['method_tags'][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                validate(entry)
        entry = copy.deepcopy(original)
        entry['method_tags'].append(entry['method_tags'][0])
        with self.assertRaises(ValueError):
            validate(entry)

    def test_new_submission_preserves_multiple_scoped_methods(self):
        extra = '\n### Reconstruction methods\n\nMatching decompilation, Ghidra pseudocode\n\n### Method evidence URL\n\nhttps://github.com/example/game#methods\n\n### Method scope\n\nThe workspace exports pseudocode and develops matching source separately.\n'
        entry = entry_from_issue({'body': BODY + extra})
        self.assertEqual({t['id'] for t in entry['method_tags']}, {'matching-decompilation', 'ghidra-pseudocode'})
        self.assertEqual(entry['progress']['decompiled'], 0)
        with self.assertRaises(ValueError):
            entry_from_issue({'body': BODY + '\n### Reconstruction methods\n\nGhidra pseudocode\n'})


if __name__ == '__main__':
    unittest.main()
