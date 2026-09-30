"""An arbitrary exit code 1 must never count as a successful release audit."""
import copy
import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("closure_harness", Path(__file__).parent / "manual/validate_post_campaign_synthesis.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ReleaseHarnessTests(unittest.TestCase):
    def setUp(self):
        self.report = {
            "schema_version": "publication-campaign-release-audit-v2", "integrity_status": "passed",
            "integrity_errors": [], "declared_final_jobs": 517, "declared_final_attempts": 518,
            "exit_code": 1, "status": "blocked_public_release", "release_passed": False,
            "checks": [{"check": key, "status": "passed"} for key in
                       ("transitive_inventory", "transitive_byte_integrity", "declared_campaigns_and_attempts", "scientific_claim_sources")],
            "public_release_blockers": [{"check": "external_archive", "reason": "No public DOI deposited",
                                         "classification": "public_release_prerequisite_pending"}],
        }

    def test_known_prerequisite_not_scientific_rejection(self):
        self.assertTrue(MODULE.acceptable_release_response(1, self.report))
        for key, value in (("status", "validator_error"), ("declared_final_jobs", 0),
                           ("integrity_errors", [{"reason": "missing trace"}]), ("release_passed", True)):
            report = copy.deepcopy(self.report)
            report[key] = value
            self.assertFalse(MODULE.acceptable_release_response(1, report))
        self.report["public_release_blockers"][0]["check"] = "scientific_gate_rejected"
        self.assertFalse(MODULE.acceptable_release_response(1, self.report))

    def test_error_or_missing_check_not_accepted(self):
        self.assertFalse(MODULE.acceptable_release_response(2, self.report))
        self.assertFalse(MODULE.acceptable_release_response(1, {}))
        self.report["checks"].pop()
        self.assertFalse(MODULE.acceptable_release_response(1, self.report))

    def test_actual_pass_requires_zero_and_no_blockers(self):
        self.report.update(status="passed", release_passed=True, exit_code=0, public_release_blockers=[])
        self.assertTrue(MODULE.acceptable_release_response(0, self.report))
        self.assertFalse(MODULE.acceptable_release_response(1, self.report))


if __name__ == "__main__":
    unittest.main()
