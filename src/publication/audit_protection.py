"""Record/verify an immutable local pre-remediation snapshot (no inference)."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from publication.evidence_archive import SCHEMA as INVENTORY_SCHEMA
from publication.evidence_archive import digest_json

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / "publication/validation/external_audit_closure_v1/protected_snapshot.json"
DEFAULT_INVENTORY = ROOT / "publication/validation/external_audit_closure_v1/transitive_inventory_final.json"
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
    root = root.resolve()
    checked_parents = {}
    for row in snapshot["files"]:
        name = row["path"]
        logical = PurePosixPath(name)
        if (not name or "\\" in name or ":" in name or logical.is_absolute()
                or any(part in {"", ".", ".."} for part in name.split("/"))):
            errors.append({"path": name, "error": "unsafe_path"})
            continue
        path = root / logical
        if path.parent not in checked_parents:
            checked_parents[path.parent] = (
                path.parent.resolve().is_relative_to(root)
                and not any(parent.is_symlink() for parent in path.parents if parent.is_relative_to(root))
            )
        if not checked_parents[path.parent]:
            errors.append({"path": name, "error": "unsafe_parent"})
            continue
        if not path.is_file() or path.is_symlink():
            errors.append({"path": row["path"], "error": "missing_or_symlink"})
        elif path.stat().st_size != row["size_bytes"] or digest(path) != row["sha256"]:
            errors.append({"path": row["path"], "error": "bytes_changed"})
    return {"status": "passed" if not errors else "failed",
            "files_checked": len(snapshot["files"]), "errors": errors}


def verify_portable(root: Path, snapshot: dict, inventory: dict,
                    tracked_paths: set[str]) -> dict:
    """Verify Git bytes and bind intentionally external files to a sealed inventory.

    This mode does not claim that the external ZIP is available in CI. A full
    ``--check`` is still required after independently restoring that ZIP.
    """
    payload = dict(inventory)
    checksum = payload.pop("inventory_content_sha256", None)
    if payload.get("schema_version") != INVENTORY_SCHEMA or checksum != digest_json(payload):
        return {"status": "failed", "errors": [{"error": "inventory_identity_mismatch"}]}
    indexed = {(row["path"], row["sha256"]): row for row in payload["files"]}
    if len(indexed) != len(payload["files"]):
        return {"status": "failed", "errors": [{"error": "duplicate_inventory_identity"}]}
    committed = [row for row in snapshot["files"] if row["path"] in tracked_paths]
    external = [row for row in snapshot["files"] if row["path"] not in tracked_paths]
    result = verify(root, {"files": committed})
    errors = result["errors"]
    for row in external:
        name = row["path"]
        logical = PurePosixPath(name)
        if (not name or "\\" in name or ":" in name or logical.is_absolute()
                or any(part in {"", ".", ".."} for part in name.split("/"))):
            errors.append({"path": name, "error": "unsafe_path"})
            continue
        binding = indexed.get((name, row["sha256"]))
        if (binding is None or binding.get("storage") != "local_external_bundle"
                or binding.get("sha256") != row["sha256"]
                or binding.get("size_bytes") != row["size_bytes"]):
            errors.append({"path": name, "error": "external_inventory_mismatch"})
            continue
        path = root / logical
        if path.exists() and (path.is_symlink() or not path.is_file()
                              or not path.resolve().is_relative_to(root.resolve())
                              or path.stat().st_size != row["size_bytes"]
                              or digest(path) != row["sha256"]):
            errors.append({"path": name, "error": "external_bytes_changed"})
    return {"status": "passed" if not errors else "failed",
            "protected_files": len(snapshot["files"]),
            "git_bytes_checked": len(committed),
            "external_inventory_bound": len(external),
            "external_bundle_bytes_checked": 0,
            "scope": "Git bytes plus sealed external references; run full --check after bundle restore",
            "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--check-portable", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    args = parser.parse_args()
    if args.check_portable:
        tracked = set(subprocess.check_output(
            ["git", "ls-files", "-z"], cwd=ROOT).decode("utf-8").split("\0"))
        result = verify_portable(ROOT, json.loads(args.output.read_text()),
                                 json.loads(args.inventory.read_text()), tracked)
        print(json.dumps(result, indent=2))
        return int(result["status"] != "passed")
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
