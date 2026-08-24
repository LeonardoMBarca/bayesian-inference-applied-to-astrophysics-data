from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bayesian_modeling.contracts import (  # noqa: E402
    build_m5_paths,
    evaluate_interpretation_gate,
    physical_model_spec,
    validate_formal_comparison_contract,
)
from project_config import get_target  # noqa: E402


class M5ContractTests(unittest.TestCase):
    def test_paths_are_target_and_run_specific(self) -> None:
        root = PROJECT_ROOT / ".test-path-contract"
        hat = build_m5_paths(root, get_target("hat_p_7_b"), "run-a")
        kepler = build_m5_paths(root, get_target("kepler_10_b"), "run-b")
        self.assertIn("hat_p_7_b", hat.report_path.name)
        self.assertIn("kepler_10_b", kepler.report_path.name)
        self.assertNotIn("hat_p_7_b", kepler.report_path.as_posix())
        self.assertNotEqual(hat.model_dir, kepler.model_dir)

    def test_physical_model_spec_uses_target_period_and_exposure(self) -> None:
        target = get_target("kepler_10_b")
        spec = physical_model_spec(target, 1765.5, 2e-4)
        self.assertEqual(spec["orbit"]["period_days"], target.orbital_period_days)
        self.assertTrue(spec["exposure_integration"]["enabled"])
        self.assertEqual(spec["priors"]["r"]["distribution"], "LogNormal")
        self.assertAlmostEqual(spec["priors"]["extra_sigma"]["sigma"], 0.001)
        self.assertNotIn("half_duration", repr(spec))

    def test_sampler_convergence_alone_does_not_pass_gate(self) -> None:
        gate = evaluate_interpretation_gate(
            diagnostics={"max_r_hat": 1.0, "min_ess": 1000, "divergences": 0, "bfmi_min": 0.8},
            residual_metrics={
                "posterior_predictive_interval_94_coverage_observed_points": 0.94,
                "standardized_residual_std": 1.0,
            },
            input_summary={
                "preprocessing_status": "global_normalization",
                "dataset_id": "bad-data",
                "segment_count": 3,
                "median_exposure_seconds": 1765.5,
            },
            posterior_scale_checks={
                "extra_sigma_to_measurement_sigma": 672.0,
                "radius_ratio_boundary_fraction": 0.2,
            },
            posterior_predictive_status="created",
        )
        self.assertTrue(gate["sampler_converged"])
        self.assertFalse(gate["scientifically_interpretable"])
        self.assertGreaterEqual(len(gate["rejection_reasons"]), 2)

    def test_formal_comparison_rejects_different_inputs_or_failed_gate(self) -> None:
        common = {
            "model": {"likelihood": {"distribution": "Normal"}},
            "log_likelihood": {"available": True},
        }
        first = {
            **common,
            "run_id": "first",
            "input_summary": {"dataset_id": "one", "modeling_input_sha256": "abc"},
            "interpretation_gate": {"scientifically_interpretable": True},
        }
        second = {
            **common,
            "run_id": "second",
            "input_summary": {"dataset_id": "one", "modeling_input_sha256": "different"},
            "interpretation_gate": {"scientifically_interpretable": False},
        }
        contract = validate_formal_comparison_contract([first, second])
        self.assertFalse(contract["formal_comparison_valid"])
        self.assertEqual(contract["allowed_metrics"], [])
        self.assertGreaterEqual(len(contract["rejection_reasons"]), 2)

    def test_formal_comparison_accepts_equivalent_likelihood_key_order(self) -> None:
        first = {
            "run_id": "first",
            "model": {"likelihood": {"distribution": "Normal", "sigma": "known"}},
            "log_likelihood": {"available": True},
            "input_summary": {"dataset_id": "same", "modeling_input_sha256": "abc"},
            "interpretation_gate": {"scientifically_interpretable": True},
        }
        second = {
            **first,
            "run_id": "second",
            "model": {"likelihood": {"sigma": "known", "distribution": "Normal"}},
        }
        contract = validate_formal_comparison_contract([first, second])
        self.assertTrue(contract["formal_comparison_valid"])
        self.assertEqual(contract["allowed_metrics"], ["LOO", "WAIC", "ELPD"])


if __name__ == "__main__":
    unittest.main()
