"""Regression checks for current-versus-historical model-run classification."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.build_model_run_inventory import classify_run, interpretability_state

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ModelRunInventoryTests(unittest.TestCase):
    def test_passed_gate_requires_current_dataset_identity(self) -> None:
        gate = {"scientifically_interpretable": True}
        current = classify_run(
            status={"status": "completed"},
            gate=gate,
            dataset_id="dataset-new",
            current_dataset_id="dataset-new",
        )
        historical = classify_run(
            status={"status": "completed"},
            gate=gate,
            dataset_id="dataset-old",
            current_dataset_id="dataset-new",
        )

        self.assertEqual(current, "current_scientifically_interpretable")
        self.assertEqual(historical, "historical_gated_dataset_not_current")

        current_state = interpretability_state(
            status={"status": "completed"},
            gate=gate,
            dataset_id="dataset-new",
            current_dataset_id="dataset-new",
        )
        historical_state = interpretability_state(
            status={"status": "completed"},
            gate=gate,
            dataset_id="dataset-old",
            current_dataset_id="dataset-new",
        )
        self.assertTrue(current_state["stored_gate_scientifically_interpretable"])
        self.assertTrue(current_state["currently_scientifically_interpretable"])
        self.assertTrue(historical_state["stored_gate_scientifically_interpretable"])
        self.assertFalse(historical_state["currently_scientifically_interpretable"])

    def test_failed_status_wins_over_stale_true_gate(self) -> None:
        classification = classify_run(
            status={"status": "failed"},
            gate={"scientifically_interpretable": True},
            dataset_id="dataset-new",
            current_dataset_id="dataset-new",
        )

        self.assertEqual(classification, "failed_preserved_for_traceability")

        state = interpretability_state(
            status={"status": "failed"},
            gate={"scientifically_interpretable": True},
            dataset_id="dataset-new",
            current_dataset_id="dataset-new",
        )
        self.assertTrue(state["stored_gate_scientifically_interpretable"])
        self.assertFalse(state["currently_scientifically_interpretable"])

    def test_rejected_and_missing_stored_gates_are_explicit(self) -> None:
        rejected = interpretability_state(
            status={"status": "completed"},
            gate={"scientifically_interpretable": False},
            dataset_id="dataset-new",
            current_dataset_id="dataset-new",
        )
        ungated = interpretability_state(
            status={},
            gate=None,
            dataset_id=None,
            current_dataset_id=None,
        )

        self.assertFalse(rejected["stored_gate_scientifically_interpretable"])
        self.assertFalse(rejected["currently_scientifically_interpretable"])
        self.assertEqual(rejected["classification"], "stored_gate_rejected")
        self.assertIsNone(ungated["stored_gate_scientifically_interpretable"])
        self.assertFalse(ungated["currently_scientifically_interpretable"])

    def test_generated_inventory_separates_stored_and_current_meanings(self) -> None:
        payload = json.loads(
            (PROJECT_ROOT / "reports" / "model_run_inventory.json").read_text(
                encoding="utf-8"
            )
        )
        runs = {row["run_id"]: row for row in payload["runs"]}

        historical = runs["scientific_002"]
        current = runs["scientific_003"]
        self.assertTrue(historical["stored_gate_scientifically_interpretable"])
        self.assertFalse(historical["currently_scientifically_interpretable"])
        self.assertTrue(current["stored_gate_scientifically_interpretable"])
        self.assertTrue(current["currently_scientifically_interpretable"])
        self.assertTrue(
            all(
                "stored_gate_scientifically_interpretable" in row
                and "currently_scientifically_interpretable" in row
                and "scientifically_interpretable" not in row
                for row in payload["runs"]
            )
        )


if __name__ == "__main__":
    unittest.main()
