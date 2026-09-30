"""A bounded new study must not replace historical evidence or select seeds."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from publication.campaign_plan import build_plan  # noqa: E402
from publication.campaign_worker import prepare_benchmark  # noqa: E402
from publication.numerical_campaign import (  # noqa: E402
    CAMPAIGN_ID,
    paired_numeric_metrics,
    prepare_study,
)


class NumericalCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config_path = Path(f"configs/publication/{CAMPAIGN_ID}.json")
        cls.plan = build_plan(ROOT, cls.config_path)

    def test_exact_24_jobs_and_no_new_external_or_observational_batch(self):
        self.assertEqual(Counter(job["experiment_id"] for job in self.plan["jobs"]), {"PUB-02": 12, "PUB-03": 3, "PUB-04": 9})
        self.assertEqual(len({job["run_id"] for job in self.plan["jobs"]}), 24)
        self.assertEqual(len({job["output_dir"] for job in self.plan["jobs"]}), 24)
        self.assertTrue(all(job["max_technical_retries"] == 0 for job in self.plan["jobs"]))
        self.assertFalse(any(job["payload"]["kind"] in {"benchmark_external", "observational"} for job in self.plan["jobs"]))

    def test_same_new_dataset_within_each_pair_separate_mc_streams(self):
        groups = defaultdict(list)
        for job in self.plan["jobs"]:
            if "pair_id" in job["payload"]:
                groups[(job["experiment_id"], job["payload"]["pair_id"], job["replicate_id"])].append(job)
        self.assertEqual(len(groups), 9)
        generation_seeds = []
        for key, jobs in groups.items():
            self.assertEqual(len(jobs), 2 if key[0] == "PUB-02" else 3)
            self.assertEqual(len({job["seeds"]["generation"] for job in jobs}), 1)
            self.assertEqual(len({job["seeds"]["inference"] for job in jobs}), len(jobs))
            self.assertTrue(all(job["payload"]["scenario"] == jobs[0]["payload"]["scenario"] for job in jobs))
            generation_seeds.append(jobs[0]["seeds"]["generation"])
        self.assertEqual(len(set(generation_seeds)), 9)
        old = json.loads((ROOT / "configs/publication/tcc_campaign_v1_plan.json").read_text())
        historical = {job["seeds"]["generation"] for job in old["declared_jobs"]}
        self.assertTrue(set(generation_seeds).isdisjoint(historical))

    def test_p2_only_declared_coordinate_changes_no_truth_in_inference(self):
        jobs = [job for job in self.plan["jobs"] if job["experiment_id"] == "PUB-02" and job["replicate_id"] == "rep_0000"]
        by_pair = defaultdict(list)
        for job in jobs:
            by_pair[job["payload"]["pair_id"]].append(job)
        for pair in by_pair.values():
            left, right = [copy.deepcopy(job["payload"]["inference"]) for job in pair]
            self.assertEqual({left.pop("transit_center_parameterization"), right.pop("transit_center_parameterization")}, {"direct", "standardized"})
            self.assertEqual(left, right)
            self.assertNotIn("truth", left)
            self.assertNotIn("initial_values", left)
            self.assertEqual(left["t0_prior_sigma_days"], .025)
            self.assertEqual(left["sampling"]["draws"], 1000)
            self.assertTrue(left["sampling"]["save_warmup"])

    def test_ablation_high_exposure_contrast_uses_high_baseline(self):
        jobs = [job for job in self.plan["jobs"] if job["experiment_id"] == "PUB-04" and job["replicate_id"] == "rep_0000"]
        by_variant = {job["payload"]["variant_id"]: job for job in jobs}
        high = by_variant["baseline_high_accuracy"]["payload"]
        off = by_variant["exposure_off_high_accuracy"]["payload"]
        self.assertEqual(off["reference_variant"], "baseline_high_accuracy")
        self.assertEqual(high["inference"], off["inference"])
        self.assertEqual(off["intervention"], "exposure_off")
        self.assertEqual(high["inference"]["sampling"]["draws"], 2000)
        self.assertEqual(high["inference"]["sampling"]["tune"], 2000)
        self.assertEqual(high["inference"]["sampling"]["target_accept"], .99)

    def test_benchmark_input_is_exact_old_contract_but_new_local_mc_identity(self):
        jobs = [job for job in self.plan["jobs"] if job["experiment_id"] == "PUB-03"]
        self.assertEqual(len({job["seeds"]["inference"] for job in jobs}), 3)
        with tempfile.TemporaryDirectory() as directory:
            path, config = prepare_benchmark(ROOT, self.plan, jobs[0], Path(directory))
            self.assertTrue(path.is_file())
            self.assertEqual(config["input_sha256"], "6653fced1df0b3a29be96d181daa695f86ef709a7aa459bc1b3f837d48ad8791")
            self.assertEqual(config["transit_center_parameterization"], "standardized")
            self.assertEqual(config["radius_prior_uniform"], [.001, .2])
            self.assertEqual(config["sampling"]["target_accept"], .97)

    def test_existing_study_cannot_be_reprepared(self):
        with self.assertRaises(FileExistsError):
            prepare_study(ROOT)

    def pair_rows(self):
        parameter = {"mean": 2., "sd": .5, "intervals": {"0.94": [1., 3.]}}
        return [
            {"job_id": "a", "replicate_id": "rep_0000", "status": "COMPLETED_REJECTED", "payload": {"pair_id": "p", "variant_id": "direct", "reference_variant": "direct"},
             "result": {"input_sha256": "a"*64, "parameters": {"r": parameter}, "gates": {"sampler": False}}},
            {"job_id": "b", "replicate_id": "rep_0000", "status": "PLANNED", "payload": {"pair_id": "p", "variant_id": "standardized", "reference_variant": "direct"}, "result": None},
        ]

    def test_missing_is_null_not_zero_and_failed_sampler_is_not_promoted(self):
        rows = self.pair_rows()
        missing = paired_numeric_metrics(rows)[0]
        self.assertFalse(missing["both_numeric"])
        self.assertIsNone(missing["mean_shift"])
        rows[1]["result"] = copy.deepcopy(rows[0]["result"])
        rows[1]["result"]["parameters"]["r"]["mean"] = 2.5
        item = paired_numeric_metrics(rows)[0]
        self.assertTrue(item["both_numeric"])
        self.assertFalse(item["both_sampler_pass"])
        self.assertEqual(item["mean_shift"], .5)
        self.assertEqual(item["shift_over_reference_sd"], 1.)

    def test_paired_input_mismatch_cannot_produce_effect(self):
        rows = self.pair_rows()
        rows[1]["result"] = copy.deepcopy(rows[0]["result"])
        rows[1]["result"]["input_sha256"] = "b"*64
        with self.assertRaisesRegex(ValueError, "mismatched physical inputs"):
            paired_numeric_metrics(rows)

    def test_planned_and_failed_rows_generate_reports_without_sampling(self):
        from publication.numerical_campaign import numerical_family_report
        jobs = [job for job in self.plan["jobs"] if job["experiment_id"] == "PUB-02"]
        rows = [{**copy.deepcopy(job), "status": "PLANNED", "result": None, "truth": None,
                 "completion": None, "authoritative_attempt_dir": None} for job in jobs]
        rows[0].update(status="FAILED_TECHNICAL", result={"status": "failed", "gates": {}, "parameters": {}},
                       completion={"artifacts": {}, "wall_seconds": 1.})
        protocol = json.loads((ROOT / self.plan["protocols"]["PUB-02"]["path"]).read_text())
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            summary, files, _ = numerical_family_report(ROOT, rows, output, protocol)
            self.assertEqual(summary["declared_jobs"], 12)
            self.assertEqual(summary["status_counts"], {"FAILED_TECHNICAL": 1, "PLANNED": 11})
            self.assertTrue(all(path.is_file() for path in files))
            self.assertTrue(all(item["mean_shift"] is None for item in summary["paired_effects"]))
            self.assertEqual(len((output / "t0_chain_locations.csv").read_text().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
