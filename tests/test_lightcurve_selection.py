from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from lightcurve_selection import product_ranking  # noqa: E402


class LightcurveSelectionTests(unittest.TestCase):
    def test_short_cadence_is_preferred_for_kepler_10_policy(self) -> None:
        short = product_ranking(
            author="Kepler", exposure_time_seconds=58.85, index=1, cadence_preference="short"
        )
        long = product_ranking(
            author="Kepler", exposure_time_seconds=1765.5, index=0, cadence_preference="short"
        )
        self.assertLess(short, long)

    def test_author_priority_precedes_cadence(self) -> None:
        official_long = product_ranking(
            author="Kepler", exposure_time_seconds=1765.5, index=0, cadence_preference="short"
        )
        unknown_short = product_ranking(
            author="unknown", exposure_time_seconds=58.85, index=1, cadence_preference="short"
        )
        self.assertLess(official_long, unknown_short)


if __name__ == "__main__":
    unittest.main()
