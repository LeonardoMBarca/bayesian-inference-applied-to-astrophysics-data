"""Small no-network RAW -> Silver -> Gold clean-room integration fixture."""

from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

try:
    import numpy as np
    import pandas as pd
    import silver_data_config
    from astropy.io import fits

    from gold_processing.lightcurve_preparation import normalize_segments_dataframe
    from silver_processing.lightcurves_mast import _extract_one_fits
except ImportError as exc:  # pragma: no cover - depends on scientific environment
    SCIENTIFIC_IMPORT_ERROR = exc
else:
    SCIENTIFIC_IMPORT_ERROR = None


@unittest.skipIf(
    SCIENTIFIC_IMPORT_ERROR is not None,
    f"scientific environment unavailable: {SCIENTIFIC_IMPORT_ERROR}",
)
class CleanRoomPipelineTests(unittest.TestCase):
    @staticmethod
    def _write_raw_fits(path: Path, baseline: float, quarter: int) -> None:
        phase = np.linspace(-0.15, 0.15, 121)
        flux = np.full(len(phase), baseline)
        flux[np.abs(phase) < 0.025] *= 0.9998
        columns = [
            fits.Column(name="TIME", format="D", array=phase),
            fits.Column(name="PDCSAP_FLUX", format="D", array=flux),
            fits.Column(
                name="PDCSAP_FLUX_ERR", format="D", array=np.full(len(phase), 0.1)
            ),
            fits.Column(name="SAP_FLUX", format="D", array=flux),
            fits.Column(name="SAP_FLUX_ERR", format="D", array=np.full(len(phase), 0.1)),
            fits.Column(name="QUALITY", format="K", array=np.zeros(len(phase), dtype=int)),
            fits.Column(name="CADENCENO", format="K", array=np.arange(len(phase))),
        ]
        table = fits.BinTableHDU.from_columns(columns, name="LIGHTCURVE")
        table.header["TIMEDEL"] = 58.8488 / 86_400.0
        table.header["TIMEUNIT"] = "d"
        table.header["TIMESYS"] = "TDB"
        table.header["BJDREFI"] = 2454833
        table.header["BJDREFF"] = 0.0
        table.header["QUARTER"] = quarter
        table.header["TELESCOP"] = "Kepler"
        fits.HDUList([fits.PrimaryHDU(), table]).writeto(path)

    def test_clean_fixture_preserves_provenance_and_removes_segment_offsets(self) -> None:
        planet = {
            "planet_name": "Kepler-10 b",
            "host_star": "Kepler-10",
            "planet_slug": "kepler_10_b",
        }
        config = SimpleNamespace(
            PROJECT_ROOT=PROJECT_ROOT,
            FITS_OUTPUT_COLUMNS=silver_data_config.FITS_OUTPUT_COLUMNS,
            FITS_PREFERRED_COLUMNS=silver_data_config.FITS_PREFERRED_COLUMNS,
        )
        silver_segments = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for quarter, baseline in ((2, 1000.0), (3, 1200.0)):
                path = root / f"fixture_q{quarter}_slc.fits"
                self._write_raw_fits(path, baseline, quarter)
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                curve, metadata = _extract_one_fits(
                    config=config,
                    path=path,
                    planet=planet,
                    mission="Kepler",
                    mission_slug="kepler",
                    raw_info={
                        "source_name": "clean-room fixture",
                        "source_raw_path": f"fixtures/{path.name}",
                        "source_raw_sha256": digest,
                        "source_raw_file_name": path.name,
                    },
                    created_at="2026-08-24T00:00:00+00:00",
                )
                self.assertEqual(metadata["sha256"], digest)
                self.assertEqual(metadata["cadence_type"], "short")
                self.assertAlmostEqual(metadata["exposure_time_seconds"], 58.8488, places=3)
                curve = curve.assign(
                    phase=pd.to_numeric(curve["time"]),
                    flux=pd.to_numeric(curve["pdcsap_flux"]),
                    flux_err=pd.to_numeric(curve["pdcsap_flux_err"]),
                    segment_id=f"kepler:{path.name}",
                    source_fits_sha256=digest,
                )
                silver_segments.append(curve)
        silver = pd.concat(silver_segments, ignore_index=True)
        gold, diagnostics = normalize_segments_dataframe(
            silver,
            transit_exclusion_half_width_days=0.04,
            min_baseline_points=20,
        )
        self.assertEqual(gold["segment_id"].nunique(), 2)
        self.assertEqual(gold["source_fits_sha256"].nunique(), 2)
        self.assertEqual(gold["source_raw_sha256"].nunique(), 2)
        self.assertTrue(gold["preprocessing_status"].eq("segment_normalized").all())
        np.testing.assert_allclose(
            diagnostics["normalized_baseline_median"].to_numpy(),
            np.ones(2),
            atol=1e-12,
        )
        self.assertAlmostEqual(
            float(gold.loc[gold["phase"].abs() < 0.025, "flux"].median()),
            0.9998,
            places=7,
        )


if __name__ == "__main__":
    unittest.main()
