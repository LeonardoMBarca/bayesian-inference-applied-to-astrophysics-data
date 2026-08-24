from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from project_config import (  # noqa: E402
    BACKUP_GOLD_TARGET_SLUG,
    PRIMARY_GOLD_TARGET_SLUG,
    TARGETS,
    get_target,
    hours_to_days,
    percent_to_fraction,
)


class TargetConfigurationTests(unittest.TestCase):
    def test_supported_target_identity_is_unique(self) -> None:
        self.assertEqual(len({target.planet_slug for target in TARGETS}), len(TARGETS))
        self.assertEqual(len({target.planet_name for target in TARGETS}), len(TARGETS))

    def test_gold_primary_and_backup_are_reproducible_supported_targets(self) -> None:
        self.assertEqual(get_target(PRIMARY_GOLD_TARGET_SLUG).planet_name, "Kepler-10 b")
        self.assertEqual(get_target(BACKUP_GOLD_TARGET_SLUG).planet_name, "HAT-P-7 b")

    def test_kepler_10_has_its_own_period_and_paths(self) -> None:
        hat = get_target("hat_p_7_b")
        kepler = get_target("kepler_10_b")
        self.assertNotEqual(hat.orbital_period_days, kepler.orbital_period_days)
        self.assertAlmostEqual(kepler.orbital_period_days, 0.8374907)
        self.assertIn("kepler_10_b", kepler.source_gold_path.as_posix())
        self.assertNotIn("hat_p_7_b", kepler.source_gold_path.as_posix())

    def test_transit_depth_units_are_explicit_and_convertible(self) -> None:
        kepler = get_target("kepler_10_b")
        self.assertAlmostEqual(kepler.transit_depth_fraction, 0.0001919)
        self.assertAlmostEqual(kepler.reference_radius_ratio_from_depth, 0.0138528, places=6)
        self.assertAlmostEqual(percent_to_fraction(1.5), 0.015)
        self.assertAlmostEqual(hours_to_days(12.0), 0.5)


if __name__ == "__main__":
    unittest.main()
