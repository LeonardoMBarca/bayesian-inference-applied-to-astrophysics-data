from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from publication.campaign_preflight import (  # noqa: E402
    ExecutionEnvironmentError,
    inspect_external_interpreter,
    validate_execution_environment,
)


class CampaignPreflightTests(unittest.TestCase):
    def test_smoke_does_not_probe_or_require_large_archived_evidence(self):
        with patch("publication.campaign_preflight.verify_baseline") as baseline:
            self.assertTrue(validate_execution_environment(ROOT, {"mode": "smoke"})["passed"])
            baseline.assert_not_called()

    def test_external_metadata_probe_rejects_wrong_version(self):
        expected = {"python_version": "3.12.14", "packages": [{"name": "juliet", "version": "2.2.10"}], "source_sha256": {}}
        observed = {"python_version": "3.12.14", "packages": {"juliet": "0.0.0"}, "source_sha256": {}, "executable": sys.executable}
        response = subprocess.CompletedProcess([], 0, json.dumps(observed), "")
        with patch("publication.campaign_preflight.subprocess.run", return_value=response):
            result = inspect_external_interpreter(sys.executable, expected)
        self.assertFalse(result["passed"])
        self.assertIn("juliet", result["errors"][0])

    def test_final_preflight_probes_dependencies_and_rejects_modified_raw(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            raw = root / "data/raw/t.fits"
            raw.parent.mkdir(parents=True)
            raw.write_bytes(b"scientific input")
            digest = hashlib.sha256(raw.read_bytes()).hexdigest()
            protocol = {"targets": [{"config": {"planet_slug": "test_target"}, "expected_source_count": 1,
                                     "sources": [{"path": "data/raw/t.fits", "sha256": digest}]}]}
            path = root / "protocol.json"
            path.write_text(json.dumps(protocol), encoding="utf-8")
            plan = {"campaign_id": "test", "mode": "final", "runtime": {"scientific_python": sys.executable},
                    "protocols": {"PUB-05": {"path": "protocol.json", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}}}
            stack.enter_context(patch("publication.campaign_preflight.require_scientific_environment", return_value={"passed": True}))
            baseline = stack.enter_context(patch("publication.campaign_preflight.verify_baseline", return_value={"status": "verified"}))
            stack.enter_context(patch("publication.campaign_preflight.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "publication-grade-validation\n", "")))
            result = validate_execution_environment(root, plan)
            self.assertTrue(result["passed"])
            baseline.assert_called_once_with(root.resolve(), require_external=True)
            raw.write_bytes(b"changed scientific input")
            with self.assertRaises(ExecutionEnvironmentError) as caught:
                validate_execution_environment(root, plan)
            self.assertFalse(caught.exception.report["sources"][0]["matched"])

    def test_final_wrong_branch_blocks_before_jobs(self):
        with ExitStack() as stack:
            stack.enter_context(patch("publication.campaign_preflight.require_scientific_environment", return_value={"passed": True}))
            stack.enter_context(patch("publication.campaign_preflight.verify_baseline", return_value={"status": "verified"}))
            stack.enter_context(patch("publication.campaign_preflight.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "main\n", "")))
            with self.assertRaisesRegex(ExecutionEnvironmentError, "publication-grade-validation"):
                validate_execution_environment(ROOT, {"campaign_id": "test", "mode": "final", "runtime": {"scientific_python": sys.executable}, "protocols": {}})

    def test_local_only_benchmark_checks_historical_reference_without_external_python(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            input_path = root / "input.csv"
            input_path.write_bytes(b"time,flux\n0,1\n")
            reference = root / "external/completion_manifest.json"
            reference.parent.mkdir()
            reference.write_bytes(b'{"status":"COMPLETED_REJECTED"}\n')
            protocol = {
                "dataset": {"input_path": "input.csv", "input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest()},
                "external_reference": {"attempt_dir": "external", "new_external_inference": False,
                                       "completion_manifest_sha256": hashlib.sha256(reference.read_bytes()).hexdigest()},
            }
            path = root / "protocol.json"
            path.write_text(json.dumps(protocol), encoding="utf-8")
            plan = {"campaign_id": "local_only", "mode": "final", "runtime": {"scientific_python": sys.executable},
                    "jobs": [{"experiment_id": "PUB-03", "payload": {"kind": "benchmark_local"}}],
                    "protocols": {"PUB-03": {"path": "protocol.json", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}}}
            stack.enter_context(patch("publication.campaign_preflight.require_scientific_environment", return_value={"passed": True}))
            stack.enter_context(patch("publication.campaign_preflight.verify_baseline", return_value={"status": "verified"}))
            stack.enter_context(patch("publication.campaign_preflight.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "publication-grade-validation\n", "")))
            probe = stack.enter_context(patch("publication.campaign_preflight.inspect_external_interpreter"))
            result = validate_execution_environment(root, plan)
            self.assertTrue(result["passed"])
            self.assertEqual(len(result["sources"]), 2)
            self.assertFalse(result["benchmark_environment"]["external_interpreter_probed"])
            probe.assert_not_called()
            reference.write_bytes(b'{"status":"tampered"}\n')
            with self.assertRaises(ExecutionEnvironmentError) as caught:
                validate_execution_environment(root, plan)
            self.assertIn("checksum mismatch", " ".join(caught.exception.report["errors"]))


if __name__ == "__main__":
    unittest.main()
