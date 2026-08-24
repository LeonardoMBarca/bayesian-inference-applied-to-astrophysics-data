"""Static regression checks for environment, CI, and storage contracts."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from scripts.run_ci_tests import enforce_ci_result
from scripts.verify_scientific_environment import IMPORTS

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
        self.assertIn("ruff", names)
        self.assertEqual(names, set(IMPORTS))

    def test_ci_runs_tests_and_artifact_validation(self) -> None:
        workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("run_ci_tests.py", workflow)
        self.assertIn("verify_scientific_environment.py", workflow)
        self.assertIn("ruff check .", workflow)
        self.assertIn("validate_hardened_artifacts.py", workflow)
        self.assertIn("static_validate.py", workflow)
        self.assertIn("validate_clean_rebuild.py", workflow)
        self.assertIn("requirements.txt", workflow)

    def test_ci_rejects_skipped_scientific_tests(self) -> None:
        result = SimpleNamespace(
            wasSuccessful=lambda: True,
            failures=[],
            errors=[],
            skipped=[("scientific_test", "missing exoplanet")],
        )
        with self.assertRaisesRegex(RuntimeError, "skips are forbidden"):
            enforce_ci_result(result)

    def test_clean_rebuild_evidence_records_verified_network_guard(self) -> None:
        evidence = json.loads(
            (PROJECT_ROOT / "reports" / "clean_rebuild_validation.json").read_text(
                encoding="utf-8"
            )
        )
        isolation = evidence["network_isolation"]
        self.assertEqual(isolation["enforcement"], "verified Python socket guard")
        self.assertTrue(isolation["verification"]["verified"])
        self.assertEqual(isolation["pipeline_attempted_network_calls"], [])
        self.assertIn("not an operating-system network namespace", isolation["scope"])

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
