"""Regression checks for the repository's code organization contracts."""

from __future__ import annotations

import ast
import importlib
import importlib.util
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


class RepositoryLayoutTests(unittest.TestCase):
    def test_top_level_scripts_are_thin_entry_points(self) -> None:
        script_paths = sorted((PROJECT_ROOT / "scripts").glob("*.py"))
        oversized = {
            path.name: len(path.read_text(encoding="utf-8").splitlines())
            for path in script_paths
            if len(path.read_text(encoding="utf-8").splitlines()) > 120
        }
        self.assertEqual(oversized, {})

    def test_grouped_implementation_modules_exist(self) -> None:
        expected = {
            "src/gold_analysis/lightcurve.py",
            "src/bayesian_modeling/legacy/baseline.py",
            "src/bayesian_modeling/legacy/baseline_nuts_robust.py",
            "src/bayesian_modeling/legacy/predictive_phase_regression.py",
            "src/bayesian_modeling/legacy/trapezoid_transit.py",
            "src/repository_tools/model_run_inventory.py",
            "src/repository_tools/ci_tests.py",
            "src/repository_tools/static_validation.py",
            "src/repository_tools/clean_rebuild.py",
            "src/repository_tools/artifact_validation.py",
            "src/repository_tools/environment_validation.py",
        }
        missing = sorted(path for path in expected if not (PROJECT_ROOT / path).is_file())
        self.assertEqual(missing, [])

    def test_notebook_facing_compatibility_apis_remain_available(self) -> None:
        contracts = {
            "scripts/analyze_gold_lightcurve.py": (
                "gold_analysis.lightcurve",
                "run_analysis",
            ),
            "scripts/run_bayesian_baseline.py": (
                "bayesian_modeling.legacy.baseline",
                "run_pipeline",
            ),
            "scripts/run_bayesian_predictive_phase_regression.py": (
                "bayesian_modeling.legacy.predictive_phase_regression",
                "main",
            ),
            "scripts/run_bayesian_trapezoid_transit.py": (
                "bayesian_modeling.legacy.trapezoid_transit",
                "main",
            ),
        }
        for wrapper_path, (module_name, required_function) in contracts.items():
            wrapper_source = (PROJECT_ROOT / wrapper_path).read_text(encoding="utf-8")
            self.assertIn(f"from {module_name} import *", wrapper_source)
            implementation_path = SRC_DIR / Path(*module_name.split(".")).with_suffix(".py")
            tree = ast.parse(implementation_path.read_text(encoding="utf-8"))
            functions = {
                node.name for node in tree.body if isinstance(node, ast.FunctionDef)
            }
            self.assertIn(required_function, functions)

    def test_notebook_facing_wrappers_import_and_resolve_the_same_root(self) -> None:
        for script_name, module_name, required_function in (
            ("analyze_gold_lightcurve.py", "gold_eda_layout_test", "run_analysis"),
            ("run_bayesian_baseline.py", "baseline_layout_test", "run_pipeline"),
        ):
            spec = importlib.util.spec_from_file_location(
                module_name, PROJECT_ROOT / "scripts" / script_name
            )
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.assertTrue(callable(getattr(module, required_function)))
            self.assertEqual(module.resolve_project_root(), PROJECT_ROOT)

        for module_name in (
            "scripts.run_bayesian_predictive_phase_regression",
            "scripts.run_bayesian_trapezoid_transit",
        ):
            module = importlib.import_module(module_name)
            self.assertTrue(callable(module.main))
            self.assertEqual(module.resolve_project_root(), PROJECT_ROOT)

    def test_legacy_config_imports_match_canonical_modules(self) -> None:
        from gold_processing import config as gold_config
        from raw_ingestion import config as raw_config
        from scripts import gold_data_config, raw_data_config, silver_data_config
        from silver_processing import config as silver_config

        pairs = (
            (raw_data_config, raw_config, "RAW_DATA_DIR"),
            (silver_data_config, silver_config, "SILVER_DATA_DIR"),
            (gold_data_config, gold_config, "GOLD_DATA_DIR"),
        )
        for compatibility, canonical, sentinel in pairs:
            self.assertEqual(getattr(compatibility, sentinel), getattr(canonical, sentinel))
            self.assertEqual(compatibility.PROJECT_ROOT, PROJECT_ROOT)
            self.assertEqual(canonical.PROJECT_ROOT, PROJECT_ROOT)


if __name__ == "__main__":
    unittest.main()
