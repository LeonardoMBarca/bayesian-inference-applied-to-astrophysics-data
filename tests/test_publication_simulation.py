from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from publication.calibration import coverage_metrics, wilson_interval
from publication.simulation import TransitTruth, physical_flux, simulate


class SyntheticTransitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.truth = {"r": 0.08, "b": 0.35, "a": 8.0, "period_days": 2.0}
        self.design = {
            "window_days": 0.12, "cadence_seconds": 600.0,
            "exposure_time_seconds": 580.0, "measurement_sigma": 0.0001,
            "segments": 2, "transits_per_segment": 2,
        }

    def test_uniform_star_analytic_depth_and_out_of_transit_baseline(self) -> None:
        truth = TransitTruth(**{**self.truth, "q1": 0.0, "baseline": 1.0002})
        flux = physical_flux(np.array([-0.2, 0.0, 0.2]), 0.0, truth)
        np.testing.assert_allclose(flux[[0, 2]], truth.baseline, atol=1e-13, rtol=0)
        self.assertAlmostEqual(truth.baseline - flux[1], truth.r**2, places=11)

    def test_geometric_duration_matches_contact_locations(self) -> None:
        truth = TransitTruth(**{**self.truth, "q1": 0.0})
        contact = truth.full_duration / 2
        flux = physical_flux(np.array([contact * 0.99, contact * 1.01]), 0.0, truth)
        self.assertLess(flux[0], 1.0)
        self.assertAlmostEqual(flux[1], 1.0, places=12)
        central = TransitTruth(**{**self.truth, "b": 0.0})
        expected = 2.0 / np.pi * np.arcsin(1.08 / 8.0)
        self.assertAlmostEqual(central.full_duration, expected, places=15)

    def test_finite_exposure_matches_numerical_integral(self) -> None:
        truth = TransitTruth(**self.truth)
        center = truth.full_duration / 2
        exposure = 1800.0
        times = np.linspace(center - exposure / 172800, center + exposure / 172800, 2001)
        instantaneous = physical_flux(times, 0.0, truth)
        numerical_mean = np.trapezoid(instantaneous, times) / (times[-1] - times[0])
        integrated = physical_flux(np.array([center]), exposure, truth, oversample=101)[0]
        self.assertAlmostEqual(integrated, numerical_mean, delta=2e-7)
        at_contact = physical_flux(np.array([center]), 0, truth)[0]
        self.assertGreater(at_contact - integrated, 1e-5)

    def test_seed_determinism_independence_and_no_input_mutation(self) -> None:
        before = copy.deepcopy((self.truth, self.design))
        first, metadata = simulate(self.truth, self.design, 412)
        again, again_metadata = simulate(self.truth, self.design, 412)
        other, other_metadata = simulate(self.truth, self.design, 413)
        pd.testing.assert_frame_equal(first, again)
        self.assertEqual(metadata, again_metadata)
        self.assertEqual(before, (self.truth, self.design))
        self.assertNotEqual(metadata["data_sha256"], other_metadata["data_sha256"])
        self.assertEqual(metadata["truth_sha256"], other_metadata["truth_sha256"])
        self.assertFalse(np.array_equal(first.normalized_flux, other.normalized_flux))
        self.assertEqual(hashlib.sha256(first.to_csv(index=False, float_format="%.17g", lineterminator="\n").encode()).hexdigest(), metadata["data_sha256"])
        json.dumps(metadata, allow_nan=False)

    def test_truth_and_noise_realizations_never_enter_inference_frame(self) -> None:
        frame, metadata = simulate(self.truth, self.design, 2)
        self.assertEqual(set(frame.columns), {
            "phase", "time", "normalized_flux", "normalized_flux_err",
            "exposure_time_seconds", "segment_id",
        })
        self.assertEqual(metadata["truth"]["depth"], self.truth["r"] ** 2)
        reconstructed = sum(np.asarray(values) for values in metadata["components"].values())
        np.testing.assert_allclose(reconstructed, frame.normalized_flux, atol=0, rtol=0)

    def test_actual_cadence_segment_identity_and_exposure(self) -> None:
        frame, _ = simulate(self.truth, self.design, 2)
        self.assertTrue((np.diff(frame.time) > 0).all())
        self.assertEqual(frame.segment_id.nunique(), 2)
        for _, segment in frame.groupby("segment_id"):
            steps = np.diff(segment.time) * 86400 / self.design["cadence_seconds"]
            np.testing.assert_allclose(steps, np.round(steps), atol=1e-10)
            self.assertAlmostEqual(segment.normalized_flux_err.min(), 0.8e-4)
            self.assertAlmostEqual(segment.normalized_flux_err.max(), 1.2e-4)
        self.assertTrue((frame.exposure_time_seconds == 580.0).all())
        # Consecutive transits retain different sampling phases because period
        # is not an integer number of cadences in this independent design.
        shifted = {**self.truth, "period_days": 2.003}
        frame, _ = simulate(shifted, self.design, 2)
        segment = frame[frame.segment_id == "synthetic_segment_000"]
        nearest = [segment.loc[abs(segment.time - center).idxmin(), "phase"] for center in (0, 2.003)]
        self.assertNotAlmostEqual(nearest[0], nearest[1], places=5)

    def test_segment_scaling_propagates_uncertainty_and_jitter_is_separate(self) -> None:
        frame, metadata = simulate(
            {**self.truth, "extra_sigma": 0.0003},
            {**self.design, "include_raw_flux": True, "segment_offsets": [0.98, 1.02]}, 10,
        )
        for (_, segment), factor in zip(frame.groupby("segment_id"), (0.98, 1.02), strict=True):
            np.testing.assert_allclose(segment.raw_flux / segment.normalized_flux, factor)
            np.testing.assert_allclose(segment.raw_flux_err / segment.normalized_flux_err, factor)
        self.assertGreater(np.std(metadata["components"]["white_jitter"]), 0)
        np.testing.assert_array_equal(metadata["components"]["correlated_stochastic"], np.zeros(len(frame)))

    def test_ou_and_ar1_match_on_the_same_regular_clock_and_preserve_gaps(self) -> None:
        rho = 0.85
        timescale = -(600 / 86400) / np.log(rho)
        _, ou = simulate(self.truth, {**self.design, "noise": {"kind": "ou", "amplitude_fraction": 0.0002, "timescale_days": timescale}}, 123)
        _, ar1 = simulate(self.truth, {**self.design, "noise": {"kind": "ar1", "amplitude_fraction": 0.0002, "rho": rho}}, 123)
        np.testing.assert_allclose(ou["components"]["correlated_stochastic"], ar1["components"]["correlated_stochastic"], atol=1e-16)
        self.assertTrue(np.any(np.asarray(ou["components"]["correlated_stochastic"]) != 0))

    def test_sinusoid_is_deterministic_not_a_correlated_likelihood(self) -> None:
        design = {**self.design, "systematic": {"amplitude_fraction": 0.002, "period_days": 0.13}}
        frame, metadata = simulate(self.truth, design, 1)
        _, other = simulate(self.truth, design, 2)
        systematic = metadata["components"]["deterministic_systematic"]
        self.assertEqual(systematic, other["components"]["deterministic_systematic"])
        np.testing.assert_allclose(systematic, 0.002 * np.sin(2 * np.pi * frame.time / 0.13))

    def test_invalid_geometry_configuration_and_exposure_fail_loudly(self) -> None:
        for changes in ({"b": 1.1}, {"a": 0.9}, {"r": -0.1}, {"q1": 2}, {"period_days": 0}, {"extra_sigma": -1}, {"t0": float("nan")}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                simulate({**self.truth, **changes}, self.design, 1)
        for changes in ({"exposure_time_seconds": 601}, {"segments": 0}, {"window_days": 1.1}, {"measurement_sigma": 0}, {"oversample": 2}, {"unknown": 3}, {"noise": {"kind": "ar1", "rho": 1, "amplitude_fraction": 1e-4}}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                simulate(self.truth, {**self.design, **changes}, 1)


class CalibrationSummaryTests(unittest.TestCase):
    @staticmethod
    def record(identifier: str, *, mean: float = 2.0, truth: float = 1.0, gate: bool = True, status: str = "completed") -> dict:
        return {
            "replicate_id": identifier, "status": status,
            "gates": {"sampler": True, "ppc": gate, "scientific": gate},
            "parameters": {"r": {"truth": truth, "mean": mean, "sd": 0.5,
                                   "intervals": {"0.5": [1.5, 2.5], "0.8": [1.0, 3.0], "0.94": [0.5, 3.5]}}},
        }

    def test_coverage_counts_boundaries_and_denominators_include_failures(self) -> None:
        records = [self.record("one"), self.record("two", mean=0.0, gate=False, status="rejected"),
                   {"replicate_id": "three", "status": "failed"}]
        summary = coverage_metrics(records, ["one", "two", "three", "four"], parameter_names=["r"])
        result = summary["parameters"]["r"]
        self.assertEqual(result["bias"], 0.0)
        self.assertEqual(result["absolute_bias"], 0.0)
        self.assertEqual(result["mae"], 1.0)
        self.assertEqual(result["rmse"], 1.0)
        self.assertEqual(result["numeric_count"], 2)
        self.assertEqual(result["coverage"]["0.5"]["empirical_coverage_numeric"], 0.0)
        self.assertEqual(result["coverage"]["0.8"]["empirical_coverage_numeric"], 1.0)
        self.assertEqual(result["coverage"]["0.8"]["operational_covered_and_passed_rate_all_declared"], 0.25)
        self.assertEqual(result["coverage"]["0.8"]["coverage_conditional_on_scientific_gate"], 1.0)
        self.assertEqual(summary["missing_ids"], ["four"])
        self.assertEqual(summary["execution_failure_rate_all_declared"], 0.25)
        self.assertEqual(summary["gates"]["scientific"]["rejection_rate_all_declared"], 0.25)

    def test_failed_pilot_partial_results_never_count_as_final_numeric_posteriors(self) -> None:
        records = [self.record("pilot", status="pilot"), self.record("failed", status="failed")]
        summary = coverage_metrics(records, ["pilot", "failed"])
        self.assertEqual(summary["parameters"]["r"]["numeric_count"], 0)
        self.assertEqual(summary["gates"]["sampler"]["passed_count"], 0)
        json.dumps(summary, allow_nan=False)

    def test_operational_success_fails_closed_for_inconsistent_status_and_gates(self) -> None:
        bad_status = self.record("rejected", status="rejected")
        bad_sampler = self.record("sampler_failed")
        bad_sampler["gates"]["sampler"] = False
        summary = coverage_metrics([bad_status, bad_sampler], ["rejected", "sampler_failed"])
        level = summary["parameters"]["r"]["coverage"]["0.94"]
        self.assertEqual(level["empirical_coverage_numeric"], 1.0)
        self.assertEqual(level["operational_covered_and_passed_rate_all_declared"], 0.0)

    def test_wilson_intervals_match_known_values_and_do_not_shrink_to_zero(self) -> None:
        np.testing.assert_allclose(wilson_interval(5, 10), [0.2365930905, 0.7634069095], atol=1e-9)
        self.assertGreater(wilson_interval(0, 10)[1], 0.27)
        self.assertLess(wilson_interval(10, 10)[0], 0.73)
        self.assertIsNone(wilson_interval(0, 0))
        with self.assertRaises(ValueError):
            wilson_interval(11, 10)

    def test_zero_truth_relative_bias_undefined_and_invalid_parameter_accounted(self) -> None:
        good = self.record("one", truth=0.0)
        bad = self.record("two")
        bad["parameters"]["r"]["mean"] = float("nan")
        summary = coverage_metrics([good, bad], ["one", "two"])
        self.assertIsNone(summary["parameters"]["r"]["relative_bias"])
        self.assertEqual(summary["parameters"]["r"]["missing_or_invalid_count"], 1)
        json.dumps(summary, allow_nan=False)

    def test_duplicate_undeclared_and_string_gates_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            coverage_metrics([self.record("one"), self.record("one")], ["one"])
        with self.assertRaises(ValueError):
            coverage_metrics([self.record("two")], ["one"])
        wrong = self.record("one")
        wrong["gates"]["scientific"] = "false"
        with self.assertRaises(ValueError):
            coverage_metrics([wrong], ["one"])


if __name__ == "__main__":
    unittest.main()
