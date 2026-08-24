"""Static regression checks for environment, CI, and storage contracts."""

from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ReproducibilityContractTests(unittest.TestCase):
    def test_scientific_dependencies_are_exact_and_include_m5_stack(self) -> None:
        lines = [
            line.strip()
            for line in (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertTrue(all("==" in line for line in lines))
        names = {line.split("==", 1)[0].lower() for line in lines}
        self.assertTrue(
            {"pymc", "pytensor", "arviz", "exoplanet", "exoplanet-core"}.issubset(names)
        )

    def test_ci_runs_tests_and_artifact_validation(self) -> None:
        workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("unittest discover", workflow)
        self.assertIn("validate_hardened_artifacts.py", workflow)
        self.assertIn("static_validate.py", workflow)
        self.assertIn("validate_clean_rebuild.py", workflow)
        self.assertIn("requirements.txt", workflow)

    def test_gitignore_does_not_hide_the_repository(self) -> None:
        lines = {
            line.strip()
            for line in (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        }
        self.assertNotIn("*", lines)
        self.assertIn("*.nc", lines)
        self.assertTrue((PROJECT_ROOT / "docs" / "STORAGE_POLICY.md").exists())


if __name__ == "__main__":
    unittest.main()
