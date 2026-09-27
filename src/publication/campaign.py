"""Resumable, budget-aware campaign controller; never selects favorable science.

Workers own scientific decisions. This controller owns exclusive attempt paths,
process identity, resource scheduling, checkpoints and preservation of failures.
It never changes a seed, scientific configuration, rejection or finished output.
"""

from __future__ import annotations

import argparse
import errno
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from publication.contracts import canonical_hash, safe_path, sha256_file, utc_now

TERMINAL = frozenset({"COMPLETED", "COMPLETED_REJECTED", "FAILED_TECHNICAL", "BLOCKED"})
SCIENTIFIC_TERMINAL = frozenset({"COMPLETED", "COMPLETED_REJECTED"})
COMPLETION_STATUSES = TERMINAL


class CampaignBusyError(RuntimeError):
    """Another controller owns the OS lock; do not start a second controller."""


class CampaignIntegrityError(RuntimeError):
    """A frozen identity or preserved output no longer matches its checkpoint."""


def _identifier(value: Any, kind: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,180}", value):
        raise ValueError(f"Unsafe {kind}: {value!r}")
    return value


def _replace_checkpoint_with_retry(temporary: Path, path: Path, *, exclusive: bool = False) -> None:
    """Keep the fsynced candidate intact while a Windows/DrvFS reader locks it.

    Retry only sharing/access/busy replacement failures for at most 12 seconds.
    The old destination is never unlinked, opened for writing or truncated.
    A persistent failure is raised to the controller, not treated as a save.
    """
    started = time.monotonic()
    deadline, delay, failures = started + 12.0, .025, 0
    while True:
        if exclusive and path.exists():
            raise FileExistsError(path)
        try:
            os.replace(temporary, path)
        except OSError as exc:
            transient = (exc.errno in {errno.EACCES, errno.EPERM, errno.EBUSY}
                         or getattr(exc, "winerror", None) in {32, 33})
            # Disk/full-I/O failures are not sharing violations even if an
            # unusual exception also carries a Windows sharing-error attribute.
            if not transient or exc.errno in {errno.ENOSPC, errno.EIO}:
                raise
            failures += 1
            if failures == 1:
                print(f"WARNING: checkpoint atomic replacement temporarily blocked for {path}: {exc}; "
                      "retrying for at most 12 seconds without modifying the existing checkpoint.",
                      file=sys.stderr, flush=True)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                print(f"ERROR: checkpoint atomic replacement remains blocked for {path} after "
                      f"{failures} failed attempts; save failed and the existing checkpoint was not modified.",
                      file=sys.stderr, flush=True)
                raise
            time.sleep(min(delay, remaining))
            delay = min(delay * 2, .5)
            continue
        if failures:
            print(f"WARNING: checkpoint atomic replacement recovered for {path} after {failures} retries "
                  f"in {time.monotonic() - started:.3f} seconds.", file=sys.stderr, flush=True)
        return


def _atomic_json(path: Path, payload: Any, *, exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if exclusive and path.exists():
        raise FileExistsError(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent,
                                         prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if exclusive and path.exists():
            raise FileExistsError(path)
        _replace_checkpoint_with_retry(temporary, path, exclusive=exclusive)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _read(path: Path) -> Any:
    # DrvFS readers can briefly observe ENOENT during another process's replace.
    # Retry only that transient condition; never substitute stale/empty state.
    attempts = 26 if path.name == "campaign_state.json" else 1
    for index in range(attempts):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            if index == attempts - 1:
                raise
            time.sleep(.02)
    raise AssertionError("Unreachable state-read retry branch")


class CampaignLock:
    """Kernel-held lock, automatically released when its owning process dies."""

    def __init__(self, path: Path):
        self.path = path
        self.handle = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("a+b")
        if self.path.stat().st_size == 0:
            self.handle.write(b"\0")
            self.handle.flush()
        self.handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self.handle.close()
            self.handle = None
            raise CampaignBusyError(f"Another controller holds {self.path}") from exc
        return self

    def __exit__(self, *_args):
        if self.handle is not None:
            self.handle.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
            self.handle.close()


def process_identity(pid: int) -> dict[str, Any] | None:
    """Return PID plus reuse-resistant start identity, or None if provably dead.

    Linux binds PID to kernel start ticks AND boot ID. Windows uses process
    creation FILETIME. Unknown process-inspection failures are not called dead.
    """
    if pid <= 0:
        return None
    if sys.platform.startswith("linux"):
        try:
            raw = Path(f"/proc/{pid}/stat").read_text()
            fields = raw[raw.rfind(")") + 2:].split()
            if fields[0] in {"Z", "X"}:
                return None
            boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
            return {"pid": pid, "start_token": f"linux:{boot_id}:{fields[19]}", "platform": "linux",
                    "process_group": int(fields[2]), "session_id": int(fields[3])}
        except FileNotFoundError:
            return None
        except (OSError, IndexError):
            return {"pid": pid, "start_token": None, "platform": "linux", "inspection": "unknown"}
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return None if ctypes.get_last_error() == 87 else {"pid": pid, "start_token": None, "platform": "windows"}
        try:
            exit_code = wintypes.DWORD()
            if kernel.GetExitCodeProcess(handle, ctypes.byref(exit_code)) and exit_code.value != 259:
                return None
            creation, exited, system, user = (wintypes.FILETIME() for _ in range(4))
            if not kernel.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exited), ctypes.byref(system), ctypes.byref(user)):
                return {"pid": pid, "start_token": None, "platform": "windows"}
            ticks = (creation.dwHighDateTime << 32) | creation.dwLowDateTime
            return {"pid": pid, "start_token": f"windows:{ticks}", "platform": "windows"}
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return None
    except PermissionError:
        pass
    return {"pid": pid, "start_token": None, "platform": sys.platform, "inspection": "unknown"}


def process_matches(record: dict[str, Any] | None) -> bool | None:
    """True: same live process; False: dead/reused PID; None: cannot prove either."""
    if not record or not record.get("pid"):
        return None
    current = process_identity(int(record["pid"]))
    if current is None:
        return False
    if not current.get("start_token") or not record.get("start_token"):
        return None
    return current["start_token"] == record["start_token"]


def _find_attempt_process(attempt_dir: Path) -> dict[str, Any] | None:
    metadata = attempt_dir / "worker_metadata.json"
    if metadata.exists():
        try:
            value = _read(metadata)
            candidate = value.get("process_identity", value)
            if candidate.get("pid") and candidate.get("start_token"):
                return candidate
        except (OSError, ValueError, AttributeError):
            pass
    if sys.platform.startswith("linux"):
        for path in Path("/proc").glob("[0-9]*/cmdline"):
            try:
                tokens = path.read_bytes().split(b"\0")
                encoded = os.fsencode(str(attempt_dir))
                if any(tokens[index] == b"--attempt-dir" and tokens[index + 1] == encoded for index in range(len(tokens)-1)):
                    return process_identity(int(path.parent.name))
            except (OSError, ValueError):
                continue
    return None


def _live_session_descendant(record: dict[str, Any] | None) -> dict[str, Any] | None:
    """A killed worker can leave its inference/chain children writing evidence."""
    if not sys.platform.startswith("linux") or not record:
        return None
    group, session = record.get("process_group"), record.get("session_id")
    if not group or group != session:
        return None
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    if not str(record.get("start_token", "")).startswith(f"linux:{boot_id}:"):
        return None
    for path in Path("/proc").glob("[0-9]*/stat"):
        candidate = process_identity(int(path.parent.name))
        if candidate and candidate.get("process_group") == group and candidate.get("session_id") == session:
            return candidate
    return None


def validate_completion(attempt_dir: Path, *, expected_manifest_sha256: str | None = None,
                        declared_intervention: str | None = None) -> dict[str, Any]:
    path = attempt_dir / "completion_manifest.json"
    if expected_manifest_sha256 and sha256_file(path) != expected_manifest_sha256:
        raise CampaignIntegrityError("Previously completed manifest changed")
    manifest = _read(path)
    if manifest.get("status") not in COMPLETION_STATUSES:
        raise CampaignIntegrityError("Worker completion status is invalid")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict) or "result.json" not in artifacts:
        raise CampaignIntegrityError("Completion must bind result.json and its artifact hashes")
    if not isinstance(manifest.get("gates"), dict):
        raise CampaignIntegrityError("Completion must distinguish scientific gates")
    for relative, digest in artifacts.items():
        if relative == "completion_manifest.json":
            raise CampaignIntegrityError("Completion manifest cannot circularly hash itself")
        if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise CampaignIntegrityError("Invalid artifact checksum")
        file_path = safe_path(attempt_dir, relative)
        if not file_path.is_file() or sha256_file(file_path) != digest:
            raise CampaignIntegrityError(f"Worker artifact missing or changed: {relative}")
    input_hash = manifest.get("input_sha256")
    if input_hash is not None and not re.fullmatch(r"[a-f0-9]{64}", input_hash):
        raise CampaignIntegrityError("Invalid input SHA-256")
    if input_hash and "input.csv" in artifacts and artifacts["input.csv"] != input_hash:
        raise CampaignIntegrityError("Input identity differs from preserved input.csv")
    if not isinstance(manifest.get("technical_retryable", False), bool):
        raise CampaignIntegrityError("technical_retryable must be a boolean")
    result = _read(attempt_dir / "result.json")
    result_status = str(result.get("status", "")).upper()
    result_status = {"REJECTED": "COMPLETED_REJECTED", "FAILED": "FAILED_TECHNICAL"}.get(result_status, result_status)
    expected_identity_rejection = (
        declared_intervention in {"invalid_input_hash", "dataset_identity_mismatch"}
        and manifest.get("expected_identity_rejection") is True
        and result.get("failure_stage") == "input_validation"
        and result.get("failure_code") == {
            "invalid_input_hash": "input_sha256_mismatch",
            "dataset_identity_mismatch": "dataset_identity_mismatch",
        }.get(declared_intervention)
        and result.get("gates", {}).get("provenance") is False
        and result.get("gates", {}).get("scientific") is False
    )
    if result_status == "FAILED_TECHNICAL" and expected_identity_rejection:
        result_status = "COMPLETED_REJECTED"
    if result_status != manifest["status"] or result.get("gates") != manifest["gates"]:
        raise CampaignIntegrityError("Result status/gates disagree with the completion manifest")
    if manifest["status"] == "COMPLETED" and manifest["gates"].get("scientific") is not True:
        raise CampaignIntegrityError("COMPLETED cannot promote an unpassed scientific gate")
    if manifest["status"] == "COMPLETED_REJECTED" and manifest["gates"].get("scientific") is not False:
        raise CampaignIntegrityError("COMPLETED_REJECTED requires an explicit failed scientific gate")
    return manifest


def _plan_identity(plan: dict[str, Any]) -> str:
    # Budgets/worker capacity may be raised on explicit resume; scientific jobs,
    # commands, seeds, paths and ordering cannot change under a campaign ID.
    payload = {key: plan.get(key) for key in (
        "campaign_id", "mode", "scientific_config_sha256", "phase_order",
        "family_summarizers", "aggregate_command", "source_checksums", "protocol_identities",
    )}
    payload["jobs"] = [{key: value for key, value in job.items() if key not in {"cores", "estimated_seconds", "estimated_memory_gb"}}
                       for job in plan["jobs"]]
    return canonical_hash(payload)


def _journal(state: dict[str, Any], kind: str, **payload) -> None:
    events = state["events"]
    event = {"sequence": len(events), "timestamp_utc": utc_now(), "kind": kind,
             "payload": payload, "previous_sha256": events[-1]["sha256"] if events else None}
    event["sha256"] = canonical_hash(event)
    events.append(event)


def _verify_journal(state: dict[str, Any]) -> None:
    previous = None
    for index, event in enumerate(state["events"]):
        payload = {key: value for key, value in event.items() if key != "sha256"}
        if event["sequence"] != index or event["previous_sha256"] != previous or canonical_hash(payload) != event["sha256"]:
            raise CampaignIntegrityError("Campaign journal integrity failed")
        previous = event["sha256"]


def _commit(root: Path) -> str | None:
    try:
        return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _elapsed_utc(first: str, second: str) -> float:
    return max(0.0, (datetime.fromisoformat(second) - datetime.fromisoformat(first)).total_seconds())


class CampaignRunner:
    def __init__(self, root: Path, plan: dict[str, Any]):
        self.root = root.resolve()
        self.plan = plan
        self.campaign_id = _identifier(plan["campaign_id"], "campaign ID")
        self.directory = safe_path(self.root, f"artifacts/publication_campaign/{self.campaign_id}")
        self.state_path = self.directory / "campaign_state.json"
        self.stop_path = self.directory / "stop_requested.json"
        self.resources = dict(plan["resources"])
        self.jobs = {job["job_id"]: job for job in plan["jobs"]}
        self.cpu_count = os.cpu_count() or 1
        self.state: dict[str, Any] = {}
        self.active: dict[str, dict[str, Any]] = {}
        self.stop_reason: str | None = None
        self.previous_handlers = {}
        self.aggregated_this_session: set[str] = set()
        self.force_aggregation = False
        self.last_tick = time.monotonic()
        self.session_started = self.last_tick
        self.last_save = self.last_tick
        self.last_logged_event = -1
        self._validate_plan()

    def _validate_plan(self) -> None:
        if self.plan.get("mode") not in {"final", "smoke"}:
            raise ValueError("Campaign mode must be final or smoke")
        if len(self.jobs) != len(self.plan["jobs"]):
            raise ValueError("Duplicate job ID")
        phases = self.plan["phase_order"]
        if len(set(phases)) != len(phases):
            raise ValueError("Duplicate phase order")
        for name in ("max_workers", "cores_per_run"):
            value = self.resources[name]
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        for name in ("max_campaign_hours", "estimated_run_minutes"):
            if float(self.resources[name]) <= 0:
                raise ValueError(f"{name} must be positive")
        if float(self.resources.get("stop_margin_minutes", 0)) < 0:
            raise ValueError("stop_margin_minutes must be nonnegative")
        if self.resources.get("max_runtime_hours") is not None and float(self.resources["max_runtime_hours"]) <= 0:
            raise ValueError("max_runtime_hours must be positive or null")
        paths = []
        for job in self.plan["jobs"]:
            _identifier(job["job_id"], "job ID")
            _identifier(job["experiment_id"], "experiment ID")
            if job["experiment_id"] not in phases:
                raise ValueError("Every job needs an explicit phase")
            for key in ("scenario_id", "replicate_id", "run_id"):
                _identifier(job[key], key)
            if not isinstance(job["seeds"], dict) or not job["seeds"]:
                raise ValueError("Every job requires frozen seeds")
            if not isinstance(job["command"], list) or not job["command"] or any(not isinstance(token, str) for token in job["command"]):
                raise ValueError("Commands must be nonempty argv lists, never shell strings")
            if "--attempt-dir" in job["command"]:
                raise ValueError("Attempt path is reserved and supplied by the controller")
            cores = job.get("cores", self.resources["cores_per_run"])
            if isinstance(cores, bool) or not isinstance(cores, int) or not 1 <= cores <= self.cpu_count:
                raise ValueError("A job's core allocation must fit the available CPU count")
            retries = job.get("max_technical_retries", 0)
            if isinstance(retries, bool) or not isinstance(retries, int) or retries < 0:
                raise ValueError("max_technical_retries must be a nonnegative integer")
            output = safe_path(self.root, job["output_dir"])
            if output == self.directory or not output.is_relative_to(self.directory):
                raise ValueError("Job outputs must be isolated beneath this campaign namespace")
            if any(output == previous or output.is_relative_to(previous) or previous.is_relative_to(output) for previous in paths):
                raise ValueError("Job output directories overlap")
            paths.append(output)

    def _new_state(self) -> dict[str, Any]:
        jobs = {}
        for job_id, job in self.jobs.items():
            jobs[job_id] = {"job_id": job_id, "experiment_id": job["experiment_id"],
                            "scenario_id": job["scenario_id"], "replicate_id": job["replicate_id"],
                            "run_id": job["run_id"], "seeds": job["seeds"], "command": job["command"],
                            "output_dir": job["output_dir"], "status": "PLANNED", "attempts": [],
                            "input_sha256": None, "dataset_id": None, "gates": {}, "error": None,
                            "created_at_utc": utc_now(), "updated_at_utc": utc_now()}
        state = {"schema_version": "publication-campaign-state-v1", "campaign_id": self.campaign_id,
                 "mode": self.plan["mode"], "scientific_config_sha256": self.plan["scientific_config_sha256"],
                 "plan_identity_sha256": _plan_identity(self.plan), "config_path": self.plan.get("config_path"),
                 "status": "PLANNED", "created_at_utc": utc_now(), "updated_at_utc": utc_now(),
                 "code_commit": _commit(self.root), "controller_pid": os.getpid(),
                 "controller_process": process_identity(os.getpid()), "jobs": jobs,
                 "resources": self.resources, "available_cpus": self.cpu_count,
                 "budget": {"active_seconds": 0.0, "last_checkpoint_utc": utc_now(), "orphan_downtime_seconds": 0.0},
                 "resource_notes": ["Memory limits are advisory estimates, not an OS-enforced allocation cap."] if self.resources.get("memory_limit_gb") else [],
                 "family_summaries": {}, "aggregate": {}, "events": []}
        _journal(state, "campaign_declared", jobs=len(jobs), scientific_config_sha256=self.plan["scientific_config_sha256"])
        return state

    def _tick(self) -> None:
        now = time.monotonic()
        self.state["budget"]["active_seconds"] += max(0.0, now - self.last_tick)
        self.last_tick = now

    def _save(self) -> None:
        self._tick()
        self.state["updated_at_utc"] = utc_now()
        self.state["budget"]["last_checkpoint_utc"] = self.state["updated_at_utc"]
        _atomic_json(self.state_path, self.state)
        log_path = safe_path(self.root, f"logs/publication_campaign/{self.campaign_id}/campaign.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        new_events = self.state["events"][self.last_logged_event+1:]
        if new_events:
            with log_path.open("a", encoding="utf-8", newline="\n") as stream:
                for event in new_events:
                    stream.write(json.dumps(event, sort_keys=True) + "\n")
            self.last_logged_event = len(self.state["events"])-1
        self.last_save = time.monotonic()

    def _load(self, *, resume: bool) -> None:
        if self.state_path.exists():
            if not resume:
                raise FileExistsError("Campaign state already exists; use --resume, --status or a new campaign ID")
            self.state = _read(self.state_path)
            _verify_journal(self.state)
            self.last_logged_event = len(self.state["events"])-1
            if self.state["schema_version"] != "publication-campaign-state-v1" or self.state["plan_identity_sha256"] != _plan_identity(self.plan):
                raise CampaignIntegrityError("Scientific plan changed; counts, seeds, jobs and commands cannot change on resume")
            if set(self.state["jobs"]) != set(self.jobs):
                raise CampaignIntegrityError("Checkpoint lost or added declared jobs")
            for job_id, job in self.jobs.items():
                row = self.state["jobs"][job_id]
                for field in ("experiment_id", "scenario_id", "replicate_id", "run_id", "seeds", "command", "output_dir"):
                    if row[field] != job[field]:
                        raise CampaignIntegrityError(f"Checkpoint job identity changed: {job_id}/{field}")
                self._validate_attempt_history(job_id)
            if any(row["status"] == "RUNNING" for row in self.state["jobs"].values()):
                downtime = _elapsed_utc(self.state["budget"]["last_checkpoint_utc"], utc_now())
                self.state["budget"]["active_seconds"] += downtime
                self.state["budget"]["orphan_downtime_seconds"] += downtime
                _journal(self.state, "orphan_budget_accounting", seconds=downtime,
                         policy="Conservatively charge all unobserved downtime with recorded running workers")
            if self.state["resources"] != self.resources:
                _journal(self.state, "runtime_resource_change", previous=self.state["resources"], current=self.resources)
            self.state["resources"] = self.resources
            self.state["controller_pid"] = os.getpid()
            self.state["controller_process"] = process_identity(os.getpid())
            if self.stop_path.exists():
                _journal(self.state, "explicit_resume_clears_previous_stop", previous_request=_read(self.stop_path))
                self.stop_path.unlink()
            _journal(self.state, "campaign_resumed", code_commit=_commit(self.root))
        else:
            self.state = self._new_state()
        amendment = self.plan.get("runtime_amendments")
        previous_amendment = self.state.get("runtime_amendments")
        if previous_amendment:
            previous_entries = previous_amendment["amendments"]
            if not amendment or amendment["amendments"][:len(previous_entries)] != previous_entries:
                raise CampaignIntegrityError("Recorded runtime amendment cannot be removed or rewritten")
        if amendment and amendment != previous_amendment:
            self.state["runtime_amendments"] = amendment
            _journal(self.state, "runtime_amendment_verified", metadata=amendment,
                     code_commit=_commit(self.root))
        self.last_tick = time.monotonic()
        self.session_started = self.last_tick
        self._save()

    def _validate_attempt_history(self, job_id: str) -> None:
        row, job = self.state["jobs"][job_id], self.jobs[job_id]
        attempts = row["attempts"]
        allowed = TERMINAL | {"PLANNED", "RUNNING", "CANCELLED"}
        if row["status"] not in allowed:
            raise CampaignIntegrityError("Unknown checkpoint job status")
        for index, attempt in enumerate(attempts):
            if (attempt["attempt_index"] != index or attempt["output_dir"] != job["output_dir"] + f"/attempt_{index:03d}"
                    or attempt["seeds"] != job["seeds"] or attempt["status"] not in allowed - {"PLANNED"}):
                raise CampaignIntegrityError("Checkpoint attempt identity/history changed")
            if index < len(attempts)-1 and attempt["status"] not in {"CANCELLED", "FAILED_TECHNICAL"}:
                raise CampaignIntegrityError("A completed/rejected scientific attempt cannot be repeated")
        if not attempts:
            if row["status"] not in {"PLANNED", "BLOCKED"}:
                raise CampaignIntegrityError("Nonplanned job has no attempt history")
            return
        last = attempts[-1]
        if row["status"] == "PLANNED":
            retries = sum(item["status"] == "FAILED_TECHNICAL" for item in attempts)
            retryable = last["status"] == "FAILED_TECHNICAL" and last.get("technical_retryable") is True and retries <= job.get("max_technical_retries", 0)
            if last["status"] != "CANCELLED" and not retryable:
                raise CampaignIntegrityError("Checkpoint cannot schedule a completed or nonretryable attempt")
        elif row["status"] != "BLOCKED" and row["status"] != last["status"]:
            raise CampaignIntegrityError("Checkpoint job status differs from its latest attempt")

    def _handle_signal(self, signum, _frame) -> None:
        # No unsafe filesystem work inside a signal handler. The loop persists it.
        self.stop_reason = f"signal:{signal.Signals(signum).name}"

    def _install_signals(self) -> None:
        if threading.current_thread() is not threading.main_thread():
            return
        for name in ("SIGINT", "SIGTERM", "SIGHUP", "SIGBREAK"):
            value = getattr(signal, name, None)
            if value is not None:
                self.previous_handlers[value] = signal.getsignal(value)
                signal.signal(value, self._handle_signal)

    def _restore_signals(self) -> None:
        for value, previous in self.previous_handlers.items():
            signal.signal(value, previous)

    def _stop_check(self) -> None:
        if self.stop_path.exists() and not self.stop_reason:
            self.stop_reason = "requested_stop_file"

    def _remaining_seconds(self) -> float:
        self._tick()
        return float(self.resources["max_campaign_hours"]) * 3600 - self.state["budget"]["active_seconds"]

    def _dispatch_budget(self) -> tuple[float, str]:
        remaining = self._remaining_seconds()
        reason = "budget_dispatch_margin"
        session_limit = self.resources.get("max_runtime_hours")
        if session_limit is not None:
            session_remaining = float(session_limit)*3600 - (time.monotonic()-self.session_started)
            if session_remaining < remaining:
                return session_remaining, "runtime_session_dispatch_margin"
        return remaining, reason

    def _command(self, command: list[str]) -> list[str]:
        return [sys.executable if value == "{python}" else value for value in command]

    def _popen(self, command: list[str], stdout, stderr) -> subprocess.Popen:
        env = os.environ.copy()
        env.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
        kwargs = {"cwd": self.root, "env": env, "stdout": stdout, "stderr": stderr,
                  "stdin": subprocess.DEVNULL, "start_new_session": os.name != "nt"}
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        return subprocess.Popen(command, **kwargs)

    def _start(self, job_id: str) -> None:
        job, row = self.jobs[job_id], self.state["jobs"][job_id]
        index = len(row["attempts"])
        relative = job["output_dir"] + f"/attempt_{index:03d}"
        destination = safe_path(self.root, relative)
        try:
            destination.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            row.update(status="BLOCKED", error=f"Reserved output collision: {relative}", updated_at_utc=utc_now())
            _journal(self.state, "attempt_path_collision", job_id=job_id, output_dir=relative)
            self._save()
            return
        log_base = f"logs/publication_campaign/{self.campaign_id}/{job['experiment_id']}/{job_id}.attempt{index:03d}"
        stdout_path, stderr_path = safe_path(self.root, log_base + ".stdout.log"), safe_path(self.root, log_base + ".stderr.log")
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        command = self._command(job["command"]) + ["--attempt-dir", str(destination)]
        attempt = {"attempt_index": index, "status": "RUNNING", "started_at_utc": utc_now(), "finished_at_utc": None,
                   "seeds": job["seeds"], "command": command, "code_commit": _commit(self.root), "output_dir": relative,
                   "stdout_log": stdout_path.relative_to(self.root).as_posix(), "stderr_log": stderr_path.relative_to(self.root).as_posix(),
                   "process": None, "return_code": None, "return_code_known": False,
                   "input_sha256": None, "dataset_id": None, "gates": {}, "error": None}
        row["attempts"].append(attempt)
        row.update(status="RUNNING", updated_at_utc=utc_now())
        _journal(self.state, "attempt_reserved", job_id=job_id, attempt_index=index, output_dir=relative)
        self._save()
        try:
            with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
                process = self._popen(command, stdout, stderr)
            attempt["process"] = process_identity(process.pid) or {"pid": process.pid, "start_token": None}
            attempt["worker_session"] = attempt["process"]
            self.active[job_id] = {"popen": process, "adopted": False}
            _journal(self.state, "worker_started", job_id=job_id, attempt_index=index, process=attempt["process"])
            self._save()
        except (OSError, ValueError) as exc:
            attempt.update(status="FAILED_TECHNICAL", finished_at_utc=utc_now(), error=f"launch_error: {exc}", technical_retryable=False)
            row.update(status="FAILED_TECHNICAL", error=attempt["error"], updated_at_utc=utc_now())
            _journal(self.state, "worker_launch_failed", job_id=job_id, error=attempt["error"])
            self._save()

    def _finish(self, job_id: str, return_code: int | None, *, adopted: bool = False) -> None:
        row = self.state["jobs"][job_id]
        attempt = row["attempts"][-1]
        destination = safe_path(self.root, attempt["output_dir"])
        attempt.update(finished_at_utc=utc_now(), return_code=return_code, return_code_known=not adopted,
                       exit_observation="adopted worker exit code unavailable" if adopted else "child process return code")
        try:
            manifest = validate_completion(destination,
                declared_intervention=self.jobs[job_id].get("payload", {}).get("intervention"))
            status = manifest["status"]
            if return_code not in {None, 0} and status in SCIENTIFIC_TERMINAL:
                raise CampaignIntegrityError("Worker claims completion despite a nonzero exit code")
            if row.get("input_sha256") and manifest.get("input_sha256") and row["input_sha256"] != manifest["input_sha256"]:
                raise CampaignIntegrityError("Retry changed the scientific input realization")
            if row.get("dataset_id") and manifest.get("dataset_id") and row["dataset_id"] != manifest["dataset_id"]:
                raise CampaignIntegrityError("Retry changed the dataset identity")
            attempt.update(status=status, completion_manifest_sha256=sha256_file(destination / "completion_manifest.json"),
                           input_sha256=manifest.get("input_sha256"), dataset_id=manifest.get("dataset_id"),
                           gates=manifest["gates"], error=manifest.get("error"),
                           technical_retryable=manifest.get("technical_retryable", False))
        except (OSError, ValueError, KeyError, CampaignIntegrityError) as exc:
            status = "CANCELLED" if (return_code is not None and return_code < 0) or (adopted and isinstance(exc, FileNotFoundError)) else "FAILED_TECHNICAL"
            if isinstance(exc, CampaignIntegrityError):
                status = "BLOCKED"
            attempt.update(status=status, error=f"completion_validation: {exc}", technical_retryable=False)
        row.update(status=attempt["status"], input_sha256=attempt.get("input_sha256") or row.get("input_sha256"),
                   dataset_id=attempt.get("dataset_id") or row.get("dataset_id"), gates=attempt["gates"],
                   error=attempt["error"], updated_at_utc=utc_now())
        _journal(self.state, "attempt_finished", job_id=job_id, attempt_index=attempt["attempt_index"], status=attempt["status"],
                 return_code=return_code, return_code_known=not adopted)
        if row["status"] == "FAILED_TECHNICAL" and attempt.get("technical_retryable"):
            failed_count = sum(item["status"] == "FAILED_TECHNICAL" for item in row["attempts"])
            if failed_count <= self.jobs[job_id].get("max_technical_retries", 0):
                row["status"] = "PLANNED"
                _journal(self.state, "technical_retry_scheduled", job_id=job_id, preserved_attempt=attempt["attempt_index"])
        self.active.pop(job_id, None)
        self._save()

    def _recover(self) -> None:
        for job_id in self.jobs:
            row = self.state["jobs"][job_id]
            if not row["attempts"]:
                if row["status"] not in {"PLANNED", "BLOCKED"}:
                    raise CampaignIntegrityError("Nonplanned job has no attempt history")
                continue
            attempt = row["attempts"][-1]
            destination = safe_path(self.root, attempt["output_dir"])
            if row["status"] in SCIENTIFIC_TERMINAL or attempt.get("completion_manifest_sha256"):
                try:
                    preserved = validate_completion(destination, expected_manifest_sha256=attempt.get("completion_manifest_sha256"),
                        declared_intervention=self.jobs[job_id].get("payload", {}).get("intervention"))
                    for field in ("status", "gates", "input_sha256", "dataset_id"):
                        if attempt.get(field) != preserved.get(field):
                            raise CampaignIntegrityError(f"Checkpoint attempt differs from preserved completion: {field}")
                    if attempt.get("technical_retryable", False) != preserved.get("technical_retryable", False):
                        raise CampaignIntegrityError("Checkpoint changed technical-retry permission")
                except (OSError, ValueError, KeyError, CampaignIntegrityError) as exc:
                    row.update(status="BLOCKED", error=f"preserved_output_integrity: {exc}", updated_at_utc=utc_now())
                    _journal(self.state, "preserved_output_blocked", job_id=job_id, reason=row["error"])
                    continue
            if row["status"] == "RUNNING":
                process = attempt.get("process") or _find_attempt_process(destination)
                if process is not None:
                    attempt["process"] = process
                alive = process_matches(process)
                if alive is False:
                    descendant = _live_session_descendant(attempt.get("worker_session", process))
                    if descendant:
                        attempt["process"] = process = descendant
                        alive = True
                if alive is True:
                    self.active[job_id] = {"popen": None, "adopted": True}
                    _journal(self.state, "live_orphan_adopted", job_id=job_id, process=process)
                    continue
                if alive is None:
                    # A launch-intent checkpoint without a PID is ambiguous; a
                    # new attempt could duplicate an untracked live child.
                    self.state.update(status="BLOCKED", stop_reason="unproven_orphan_liveness")
                    self._save()
                    raise CampaignIntegrityError(f"Cannot prove old worker dead or adopt it: {job_id}")
                if (destination / "completion_manifest.json").exists():
                    self._finish(job_id, None, adopted=True)
                    continue
                attempt.update(status="CANCELLED", finished_at_utc=utc_now(), error="Prior controller/worker interrupted; original process proven absent")
                input_path = destination / "input.csv"
                if input_path.is_file():
                    row["input_sha256"] = sha256_file(input_path)
                _journal(self.state, "dead_orphan_cancelled", job_id=job_id, attempt_index=attempt["attempt_index"])
                row["status"] = "PLANNED"
            elif row["status"] == "CANCELLED":
                row["status"] = "PLANNED"
                _journal(self.state, "cancelled_attempt_rescheduled", job_id=job_id)
        self._save()

    def _poll(self) -> None:
        for job_id, running in list(self.active.items()):
            if running["popen"] is not None:
                return_code = running["popen"].poll()
                if return_code is not None:
                    attempt = self.state["jobs"][job_id]["attempts"][-1]
                    descendant = _live_session_descendant(attempt.get("worker_session", attempt.get("process")))
                    if descendant:
                        attempt.update(process=descendant, worker_parent_return_code=return_code)
                        running.update(popen=None, adopted=True)
                        _journal(self.state, "worker_descendant_adopted", job_id=job_id, process=descendant)
                        self._save()
                        continue
                    self._finish(job_id, return_code)
            else:
                process = self.state["jobs"][job_id]["attempts"][-1]["process"]
                alive = process_matches(process)
                if alive is False:
                    attempt = self.state["jobs"][job_id]["attempts"][-1]
                    descendant = _live_session_descendant(attempt.get("worker_session", process))
                    if descendant:
                        attempt["process"] = descendant
                        self._save()
                        continue
                    self._finish(job_id, None, adopted=True)
                elif alive is None:
                    self.stop_reason = "adopted_process_liveness_unknown"

    def _phase(self) -> str | None:
        for family in self.plan["phase_order"]:
            rows = [row for row in self.state["jobs"].values() if row["experiment_id"] == family]
            if any(row["status"] not in TERMINAL for row in rows):
                return family
        return None

    def _fingerprint(self, family: str | None = None) -> str:
        return canonical_hash([{key: row.get(key) for key in ("job_id", "status", "seeds", "input_sha256", "dataset_id", "gates")}
                               | {"attempts": [(item["status"], item.get("completion_manifest_sha256")) for item in row["attempts"]]}
                               for job_id in sorted(self.jobs) for row in [self.state["jobs"][job_id]]
                               if family is None or row["experiment_id"] == family])

    def _auxiliary(self, label: str, command: list[str], record: dict[str, Any], fingerprint: str) -> None:
        if label in self.aggregated_this_session:
            return
        if record.get("status") in {"COMPLETED", "FAILED_TECHNICAL"} and record.get("source_state_sha256") == fingerprint and not self.force_aggregation:
            return
        self.aggregated_this_session.add(label)
        previous = record.get("attempts", [])
        if previous and previous[-1]["status"] == "RUNNING":
            while process_matches(previous[-1].get("process")) is True:
                self._stop_check()
                self._save()
                time.sleep(self.poll_seconds)
            if process_matches(previous[-1].get("process")) is None:
                raise CampaignIntegrityError("Cannot determine whether an earlier aggregator is alive")
            previous[-1].update(status="CANCELLED", error="Orphan aggregator exited with unknown return code; rerun derived aggregation only")
        index = len(previous)
        log_base = f"logs/publication_campaign/{self.campaign_id}/aggregation/{label}.attempt{index:03d}"
        stdout_path, stderr_path = safe_path(self.root, log_base + ".stdout.log"), safe_path(self.root, log_base + ".stderr.log")
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        attempt = {"status": "RUNNING", "started_at_utc": utc_now(), "command": self._command(command),
                   "stdout_log": stdout_path.relative_to(self.root).as_posix(), "stderr_log": stderr_path.relative_to(self.root).as_posix(),
                   "process": None, "return_code": None}
        previous.append(attempt)
        record.update(status="RUNNING", attempts=previous, source_state_sha256=fingerprint)
        self._save()
        try:
            with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
                process = self._popen(attempt["command"], stdout, stderr)
            attempt["process"] = process_identity(process.pid) or {"pid": process.pid, "start_token": None}
            self._save()
            while process.poll() is None:
                self._stop_check()
                if time.monotonic() - self.last_save >= self.checkpoint_seconds:
                    self._save()
                time.sleep(self.poll_seconds)
            status = "COMPLETED" if process.returncode == 0 else "FAILED_TECHNICAL"
            attempt.update(status=status, return_code=process.returncode, finished_at_utc=utc_now())
            record["status"] = status
        except OSError as exc:
            attempt.update(status="FAILED_TECHNICAL", error=str(exc), finished_at_utc=utc_now())
            record["status"] = "FAILED_TECHNICAL"
        _journal(self.state, "aggregation_finished", label=label, status=record["status"])
        self._save()

    @property
    def poll_seconds(self) -> float:
        return max(.01, float(self.resources.get("poll_interval_seconds", .5)))

    @property
    def checkpoint_seconds(self) -> float:
        return max(.01, float(self.resources.get("checkpoint_interval_seconds", 2.0)))

    def _summarize_completed_families(self) -> None:
        for family, command in self.plan.get("family_summarizers", {}).items():
            rows = [row for row in self.state["jobs"].values() if row["experiment_id"] == family]
            if rows and all(row["status"] in TERMINAL for row in rows):
                record = self.state["family_summaries"].setdefault(family, {})
                self._auxiliary(family, command, record, self._fingerprint(family))

    def _aggregate_all(self) -> None:
        command = self.plan.get("aggregate_command")
        if command:
            self._auxiliary("campaign", command, self.state["aggregate"], self._fingerprint())

    def run(self, *, resume: bool = False, aggregate_only: bool = False) -> dict[str, Any]:
        if self.plan.get("preflight_errors") and not aggregate_only:
            raise ValueError("Campaign preflight failed: " + "; ".join(map(str, self.plan["preflight_errors"])))
        execution_environment = None
        if self.plan["mode"] == "final" and not aggregate_only:
            from publication.campaign_preflight import validate_execution_environment
            execution_environment = validate_execution_environment(self.root, self.plan)
        with CampaignLock(self.directory / "campaign.lock"):
            self._load(resume=resume)
            if execution_environment is not None:
                self.state["execution_environment"] = execution_environment
                _journal(self.state, "execution_environment_verified", report_sha256=canonical_hash(execution_environment))
            self.force_aggregation = aggregate_only
            self._install_signals()
            try:
                self._recover()
                self.state["status"] = "RUNNING"
                self.state.pop("stop_reason", None)
                self._save()
                if not aggregate_only:
                    while True:
                        self._stop_check()
                        self._poll()
                        self._summarize_completed_families()
                        family = self._phase()
                        if family is None and not self.active:
                            break
                        if not self.stop_reason:
                            candidates = [job_id for job_id in self.jobs for row in [self.state["jobs"][job_id]]
                                          if row["experiment_id"] == family and row["status"] == "PLANNED"]
                            for job_id in candidates:
                                if len(self.active) >= self.resources["max_workers"]:
                                    break
                                cores = self.jobs[job_id].get("cores", self.resources["cores_per_run"])
                                used = sum(self.jobs[key].get("cores", self.resources["cores_per_run"]) for key in self.active)
                                if used + cores > self.cpu_count:
                                    continue
                                estimated = float(self.jobs[job_id].get("estimated_seconds", self.resources["estimated_run_minutes"] * 60))
                                margin = float(self.resources.get("stop_margin_minutes", 0)) * 60
                                remaining, reason = self._dispatch_budget()
                                if remaining < estimated + margin:
                                    self.stop_reason = reason
                                    _journal(self.state, "budget_stopped_dispatch", remaining_seconds=remaining,
                                             next_job=job_id, estimated_seconds=estimated, margin_seconds=margin)
                                    break
                                self._start(job_id)
                        if self.stop_reason and not self.active:
                            break
                        if not self.active and family is not None and not any(row["status"] == "PLANNED" and row["experiment_id"] == family for row in self.state["jobs"].values()):
                            self.stop_reason = "interrupted_attempt_requires_resume"
                            break
                        if time.monotonic() - self.last_save >= self.checkpoint_seconds:
                            self._save()
                        time.sleep(self.poll_seconds)
                elif self.active:
                    raise CampaignBusyError("Live orphan science worker exists; resume monitoring before aggregating separately")
                self.state.update(status="AGGREGATING", stop_reason=self.stop_reason)
                self._save()
                self._summarize_completed_families()
                self._aggregate_all()
                terminal = all(row["status"] in TERMINAL for row in self.state["jobs"].values())
                if terminal:
                    failures = any(row["status"] in {"FAILED_TECHNICAL", "BLOCKED"} for row in self.state["jobs"].values())
                    failures |= any(record.get("status") == "FAILED_TECHNICAL" for record in [*self.state["family_summaries"].values(), self.state["aggregate"]])
                    self.state["status"] = "COMPLETED_WITH_FAILURES" if failures else "COMPLETED"
                else:
                    self.state["status"] = "STOPPED"
                self.state["stop_reason"] = self.stop_reason
                _journal(self.state, "controller_checkpointed_exit", status=self.state["status"], stop_reason=self.stop_reason)
                self._save()
                return self.state
            finally:
                self._restore_signals()


def run_campaign(root: Path, plan: dict[str, Any], *, resume: bool = False) -> dict[str, Any]:
    return CampaignRunner(root, plan).run(resume=resume)


def request_stop(root: Path, campaign_id: str) -> Path:
    _identifier(campaign_id, "campaign ID")
    directory = safe_path(root, f"artifacts/publication_campaign/{campaign_id}")
    _read(directory / "campaign_state.json")
    path = directory / "stop_requested.json"
    _atomic_json(path, {"requested_at_utc": utc_now(), "reason": "explicit --stop; current workers may finish"})
    return path


def read_status(root: Path, campaign_id: str) -> dict[str, Any]:
    _identifier(campaign_id, "campaign ID")
    path = safe_path(root, f"artifacts/publication_campaign/{campaign_id}/campaign_state.json")
    state = _read(path)
    _verify_journal(state)
    counts = {}
    families = {}
    for row in state["jobs"].values():
        counts[row["status"]] = counts.get(row["status"], 0) + 1
        family_counts = families.setdefault(row["experiment_id"], {})
        family_counts[row["status"]] = family_counts.get(row["status"], 0) + 1
    age = _elapsed_utc(state["updated_at_utc"], utc_now())
    # Persisted RUNNING is not proof of process liveness. Never trust a reused PID.
    controller = process_matches(state.get("controller_process"))
    workers = {key: process_matches(row["attempts"][-1].get("process"))
               for key, row in state["jobs"].items() if row["status"] == "RUNNING" and row["attempts"]}
    effective = state["status"]
    if state["status"] in {"RUNNING", "AGGREGATING"}:
        if controller is False:
            effective = "ORPHANED_WORKERS" if any(value is True for value in workers.values()) else "CONTROLLER_STOPPED"
        elif age > 30:
            effective = "CHECKPOINT_STALE"
        elif controller is None:
            effective = "LIVENESS_UNCONFIRMED"
    return {"campaign_id": campaign_id, "mode": state["mode"], "status": state["status"],
            "effective_status": effective, "checkpoint_age_seconds": age,
            "controller_alive": controller, "worker_liveness": workers,
            "updated_at_utc": state["updated_at_utc"], "declared_jobs": len(state["jobs"]),
            "status_counts": counts, "status_counts_by_family": families,
            "active_seconds_checkpointed": state["budget"]["active_seconds"],
            "max_campaign_hours": state["resources"]["max_campaign_hours"],
            "stop_reason": state.get("stop_reason"),
            "progress_semantics": "Counts/status describe persisted attempts, not liveness or scientific success; consult effective_status/controller_alive. No unsupported ETA is inferred."}


def planned_status(plan: dict[str, Any]) -> dict[str, Any]:
    """Read-only progress before the first campaign checkpoint exists."""
    families = {}
    for job in plan["jobs"]:
        counts = families.setdefault(job["experiment_id"], {"PLANNED": 0})
        counts["PLANNED"] += 1
    return {"campaign_id": plan["campaign_id"], "mode": plan["mode"], "status": "NOT_INITIALIZED",
            "declared_jobs": len(plan["jobs"]), "attempted_jobs": 0,
            "status_counts": {"PLANNED": len(plan["jobs"])}, "status_counts_by_family": families,
            "active_seconds_checkpointed": 0.0, "max_campaign_hours": plan["resources"]["max_campaign_hours"],
            "preflight_errors": plan.get("preflight_errors", []),
            "progress_semantics": "Declared only: no persisted state or evidence exists; nothing has been executed."}


def verify_report(root: Path, campaign_id: str) -> dict[str, Any]:
    """Verify stored derived evidence without claiming a scientific release."""
    from publication.campaign_reporting import validate_campaign_report
    _identifier(campaign_id, "campaign ID")
    output = safe_path(root, f"reports/publication_campaign/{campaign_id}")
    validate_campaign_report(root, output)
    summary = _read(output / "summary.json")
    if summary.get("integrity_errors"):
        raise CampaignIntegrityError("Campaign report contains preserved integrity failures: " + "; ".join(map(str, summary["integrity_errors"])))
    return {"campaign_id": campaign_id, "mode": summary["mode"], "artifact_integrity_passed": True,
            "declared_jobs": summary["declared_jobs"], "status_counts": summary["status_counts"],
            "complete_declared_batch": summary["complete_declared_batch"],
            "all_declared_scientific_jobs_finished": summary["all_declared_scientific_jobs_finished"],
            "scientifically_interpretable_count": summary["scientifically_interpretable_count"],
            "claim_limit": "Artifact integrity does not authorize scientific claims or paper release; smoke is infrastructure evidence only."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/publication/tcc_final_campaign.json"))
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--dry-run", action="store_true")
    actions.add_argument("--status", action="store_true")
    actions.add_argument("--stop", action="store_true")
    actions.add_argument("--aggregate", action="store_true")
    actions.add_argument("--verify", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    config_path = args.config.resolve()
    if args.status or args.stop or args.verify:
        campaign_id = _read(config_path)["campaign_id"]
        if args.verify:
            print(json.dumps(verify_report(root, campaign_id), indent=2))
        elif args.stop:
            print(json.dumps({"stop_request": request_stop(root, campaign_id).relative_to(root).as_posix()}))
        else:
            try:
                status = read_status(root, campaign_id)
            except FileNotFoundError:
                from publication.campaign_plan import build_plan
                status = planned_status(build_plan(root, config_path))
            print(json.dumps(status, indent=2))
        return
    from publication.campaign_plan import build_plan
    plan = build_plan(root, config_path)
    if args.dry_run:
        print(json.dumps({"campaign_summary": planned_status(plan), **plan}, indent=2, sort_keys=True))
        return
    runner = CampaignRunner(root, plan)
    state = runner.run(resume=args.resume or args.aggregate, aggregate_only=args.aggregate)
    print(json.dumps(read_status(root, state["campaign_id"]), indent=2))
    if state["status"] == "COMPLETED_WITH_FAILURES":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
