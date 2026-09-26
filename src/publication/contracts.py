"""Small, standard-library contracts for auditable publication experiments.

Registries declare attempts before execution. Run directories are never reused;
status and protocol amendments are append-only, content-linked event streams.
These safeguards detect accidental mutation, not an adversarial Git rewrite.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

BASE_COMMIT = "7489a90689a753bea5243f86c1489329916c98e2"
BASE_DATASET = "kepler_10_b-b4d1e6ec961c1f4d"
BASE_INPUT_SHA256 = "6653fced1df0b3a29be96d181daa695f86ef709a7aa459bc1b3f837d48ad8791"
BASE_MODEL_VERSION = "m5-v2-exposure-integrated"
STATUSES = frozenset({"planned", "pilot", "running", "completed", "failed", "rejected", "not_interpretable"})
TERMINAL = frozenset({"completed", "failed", "rejected", "not_interpretable"})
PHASES = ["baseline_freeze", "literature", "injection_recovery", "independent_benchmark",
          "ablation_failure", "multi_target", "correlated_noise", "release", "synthesis"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_hash(payload: Any) -> str:
    """SHA-256 of canonical JSON (not a file-byte checksum)."""
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_new(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def safe_path(root: Path, relative: str) -> Path:
    """Reject traversal, Windows paths and symlink escape before any write/read."""
    parsed = PurePosixPath(relative)
    if not relative or "\\" in relative or ":" in relative or parsed.is_absolute():
        raise ValueError(f"Not a repository-relative POSIX path: {relative!r}")
    if any(part in {".", "..", ""} for part in relative.split("/")):
        raise ValueError(f"Unsafe relative path: {relative!r}")
    resolved = (root.resolve() / Path(*parsed.parts)).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes repository: {relative!r}")
    return resolved


def _identifier(value: str, label: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,95}", value):
        raise ValueError(f"Invalid {label}: {value!r}")


@dataclass(frozen=True)
class RunIdentity:
    experiment_id: str
    scenario_id: str
    replicate_id: str
    run_id: str

    def __post_init__(self) -> None:
        if not re.fullmatch(r"PUB-\d{2}", self.experiment_id):
            raise ValueError(f"Invalid experiment_id: {self.experiment_id!r}")
        for name in ("scenario_id", "replicate_id", "run_id"):
            _identifier(getattr(self, name), name)

    @property
    def relative_path(self) -> str:
        return "/".join(["publication", "experiments", self.experiment_id,
                         self.scenario_id, self.replicate_id, self.run_id])


def deterministic_seed(experiment_id: str, scenario_id: str, replicate_id: str,
                       stream: str = "simulation") -> int:
    """Stable independent-stream seeds; never depend on process hash randomization."""
    RunIdentity(experiment_id, scenario_id, replicate_id, "identity_check")
    _identifier(stream, "stream")
    digest = canonical_hash(["publication-seed-v1", experiment_id, scenario_id, replicate_id, stream])
    return int(digest[:8], 16)


def _git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE)


def committed_protocol(root: Path, relative: str) -> dict[str, Any]:
    """Return byte identity of an unchanged committed protocol, before final runs.

    The commit is recorded outside the protocol, avoiding a self-referential SHA.
    For JSON protocols, canonical_json_sha256 is also recorded distinctly.
    """
    path = safe_path(root, relative)
    content = path.read_bytes()
    if _git(root, "show", f"HEAD:{relative}") != content:
        raise ValueError("Protocol differs from committed HEAD; commit before final execution")
    identity = {"path": relative, "sha256": hashlib.sha256(content).hexdigest(),
                "commit": _git(root, "rev-parse", "HEAD").decode().strip(),
                "last_changed_commit": _git(root, "log", "-1", "--format=%H", "--", relative).decode().strip()}
    if path.suffix == ".json":
        payload = _read(path)
        if payload.get("protocol_status", "").lower() not in {"frozen", "amended"}:
            raise ValueError("Final protocol must declare FROZEN or AMENDED")
        identity["canonical_json_sha256"] = canonical_hash(payload)
    return identity


def _verify_protocol(root: Path, identity: dict[str, Any]) -> None:
    path = safe_path(root, identity["path"])
    if sha256_file(path) != identity["sha256"]:
        raise ValueError("Frozen protocol checksum mismatch")
    committed = _git(root, "show", f"{identity['commit']}:{identity['path']}")
    if hashlib.sha256(committed).hexdigest() != identity["sha256"]:
        raise ValueError("Protocol identity is not backed by its declared commit")
    _git(root, "merge-base", "--is-ancestor", identity["commit"], "HEAD")


def initialize_registry(root: Path) -> Path:
    path = safe_path(root, "publication/registry.json")
    _write_new(path, {"schema_version": "publication-registry-v1", "base_commit": BASE_COMMIT,
                      "experiments": [{"experiment_id": f"PUB-{index:02d}", "family": family,
                                       "status": "planned", "protocol": None, "expected_runs": []}
                                      for index, family in enumerate(PHASES)]})
    return path


def load_registry(root: Path) -> dict[str, Any]:
    registry = _read(safe_path(root, "publication/registry.json"))
    if registry.get("schema_version") != "publication-registry-v1":
        raise ValueError("Unknown publication registry schema")
    seen = set()
    for experiment in registry["experiments"]:
        experiment_id = experiment["experiment_id"]
        if not re.fullmatch(r"PUB-\d{2}", experiment_id) or experiment_id in seen:
            raise ValueError("Invalid or duplicate experiment identity")
        seen.add(experiment_id)
        if experiment["status"] not in STATUSES:
            raise ValueError("Unknown experiment status")
        expected = [RunIdentity(**entry) for entry in experiment["expected_runs"]]
        if any(run.experiment_id != experiment_id for run in expected) or len(set(expected)) != len(expected):
            raise ValueError("Duplicate/cross-experiment expected runs")
    return registry


def register_experiment(root: Path, experiment_id: str, protocol: dict[str, Any],
                        expected_runs: list[RunIdentity]) -> None:
    """Fill an unstarted declaration once; amendments require a new declaration ID.

    The registry itself must be committed before reserve_run for final execution.
    """
    _verify_protocol(root, protocol)
    registry = load_registry(root)
    matches = [item for item in registry["experiments"] if item["experiment_id"] == experiment_id]
    if len(matches) != 1:
        raise ValueError("Experiment must exist in the registry")
    experiment = matches[0]
    if experiment["protocol"] is not None or experiment["expected_runs"]:
        raise ValueError("Existing declarations are immutable; use a new experiment ID/amendment")
    if not expected_runs or any(run.experiment_id != experiment_id for run in expected_runs):
        raise ValueError("Declare at least one run belonging to the experiment")
    if len(set(expected_runs)) != len(expected_runs):
        raise ValueError("Duplicate expected run identity")
    experiment.update(protocol=protocol, expected_runs=[asdict(run) for run in expected_runs])
    # This is a declaration edit, not result editing; no reserved final runs exist yet.
    path = safe_path(root, "publication/registry.json")
    path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _events(directory: Path) -> list[dict[str, Any]]:
    entries = []
    previous = None
    for index, path in enumerate(sorted(directory.glob("*.json"))):
        event = _read(path)
        if path.name != f"{index:06d}.json" or event["previous_sha256"] != previous:
            raise ValueError("Broken append-only event sequence")
        if event["event_sha256"] != canonical_hash({key: value for key, value in event.items() if key != "event_sha256"}):
            raise ValueError("Mutated event detected")
        previous = event["event_sha256"]
        entries.append(event)
    return entries


def _append_event(directory: Path, payload: dict[str, Any]) -> dict[str, Any]:
    entries = _events(directory)
    event = dict(payload, timestamp_utc=utc_now(), previous_sha256=entries[-1]["event_sha256"] if entries else None)
    event["event_sha256"] = canonical_hash(event)
    _write_new(directory / f"{len(entries):06d}.json", event)
    return event


def reserve_run(root: Path, identity: RunIdentity, config: dict[str, Any],
                protocol: dict[str, Any] | None = None, *, pilot: bool = False) -> Path:
    """Reserve exclusively before inference; final attempts require frozen declaration."""
    if not pilot:
        if _git(root, "branch", "--show-current").decode().strip() != "publication-grade-validation":
            raise ValueError("Final publication execution requires publication-grade-validation")
        if protocol is None:
            raise ValueError("Final run requires a committed frozen protocol")
        _verify_protocol(root, protocol)
        registry_path = safe_path(root, "publication/registry.json")
        if _git(root, "show", "HEAD:publication/registry.json") != registry_path.read_bytes():
            raise ValueError("Commit the complete registry declaration before final execution")
        registry = load_registry(root)
        experiment = next((row for row in registry["experiments"] if row["experiment_id"] == identity.experiment_id), None)
        if experiment is None or asdict(identity) not in experiment["expected_runs"]:
            raise ValueError("Final run is not in the predeclared registry")
        if experiment["protocol"] != protocol:
            raise ValueError("Run protocol differs from predeclared experiment")
    path = safe_path(root, identity.relative_path)
    source_paths = sorted((root / "src/publication").glob("*.py"))
    source_paths += [root / relative for relative in (
        "src/bayesian_modeling/physical_transit.py", "src/bayesian_modeling/contracts.py",
        "src/project_config.py", "scripts/run_publication_batch.py",
        "scripts/publication_inventory.py",
    ) if (root / relative).is_file()]
    code_relative_paths = [item.relative_to(root).as_posix() for item in source_paths]
    audit_paths = code_relative_paths + [name for name in
                   ("requirements.txt", "environment.yml", "pyproject.toml") if (root / name).exists()]
    try:
        status = _git(root, "status", "--porcelain", "--untracked-files=no", "--", *audit_paths).decode().splitlines() if audit_paths else []
        if not pilot:
            if status:
                raise ValueError("Final execution requires committed relevant source and environment files")
            if audit_paths:
                _git(root, "ls-files", "--error-unmatch", "--", *audit_paths)
        code = {"commit": _git(root, "rev-parse", "HEAD").decode().strip(),
                "working_tree_status": status,
                "working_tree_status_scope": "tracked-only relevant executable source and environment locks; untracked publication modules are separately hashed",
                "audited_paths": audit_paths,
                "working_tree_diff_sha256": hashlib.sha256(_git(root, "diff", "HEAD", "--binary", "--", *audit_paths)).hexdigest() if audit_paths else None}
    except subprocess.CalledProcessError:
        if not pilot:
            raise ValueError("Final executable sources must be tracked and committed") from None
        code = {"commit": None, "note": "non-Git pilot fixture"}
    code["executable_source_sha256"] = {
        item.relative_to(root).as_posix(): sha256_file(item)
        for item in source_paths
    }
    environment_locks = {name: sha256_file(root / name) for name in
                         ["requirements.txt", "environment.yml", "pyproject.toml"] if (root / name).exists()}
    path.mkdir(parents=True, exist_ok=False)
    _write_new(path / "run_config.json", {"schema_version": "publication-run-v1", "identity": asdict(identity),
               "mode": "pilot" if pilot else "final", "config": config, "config_sha256": canonical_hash(config),
               "protocol": protocol, "code": code, "environment_lock_sha256": environment_locks,
               "created_at_utc": utc_now()})
    _append_event(path / "status", {"status": "pilot" if pilot else "running", "reason": "exclusive reservation"})
    return path


def update_run_status(run_path: Path, status: str, *, reason: str,
                      evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    if status not in STATUSES or status == "planned":
        raise ValueError("Invalid run status")
    if not reason.strip():
        raise ValueError("Status changes require an explicit reason")
    entries = _events(run_path / "status")
    if not entries or entries[-1]["status"] in TERMINAL:
        raise ValueError("Terminal/historical run statuses cannot be rewritten; reserve a new run")
    if status in {"pilot", "running"}:
        raise ValueError("An active reservation can only transition to a terminal result")
    return _append_event(run_path / "status", {"status": status, "reason": reason, "evidence": evidence or {}})


def verify_run_artifacts(run_path: Path) -> dict[str, Any]:
    """Verify an already-terminal worker attempt before reusing any result."""
    events = _events(run_path / "status")
    if not events or events[-1]["status"] not in TERMINAL:
        raise ValueError("Attempt is not terminal; a result filename alone is insufficient")
    evidence = events[-1].get("evidence", {})
    for name in ("result", "checksums"):
        if sha256_file(run_path / f"{name}.json") != evidence.get(f"{name}_sha256"):
            raise ValueError(f"Terminal {name} artifact mismatch")
    for relative, digest in _read(run_path / "checksums.json")["artifacts"].items():
        if sha256_file(safe_path(run_path, relative)) != digest:
            raise ValueError(f"Terminal run artifact mismatch: {relative}")
    result = _read(run_path / "result.json")
    if result["status"] != events[-1]["status"]:
        raise ValueError("Result status differs from immutable terminal status")
    return result


def append_amendment(root: Path, experiment_id: str, *, reason: str, change: str,
                     previous_protocol: dict[str, Any], new_protocol: dict[str, Any],
                     runs_already_started: bool, impact_on_previous_evidence: str) -> dict[str, Any]:
    RunIdentity(experiment_id, "amendment", "log", "entry")
    if not all(value.strip() for value in [reason, change, impact_on_previous_evidence]):
        raise ValueError("Amendment reason, change and evidence impact are required")
    _verify_protocol(root, new_protocol)
    return _append_event(safe_path(root, f"publication/amendments/{experiment_id}"),
                         {"experiment_id": experiment_id, "reason": reason, "change": change,
                          "previous_protocol": previous_protocol, "new_protocol": new_protocol,
                          "runs_already_started": runs_already_started,
                          "impact_on_previous_evidence": impact_on_previous_evidence})


def generate_inventory(root: Path) -> dict[str, Any]:
    registry = load_registry(root)
    rows = []
    declared_paths = set()
    for experiment in registry["experiments"]:
        for expected in experiment["expected_runs"]:
            identity = RunIdentity(**expected)
            declared_paths.add(identity.relative_path)
            run_path = safe_path(root, identity.relative_path)
            row = dict(expected, path=identity.relative_path, status="missing", mode="final", integrity_valid=True)
            if run_path.exists():
                try:
                    config = _read(run_path / "run_config.json")
                    if config["identity"] != expected or canonical_hash(config["config"]) != config["config_sha256"]:
                        raise ValueError("Run config identity/checksum mismatch")
                    if config["protocol"] != experiment["protocol"] or config["mode"] != "final":
                        raise ValueError("Final run protocol/mode differs from declaration")
                    _verify_protocol(root, config["protocol"])
                    events = _events(run_path / "status")
                    if events[-1]["status"] not in STATUSES:
                        raise ValueError("Unknown persisted run status")
                    if events[-1].get("evidence", {}).get("checksums_sha256"):
                        verify_run_artifacts(run_path)
                    row.update(status=events[-1]["status"], reason=events[-1]["reason"],
                               config_sha256=config["config_sha256"], evidence=events[-1].get("evidence", {}))
                except (ValueError, KeyError, IndexError, OSError, subprocess.CalledProcessError) as error:
                    row.update(status="not_interpretable", integrity_valid=False, reason=str(error))
            rows.append(row)
    pilots = []
    undeclared = []
    for config_path in (root / "publication/experiments").glob("*/*/*/*/run_config.json"):
        relative = config_path.parent.relative_to(root).as_posix()
        if relative not in declared_paths:
            config = _read(config_path)
            item = {"path": relative, "identity": config["identity"],
                    "status": _events(config_path.parent / "status")[-1]["status"]}
            (pilots if config["mode"] == "pilot" else undeclared).append(item)
    counts = dict(Counter(row["status"] for row in rows))
    return {"schema_version": "publication-inventory-v1", "registry_sha256": canonical_hash(registry),
            "declared_final_attempts": len(rows), "status_counts": counts, "runs": rows,
            "pilot_runs": pilots, "undeclared_final_runs": undeclared,
            "all_declared_attempts_terminal": bool(rows) and all(row["status"] in TERMINAL for row in rows),
            "integrity_valid": not undeclared and all(row["integrity_valid"] for row in rows),
            "denominator_policy": "Every declared final attempt remains represented, including missing, rejected and failed attempts."}


def _artifact(root: Path, relative: str, *, role: str) -> dict[str, Any]:
    path = safe_path(root, relative)
    return {"path": relative, "sha256": sha256_file(path), "size_bytes": path.stat().st_size, "role": role}


def freeze_baseline(root: Path) -> Path:
    """Freeze observed baseline bytes without changing any legacy artifact."""
    root = root.resolve()
    manifest_path = safe_path(root, "publication/baseline/manifest.json")
    if manifest_path.exists():
        raise FileExistsError("Baseline already frozen; verify instead of overwriting")
    if _git(root, "rev-parse", "main").decode().strip() != BASE_COMMIT:
        raise ValueError("Protected main ref differs from declared baseline")
    branch = _git(root, "branch", "--show-current").decode().strip()
    if branch != "publication-grade-validation":
        raise ValueError("Baseline freeze must occur on publication-grade-validation")
    protected_refs = {"main": BASE_COMMIT}
    for reference in ["backup-main-2026-08-24", "origin/backup-main-2026-08-24"]:
        try:
            commit = _git(root, "rev-parse", "--verify", reference).decode().strip()
        except subprocess.CalledProcessError:
            continue
        if commit != BASE_COMMIT:
            raise ValueError(f"Protected backup reference changed: {reference}")
        protected_refs[reference] = commit
    model_root = "models/bayesian_physical_transit/kepler_10_b/runs/scientific_003"
    model = _read(root / model_root / "model_config.json")
    metadata_path = "data/gold/kepler_10_b/modeling/dataset_metadata.json"
    metadata = _read(root / metadata_path)
    input_path = "tables/bayesian_physical_transit/kepler_10_b/runs/scientific_003/modeling_input_physical.csv"
    if (model["input_summary"]["dataset_id"] != BASE_DATASET or metadata["dataset_id"] != BASE_DATASET
            or model["model"]["model_version"] != BASE_MODEL_VERSION
            or sha256_file(root / input_path) != BASE_INPUT_SHA256):
        raise ValueError("Protected baseline scientific identities do not match")
    paths = {metadata_path, input_path, model["source_gold_path"],
             "reports/bayesian_physical_transit_kepler_10_b_scientific_003_report.md"}
    for parent in [model_root, "tables/bayesian_physical_transit/kepler_10_b/runs/scientific_003",
                   "figures/bayesian_physical_transit/kepler_10_b/runs/scientific_003"]:
        paths.update(path.relative_to(root).as_posix() for path in (root / parent).rglob("*") if path.is_file())
    for segment in metadata["segments"]:
        matches = list((root / "data/raw").rglob(segment["source_fits_file"]))
        matching = [path for path in matches if sha256_file(path) == segment["source_fits_sha256"]]
        if not matching:
            raise ValueError("Canonical source FITS unavailable or mutated")
        paths.update(path.relative_to(root).as_posix() for path in matching)
    artifacts = [_artifact(root, path, role="protected_scientific_evidence") for path in sorted(paths)]
    # Git-owned historical outputs have an additional baseline-object comparison.
    for artifact in artifacts:
        try:
            historical = _git(root, "show", f"{BASE_COMMIT}:{artifact['path']}")
        except subprocess.CalledProcessError:
            artifact["storage"] = "external_or_regenerable_local_artifact"
        else:
            if hashlib.sha256(historical).hexdigest() != artifact["sha256"]:
                raise ValueError(f"Artifact differs from protected Git baseline: {artifact['path']}")
            artifact["storage"] = "git"
    locks = []
    for source in ["requirements.txt", "environment.yml", "pyproject.toml"]:
        data = (root / source).read_bytes()
        path = safe_path(root, "publication/baseline/environment/" + source)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(data)
        locks.append(_artifact(root, path.relative_to(root).as_posix(), role="historical_environment_snapshot"))
    payload = {"schema_version": "publication-baseline-v1", "base_commit": BASE_COMMIT,
               "frozen_at_utc": utc_now(), "freeze_commit": _git(root, "rev-parse", "HEAD").decode().strip(),
               "protected_refs": protected_refs, "target": "kepler_10_b", "run_id": "scientific_003",
               "dataset_id": BASE_DATASET, "modeling_input_sha256": BASE_INPUT_SHA256,
               "model_version": BASE_MODEL_VERSION, "gold_metadata": metadata,
               "environment": model["environment"], "environment_lock_artifacts": locks,
               "artifacts": artifacts,
               "storage_note": "Large local traces are hashed, not copied or silently assumed present in a checkout. Restore from an archive or reproduce using the protected baseline environment before full verification."}
    payload["manifest_content_sha256"] = canonical_hash(payload)
    _write_new(manifest_path, payload)
    return manifest_path


def verify_baseline(root: Path, *, require_external: bool = True) -> dict[str, Any]:
    manifest = _read(safe_path(root, "publication/baseline/manifest.json"))
    digest = manifest.pop("manifest_content_sha256")
    if digest != canonical_hash(manifest):
        raise ValueError("Baseline manifest mutated")
    if (manifest["base_commit"] != BASE_COMMIT or manifest["dataset_id"] != BASE_DATASET
            or manifest["model_version"] != BASE_MODEL_VERSION
            or manifest["modeling_input_sha256"] != BASE_INPUT_SHA256):
        raise ValueError("Protected baseline identities changed")
    missing_external = []
    verified = 0
    for artifact in manifest["artifacts"] + manifest["environment_lock_artifacts"]:
        path = safe_path(root, artifact["path"])
        if not path.exists() and not require_external and artifact.get("storage") == "external_or_regenerable_local_artifact":
            missing_external.append(artifact["path"])
            continue
        if not path.is_file() or sha256_file(path) != artifact["sha256"]:
            raise ValueError(f"Baseline artifact missing or mutated: {artifact['path']}")
        verified += 1
    for reference, expected in manifest["protected_refs"].items():
        try:
            actual = _git(root, "rev-parse", "--verify", reference).decode().strip()
        except subprocess.CalledProcessError:
            continue  # CI shallow checkouts may not have all local tracking refs.
        if actual != expected:
            raise ValueError(f"Protected reference changed: {reference}")
    return {"verified_artifacts": verified, "missing_external": missing_external,
            "status": "verified" if not missing_external else "partial_external_artifacts_absent",
            "manifest_content_sha256": digest}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--freeze-baseline", action="store_true")
    parser.add_argument("--initialize-registry", action="store_true")
    parser.add_argument("--allow-missing-external", action="store_true")
    args = parser.parse_args()
    if args.freeze_baseline:
        freeze_baseline(args.root)
    if args.initialize_registry:
        initialize_registry(args.root)
    verification = verify_baseline(args.root, require_external=not args.allow_missing_external)
    inventory = generate_inventory(args.root)
    output = args.root / "publication/inventory.json"
    output.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    lines = ["# Publication experiment inventory", "", f"Declared final attempts: {inventory['declared_final_attempts']}",
             f"Pilot attempts (excluded): {len(inventory['pilot_runs'])}", "", "| Experiment | Scenario | Replicate | Run | Status |",
             "|---|---|---|---|---|"]
    lines.extend("| " + " | ".join(str(row[field]) for field in ["experiment_id", "scenario_id", "replicate_id", "run_id", "status"]) + " |" for row in inventory["runs"])
    lines.extend(["", inventory["denominator_policy"], "", f"Baseline verification: `{verification['status']}`; {verification['verified_artifacts']} checked artifacts.", ""])
    (args.root / "publication/inventory.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(json.dumps({"baseline": verification, "status_counts": inventory["status_counts"], "integrity_valid": inventory["integrity_valid"]}, indent=2))
    if not inventory["integrity_valid"]:
        raise SystemExit(1)
