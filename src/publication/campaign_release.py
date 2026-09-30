"""Current campaign release audit: integrity, scientific sign and readiness differ.

Exit 1 means a structured, legitimate public-release prerequisite is pending.
Exit 2 means missing/corrupt evidence or an unexpected validator exception.
Rejected scientific outcomes are preserved evidence, not integrity failures.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from publication.claim_authorization import authorize_claim
from publication.evidence_archive import (
    digest_file,
    read_json,
    safe_file,
    verify_inventory,
    write_new,
)

TERMINAL = {"COMPLETED", "COMPLETED_REJECTED", "FAILED_TECHNICAL", "CANCELLED", "BLOCKED"}
PUBLIC_REVIEWS = ("citation", "public_safety", "third_party_redistribution", "external_archive",
                  "exact_scientific_environment", "clean_room", "remote_ci")


def audit_campaign_rows(root: Path, registry: dict) -> list[dict]:
    """Compare independently persisted declarations, attempts and execution state."""
    result = []
    campaigns = registry.get("campaign_registries", [])
    if not campaigns or len({row["campaign_id"] for row in campaigns}) != len(campaigns):
        raise ValueError("Current campaign registry is empty or duplicated")
    for item in campaigns:
        declaration = read_json(safe_file(root, item["frozen_declaration"]))
        state = read_json(safe_file(root, item["execution_state"]))
        summary_path = str(Path(item["final_report"]).parent.as_posix()) + "/campaign_summary.json"
        summary = read_json(safe_file(root, summary_path))
        planned = declaration["declared_jobs"]
        jobs = summary["jobs"]
        if not planned or len({row["job_id"] for row in planned}) != len(planned):
            raise ValueError("Frozen declaration is empty or has duplicate jobs")
        by_id = {row["job_id"]: row for row in jobs}
        if len(by_id) != len(jobs) or set(by_id) != {row["job_id"] for row in planned}:
            raise ValueError("Aggregate omitted or added a declared job")
        if any(summary.get(key) != item["campaign_id"] for key in ("campaign_id",)):
            raise ValueError("Campaign report identity mismatch")
        family_counts = Counter(row["experiment_id"] for row in planned)
        if dict(family_counts) != item["declared_job_counts"]:
            raise ValueError("Registry family counts differ from frozen declaration")
        if summary["declared_jobs"] != len(planned) or summary["total_attempts"] != len(summary["attempts"]):
            raise ValueError("Declared job/attempt denominator mismatch")
        if len({(row["job_id"], row["attempt_index"]) for row in summary["attempts"]}) != len(summary["attempts"]):
            raise ValueError("Duplicate attempt identity")
        if not summary.get("complete_declared_batch") or summary.get("integrity_errors") or summary.get("preflight_errors"):
            raise ValueError("Campaign aggregate declares incomplete/corrupt evidence")
        state_jobs = state["jobs"]
        if isinstance(state_jobs, list):
            state_jobs = {row["job_id"]: row for row in state_jobs}
        if set(state_jobs) != set(by_id):
            raise ValueError("Execution state differs from final declaration")
        for row in planned:
            job = by_id[row["job_id"]]
            persisted = state_jobs[row["job_id"]]
            for key in ("experiment_id", "scenario_id", "replicate_id", "seeds"):
                if row[key] != job[key]:
                    raise ValueError(f"Changed declared identity/seed: {row['job_id']}:{key}")
            if job["status"] not in TERMINAL or job["status"] != persisted["status"]:
                raise ValueError("Nonterminal or changed job status")
            attempts = [attempt for attempt in summary["attempts"] if attempt["job_id"] == row["job_id"]]
            if len(attempts) != len(persisted["attempts"]):
                raise ValueError("Historical attempts were omitted")
            for attempt, source in zip(sorted(attempts, key=lambda item: item["attempt_index"]), persisted["attempts"]):
                if attempt["status"] != source["status"]:
                    raise ValueError("Historical attempt status changed")
                checksum = attempt.get("completion_manifest_sha256")
                if checksum:
                    completion_path = safe_file(root, attempt["output_dir"] + "/completion_manifest.json")
                    if digest_file(completion_path) != checksum:
                        raise ValueError("Sealed completion manifest differs")
                    completion = read_json(completion_path)
                    if completion["status"] != attempt["status"]:
                        raise ValueError("Completion/attempt status mismatch")
                elif attempt["status"] not in {"CANCELLED", "FAILED_TECHNICAL", "BLOCKED"}:
                    raise ValueError("Scientific terminal attempt has no sealed completion")
        counts = dict(Counter(row["status"] for row in jobs))
        if counts != summary["status_counts"]:
            raise ValueError("Status denominator mismatch")
        result.append({"campaign_id": item["campaign_id"], "declared_jobs": len(planned),
                       "preserved_attempts": len(summary["attempts"]), "status_counts": counts,
                       "family_job_counts": dict(family_counts),
                       "meaning": "Execution and preservation counts; scientific rejection is not technical corruption."})
    return result


def validate_synthesis(root: Path, relative: str) -> dict:
    directory = safe_file(root, relative)
    manifest = read_json(directory / "artifact_manifest.json")
    if manifest.get("schema_version") != "tcc-evidence-v2":
        raise ValueError("Current review requires the explicitly versioned v2 synthesis")
    for group, base in (("artifacts", directory), ("source_checksums", root), ("generator_source_checksums", root)):
        if not manifest.get(group):
            raise ValueError(f"Synthesis lacks {group}")
        for name, checksum in manifest[group].items():
            if digest_file(safe_file(base, name)) != checksum:
                raise ValueError(f"Stale synthesis source/artifact: {name}")
    if "claims.json" not in manifest["artifacts"]:
        raise ValueError("Synthesis lacks a checksum-bound claim ledger")
    claims = read_json(directory / "claims.json")
    if claims.get("schema_version") != "tcc-claims-v2" or not claims.get("evaluator_version") or not claims.get("claims"):
        raise ValueError("Missing versioned scientific claim scope")
    if len({claim["claim_id"] for claim in claims["claims"]}) != len(claims["claims"]):
        raise ValueError("Duplicate scientific claim ID")
    for claim in claims["claims"]:
        if not all(key in claim for key in ("status", "scope", "sources", "supported_text", "unsupported_claims", "denominators")):
            raise ValueError("Claim omits scope, limitations, sources or denominators")
        if not claim["sources"]:
            raise ValueError("Unbound scientific claim")
        for name, checksum in claim["sources"].items():
            if digest_file(safe_file(root, name)) != checksum:
                raise ValueError("Claim source is stale")
    evaluations = claims["run_evaluations_path"]
    if evaluations not in manifest["artifacts"]:
        raise ValueError("Run-level claim authorizations are not checksum-bound")
    run_evaluations = read_json(safe_file(directory, evaluations))
    if not isinstance(run_evaluations, list) or not run_evaluations:
        raise ValueError("Run-level claim authorization list is empty")
    by_run = {}
    for evaluation in run_evaluations:
        identity = evaluation["run_identity"]
        run_id = identity["run_id"]
        if run_id in by_run:
            raise ValueError("Duplicate run-level claim evaluation")
        by_run[run_id] = evaluation
        if evaluation.get("schema_version") != claims["evaluator_version"] or not evaluation.get("source_checksums"):
            raise ValueError("Run evaluation lacks versioned, bound evidence")
        for name, checksum in evaluation["source_checksums"].items():
            if digest_file(safe_file(root, name)) != checksum:
                raise ValueError("Run evaluation source changed")
        dimensions = evaluation["dimensions"]
        if not {"provenance_integrity", "computational_screen", "predictive_screen",
                "physical_scale_screen", "parameter_information", "manuscript_claim_permissions"}.issubset(dimensions):
            raise ValueError("Claim evaluation conflates evidence dimensions")
    for claim in claims["claims"]:
        for authorization in claim.get("run_authorizations", []):
            authorize_claim(by_run[authorization["run_id"]], authorization["permission"])
    return {"claim_count": len(claims["claims"]), "evaluator_version": claims["evaluator_version"],
            "scope": "Claim-source and versioned authorization integrity; no demand that study findings be favorable."}


def validate_campaign_release(root: Path, *, inventory_path: str, synthesis: str,
                              reviews_path: str = "publication/public_release_reviews.json") -> dict:
    checks, errors, blockers = [], [], []

    def check(name, function):
        try:
            value = function()
        except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
            errors.append({"check": name, "reason": str(exc), "classification": "invalid_or_missing_evidence"})
            checks.append({"check": name, "status": "failed"})
            return None
        checks.append({"check": name, "status": "passed"})
        return value

    inventory = check("transitive_inventory", lambda: read_json(safe_file(root, inventory_path)))
    if inventory:
        check("transitive_byte_integrity", lambda: verify_inventory(root, inventory))
    campaigns = check("declared_campaigns_and_attempts", lambda: audit_campaign_rows(root, read_json(root / "publication/registry.json")))
    claim_summary = check("scientific_claim_sources", lambda: validate_synthesis(root, synthesis))
    review_file = safe_file(root, reviews_path)
    reviews = read_json(review_file) if review_file.exists() else {}
    for name in PUBLIC_REVIEWS:
        reference = reviews.get(name)
        if not reference:
            blockers.append({"check": name, "classification": "public_release_prerequisite_pending",
                             "reason": "No completed, source-bound review/deposition receipt supplied."})
            continue

        def review_check(reference=reference):
            path = safe_file(root, reference["path"])
            if digest_file(path) != reference["sha256"]:
                raise ValueError("Public review receipt hash mismatch")
            review = read_json(path)
            if review.get("status") != "passed" or not review.get("source_checksums"):
                raise ValueError("Public review lacks passed, source-bound evidence")
            for name, checksum in review["source_checksums"].items():
                if digest_file(safe_file(root, name)) != checksum:
                    raise ValueError("Public review sources changed")
        check("public_review:" + name, review_check)
    status = "invalid_evidence" if errors else "blocked_public_release" if blockers else "passed"
    return {"schema_version": "publication-campaign-release-audit-v2", "status": status,
            "integrity_status": "failed" if errors else "passed", "release_passed": status == "passed",
            "scientific_outcome_policy": "Positive, qualified and negative results can be preserved/published; no gate weakening or favorable-outcome requirement.",
            "declared_final_jobs": sum(row["declared_jobs"] for row in campaigns or []),
            "declared_final_attempts": sum(row["preserved_attempts"] for row in campaigns or []),
            "campaigns": campaigns, "claims": claim_summary, "checks": checks,
            "integrity_errors": errors, "public_release_blockers": blockers,
            "exit_code": 2 if errors else 1 if blockers else 0,
            "scope": "Exact existing evidence availability is distinct from numeric re-execution and public archival readiness."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--inventory", default="publication/validation/external_audit_closure_v1/transitive_inventory_final.json")
    parser.add_argument("--synthesis", default="reports/publication_synthesis/tcc_evidence_v2")
    parser.add_argument("--reviews", default="publication/public_release_reviews.json")
    parser.add_argument("--audit-output", type=Path)
    parser.add_argument("--audit", action="store_true", help="Retained spelling; does not change truthful exit classifications")
    args = parser.parse_args()
    try:
        report = validate_campaign_release(args.root, inventory_path=args.inventory, synthesis=args.synthesis, reviews_path=args.reviews)
        if args.audit_output:
            write_new(args.audit_output, report)
    except Exception as exc:
        print(json.dumps({"status": "validator_error", "error_type": type(exc).__name__, "reason": str(exc), "exit_code": 2}), file=sys.stderr)
        raise SystemExit(2) from exc
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(report["exit_code"])


if __name__ == "__main__":
    main()
