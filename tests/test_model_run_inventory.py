"""Regression checks for current-versus-historical model-run classification."""

from __future__ import annotations

import unittest

from scripts.build_model_run_inventory import classify_run


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

    def test_failed_status_wins_over_stale_true_gate(self) -> None:
        classification = classify_run(
            status={"status": "failed"},
            gate={"scientifically_interpretable": True},
            dataset_id="dataset-new",
            current_dataset_id="dataset-new",
        )

        self.assertEqual(classification, "failed_preserved_for_traceability")


if __name__ == "__main__":
    unittest.main()
