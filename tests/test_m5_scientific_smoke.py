from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    import numpy as np
    import pandas as pd

    from bayesian_modeling.contracts import build_m5_paths
    from bayesian_modeling.physical_transit import (
        build_model,
        diagnostics_from_summary,
        normalize_arviz_hdi_columns,
        save_prior_predictive_summary,
    )
    from project_config import get_target
except ImportError as exc:  # pragma: no cover - depends on scientific environment
    SCIENTIFIC_IMPORT_ERROR = exc
else:
    SCIENTIFIC_IMPORT_ERROR = None


@unittest.skipIf(
    SCIENTIFIC_IMPORT_ERROR is not None,
    f"scientific environment unavailable: {SCIENTIFIC_IMPORT_ERROR}",
)
class M5ScientificSmokeTests(unittest.TestCase):
    def test_exoplanet_graph_builds_with_exposure_integration(self) -> None:
        expected = {
            "r",
            "b",
            "a",
            "t0",
            "q1",
            "q2",
            "u",
            "extra_sigma",
            "obs",
            "full_duration",
        }
        for target_slug, exposure in (
            ("kepler_10_b", 58.85),
            ("hat_p_7_b", 1765.46),
        ):
            with self.subTest(target=target_slug):
                target = get_target(target_slug)
                prepared = pd.DataFrame(
                    {
                        "phase": np.linspace(-0.1, 0.1, 20),
                        "normalized_flux": np.ones(20),
                        "normalized_flux_err": np.full(20, 1e-4),
                        "exposure_time_seconds": np.full(20, exposure),
                    }
                )
                model = build_model(
                    prepared, np.linspace(-target.phase_window_days, target.phase_window_days, 30), target
                )
                self.assertTrue(expected.issubset(model.named_vars))

    def test_prior_predictive_includes_simulated_observations(self) -> None:
        target = get_target("kepler_10_b")
        prepared = pd.DataFrame(
            {
                "phase": np.linspace(-0.1, 0.1, 12),
                "normalized_flux": np.ones(12),
                "normalized_flux_err": np.full(12, 1e-4),
                "exposure_time_seconds": np.full(12, 58.85),
            }
        )
        model = build_model(prepared, np.linspace(-0.15, 0.15, 20), target)
        with tempfile.TemporaryDirectory() as directory:
            paths = build_m5_paths(Path(directory), target, "prior-smoke")
            paths.table_dir.mkdir(parents=True)
            table, metrics = save_prior_predictive_summary(
                paths, model, target, prepared, samples=5
            )
            self.assertEqual(len(table), 5)
            self.assertIn("minimum_simulated_flux", table)
            self.assertTrue(paths.prior_predictive_summary_path.exists())
            self.assertIn(
                "prior_predictive_interval_94_coverage_observed_points", metrics
            )

    def test_bfmi_is_extracted_from_current_arviz_datatree(self) -> None:
        import pymc as pm

        with pm.Model() as model:
            pm.Normal("x")
            idata = pm.sample(
                draws=20,
                tune=20,
                chains=2,
                cores=1,
                random_seed=42,
                progressbar=False,
            )
        summary = pd.DataFrame(
            {
                "parameter": ["x"],
                "r_hat": [1.0],
                "ess_bulk": [100.0],
                "ess_tail": [100.0],
            }
        )
        diagnostics = diagnostics_from_summary(summary, idata)
        self.assertIsNotNone(diagnostics["bfmi_min"])
        self.assertTrue(np.isfinite(diagnostics["bfmi_min"]))

    def test_current_arviz_hdi_schema_is_normalized(self) -> None:
        summary = pd.DataFrame(
            {"parameter": ["r"], "hdi94_lb": [0.01], "hdi94_ub": [0.02]}
        )
        normalized = normalize_arviz_hdi_columns(summary)
        self.assertEqual(float(normalized.loc[0, "hdi_3%"]), 0.01)
        self.assertEqual(float(normalized.loc[0, "hdi_97%"]), 0.02)


if __name__ == "__main__":
    unittest.main()
