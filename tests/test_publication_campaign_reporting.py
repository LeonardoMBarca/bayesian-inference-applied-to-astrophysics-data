from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from publication.campaign_reporting import (  # noqa: E402
    ablation_report,
    aggregate_campaign,
    benchmark_report,
    calibration_report,
    collect_campaign,
    state_fingerprint,
    validate_campaign_report,
)
from publication.contracts import sha256_file  # noqa: E402


def dump(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


class PublicationCampaignReportingTests(unittest.TestCase):
    def fixture(self, root: Path) -> tuple[dict, dict]:
        jobs = []
        for replicate in range(4):
            identifier = f"PUB-02__fixture__rep_{replicate:04d}"
            jobs.append({"job_id": identifier, "experiment_id": "PUB-02", "scenario_id": "fixture",
                         "replicate_id": f"rep_{replicate:04d}", "run_id": "report_fixture", "seeds": {"inference": replicate + 1},
                         "output_dir": f"artifacts/publication_campaign/report_fixture/runs/{identifier}",
                         "payload": {"kind": "synthetic"}})
        plan = {"campaign_id": "report_fixture", "mode": "smoke", "scientific_config_sha256": "config",
                "jobs": jobs, "config_path": "config.json", "protocols": {}, "phase_order": ["PUB-02", "PUB-03", "PUB-04", "PUB-05"], "preflight_errors": []}
        state = {"campaign_id": plan["campaign_id"], "scientific_config_sha256": "config", "status": "STOPPED", "jobs": {}}
        for index, job in enumerate(jobs):
            row = {**job, "status": ["COMPLETED", "COMPLETED_REJECTED", "FAILED_TECHNICAL", "PLANNED"][index], "attempts": []}
            state["jobs"][job["job_id"]] = row
            if index == 3:
                continue
            attempt_dir = root / job["output_dir"] / "attempt_000"
            attempt_dir.mkdir(parents=True)
            (attempt_dir / "input.csv").write_text("value\n1\n", encoding="utf-8")
            checksum = sha256_file(attempt_dir / "input.csv")
            parameter = {"mean": [.1, .11, .1][index], "median": .1, "sd": .01,
                         "intervals": {"0.5": [.095, .105], "0.8": [.09, .11], "0.94": [.08, .12]}}
            result = {"status": ["completed", "rejected", "failed"][index], "input_sha256": checksum, "dataset_id": "fixture-data",
                      "gates": {"provenance": True, "sampler": index < 2, "ppc": index == 0, "scientific": index == 0},
                      "parameters": {"r": parameter} if index < 2 else {}}
            dump(attempt_dir / "result.json", result)
            dump(attempt_dir / "truth.json", {"truth": {"r": .1}, "data_sha256": checksum})
            completion = {"status": row["status"], "gates": result["gates"], "input_sha256": checksum, "dataset_id": "fixture-data",
                          "artifacts": {name: sha256_file(attempt_dir / name) for name in ("result.json", "truth.json", "input.csv")}}
            dump(attempt_dir / "completion_manifest.json", completion)
            row["attempts"].append({"attempt_index": 0, "status": row["status"], "output_dir": attempt_dir.relative_to(root).as_posix(),
                                    "seeds": job["seeds"], "completion_manifest_sha256": sha256_file(attempt_dir / "completion_manifest.json")})
        dump(root / "config.json", {"campaign_id": plan["campaign_id"]})
        dump(root / "artifacts/publication_campaign/report_fixture/campaign_state.json", state)
        return plan, state

    def test_full_denominator_and_all_attempts_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan, state = self.fixture(root)
            evidence = collect_campaign(root, plan, state)
            self.assertEqual(len(evidence["jobs"]), 4)
            self.assertEqual(len(evidence["attempts"]), 3)
            self.assertEqual(evidence["integrity_errors"], [])
            self.assertEqual(sum(row["scientifically_interpretable"] for row in evidence["jobs"]), 0)
            self.assertEqual(sum(row["computational_gates_passed"] for row in evidence["jobs"]), 1)
            self.assertEqual(evidence["jobs"][3]["status"], "PLANNED")

    def test_changed_artifact_never_promotes_but_is_retained(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan, state = self.fixture(root)
            target = root / plan["jobs"][0]["output_dir"] / "attempt_000/result.json"
            target.write_text("{}", encoding="utf-8")
            evidence = collect_campaign(root, plan, state)
            self.assertTrue(evidence["integrity_errors"])
            self.assertIsNone(evidence["jobs"][0]["result"])
            self.assertFalse(evidence["jobs"][0]["scientifically_interpretable"])
            self.assertEqual(len(evidence["attempts"]), 3)

    def test_current_blocked_and_latest_partial_never_fall_back_to_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan, state = self.fixture(root)
            row = state["jobs"][plan["jobs"][0]["job_id"]]
            row["status"] = "BLOCKED"
            evidence = collect_campaign(root, plan, state)
            self.assertIsNone(evidence["jobs"][0]["result"])
            row["status"] = "CANCELLED"
            row["attempts"].append({"attempt_index": 1, "status": "CANCELLED", "output_dir": row["output_dir"] + "/attempt_001", "seeds": row["seeds"]})
            evidence = collect_campaign(root, plan, state)
            self.assertEqual(len(evidence["attempts"]), 4)
            self.assertIsNone(evidence["jobs"][0]["result"])

    def test_regeneration_coverage_and_bookkeeping_freshness(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan, state = self.fixture(root)
            with patch("publication.campaign_reporting.build_plan", return_value=plan):
                output = aggregate_campaign(root, Path("config.json"))
            summary = json.loads((output / "summary.json").read_text())
            self.assertEqual(summary["declared_jobs"], 4)
            self.assertEqual(summary["total_attempts"], 3)
            self.assertEqual(summary["scientifically_interpretable_count"], 0)
            self.assertEqual(summary["computational_gates_passed_count"], 1)
            self.assertTrue((output / "campaign_summary.md").exists())
            metrics = summary["families"]["PUB-02"]["scenarios"]["fixture"]
            self.assertEqual(metrics["declared_count"], 4)
            self.assertEqual(metrics["parameters"]["r"]["numeric_count"], 2)
            self.assertAlmostEqual(metrics["parameters"]["r"]["bias"], .005)
            self.assertEqual(metrics["parameters"]["r"]["coverage"]["0.94"]["operational_covered_and_passed_rate_all_declared"], .25)
            validate_campaign_report(root, output)
            state["aggregate"] = {"status": "COMPLETED"}
            state_path = root / "artifacts/publication_campaign/report_fixture/campaign_state.json"
            dump(state_path, state)
            validate_campaign_report(root, output)
            state["jobs"][plan["jobs"][3]["job_id"]]["status"] = "RUNNING"
            dump(state_path, state)
            with self.assertRaisesRegex(ValueError, "job state changed"):
                validate_campaign_report(root, output)

    def test_fingerprint_order_independent_but_seed_sensitive(self) -> None:
        first = {"jobs": {"b": {"job_id": "b", "attempts": [], "seeds": {"generation": 1}},
                          "a": {"job_id": "a", "attempts": []}}}
        second = {"jobs": dict(reversed(list(first["jobs"].items())))}
        self.assertEqual(state_fingerprint(first), state_fingerprint(second))
        second = copy.deepcopy(second)
        second["jobs"]["b"]["seeds"]["generation"] = 2
        self.assertNotEqual(state_fingerprint(first), state_fingerprint(second))

    def test_presampling_negative_control_is_rejected_not_technical_or_sampler_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan, state = self.fixture(root)
            job = plan["jobs"][1]
            job["payload"] = {"kind": "ablation", "intervention": "invalid_input_hash", "variant_id": "invalid_input_hash", "pair_id": "fixture"}
            row = state["jobs"][job["job_id"]]
            attempt = root / row["attempts"][0]["output_dir"]
            result = {"status": "failed", "failure_stage": "input_validation", "failure_code": "input_sha256_mismatch", "gates": {name: False for name in ("provenance", "sampler", "ppc", "scientific")}}
            dump(attempt / "result.json", result)
            completion = json.loads((attempt / "completion_manifest.json").read_text())
            completion.update(expected_identity_rejection=True, gates=result["gates"])
            completion["artifacts"]["result.json"] = sha256_file(attempt / "result.json")
            dump(attempt / "completion_manifest.json", completion)
            row["attempts"][0]["completion_manifest_sha256"] = sha256_file(attempt / "completion_manifest.json")
            evidence = collect_campaign(root, plan, state)
            self.assertEqual(evidence["integrity_errors"], [])
            self.assertIsNotNone(evidence["jobs"][1]["result"])
            report = ablation_report([evidence["jobs"][1]], root / "ablation")
            self.assertEqual(report["gate_matrix"][0]["gate_provenance"], False)
            self.assertIsNone(report["gate_matrix"][0]["gate_sampler"])
            self.assertIsNone(report["gate_matrix"][0]["gate_ppc"])
            calibration = calibration_report([evidence["jobs"][1]], root / "calibration", mode="smoke")
            self.assertEqual(calibration["scenarios"]["fixture"]["execution_failure_rate_all_declared"], 0)
            self.assertEqual(calibration["scenarios"]["fixture"]["gates"]["sampler"]["evaluated_count"], 0)

    def test_failed_benchmark_is_unavailable_not_false_agreement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = [{"payload": {"kind": f"benchmark_{engine}"}, "result": {"status": "failed"}} for engine in ("local", "external")]
            report = benchmark_report(root, rows, root)
            self.assertEqual(report["status"], "unavailable")
            self.assertNotIn("comparison", report)

    def test_incomplete_ablation_pairs_are_unavailable_not_zero(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan, state = self.fixture(root)
            rows = collect_campaign(root, plan, state)["jobs"]
            for index, row in enumerate(rows[:2]):
                row["payload"] = {"pair_id": "fixture", "variant_id": "baseline" if index == 0 else "global"}
                row["replicate_id"] = "rep_0000"
            rows[1]["result"] = None
            output = root / "derived"
            report = ablation_report(rows[:2], output)
            effects = [row for row in report["paired_effects"] if row["variant_id"] == "global"]
            self.assertEqual(len(effects), 7)
            self.assertTrue(all(not row["pair_complete_numeric"] and row["mean_shift"] is None for row in effects))


if __name__ == "__main__":
    unittest.main()
