"""Regression tests for the scientifically justified M5 prior family."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bayesian_modeling.contracts import (  # noqa: E402
    PRIOR_PROFILES,
    get_prior_profile,
    jitter_prior_scale,
    physical_model_spec,
)
from project_config import get_target  # noqa: E402


class PriorProfileTests(unittest.TestCase):
    def test_profiles_expand_monotonically_around_catalog_scale(self) -> None:
        tighter = PRIOR_PROFILES["catalog_tighter"]
        baseline = PRIOR_PROFILES["baseline"]
        weak = PRIOR_PROFILES["weak"]
        self.assertLess(tighter.radius_ratio_log_sigma, baseline.radius_ratio_log_sigma)
        self.assertLess(baseline.radius_ratio_log_sigma, weak.radius_ratio_log_sigma)
        self.assertLess(tighter.jitter_error_multiplier, baseline.jitter_error_multiplier)
        self.assertLess(baseline.jitter_error_multiplier, weak.jitter_error_multiplier)

    def test_jitter_scale_is_in_normalized_flux_units(self) -> None:
        measurement_sigma = 2e-5
        self.assertAlmostEqual(
            jitter_prior_scale(measurement_sigma, PRIOR_PROFILES["baseline"]),
            5e-4,
        )
        self.assertLess(
            jitter_prior_scale(measurement_sigma, PRIOR_PROFILES["catalog_tighter"]),
            jitter_prior_scale(measurement_sigma, PRIOR_PROFILES["weak"]),
        )

    def test_model_spec_records_selected_profile_and_target(self) -> None:
        target = get_target("kepler_10_b")
        spec = physical_model_spec(target, 58.85, 2e-5, get_prior_profile("weak"))
        self.assertEqual(spec["priors"]["profile"]["name"], "weak")
        self.assertEqual(spec["orbit"]["period_days"], target.orbital_period_days)
        self.assertEqual(
            spec["priors"]["r"]["center_source"],
            "sqrt(authoritative catalog transit_depth_fraction)",
        )

    def test_unknown_profile_fails_loudly(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown prior profile"):
            get_prior_profile("absurd")


if __name__ == "__main__":
    unittest.main()
