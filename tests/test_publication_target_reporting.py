from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from publication.contracts import canonical_hash, sha256_file  # noqa: E402
from publication.observational import prepare_observational_target  # noqa: E402
from publication.target_reporting import (  # noqa: E402
    aggregate_target_outcomes,
    write_target_report,
)


class PublicationTargetReportingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol = json.loads((PROJECT_ROOT / "publication/protocols/PUB-05.json").read_text(encoding="utf-8"))
        self.result = {
            "status": "completed", "gates": {name: True for name in ("provenance", "sampler", "ppc", "scientific")},
            "dataset_id": "isolated-data", "input_sha256": "a" * 64,
            "parameters": {"r": {"mean": .1, "sd": .01, "interval_method": "equal_tailed",
                                    "intervals": {"0.5": [.095, .105], "0.8": [.09, .11], "0.94": [.08, .12]}}},
        }

    def test_all_five_remain_with_missing_failed_and_rejected_posteriors(self) -> None:
        rejected = copy.deepcopy(self.result)
        rejected.update(status="rejected", gates={"provenance": True, "sampler": True, "ppc": False, "scientific": False})
        report = aggregate_target_outcomes(self.protocol, [
            {"target_id": "hat_p_7_b", "status": "completed", "result": self.result},
            {"target_id": "tres_2_b", "status": "rejected", "result": rejected},
            {"target_id": "kepler_4_b", "status": "failed", "failure_stage": "preparation"},
        ])
        self.assertEqual(report["declared_targets"], 5)
        self.assertEqual(report["status_counts"], {"completed": 1, "failed": 1, "missing": 2, "rejected": 1})
        self.assertEqual(report["scientifically_interpretable_fraction_all_selected"], .2)
        self.assertEqual(report["gate_counts"]["ppc"], {"passed": 1, "rejected": 1, "unavailable": 3})
        self.assertEqual(len(report["posterior_intervals"]), 6)
        self.assertFalse(report["complete_declared_batch"])

    def test_status_and_identity_conflicts_reject_and_promotion_fails_closed(self) -> None:
        result = copy.deepcopy(self.result)
        result["gates"]["sampler"] = False
        report = aggregate_target_outcomes(self.protocol, [{"target_id": "hat_p_7_b", "status": "completed", "result": result}])
        self.assertEqual(report["scientifically_interpretable_count"], 0)
        with self.assertRaisesRegex(ValueError, "status mismatch"):
            aggregate_target_outcomes(self.protocol, [{"target_id": "hat_p_7_b", "status": "failed", "result": result}])
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            aggregate_target_outcomes(self.protocol, [{"target_id": "hat_p_7_b", "status": "completed", "result": result,
                                                       "preparation": {"target_id": "hat_p_7_b", "dataset_id": "wrong"}}])

    def test_report_requires_real_source_values_and_generates_fresh_figures(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            protocol_path = root / "protocol.json"
            protocol_path.write_text(json.dumps(self.protocol), encoding="utf-8")
            (root / "result.json").write_text(json.dumps(self.result), encoding="utf-8")
            outcomes = [{"target_id": "hat_p_7_b", "status": "completed", "result": self.result, "source_paths": ["result.json"]}]
            output = write_target_report(root, protocol_path, outcomes, Path("publication/derived/PUB-05/fixture"), campaign_id="fixture")
            manifest = json.loads((output / "artifact_manifest.json").read_text())
            self.assertEqual(manifest["source_checksums"]["result.json"], sha256_file(root / "result.json"))
            for name, checksum in manifest["artifacts"].items():
                self.assertEqual(checksum, sha256_file(output / name))
            self.assertEqual(len((output / "targets.csv").read_text().splitlines()), 6)
            tampered = copy.deepcopy(outcomes)
            tampered[0]["result"]["parameters"]["r"]["mean"] = .2
            with self.assertRaisesRegex(ValueError, "audited source JSON"):
                write_target_report(root, protocol_path, tampered, output, campaign_id="fixture")

    def test_campaign_wrapper_separates_file_and_canonical_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "protocol.json"
            path.write_text(json.dumps(self.protocol, indent=2), encoding="utf-8")
            identity = {"path": "protocol.json", "sha256": sha256_file(path), "canonical_json_sha256": canonical_hash(self.protocol)}
            preparation = {"output_directory": "publication/observational/PUB-05/hat_p_7_b/campaign_job_attempt_000",
                           "dataset_id": "fixture", "input_sha256": "1" * 64}
            with patch("publication.contracts.committed_protocol", return_value=identity), patch("publication.observational.prepare_target", return_value=preparation) as prepare, patch("publication.observational.verify_prepared_target", return_value={"status": "passed"}):
                result = prepare_observational_target(root, Path("protocol.json"), "hat_p_7_b", "campaign_job_attempt_000",
                                                      expected_protocol_sha256=identity["sha256"], expected_protocol_canonical_sha256=identity["canonical_json_sha256"])
                self.assertEqual(result["protocol_file_sha256"], identity["sha256"])
                self.assertNotEqual(result["protocol_file_sha256"], result["protocol_canonical_sha256"])
                self.assertFalse(Path(result["input_path"]).is_absolute())
                self.assertNotIn("\\", result["input_path"])
                prepare.assert_called_once()
                with self.assertRaisesRegex(ValueError, "file SHA-256 mismatch"):
                    prepare_observational_target(root, path, "hat_p_7_b", "attempt_001", expected_protocol_sha256="0" * 64)
                self.assertEqual(prepare.call_count, 1)


if __name__ == "__main__":
    unittest.main()
