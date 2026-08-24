"""Regression checks tying the published M5 report to its machine config."""

from __future__ import annotations

import csv
import hashlib
import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "scientific_002"
MODEL_DIR = (
    PROJECT_ROOT
    / "models"
    / "bayesian_physical_transit"
    / "kepler_10_b"
    / "runs"
    / RUN_ID
)
TABLE_DIR = (
    PROJECT_ROOT
    / "tables"
    / "bayesian_physical_transit"
    / "kepler_10_b"
    / "runs"
    / RUN_ID
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class CurrentM5ArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = json.loads(
            (MODEL_DIR / "model_config.json").read_text(encoding="utf-8")
        )

    def test_config_report_and_status_have_one_target_identity(self) -> None:
        serialized = json.dumps(self.config, ensure_ascii=False)
        report = (
            PROJECT_ROOT
            / "reports"
            / "bayesian_physical_transit_kepler_10_b_scientific_002_report.md"
        ).read_text(encoding="utf-8")
        status = json.loads((MODEL_DIR / "run_status.json").read_text(encoding="utf-8"))
        self.assertEqual(self.config["target"]["planet_name"], "Kepler-10 b")
        self.assertEqual(self.config["run_id"], RUN_ID)
        self.assertNotIn("HAT-P-7", serialized)
        self.assertNotIn("hat_p_7_b", serialized)
        self.assertIn("Kepler-10 b", report)
        self.assertIn(RUN_ID, report)
        self.assertNotIn("HAT-P-7", report)
        self.assertEqual(status["status"], "completed")
        self.assertTrue(status["interpretation_gate"]["scientifically_interpretable"])

    def test_period_and_input_checksum_propagate(self) -> None:
        input_path = TABLE_DIR / "modeling_input_physical.csv"
        self.assertEqual(
            sha256(input_path), self.config["input_summary"]["modeling_input_sha256"]
        )
        with (TABLE_DIR / "derived_parameters_summary.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            derived = next(csv.DictReader(handle))
        self.assertEqual(
            float(derived["orbital_period_days_used"]),
            float(self.config["model"]["orbit"]["period_days"]),
        )
        self.assertEqual(float(derived["orbital_period_days_used"]), 0.8374907)
        self.assertTrue(derived["rp_rs_hdi_3"])
        self.assertTrue(derived["rp_rs_hdi_97"])

    def test_machine_model_matches_documented_physical_family(self) -> None:
        model = self.config["model"]
        self.assertEqual(model["family"], "quadratic_limb_darkened_keplerian_transit")
        self.assertEqual(model["limb_darkening"]["sampling_parameters"], ["q1", "q2"])
        self.assertTrue(model["exposure_integration"]["enabled"])
        self.assertEqual(model["likelihood"]["distribution"], "Normal")
        self.assertTrue(self.config["log_likelihood"]["available"])


if __name__ == "__main__":
    unittest.main()
