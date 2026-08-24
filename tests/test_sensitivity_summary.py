"""Regression tests for honest prior-sensitivity interpretation."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    import pandas as pd

    from bayesian_modeling.contracts import PRIOR_PROFILES, build_m5_paths
    from bayesian_modeling.sensitivity import summarize_sensitivity
    from project_config import get_target
except ImportError as exc:  # pragma: no cover - depends on scientific environment
    SCIENTIFIC_IMPORT_ERROR = exc
else:
    SCIENTIFIC_IMPORT_ERROR = None


@unittest.skipIf(
    SCIENTIFIC_IMPORT_ERROR is not None,
    f"scientific environment unavailable: {SCIENTIFIC_IMPORT_ERROR}",
)
class SensitivitySummaryTests(unittest.TestCase):
    def _fixture(
        self,
        root: Path,
        failed_profile: str | None = None,
        incomplete_profile: str | None = None,
    ) -> dict[str, str]:
        target = get_target("kepler_10_b")
        runs: dict[str, str] = {}
        for index, profile in enumerate(PRIOR_PROFILES):
            run_id = f"fixture_{profile}"
            runs[profile] = run_id
            paths = build_m5_paths(root, target, run_id)
            paths.model_dir.mkdir(parents=True)
            paths.table_dir.mkdir(parents=True)
            gate = profile != failed_profile
            config = {
                "run_id": run_id,
                "model": {
                    "priors": {"profile": {"name": profile}},
                    "likelihood": {"distribution": "Normal"},
                },
                "log_likelihood": {"available": True},
                "input_summary": {
                    "dataset_id": "same",
                    "modeling_input_sha256": "abc",
                },
                "interpretation_gate": {"scientifically_interpretable": gate},
                "diagnostics": {
                    "max_r_hat": 1.0,
                    "min_ess": 500,
                    "divergences": 0,
                    "bfmi_min": 0.8,
                },
                "prior_predictive_metrics": {
                    "catalog_reference_inside_94_interval": True
                },
            }
            paths.model_config_path.write_text(json.dumps(config), encoding="utf-8")
            (paths.model_dir / "run_status.json").write_text(
                json.dumps(
                    {
                        "status": (
                            "failed" if profile == incomplete_profile else "completed"
                        )
                    }
                ),
                encoding="utf-8",
            )
            means = {"r": 0.012 + index * 0.0001, "depth": 0.00015}
            means.update({"extra_sigma": 0.0002, "full_duration": 0.08})
            posterior = pd.DataFrame(
                [
                    {
                        "parameter": parameter,
                        "mean": mean,
                        "hdi_3%": mean * 0.8,
                        "hdi_97%": mean * 1.2,
                    }
                    for parameter, mean in means.items()
                ]
            )
            posterior.to_csv(paths.posterior_summary_path, index=False)
        return runs

    def test_all_profiles_require_independent_gates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runs = self._fixture(root)
            result = summarize_sensitivity(
                project_root=root,
                target_slug="kepler_10_b",
                run_by_profile=runs,
                experiment_id="fixture",
            )
            self.assertTrue(result["all_scientific_gates_pass"])
            self.assertTrue(result["formal_comparison_contract"]["formal_comparison_valid"])
            self.assertIn("reported descriptively", result["conclusion"])

    def test_failed_profile_forbids_robustness_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runs = self._fixture(root, failed_profile="weak")
            result = summarize_sensitivity(
                project_root=root,
                target_slug="kepler_10_b",
                run_by_profile=runs,
                experiment_id="fixture-failed",
            )
            self.assertFalse(result["all_scientific_gates_pass"])
            self.assertFalse(result["formal_comparison_contract"]["formal_comparison_valid"])
            self.assertIn("No robustness claim", result["conclusion"])

    def test_failed_status_rejects_true_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runs = self._fixture(root, incomplete_profile="weak")
            result = summarize_sensitivity(
                project_root=root,
                target_slug="kepler_10_b",
                run_by_profile=runs,
                experiment_id="fixture-incomplete",
            )
            self.assertFalse(result["all_runs_completed"])
            self.assertFalse(result["all_scientific_gates_pass"])
            self.assertFalse(result["formal_comparison_contract"]["formal_comparison_valid"])
            self.assertIn("not completed", result["conclusion"])


if __name__ == "__main__":
    unittest.main()
