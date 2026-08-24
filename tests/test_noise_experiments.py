from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    import numpy as np
    import pandas as pd

    from bayesian_modeling.noise_experiments import NoiseInjectionConfig, inject_noise
except ImportError as exc:  # pragma: no cover - depends on scientific environment
    SCIENTIFIC_IMPORT_ERROR = exc
else:
    SCIENTIFIC_IMPORT_ERROR = None


@unittest.skipIf(
    SCIENTIFIC_IMPORT_ERROR is not None,
    f"scientific environment unavailable: {SCIENTIFIC_IMPORT_ERROR}",
)
class NoiseExperimentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = pd.DataFrame(
            {
                "segment_id": ["a"] * 500 + ["b"] * 500,
                "time": np.concatenate([np.arange(500), np.arange(500)]),
                "flux": np.ones(1000),
            }
        )

    def test_injection_is_reproducible_and_does_not_mutate_input(self) -> None:
        config = NoiseInjectionConfig("white_gaussian", 0.001, seed=7)
        source = self.frame.copy(deep=True)
        source.index = np.arange(1000) * 3 + 101
        original = source.copy(deep=True)
        first, _ = inject_noise(source, config)
        second, _ = inject_noise(source, config)
        self.assertTrue(first.equals(second))
        pd.testing.assert_frame_equal(source, original)
        self.assertFalse(np.shares_memory(first["flux"].to_numpy(), source["flux"].to_numpy()))
        recovered = first["flux"] - first["injected_component_fraction"]
        np.testing.assert_allclose(recovered.to_numpy(), first["base_flux"].to_numpy())

    def test_invalid_correlation_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "ar1_rho"):
            inject_noise(
                self.frame,
                NoiseInjectionConfig(
                    "correlated_ar1", 0.001, ar1_rho=1.0
                ),
            )

    def test_correlated_ar1_is_distinct_from_white_noise(self) -> None:
        _, white = inject_noise(
            self.frame, NoiseInjectionConfig("white_gaussian", 0.001, seed=9)
        )
        _, correlated = inject_noise(
            self.frame,
            NoiseInjectionConfig("correlated_ar1", 0.001, seed=9, ar1_rho=0.85),
        )
        self.assertLess(abs(float(white["median_segment_lag1_autocorrelation"])), 0.15)
        self.assertGreater(float(correlated["median_segment_lag1_autocorrelation"]), 0.7)
        self.assertFalse(correlated["correlated_likelihood_implemented_by_this_generator"])

    def test_sinusoid_is_labelled_systematic_not_stochastic_noise(self) -> None:
        _, metrics = inject_noise(
            self.frame,
            NoiseInjectionConfig("deterministic_sinusoid", 0.001, sinusoid_period_days=17.0),
        )
        self.assertIn("deterministic systematic", str(metrics["claim"]))


if __name__ == "__main__":
    unittest.main()
