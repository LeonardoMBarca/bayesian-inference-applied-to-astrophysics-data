"""Regression tests for explicit centered phase construction."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    import numpy as np
    import pandas as pd

    from gold_processing.lightcurve_preparation import construct_centered_phase
except ImportError as exc:  # pragma: no cover - depends on scientific environment
    SCIENTIFIC_IMPORT_ERROR = exc
else:
    SCIENTIFIC_IMPORT_ERROR = None


@unittest.skipIf(
    SCIENTIFIC_IMPORT_ERROR is not None,
    f"scientific environment unavailable: {SCIENTIFIC_IMPORT_ERROR}",
)
class PhaseConstructionTests(unittest.TestCase):
    def test_midpoint_and_period_wrap_are_centered_in_days(self) -> None:
        phase = construct_centered_phase(
            pd.Series([10.0, 10.25, 10.75, 11.0]),
            orbital_period_days=1.0,
            transit_midpoint_in_time_scale=10.0,
        )
        np.testing.assert_allclose(phase.to_numpy(), [0.0, 0.25, -0.25, 0.0])

    def test_invalid_period_fails_loudly(self) -> None:
        with self.assertRaisesRegex(ValueError, "orbital_period_days"):
            construct_centered_phase(
                pd.Series([1.0]),
                orbital_period_days=0.0,
                transit_midpoint_in_time_scale=1.0,
            )


if __name__ == "__main__":
    unittest.main()
