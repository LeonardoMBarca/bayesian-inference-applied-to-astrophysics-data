"""Record/verify an immutable local pre-remediation snapshot (no inference)."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / "publication/validation/external_audit_closure_v1/protected_snapshot.json"
CAMPAIGNS = ("tcc_campaign_v1", "tcc_calibration_confirmatory_v1")


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def collect(root: Path) -> dict:
    baseline = json.loads((root / "publication/baseline/manifest.json").read_text())
    expected = {r["path"]: r["sha256"] for r in
                baseline["artifacts"] + baseline["environment_lock_artifacts"]}
    paths = set(expected)
    trees = ["publication/baseline", "publication/protocols", "configs/publication",
             "publication/observational", "publication/experiments",
             "reports/publication_synthesis/tcc_evidence_v1"]
    counts = {}
    for campaign in CAMPAIGNS:
        report = f"reports/publication_campaign/{campaign}"
        trees += [report, f"artifacts/publication_campaign/{campaign}"]
        summary = json.loads((root / report / "campaign_summary.json").read_text())
        counts[campaign] = {key: summary[key] for key in
                            ("declared_jobs", "total_attempts", "status_counts")}
        for name, sha in summary["source_checksums"].items():
            if name.startswith(("artifacts/", "publication/observational/",
                                "publication/experiments/", "publication/protocols/")):
                if name in expected and expected[name] != sha:
                    raise ValueError(f"Conflicting historical checksum: {name}")
                expected[name] = sha
                paths.add(name)
    for tree in trees:
        paths.update(p.relative_to(root).as_posix() for p in (root / tree).rglob("*")
                     if p.is_file())

    def row(name):
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Unsafe protected path: {name}")
        sha = digest(path)
        if name in expected and sha != expected[name]:
            raise ValueError(f"Historical checksum mismatch: {name}")
        return {"path": name, "size_bytes": path.stat().st_size, "sha256": sha,
                "preexisting_manifest_checked": name in expected}

    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(row, sorted(paths)))
    return {"schema_version": "external-audit-protection-v1",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
            "campaign_counts": counts, "files": rows,
            "scope": "Historical scientific artifacts, protocols/seeds/config snapshots, both campaign reports, baseline and tcc_evidence_v1; no claim of remote availability"}


def verify(root: Path, snapshot: dict) -> dict:
    errors = []
    for row in snapshot["files"]:
        path = root / row["path"]
        if not path.is_file() or path.is_symlink():
            errors.append({"path": row["path"], "error": "missing_or_symlink"})
        elif path.stat().st_size != row["size_bytes"] or digest(path) != row["sha256"]:
            errors.append({"path": row["path"], "error": "bytes_changed"})
    return {"status": "passed" if not errors else "failed",
            "files_checked": len(snapshot["files"]), "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT)
    args = parser.parse_args()
    if args.check:
        result = verify(ROOT, json.loads(args.output.read_text()))
        print(json.dumps(result, indent=2))
        return int(result["status"] != "passed")
    if args.output.exists():
        raise FileExistsError("Protection snapshots must never be overwritten")
    snapshot = collect(ROOT)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(snapshot, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"snapshot": str(args.output), "files": len(snapshot["files"]),
                      "campaign_counts": snapshot["campaign_counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
