from __future__ import annotations

import ast
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bayesian_modeling.contracts import TransitModelOptions  # noqa: E402
from publication.inference import (  # noqa: E402
    file_hash,
    posterior_intervals,
    read_input,
    residual_correlations,
    sampler_summary,
)


class PublicationInferenceTests(unittest.TestCase):
    def test_quantiles_are_equal_tailed_not_mislabeled_hdi(self):
        result = posterior_intervals(np.arange(101.))
        self.assertEqual(result["intervals"]["0.5"], [25., 75.])
        self.assertEqual(result["mean"], 50.)
        self.assertEqual(result["interval_method"], "equal_tailed")

    def test_data_identity_fails_before_model_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            pd.DataFrame({"phase": [0.]}).to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                read_input(path, {"input_sha256": "wrong"})
            with self.assertRaisesRegex(ValueError, "identity"):
                read_input(path, {"input_sha256": file_hash(path), "dataset_id": "a", "expected_dataset_id": "b"})

    def test_configuration_rejects_conflicting_or_negative_priors(self):
        for kwargs in ({"baseline_prior_sigma": 0}, {"radius_prior_median": -1},
                       {"radius_prior_uniform": (.01, .1), "radius_prior_median": .04}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                TransitModelOptions(**kwargs)

    def test_correlation_does_not_cross_segment_or_transit_gaps(self):
        frame = pd.DataFrame({"time": np.r_[np.arange(100), np.arange(100)+1000],
                              "segment_id": ["a"] * 200})
        residual = np.sin(np.arange(200)/4)
        result = residual_correlations(frame, residual)
        self.assertTrue(result["flagged"])
        self.assertEqual(result["lags"][0]["pairs"], 198)

    def test_inference_module_has_no_truth_or_simulator_read_surface(self):
        source = (ROOT / "src/publication/inference.py").read_text(encoding="utf-8")
        parsed = ast.parse(source)
        imports = [n.module for n in ast.walk(parsed) if isinstance(n, ast.ImportFrom)]
        self.assertNotIn("publication.simulation", imports)
        self.assertNotIn('"--truth"', source)
        self.assertNotIn('"truth.json"', source)

    def test_historical_run_collision_preserves_bytes(self):
        from bayesian_modeling.physical_transit import run_m5

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination = root / "models/bayesian_physical_transit/kepler_10_b/runs/scientific_003"
            destination.mkdir(parents=True)
            evidence = destination / "run_status.json"
            original = json.dumps({"historical": True}).encode()
            evidence.write_bytes(original)
            with self.assertRaises(FileExistsError):
                run_m5(target_slug="kepler_10_b", run_id="scientific_003", project_root=root)
            self.assertEqual(evidence.read_bytes(), original)

    def test_locked_arviz_summary_interface(self):
        import pymc as pm
        with pm.Model():
            pm.Normal("example")
            idata = pm.sample(draws=20, tune=20, chains=2, cores=1, random_seed=531, progressbar=False)
        result = sampler_summary(idata, ["example"])
        self.assertEqual(result.parameter.tolist(), ["example"])
        self.assertTrue({"r_hat", "ess_bulk", "ess_tail"}.issubset(result.columns))


if __name__ == "__main__":
    unittest.main()
