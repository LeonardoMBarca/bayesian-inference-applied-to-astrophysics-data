import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from publication.residual_review import segment_review, verify_prediction_input  # noqa: E402


class ResidualReviewTests(unittest.TestCase):
    def fixture(self):
        t = np.r_[np.arange(30), np.arange(30) + 100.]
        return pd.DataFrame({"time": t, "phase": np.linspace(-1, 1, 60),
                             "residual": np.sin(t), "posterior_mean": 1 - .01 * np.exp(-np.linspace(-4, 4, 60)**2),
                             "segment_id": ["a"] * 60, "exposure_time_seconds": [86400.] * 60})

    def test_order_invariance_and_gap_exclusion(self):
        frame = self.fixture()
        result = segment_review(frame, half_duration=.2)
        self.assertEqual(result, segment_review(frame.iloc[::-1], half_duration=.2))
        self.assertEqual(result["partitions"]["all"]["selected_lag_pairs"], 58)
        self.assertEqual(result["gaps_larger_than_1_5_selected_median"], 1)

    def test_mixed_segment_and_duplicate_time_reject(self):
        frame = self.fixture()
        frame.loc[0, "segment_id"] = "b"
        with self.assertRaises(ValueError):
            segment_review(frame, half_duration=.2)
        frame["segment_id"] = "a"
        frame.loc[0, "time"] = frame.time.iloc[1]
        with self.assertRaises(ValueError):
            segment_review(frame, half_duration=.2)

    def test_no_transit_points_is_unassessed_not_zero_correlation(self):
        result = segment_review(self.fixture(), half_duration=0.)
        self.assertEqual(result["partitions"]["in_transit"]["rows"], 0)
        self.assertIsNone(result["partitions"]["in_transit"]["selected_lag1"])

    def test_same_times_but_other_observed_flux_rejects(self):
        curve = self.fixture()
        curve["observed"] = curve.posterior_mean + curve.residual
        inputs = curve.copy()
        inputs["normalized_flux"] = curve.observed
        verify_prediction_input(inputs, curve)
        curve["observed"] += .01
        curve["residual"] += .01
        with self.assertRaises(AssertionError):
            verify_prediction_input(inputs, curve)
