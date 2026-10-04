"""Regression checks for the dated audit artifact, not claims about future edits."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AuditArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / 'sources/audit-results.json').read_text())
        cls.projects = cls.report['projects']

    def test_every_original_entry_was_audited(self):
        self.assertEqual(len(self.projects), 303)
        self.assertEqual(len({p['id'] for p in self.projects}), 303)
        self.assertEqual(sum(p['repository']['status'] == 404 for p in self.projects), 1)
        self.assertTrue(all(source['status'] == 200 for p in self.projects for source in p['sources']))

    def test_tracker_numbers_and_commits_match_two_pinned_representations(self):
        trackers = [p for p in self.projects if 'second_representation' in p['metric']]
        self.assertEqual(len(trackers), 202)
        for project in trackers:
            metric = project['metric']
            actual, precise = metric['observed'], metric['second_representation']
            with self.subTest(id=project['id']):
                self.assertEqual(metric['status'], 'confirmed')
                self.assertEqual(precise['status'], 'consistent')
                self.assertLessEqual(abs(actual['decompiled'] - precise['matched_code_percent']), 0.00501)
                if actual['linked'] is not None:
                    self.assertLessEqual(abs(actual['linked'] - precise['complete_code_percent']), 0.00501)
                self.assertEqual(actual['report_commit'], precise['report_commit'])
                self.assertTrue(actual['url'].endswith(actual['report_commit'].split('/')[-1]))
                self.assertTrue(precise['report_date'])

    def test_claims_and_function_counts_remain_non_numeric(self):
        for project in self.projects:
            if project['metric']['status'] in ('qualified-maintainer-claim', 'confirmed-function-count'):
                self.assertIsNone(project['catalog_snapshot']['progress']['decompiled'])
                self.assertIsNone(project['catalog_snapshot']['progress']['linked'])

    def test_tools_and_related_projects_do_not_claim_game_percentages(self):
        for project in self.projects:
            snapshot = project['catalog_snapshot']
            if snapshot['category'] in ('tool', 'related'):
                self.assertIsNone(snapshot['progress']['decompiled'])
                self.assertIsNone(snapshot['progress']['linked'])

    def test_no_unreviewed_numeric_or_claim_records_left(self):
        self.assertFalse(any(p['metric']['status'] in ('needs-review', 'manual-review-required') for p in self.projects))

    def test_refresh_counts_do_not_count_display_only_edits(self):
        changes = self.report['changes']
        self.assertEqual(len(changes), 12)
        numeric = sum(c['before']['progress']['decompiled'] != c['after']['progress']['decompiled']
                      or c['before']['progress']['linked'] != c['after']['progress']['linked'] for c in changes)
        self.assertEqual(numeric, 7)


if __name__ == '__main__':
    unittest.main()
