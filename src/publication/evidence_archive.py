"""Schema-aware, byte-preserving local evidence archive (no inference/network).

Only declared reference fields are traversed. Historical source-code references
may resolve to an exact Git blob; scientific input/result bytes never do. This
is an availability/integrity audit, not a scientific-success or release gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from repository_tools.raw_byte_audit import filesystem_path, plain_path

SCHEMA = "publication-transitive-evidence-v1"
PIPELINE_MANIFESTS = {
    "gold": "data/gold/manifests/gold_data_manifest.json",
    "silver": "data/silver/manifests/silver_data_manifest.json",
    "raw": "data/raw/_manifests/raw_data_current_state.json",
}


def digest_file(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def digest_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_new(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")


def safe_file(root: Path, relative: str, *, resolved_root: bool = False) -> Path:
    """Reject lexical traversal and every symlink component, also inside root."""
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise ValueError(f"Unsafe evidence path: {relative!r}")
    parsed = PurePosixPath(relative)
    if (parsed.is_absolute() or any(part.lower() in {"..", ".git"} or part.endswith((" ", ".")) for part in parsed.parts)
            or str(parsed) != relative):
        raise ValueError(f"Unsafe evidence path: {relative!r}")
    root = plain_path(root) if resolved_root else plain_path(root).resolve()
    current = root
    for part in parsed.parts:
        current /= part
        native = filesystem_path(current)
        if native.is_symlink() or (hasattr(native, "is_junction") and native.is_junction()):
            raise ValueError(f"Symlink evidence is not supported: {relative}")
    # Lexical traversal is forbidden and each appended component was checked
    # for symlinks/junctions; resolving the full prefix again is unnecessary.
    return filesystem_path(current)


def _git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE)


def _historical_allowed(path: str) -> bool:
    return path.startswith(("src/", "scripts/", "docs/", ".agents/")) or path == "publication/registry.json"


class EvidenceWalker:
    """An explicit reference graph with cycle/conflict detection and byte checks."""

    def __init__(self, root: Path, *, snapshot_commit: str = "HEAD"):
        self.root = root.resolve()
        self.commit = _git(root, "rev-parse", snapshot_commit).decode().strip()
        self.tracked = set(_git(root, "ls-files", "-z").decode().split("\0"))
        self.rows: dict[tuple[str, str], dict] = {}
        self.edges: set[tuple[str, str, str]] = set()
        self.active: set[tuple[str, str]] = set()
        self.finished: set[tuple[str, str]] = set()
        self.root_paths: list[str] = []
        self.pipeline: dict[str, tuple[str, dict]] = {}
        self._hashes: dict[str, str] = {}
        self._histories: dict[str, list[str]] = {}
        for layer, relative in PIPELINE_MANIFESTS.items():
            path = safe_file(self.root, relative)
            if not path.exists():
                continue
            key = {"raw": "local_path", "silver": "silver_file_path", "gold": "gold_file_path"}[layer]
            for entry in read_json(path):
                name = entry.get(key)
                if not name or not entry.get("sha256"):
                    continue
                if name in self.pipeline and self.pipeline[name][1]["sha256"] != entry["sha256"]:
                    raise ValueError(f"Conflicting pipeline manifest hashes: {name}")
                self.pipeline[name] = (relative, entry)

    def _local_hash(self, name: str) -> str:
        if name not in self._hashes:
            self._hashes[name] = digest_file(safe_file(self.root, name, resolved_root=True))
        return self._hashes[name]

    def _historical(self, name: str, expected: str, commit: str | None) -> tuple[bytes, str, str]:
        if not _historical_allowed(name):
            raise ValueError(f"Scientific artifact checksum mismatch: {name}")
        if name not in self._histories:
            self._histories[name] = _git(self.root, "log", "--format=%H", self.commit, "--", name).decode().splitlines()
        candidates = list(dict.fromkeys([commit, self.commit, *self._histories[name]]))
        for candidate in candidates:
            if not candidate:
                continue
            try:
                _git(self.root, "merge-base", "--is-ancestor", candidate, self.commit)
                content = _git(self.root, "show", f"{candidate}:{name}")
            except subprocess.CalledProcessError:
                continue
            if hashlib.sha256(content).hexdigest() == expected:
                blob = _git(self.root, "rev-parse", f"{candidate}:{name}").decode().strip()
                return content, candidate, blob
        raise ValueError(f"No exact historical Git blob for {name}: {expected}")

    def add(self, name: str, expected: str | None = None, *, parent: str = "ROOT", role: str = "declared_reference",
            size: int | None = None, commit: str | None = None) -> None:
        # A reference already checked within this audit is not rehashed for each
        # parent edge. Bundle/restore verification performs a fresh byte pass.
        key = (name, expected)
        if expected is not None and key in self.finished:
            self.edges.add((parent, name, role))
            if size is not None and self.rows[key]["size_bytes"] != size:
                raise ValueError(f"Conflicting size: {name}")
            return
        path = safe_file(self.root, name, resolved_root=True)
        if expected is not None and re.fullmatch(r"[a-f0-9]{64}", expected) is None:
            raise ValueError(f"Invalid SHA-256: {name}")
        if not path.is_file():
            raise FileNotFoundError(f"Missing evidence: {name}")
        actual = self._local_hash(name)
        expected = expected or actual
        key = (name, expected)
        self.edges.add((parent, name, role))
        if key in self.active:
            raise ValueError(f"Cyclic evidence reference: {name}")
        if key in self.finished:
            if size is not None and self.rows[key]["size_bytes"] != size:
                raise ValueError(f"Conflicting size: {name}")
            return
        if any(other[0] == name and other[1] != expected for other in self.rows) and not _historical_allowed(name):
            raise ValueError(f"Conflicting evidence hashes: {name}")
        resolution = "working_tree_bytes"
        historical = None
        content = None
        if actual != expected:
            content, resolved_commit, blob = self._historical(name, expected, commit)
            historical = {"commit": resolved_commit, "blob": blob,
                          "meaning": "Exact recorded source bytes located in Git; not an assertion that this location commit executed the run."}
            resolution = "historical_git_blob"
        length = len(content) if content is not None else path.stat().st_size
        if size is not None and length != size:
            raise ValueError(f"Evidence size mismatch: {name}")
        row = {"path": name, "sha256": expected, "size_bytes": length,
               "storage": "git" if name in self.tracked else "local_external_bundle",
               "resolution": resolution, "historical_git": historical,
               "binding": "historical_recorded_checksum" if role != "new_audit_discovery" else "first_bound_by_this_audit"}
        self.rows[key] = row
        self.active.add(key)
        if name.endswith(".json"):
            data = json.loads(content.decode("utf-8")) if content is not None else read_json(path)
            self._follow(name, data)
        self._pipeline_follow(name)
        self.active.remove(key)
        self.finished.add(key)

    def _mapping(self, parent: str, mapping: dict, base: str = "", *, commit: str | None = None) -> None:
        for relative, checksum in mapping.items():
            parsed = PurePosixPath(relative)
            if (not relative or str(parsed) != relative or parsed.is_absolute()
                    or ".." in parsed.parts or ".git" in parsed.parts or "\\" in relative or ":" in relative):
                raise ValueError("Reference escapes its narrower artifact namespace")
            name = f"{base}/{relative}" if base else relative
            self.add(name, checksum, parent=parent, commit=commit)

    def _pipeline_follow(self, name: str) -> None:
        if name not in self.pipeline:
            return
        manifest, row = self.pipeline[name]
        # The manifest itself is a leaf table; follow only the matched row.
        self.add(manifest, parent=name, role="new_audit_discovery")
        if row["sha256"] != self._local_hash(name):
            raise ValueError(f"Pipeline identity mismatch: {name}")
        for field in ("source_silver_path", "source_raw_path", "source_raw_manifest_path"):
            for source in filter(None, row.get(field, "").split("|")):
                if source == name:
                    raise ValueError(f"Self-referencing pipeline artifact: {name}")
                source_row = self.pipeline.get(source)
                self.add(source, source_row[1]["sha256"] if source_row else None,
                         parent=name, role="pipeline_dependency" if source_row else "new_audit_discovery")

    def _follow(self, name: str, data: Any) -> None:
        if not isinstance(data, dict):
            return
        schema = data.get("schema_version", "")
        base = str(PurePosixPath(name).parent)
        commit = data.get("code_commit") or data.get("campaign_initial_code_commit")
        # Recognized report manifests, not arbitrary dictionaries with paths.
        if PurePosixPath(name).name.endswith("artifact_manifest.json"):
            if (schema not in {"publication-derived-v1", "publication-post-campaign-synthesis-v1", "tcc-evidence-v2",
                               "independent-posterior-trace-audit-v1"}
                    or not isinstance(data.get("artifacts"), dict) or not isinstance(data.get("source_checksums"), dict)):
                raise ValueError(f"Unsupported artifact manifest schema: {name}")
            self._mapping(name, data["artifacts"], base)
            self._mapping(name, data["source_checksums"], commit=commit)
        elif name.endswith("/completion_manifest.json"):
            if data.get("status") not in {"COMPLETED", "COMPLETED_REJECTED", "FAILED_TECHNICAL"}:
                raise ValueError(f"Unsupported completion status: {name}")
            self._mapping(name, data["artifacts"], base)
        elif schema == "publication-observational-v1":
            output = data["output_directory"]
            self._mapping(name, data["artifacts"], output)
            acquisition_roots = {str(PurePosixPath(ref["path"]).parent) for ref in data["source_artifacts"]
                                 if ref["path"].startswith("publication/inputs/raw/")}
            for directory in sorted(acquisition_roots):
                self.add(directory + "/acquisition_manifest.json", parent=name, role="new_audit_discovery")
            for ref in data["source_artifacts"]:
                self.add(ref["path"], ref["sha256"], parent=name)
            if data.get("preparation_manifest_path"):
                ref = data["input_validation"]
                self.add(ref["preparation_manifest_path"], ref["preparation_manifest_sha256"], parent=name)
        elif schema == "publication-raw-acquisition-v1":
            self.add(data["selection_path"], data["selection_file_sha256"], parent=name, commit=data["selection_commit"])
            for ref in data["files"]:
                self.add(ref["path"], ref["sha256"], size=ref["size_bytes"], parent=name)
        elif schema == "publication-baseline-v1":
            for ref in data["artifacts"] + data["environment_lock_artifacts"]:
                self.add(ref["path"], ref["sha256"], size=ref.get("size_bytes"), parent=name)
        elif name.endswith("/campaign_summary.json"):
            self._mapping(name, data["source_checksums"], commit=commit)
            for attempt in data["attempts"]:
                directory = attempt["output_dir"]
                for log_field in ("stdout_log", "stderr_log"):
                    if attempt.get(log_field):
                        self.add(attempt[log_field], parent=name, role="new_audit_discovery")
                checksum = attempt.get("completion_manifest_sha256")
                if checksum:
                    self.add(directory + "/completion_manifest.json", checksum, parent=name)
                else:
                    # Registry-declared cancelled/failed directory, never inferred from arbitrary JSON strings.
                    for path in sorted(safe_file(self.root, directory).rglob("*")):
                        relative = plain_path(path).relative_to(self.root).as_posix()
                        safe_file(self.root, relative)
                        if path.is_file():
                            self.add(relative, parent=name, role="new_audit_discovery")
        elif name.startswith("configs/publication/") and name.endswith("_plan.json"):
            self._mapping(name, data["source_checksums"], commit=commit)
            for ref in data["protocols"].values():
                self.add(ref["path"], ref["sha256"], parent=name, commit=ref.get("commit"))
        elif schema == "publication-registry-v1":
            for campaign in data.get("campaign_registries", []):
                for field in ("config", "frozen_declaration", "execution_state", "final_report"):
                    self.add(campaign[field], parent=name, role="new_audit_discovery")
                report_dir = str(PurePosixPath(campaign["final_report"]).parent)
                self.add(report_dir + "/artifact_manifest.json", parent=name, role="new_audit_discovery")
                self.add(report_dir + "/campaign_summary.json", parent=name, role="new_audit_discovery")

    def build(self, roots: list[str]) -> dict:
        for relative in roots:
            self.root_paths.append(relative)
            self.add(relative, role="new_audit_discovery")
        files = sorted(self.rows.values(), key=lambda row: (row["path"], row["sha256"]))
        payload = {"schema_version": SCHEMA, "snapshot_commit": self.commit, "roots": roots,
                   "files": files, "edges": [dict(parent=p, child=c, role=r) for p, c, r in sorted(self.edges)],
                   "file_count": len(files), "total_bytes": sum(row["size_bytes"] for row in files),
                   "external_file_count": sum(row["storage"] == "local_external_bundle" for row in files),
                   "external_bytes": sum(row["size_bytes"] for row in files if row["storage"] == "local_external_bundle"),
                   "semantics": "Exact byte availability and transitive declared-schema dependencies; no numeric reproduction or scientific-success claim.",
                   "public_archive": None, "release_approved": False}
        payload["inventory_content_sha256"] = digest_json(payload)
        return payload


def verify_inventory(root: Path, inventory: dict) -> dict:
    root = root.resolve()
    payload = dict(inventory)
    digest = payload.pop("inventory_content_sha256")
    if payload.get("schema_version") != SCHEMA or digest_json(payload) != digest:
        raise ValueError("Inventory identity mismatch")
    seen = set()
    resolutions = []
    for row in payload["files"]:
        identity = row["path"], row["sha256"]
        if identity in seen:
            raise ValueError("Duplicate inventory identity")
        seen.add(identity)
        if row["resolution"] == "historical_git_blob":
            ref = row["historical_git"]
            content = _git(root, "show", f"{ref['commit']}:{row['path']}")
            actual, length = hashlib.sha256(content).hexdigest(), len(content)
            if _git(root, "rev-parse", f"{ref['commit']}:{row['path']}").decode().strip() != ref["blob"]:
                raise ValueError("Historical Git blob changed")
        else:
            path = safe_file(root, row["path"], resolved_root=True)
            actual, length = digest_file(path), path.stat().st_size
            if actual != row["sha256"] and _historical_allowed(row["path"]):
                # The inventory is an immutable snapshot; later review-source
                # edits must not invalidate preserved original source bytes.
                commit = payload["snapshot_commit"]
                content = _git(root, "show", f"{commit}:{row['path']}")
                actual, length = hashlib.sha256(content).hexdigest(), len(content)
                resolutions.append({"path": row["path"], "resolution": "historical_git_blob",
                                    "commit": commit, "blob": _git(root, "rev-parse", f"{commit}:{row['path']}").decode().strip()})
        if actual != row["sha256"] or length != row["size_bytes"]:
            raise ValueError(f"Inventory evidence mismatch: {row['path']}")
    return {"status": "passed", "checked_files": len(seen), "checked_bytes": payload["total_bytes"],
            "inventory_content_sha256": digest, "mcmc_executed": False,
            "historical_source_resolutions": resolutions,
            "scope": "Exact byte availability only; not inference re-execution, table regeneration, or public release approval."}


def bundle_external(root: Path, inventory: dict, destination: Path) -> dict:
    verify_inventory(root, inventory)
    destination.parent.mkdir(parents=True, exist_ok=True)
    selected = [row for row in inventory["files"] if row["storage"] == "local_external_bundle"]
    # No extractall on restoration; members are individually checked and streamed.
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as bundle:
        for row in selected:
            bundle.write(safe_file(root, row["path"]), row["path"])
    return {"schema_version": "publication-local-bundle-v1", "bundle_id": digest_file(destination),
            "bundle_sha256": digest_file(destination), "bundle_size_bytes": destination.stat().st_size,
            "inventory_content_sha256": inventory["inventory_content_sha256"], "members": selected,
            "member_count": len(selected), "storage": "local_only", "public_archive": None,
            "restore_command": "python scripts/publication_evidence_archive.py restore --inventory INVENTORY.json --bundle BUNDLE.zip --bundle-manifest BUNDLE_MANIFEST.json --root INDEPENDENT_CHECKOUT"}


def rebind_existing_bundle(inventory: dict, archive: Path) -> dict:
    """Bind an existing ZIP to a revised graph only after checking every member.

    The new inventory may add Git-provided dependencies without changing the
    archive members. This operation neither extracts nor rewrites the ZIP.
    """
    payload = dict(inventory)
    expected_digest = payload.pop("inventory_content_sha256")
    if payload.get("schema_version") != SCHEMA or digest_json(payload) != expected_digest:
        raise ValueError("Inventory identity mismatch before bundle binding")
    selected = [row for row in inventory["files"] if row["storage"] == "local_external_bundle"]
    expected = {row["path"]: row for row in selected}
    if len(expected) != len(selected):
        raise ValueError("Duplicate external logical path")
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if len(names) != len(set(names)) or set(names) != set(expected):
            raise ValueError("Existing ZIP membership differs from revised inventory")
        for info in bundle.infolist():
            safe_file(Path.cwd(), info.filename)
            row = expected[info.filename]
            if info.file_size != row["size_bytes"] or ((info.external_attr >> 16) & 0o170000) == 0o120000:
                raise ValueError(f"Existing ZIP member size/type mismatch: {info.filename}")
            digest = hashlib.sha256()
            with bundle.open(info) as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != row["sha256"]:
                raise ValueError(f"Existing ZIP member checksum mismatch: {info.filename}")
    archive_hash = digest_file(archive)
    return {"schema_version": "publication-local-bundle-v1", "bundle_id": archive_hash,
            "bundle_sha256": archive_hash, "bundle_size_bytes": archive.stat().st_size,
            "inventory_content_sha256": inventory["inventory_content_sha256"], "members": selected,
            "member_count": len(selected), "storage": "local_only", "public_archive": None,
            "restore_command": "python scripts/publication_evidence_archive.py restore --inventory INVENTORY.json --bundle BUNDLE.zip --bundle-manifest BUNDLE_MANIFEST.json --root INDEPENDENT_CHECKOUT",
            "rebound_existing_zip_after_full_member_verification": True}


def audit_checkout_transport(root: Path, inventory: dict) -> dict:
    """Inventory ALL Git-provided mismatches, without repairing or rehashing authority."""
    rows = []
    checked = 0
    root = root.resolve()
    for row in inventory["files"]:
        if row["storage"] != "git" or row["resolution"] == "historical_git_blob":
            continue
        checked += 1
        path = safe_file(root, row["path"], resolved_root=True)
        if not path.is_file():
            rows.append({"path": row["path"], "classification": "missing", "expected_sha256": row["sha256"]})
            continue
        actual = digest_file(path)
        if actual == row["sha256"]:
            continue
        content = path.read_bytes()
        normalized = content.replace(b"\r\n", b"\n")
        eol_only = hashlib.sha256(normalized).hexdigest() == row["sha256"] and len(normalized) == row["size_bytes"]
        rows.append({"path": row["path"], "classification": "checkout_CRLF_to_frozen_LF" if eol_only else "other_content_or_source_revision",
                     "expected_sha256": row["sha256"], "actual_sha256": actual,
                     "expected_size_bytes": row["size_bytes"], "actual_size_bytes": len(content)})
    return {"schema_version": "publication-checkout-transport-v1", "commit": _git(root, "rev-parse", "HEAD").decode().strip(),
            "checked_git_files": checked, "mismatches": rows, "mismatch_count": len(rows),
            "source_of_expected_identity": inventory["inventory_content_sha256"], "repair_performed": False}


def restore_bundle(root: Path, inventory: dict, archive: Path, manifest: dict) -> dict:
    inventory_payload = dict(inventory)
    expected_inventory_hash = inventory_payload.pop("inventory_content_sha256")
    if inventory_payload.get("schema_version") != SCHEMA or digest_json(inventory_payload) != expected_inventory_hash:
        raise ValueError("Inventory identity mismatch before restoration")
    if digest_file(archive) != manifest["bundle_sha256"] or archive.stat().st_size != manifest["bundle_size_bytes"]:
        raise ValueError("External bundle identity mismatch")
    if manifest["inventory_content_sha256"] != inventory["inventory_content_sha256"]:
        raise ValueError("Bundle belongs to another inventory")
    expected = {row["path"]: row for row in inventory["files"] if row["storage"] == "local_external_bundle"}
    if manifest["members"] != [row for row in inventory["files"] if row["storage"] == "local_external_bundle"]:
        raise ValueError("Bundle member manifest differs from inventory")
    restored, already_present = 0, 0
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if len(names) != len(set(names)) or set(names) != set(expected):
            raise ValueError("Unexpected/missing/duplicate archive member")
        for info in bundle.infolist():
            path = safe_file(root, info.filename)
            row = expected[info.filename]
            if info.file_size != row["size_bytes"] or ((info.external_attr >> 16) & 0o170000) == 0o120000:
                raise ValueError("Archive member size/type mismatch")
            if path.exists():
                if not path.is_file() or digest_file(path) != row["sha256"]:
                    raise ValueError(f"Refuse to overwrite existing evidence: {row['path']}")
                already_present += 1
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_name(path.name + ".restoring")
            with bundle.open(info) as source, temporary.open("xb") as target:
                shutil.copyfileobj(source, target, 1024 * 1024)
            if digest_file(temporary) != row["sha256"]:
                raise ValueError(f"Restored member checksum mismatch: {row['path']}")
            # Exclusive destination creation prevents races from overwriting another run.
            with temporary.open("rb") as source, path.open("xb") as target:
                shutil.copyfileobj(source, target, 1024 * 1024)
            temporary.unlink()
            restored += 1
    return {**verify_inventory(root, inventory), "restored_files": restored, "already_present_files": already_present,
            "bundle_sha256": manifest["bundle_sha256"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("inventory", "verify", "bundle", "rebind-bundle", "restore", "checkout-audit"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--snapshot-commit", default="HEAD")
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--bundle-manifest", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    if args.action == "inventory":
        roots = ["publication/registry.json", "publication/baseline/manifest.json",
                 "reports/publication_synthesis/tcc_evidence_v1/artifact_manifest.json"]
        report = EvidenceWalker(args.root, snapshot_commit=args.snapshot_commit).build(roots)
        write_new(args.inventory, report)
        print(json.dumps({key: report[key] for key in ("file_count", "total_bytes", "external_file_count", "external_bytes")}, indent=2))
        return
    inventory = read_json(args.inventory)
    if args.action == "checkout-audit":
        report = audit_checkout_transport(args.root, inventory)
    elif args.action == "verify":
        report = verify_inventory(args.root, inventory)
    elif args.action == "bundle":
        if args.bundle is None or args.bundle_manifest is None:
            parser.error("bundle requires --bundle and --bundle-manifest")
        report = bundle_external(args.root, inventory, args.bundle)
        write_new(args.bundle_manifest, report)
        print(json.dumps({"bundle_sha256": report["bundle_sha256"], "member_count": report["member_count"]}, indent=2))
        return
    elif args.action == "rebind-bundle":
        if args.bundle is None or args.bundle_manifest is None:
            parser.error("rebind-bundle requires --bundle and --bundle-manifest")
        report = rebind_existing_bundle(inventory, args.bundle)
        write_new(args.bundle_manifest, report)
        print(json.dumps({"bundle_sha256": report["bundle_sha256"], "member_count": report["member_count"],
                          "inventory_content_sha256": report["inventory_content_sha256"]}, indent=2))
        return
    else:
        if args.bundle is None or args.bundle_manifest is None:
            parser.error("restore requires --bundle and --bundle-manifest")
        report = restore_bundle(args.root, inventory, args.bundle, read_json(args.bundle_manifest))
    if args.receipt:
        write_new(args.receipt, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
