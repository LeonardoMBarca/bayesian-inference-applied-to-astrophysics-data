from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from publication.benchmark import (  # noqa: E402
    array_identity,
    compare_posterior_arrays,
    exposure_argument_seconds,
    juliet_arguments,
    load_dataset,
    posterior_parameters,
)
from publication.benchmark_runner import (  # noqa: E402
    dynesty_rng_bridge,
    nested_diagnostics,
    predictive_gate,
    validate_execution_contract,
)


def frame_fixture() -> pd.DataFrame:
    return pd.DataFrame({"phase": np.linspace(-.1, .1, 20), "time": np.linspace(0, .2, 20),
                         "normalized_flux": np.ones(20), "normalized_flux_err": np.linspace(.0001, .0002, 20),
                         "exposure_time_seconds": [60.] * 10 + [120.] * 10,
                         "segment_id": ["a"] * 10 + ["b"] * 10})


def config_fixture() -> dict:
    return {"period_days": 2.0, "radius_prior_uniform": [.001, .2], "radius_prior_median": None,
            "baseline_prior_sigma": .02, "t0_prior_sigma_days": .025,
            "jitter_error_multiplier": 5.0, "jitter_floor_fraction": .0005,
            "infer_jitter": True, "integrate_exposure": True, "oversample": 15}


class PublicationBenchmarkTests(unittest.TestCase):
    def test_midpoint_stencil_equivalence_not_exposure_approximation(self):
        for n in (3, 15, 31):
            actual = np.linspace(-.5, .5, n) * exposure_argument_seconds(1800., n)
            expected = ((np.arange(n) + .5) / n - .5) * 1800.
            np.testing.assert_allclose(actual, expected, atol=1e-12)
        self.assertEqual(exposure_argument_seconds(60., 1), 0.)
        for n in (False, 0, 2, 1.5):
            with self.assertRaises(ValueError):
                exposure_argument_seconds(60., n)

    def test_exact_exposure_groups_share_nuisance_parameters_and_preserve_rows(self):
        frame = frame_fixture()
        args, meta = juliet_arguments(frame, config_fixture())
        self.assertEqual(meta["physical_exposure_seconds_by_instrument"], {"B000": 60., "B001": 120.})
        self.assertEqual(meta["row_indices_by_instrument"]["B001"], list(range(10, 20)))
        self.assertIn("theta0_B000_B001", args["priors"])
        self.assertNotIn("theta0_B000", args["priors"])
        self.assertEqual(args["priors"]["mflux_B000_B001"]["hyperparameters"], 0.)
        np.testing.assert_array_equal(args["linear_regressors_lc"]["B000"], np.ones((10, 1)))
        np.testing.assert_array_equal(args["t_lc"]["B001"], frame.phase.to_numpy()[10:])
        self.assertAlmostEqual(args["priors"]["sigma_w_B000_B001"]["hyperparameters"][1], 750.)

    def test_input_hash_and_identity_reject_before_importing_juliet(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            frame_fixture().to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                load_dataset(path, {"input_sha256": "incorrect"})

    def test_array_identity_binds_values_order_and_segment(self):
        frame = frame_fixture()
        original = array_identity(frame)
        self.assertEqual(original, array_identity(frame.copy()))
        self.assertNotEqual(original, array_identity(frame.iloc[::-1]))
        altered = frame.copy()
        altered.loc[0, "segment_id"] = "other"
        self.assertNotEqual(original, array_identity(altered))
        altered = frame.copy()
        altered.loc[0, "normalized_flux"] += 1e-10
        self.assertNotEqual(original, array_identity(altered))

    def test_output_collision_rejected_before_external_engine_import(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            frame_fixture().to_csv(path, index=False)
            config = config_fixture()
            config.update(input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                          dataset_id="engineering-fixture", expected_dataset_id="engineering-fixture")
            output = Path(directory) / "existing-run"
            output.mkdir()
            marker = output / "do-not-overwrite.txt"
            marker.write_text("preserve", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                load_dataset(path, config, out_folder=output)
            self.assertEqual(marker.read_text(encoding="utf-8"), "preserve")

    def test_no_silent_lognormal_prior_substitution(self):
        config = config_fixture()
        config["radius_prior_median"] = .04
        with self.assertRaisesRegex(ValueError, "uniform-radius"):
            juliet_arguments(frame_fixture(), config)

    def test_parameter_mapping_ppm_offset_and_derived_geometry(self):
        samples = {"p_p1": [.1, .2], "b_p1": [0., .4], "a_p1": [10., 15.], "t0_p1": [0., .01],
                   "q1_B000": [.25, .3], "q2_B000": [.2, .4], "theta0_B000": [.01, -.02],
                   "sigma_w_B000": [100., 200.]}
        result = posterior_parameters(samples, "B000", 2.)
        np.testing.assert_allclose(result["baseline"], [1.01, .98])
        np.testing.assert_allclose(result["extra_sigma"], [.0001, .0002])
        np.testing.assert_allclose(result["depth"], [.01, .04])
        self.assertAlmostEqual(result["full_duration"][0], 2 / np.pi * np.arcsin(.11))
        samples["a_p1"] = [10.]
        with self.assertRaisesRegex(ValueError, "misaligned"):
            posterior_parameters(samples, "B000", 2.)

    def test_nested_budget_termination_cannot_be_promoted(self):
        raw = SimpleNamespace(logwt=np.zeros(500), ncall=np.ones(500), niter=499,
                              logz=np.array([10.]), logzerr=np.array([.2]))
        sampling = {"maxcall": 100, "maxiter": None, "minimum_weighted_ess": 400,
                    "maximum_logz_error": .5}
        diagnostics, weights = nested_diagnostics(raw, sampling)
        self.assertFalse(diagnostics["passed"])
        self.assertTrue(diagnostics["budget_stopped"])
        self.assertAlmostEqual(float(weights.sum()), 1.)
        sampling["maxcall"] = 1000
        self.assertTrue(nested_diagnostics(raw, sampling)[0]["passed"])

    def test_final_execution_requires_explicit_mode_and_environment_identity(self):
        with self.assertRaisesRegex(ValueError, "mode"):
            validate_execution_contract({})
        with self.assertRaisesRegex(ValueError, "environment manifest"):
            validate_execution_contract({"mode": "pilot", "benchmark_environment_sha256": "incorrect"})

    def test_distribution_comparison_detects_width_disagreement_with_identical_mean(self):
        names = ("r", "depth", "b", "a", "t0", "full_duration", "extra_sigma")
        local = {name: np.linspace(-1., 1., 101) for name in names}
        external = {name: values * 3 for name, values in local.items()}
        result = compare_posterior_arrays(local, external)["parameters"]["r"]
        self.assertAlmostEqual(result["standardized_mean_difference"], 0.)
        self.assertAlmostEqual(result["intervals"]["0.94"]["width_ratio_external_local"], 3.)
        self.assertTrue(result["material_discrepancy_flag"])

    def test_juliet_rng_introspection_bridge_delegates_and_restores(self):
        class SamplerBase:
            def __init__(self, *, rstate):
                self.rstate = rstate

        class InheritedSampler(SamplerBase):
            pass

        module = SimpleNamespace(NestedSampler=InheritedSampler)
        generator = np.random.default_rng(7)
        with patch.dict(sys.modules, {"dynesty": module}):
            with dynesty_rng_bridge():
                cls = module.NestedSampler
                self.assertIn("rstate", vars(cls)["__init__"].__code__.co_varnames)
                self.assertIs(cls(rstate=generator).rstate, generator)
                with self.assertRaisesRegex(ValueError, "seeded"):
                    cls()
            self.assertIs(module.NestedSampler, InheritedSampler)

    def test_undefined_temporal_check_cannot_pass_predictive_gate(self):
        metrics = {"posterior_predictive_interval_94_coverage_observed_points": .94,
                   "standardized_residual_std": 1.}
        self.assertFalse(predictive_gate(metrics, {"flagged": False}))
        self.assertFalse(predictive_gate(metrics, {"flagged": False, "assessable": False}))
        self.assertTrue(predictive_gate(metrics, {"flagged": False, "assessable": True}))


if __name__ == "__main__":
    unittest.main()
