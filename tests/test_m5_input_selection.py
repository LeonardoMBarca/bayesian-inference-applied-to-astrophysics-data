from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    import numpy as np
    import pandas as pd

    from bayesian_modeling.physical_transit import stratified_phase_thin
except ImportError as exc:  # pragma: no cover - depends on scientific environment
    SCIENTIFIC_IMPORT_ERROR = exc
else:
    SCIENTIFIC_IMPORT_ERROR = None


@unittest.skipIf(
    SCIENTIFIC_IMPORT_ERROR is not None,
    f"scientific environment unavailable: {SCIENTIFIC_IMPORT_ERROR}",
)
class M5InputSelectionTests(unittest.TestCase):
    def test_thinning_is_segment_stratified_and_deterministic(self) -> None:
        frame = pd.concat(
            [
                pd.DataFrame(
                    {
                        "segment_id": segment,
                        "phase": np.linspace(-0.15, 0.15, 101),
                        "time": np.arange(101),
                        "source_fits_file": f"{segment}.fits",
                        "exposure_time_seconds": 58.85,
                    }
                )
                for segment in ("q2", "q3")
            ],
            ignore_index=True,
        )
        first = stratified_phase_thin(frame, max_points_per_segment=11)
        second = stratified_phase_thin(frame, max_points_per_segment=11)
        self.assertTrue(first.equals(second))
        self.assertEqual(first.groupby("segment_id").size().to_dict(), {"q2": 11, "q3": 11})
        self.assertEqual(first["source_fits_file"].nunique(), 2)
        self.assertEqual(set(first.groupby("segment_id")["phase"].min()), {-0.15})
        self.assertEqual(set(first.groupby("segment_id")["phase"].max()), {0.15})


if __name__ == "__main__":
    unittest.main()
