"""Regression tests for content-bound Gold identity and manifest metadata."""

from __future__ import annotations

import json
import logging
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    import numpy as np
    import pandas as pd

    from gold_processing.lightcurve_preparation import (
        build_segment_normalized_lightcurve,
        normalize_segments_dataframe,
        normalized_content_sha256,
        read_normalized_signature_frame,
    )
    from gold_processing.manifests import GoldManifest
    from gold_processing.utils import read_csv
    from scripts.validate_hardened_artifacts import validate_gold_content_signature
except ImportError as exc:  # pragma: no cover - depends on scientific environment
    SCIENTIFIC_IMPORT_ERROR = exc
else:
    SCIENTIFIC_IMPORT_ERROR = None


@unittest.skipIf(
    SCIENTIFIC_IMPORT_ERROR is not None,
    f"scientific environment unavailable: {SCIENTIFIC_IMPORT_ERROR}",
)
class GoldDatasetManifestTests(unittest.TestCase):
    def test_metadata_manifest_count_and_content_bound_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            gold_root = root / "data" / "gold"
            phase_path = gold_root / "kepler_10_b" / "modeling" / "phase.csv"
            phase_path.parent.mkdir(parents=True)
            phase = np.linspace(-0.2, 0.2, 51)
            parts = []
            for index, checksum in enumerate(("a" * 64, "b" * 64), start=1):
                parts.append(
                    pd.DataFrame(
                        {
                            "segment_id": f"kepler:q{index}.fits",
                            "source_fits_file": f"q{index}.fits",
                            "source_fits_sha256": checksum,
                            "source_raw_path": f"data/raw/q{index}.fits",
                            "phase": phase,
                            "time": phase + index,
                            "flux": np.where(np.abs(phase) < 0.02, 999.8, 1000.0),
                            "flux_err": 0.1,
                            "exposure_time_seconds": 58.8488,
                            "cadence_type": "short",
                            "quarter": index,
                        }
                    )
                )
            pd.concat(parts, ignore_index=True).to_csv(phase_path, index=False)
            config = SimpleNamespace(
                PROJECT_ROOT=root,
                GOLD_DATA_DIR=gold_root,
                DATASET_SCHEMA_VERSION="2",
                SEGMENT_BASELINE_DURATION_MULTIPLIER=2.0,
                SEGMENT_MIN_BASELINE_POINTS=20,
                SEGMENT_NORMALIZATION_METHOD="out_of_transit_median",
                NORMALIZATION_POLICY="fixture policy",
            )
            selected = {
                "selected_planet_slug": "kepler_10_b",
                "selected_planet_name": "Kepler-10 b",
                "selected_host_star": "Kepler-10",
            }
            reference = pd.DataFrame(
                [{"transit_duration_hours": 1.0, "orbital_period_days": 0.8374907}]
            )
            manifest = GoldManifest(config)
            result = build_segment_normalized_lightcurve(
                config=config,
                selected=selected,
                reference=reference,
                phase_result={"created": True, "path": phase_path},
                manifest=manifest,
                logger=logging.getLogger("gold-dataset-test"),
            )

            metadata = json.loads(result["metadata_path"].read_text(encoding="utf-8"))
            persisted = read_normalized_signature_frame(result["path"])
            expected, _ = normalize_segments_dataframe(
                read_csv(phase_path),
                transit_exclusion_half_width_days=1.0 / 24.0,
                min_baseline_points=20,
            )
            pd.testing.assert_frame_equal(
                expected,
                persisted.loc[:, expected.columns],
                check_dtype=False,
                check_exact=True,
            )
            metadata_row = next(
                row
                for row in manifest.rows
                if row["transformation_type"] == "gold_dataset_metadata"
            )
            self.assertEqual(metadata_row["column_count"], len(metadata))
            self.assertRegex(metadata["normalized_content_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(
                normalized_content_sha256(persisted),
                metadata["normalized_content_sha256"],
            )
            _, present_status = validate_gold_content_signature(
                normalized_path=result["path"],
                diagnostics=pd.read_csv(result["diagnostics_path"]),
                metadata=metadata,
                planet_slug="kepler_10_b",
            )
            result["path"].unlink()
            _, absent_status = validate_gold_content_signature(
                normalized_path=result["path"],
                diagnostics=pd.read_csv(result["diagnostics_path"]),
                metadata=metadata,
                planet_slug="kepler_10_b",
            )
            self.assertEqual(present_status, "recomputed_from_local_normalized_artifact")
            self.assertIn("excluded_by_storage_policy", absent_status)
            self.assertEqual(
                {segment["source_fits_sha256"] for segment in metadata["segments"]},
                {"a" * 64, "b" * 64},
            )


if __name__ == "__main__":
    unittest.main()
