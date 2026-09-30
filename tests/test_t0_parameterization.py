"""Density/Jacobian/gradient equivalence before any new scientific sampling."""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from publication.inference import make_model  # noqa: E402


def fixture():
    frame = pd.DataFrame({"phase": np.linspace(-.1, .1, 21),
                          "normalized_flux": np.ones(21),
                          "normalized_flux_err": np.full(21, .001),
                          "exposure_time_seconds": np.full(21, 60.)})
    config = {"period_days": 1., "oversample": 3, "t0_prior_sigma_days": .025,
              "baseline_prior_sigma": .02, "radius_prior_median": .04,
              "radius_prior_log_sigma": .9, "infer_jitter": True,
              "integrate_exposure": True, "jitter_error_multiplier": 5.,
              "jitter_floor_fraction": .0005}
    return frame, config


class TransitCenterParameterizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        frame, config = fixture()
        cls.legacy, cls.old_spec = make_model(frame, config)
        cls.scaled, cls.new_spec = make_model(frame, {**config, "transit_center_parameterization": "standardized"})
        cls.old_logp = cls.legacy.compile_logp()
        cls.new_logp = cls.scaled.compile_logp()
        cls.old_grad = cls.legacy.compile_dlogp()
        cls.new_grad = cls.scaled.compile_dlogp()
        cls.old_likelihood = cls.legacy.compile_logp(vars=cls.legacy.observed_RVs, jacobian=False)
        cls.new_likelihood = cls.scaled.compile_logp(vars=cls.scaled.observed_RVs, jacobian=False)

    def points(self, z):
        old = self.legacy.initial_point()
        old["t0"] = np.asarray(.025 * z)
        new = {name: value.copy() for name, value in old.items() if name != "t0"}
        new["t0_standardized"] = np.asarray(z)
        return old, new

    def test_likelihood_prior_jacobian_and_gradients_at_nonzero_and_alias_points(self):
        names_old = [v.name for v in self.legacy.value_vars]
        names_new = [v.name for v in self.scaled.value_vars]
        for z in (-40., -1.2, 0., .7, 40.):
            old, new = self.points(z)
            with self.subTest(z=z):
                self.assertAlmostEqual(float(self.new_logp(new) - self.old_logp(old)), math.log(.025), places=8)
                self.assertAlmostEqual(float(self.old_likelihood(old)), float(self.new_likelihood(new)), places=8)
                go, gn = self.old_grad(old), self.new_grad(new)
                for index, name in enumerate(names_old):
                    match = "t0_standardized" if name == "t0" else name
                    expected = go[index] * (.025 if name == "t0" else 1)
                    np.testing.assert_allclose(gn[names_new.index(match)], expected, rtol=1e-8, atol=1e-6)

    def test_output_t0_is_in_days_and_version_is_explicit(self):
        self.assertIn("t0", [v.name for v in self.scaled.deterministics])
        self.assertIn("t0", [v.name for v in self.legacy.free_RVs])
        self.assertEqual(self.old_spec["family"], "M5-publication-v1")
        self.assertEqual(self.new_spec["family"], "M5-publication-v2-standardized-t0")
        self.assertEqual(self.old_spec["options"], self.new_spec["options"])
        self.assertEqual(self.old_spec["prior_profile"], self.new_spec["prior_profile"])

    def test_invalid_coordinate_mode_rejects(self):
        frame, config = fixture()
        with self.assertRaises(ValueError):
            make_model(frame, {**config, "transit_center_parameterization": "wrapped"})


if __name__ == "__main__":
    unittest.main()
