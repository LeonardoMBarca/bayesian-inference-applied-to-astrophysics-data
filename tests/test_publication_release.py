"""Publication release checks fail closed without running scientific MCMC."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from publication.contracts import (  # noqa: E402
    RunIdentity,
    committed_protocol,
    initialize_registry,
    register_experiment,
    reserve_run,
    update_run_status,
)
from publication.release import (  # noqa: E402
    bind_artifact,
    build_reproducibility_manifest,
    main,
    reference,
    validate_publication_release,
    verify_aggregate,
    verify_artifact,
    verify_claim,
    verify_m6_disposition,
    verify_reference,
    verify_reproducibility_manifest,
    verify_runtime,
)


class PublicationReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, relative: str, payload) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        content = payload if isinstance(payload, str) else json.dumps(payload)
        path.write_text(content, encoding="utf-8", newline="\n")
        return path

    def artifact(self) -> dict:
        self.write("publication/source.json", {"all_attempts": ["failed", "completed"]})
        self.write("publication/figure.svg", "<svg/>")
        return bind_artifact(self.root, "publication/figure.svg", artifact_id="coverage",
                             kind="figure", source_paths=["publication/source.json"],
                             experiment_ids=["PUB-02"], regenerate_command="python scripts/render.py")

    def test_source_change_invalidates_unchanged_figure(self) -> None:
        item = self.artifact()
        verify_artifact(self.root, item)
        self.write("publication/source.json", {"all_attempts": ["completed"]})
        with self.assertRaisesRegex(ValueError, "stale"):
            verify_artifact(self.root, item)

    def test_artifact_change_or_path_escape_is_rejected(self) -> None:
        item = self.artifact()
        self.write("publication/figure.svg", "<svg>unrecorded edit</svg>")
        with self.assertRaises(ValueError):
            verify_artifact(self.root, item)
        with self.assertRaises(ValueError):
            verify_reference(self.root, {"path": "../outside", "sha256": "0" * 64})
        with self.assertRaises(ValueError):
            bind_artifact(self.root, "publication/figure.svg", artifact_id="bad", kind="figure",
                          source_paths=["publication/figure.svg"], experiment_ids=[], regenerate_command="true")

    def test_failed_declared_attempt_cannot_disappear_from_aggregate(self) -> None:
        runs = [{"path": "publication/experiments/PUB-02/a/rep_0000/final", "status": "completed"},
                {"path": "publication/experiments/PUB-02/a/rep_0001/final", "status": "failed"}]
        sources = {}
        for run in runs:
            relative = run["path"] + "/result.json"
            self.write(relative, {"status": run["status"]})
            sources[relative] = reference(self.root, relative)["sha256"]
        payload = {"experiment_id": "PUB-02", "declared_run_paths": [row["path"] for row in runs],
                   "result_source_sha256": sources}
        self.write("publication/aggregate.json", payload)
        item = bind_artifact(self.root, "publication/aggregate.json", artifact_id="calibration",
                             kind="aggregate", source_paths=list(sources), experiment_ids=["PUB-02"],
                             regenerate_command="python scripts/aggregate.py")
        verify_aggregate(self.root, item, runs)
        payload["declared_run_paths"].pop()
        self.write("publication/aggregate.json", payload)
        with self.assertRaisesRegex(ValueError, "every declared attempt"):
            verify_aggregate(self.root, item, runs)

    def test_positive_claim_cannot_use_rejected_run_but_negative_can(self) -> None:
        run_path = "publication/experiments/PUB-04/a/rep_0001/final"
        runs = {run_path: {"status": "rejected", "experiment_id": "PUB-04"}}
        results = {run_path: {"gates": {"scientific": False}}}
        artifacts = {"failure_table": {"experiment_ids": ["PUB-04"]}}
        claim = {"claim_id": "convergence_is_insufficient", "kind": "negative", "text": "A declared control was rejected.",
                 "support_runs": [run_path], "source_artifacts": ["failure_table"]}
        verify_claim(claim, runs, results, artifacts)
        claim["kind"] = "positive"
        with self.assertRaisesRegex(ValueError, "rejected/failed/ungated"):
            verify_claim(claim, runs, results, artifacts)
        runs[run_path]["status"] = "completed"
        with self.assertRaises(ValueError):
            verify_claim(claim, runs, results, artifacts)
        results[run_path]["gates"]["scientific"] = True
        with self.assertRaisesRegex(ValueError, "ungated"):
            verify_claim(claim, runs, results, artifacts)
        results[run_path]["gates"].update(provenance=True, sampler=True, ppc=True)
        verify_claim(claim, runs, results, artifacts)

    def test_pilot_or_undeclared_claim_support_is_rejected(self) -> None:
        claim = {"claim_id": "bad", "kind": "positive", "text": "Unsupported",
                 "support_runs": ["publication/experiments/PUB-02/a/rep_0/pilot"], "source_artifacts": ["plot"]}
        with self.assertRaisesRegex(ValueError, "undeclared, pilot"):
            verify_claim(claim, {}, {}, {"plot": {"experiment_ids": ["PUB-02"]}})

    def test_runtime_lock_mismatch_or_empty_lock_fails(self) -> None:
        environment = {"python_version": "3.14.6", "expected_python_version": "3.14.6",
                       "packages": {"numpy": {"installed": "2.4.6", "expected": "2.4.6"}}}
        verify_runtime(environment)
        environment["packages"]["numpy"]["installed"] = "2.0.0"
        with self.assertRaises(ValueError):
            verify_runtime(environment)
        environment["packages"] = {}
        with self.assertRaises(ValueError):
            verify_runtime(environment)

    def test_m6_cannot_be_silently_skipped(self) -> None:
        with self.assertRaisesRegex(ValueError, "protocol-backed"):
            verify_m6_disposition(self.root, {}, {"PUB-06": {"expected_runs": []}})

    def test_m6_omission_requires_blocking_evidence_and_forbids_claims(self) -> None:
        self.write("publication/blocker.json", {"status": "failed", "reason": "declared upstream experiment unresolved"})
        self.write("publication/m6_protocol.json", {
            "experiment_id": "PUB-06", "execution_disposition": "methodologically_blocked",
            "blocking_evidence": [reference(self.root, "publication/blocker.json")],
            "m6_scientific_claims_allowed": False,
        })
        manifest = {"m6_disposition": {"mode": "methodologically_blocked", "reason": "P2-P4 not methodologically resolved",
                                       "protocol": {"path": "publication/m6_protocol.json"},
                                       "limitation_artifact_id": "m6_limit"},
                    "artifacts": [{"artifact_id": "m6_limit", "kind": "limitation", "experiment_ids": ["PUB-06"]}],
                    "claims": []}
        with patch("publication.release._verify_protocol"):
            verify_m6_disposition(self.root, manifest, {})
            manifest["claims"] = [{"kind": "positive", "source_artifacts": ["m6_limit"]}]
            with self.assertRaisesRegex(ValueError, "cannot support"):
                verify_m6_disposition(self.root, manifest, {})

    def test_empty_repository_audit_is_explicitly_incomplete(self) -> None:
        initialize_registry(self.root)
        report = validate_publication_release(self.root)
        self.assertFalse(report["release_passed"])
        failed = {item["check"] for item in report["checks"] if item["status"] == "failed"}
        self.assertTrue({"required_family:PUB-02", "required_family:PUB-03", "required_family:PUB-04", "required_family:PUB-05"}.issubset(failed))
        self.assertEqual(report["declared_final_attempts"], 0)

    def test_reproducibility_manifest_is_non_circular_and_carries_incompleteness(self) -> None:
        initialize_registry(self.root)
        audit = {"status": "incomplete", "release_passed": False, "environment": {}, "declared_final_attempts": 0}
        self.write("REPRODUCIBILITY_MANIFEST.json", {"old": "must not bind itself"})
        payload = build_reproducibility_manifest(self.root, audit)
        self.assertFalse(payload["release_passed"])
        self.assertNotIn("REPRODUCIBILITY_MANIFEST.json", [item["path"] for item in payload["evidence"]])
        self.assertIn("publication/paper_artifact_manifest.json", payload["missing_evidence"])

    def test_reproducibility_manifest_refuses_circular_or_incomplete_evidence(self) -> None:
        self.write("REPRODUCIBILITY_MANIFEST.json", {"schema_version": "publication-reproducibility-v1",
                                                   "missing_evidence": ["missing.json"]})
        with self.assertRaisesRegex(ValueError, "incomplete"):
            verify_reproducibility_manifest(self.root)
        self.write("REPRODUCIBILITY_MANIFEST.json", {"schema_version": "publication-reproducibility-v1", "missing_evidence": [],
                                                   "evidence": [{"path": "REPRODUCIBILITY_MANIFEST.json", "sha256": "0"*64}]})
        with self.assertRaisesRegex(ValueError, "circular"):
            verify_reproducibility_manifest(self.root)

    def test_default_cli_fails_but_audit_mode_records_failure_without_approval(self) -> None:
        initialize_registry(self.root)
        with patch.object(sys, "argv", ["validator", "--root", str(self.root)]):
            with self.assertRaises(SystemExit) as caught:
                main()
        self.assertEqual(caught.exception.code, 1)
        with patch.object(sys, "argv", ["validator", "--root", str(self.root), "--audit", "--write-manifest"]):
            main()
        report = json.loads((self.root / "publication/release_audit.json").read_text())
        manifest = json.loads((self.root / "REPRODUCIBILITY_MANIFEST.json").read_text())
        self.assertFalse(report["release_passed"])
        self.assertFalse(manifest["release_passed"])

    def test_complete_negative_evidence_fixture_can_pass_without_promoting_success(self) -> None:
        """Exercise real Git/protocol/run contracts; only baseline/runtime are fixtures."""
        def git(*args):
            return subprocess.check_output(["git", "-C", str(self.root), *args], stderr=subprocess.PIPE)

        def commit():
            git("add", ".")
            git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "Fixture evidence")

        git("init", "-b", "publication-grade-validation")
        self.write(".gitattributes", "* text eol=lf\n")
        for relative, content in {"requirements.txt": "numpy==1.0.0\n", "environment.yml": "dependencies:\n - python=3.14.6\n",
                                  "pyproject.toml": '[project]\nname="fixture"\n',
                                  "CITATION.cff": "cff-version: 1.2.0\ntitle: Fixture\nauthors:\n - family-names: Test\n   given-names: Only\nrepository-code: https://example.invalid\nlicense: MIT\n",
                                  "publication/baseline/manifest.json": "{}"}.items():
            self.write(relative, content)
        self.write("data/raw/_manifests/raw_data_current_state.json", {"fixture_only": True})
        initialize_registry(self.root)
        families = ["PUB-02", "PUB-03", "PUB-04", "PUB-05"]
        for family in families:
            self.write(f"publication/protocols/{family}.json", {"experiment_id": family, "protocol_status": "FROZEN"})
        commit()
        protocols = {family: committed_protocol(self.root, f"publication/protocols/{family}.json") for family in families}
        identities = {family: RunIdentity(family, "control", "rep_0000", "final_001") for family in families}
        for family in families:
            register_experiment(self.root, family, protocols[family], [identities[family]])
        commit()
        artifacts = []
        claims = []
        for family in families:
            identity = identities[family]
            run_path = reserve_run(self.root, identity, {}, protocols[family])
            result_path = identity.relative_path + "/result.json"
            self.write(result_path, {"status": "rejected", "gates": {"scientific": False}})
            checksums_path = identity.relative_path + "/checksums.json"
            self.write(checksums_path, {"artifacts": {"result.json": reference(self.root, result_path)["sha256"]}})
            update_run_status(run_path, "rejected", reason="Synthetic fixture, no scientific inference", evidence={
                "result_sha256": reference(self.root, result_path)["sha256"],
                "checksums_sha256": reference(self.root, checksums_path)["sha256"],
            })
            aggregate_path = f"publication/{family}/aggregate.json"
            self.write(aggregate_path, {"experiment_id": family, "declared_run_paths": [identity.relative_path],
                                       "result_source_sha256": {result_path: reference(self.root, result_path)["sha256"]}})
            artifacts.append(bind_artifact(self.root, aggregate_path, artifact_id=family + "_aggregate", kind="aggregate",
                                           source_paths=[result_path], experiment_ids=[family], regenerate_command="fixture aggregate"))
            for kind, suffix in [("figure", "svg"), ("report", "md"), ("table", "csv")]:
                relative = f"publication/{family}/{kind}.{suffix}"
                self.write(relative, "explicitly rejected fixture result")
                artifacts.append(bind_artifact(self.root, relative, artifact_id=family + "_" + kind, kind=kind,
                                               source_paths=[aggregate_path], experiment_ids=[family], regenerate_command="fixture report"))
            claims.append({"claim_id": family + "_negative", "kind": "negative", "text": "Fixture rejected, no positive claim.",
                           "support_runs": [identity.relative_path], "source_artifacts": [family + "_table"]})
        m6_source = identities["PUB-04"].relative_path + "/result.json"
        self.write("publication/protocols/PUB-06.json", {"experiment_id": "PUB-06", "protocol_status": "FROZEN",
                                                       "execution_disposition": "methodologically_blocked",
                                                       "m6_scientific_claims_allowed": False,
                                                       "blocking_evidence": [reference(self.root, m6_source)]})
        commit()
        m6_protocol = committed_protocol(self.root, "publication/protocols/PUB-06.json")
        self.write("publication/m6_limitation.md", "Fixture block only, not a scientific conclusion.")
        artifacts.append(bind_artifact(self.root, "publication/m6_limitation.md", artifact_id="m6_limit", kind="limitation",
                                       source_paths=["publication/protocols/PUB-06.json"], experiment_ids=["PUB-06"], regenerate_command="fixture limitation"))
        self.write("publication/benchmark_requirements.txt", "fixture-benchmark==1.0\n")
        self.write("publication/benchmark_environment.json", {"python_version": "3.14.6", "packages": {"fixture-benchmark": "1.0"},
                                                              "isolated": True, "lock_files": [reference(self.root, "publication/benchmark_requirements.txt")]})
        reviews = {}
        for review in ("tests", "clean_room", "public_safety", "citation"):
            relative = f"publication/reviews/{review}.json"
            self.write(relative, {"status": "passed", "source_checksums": {"requirements.txt": reference(self.root, "requirements.txt")["sha256"]}})
            reviews[review] = reference(self.root, relative)
        self.write("publication/paper_artifact_manifest.json", {
            "schema_version": "publication-paper-artifacts-v1", "artifacts": artifacts, "claims": claims, "reviews": reviews,
            "environment_locks": [reference(self.root, name) for name in ("requirements.txt", "environment.yml", "pyproject.toml")],
            "citation": reference(self.root, "CITATION.cff"),
            "benchmark_environment": reference(self.root, "publication/benchmark_environment.json"),
            "m6_disposition": {"mode": "methodologically_blocked", "reason": "Declared fixture dependency outcome", "protocol": m6_protocol,
                               "limitation_artifact_id": "m6_limit"},
        })
        commit()
        runtime = {"python_version": "3.14.6", "expected_python_version": "3.14.6",
                   "packages": {"numpy": {"installed": "1.0.0", "expected": "1.0.0"}}}
        audit = {"status": "incomplete", "release_passed": False, "environment": runtime, "declared_final_attempts": 4}
        self.write("REPRODUCIBILITY_MANIFEST.json", build_reproducibility_manifest(self.root, audit))
        commit()
        with patch("publication.release.verify_baseline", return_value={"status": "fixture_verified"}), patch("publication.release.runtime_environment", return_value=runtime):
            report = validate_publication_release(self.root)
        self.assertTrue(report["release_passed"], report["checks"])
        self.assertEqual(report["status_counts"], {"rejected": 4})


if __name__ == "__main__":
    unittest.main()
