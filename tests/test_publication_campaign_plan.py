"""Frozen design, count, truth separation and classification regressions."""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from publication.campaign_plan import (  # noqa: E402
    build_plan,
    freeze_plan,
    seed,
    source_identity,
    uncommitted_sources,
)
from publication.campaign_worker import (  # noqa: E402
    accept_child_result,
    classify_result,
    execute_attempt,
    prepare_synthetic,
)
from publication.contracts import sha256_file  # noqa: E402


class CampaignPlanTests(unittest.TestCase):
    def test_source_git_blob_identity_detects_modified_untracked_and_deleted_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            source = root / "src/model.py"
            source.write_bytes(b"answer = 42\n")
            for command in (["init", "-q"], ["add", "src/model.py"],
                            ["-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture"]):
                subprocess.run(["git", "-C", str(root), *command], check=True, capture_output=True)
            self.assertEqual(uncommitted_sources(root, source_identity(root)), [])
            source.write_bytes(b"answer = 43\n")
            self.assertEqual(uncommitted_sources(root, source_identity(root)), ["src/model.py"])
            source.unlink()
            (root / "src/new.py").write_bytes(b"new = True\n")
            self.assertEqual(uncommitted_sources(root, source_identity(root)), ["src/model.py", "src/new.py"])
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
        self.assertIn("scripts/_network_guard/sitecustomize.py", sources)
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


class RuntimeAmendmentTests(unittest.TestCase):
    """Real isolated Git histories; no scientific inference or live-state edits."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.config_path = Path("configs/publication/fixture.json")
        self.frozen_path = self.root / "configs/publication/fixture_plan.json"
        self.record_path = self.root / "publication/runtime_amendments/fixture.json"
        self.protocol_path = self.root / "publication/protocols/PUB-02.json"
        self.engine_path = "src/publication/campaign.py"
        self.plan_path = "src/publication/campaign_plan.py"
        self.inference_path = "src/publication/inference.py"
        for relative in (self.engine_path, self.plan_path, self.inference_path):
            self.write(relative, b"original = True\n")
        self.write(self.config_path, {
            "campaign_id": "fixture", "mode": "final",
            "protocols": {"PUB-02": "publication/protocols/PUB-02.json"},
            "injection_recovery": {"enabled": True, "replicates_per_scenario": 1},
            "benchmark": {"enabled": False}, "ablations": {"enabled": False},
            "multi_target": {"enabled": False},
        })
        self.write(self.protocol_path, {"experiment_id": "PUB-02", "protocol_status": "FROZEN",
                   "replicates_per_scenario": 1, "scenarios": [{"scenario_id": "fixture", "truth": {}, "design": {}}],
                   "inference": {}})
        self.git("init", "-q")
        self.git("config", "core.autocrlf", "false")
        self.commit("Original protocol and source")
        freeze_plan(self.root, self.config_path)
        self.commit("Immutable scientific ledger")
        self.original_ledger = self.frozen_path.read_bytes()
        self.original_sources = json.loads(self.original_ledger)["source_checksums"]
        self.original_plan = self.plan()
        self.assertEqual(self.original_plan["preflight_errors"], [])

    def write(self, relative, payload):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload if isinstance(payload, bytes) else (json.dumps(payload, sort_keys=True) + "\n").encode())

    def git(self, *arguments):
        return subprocess.check_output(["git", "-C", str(self.root), *arguments], stderr=subprocess.PIPE).decode().strip()

    def commit(self, message):
        self.git("add", "-A")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", message)
        return self.git("rev-parse", "HEAD")

    def plan(self):
        return build_plan(self.root, self.config_path)

    def make_record(self, paths=None):
        paths = paths or [self.engine_path]
        for path in paths:
            self.write(path, b"operational_repair = True\n")
        approved_commit = self.commit("Reviewed operational source repair")
        evidence_path = "publication/validation/runtime_repair_001.json"
        self.write(evidence_path, {"status": "passed", "source_commit": approved_commit})
        return {"schema_version": "campaign-runtime-amendments-v1", "campaign_id": "fixture",
                "frozen_plan_sha256": sha256_file(self.frozen_path), "amendments": [{
                    "amendment_id": "runtime_001", "reason": "Repair checkpoint I/O only; scientific design unchanged",
                    "approved_source_commit": approved_commit,
                    "changes": {path: {"from_sha256": self.original_sources[path], "to_sha256": sha256_file(self.root / path)} for path in paths},
                    "validation_evidence": [{"path": evidence_path, "sha256": sha256_file(self.root / evidence_path)}],
                }]}

    def commit_record(self, record):
        self.write(self.record_path, record)
        self.commit("Append audited runtime amendment and evidence")

    def initialize(self, commit=None):
        from publication.campaign import _journal
        state = {"campaign_id": "fixture", "code_commit": commit or self.git("rev-parse", "HEAD"), "events": []}
        _journal(state, "campaign_declared", scientific_config_sha256=self.plan()["scientific_config_sha256"])
        self.write("artifacts/publication_campaign/fixture/campaign_state.json", state)
        return state

    def assert_blocked(self, substring):
        self.assertIn(substring, "\n".join(self.plan()["preflight_errors"]))

    def test_no_amendment_source_drift_remains_blocked(self):
        self.make_record()
        self.assert_blocked("without an audited runtime amendment")

    def test_valid_engine_only_amendment_preserves_science_jobs_seeds_and_ledger(self):
        from publication.campaign import _plan_identity
        record = self.make_record()
        self.commit_record(record)
        approved = self.plan()
        self.assertEqual(approved["preflight_errors"], [])
        self.assertEqual(approved["scientific_config_sha256"], self.original_plan["scientific_config_sha256"])
        self.assertEqual(approved["jobs"], self.original_plan["jobs"])
        self.assertEqual(_plan_identity(approved), _plan_identity(self.original_plan))
        self.assertEqual(self.frozen_path.read_bytes(), self.original_ledger)
        self.assertEqual(approved["runtime_amendments"]["amendments"], record["amendments"])

    def test_exact_two_operational_source_paths_are_supported(self):
        self.commit_record(self.make_record([self.engine_path, self.plan_path]))
        self.assertEqual(self.plan()["preflight_errors"], [])

    def test_uncommitted_record_and_source_remain_blocked(self):
        record = self.make_record()
        self.write(self.record_path, record)
        self.assert_blocked("record is not committed")
        self.commit("Commit record")
        self.write(self.engine_path, b"unreviewed = True\n")
        self.assert_blocked("sources differ from committed HEAD")

    def test_uncommitted_tampering_of_record_is_blocked(self):
        record = self.make_record()
        self.commit_record(record)
        record["amendments"][0]["reason"] = "Changed after commit"
        self.write(self.record_path, record)
        self.assert_blocked("record differs from committed HEAD")

    def test_committed_rewrite_of_old_entry_is_not_append_only(self):
        record = self.make_record()
        self.commit_record(record)
        record["amendments"][0]["reason"] = "Retroactively rewritten"
        self.commit_record(record)
        self.assert_blocked("not append-only")

    def test_deleted_amendment_cannot_hide_history_even_after_source_revert(self):
        record = self.make_record()
        self.commit_record(record)
        self.record_path.unlink()
        self.write(self.engine_path, b"original = True\n")
        self.commit("Deliberate invalid removal fixture")
        self.assert_blocked("cannot be deleted")

    def test_inference_source_cannot_be_approved_by_runtime_amendment(self):
        self.commit_record(self.make_record([self.inference_path]))
        self.assert_blocked("exact operational-source allowlist")

    def test_extra_committed_source_drift_is_not_covered_by_engine_approval(self):
        record = self.make_record()
        self.write(self.inference_path, b"unauthorized_science = True\n")
        self.commit_record(record)
        self.assert_blocked("differs from frozen sources plus exact approved")

    def test_protocol_change_is_blocked_despite_valid_runtime_approval(self):
        record = self.make_record()
        self.commit_record(record)
        protocol = json.loads(self.protocol_path.read_text())
        protocol["inference"]["prior"] = "changed"
        self.write(self.protocol_path, protocol)
        self.commit("Deliberately altered scientific protocol fixture")
        self.assert_blocked("Scientific config/protocol changed")
        self.assert_blocked("Declared jobs/seeds differ")

    def test_frozen_plan_byte_mismatch_is_blocked(self):
        record = self.make_record()
        record["frozen_plan_sha256"] = "0" * 64
        self.commit_record(record)
        self.assert_blocked("frozen-plan identity mismatch")

    def test_broken_source_hash_chain_is_blocked(self):
        record = self.make_record()
        record["amendments"][0]["changes"][self.engine_path]["from_sha256"] = "0" * 64
        self.commit_record(record)
        self.assert_blocked("SHA-256 chain is invalid")

    def test_target_hash_must_match_approved_source_commit(self):
        previous_commit = self.git("rev-parse", "HEAD")
        record = self.make_record()
        record["amendments"][0]["approved_source_commit"] = previous_commit
        self.commit_record(record)
        self.assert_blocked("does not contain the declared target bytes")

    def test_approved_source_commit_must_be_ancestor(self):
        record = self.make_record()
        tree = self.git("rev-parse", "HEAD^{tree}")
        orphan = self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit-tree", tree, "-m", "Unrelated root commit")
        record["amendments"][0]["approved_source_commit"] = orphan
        self.commit_record(record)
        self.assert_blocked("not an ancestor")

    def test_validation_evidence_must_be_safe_immutable_and_committed(self):
        record = self.make_record()
        self.commit_record(record)
        evidence = record["amendments"][0]["validation_evidence"][0]
        self.write(evidence["path"], {"status": "tampered"})
        self.assert_blocked("evidence differs from committed checksum")

    def test_validation_evidence_path_cannot_escape_repository(self):
        record = self.make_record()
        record["amendments"][0]["validation_evidence"][0]["path"] = "../outside.json"
        self.commit_record(record)
        self.assert_blocked("Unsafe relative path")

    def test_duplicate_json_change_keys_are_rejected(self):
        record = self.make_record()
        content = json.dumps(record)
        key = json.dumps(self.engine_path)
        change = json.dumps(record["amendments"][0]["changes"][self.engine_path])
        content = content.replace(key + ": " + change, key + ": " + change + ", " + key + ": " + change)
        self.write(self.record_path, content.encode())
        self.commit("Duplicate JSON key fixture")
        self.assert_blocked("Duplicate runtime amendment JSON key")

    def test_append_second_amendment_retains_first_and_extends_exact_hash_chain(self):
        record = self.make_record()
        self.commit_record(record)
        before = sha256_file(self.root / self.engine_path)
        self.write(self.engine_path, b"second_operational_repair = True\n")
        source_commit = self.commit("Second reviewed operational repair")
        evidence_path = "publication/validation/runtime_repair_002.json"
        self.write(evidence_path, {"status": "passed", "source_commit": source_commit})
        record["amendments"].append({"amendment_id": "runtime_002", "reason": "Second independently audited repair",
            "approved_source_commit": source_commit,
            "changes": {self.engine_path: {"from_sha256": before, "to_sha256": sha256_file(self.root / self.engine_path)}},
            "validation_evidence": [{"path": evidence_path, "sha256": sha256_file(self.root / evidence_path)}]})
        self.commit_record(record)
        self.assertEqual(self.plan()["preflight_errors"], [])
        self.assertEqual(self.frozen_path.read_bytes(), self.original_ledger)

    def test_runtime_amendment_does_not_allow_refreezing_initialized_campaign(self):
        self.commit_record(self.make_record())
        self.write("artifacts/publication_campaign/fixture/campaign_state.json", {"status": "STOPPED"})
        with self.assertRaises(FileExistsError):
            freeze_plan(self.root, self.config_path)
        self.assertEqual(self.frozen_path.read_bytes(), self.original_ledger)

    def test_initialized_campaign_accepts_only_original_launch_ledger(self):
        from publication.campaign import _plan_identity
        self.initialize()
        self.commit_record(self.make_record())
        approved = self.plan()
        self.assertEqual(approved["preflight_errors"], [])
        self.assertEqual(_plan_identity(approved), _plan_identity(self.original_plan))
        self.assertEqual(approved["jobs"], self.original_plan["jobs"])

    def test_first_amendment_cannot_launder_scientific_source_via_rewritten_ledger(self):
        self.initialize()
        self.write(self.inference_path, b"unapproved_scientific_change = True\n")
        record = self.make_record()
        ledger = json.loads(self.frozen_path.read_text())
        ledger["source_checksums"][self.inference_path] = sha256_file(self.root / self.inference_path)
        self.write(self.frozen_path, ledger)
        record["frozen_plan_sha256"] = sha256_file(self.frozen_path)
        self.commit_record(record)
        self.assert_blocked("ledger differs from its initialization commit")

    def test_legitimate_prelaunch_ledger_updates_are_not_bound_to_first_git_blob(self):
        ledger = json.loads(self.frozen_path.read_text())
        ledger["seed_policy"] += " Clarified before initialization."
        self.write(self.frozen_path, ledger)
        self.commit("Legitimate prelaunch ledger clarification")
        self.assertEqual(self.plan()["preflight_errors"], [])
        launch_bytes = self.frozen_path.read_bytes()
        self.initialize()
        self.commit_record(self.make_record())
        self.assertEqual(self.plan()["preflight_errors"], [])
        self.assertEqual(self.frozen_path.read_bytes(), launch_bytes)

    def test_initialized_campaign_requires_valid_original_source_commit(self):
        state = self.initialize()
        for invalid in (None, "not-a-commit", "f" * 40):
            with self.subTest(commit=invalid):
                state["code_commit"] = invalid
                self.write("artifacts/publication_campaign/fixture/campaign_state.json", state)
                self.assert_blocked("source commit")

    def test_initialization_commit_without_frozen_ledger_is_blocked(self):
        self.initialize(self.git("rev-parse", "HEAD^"))
        self.assertTrue(self.plan()["preflight_errors"])

    def test_unreadable_existing_checkpoint_cannot_fall_back_to_prelaunch(self):
        self.initialize()
        with patch("publication.campaign._read", side_effect=FileNotFoundError("transient atomic replacement")):
            self.assert_blocked("initialization checkpoint is unavailable")

    def test_missing_state_in_existing_namespace_fails_closed(self):
        namespace = self.root / "artifacts/publication_campaign/fixture"
        namespace.mkdir(parents=True)
        self.assert_blocked("initialization checkpoint is unavailable")

    def test_false_exists_during_atomic_rename_does_not_bypass_ledger_guard(self):
        self.initialize()
        ledger = json.loads(self.frozen_path.read_text())
        ledger["seed_policy"] = "changed after launch"
        self.write(self.frozen_path, ledger)
        self.commit("Invalid postlaunch ledger change")
        real_exists = Path.exists
        def state_temporarily_absent(path):
            return False if path.name == "campaign_state.json" else real_exists(path)
        with patch.object(Path, "exists", state_temporarily_absent):
            self.assert_blocked("ledger differs from its initialization commit")

    def test_corrupted_initialization_journal_cannot_authorize_an_amendment(self):
        state = self.initialize()
        state["events"][0]["payload"]["scientific_config_sha256"] = "0" * 64
        self.write("artifacts/publication_campaign/fixture/campaign_state.json", state)
        self.assert_blocked("initialization journal is invalid")


if __name__ == "__main__":
    unittest.main()
