from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.io import fits

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from project_config import get_target  # noqa: E402
from publication.observational import (  # noqa: E402
    prepare_target,
    target_outcome_table,
    target_registry,
    verify_prepared_target,
)


def synthetic_fits(path: Path, *, target_id: int = 10666592, scale: float = 1000.0,
                   mission: str = "Kepler", period: float = 2.20474,
                   epoch: float = 2454954.358572, reference: float = 2454833,
                   exposure: float = 1765.462885941888) -> str:
    """Independent small RAW fixture; not an observational/scientific batch."""
    primary = fits.PrimaryHDU()
    primary.header["TELESCOP"] = mission
    primary.header["KEPLERID" if mission == "Kepler" else "TICID"] = target_id
    primary.header["QUARTER" if mission == "Kepler" else "SECTOR"] = 1
    times = epoch - reference + np.linspace(-period / 2 + .01, period / 2 - .01, 181)
    flux = np.full(len(times), scale)
    flux[np.abs(times - (epoch - reference)) < .05] *= .99
    quality = np.zeros(len(times), dtype=np.int32)
    quality[0] = 1
    flux[1] = np.nan
    columns = [fits.Column(name="TIME", format="D", array=times),
               fits.Column(name="PDCSAP_FLUX", format="D", array=flux),
               fits.Column(name="PDCSAP_FLUX_ERR", format="D", array=np.full(len(times), scale * .001)),
               fits.Column(name="SAP_QUALITY", format="J", array=quality),
               fits.Column(name="CADENCENO", format="J", array=np.arange(len(times)))]
    table = fits.BinTableHDU.from_columns(columns)
    table.header["BJDREFI"] = reference
    table.header["BJDREFF"] = 0
    table.header["TIMESYS"] = "TDB"
    table.header["TIMEUNIT"] = "d"
    table.header["TIMEDEL"] = exposure / 86400
    path.parent.mkdir(parents=True, exist_ok=True)
    fits.HDUList([primary, table]).writeto(path, overwrite=False)
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PublicationObservationalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol = json.loads((PROJECT_ROOT / "publication/protocols/PUB-05-draft.json").read_text(encoding="utf-8"))

    def fixture_protocol(self, root: Path, slug: str = "hat_p_7_b", **kwargs) -> tuple[dict, Path, str]:
        protocol = copy.deepcopy(self.protocol)
        entry = next(entry for entry in protocol["targets"] if entry["config"]["planet_slug"] == slug)
        config = entry["config"]
        path = root / "raw_fixtures" / slug / "lightcurve.fits"
        checksum = synthetic_fits(
            path, target_id=entry["archive_identity"]["value"], mission=config["mission"],
            period=config["orbital_period_days"], epoch=config["transit_midpoint_bjd"],
            reference=entry["time_reference_bjd"], **kwargs,
        )
        entry["sources"] = [{"path": path.relative_to(root).as_posix(), "sha256": checksum}]
        entry["expected_source_count"] = 1
        protocol["preprocessing"]["max_points_per_segment"] = 100
        return protocol, path, checksum

    def test_preselected_registry_contains_five_including_unchanged_anchors(self) -> None:
        registry = target_registry(self.protocol)
        self.assertEqual(set(registry), {"hat_p_7_b", "kepler_10_b", "tres_2_b", "hd_189733_b", "kepler_4_b"})
        for slug in ("hat_p_7_b", "kepler_10_b"):
            existing = get_target(slug)
            for key, value in registry[slug]["config"].items():
                self.assertEqual(value, getattr(existing, key))
        self.assertEqual(registry["kepler_4_b"]["config"]["orbital_period_days"], 3.213668926)
        self.assertEqual(registry["kepler_4_b"]["config"]["transit_midpoint_bjd"], 2454833 + 123.611878)

    def test_all_target_outcomes_include_failures_and_missing_without_replacement(self) -> None:
        rows = target_outcome_table(self.protocol, [
            {"target_id": "hat_p_7_b", "status": "completed"},
            {"target_id": "kepler_4_b", "status": "failed", "reason": "data_access"},
        ])
        self.assertEqual(len(rows), 5)
        self.assertEqual(sum(row["status"] == "missing" for row in rows), 3)
        self.assertEqual(rows[-1]["status"], "failed")
        altered = copy.deepcopy(self.protocol)
        altered["targets"].pop()
        with self.assertRaises(ValueError):
            target_registry(altered)
        with self.assertRaises(ValueError):
            target_outcome_table(self.protocol, [{"target_id": "unselected", "status": "completed"}])

    def test_shared_preparation_isolated_reproducible_and_scales_errors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            protocol, source, checksum = self.fixture_protocol(root)
            before = copy.deepcopy(protocol)
            first = prepare_target(root, protocol, "hat_p_7_b", "fixture_one", allow_draft=True)
            second = prepare_target(root, protocol, "hat_p_7_b", "fixture_two", allow_draft=True)
            self.assertEqual(first["status"], "completed")
            self.assertEqual(first["purpose"], "PILOT")
            self.assertEqual(first["dataset_id"], second["dataset_id"])
            self.assertEqual(first["input_sha256"], second["input_sha256"])
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), checksum)
            self.assertEqual(protocol, before)
            self.assertFalse((root / "data/silver").exists())
            self.assertFalse((root / "data/gold").exists())
            self.assertEqual(first["quality_removed_count"], 2)
            model_input = pd.read_csv(root / first["output_directory"] / "model_input.csv")
            np.testing.assert_allclose(model_input.normalized_flux_err, .001)
            self.assertTrue(set(["source_row_index", "source_fits_sha256", "segment_id", "phase", "time"]).issubset(model_input))
            self.assertEqual(set(model_input.planet_slug), {"hat_p_7_b"})
            self.assertEqual(first["source_artifacts"][0]["sha256"], checksum)
            validation = verify_prepared_target(root, first)
            self.assertTrue(validation["all_row_dataset_and_target_ids_match"])
            self.assertFalse(validation["sampler_executed"])
            with self.assertRaises(FileExistsError):
                prepare_target(root, protocol, "hat_p_7_b", "fixture_one", allow_draft=True)

    def test_draft_final_and_target_path_mismatches_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            protocol, _, _ = self.fixture_protocol(root)
            with self.assertRaises(ValueError):
                prepare_target(root, protocol, "hat_p_7_b", "final_one")
            with self.assertRaises(ValueError):
                prepare_target(root, protocol, "hat_p_7_b", "../main", allow_draft=True)
            with self.assertRaises(ValueError):
                prepare_target(root, protocol, "not_selected", "fixture", allow_draft=True)
            entry = next(entry for entry in protocol["targets"] if entry["config"]["planet_slug"] == "hat_p_7_b")
            entry["archive_identity"]["value"] = 11904151
            with self.assertRaisesRegex(ValueError, "target identity mismatch"):
                prepare_target(root, protocol, "hat_p_7_b", "wrong_target", allow_draft=True)
            manifest = json.loads((root / "publication/observational/PUB-05/hat_p_7_b/wrong_target/preparation_manifest.json").read_text())
            self.assertEqual(manifest["status"], "failed")

    def test_invalid_hash_rejected_before_extraction_and_failure_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            protocol, _, _ = self.fixture_protocol(root)
            entry = next(entry for entry in protocol["targets"] if entry["config"]["planet_slug"] == "hat_p_7_b")
            entry["sources"][0]["sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                prepare_target(root, protocol, "hat_p_7_b", "bad_hash", allow_draft=True)
            output = root / "publication/observational/PUB-05/hat_p_7_b/bad_hash"
            self.assertTrue((output / "preparation_manifest.json").exists())
            self.assertFalse((output / "silver_lightcurve.csv").exists())

    def test_tess_reference_and_cadence_roundoff_use_same_shared_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            protocol, _, _ = self.fixture_protocol(root, "hd_189733_b", exposure=120.00000000000097)
            result = prepare_target(root, protocol, "hd_189733_b", "tess_fixture", allow_draft=True)
            frame = pd.read_csv(root / result["output_directory"] / "model_input.csv")
            self.assertTrue(frame.cadence_type.eq("short").all())
            self.assertTrue(frame.planet_slug.eq("hd_189733_b").all())
            self.assertEqual(result["source_artifacts"][0]["bjd_reference"], 2457000)
            minimum = frame.loc[frame.normalized_flux.idxmin()]
            self.assertLess(abs(minimum.phase), .05)


if __name__ == "__main__":
    unittest.main()
