"""Prospective fixed-N cohort contract: unchanged science and independent data."""

import copy
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from publication.campaign_plan import build_plan  # noqa: E402
from publication.contracts import sha256_file  # noqa: E402

CONFIG = Path("configs/publication/tcc_calibration_confirmatory_v1.json")


class ConfirmatoryCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT / CONFIG).read_text())
        cls.protocol = json.loads((ROOT / cls.config["protocols"]["PUB-02"]).read_text())
        cls.parent = json.loads((ROOT / "publication/protocols/PUB-02.json").read_text())
        cls.plan = build_plan(ROOT, CONFIG)
        cls.ledger = json.loads((ROOT / cls.plan["frozen_plan_path"]).read_text())
        cls.parent_plan = json.loads((ROOT / "configs/publication/tcc_campaign_v1_plan.json").read_text())

    def test_only_declared_replication_and_prospective_metadata_change(self):
        allowed = {
            "protocol_version", "replicates_per_scenario", "total_declared_final_attempts",
            "replication_precision", "freeze_note", "deferred_scenario_reason",
            "confirmatory_extension", "amendments",
        }
        old = {k: v for k, v in self.parent.items() if k not in allowed}
        new = {k: v for k, v in self.protocol.items() if k not in allowed}
        self.assertEqual(old, new)
        self.assertEqual(self.protocol["amendments"][:-1], self.parent["amendments"])
        for identity in ("parent_protocol", "parent_ledger"):
            record = self.protocol["confirmatory_extension"][identity]
            self.assertEqual(sha256_file(ROOT / record["path"]), record["sha256"])

    def test_fixed_400_jobs_all_original_scenarios(self):
        # This is a historical design contract, not authorization to launch an
        # old campaign from a later analysis-only source tree. Execution
        # preflight deliberately rejects any source not in its frozen ledger.
        fields = ("job_id", "experiment_id", "scenario_id", "replicate_id",
                  "run_id", "seeds", "payload")
        self.assertEqual(
            [{key: job[key] for key in fields} for job in self.plan["jobs"]],
            self.ledger["declared_jobs"],
        )
        self.assertEqual(self.plan["protocols"], self.ledger["protocols"])
        self.assertEqual(self.plan["scientific_config_sha256"],
                         self.ledger["scientific_config_sha256"])
        jobs = self.plan["jobs"]
        self.assertEqual(len(jobs), 400)
        self.assertEqual({j["experiment_id"] for j in jobs}, {"PUB-02"})
        counts = Counter(j["scenario_id"] for j in jobs)
        self.assertEqual(counts, {s["scenario_id"]: 100 for s in self.parent["scenarios"]})
        self.assertEqual(self.protocol["total_declared_final_attempts"], len(jobs))
        for job in jobs:
            self.assertEqual(job["payload"]["inference"], self.parent["inference"])
            self.assertEqual(job["max_technical_retries"], 0)

    def test_all_seed_streams_and_run_paths_are_disjoint_from_parent(self):
        old_jobs = self.parent_plan["declared_jobs"]
        old_seeds = {s for j in old_jobs for s in j["seeds"].values()}
        jobs = self.plan["jobs"]
        seeds = [s for j in jobs for s in j["seeds"].values()]
        self.assertEqual(len(seeds), 1600)
        self.assertEqual(len(set(seeds)), len(seeds))
        self.assertFalse(set(seeds) & old_seeds)
        self.assertFalse({j["run_id"] for j in jobs} & {j["run_id"] for j in old_jobs})
        self.assertEqual(len({j["output_dir"] for j in jobs}), 400)
        prefix = "artifacts/publication_campaign/tcc_calibration_confirmatory_v1/runs/"
        self.assertTrue(all(j["output_dir"].startswith(prefix) for j in jobs))
        self.assertTrue(all("scientific_003" not in j["output_dir"] for j in jobs))
        ledger = json.loads((ROOT / self.plan["frozen_plan_path"]).read_text())
        self.assertEqual([j["seeds"] for j in jobs], [j["seeds"] for j in ledger["declared_jobs"]])

    def test_runtime_resources_preserve_frozen_scientific_scope(self):
        # The original 22h/four-core planning statement remains immutable.
        # Later user-authorized dispatch limits are operational, not changes
        # to the chain count, draws, seeds or the fixed-N stopping rule.
        extension = self.protocol["confirmatory_extension"]
        self.assertEqual(extension["runtime_budget_hours"], 22)
        self.assertEqual(self.protocol["inference"]["sampling"]["chains"], 4)
        self.assertEqual(self.protocol["inference"]["sampling"]["cores"], 4)
        self.assertLessEqual(22 + extension["parent_checkpointed_active_hours"], 36)
        resources = self.plan["resources"]
        self.assertGreaterEqual(resources["max_workers"], 1)
        self.assertGreaterEqual(resources["cores_per_run"], 1)
        self.assertGreater(resources["max_campaign_hours"], 0)
        self.assertEqual(resources["cores_per_run"], self.config["resources"]["cores_per_run"])
        self.assertTrue(all(job["cores"] == resources["cores_per_run"] for job in self.plan["jobs"]))
        self.assertEqual(self.plan["scientific_config_sha256"],
                         self.ledger["scientific_config_sha256"])
        self.assertEqual(self.plan["estimated_total_hours"], 20)
        for family in ("benchmark", "ablations", "multi_target", "correlated_noise"):
            self.assertFalse(self.config[family]["enabled"])
        self.assertEqual(set(self.plan["family_summarizers"]), {"PUB-02"})

    def test_truth_is_not_part_of_inference_configuration(self):
        inference = copy.deepcopy(self.protocol["inference"])
        self.assertNotIn("truth", inference)
        self.assertNotIn("scenario_id", inference)
        self.assertEqual(inference, self.parent["inference"])


if __name__ == "__main__":
    unittest.main()
