from __future__ import annotations

import importlib.metadata
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from publication.environment_guard import (  # noqa: E402
    inspect_scientific_environment,
    parse_exact_requirements,
)


class EnvironmentGuardTests(unittest.TestCase):
    def setUp(self):
        self.expected = parse_exact_requirements((ROOT / "publication/baseline/environment/requirements.txt").read_text(encoding="utf-8"))

    def test_exact_pins_and_python_are_checked_in_actual_interpreter(self):
        good = inspect_scientific_environment(ROOT, python_version="3.14.6", version_lookup=self.expected.__getitem__)
        self.assertTrue(good["passed"])
        wrong_python = inspect_scientific_environment(ROOT, python_version="3.12.14", version_lookup=self.expected.__getitem__)
        self.assertFalse(wrong_python["passed"])
        altered = dict(self.expected, pymc="0.0.0")
        wrong_package = inspect_scientific_environment(ROOT, python_version="3.14.6", version_lookup=altered.__getitem__)
        self.assertFalse(wrong_package["passed"])
        self.assertIn("pymc", wrong_package["errors"][0])

    def test_missing_package_fails_without_importing_scientific_graph(self):
        def missing(name):
            if name == "exoplanet":
                raise importlib.metadata.PackageNotFoundError(name)
            return self.expected[name]

        result = inspect_scientific_environment(ROOT, python_version="3.14.6", version_lookup=missing)
        self.assertFalse(result["passed"])
        self.assertIsNone(result["packages"]["exoplanet"]["actual"])

    def test_nonexact_or_duplicate_requirements_are_rejected(self):
        for content in ("numpy>=2", "numpy==2\nNumPy==2", "", "-e ./local"):
            with self.assertRaises(ValueError):
                parse_exact_requirements(content)


if __name__ == "__main__":
    unittest.main()
