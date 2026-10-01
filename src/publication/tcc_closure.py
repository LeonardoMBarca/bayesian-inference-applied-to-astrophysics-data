"""Bounded TCC closure: audit and regenerate existing evidence, never inference."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from publication.audit_protection import collect, digest, verify
from publication.evidence_archive import write_new

AUDIT = "publication/validation/tcc_closure_v1"
OUTPUT = "reports/publication_synthesis/tcc_evidence_v3"
CAMPAIGNS = ("tcc_campaign_v1", "tcc_calibration_confirmatory_v1", "tcc_numerical_complement_v4")
INCIDENT_CAMPAIGN = "tcc_numerical_complement_v3"


def protect(root: Path) -> dict:
    snapshot = collect(root)
    rows = {row["path"]: row for row in snapshot["files"]}
    trees = ["reports/publication_synthesis/tcc_evidence_v2"]
    for campaign in (INCIDENT_CAMPAIGN, CAMPAIGNS[-1]):
        trees += [f"artifacts/publication_campaign/{campaign}", f"reports/publication_campaign/{campaign}",
                  f"logs/publication_campaign/{campaign}"]
    for tree in trees:
        for path in sorted((root / tree).rglob("*")):
            if path.is_file() and path.name != "campaign.lock":
                name = path.relative_to(root).as_posix()
                rows[name] = {"path": name, "size_bytes": path.stat().st_size, "sha256": digest(path),
                              "preexisting_manifest_checked": False}
    snapshot.update(files=list(sorted(rows.values(), key=lambda row: row["path"])),
                    scope="All historical baseline, campaign evidence, protocols, ledgers and v1/v2 syntheses, including interrupted v3 and completed v4.")
    return snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--protect", action="store_true")
    action.add_argument("--check-protected", action="store_true")
    action.add_argument("--build", action="store_true")
    action.add_argument("--check", action="store_true")
    action.add_argument("--verify-original", action="store_true")
    action.add_argument("--audit-traces", action="store_true")
    action.add_argument("--validate-code", action="store_true")
    parser.add_argument("--output", default=OUTPUT)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    if args.protect:
        snapshot = protect(root)
        write_new(root / AUDIT / "protected_snapshot.json", snapshot)
        print(json.dumps({"protected_files": len(snapshot["files"]), "source_commit": snapshot["source_commit"]}))
    elif args.check_protected:
        result = verify(root, json.loads((root / AUDIT / "protected_snapshot.json").read_text()))
        print(json.dumps(result))
        if result["errors"]:
            raise SystemExit(1)
    elif args.validate_code:
        destination = root / AUDIT / "code_validation_final"
        destination.mkdir(parents=True, exist_ok=False)
        rows = []
        for name, command in (
            ("ruff", ["-m", "ruff", "check", "."]),
            ("static", ["scripts/static_validate.py"]),
            ("suite", ["scripts/run_ci_tests.py"]),
            ("hardened_artifacts", ["scripts/validate_hardened_artifacts.py"]),
        ):
            with (destination / (name + ".stdout.log")).open("x") as out, (destination / (name + ".stderr.log")).open("x") as err:
                result = subprocess.run([sys.executable, *command], cwd=root, stdout=out, stderr=err)
            rows.append({"check": name, "command": [sys.executable, *command], "returncode": result.returncode,
                         "stdout_sha256": digest(destination / (name + ".stdout.log")), "stderr_sha256": digest(destination / (name + ".stderr.log"))})
            print(json.dumps(rows[-1]), flush=True)
        from publication.campaign_plan import source_identity
        receipt = {"checks": rows, "status": "passed" if all(row["returncode"] == 0 for row in rows) else "failed",
                   "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
                   "tested_source_checksums": source_identity(root), "new_final_inference": False,
                   "scope": "Existing unit/integration tests and explicitly permitted tiny scientific smoke tests, not final batches"}
        write_new(destination / "receipt.json", receipt)
        if receipt["status"] != "passed":
            raise SystemExit(1)
    elif args.audit_traces:
        from publication.complement_trace_review import review
        result = review(root)
        write_new(root / AUDIT / "complement_trace_review_final.json", result)
        print(json.dumps({"status": result["status"], "campaigns": {name: item["counts"] for name, item in result["campaigns"].items()}}))
    elif args.verify_original:
        from publication.evidence_archive import EvidenceWalker
        inventory = EvidenceWalker(root).build(["reports/publication_campaign/tcc_numerical_complement_v4/artifact_manifest.json"])
        print(json.dumps({"verified_files": inventory["file_count"], "original_reports_modified": False}))
    elif args.check:
        from publication.campaign_release import validate_synthesis
        print(json.dumps(validate_synthesis(root, args.output), indent=2))
    else:
        from publication.synthesis_v3 import build
        build(root, root / args.output)
        print(json.dumps({"output": args.output, "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(), "new_inference": False}))


if __name__ == "__main__":
    main()
