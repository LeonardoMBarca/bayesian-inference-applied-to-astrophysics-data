from __future__ import annotations

import hashlib
import io
import math
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from publication.trace_audit import (
    Sources,
    aggregate,
    audit_trace,
    build_audit,
    compare_parameter,
    joint_pass,
    operational_yield,
    safe_file,
    score_interval,
    summarize_counts,
    summarize_draws,
)


def record(identifier="one", *, status="COMPLETED", sampler=True, ppc=True, truth=1.5):
    values = summarize_draws([0, 1, 2, 3])
    values["truth"] = truth
    return {"job_id": identifier, "status": status,
            "gates": {"provenance": True, "sampler": sampler, "ppc": ppc, "scientific": ppc and sampler},
            "parameters": {"r": values}}


class IndependentTraceAuditTests(unittest.TestCase):
    def test_mean_sample_sd_and_interpolated_quantiles_by_hand(self):
        result = summarize_draws([0, 1, 2, 3])
        self.assertEqual(result["mean"], 1.5)
        self.assertAlmostEqual(result["sd"], math.sqrt(5 / 3))
        self.assertEqual(result["intervals"]["0.5"], [0.75, 2.25])
        np.testing.assert_allclose(result["intervals"]["0.8"], [0.3, 2.7], atol=1e-15)
        np.testing.assert_allclose(result["intervals"]["0.94"], [0.09, 2.91], atol=1e-15)

    def test_nonfinite_and_single_draw_are_not_silently_removed(self):
        for data in ([0], [0, np.nan], [1, np.inf]):
            with self.assertRaises(ValueError):
                summarize_draws(data)

    def test_skewed_sample_uses_mean_not_median_and_nonlinear_depth(self):
        radius = summarize_draws([1, 1, 1, 5])
        depth = summarize_draws([1, 1, 1, 25])
        self.assertEqual(radius["mean"], 2)
        self.assertEqual(depth["mean"], 7)
        self.assertNotEqual(depth["mean"], radius["mean"] ** 2)

    def test_wilson_boundaries_and_known_balanced_example(self):
        self.assertIsNone(score_interval(0, 0))
        self.assertEqual(score_interval(0, 100)[0], 0)
        self.assertAlmostEqual(score_interval(0, 100)[1], 0.03699349820698568)
        self.assertAlmostEqual(score_interval(100, 100)[0], 0.9630065017930143)
        self.assertAlmostEqual(score_interval(50, 100)[0], 0.4038315303659956)
        for args in ((-1, 3), (4, 3), (0, -1), (True, 3)):
            with self.assertRaises(ValueError):
                score_interval(*args)

    def test_rejected_numeric_draws_remain_and_selected_denominators_differ(self):
        rows = [record(), record("bad", status="COMPLETED_REJECTED", sampler=False, truth=10)]
        all_numeric = aggregate(rows, "r", "all_numeric")
        selected = aggregate(rows, "r", "sampler_passed")
        self.assertEqual(all_numeric["numeric_count"], 2)
        self.assertEqual(all_numeric["coverage"]["0.94"]["empirical_coverage"], 0.5)
        self.assertEqual(selected["numeric_count"], 1)
        self.assertEqual(selected["coverage"]["0.94"]["empirical_coverage"], 1)
        self.assertEqual(operational_yield(rows, "r")["0.94"]["rate"], 0.5)
        self.assertEqual(all_numeric["bias"], -4.25)
        self.assertAlmostEqual(all_numeric["rmse"], math.sqrt(8.5**2 / 2))

    def test_missing_is_not_measured_noncoverage_or_diagnostic_rejection(self):
        rows = [{"status": "FAILED_TECHNICAL", "parameters": {}, "gates": {}}]
        metrics = aggregate(rows, "r", "all_numeric")
        self.assertIsNone(metrics["bias"])
        self.assertIsNone(metrics["coverage"]["0.94"]["empirical_coverage"])
        self.assertIsNone(metrics["coverage"]["0.94"]["wilson95"])
        self.assertEqual(metrics["declared_count"], 1)
        self.assertEqual(metrics["numeric_count"], 0)
        self.assertEqual(summarize_counts(rows)["gates"]["sampler"], {"passed": 0, "rejected": 0, "unassessed": 1})
        self.assertEqual(operational_yield(rows, "r")["0.94"]["rate"], 0)

    def test_ppc_failure_is_not_numerical_failure_or_joint_success(self):
        row = record(status="COMPLETED_REJECTED", ppc=False)
        self.assertFalse(joint_pass(row))
        self.assertEqual(aggregate([row], "r", "sampler_passed")["numeric_count"], 1)
        self.assertEqual(aggregate([row], "r", "joint_gate_passed")["numeric_count"], 0)
        self.assertEqual(summarize_counts([row])["technical_failure_jobs"], 0)
        row["status"] = "COMPLETED"
        row["gates"] = {"sampler": True, "ppc": True, "scientific": True}
        self.assertFalse(joint_pass(row), "Provenance unavailable is not a pass")

    def test_relative_bias_undefined_at_zero_truth(self):
        metrics = aggregate([record(truth=0)], "r", "all_numeric")
        self.assertIsNone(metrics["relative_bias"])
        self.assertEqual(metrics["relative_bias_nonzero_truth_count"], 0)

    def test_summary_mismatch_and_hdi_mislabelling_detected(self):
        values = summarize_draws([1, 2, 3, 4])
        self.assertTrue(compare_parameter(values, values)["matched"])
        self.assertFalse(compare_parameter(values, {**values, "mean": 2.50001})["matched"])
        self.assertFalse(compare_parameter(values, {**values, "interval_method": "hdi"})["matched"])

    def test_checksum_content_tamper_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "result.json"
            path.write_bytes(b"original")
            sources = Sources(root)
            digest = hashlib.sha256(b"original").hexdigest()
            self.assertEqual(sources.read("result.json", digest), b"original")
            path.write_bytes(b"modified")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                sources.read("result.json", digest)
            with self.assertRaisesRegex(ValueError, "changed during audit"):
                sources.read("result.json")

    def test_path_traversal_rejected(self):
        root = Path(tempfile.gettempdir())
        for path in ("../private", "C:/private", "/private", "foo\\bar", ""):
            with self.assertRaises(ValueError):
                safe_file(root, path)

    def test_existing_audit_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "preserved_audit"
            output.mkdir()
            marker = output / "audit.json"
            marker.write_bytes(b"protected earlier result")
            with self.assertRaises(FileExistsError):
                build_audit(root, output)
            self.assertEqual(marker.read_bytes(), b"protected earlier result")

    def test_real_netcdf_all_chains_and_derived_geometry(self):
        radius = np.array([[0.1, 0.11], [0.12, 0.13]])
        impact = np.full_like(radius, 0.3)
        scale = np.full_like(radius, 5)
        duration = 2 / math.pi * np.arcsin(np.sqrt(((1 + radius)**2 - impact**2) / (scale**2 - impact**2)))
        arrays = {"r": radius, "depth": radius**2, "b": impact, "a": scale,
                  "t0": np.array([[0.001, 0.002], [1.001, 1.002]]),
                  "full_duration": duration, "extra_sigma": radius / 100}
        dataset = xr.Dataset({name: (("chain", "draw"), value) for name, value in arrays.items()})
        stream = io.BytesIO()
        dataset.to_netcdf(stream, group="posterior", engine="h5netcdf")
        values, derived = audit_trace(stream.getvalue(), 2)
        self.assertTrue(derived["depth_equals_squared_radius"])
        self.assertTrue(derived["duration_equals_circular_contact_formula"])
        self.assertEqual(values["r"]["draw_count"], 4)
        self.assertAlmostEqual(values["t0"]["mean"], 0.5015)
        np.testing.assert_allclose(derived["t0_chain_means_days"], [0.0015, 1.0015])

    def test_producer_modules_not_imported(self):
        import publication.trace_audit as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        for prohibited in ("from publication.calibration", "from publication.inference", "from publication.synthesis"):
            self.assertNotIn(prohibited, source)


if __name__ == "__main__":
    unittest.main()
