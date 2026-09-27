"""Deterministic campaign expansion and pre-execution scientific identity checks."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path

from publication.contracts import canonical_hash, committed_protocol, safe_path, sha256_file

DEFAULT_CONFIG = "configs/publication/tcc_final_campaign.json"
PHASES = ("PUB-02", "PUB-03", "PUB-04", "PUB-05", "PUB-06")
RUNTIME_AMENDMENT_PATHS = frozenset({"src/publication/campaign.py", "src/publication/campaign_plan.py"})


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def seed(campaign: str, experiment: str, scenario: str, replicate: str, stream: str) -> int:
    return int(canonical_hash(["campaign-seed-v1", campaign, experiment, scenario, replicate, stream])[:8], 16)


def scientific_config(config: dict) -> dict:
    """Only runtime budget/concurrency and interpreter paths may vary on resume."""
    return {key: value for key, value in config.items() if key not in {"resources", "runtime", "description"}}


def _safe(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,120}", value):
        raise ValueError(f"Unsafe identity: {value!r}")
    return value


def source_identity(root: Path) -> dict:
    paths = list((root / "src").rglob("*.py"))
    paths += list((root / "scripts").rglob("*.py"))
    return {path.relative_to(root).as_posix(): sha256_file(path) for path in sorted(set(paths)) if path.is_file()}


def uncommitted_sources(root: Path, sources: dict) -> list[str]:
    """Compare actual source bytes to HEAD blobs without refreshing the huge RAW index.

    Sources are LF-normalized by .gitattributes. Git's object hash binds the
    canonical blob header plus file bytes; the release ledger separately uses
    SHA-256 file hashes. Both SHA-1 and SHA-256 Git object formats are supported.
    """
    records = subprocess.check_output(["git", "-C", str(root), "ls-tree", "-rz", "HEAD", "--", "src", "scripts"])
    committed = {}
    for record in records.split(b"\0"):
        if record:
            metadata, path = record.split(b"\t", 1)
            _, kind, digest = metadata.split()
            if kind == b"blob":
                committed[path.decode("utf-8")] = digest.decode("ascii")
    changed = []
    for path in sources:
        expected = committed.get(path)
        if expected is None:
            changed.append(path)
            continue
        content = (root / path).read_bytes()
        algorithm = "sha1" if len(expected) == 40 else "sha256"
        actual = hashlib.new(algorithm, b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
        if actual != expected:
            changed.append(path)
    changed.extend(path for path in committed if path.endswith(".py") and path not in sources)
    return sorted(changed)


def _git_blob(root: Path, commit: str, relative: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), "show", f"{commit}:{relative}"], stderr=subprocess.PIPE)


def _amendment_json(content: bytes) -> dict:
    def unique_object(pairs):
        result = {}
        for name, value in pairs:
            if name in result:
                raise ValueError(f"Duplicate runtime amendment JSON key: {name}")
            result[name] = value
        return result

    payload = json.loads(content, object_pairs_hook=unique_object)
    if not isinstance(payload, dict):
        raise ValueError("Runtime amendment record must be a JSON object")
    return payload


def _sha256_digest(value: str) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _verify_initialized_ledger(root: Path, campaign_id: str, frozen_plan_path: str) -> str | None:
    """Bind an active campaign to its launch ledger, not its first draft.

    Do not check state.exists() before reading: DrvFS can briefly report ENOENT
    during atomic replacement. The controller's bounded reader retries that
    race. A preexisting campaign namespace without readable state fails closed;
    only a namespace that does not exist can be treated as not initialized.
    """
    from publication.campaign import CampaignIntegrityError, _read, _verify_journal

    state_path = safe_path(root, f"artifacts/publication_campaign/{campaign_id}/campaign_state.json")
    try:
        state = _read(state_path)
    except FileNotFoundError as exc:
        if state_path.parent.exists():
            raise ValueError("Campaign namespace exists but its initialization checkpoint is unavailable") from exc
        return None
    try:
        _verify_journal(state)
    except (CampaignIntegrityError, KeyError, TypeError) as exc:
        raise ValueError("Campaign initialization journal is invalid") from exc
    commit = state.get("code_commit")
    if state.get("campaign_id") != campaign_id or not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit) is None:
        raise ValueError("Campaign initialization requires its exact original source commit and campaign ID")
    ancestor = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", commit, "HEAD"], capture_output=True, check=False)
    if ancestor.returncode != 0:
        raise ValueError("Campaign initialization source commit is not an ancestor of HEAD")
    if _git_blob(root, commit, frozen_plan_path) != safe_path(root, frozen_plan_path).read_bytes():
        raise ValueError("Frozen campaign ledger differs from its initialization commit; runtime amendments cannot rewrite scientific history")
    return commit


def validate_runtime_amendments(root: Path, campaign_id: str, frozen_plan_path: str,
                                frozen_plan: dict, current_sources: dict) -> dict | None:
    """Authorize only committed operational repairs, never changed science.

    The original ledger is immutable. A separate committed record must append
    to its entire Git history, identify reviewed source commits and immutable
    validation evidence, and form an exact SHA-256 chain from the frozen map.
    Even approved runtime files must separately match committed HEAD bytes.
    """
    campaign_id = _safe(campaign_id)
    _verify_initialized_ledger(root, campaign_id, frozen_plan_path)
    relative = f"publication/runtime_amendments/{campaign_id}.json"
    record_path = safe_path(root, relative)
    try:
        head_record = _git_blob(root, "HEAD", relative)
    except subprocess.CalledProcessError:
        if record_path.exists():
            raise ValueError("Runtime amendment record is not committed") from None
        prior_record = subprocess.check_output(["git", "-C", str(root), "rev-list", "-n", "1", "HEAD", "--", relative]).strip()
        if prior_record:
            raise ValueError("A previously committed runtime amendment record cannot be deleted") from None
        if frozen_plan["source_checksums"] != current_sources:
            raise ValueError("Scientific campaign source differs from frozen tested source without an audited runtime amendment") from None
        return None
    if not record_path.is_file() or record_path.read_bytes() != head_record:
        raise ValueError("Runtime amendment record differs from committed HEAD bytes")
    record = _amendment_json(head_record)
    required = {"schema_version", "campaign_id", "frozen_plan_sha256", "amendments"}
    if set(record) != required or record["schema_version"] != "campaign-runtime-amendments-v1":
        raise ValueError("Invalid runtime amendment schema")
    if record["campaign_id"] != campaign_id or record["frozen_plan_sha256"] != sha256_file(safe_path(root, frozen_plan_path)):
        raise ValueError("Runtime amendment campaign/frozen-plan identity mismatch")
    if not isinstance(record["amendments"], list) or not record["amendments"]:
        raise ValueError("Runtime amendment list must be nonempty")
    history = subprocess.check_output(["git", "-C", str(root), "rev-list", "--reverse", "HEAD", "--", relative]).decode().splitlines()
    previous = []
    for commit in history:
        try:
            historical = _amendment_json(_git_blob(root, commit, relative))
        except subprocess.CalledProcessError as exc:
            raise ValueError("Runtime amendment history contains a deletion") from exc
        if ({key: value for key, value in historical.items() if key != "amendments"}
                != {key: value for key, value in record.items() if key != "amendments"}):
            raise ValueError("Runtime amendment history changed its frozen identity/schema")
        entries = historical.get("amendments")
        if not isinstance(entries, list) or entries[:len(previous)] != previous or len(entries) < len(previous):
            raise ValueError("Runtime amendment history is not append-only")
        previous = entries
    if previous != record["amendments"]:
        raise ValueError("Runtime amendment HEAD differs from its recorded history")
    expected_sources = dict(frozen_plan["source_checksums"])
    amendment_ids = set()
    for amendment in record["amendments"]:
        fields = {"amendment_id", "reason", "approved_source_commit", "changes", "validation_evidence"}
        if not isinstance(amendment, dict) or set(amendment) != fields:
            raise ValueError("Invalid runtime amendment entry fields")
        identifier = _safe(amendment["amendment_id"])
        if identifier in amendment_ids:
            raise ValueError("Duplicate runtime amendment ID")
        amendment_ids.add(identifier)
        if not isinstance(amendment["reason"], str) or not amendment["reason"].strip():
            raise ValueError("Runtime amendment requires a reason")
        commit = amendment["approved_source_commit"]
        if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit) is None:
            raise ValueError("Runtime amendment requires an exact source commit ID")
        ancestor = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", commit, "HEAD"], capture_output=True, check=False)
        if ancestor.returncode != 0:
            raise ValueError("Approved runtime source commit is not an ancestor of HEAD")
        changes = amendment["changes"]
        if not isinstance(changes, dict) or not changes or set(changes) - RUNTIME_AMENDMENT_PATHS:
            raise ValueError("Runtime amendment changes are outside the exact operational-source allowlist")
        for path, change in changes.items():
            if not isinstance(change, dict) or set(change) != {"from_sha256", "to_sha256"}:
                raise ValueError("Invalid runtime source change")
            before, after = change["from_sha256"], change["to_sha256"]
            if not _sha256_digest(before) or not _sha256_digest(after) or before == after or expected_sources.get(path) != before:
                raise ValueError("Runtime amendment source SHA-256 chain is invalid")
            if hashlib.sha256(_git_blob(root, commit, path)).hexdigest() != after:
                raise ValueError("Approved source commit does not contain the declared target bytes")
            expected_sources[path] = after
        evidence = amendment["validation_evidence"]
        if not isinstance(evidence, list) or not evidence:
            raise ValueError("Runtime amendment requires committed validation evidence")
        evidence_paths = set()
        for item in evidence:
            if not isinstance(item, dict) or set(item) != {"path", "sha256"} or not _sha256_digest(item["sha256"]):
                raise ValueError("Invalid runtime validation evidence")
            evidence_path = safe_path(root, item["path"])
            if item["path"] in evidence_paths or item["path"] == relative or evidence_path.as_posix() != (root / item["path"]).as_posix():
                raise ValueError("Duplicate, circular or noncanonical runtime evidence path")
            evidence_paths.add(item["path"])
            if sha256_file(evidence_path) != item["sha256"] or hashlib.sha256(_git_blob(root, "HEAD", item["path"])).hexdigest() != item["sha256"]:
                raise ValueError("Runtime validation evidence differs from committed checksum")
    if expected_sources != current_sources:
        raise ValueError("Current source map differs from frozen sources plus exact approved runtime amendments")
    return {"path": relative, "sha256": hashlib.sha256(head_record).hexdigest(),
            "record_commit": history[-1], "frozen_plan_sha256": record["frozen_plan_sha256"],
            "amendments": record["amendments"], "effective_source_checksums_sha256": canonical_hash(expected_sources)}


def build_plan(root: Path, config_path: Path) -> dict:
    root = root.resolve()
    config_path = (root / config_path).resolve() if not config_path.is_absolute() else config_path.resolve()
    relative = config_path.relative_to(root).as_posix()
    config = read_json(config_path)
    campaign = _safe(config["campaign_id"])
    mode = config["mode"]
    if mode not in {"final", "smoke"}:
        raise ValueError("Campaign mode must be final or smoke")
    resources = {"max_workers": 1, "cores_per_run": 4, "max_campaign_hours": 36,
                 "stop_margin_minutes": 5, "estimated_run_minutes": 20, **config.get("resources", {})}
    jobs, protocols, errors = [], {}, []
    protocol_paths = config.get("protocols", {})
    for experiment, relative_protocol in protocol_paths.items():
        protocol_path = (root / relative_protocol).resolve()
        protocol_path.relative_to(root)
        if not protocol_path.exists():
            errors.append(f"Missing protocol: {relative_protocol}")
            continue
        protocol = read_json(protocol_path)
        protocols[experiment] = {"path": relative_protocol, "sha256": sha256_file(protocol_path), "payload": protocol}
        if mode == "final":
            try:
                if protocol.get("protocol_status") != "FROZEN":
                    raise ValueError("protocol is not FROZEN")
                protocols[experiment]["committed_identity"] = committed_protocol(root, relative_protocol)
            except (ValueError, OSError, subprocess.CalledProcessError) as exc:
                errors.append(f"Protocol {experiment}: {exc}")

    def add(experiment: str, scenario: str, rep: int, payload: dict, *, kind: str,
            generation_group: str | None = None, estimate: float = 1200) -> None:
        _safe(scenario)
        replicate = f"rep_{rep:04d}"
        job_id = f"{experiment}__{scenario}__{replicate}"
        seeds = {name: seed(campaign, experiment, generation_group if name == "generation" and generation_group else scenario, replicate, name)
                 for name in ("generation", "inference", "predictive", "resampling")}
        jobs.append({"job_id": job_id, "experiment_id": experiment, "scenario_id": scenario,
                     "replicate_id": replicate, "run_id": f"{campaign}__{job_id}", "seeds": seeds,
                     "command": ["{python}", "scripts/publication_campaign_job.py", "--config", relative, "--job-id", job_id],
                     "output_dir": f"artifacts/publication_campaign/{campaign}/runs/{experiment}/{scenario}/{replicate}",
                     "cores": resources["cores_per_run"], "estimated_seconds": estimate,
                     "max_technical_retries": config.get("technical_retries", 0),
                     "payload": {"kind": kind, **payload}})

    if mode == "smoke":
        for fixture in config["smoke_jobs"]:
            add(fixture.get("experiment_id", "PUB-02"), fixture["scenario_id"], 0, fixture,
                kind=fixture["kind"], estimate=fixture.get("estimated_seconds", 30))
    else:
        p2 = config["injection_recovery"]
        if p2["enabled"] and "PUB-02" in protocols:
            protocol = protocols["PUB-02"]["payload"]
            for scenario in protocol["scenarios"]:
                count = p2.get("scenario_replicates", {}).get(scenario["scenario_id"], p2["replicates_per_scenario"])
                if not isinstance(count, int) or count < 1:
                    raise ValueError("Replicate counts must be positive integers")
                declared_count = protocol.get("scenario_replicates", {}).get(scenario["scenario_id"], protocol["replicates_per_scenario"])
                if count != declared_count:
                    errors.append(f"PUB-02 {scenario['scenario_id']}: configured replicates differ from frozen protocol")
                for index in range(count):
                    add("PUB-02", scenario["scenario_id"], index,
                        {"scenario": scenario, "inference": protocol["inference"], "protocol": protocols["PUB-02"]["path"]},
                        kind="synthetic", estimate=p2.get("estimated_seconds_by_scenario", {}).get(scenario["scenario_id"], 2000))
        if config["benchmark"]["enabled"] and "PUB-03" in protocols:
            for engine in ("local", "external"):
                add("PUB-03", f"kepler_10_b_{engine}", 0,
                    {"protocol": protocols["PUB-03"]["path"]}, kind=f"benchmark_{engine}",
                    estimate=config["benchmark"].get("estimated_seconds", 3600))
        if config["ablations"]["enabled"] and "PUB-04" in protocols:
            protocol = protocols["PUB-04"]["payload"]
            if config["ablations"]["replicates_per_pair"] != protocol["replication_plan"]["replicates_per_pair"]:
                errors.append("PUB-04 configured replicates differ from frozen protocol")
            for design in protocol["paired_designs"]:
                for variant in design["variants"]:
                    variant = {"variant_id": variant, "intervention": variant} if isinstance(variant, str) else variant
                    scenario = {"truth": protocol["truth"], "design": copy.deepcopy(design["design"])}
                    if "systematic" in variant:
                        scenario["design"]["systematic"] = variant["systematic"]
                    name = f"{design['pair_id']}__{variant['variant_id']}"
                    for index in range(config["ablations"]["replicates_per_pair"]):
                        add("PUB-04", name, index, {"scenario": scenario, "inference": protocol["inference"],
                            "intervention": variant["intervention"], "pair_id": design["pair_id"],
                            "variant_id": variant["variant_id"], "protocol": protocols["PUB-04"]["path"]},
                            kind="ablation", generation_group=design["pair_id"],
                            estimate=15 if variant["intervention"] in {"invalid_input_hash", "dataset_identity_mismatch"} else 300)
        if config["multi_target"]["enabled"] and "PUB-05" in protocols:
            for target in protocols["PUB-05"]["payload"]["targets"]:
                slug = target.get("target_id", target.get("target_slug", target.get("slug")))
                if slug is None:
                    slug = target["config"]["planet_slug"]
                add("PUB-05", slug, 0, {"target_slug": slug, "protocol": protocols["PUB-05"]["path"]},
                    kind="observational", estimate=config["multi_target"].get("estimated_seconds", 1800))
        if config.get("correlated_noise", {}).get("enabled"):
            errors.append("M6 is intentionally deferred for the TCC; no validated M6 worker is installed. Do not enable it without a new frozen protocol and tested implementation.")
    if len({job["job_id"] for job in jobs}) != len(jobs):
        raise ValueError("Duplicate declared job identities")
    assigned = {}
    for job in jobs:
        for stream, value in job["seeds"].items():
            scenario = job["payload"].get("pair_id", job["scenario_id"]) if stream == "generation" else job["scenario_id"]
            identity = (job["experiment_id"], scenario, job["replicate_id"], stream)
            if value in assigned and assigned[value] != identity:
                raise ValueError("32-bit seed collision between independent streams; amend seed policy before final execution")
            assigned[value] = identity
    digest = canonical_hash({"scientific_config": scientific_config(config),
                             "protocol_sha256": {key: value["sha256"] for key, value in protocols.items()}})
    frozen_path = f"configs/publication/{campaign}_plan.json"
    frozen = root / frozen_path
    runtime_amendments = None
    if mode == "final":
        try:
            current_sources = source_identity(root)
            if changed := uncommitted_sources(root, current_sources):
                errors.append("Scientific sources differ from committed HEAD: " + ", ".join(changed))
            stored = read_json(frozen)
            if stored["scientific_config_sha256"] != digest:
                errors.append("Scientific config/protocol changed: prepare and commit a NEW campaign identity; never modify an active campaign")
            # Interpreter paths and resource ceilings can change; actual science cannot.
            expected_jobs = [{key: job[key] for key in ("job_id", "experiment_id", "scenario_id", "replicate_id", "run_id", "seeds", "payload")} for job in jobs]
            if stored["declared_jobs"] != expected_jobs:
                errors.append("Declared jobs/seeds differ from the frozen plan")
            runtime_amendments = validate_runtime_amendments(root, campaign, frozen_path, stored, current_sources)
            if subprocess.check_output(["git", "-C", str(root), "show", f"HEAD:{frozen_path}"]) != frozen.read_bytes():
                errors.append("Frozen campaign plan is not committed")
        except (OSError, KeyError, TypeError, ValueError, subprocess.CalledProcessError) as exc:
            errors.append(f"Frozen campaign plan unavailable: {exc}")
    return {"campaign_id": campaign, "mode": mode, "config_path": relative,
            "scientific_config_sha256": digest, "frozen_plan_path": frozen_path,
            "resources": resources, "runtime": config.get("runtime", {}), "jobs": jobs,
            "protocols": {key: {field: value[field] for field in ("path", "sha256")} for key, value in protocols.items()},
            "phase_order": list(PHASES), "preflight_errors": errors,
            "runtime_amendments": runtime_amendments,
            "family_summarizers": {experiment: ["{python}", "scripts/aggregate_publication_campaign.py", "--config", relative, "--family", experiment]
                                   for experiment in PHASES if any(job["experiment_id"] == experiment for job in jobs)},
            "aggregate_command": ["{python}", "scripts/aggregate_publication_campaign.py", "--config", relative],
            "estimated_total_hours": sum(job["estimated_seconds"] for job in jobs)/3600,
            "estimate_caveat": "Pilot-based planning estimate, not a completion guarantee; compiler contention and posterior geometry affect timing. Budget stops only between jobs."}


def freeze_plan(root: Path, config_path: Path) -> Path:
    """Preparation only: generate the pre-execution seed/identity ledger to commit."""
    plan = build_plan(root, config_path)
    destination = root / plan["frozen_plan_path"]
    state = root / f"artifacts/publication_campaign/{plan['campaign_id']}/campaign_state.json"
    if state.exists():
        raise FileExistsError("An initialized campaign cannot be refrozen; create a new campaign ID")
    payload = {"schema_version": "frozen-campaign-plan-v1", "campaign_id": plan["campaign_id"],
               "scientific_config_sha256": plan["scientific_config_sha256"],
               "source_checksums": source_identity(root), "protocols": plan["protocols"],
               "declared_jobs": [{key: job[key] for key in ("job_id", "experiment_id", "scenario_id", "replicate_id", "run_id", "seeds", "payload")} for job in plan["jobs"]],
               "seed_policy": "SHA256 canonical JSON ['campaign-seed-v1',campaign_id,experiment_id,scenario_or_generation_pair_id,replicate_id,stream], first32bits; fixed across retries; separate campaigns have disjoint namespaces.",
               "reproducibility_note": "Commit this generated ledger and all referenced protocols/config/source before final execution. Changing budgets is permitted, changing science requires a new campaign ID."}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(DEFAULT_CONFIG))
    parser.add_argument("--freeze-plan", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    print(freeze_plan(root, args.config) if args.freeze_plan else json.dumps(build_plan(root, args.config), indent=2))


if __name__ == "__main__":
    main()
