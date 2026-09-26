"""Regression tests for paired interventions, not scientific inference results."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from publication.ablations import (  # noqa: E402
    INTERVENTIONS,
    apply_ablation,
    estimate_normalization,
    frame_sha256,
    paired_generation_seed,
)
from publication.inference import read_input  # noqa: E402


def fixture() -> tuple[pd.DataFrame, dict]:
    phase = np.array([-.15, -.12, -.10, -.04, .04, .10, .12, .15])
    # Exactly-at-cutoff large values must not enter OOT calibration. The noisy
    # observed median 101 differs from a hypothetical true segment factor 100.
    raw = np.array([100., 102., 5000., 95., 95., 5000., 104., 98.])
    frame = pd.DataFrame({"phase": np.tile(phase, 2), "time": np.r_[phase, phase + 2.],
                          "segment_id": ["a"]*8 + ["b"]*8, "exposure_time_seconds": 1765.,
                          "raw_flux": np.r_[raw, raw*2], "raw_flux_err": np.r_[np.ones(8), np.full(8, 2.)],
                          "normalized_flux": -999., "normalized_flux_err": -999.})
    config = {"input_kind": "synthetic", "period_days": 1., "integrate_exposure": True,
              "infer_jitter": True, "radius_prior_median": .04, "radius_prior_log_sigma": .9,
              "baseline_prior_sigma": .02, "sampling": {"draws": 1000, "tune": 1000, "chains": 4,
                                                         "cores": 4, "target_accept": .95}}
    return frame, config


class PublicationAblationTests(unittest.TestCase):
    def test_normalization_uses_noisy_observed_oot_medians_not_existing_calibration(self) -> None:
        raw, _ = fixture()
        normalized, metadata = estimate_normalization(raw)
        self.assertEqual([item["raw_oot_median"] for item in metadata["estimated_factors"]], [101., 202.])
        self.assertEqual([item["oot_count"] for item in metadata["estimated_factors"]], [4, 4])
        np.testing.assert_allclose(normalized.normalized_flux[:8], raw.raw_flux[:8]/101.)
        np.testing.assert_allclose(normalized.normalized_flux[8:], raw.raw_flux[8:]/202.)
        np.testing.assert_allclose(normalized.normalized_flux_err, 1./101.)
        self.assertFalse(metadata["normalization_uncertainty_propagated"])

    def test_global_alternative_is_empirical_and_preserves_raw_error_rows_metadata(self) -> None:
        raw, _ = fixture()
        raw.index = [0, 0, 1, 1, 2, 2, 3, 3]*2  # Position-based grouping survives duplicate indices.
        before = raw.copy(deep=True)
        normalized, metadata = estimate_normalization(raw, method="global")
        self.assertEqual(metadata["estimated_factors"][0]["raw_oot_median"], 150.)
        np.testing.assert_allclose(normalized.normalized_flux, raw.raw_flux/150.)
        np.testing.assert_allclose(normalized.normalized_flux_err, raw.raw_flux_err/150.)
        for column in raw.columns.difference(["normalized_flux", "normalized_flux_err"]):
            pd.testing.assert_series_equal(normalized[column], raw[column])
        pd.testing.assert_frame_equal(raw, before)

    def test_model_only_ablations_change_only_predeclared_fields_and_share_bytes(self) -> None:
        raw, config = fixture()
        original_config = copy.deepcopy(config)
        original_frame = raw.copy(deep=True)
        baseline, base = apply_ablation(raw, config, "baseline")
        expected_fields = {"exposure_off": {"integrate_exposure"}, "no_jitter": {"infer_jitter"},
                           "strong_wrong_radius_prior": {"radius_prior_median", "radius_prior_log_sigma"},
                           "invalid_input_hash": {"input_sha256"}, "dataset_identity_mismatch": {"expected_dataset_id"},
                           "insufficient_sampling": {"sampling"}}
        for intervention, fields in expected_fields.items():
            with self.subTest(intervention=intervention):
                frame, altered = apply_ablation(raw, config, intervention)
                pd.testing.assert_frame_equal(frame, baseline)
                self.assertEqual(frame_sha256(frame), frame_sha256(baseline))
                self.assertEqual({key for key in base if base[key] != altered[key]}, fields)
        self.assertEqual(config, original_config)
        pd.testing.assert_frame_equal(raw, original_frame)

    def test_global_intervention_rebinds_actual_data_identity_and_honest_status(self) -> None:
        raw, config = fixture()
        baseline, base = apply_ablation(raw, config, "baseline")
        altered, actual = apply_ablation(raw, config, "global_normalization")
        self.assertNotEqual(frame_sha256(baseline), frame_sha256(altered))
        self.assertEqual(actual["input_sha256"], frame_sha256(altered))
        self.assertEqual(actual["dataset_id"], actual["expected_dataset_id"])
        self.assertEqual(actual["dataset_id"], "synthetic-" + frame_sha256(altered)[:20])
        self.assertEqual(actual["preprocessing_status"], "global_normalized_negative_control")
        self.assertEqual({key for key in base if base[key] != actual[key]},
                         {"input_sha256", "dataset_id", "expected_dataset_id", "preprocessing_status"})

    def test_identity_controls_fail_in_existing_reader_before_inference(self) -> None:
        raw, config = fixture()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            for intervention in ("baseline", "invalid_input_hash", "dataset_identity_mismatch"):
                normalized, altered = apply_ablation(raw, config, intervention)
                normalized.to_csv(path, index=False, float_format="%.17g", lineterminator="\n")
                if intervention == "baseline":
                    self.assertEqual(len(read_input(path, altered)), len(normalized))
                else:
                    with self.subTest(intervention=intervention), self.assertRaises(ValueError):
                        read_input(path, altered)

    def test_under_sampling_preserves_chains_target_accept_and_other_priors(self) -> None:
        raw, config = fixture()
        _, baseline = apply_ablation(raw, config, "baseline")
        _, altered = apply_ablation(raw, config, "insufficient_sampling")
        self.assertEqual(altered["sampling"]["draws"], 20)
        self.assertEqual(altered["sampling"]["tune"], 20)
        self.assertEqual(altered["sampling"]["chains"], 4)
        self.assertEqual({key for key in baseline["sampling"] if baseline["sampling"][key] != altered["sampling"][key]}, {"draws", "tune"})

    def test_seed_is_pair_bound_and_independent_across_replicates(self) -> None:
        self.assertEqual(paired_generation_seed("PUB-04", "long_segment_offsets", "rep_0000"),
                         paired_generation_seed("PUB-04", "long_segment_offsets", "rep_0000"))
        seeds = {paired_generation_seed("PUB-04", "long_segment_offsets", f"rep_{index:04d}") for index in range(10)}
        self.assertEqual(len(seeds), 10)
        self.assertNotEqual(paired_generation_seed("PUB-04", "short_temporal_systematic", "rep_0000"),
                            paired_generation_seed("PUB-04", "long_segment_offsets", "rep_0000"))

    def test_normalization_rejects_missing_provenance_or_oot_information(self) -> None:
        raw, config = fixture()
        for modified in (raw.drop(columns="raw_flux"), raw.assign(segment_id=None),
                         raw.assign(phase=0.), raw.assign(raw_flux_err=0.)):
            with self.assertRaises(ValueError):
                estimate_normalization(modified)
        with self.assertRaises(ValueError):
            apply_ablation(raw, config, {"name": "baseline", "true_segment_offsets": [.98, 1., 1.02]})
        with self.assertRaises(ValueError):
            apply_ablation(raw, {**config, "input_kind": "observational"}, "baseline")

    def test_protocol_remains_draft_and_predeclares_all_controls_without_execution(self) -> None:
        protocol = json.loads((ROOT / "publication/protocols/PUB-04-draft.json").read_text(encoding="utf-8"))
        self.assertEqual(protocol["protocol_status"], "DRAFT")
        self.assertFalse(protocol["execution_authorized"])
        self.assertEqual(set(protocol["paired_designs"][0]["variants"]), INTERVENTIONS)
        self.assertEqual(protocol["replication_plan"]["total_declared_attempts_if_frozen_unchanged"], 100)
        self.assertEqual(protocol["normalization"]["oot_mask"], "abs(phase_days) > 0.10")


if __name__ == "__main__":
    unittest.main()
