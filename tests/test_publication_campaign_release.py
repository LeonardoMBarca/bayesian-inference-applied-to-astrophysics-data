"""Campaign denominators and public-release blocking are separate contracts."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from publication.campaign_release import (
    audit_campaign_rows,
    validate_campaign_release,
    validate_synthesis,
)


class CampaignReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.job = {"job_id": "a", "experiment_id": "PUB-02", "scenario_id": "near_limit",
                    "replicate_id": "rep_0", "seeds": {"generation": 42, "inference": 18}}
        self.campaign = {"campaign_id": "fixture", "frozen_declaration": "plan.json", "execution_state": "state.json",
                         "final_report": "reports/summary.json", "declared_job_counts": {"PUB-02": 1}}
        self.registry = {"campaign_registries": [self.campaign]}
        self.attempt = {"job_id": "a", "attempt_index": 0, "status": "FAILED_TECHNICAL", "output_dir": "run"}
        self.summary = {"campaign_id": "fixture", "jobs": [self.job | {"status": "FAILED_TECHNICAL"}],
                        "attempts": [self.attempt], "declared_jobs": 1, "total_attempts": 1,
                        "complete_declared_batch": True, "status_counts": {"FAILED_TECHNICAL": 1}}
        self.put("plan.json", {"declared_jobs": [self.job]})
        self.put("state.json", {"jobs": {"a": {"status": "FAILED_TECHNICAL", "attempts": [self.attempt]}}})
        self.put("reports/campaign_summary.json", self.summary)
        self.put("publication/registry.json", self.registry)

    def put(self, name, payload):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_preserved_technical_failure_not_omitted_from_counts(self):
        result = audit_campaign_rows(self.root, self.registry)
        self.assertEqual(result[0]["declared_jobs"], 1)
        self.assertEqual(result[0]["preserved_attempts"], 1)
        self.assertEqual(result[0]["status_counts"], {"FAILED_TECHNICAL": 1})

    def test_omitted_job_changed_seed_and_missing_attempt_rejected(self):
        for mutation in ("jobs", "seed", "attempts"):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(self.summary)
                if mutation == "jobs":
                    changed["jobs"] = []
                elif mutation == "seed":
                    changed["jobs"][0]["seeds"]["inference"] += 1
                else:
                    changed["attempts"] = []
                    changed["total_attempts"] = 0
                self.put("reports/campaign_summary.json", changed)
                with self.assertRaises(ValueError):
                    audit_campaign_rows(self.root, self.registry)

    def test_successful_completion_requires_seal_scientific_rejection_too(self):
        for status in ("COMPLETED", "COMPLETED_REJECTED"):
            self.summary["jobs"][0]["status"] = status
            self.summary["attempts"][0]["status"] = status
            self.summary["status_counts"] = {status: 1}
            self.put("reports/campaign_summary.json", self.summary)
            self.put("state.json", {"jobs": {"a": {"status": status, "attempts": [self.attempt]}}})
            with self.assertRaisesRegex(ValueError, "no sealed completion"):
                audit_campaign_rows(self.root, self.registry)

    def test_legitimate_block_is_exit_one_not_arbitrary_failure(self):
        self.put("inventory.json", {"fixture": True})
        with patch("publication.campaign_release.verify_inventory", return_value={"status": "passed"}), \
             patch("publication.campaign_release.validate_synthesis", return_value={"claim_count": 1}):
            report = validate_campaign_release(self.root, inventory_path="inventory.json", synthesis="synthesis")
        self.assertEqual(report["status"], "blocked_public_release")
        self.assertEqual(report["integrity_status"], "passed")
        self.assertEqual(report["exit_code"], 1)
        self.assertEqual(len(report["public_release_blockers"]), 7)
        self.assertEqual(report["declared_final_attempts"], 1)

    def test_missing_unexpected_evidence_is_exit_two(self):
        with patch("publication.campaign_release.validate_synthesis", return_value={"claim_count": 1}):
            report = validate_campaign_release(self.root, inventory_path="absent.json", synthesis="synthesis")
        self.assertEqual(report["status"], "invalid_evidence")
        self.assertEqual(report["exit_code"], 2)
        self.assertTrue(report["integrity_errors"])

    def test_programming_error_not_swallowed_as_expected_rejection(self):
        self.put("inventory.json", {"fixture": True})
        with patch("publication.campaign_release.verify_inventory", side_effect=RuntimeError("programming defect")):
            with self.assertRaisesRegex(RuntimeError, "programming defect"):
                validate_campaign_release(self.root, inventory_path="inventory.json", synthesis="synthesis")

    def test_old_synthesis_cannot_masquerade_as_current_review(self):
        self.put("synthesis/artifact_manifest.json", {"schema_version": "publication-post-campaign-synthesis-v1"})
        with self.assertRaisesRegex(ValueError, "versioned synthesis"):
            validate_synthesis(self.root, "synthesis")


if __name__ == "__main__":
    unittest.main()
