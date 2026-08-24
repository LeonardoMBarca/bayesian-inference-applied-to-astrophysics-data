"""Integration tests for guarded model-comparison output."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    import arviz as az
    from bayesian_modeling.comparison import (
        _loo_scalar,
        _waic_from_pointwise_log_likelihood,
        compare_runs,
    )
except ImportError as exc:  # pragma: no cover - depends on scientific environment
    SCIENTIFIC_IMPORT_ERROR = exc
else:
    SCIENTIFIC_IMPORT_ERROR = None


@unittest.skipIf(
    SCIENTIFIC_IMPORT_ERROR is not None,
    f"scientific environment unavailable: {SCIENTIFIC_IMPORT_ERROR}",
)
class ModelComparisonTests(unittest.TestCase):
    def test_loo_scalar_supports_current_and_legacy_attribute_names(self) -> None:
        self.assertEqual(
            _loo_scalar(SimpleNamespace(elpd=12.5), "elpd_loo", "elpd"), 12.5
        )
        self.assertEqual(
            _loo_scalar(SimpleNamespace(elpd_loo=8.5), "elpd_loo", "elpd"), 8.5
        )

    def test_waic_matches_direct_pointwise_definition(self) -> None:
        log_likelihood = np.array(
            [
                [[-1.0, -2.0], [-1.2, -1.8]],
                [[-0.9, -2.1], [-1.1, -1.9]],
            ]
        )
        idata = az.from_dict(
            {"log_likelihood": {"obs": log_likelihood}},
            sample_dims=["chain", "draw"],
        )
        result = _waic_from_pointwise_log_likelihood(idata)
        samples = log_likelihood.reshape(4, 2)
        lppd = np.log(np.mean(np.exp(samples), axis=0))
        variance = np.var(samples, axis=0, ddof=1)
        pointwise = lppd - variance
        expected_se = np.sqrt(2 * np.var(pointwise, ddof=0))

        self.assertAlmostEqual(result["elpd_waic"], float(pointwise.sum()))
        self.assertAlmostEqual(result["p_waic"], float(variance.sum()))
        self.assertAlmostEqual(result["se"], float(expected_se))
        self.assertEqual(result["n_posterior_samples"], 4)
        self.assertEqual(result["n_observations"], 2)
        self.assertFalse(result["warning"])

    def test_waic_warns_for_high_pointwise_variance(self) -> None:
        log_likelihood = np.array([[[-1.0], [-3.0]]])
        idata = az.from_dict(
            {"log_likelihood": {"obs": log_likelihood}},
            sample_dims=["chain", "draw"],
        )
        result = _waic_from_pointwise_log_likelihood(idata)

        self.assertTrue(result["warning"])
        self.assertEqual(result["pointwise_variance_gt_0_4_count"], 1)

    def test_rejected_contract_never_reads_traces_or_computes_loo(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_paths = []
            for run_id, digest in (("one", "abc"), ("two", "different")):
                config = {
                    "run_id": run_id,
                    "model": {"likelihood": {"distribution": "Normal"}},
                    "log_likelihood": {"available": True},
                    "input_summary": {
                        "dataset_id": "same",
                        "modeling_input_sha256": digest,
                    },
                    "interpretation_gate": {"scientifically_interpretable": True},
                    "artifacts": {"trace": "does/not/exist.nc"},
                    "residual_metrics": {"rmse": 0.1, "mae": 0.08},
                }
                path = root / f"{run_id}.json"
                path.write_text(json.dumps(config), encoding="utf-8")
                config_paths.append(path)
            output = root / "comparison"
            result = compare_runs(
                project_root=root,
                config_paths=config_paths,
                output_dir=output,
            )
            self.assertFalse(result["comparison_contract"]["formal_comparison_valid"])
            self.assertIsNone(result["formal_bayesian_metrics"])
            self.assertEqual(len(result["predictive_metrics"]), 2)
            self.assertEqual(
                result["heuristic_structural_scores"]["status"], "not_computed"
            )
            self.assertTrue((output / "comparison_summary.json").exists())
            self.assertFalse((output / "loo_summary.csv").exists())


if __name__ == "__main__":
    unittest.main()
