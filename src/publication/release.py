"""Fail-closed publication artifact validation; audits are not release approval.

No inference, data rebuilding, publishing, Git commits or tagging occurs here.
Checksums provide accidental-mutation detection, not trusted attestation.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import re
import subprocess
from pathlib import Path
from typing import Any

from publication.contracts import (
    TERMINAL,
    _verify_protocol,
    canonical_hash,
    generate_inventory,
    load_registry,
    safe_path,
    sha256_file,
    utc_now,
    verify_baseline,
    verify_run_artifacts,
)

REQUIRED_FAMILIES = ("PUB-02", "PUB-03", "PUB-04", "PUB-05")
LOCK_PATHS = ("requirements.txt", "environment.yml", "pyproject.toml")
PAPER_MANIFEST = "publication/paper_artifact_manifest.json"
REPRO_MANIFEST = "REPRODUCIBILITY_MANIFEST.json"
ARTIFACT_KINDS = {"aggregate", "report", "figure", "table", "limitation", "protocol", "methodology"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def reference(root: Path, relative: str) -> dict[str, str]:
    return {"path": relative, "sha256": sha256_file(safe_path(root, relative))}


def bind_artifact(root: Path, relative: str, *, artifact_id: str, kind: str,
                  source_paths: list[str], experiment_ids: list[str],
                  regenerate_command: str) -> dict[str, Any]:
    """Create identity/freshness metadata AFTER regenerating a scientific artifact."""
    if kind not in ARTIFACT_KINDS or not artifact_id or not source_paths or not regenerate_command:
        raise ValueError("Artifact requires an ID, known kind, sources and regeneration command")
    if relative in source_paths:
        raise ValueError("An artifact cannot be its own freshness source")
    return {**reference(root, relative), "artifact_id": artifact_id, "kind": kind,
            "sources": [reference(root, source) for source in source_paths],
            "experiment_ids": experiment_ids, "regenerate_command": regenerate_command}


def verify_reference(root: Path, item: dict[str, str]) -> Path:
    path = safe_path(root, item["path"])
    if not re.fullmatch(r"[a-f0-9]{64}", item["sha256"]):
        raise ValueError("Invalid SHA-256 representation")
    if not path.is_file() or sha256_file(path) != item["sha256"]:
        raise ValueError(f"Missing or stale artifact/source: {item['path']}")
    return path


def runtime_environment(root: Path) -> dict[str, Any]:
    packages = {}
    for line in (root / "requirements.txt").read_text(encoding="utf-8").splitlines():
        if "==" not in line or line.lstrip().startswith("#"):
            continue
        name, expected = line.strip().split("==", 1)
        try:
            installed = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            installed = None
        packages[name] = {"expected": expected, "installed": installed}
    python_match = re.search(r"python=(\d+\.\d+\.\d+)", (root / "environment.yml").read_text(encoding="utf-8"))
    expected_python = python_match.group(1) if python_match else None
    return {"python_version": platform.python_version(), "expected_python_version": expected_python,
            "platform": platform.platform(), "packages": packages}


def verify_runtime(environment: dict[str, Any]) -> None:
    if not environment["expected_python_version"] or environment["python_version"] != environment["expected_python_version"]:
        raise ValueError("Python runtime does not match the declared scientific environment")
    if not environment["packages"]:
        raise ValueError("Scientific dependency lock is empty")
    mismatches = [name for name, values in environment["packages"].items() if values["installed"] != values["expected"]]
    if mismatches:
        raise ValueError(f"Scientific runtime packages differ from lock: {', '.join(mismatches)}")


def verify_artifact(root: Path, item: dict[str, Any]) -> None:
    if not item.get("artifact_id") or item.get("kind") not in ARTIFACT_KINDS:
        raise ValueError("Artifact ID/kind is invalid")
    verify_reference(root, item)
    if not item.get("sources") or not item.get("regenerate_command", "").strip():
        raise ValueError("Artifact needs nonempty sources and an explicit reproduction command")
    if any(source["path"] == item["path"] for source in item["sources"]):
        raise ValueError("Self-referential source is not freshness evidence")
    for source in item["sources"]:
        verify_reference(root, source)


def verify_aggregate(root: Path, item: dict[str, Any], runs: list[dict[str, Any]]) -> None:
    payload = read_json(safe_path(root, item["path"]))
    expected = {row["path"] for row in runs}
    declared = payload.get("declared_run_paths", [])
    if set(declared) != expected or len(declared) != len(expected):
        raise ValueError("Aggregate does not account exactly once for every declared attempt")
    if payload.get("experiment_id") not in item["experiment_ids"]:
        raise ValueError("Aggregate experiment identity differs from artifact declaration")
    sources = payload.get("result_source_sha256", {})
    required = {relative + "/result.json" for relative in expected}
    if set(sources) != required:
        raise ValueError("Aggregate sources omit or add a declared result, including failure results")
    for relative, digest in sources.items():
        verify_reference(root, {"path": relative, "sha256": digest})
    manifest_sources = {source["path"]: source["sha256"] for source in item["sources"]}
    if any(manifest_sources.get(relative) != digest for relative, digest in sources.items()):
        raise ValueError("Paper manifest does not bind every aggregate result source")


def verify_claim(claim: dict[str, Any], runs: dict[str, dict[str, Any]],
                 results: dict[str, dict[str, Any]], artifacts: dict[str, dict[str, Any]]) -> None:
    kind = claim.get("kind")
    if kind not in {"positive", "negative", "limitation"} or not claim.get("claim_id") or not claim.get("text"):
        raise ValueError("Claim needs identity, text and positive/negative/limitation classification")
    source_ids = claim.get("source_artifacts", [])
    if not source_ids or any(source not in artifacts for source in source_ids):
        raise ValueError("Claim references absent paper artifacts")
    support = claim.get("support_runs", [])
    if kind != "limitation" and not support:
        raise ValueError("Scientific claims require declared final run support")
    for relative in support:
        if relative not in runs or relative not in results:
            raise ValueError("Claim depends on an undeclared, pilot, missing or invalid attempt")
        row, result = runs[relative], results[relative]
        if row["status"] not in TERMINAL:
            raise ValueError("Claim depends on a nonterminal attempt")
        if kind == "positive" and (row["status"] != "completed" or not all(result.get("gates", {}).get(gate) is True for gate in ("provenance", "sampler", "ppc", "scientific"))):
            raise ValueError("Positive scientific claim depends on a rejected/failed/ungated result")
        if not any(row["experiment_id"] in artifacts[source].get("experiment_ids", []) for source in source_ids):
            raise ValueError("Claim artifacts are not linked to the supporting experiment")


def verify_m6_disposition(root: Path, manifest: dict[str, Any],
                          experiments: dict[str, dict[str, Any]]) -> None:
    if experiments.get("PUB-06", {}).get("expected_runs"):
        if manifest.get("m6_disposition", {}).get("mode") != "executed":
            raise ValueError("Declared M6 experiments require executed disposition and full evidence")
        return
    disposition = manifest.get("m6_disposition", {})
    if disposition.get("mode") != "methodologically_blocked" or not disposition.get("reason", "").strip():
        raise ValueError("Unexecuted M6 requires an explicit protocol-backed methodological limitation")
    identity = disposition["protocol"]
    _verify_protocol(root, identity)
    protocol = read_json(safe_path(root, identity["path"]))
    if (protocol.get("experiment_id") != "PUB-06"
            or protocol.get("execution_disposition") != "methodologically_blocked"
            or not protocol.get("blocking_evidence") or protocol.get("m6_scientific_claims_allowed") is not False):
        raise ValueError("M6 omission protocol does not identify blocking evidence and forbid M6 claims")
    for item in protocol["blocking_evidence"]:
        verify_reference(root, item)
    artifact_id = disposition.get("limitation_artifact_id")
    items = {item["artifact_id"]: item for item in manifest.get("artifacts", [])}
    if artifact_id not in items or items[artifact_id]["kind"] != "limitation" or "PUB-06" not in items[artifact_id]["experiment_ids"]:
        raise ValueError("M6 omission needs a linked limitation artifact")
    for claim in manifest.get("claims", []):
        if claim["kind"] != "limitation" and any("PUB-06" in items[source].get("experiment_ids", []) for source in claim["source_artifacts"]):
            raise ValueError("Omitted M6 cannot support scientific performance claims")


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE).decode().strip()


def verify_reproducibility_manifest(root: Path) -> None:
    payload = read_json(root / REPRO_MANIFEST)
    if payload.get("schema_version") != "publication-reproducibility-v1" or payload.get("missing_evidence"):
        raise ValueError("Reproducibility manifest is absent, incomplete, or has an unknown schema")
    evidence = payload.get("evidence", [])
    paths = [item["path"] for item in evidence]
    if not evidence or REPRO_MANIFEST in paths or len(paths) != len(set(paths)):
        raise ValueError("Reproducibility evidence is empty, duplicated or circular")
    for item in evidence:
        verify_reference(root, item)
    if canonical_hash(payload["validation_snapshot"]) != payload["audit_content_sha256"]:
        raise ValueError("Embedded release audit was modified")
    if not payload.get("code_commit"):
        raise ValueError("Reproducibility manifest lacks a code commit")
    _git(root, "merge-base", "--is-ancestor", payload["code_commit"], "HEAD")


def validate_publication_release(root: Path, *, manifest_path: str = PAPER_MANIFEST) -> dict[str, Any]:
    """Return an exhaustive audit. Missing prerequisites are failures, not skips."""
    root = root.resolve()
    checks: list[dict[str, Any]] = []

    def check(name: str, function) -> Any:
        try:
            detail = function()
        except (ValueError, KeyError, IndexError, TypeError, OSError, subprocess.CalledProcessError) as exc:
            checks.append({"check": name, "status": "failed", "reason": str(exc)})
            return None
        checks.append({"check": name, "status": "passed"})
        return detail

    baseline = check("protected_baseline", lambda: verify_baseline(root))
    registry = check("registry_schema", lambda: load_registry(root)) or {"experiments": []}
    inventory = check("registry_integrity", lambda: generate_inventory(root)) or {"runs": [], "integrity_valid": False}
    if not inventory["integrity_valid"]:
        checks.append({"check": "run_integrity", "status": "failed", "reason": "Inventory contains invalid identities or undeclared final attempts"})
    environment = check("runtime_snapshot", lambda: runtime_environment(root))
    if environment:
        check("scientific_runtime", lambda: verify_runtime(environment))
    manifest = check("paper_manifest", lambda: read_json(safe_path(root, manifest_path))) or {}
    if manifest.get("schema_version") != "publication-paper-artifacts-v1":
        checks.append({"check": "paper_manifest_schema", "status": "failed", "reason": "Missing/unknown publication-paper-artifacts-v1 schema"})
    experiments = {item["experiment_id"]: item for item in registry["experiments"]}
    runs = {row["path"]: row for row in inventory["runs"]}
    results = {}
    for relative, row in runs.items():
        if row["status"] not in TERMINAL:
            checks.append({"check": f"run:{relative}", "status": "failed", "reason": "Declared attempt is missing or not terminal"})
            continue
        result = check(f"run_artifacts:{relative}", lambda relative=relative: verify_run_artifacts(safe_path(root, relative)))
        if result:
            results[relative] = result
        def run_identity(relative=relative):
            config = read_json(safe_path(root, relative + "/run_config.json"))
            _verify_protocol(root, config["protocol"])
            if config["mode"] != "final" or config["code"].get("working_tree_status"):
                raise ValueError("Final evidence requires a clean declared source configuration")
            if not config["code"].get("commit"):
                raise ValueError("Final evidence lacks a code commit")
            _git(root, "merge-base", "--is-ancestor", config["code"]["commit"], "HEAD")
            for name in LOCK_PATHS:
                if config["environment_lock_sha256"].get(name) != sha256_file(root / name):
                    raise ValueError(f"Run uses a different unaccounted scientific environment: {name}")
            if relative in results and "input_sha256" in results[relative]:
                if sha256_file(safe_path(root, relative + "/input.csv")) != results[relative]["input_sha256"]:
                    raise ValueError("Result input identity differs from preserved observations")
        check(f"run_provenance:{relative}", run_identity)
    artifacts = {}
    for item in manifest.get("artifacts", []):
        artifact_id = item.get("artifact_id", "<missing>")
        if artifact_id in artifacts:
            checks.append({"check": f"artifact:{artifact_id}", "status": "failed", "reason": "Duplicate paper artifact ID"})
        artifacts[artifact_id] = item
        check(f"artifact:{artifact_id}", lambda item=item: verify_artifact(root, item))
    required = list(REQUIRED_FAMILIES)
    if experiments.get("PUB-06", {}).get("expected_runs"):
        required.append("PUB-06")
    for family in required:
        def family_check(family=family):
            experiment = experiments.get(family, {})
            if not experiment.get("expected_runs") or not experiment.get("protocol"):
                raise ValueError("Mandatory scientific family has no declared final batch and frozen protocol")
            _verify_protocol(root, experiment["protocol"])
            family_artifacts = [item for item in artifacts.values() if family in item.get("experiment_ids", [])]
            kinds = {item["kind"] for item in family_artifacts}
            if not {"aggregate", "report", "figure", "table"}.issubset(kinds):
                raise ValueError("Family lacks aggregate/report/figure/table publication evidence")
            family_runs = [row for row in runs.values() if row["experiment_id"] == family]
            for item in family_artifacts:
                if item["kind"] == "aggregate":
                    verify_aggregate(root, item, family_runs)
        check(f"required_family:{family}", family_check)
    check("m6_disposition", lambda: verify_m6_disposition(root, manifest, experiments))
    def environment_locks():
        locks = {item["path"]: item for item in manifest.get("environment_locks", [])}
        if not set(LOCK_PATHS).issubset(locks):
            raise ValueError("Paper manifest lacks the complete scientific environment lock identity")
        for item in locks.values():
            verify_reference(root, item)
    check("environment_locks", environment_locks)
    def benchmark_environment():
        path = verify_reference(root, manifest["benchmark_environment"])
        payload = read_json(path)
        if not payload.get("python_version") or not payload.get("packages") or not payload.get("isolated"):
            raise ValueError("Independent benchmark environment must be isolated and version-identified")
        if not payload.get("lock_files"):
            raise ValueError("Benchmark environment lacks preserved dependency locks")
        for item in payload["lock_files"]:
            verify_reference(root, item)
    check("benchmark_environment", benchmark_environment)
    seen_claims = set()
    for claim in manifest.get("claims", []):
        claim_id = claim.get("claim_id", "<missing>")
        if claim_id in seen_claims:
            checks.append({"check": f"claim:{claim_id}", "status": "failed", "reason": "Duplicate claim identity"})
        seen_claims.add(claim_id)
        check(f"claim:{claim_id}", lambda claim=claim: verify_claim(claim, runs, results, artifacts))
    if not manifest.get("claims"):
        checks.append({"check": "claim_ledger", "status": "failed", "reason": "No auditable manuscript claim ledger"})
    for review in ("tests", "clean_room", "public_safety", "citation"):
        def review_check(review=review):
            payload = read_json(verify_reference(root, manifest["reviews"][review]))
            if payload.get("status") != "passed" or not payload.get("source_checksums"):
                raise ValueError("Release review must pass and bind reviewed inputs/code/environment")
            for relative, digest in payload["source_checksums"].items():
                verify_reference(root, {"path": relative, "sha256": digest})
        check(f"review:{review}", review_check)
    def citation_check():
        path = verify_reference(root, manifest["citation"])
        content = path.read_text(encoding="utf-8")
        for field in ("cff-version:", "title:", "authors:", "family-names:", "given-names:", "repository-code:", "license:"):
            if field not in content:
                raise ValueError(f"Citation metadata missing {field}")
        if re.search(r"\b(TODO|TBD|PLACEHOLDER)\b", content):
            raise ValueError("Citation metadata contains unresolved placeholders")
    check("citation_metadata", citation_check)
    check("reproducibility_manifest", lambda: verify_reproducibility_manifest(root))
    def committed_evidence():
        paths = {manifest_path, "publication/registry.json", "publication/baseline/manifest.json", "CITATION.cff", *LOCK_PATHS}
        paths.update(item["path"] for item in artifacts.values())
        paths.update(path.relative_to(root).as_posix() for path in (root / "src/publication").glob("*.py"))
        paths.update(path.relative_to(root).as_posix() for path in (root / "scripts").glob("*publication*.py"))
        _git(root, "ls-files", "--error-unmatch", "--", *sorted(paths))
        changed = _git(root, "status", "--porcelain", "--untracked-files=no", "--", *sorted(paths))
        if changed:
            raise ValueError("Release evidence is not committed or has uncommitted changes")
    check("committed_release_evidence", committed_evidence)
    failures = [item for item in checks if item["status"] == "failed"]
    return {"schema_version": "publication-release-audit-v1", "generated_at_utc": utc_now(),
            "status": "passed" if not failures else "incomplete", "release_passed": not failures,
            "checks": checks, "failed_check_count": len(failures),
            "baseline": baseline, "environment": environment,
            "declared_final_attempts": len(runs), "status_counts": inventory.get("status_counts", {}),
            "interpretation": "Validation approval is limited to declared contracts; it does not prove novelty, scientific truth, authorship, or absence of all privacy/licensing risks."}


def build_reproducibility_manifest(root: Path, audit: dict[str, Any], *,
                                   manifest_path: str = PAPER_MANIFEST) -> dict[str, Any]:
    """Bind existing evidence; never include this manifest or its hash as a source."""
    paths = {"publication/baseline/manifest.json", "publication/registry.json", manifest_path,
             "data/raw/_manifests/raw_data_current_state.json", *LOCK_PATHS}
    paths.update(path.relative_to(root).as_posix() for path in (root / "src/publication").glob("*.py"))
    paper_path = safe_path(root, manifest_path)
    if paper_path.exists():
        paper = read_json(paper_path)
        for artifact in paper.get("artifacts", []):
            paths.add(artifact["path"])
            paths.update(item["path"] for item in artifact.get("sources", []))
        paths.update(item["path"] for item in paper.get("reviews", {}).values())
        for key in ("citation", "benchmark_environment"):
            if paper.get(key):
                paths.add(paper[key]["path"])
        if paper.get("benchmark_environment"):
            environment_path = safe_path(root, paper["benchmark_environment"]["path"])
            if environment_path.exists():
                paths.update(item["path"] for item in read_json(environment_path).get("lock_files", []))
        disposition = paper.get("m6_disposition", {})
        if disposition.get("protocol"):
            paths.add(disposition["protocol"]["path"])
    registry_path = root / "publication/registry.json"
    datasets = []
    base_commit = None
    if registry_path.exists():
        registry = load_registry(root)
        base_commit = registry["base_commit"]
        for experiment in registry["experiments"]:
            if experiment.get("protocol"):
                paths.add(experiment["protocol"]["path"])
        for run in generate_inventory(root)["runs"]:
            for name in ("run_config.json", "inference_config.json", "result.json", "checksums.json"):
                relative = run["path"] + "/" + name
                if safe_path(root, relative).exists():
                    paths.add(relative)
            result_path = safe_path(root, run["path"] + "/result.json")
            if result_path.exists():
                result = read_json(result_path)
                if result.get("dataset_id"):
                    datasets.append({"run_path": run["path"], "dataset_id": result["dataset_id"],
                                     "input_sha256": result.get("input_sha256")})
    paths.discard(REPRO_MANIFEST)
    existing = [reference(root, relative) for relative in sorted(paths) if safe_path(root, relative).is_file()]
    missing = [relative for relative in sorted(paths) if not safe_path(root, relative).is_file()]
    try:
        commit = _git(root, "rev-parse", "HEAD")
    except subprocess.CalledProcessError:
        commit = None
    return {"schema_version": "publication-reproducibility-v1", "generated_at_utc": utc_now(),
            "code_commit": commit, "base_commit": base_commit, "dataset_identities": datasets,
            "release_status": audit["status"], "release_passed": audit["release_passed"],
            "audit_content_sha256": canonical_hash(audit), "validation_snapshot": audit,
            "evidence": existing, "missing_evidence": missing,
            "environment": audit["environment"], "declared_final_attempts": audit["declared_final_attempts"],
            "self_hash_policy": "This file is deliberately excluded from evidence to avoid circular self-identity.",
            "storage_policy": "Large traces require exact checksummed external restoration or protocol-defined regeneration; no archive DOI is invented."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--manifest", default=PAPER_MANIFEST)
    parser.add_argument("--audit", action="store_true", help="Write incomplete audit evidence without pretending to pass the release gate")
    parser.add_argument("--write-manifest", action="store_true", help="Generate REPRODUCIBILITY_MANIFEST.json with explicit pass/incomplete status")
    args = parser.parse_args()
    report = validate_publication_release(args.root, manifest_path=args.manifest)
    destination = args.root / "publication"
    destination.mkdir(exist_ok=True)
    (destination / "release_audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    lines = ["# Publication release audit", "", f"Status: **{report['status']}**. Release approved: `{report['release_passed']}`.", "",
             f"Declared final attempts: {report['declared_final_attempts']}. Failed checks: {report['failed_check_count']}.", "",
             "| Check | Status | Reason |", "|---|---|---|"]
    lines.extend(f"| {row['check']} | {row['status']} | {row.get('reason', '').replace('|', '/')} |" for row in report["checks"])
    lines.extend(["", report["interpretation"], ""])
    (destination / "release_audit.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    if args.write_manifest:
        payload = build_reproducibility_manifest(args.root, report, manifest_path=args.manifest)
        (args.root / REPRO_MANIFEST).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": report["status"], "release_passed": report["release_passed"],
                      "failed_checks": report["failed_check_count"], "audit_only": args.audit}, indent=2))
    if not report["release_passed"] and not args.audit:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
