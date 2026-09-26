"""Evidence contracts must fail closed, including missing and failed attempts."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from src.publication.contracts import (
    BASE_COMMIT,
    BASE_DATASET,
    BASE_INPUT_SHA256,
    BASE_MODEL_VERSION,
    RunIdentity,
    _events,
    append_amendment,
    canonical_hash,
    committed_protocol,
    deterministic_seed,
    generate_inventory,
    initialize_registry,
    load_registry,
    register_experiment,
    reserve_run,
    safe_path,
    sha256_file,
    update_run_status,
    verify_baseline,
    verify_run_artifacts,
)


class PublicationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def git(self, *args: str) -> str:
        return subprocess.check_output(["git", "-C", str(self.root), *args], stderr=subprocess.PIPE).decode().strip()

    def commit(self) -> None:
        self.git("add", ".")
        self.git("-c", "user.name=Test fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "-m", "Freeze temporary test fixture")

    def protocol(self) -> tuple[str, dict]:
        self.git("init", "-b", "publication-grade-validation")
        (self.root / ".gitattributes").write_bytes(
            (Path(__file__).resolve().parents[1] / ".gitattributes").read_bytes()
        )
        initialize_registry(self.root)
        relative = "publication/protocols/PUB-02.json"
        path = self.root / relative
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"experiment_id": "PUB-02", "protocol_status": "FROZEN"}) + "\n", encoding="utf-8", newline="\n")
        self.commit()
        return relative, committed_protocol(self.root, relative)

    def test_seeds_stable_separate_streams_and_ids(self) -> None:
        seed = deterministic_seed("PUB-02", "shallow", "rep_0001")
        self.assertEqual(seed, deterministic_seed("PUB-02", "shallow", "rep_0001"))
        self.assertEqual(len({seed, deterministic_seed("PUB-02", "shallow", "rep_0002"),
                              deterministic_seed("PUB-02", "shallow", "rep_0001", "inference")}), 3)
        self.assertEqual(canonical_hash({"b": 2, "a": 1}), canonical_hash({"a": 1, "b": 2}))

    def test_protocol_byte_identity_survives_windows_style_checkout(self) -> None:
        relative, protocol = self.protocol()
        self.git("config", "core.autocrlf", "true")
        (self.root / relative).unlink()  # A temporary fixture, never repository evidence.
        self.git("checkout", "HEAD", "--", relative)
        self.assertEqual(committed_protocol(self.root, relative), protocol)

    def test_terminal_artifact_verification_rejects_stale_result(self) -> None:
        identity = RunIdentity("PUB-02", "smoke", "rep_0001", "pilot_001")
        path = reserve_run(self.root, identity, {}, pilot=True)
        (path / "result.json").write_text('{"status":"failed"}', encoding="utf-8")
        hashes = {"artifacts": {"result.json": sha256_file(path / "result.json")}}
        (path / "checksums.json").write_text(json.dumps(hashes), encoding="utf-8")
        with self.assertRaises(ValueError):
            verify_run_artifacts(path)
        update_run_status(path, "failed", reason="recorded failure", evidence={
            "result_sha256": sha256_file(path / "result.json"),
            "checksums_sha256": sha256_file(path / "checksums.json"),
        })
        self.assertEqual(verify_run_artifacts(path)["status"], "failed")
        (path / "result.json").write_text('{"status":"completed"}', encoding="utf-8")
        with self.assertRaises(ValueError):
            verify_run_artifacts(path)

    def test_path_traversal_and_identifier_rejection(self) -> None:
        for relative in ["../legacy", "/tmp/escape", "C:/legacy", "publication\\escape", "publication/../models"]:
            with self.subTest(relative=relative), self.assertRaises(ValueError):
                safe_path(self.root, relative)
        for name in ["../../scientific_003", "", "UPPER", "run:bad"]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                RunIdentity("PUB-02", "scenario", "rep_001", name)

    def test_collision_and_terminal_status_are_immutable(self) -> None:
        identity = RunIdentity("PUB-02", "smoke", "rep_0001", "pilot_001")
        path = reserve_run(self.root, identity, {"draws": 4}, pilot=True)
        original = (path / "run_config.json").read_bytes()
        with self.assertRaises(FileExistsError):
            reserve_run(self.root, identity, {"draws": 999}, pilot=True)
        update_run_status(path, "failed", reason="controlled regression failure")
        with self.assertRaises(ValueError):
            update_run_status(path, "completed", reason="cannot rescue a failed run")
        self.assertEqual(original, (path / "run_config.json").read_bytes())
        self.assertEqual(_events(path / "status")[-1]["status"], "failed")

    def test_final_requires_precommitted_protocol_and_registry(self) -> None:
        relative, protocol = self.protocol()
        identity = RunIdentity("PUB-02", "shallow", "rep_0001", "final_001")
        with self.assertRaises(ValueError):
            reserve_run(self.root, identity, {}, protocol)
        register_experiment(self.root, "PUB-02", protocol, [identity])
        with self.assertRaises(ValueError):
            reserve_run(self.root, identity, {}, protocol)
        self.commit()
        path = reserve_run(self.root, identity, {}, protocol)
        self.assertEqual(_events(path / "status")[0]["status"], "running")
        (self.root / relative).write_text('{"protocol_status": "FROZEN", "changed": true}\n', encoding="utf-8")
        with self.assertRaises(ValueError):
            committed_protocol(self.root, relative)
        self.assertFalse(generate_inventory(self.root)["integrity_valid"])

    def test_final_rejects_dirty_scientific_source_before_reservation(self) -> None:
        _, protocol = self.protocol()
        identity = RunIdentity("PUB-02", "shallow", "rep_0001", "final_001")
        register_experiment(self.root, "PUB-02", protocol, [identity])
        source = self.root / "src/publication/inference.py"
        source.parent.mkdir(parents=True)
        source.write_text("model_version = 1\n", encoding="utf-8", newline="\n")
        self.commit()
        source.write_text("model_version = 2\n", encoding="utf-8", newline="\n")
        with self.assertRaisesRegex(ValueError, "committed relevant source"):
            reserve_run(self.root, identity, {}, protocol)
        self.assertFalse((self.root / identity.relative_path).exists())

    def test_aggregate_preserves_failure_and_missing_denominator(self) -> None:
        _, protocol = self.protocol()
        first = RunIdentity("PUB-02", "shallow", "rep_0001", "final_001")
        second = RunIdentity("PUB-02", "shallow", "rep_0002", "final_001")
        register_experiment(self.root, "PUB-02", protocol, [first, second])
        self.commit()
        path = reserve_run(self.root, first, {}, protocol)
        update_run_status(path, "failed", reason="sampler exception remains in denominator")
        pilot = RunIdentity("PUB-02", "shallow", "rep_0000", "pilot_001")
        reserve_run(self.root, pilot, {}, pilot=True)
        inventory = generate_inventory(self.root)
        self.assertEqual(inventory["declared_final_attempts"], 2)
        self.assertEqual(inventory["status_counts"], {"failed": 1, "missing": 1})
        self.assertEqual(len(inventory["pilot_runs"]), 1)
        self.assertFalse(inventory["all_declared_attempts_terminal"])
        with self.assertRaises(ValueError):
            register_experiment(self.root, "PUB-02", protocol, [first])

    def test_mutated_config_or_status_cannot_promote_evidence(self) -> None:
        _, protocol = self.protocol()
        identity = RunIdentity("PUB-02", "shallow", "rep_0001", "final_001")
        register_experiment(self.root, "PUB-02", protocol, [identity])
        self.commit()
        path = reserve_run(self.root, identity, {"draws": 800}, protocol)
        config_path = path / "run_config.json"
        config = json.loads(config_path.read_text())
        config["config"]["draws"] = 4
        config_path.write_text(json.dumps(config), encoding="utf-8")
        self.assertFalse(generate_inventory(self.root)["integrity_valid"])
        status_path = path / "status/000000.json"
        event = json.loads(status_path.read_text())
        event["status"] = "completed"
        status_path.write_text(json.dumps(event), encoding="utf-8")
        with self.assertRaises(ValueError):
            _events(path / "status")

    def test_amendments_append_and_preserve_previous_bytes(self) -> None:
        _, protocol = self.protocol()
        kwargs = {"reason": "documented bug", "change": "new inference version",
                  "previous_protocol": protocol, "new_protocol": protocol,
                  "runs_already_started": True, "impact_on_previous_evidence": "old results retained, not promoted"}
        append_amendment(self.root, "PUB-02", **kwargs)
        first_path = self.root / "publication/amendments/PUB-02/000000.json"
        before = first_path.read_bytes()
        append_amendment(self.root, "PUB-02", **kwargs)
        self.assertEqual(first_path.read_bytes(), before)
        self.assertEqual(len(_events(first_path.parent)), 2)

    def test_registry_rejects_duplicate_expected_attempts(self) -> None:
        initialize_registry(self.root)
        registry_path = self.root / "publication/registry.json"
        registry = json.loads(registry_path.read_text())
        run = {"experiment_id": "PUB-02", "scenario_id": "one", "replicate_id": "rep_1", "run_id": "final"}
        registry["experiments"][2]["expected_runs"] = [run, run]
        registry_path.write_text(json.dumps(registry), encoding="utf-8")
        with self.assertRaises(ValueError):
            load_registry(self.root)

    def test_baseline_mutation_is_detected_without_loading_trace(self) -> None:
        artifact = self.root / "legacy.csv"
        artifact.write_text("protected scientific evidence\n", encoding="utf-8")
        manifest = {"base_commit": BASE_COMMIT, "dataset_id": BASE_DATASET,
                    "model_version": BASE_MODEL_VERSION,
                    "modeling_input_sha256": BASE_INPUT_SHA256, "protected_refs": {},
                    "environment_lock_artifacts": [], "artifacts": [
                        {"path": "legacy.csv", "sha256": sha256_file(artifact), "storage": "git"}]}
        manifest["manifest_content_sha256"] = canonical_hash(manifest)
        path = self.root / "publication/baseline/manifest.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertEqual(verify_baseline(self.root)["status"], "verified")
        artifact.write_text("altered result\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "mutated"):
            verify_baseline(self.root)


if __name__ == "__main__":
    unittest.main()
