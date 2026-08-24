from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    import numpy as np
    import pandas as pd

    from gold_processing.lightcurve_preparation import (
        build_gold_dataset_signature,
        dataset_id_from_signature,
        normalize_segments_dataframe,
    )
except ImportError as exc:  # pragma: no cover - depends on scientific environment
    SCIENTIFIC_IMPORT_ERROR = exc
else:
    SCIENTIFIC_IMPORT_ERROR = None


@unittest.skipIf(
    SCIENTIFIC_IMPORT_ERROR is not None,
    f"scientific environment unavailable: {SCIENTIFIC_IMPORT_ERROR}",
)
class SegmentNormalizationTests(unittest.TestCase):
    def test_offsets_are_removed_per_segment_without_losing_identity(self) -> None:
        phase = np.linspace(-0.2, 0.2, 51)
        first = pd.DataFrame(
            {
                "segment_id": "kepler:q1.fits",
                "source_fits_file": "q1.fits",
                "source_fits_sha256": "a" * 64,
                "quarter": 1,
                "phase": phase,
                "flux": np.where(np.abs(phase) < 0.02, 99.0, 100.0),
                "flux_err": 0.1,
                "exposure_time_seconds": 58.85,
                "cadence_type": "short",
            }
        )
        second = first.copy()
        second["segment_id"] = "kepler:q2.fits"
        second["source_fits_file"] = "q2.fits"
        second["source_fits_sha256"] = "b" * 64
        second["quarter"] = 2
        second["flux"] = np.where(np.abs(phase) < 0.02, 198.0, 200.0)
        normalized, diagnostics = normalize_segments_dataframe(
            pd.concat([first, second], ignore_index=True),
            transit_exclusion_half_width_days=0.03,
            min_baseline_points=20,
        )
        self.assertEqual(normalized["segment_id"].nunique(), 2)
        self.assertEqual(normalized["source_fits_file"].nunique(), 2)
        baselines = normalized.groupby("segment_id")["segment_baseline_flux"].first()
        self.assertEqual(set(baselines), {100.0, 200.0})
        self.assertTrue(
            np.allclose(diagnostics["normalized_baseline_median"].to_numpy(), 1.0)
        )
        self.assertEqual(set(normalized["preprocessing_status"]), {"segment_normalized"})
        signature = build_gold_dataset_signature(
            normalized=normalized,
            diagnostics=diagnostics,
            schema_version="2",
            planet_slug="kepler_10_b",
            orbital_period_days=0.8374907,
            normalization_method="out_of_transit_median",
            transit_exclusion_half_width_days=0.03,
        )
        self.assertEqual(
            {segment["source_fits_sha256"] for segment in signature["segments"]},
            {"a" * 64, "b" * 64},
        )
        self.assertRegex(signature["normalized_content_sha256"], r"^[0-9a-f]{64}$")

        changed = normalized.copy()
        changed.loc[changed["segment_id"] == "kepler:q2.fits", "source_fits_sha256"] = (
            "c" * 64
        )
        changed_diagnostics = diagnostics.copy()
        changed_diagnostics.loc[
            changed_diagnostics["segment_id"] == "kepler:q2.fits",
            "source_fits_sha256",
        ] = "c" * 64
        changed_signature = build_gold_dataset_signature(
            normalized=changed,
            diagnostics=changed_diagnostics,
            schema_version="2",
            planet_slug="kepler_10_b",
            orbital_period_days=0.8374907,
            normalization_method="out_of_transit_median",
            transit_exclusion_half_width_days=0.03,
        )
        self.assertNotEqual(
            dataset_id_from_signature("kepler_10_b", signature),
            dataset_id_from_signature("kepler_10_b", changed_signature),
        )

    def test_missing_exposure_fails_loudly(self) -> None:
        frame = pd.DataFrame(
            {
                "segment_id": ["one"] * 21,
                "source_fits_file": ["one.fits"] * 21,
                "source_fits_sha256": ["d" * 64] * 21,
                "phase": np.linspace(-0.2, 0.2, 21),
                "flux": np.ones(21),
                "flux_err": np.full(21, 0.01),
                "exposure_time_seconds": np.nan,
            }
        )
        with self.assertRaisesRegex(ValueError, "positive exposure"):
            normalize_segments_dataframe(
                frame,
                transit_exclusion_half_width_days=0.02,
                min_baseline_points=10,
            )


if __name__ == "__main__":
    unittest.main()
