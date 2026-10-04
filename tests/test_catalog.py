import json
import os
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from catalog import ROOT, load_projects, validate
from accept_submission import entry_from_issue, main, percentage


BODY = """### Project name

Example game

### Repository URL

https://github.com/example/game

### Project category

Game decompilation

### Platform / target

GameCube, USA 1.0

### What does it do?

Reconstructs a specific original code target.

### Evidence URL

https://github.com/example/game#readme

### Published progress %

0

### Fully linked %

_No response_

### Notes / scope

This is not overall port completion.
"""


class PreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = load_projects()
        cls.by_id = {e["id"]: e for e in cls.entries}

    def test_all_original_repositories_retained(self):
        source = (ROOT / "sources/game-decomp-github-linklist.txt").read_text()
        # Discovery directories are links, not project entries.
        original = set(re.findall(r"^https://(?:github\.com|gitlab\.com)/[^/\s]+/[^/\s]+$", source, re.M))
        discovery = set(json.loads((ROOT / "data/discovery.json").read_text()))
        self.assertTrue((original - discovery).issubset({e["url"] for e in self.entries}))
        self.assertEqual(len(original - discovery), 303)

    def test_precision_and_separate_linked_metric(self):
        self.assertEqual(self.by_id["zeldaret--botw"]["progress"]["decompiled"], 17.489)
        self.assertEqual(self.by_id["ieee802dot11ac--fnv"]["progress"]["linked"], 0.26)

    def test_multiple_game_targets_keep_qualifications(self):
        entry = self.by_id["open-goal--jak-project"]
        self.assertEqual(len(entry["targets"]), 3)
        self.assertIsNone(entry["progress"]["decompiled"])
        self.assertIn("substantial work remains", entry["targets"][0]["progress"]["label"])

    def test_claims_and_function_counts_are_not_matching_byte_metrics(self):
        qualified = [e for e in self.entries if e["progress"]["kind"] in {"claim", "functions"}]
        self.assertTrue(qualified)
        self.assertTrue(all(e["progress"]["decompiled"] is None for e in qualified))

    def test_original_unconfirmed_link_preserved(self):
        entry = self.by_id["skylaralbers--mkd-decomp-local-"]
        self.assertEqual(entry["category"], "unconfirmed")
        self.assertIn("404", entry["notes"][0])


class SubmissionTests(unittest.TestCase):
    def test_zero_is_a_real_published_value(self):
        entry = entry_from_issue({"body": BODY})
        self.assertEqual(entry["progress"]["decompiled"], 0)
        self.assertIsNone(entry["progress"]["linked"])
        self.assertEqual(entry["progress"]["kind"], "reported")

    def test_blank_progress_stays_unknown(self):
        entry = entry_from_issue({"body": BODY.replace("\n0\n", "\n_No response_\n")})
        self.assertIsNone(entry["progress"]["decompiled"])
        self.assertEqual(entry["progress"]["kind"], "unknown")

    def test_invalid_percentages_stop_preparation(self):
        for value in ("101", "-1", "NaN", "100% overall", "50\n### bad"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                percentage(value)

    def test_tools_cannot_claim_game_progress(self):
        with self.assertRaises(ValueError):
            entry_from_issue({"body": BODY.replace("Game decompilation", "Binding or tool")})

    def test_invalid_repository_and_evidence_urls_are_rejected(self):
        for bad in ("javascript:alert(1)", "https://github.com/a/b/../../c", "https://example.com/a/b"):
            with self.subTest(url=bad), self.assertRaises(ValueError):
                entry_from_issue({"body": BODY.replace("https://github.com/example/game\n", bad + "\n")})
        with self.assertRaises(ValueError):
            entry_from_issue({"body": BODY.replace("https://github.com/example/game#readme", "javascript:alert(1)")})

    def test_non_maintainer_cannot_prepare_or_write_a_branch(self):
        env = {"GITHUB_REPOSITORY": "solarfren69420/GameDecompLibrary", "SUBMISSION_ACTOR": "visitor", "ISSUE_NUMBER": "1"}
        with patch.dict(os.environ, env), patch("accept_submission.api", return_value={"permission": "read"}) as mocked:
            with self.assertRaises(PermissionError):
                main()
            self.assertEqual(mocked.call_count, 1)
            self.assertTrue(mocked.call_args.args[0].endswith("/collaborators/visitor/permission"))

    def test_numeric_metric_requires_primary_evidence(self):
        entry = entry_from_issue({"body": BODY})
        entry["sources"] = []
        with self.assertRaises(ValueError):
            validate(entry)

    def test_missing_required_fields_stop_preparation(self):
        with self.assertRaises(ValueError):
            entry_from_issue({"body": "My repo is somewhere"})


if __name__ == "__main__":
    unittest.main()
