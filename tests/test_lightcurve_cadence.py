from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from lightcurve_cadence import infer_exposure_metadata  # noqa: E402


class LightcurveCadenceTests(unittest.TestCase):
    def test_fits_timedel_days_is_converted_to_seconds(self) -> None:
        seconds, cadence, source = infer_exposure_metadata(
            filename="product.fits", timedel=58.84876 / 86_400.0
        )
        self.assertAlmostEqual(seconds, 58.84876)
        self.assertEqual(cadence, "short")
        self.assertEqual(source, "FITS_TIMEDEL")

    def test_kepler_filename_conventions_are_explicit_fallbacks(self) -> None:
        short = infer_exposure_metadata(filename="kplr012345678-2010009091648_slc.fits")
        long = infer_exposure_metadata(filename="kplr012345678-2010009091648_llc.fits")
        self.assertEqual(short[1:], ("short", "KEPLER_FILENAME_SLC"))
        self.assertEqual(long[1:], ("long", "KEPLER_FILENAME_LLC"))
        self.assertLess(short[0], long[0])


if __name__ == "__main__":
    unittest.main()
