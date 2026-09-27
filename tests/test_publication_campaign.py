"""Exercise campaign process control with tiny workers, never scientific MCMC."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from publication.campaign import (  # noqa: E402
    CampaignBusyError,
    CampaignIntegrityError,
    CampaignLock,
    CampaignRunner,
    _atomic_json,
    _journal,
    _read,
    planned_status,
    process_identity,
    process_matches,
    read_status,
    request_stop,
    validate_completion,
    verify_report,
)

WORKER = r'''
import argparse, hashlib, json, os, sys, time
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('--attempt-dir', type=Path, required=True)
p.add_argument('--behavior', default='complete')
p.add_argument('--seed', type=int, default=37)
p.add_argument('--delay', type=float, default=0.)
a = p.parse_args()
print('WORKER_START', flush=True)
if a.behavior == 'orphan_child':
    import subprocess
    subprocess.Popen([sys.executable, '-c', "import time,sys; from pathlib import Path; time.sleep(.35); Path(sys.argv[1]).write_text('child_finished')", str(a.attempt_dir/'descendant.txt')])
    time.sleep(.05)
    os._exit(7)
time.sleep(a.delay)
if a.behavior == 'crash':
    raise SystemExit(7)
technical = a.behavior == 'technical' or (a.behavior == 'retry_once' and a.attempt_dir.name == 'attempt_000')
status = 'FAILED_TECHNICAL' if technical else 'COMPLETED_REJECTED' if a.behavior == 'reject' else 'COMPLETED'
data = ('seed,' + str(a.seed) + '\n').encode()
(a.attempt_dir/'input.csv').write_bytes(data)
result = {'status': status, 'seed': a.seed, 'gates': {'scientific': status == 'COMPLETED'}}
(a.attempt_dir/'result.json').write_text(json.dumps(result))
artifacts = {name: hashlib.sha256((a.attempt_dir/name).read_bytes()).hexdigest() for name in ['input.csv','result.json']}
manifest = {'status': status, 'artifacts': artifacts, 'gates': result['gates'], 'input_sha256': artifacts['input.csv'],
            'dataset_id': 'fixture-'+artifacts['input.csv'][:20], 'technical_retryable': a.behavior == 'retry_once',
            'error': 'deliberate fixture technical failure' if technical else None}
(a.attempt_dir/'completion_manifest.json').write_text(json.dumps(manifest))
raise SystemExit(1 if technical else 0)
'''


class PublicationCampaignTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.worker = self.root / "fixture_worker.py"
        self.worker.write_text(WORKER, encoding="utf-8", newline="\n")

    def plan(self, behaviors=("complete",), *, delay=0., max_workers=1) -> dict:
        campaign = "fixture_campaign"
        return {"campaign_id": campaign, "mode": "smoke", "scientific_config_sha256": "f"*64,
                "config_path": "fixture.json", "preflight_errors": [],
                "resources": {"max_workers": max_workers, "cores_per_run": 1, "max_campaign_hours": 1.,
                              "stop_margin_minutes": 0., "estimated_run_minutes": .01,
                              "poll_interval_seconds": .01, "checkpoint_interval_seconds": .02},
                "jobs": [{"job_id": f"job_{index}", "experiment_id": "PUB-02", "scenario_id": "fixture",
                          "replicate_id": f"rep_{index:04d}", "run_id": "smoke_001", "seeds": {"generation": 37+index},
                          "command": ["{python}", str(self.worker), "--behavior", behavior, "--seed", str(37+index), "--delay", str(delay)],
                          "output_dir": f"artifacts/publication_campaign/{campaign}/runs/job_{index}",
                          "cores": 1, "estimated_seconds": .1, "max_technical_retries": 0}
                         for index, behavior in enumerate(behaviors)],
                "phase_order": ["PUB-02"], "family_summarizers": {}}

    def wait_for(self, predicate, timeout=8.):
        deadline = time.monotonic()+timeout
        while time.monotonic() < deadline:
            try:
                value = predicate()
                if value:
                    return value
            except (OSError, ValueError, KeyError, IndexError):
                pass
            time.sleep(.02)
        self.fail("Timed out waiting for fixture process state")

    def test_completed_rejected_and_technical_failures_are_distinct_and_idempotent(self) -> None:
        plan = self.plan(("complete", "reject", "technical", "crash"))
        state = CampaignRunner(self.root, plan).run()
        self.assertEqual([row["status"] for row in state["jobs"].values()],
                         ["COMPLETED", "COMPLETED_REJECTED", "FAILED_TECHNICAL", "FAILED_TECHNICAL"])
        self.assertEqual(state["status"], "COMPLETED_WITH_FAILURES")
        old_hashes = {job_id: row["attempts"][-1].get("completion_manifest_sha256") for job_id, row in state["jobs"].items()}
        resumed = CampaignRunner(self.root, plan).run(resume=True)
        self.assertTrue(all(len(row["attempts"]) == 1 for row in resumed["jobs"].values()))
        self.assertEqual(old_hashes, {job_id: row["attempts"][-1].get("completion_manifest_sha256") for job_id, row in resumed["jobs"].items()})
        with self.assertRaises(FileExistsError):
            CampaignRunner(self.root, plan).run()

    def test_only_explicit_retryable_technical_failure_gets_same_seed_new_attempt(self) -> None:
        plan = self.plan(("retry_once", "reject"))
        for job in plan["jobs"]:
            job["max_technical_retries"] = 1
        state = CampaignRunner(self.root, plan).run()
        row = state["jobs"]["job_0"]
        self.assertEqual([attempt["status"] for attempt in row["attempts"]], ["FAILED_TECHNICAL", "COMPLETED"])
        self.assertEqual(row["attempts"][0]["input_sha256"], row["attempts"][1]["input_sha256"])
        self.assertEqual(row["attempts"][0]["seeds"], row["attempts"][1]["seeds"])
        self.assertNotEqual(row["attempts"][0]["output_dir"], row["attempts"][1]["output_dir"])
        self.assertEqual(len(state["jobs"]["job_1"]["attempts"]), 1)

    def test_changed_finished_output_blocks_instead_of_rerunning(self) -> None:
        plan = self.plan()
        state = CampaignRunner(self.root, plan).run()
        attempt = state["jobs"]["job_0"]["attempts"][0]
        (self.root / attempt["output_dir"] / "result.json").write_text("altered evidence")
        resumed = CampaignRunner(self.root, plan).run(resume=True)
        self.assertEqual(resumed["jobs"]["job_0"]["status"], "BLOCKED")
        self.assertEqual(len(resumed["jobs"]["job_0"]["attempts"]), 1)

    def test_runtime_budget_can_increase_but_job_count_or_seed_cannot_change(self) -> None:
        plan = self.plan()
        plan["resources"]["max_campaign_hours"] = .000001
        state = CampaignRunner(self.root, plan).run()
        self.assertEqual(state["status"], "STOPPED")
        self.assertEqual(state["jobs"]["job_0"]["status"], "PLANNED")
        self.assertFalse(state["jobs"]["job_0"]["attempts"])
        changed = copy.deepcopy(plan)
        changed["jobs"][0]["seeds"]["generation"] = 999
        with self.assertRaises(CampaignIntegrityError):
            CampaignRunner(self.root, changed).run(resume=True)
        plan["resources"]["max_campaign_hours"] = 1.
        completed = CampaignRunner(self.root, plan).run(resume=True)
        self.assertEqual(completed["jobs"]["job_0"]["status"], "COMPLETED")
        self.assertGreater(completed["budget"]["active_seconds"], state["budget"]["active_seconds"])

    def test_graceful_stop_finishes_current_worker_and_preserves_pending_jobs(self) -> None:
        plan = self.plan(("complete", "complete"), delay=.35)
        runner = CampaignRunner(self.root, plan)
        def stop_when_running():
            self.wait_for(lambda: _state(runner.state_path)["jobs"]["job_0"]["attempts"][0].get("process"))
            request_stop(self.root, plan["campaign_id"])
        thread = threading.Thread(target=stop_when_running)
        thread.start()
        state = runner.run()
        thread.join(timeout=5)
        self.assertEqual(state["jobs"]["job_0"]["status"], "COMPLETED")
        self.assertEqual(state["jobs"]["job_1"]["status"], "PLANNED")
        self.assertEqual(state["status"], "STOPPED")
        resumed = CampaignRunner(self.root, plan).run(resume=True)
        self.assertEqual(len(resumed["jobs"]["job_0"]["attempts"]), 1)
        self.assertEqual(resumed["status"], "COMPLETED")

    def test_os_lock_rejects_concurrent_controller(self) -> None:
        runner = CampaignRunner(self.root, self.plan())
        with CampaignLock(runner.directory / "campaign.lock"):
            with self.assertRaises(CampaignBusyError):
                CampaignRunner(self.root, self.plan()).run()
        self.assertEqual(CampaignRunner(self.root, self.plan()).run()["status"], "COMPLETED")

    def test_dead_orphan_is_preserved_cancelled_then_resumed_with_same_seeds(self) -> None:
        plan = self.plan()
        runner = CampaignRunner(self.root, plan)
        runner.state = runner._new_state()
        row = runner.state["jobs"]["job_0"]
        relative = row["output_dir"] + "/attempt_000"
        (self.root / relative).mkdir(parents=True)
        attempt = {"attempt_index": 0, "status": "RUNNING", "output_dir": relative,
                   "process": {"pid": 99999999, "start_token": "proven_dead_fixture"}, "seeds": row["seeds"]}
        row.update(status="RUNNING", attempts=[attempt])
        _atomic_json(runner.state_path, runner.state)
        state = CampaignRunner(self.root, plan).run(resume=True)
        attempts = state["jobs"]["job_0"]["attempts"]
        self.assertEqual([item["status"] for item in attempts], ["CANCELLED", "COMPLETED"])
        self.assertEqual(attempts[0]["seeds"], attempts[1]["seeds"])
        self.assertTrue((self.root / relative).is_dir())

    def test_live_orphan_after_killed_controller_is_adopted_not_duplicated(self) -> None:
        plan = self.plan(delay=1.2)
        plan_path = self.root / "plan.json"
        plan_path.write_text(json.dumps(plan))
        code = "import json,sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); from publication.campaign import CampaignRunner; CampaignRunner(Path(sys.argv[2]),json.loads(Path(sys.argv[3]).read_text())).run()"
        controller = subprocess.Popen([sys.executable, "-c", code, str(ROOT / "src"), str(self.root), str(plan_path)],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.addCleanup(lambda: controller.poll() is None and controller.kill())
        state_path = self.root / "artifacts/publication_campaign/fixture_campaign/campaign_state.json"
        record = self.wait_for(lambda: _state(state_path)["jobs"]["job_0"]["attempts"][0].get("process"))
        self.assertTrue(process_matches(record))
        controller.kill()
        controller.wait(timeout=5)
        resumed = CampaignRunner(self.root, plan).run(resume=True)
        row = resumed["jobs"]["job_0"]
        self.assertEqual(row["status"], "COMPLETED")
        self.assertEqual(len(row["attempts"]), 1)
        self.assertFalse(row["attempts"][0]["return_code_known"])
        self.assertTrue(any(event["kind"] == "live_orphan_adopted" for event in resumed["events"]))

    def test_process_token_prevents_pid_reuse_adoption(self) -> None:
        actual = process_identity(os.getpid())
        self.assertTrue(process_matches(actual))
        self.assertFalse(process_matches({**actual, "start_token": "different_process_start"}))

    def test_phase_failure_does_not_drop_following_family_and_aggregation_runs(self) -> None:
        plan = self.plan(("technical", "complete"))
        plan["phase_order"].append("PUB-03")
        plan["jobs"][1]["experiment_id"] = "PUB-03"
        aggregate = self.root / "aggregate_fixture.py"
        aggregate.write_text("from pathlib import Path\np=Path('aggregate_calls.txt')\nwith p.open('a') as f: f.write('aggregate\\n')\n")
        command = ["{python}", str(aggregate)]
        plan["family_summarizers"] = {"PUB-02": command, "PUB-03": command}
        plan["aggregate_command"] = command
        state = CampaignRunner(self.root, plan).run()
        self.assertEqual(state["jobs"]["job_1"]["status"], "COMPLETED")
        self.assertEqual(len((self.root / "aggregate_calls.txt").read_text().splitlines()), 3)
        CampaignRunner(self.root, plan).run(resume=True)
        self.assertEqual(len((self.root / "aggregate_calls.txt").read_text().splitlines()), 3)

    def test_cpu_allocation_and_parallel_worker_limit(self) -> None:
        plan = self.plan(("complete", "complete", "complete"), delay=.12, max_workers=3)
        with patch("publication.campaign.os.cpu_count", return_value=2):
            state = CampaignRunner(self.root, plan).run()
        active = maximum = 0
        for event in state["events"]:
            if event["kind"] == "worker_started":
                active += 1
                maximum = max(maximum, active)
            elif event["kind"] == "attempt_finished":
                active -= 1
        self.assertEqual(maximum, 2)
        self.assertEqual(active, 0)

    def test_preflight_failure_does_not_create_state_and_signal_requests_safe_stop(self) -> None:
        plan = self.plan()
        plan["preflight_errors"] = ["protocol is not frozen"]
        runner = CampaignRunner(self.root, plan)
        with self.assertRaises(ValueError):
            runner.run()
        self.assertFalse(runner.state_path.exists())
        runner._handle_signal(signal.SIGINT, None)
        self.assertEqual(runner.stop_reason, "signal:SIGINT")

    def test_status_is_honest_and_checksum_manifest_cannot_escape_attempt(self) -> None:
        plan = self.plan()
        state = CampaignRunner(self.root, plan).run()
        status = read_status(self.root, plan["campaign_id"])
        self.assertEqual(status["status_counts"], {"COMPLETED": 1})
        self.assertEqual(status["status_counts_by_family"], {"PUB-02": {"COMPLETED": 1}})
        self.assertNotIn("eta", status)
        attempt = self.root / state["jobs"]["job_0"]["attempts"][0]["output_dir"]
        manifest = _state(attempt / "completion_manifest.json")
        manifest["artifacts"]["../outside"] = hashlib.sha256(b"outside").hexdigest()
        _atomic_json(attempt / "completion_manifest.json", manifest)
        with self.assertRaises(ValueError):
            validate_completion(attempt)

    def test_status_distinguishes_dead_controller_from_persisted_running(self) -> None:
        runner = CampaignRunner(self.root, self.plan())
        state = runner._new_state()
        state["status"] = "RUNNING"
        _atomic_json(runner.state_path, state)
        with patch("publication.campaign.process_matches", return_value=False):
            status = read_status(self.root, "fixture_campaign")
        self.assertEqual(status["status"], "RUNNING")
        self.assertEqual(status["effective_status"], "CONTROLLER_STOPPED")
        self.assertFalse(status["controller_alive"])
        self.assertEqual(_state(runner.state_path), state)  # status must remain read-only

    def test_status_without_controller_identity_does_not_claim_liveness(self) -> None:
        runner = CampaignRunner(self.root, self.plan())
        state = runner._new_state()
        state.pop("controller_process")
        state["status"] = "RUNNING"
        _atomic_json(runner.state_path, state)
        status = read_status(self.root, "fixture_campaign")
        self.assertEqual(status["effective_status"], "LIVENESS_UNCONFIRMED")
        self.assertIsNone(status["controller_alive"])

    def test_runtime_amendment_is_journaled_without_changing_or_repeating_jobs(self) -> None:
        plan = self.plan()
        state = CampaignRunner(self.root, plan).run()
        before = state["jobs"]
        plan["runtime_amendments"] = {"path": "fixture-amendment.json", "sha256": "a" * 64,
                                      "amendments": [{"amendment_id": "runtime-only-001"}]}
        resumed = CampaignRunner(self.root, plan).run(resume=True)
        self.assertEqual(resumed["jobs"], before)
        self.assertEqual(resumed["plan_identity_sha256"], state["plan_identity_sha256"])
        self.assertTrue(any(event["kind"] == "runtime_amendment_verified" for event in resumed["events"]))
        plan.pop("runtime_amendments")
        with self.assertRaisesRegex(CampaignIntegrityError, "amendment cannot be removed"):
            CampaignRunner(self.root, plan).run(resume=True)

    def test_journal_mutation_and_output_collision_fail_closed(self) -> None:
        plan = self.plan()
        runner = CampaignRunner(self.root, plan)
        runner.state = runner._new_state()
        _journal(runner.state, "fixture_event", detail="before")
        runner.state["events"][-1]["payload"]["detail"] = "after"
        _atomic_json(runner.state_path, runner.state)
        with self.assertRaises(CampaignIntegrityError):
            CampaignRunner(self.root, plan).run(resume=True)

    def test_existing_attempt_directory_is_not_overwritten_or_retried(self) -> None:
        plan = self.plan()
        destination = self.root / plan["jobs"][0]["output_dir"] / "attempt_000"
        destination.mkdir(parents=True)
        evidence = destination / "evidence.txt"
        evidence.write_text("preserved")
        state = CampaignRunner(self.root, plan).run()
        self.assertEqual(state["jobs"]["job_0"]["status"], "BLOCKED")
        self.assertEqual(evidence.read_text(), "preserved")
        self.assertFalse(state["jobs"]["job_0"]["attempts"])
        resumed = CampaignRunner(self.root, plan).run(resume=True)
        self.assertEqual(resumed["jobs"]["job_0"]["status"], "BLOCKED")

    def test_state_read_retries_transient_missing_but_never_returns_stale_state(self) -> None:
        path = self.root / "campaign_state.json"
        with patch.object(Path, "read_text", side_effect=[FileNotFoundError(), '{"fresh": true}']) as reader:
            with patch("publication.campaign.time.sleep") as sleep:
                self.assertEqual(_read(path), {"fresh": True})
                self.assertEqual(reader.call_count, 2)
                sleep.assert_called_once_with(.02)
        with patch.object(Path, "read_text", side_effect=FileNotFoundError()) as reader:
            with patch("publication.campaign.time.sleep"):
                with self.assertRaises(FileNotFoundError):
                    _read(path)
                self.assertEqual(reader.call_count, 26)
        with patch.object(Path, "read_text", return_value="broken json") as reader:
            with self.assertRaises(ValueError):
                _read(path)
            self.assertEqual(reader.call_count, 1)

    def test_session_budget_and_runtime_resources_can_change_without_scientific_change(self) -> None:
        plan = self.plan()
        plan["resources"]["max_runtime_hours"] = .000001
        state = CampaignRunner(self.root, plan).run()
        self.assertEqual(state["stop_reason"], "runtime_session_dispatch_margin")
        self.assertEqual(state["jobs"]["job_0"]["status"], "PLANNED")
        plan["resources"]["max_runtime_hours"] = None
        plan["resources"]["cores_per_run"] = 2
        plan["jobs"][0].update(cores=2, estimated_seconds=.2)
        with patch("publication.campaign.os.cpu_count", return_value=2):
            resumed = CampaignRunner(self.root, plan).run(resume=True)
        self.assertEqual(resumed["status"], "COMPLETED")
        self.assertTrue(any(event["kind"] == "runtime_resource_change" for event in resumed["events"]))

    def test_resumed_dispatch_uses_declared_order_not_sorted_checkpoint_keys(self) -> None:
        plan = self.plan(("complete", "complete", "complete"))
        plan["jobs"] = [plan["jobs"][2], plan["jobs"][0], plan["jobs"][1]]
        plan["resources"]["max_campaign_hours"] = .000001
        CampaignRunner(self.root, plan).run()
        plan["resources"]["max_campaign_hours"] = 1.
        resumed = CampaignRunner(self.root, plan).run(resume=True)
        started = [event["payload"]["job_id"] for event in resumed["events"] if event["kind"] == "worker_started"]
        self.assertEqual(started, ["job_2", "job_0", "job_1"])
        log = self.root / "logs/publication_campaign/fixture_campaign/campaign.log"
        self.assertEqual(len(log.read_text().splitlines()), len(resumed["events"]))

    def test_aggregation_failure_is_preserved_once_and_campaign_is_not_successful(self) -> None:
        plan = self.plan()
        command = ["{python}", "-c", "raise SystemExit(4)"]
        plan["family_summarizers"] = {"PUB-02": command}
        plan["aggregate_command"] = command
        state = CampaignRunner(self.root, plan).run()
        self.assertEqual(state["jobs"]["job_0"]["status"], "COMPLETED")
        self.assertEqual(state["status"], "COMPLETED_WITH_FAILURES")
        resumed = CampaignRunner(self.root, plan).run(resume=True)
        self.assertEqual(len(resumed["aggregate"]["attempts"]), 1)
        self.assertEqual(len(resumed["family_summaries"]["PUB-02"]["attempts"]), 1)

    def test_result_status_and_gates_must_match_completion_manifest(self) -> None:
        state = CampaignRunner(self.root, self.plan()).run()
        attempt = self.root / state["jobs"]["job_0"]["attempts"][0]["output_dir"]
        manifest = _state(attempt / "completion_manifest.json")
        manifest["gates"]["scientific"] = False
        _atomic_json(attempt / "completion_manifest.json", manifest)
        with self.assertRaisesRegex(CampaignIntegrityError, "disagree"):
            validate_completion(attempt)
        result = _state(attempt / "result.json")
        result["gates"]["scientific"] = False
        _atomic_json(attempt / "result.json", result)
        manifest["artifacts"]["result.json"] = hashlib.sha256((attempt / "result.json").read_bytes()).hexdigest()
        _atomic_json(attempt / "completion_manifest.json", manifest)
        with self.assertRaisesRegex(CampaignIntegrityError, "unpassed"):
            validate_completion(attempt)

    def test_only_declared_identity_control_can_classify_input_failure_as_rejection(self) -> None:
        state = CampaignRunner(self.root, self.plan()).run()
        attempt = self.root / state["jobs"]["job_0"]["attempts"][0]["output_dir"]
        result = {"status": "failed", "failure_stage": "input_validation",
                  "gates": {"provenance": False, "sampler": False, "ppc": False, "scientific": False}}
        _atomic_json(attempt / "result.json", result)
        manifest = _state(attempt / "completion_manifest.json")
        manifest.update(status="COMPLETED_REJECTED", gates=result["gates"], expected_identity_rejection=True)
        manifest["artifacts"]["result.json"] = hashlib.sha256((attempt / "result.json").read_bytes()).hexdigest()
        _atomic_json(attempt / "completion_manifest.json", manifest)
        with self.assertRaises(CampaignIntegrityError):
            validate_completion(attempt)
        for control, code in (("invalid_input_hash", "input_sha256_mismatch"), ("dataset_identity_mismatch", "dataset_identity_mismatch")):
            with self.assertRaises(CampaignIntegrityError):
                validate_completion(attempt, declared_intervention=control)
            result["failure_code"] = code
            _atomic_json(attempt / "result.json", result)
            manifest["artifacts"]["result.json"] = hashlib.sha256((attempt / "result.json").read_bytes()).hexdigest()
            _atomic_json(attempt / "completion_manifest.json", manifest)
            self.assertEqual(validate_completion(attempt, declared_intervention=control)["status"], "COMPLETED_REJECTED")
        for wrong_control in ("baseline", "exposure_off"):
            with self.assertRaises(CampaignIntegrityError):
                validate_completion(attempt, declared_intervention=wrong_control)
        manifest["expected_identity_rejection"] = False
        _atomic_json(attempt / "completion_manifest.json", manifest)
        with self.assertRaises(CampaignIntegrityError):
            validate_completion(attempt, declared_intervention="invalid_input_hash")

    def test_completed_checkpoint_cannot_be_changed_to_planned_for_another_draw(self) -> None:
        plan = self.plan()
        state = CampaignRunner(self.root, plan).run()
        state["jobs"]["job_0"]["status"] = "PLANNED"
        state_path = self.root / "artifacts/publication_campaign/fixture_campaign/campaign_state.json"
        _atomic_json(state_path, state)
        with self.assertRaisesRegex(CampaignIntegrityError, "cannot schedule"):
            CampaignRunner(self.root, plan).run(resume=True)
        attempts = list((self.root / plan["jobs"][0]["output_dir"]).glob("attempt_*"))
        self.assertEqual(len(attempts), 1)

    @unittest.skipUnless(sys.platform.startswith("linux"), "Scientific WSL process-session guard")
    def test_killed_worker_descendant_finishes_before_attempt_can_be_resumed(self) -> None:
        state = CampaignRunner(self.root, self.plan(("orphan_child",))).run()
        row = state["jobs"]["job_0"]
        self.assertEqual(row["status"], "CANCELLED")
        self.assertEqual(len(row["attempts"]), 1)
        self.assertEqual(state["status"], "STOPPED")
        self.assertTrue((self.root / row["attempts"][0]["output_dir"] / "descendant.txt").is_file())
        self.assertTrue(any(event["kind"] == "worker_descendant_adopted" for event in state["events"]))

    def test_not_initialized_status_counts_declared_jobs_without_writing_state(self) -> None:
        plan = self.plan(("complete", "reject"))
        status = planned_status(plan)
        self.assertEqual(status["status"], "NOT_INITIALIZED")
        self.assertEqual(status["declared_jobs"], 2)
        self.assertEqual(status["attempted_jobs"], 0)
        self.assertEqual(status["status_counts_by_family"], {"PUB-02": {"PLANNED": 2}})
        self.assertFalse((self.root / "artifacts").exists())

    def test_final_environment_preflight_fails_before_any_state_or_inference(self) -> None:
        plan = self.plan()
        plan["mode"] = "final"
        runner = CampaignRunner(self.root, plan)
        with patch("publication.campaign_preflight.validate_execution_environment", side_effect=ValueError("missing locked input")):
            with self.assertRaisesRegex(ValueError, "missing locked input"):
                runner.run()
        self.assertFalse(runner.state_path.exists())
        self.assertFalse((self.root / plan["jobs"][0]["output_dir"]).exists())

    def test_report_verification_distinguishes_integrity_from_scientific_completion(self) -> None:
        summary_path = self.root / "reports/publication_campaign/fixture_campaign/summary.json"
        summary = {"mode": "smoke", "declared_jobs": 2, "status_counts": {"COMPLETED": 1, "PLANNED": 1},
                   "complete_declared_batch": False, "all_declared_scientific_jobs_finished": False,
                   "scientifically_interpretable_count": 0, "integrity_errors": []}
        _atomic_json(summary_path, summary)
        with patch("publication.campaign_reporting.validate_campaign_report"):
            verified = verify_report(self.root, "fixture_campaign")
            self.assertTrue(verified["artifact_integrity_passed"])
            self.assertFalse(verified["all_declared_scientific_jobs_finished"])
            summary["integrity_errors"] = ["declared input checksum mismatch"]
            _atomic_json(summary_path, summary)
            with self.assertRaises(CampaignIntegrityError):
                verify_report(self.root, "fixture_campaign")
        self.assertFalse((self.root / "artifacts").exists())


def _state(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
