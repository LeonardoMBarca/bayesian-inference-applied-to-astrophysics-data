"""Frozen design, count, truth separation and classification regressions."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from publication.campaign_plan import build_plan, freeze_plan, seed, source_identity  # noqa: E402
from publication.campaign_worker import (  # noqa: E402
    accept_child_result,
    classify_result,
    execute_attempt,
    prepare_synthetic,
)


class CampaignPlanTests(unittest.TestCase):
    def test_nonzero_child_cannot_promote_a_written_posterior(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            original = {"status": "completed", "gates": {key: True for key in ("provenance", "sampler", "ppc", "scientific")}}
            (output / "result.json").write_text(json.dumps(original))
            result, expected = accept_child_result(output, 7, None)
            self.assertEqual(result["status"], "failed")
            self.assertFalse(expected)
            self.assertEqual(json.loads((output / "child_result.json").read_text()), original)

    def test_negative_control_requires_its_exact_failure_not_an_environment_error(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            result = {"status": "failed", "failure_stage": "input_validation", "failure_code": None}
            (output / "result.json").write_text(json.dumps(result))
            self.assertFalse(accept_child_result(output, 1, "invalid_input_hash")[1])
            result["failure_code"] = "input_sha256_mismatch"
            (output / "result.json").write_text(json.dumps(result))
            self.assertTrue(accept_child_result(output, 1, "invalid_input_hash")[1])
            self.assertFalse(accept_child_result(output, 1, "dataset_identity_mismatch")[1])
    def test_tcc_counts_order_seeds_and_paired_generation(self):
        plan = build_plan(ROOT, Path("configs/publication/tcc_final_campaign.json"))
        counts = {phase: sum(job["experiment_id"] == phase for job in plan["jobs"]) for phase in plan["phase_order"]}
        self.assertEqual(counts, {"PUB-02": 80, "PUB-03": 2, "PUB-04": 30, "PUB-05": 5, "PUB-06": 0})
        self.assertLess(plan["estimated_total_hours"], plan["resources"]["max_campaign_hours"])
        p4 = [job for job in plan["jobs"] if job["experiment_id"] == "PUB-04" and job["replicate_id"] == "rep_0000"]
        long_pair = [job for job in p4 if job["payload"]["pair_id"] == "long_segment_offsets"]
        self.assertEqual(len({job["seeds"]["generation"] for job in long_pair}), 1)
        self.assertEqual(len({job["seeds"]["inference"] for job in long_pair}), 8)
        self.assertNotEqual(seed("paper_v1", "PUB-02", "deep", "rep_0000", "generation"),
                            seed("tcc_v1", "PUB-02", "deep", "rep_0000", "generation"))

    def test_science_rejection_is_not_a_retryable_technical_error(self):
        self.assertEqual(classify_result({"status": "rejected", "gates": {"scientific": False}}), "COMPLETED_REJECTED")
        failed = {"status": "failed", "failure_stage": "input_validation"}
        self.assertEqual(classify_result(failed), "FAILED_TECHNICAL")
        self.assertEqual(classify_result(failed, expected_identity_rejection=True), "COMPLETED_REJECTED")
        self.assertEqual(classify_result({"status": "completed", "gates": {"scientific": True}}), "COMPLETED_REJECTED")

    def test_runtime_budget_changes_do_not_change_science_identity(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "configs/publication") as directory:
            path = Path(directory) / "smoke.json"
            config = json.loads((ROOT / "configs/publication/smoke_campaign.json").read_text())
            path.write_text(json.dumps(config))
            first = build_plan(ROOT, path)
            config["resources"]["max_campaign_hours"] = 99
            path.write_text(json.dumps(config))
            self.assertEqual(first["scientific_config_sha256"], build_plan(ROOT, path)["scientific_config_sha256"])
            config["smoke_jobs"][0]["action"] = "scientific_rejection"
            path.write_text(json.dumps(config))
            self.assertNotEqual(first["scientific_config_sha256"], build_plan(ROOT, path)["scientific_config_sha256"])

    def test_source_identity_covers_imported_gold_modules(self):
        sources = source_identity(ROOT)
        self.assertIn("src/project_config.py", sources)
        self.assertIn("src/publication/environment_guard.py", sources)
        self.assertTrue(any(path.startswith("src/gold") for path in sources))

    def test_synthetic_input_contains_no_truth_and_config_does_not_depend_on_it(self):
        plan = build_plan(ROOT, Path("configs/publication/smoke_campaign.json"))
        job = copy.deepcopy(plan["jobs"][-1])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first, second = root / "first", root / "second"
            first.mkdir()
            second.mkdir()
            path, config = prepare_synthetic(job, first)
            job["payload"]["scenario"]["truth"]["r"] = .12
            _, changed = prepare_synthetic(job, second)
            for key in ("input_sha256", "dataset_id", "expected_dataset_id"):
                config.pop(key)
                changed.pop(key)
            self.assertEqual(config, changed)
            columns = path.read_text().splitlines()[0]
            self.assertNotIn("truth", columns)
            self.assertNotIn("injected", columns)

    def test_unexpected_preparation_failure_has_sealed_result_and_no_retry(self):
        plan = build_plan(ROOT, Path("configs/publication/smoke_campaign.json"))
        job = plan["jobs"][-1]
        with tempfile.TemporaryDirectory() as directory:
            with patch("publication.campaign_worker.prepare_synthetic", side_effect=ValueError("deliberate")):
                result = execute_attempt(ROOT, plan, job, Path(directory))
            self.assertEqual(result["status"], "FAILED_TECHNICAL")
            self.assertFalse(result["technical_retryable"])
            self.assertIn("result.json", result["artifacts"])

    def test_initialized_campaign_cannot_be_refrozen(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "configs").mkdir()
            config = {"campaign_id": "frozen", "mode": "smoke", "smoke_jobs": []}
            (root / "configs/smoke.json").write_text(json.dumps(config))
            state = root / "artifacts/publication_campaign/frozen/campaign_state.json"
            state.parent.mkdir(parents=True)
            state.write_text("{}")
            with self.assertRaises(FileExistsError):
                freeze_plan(root, Path("configs/smoke.json"))


if __name__ == "__main__":
    unittest.main()
