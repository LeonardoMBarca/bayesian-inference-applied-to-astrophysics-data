"""Audit immutable RAW payloads across worktree, Git blobs and real checkouts.

The current-state manifest remains the authority. This module never repairs a
payload, changes an expected checksum, or normalizes source data. Candidate
transformations only classify an observed mismatch when BOTH size and digest
reproduce the previously recorded identity.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import subprocess
import tempfile
from collections import Counter
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

MANIFEST = "data/raw/_manifests/raw_data_current_state.csv"
BYTE_POLICY = "data/raw/** -text -filter -ident -working-tree-encoding"


def plain_path(path: Path) -> Path:
    value = str(path)
    if value.startswith("\\\\?\\UNC\\"):
        return Path("\\\\" + value[8:])
    if value.startswith("\\\\?\\"):
        return Path(value[4:])
    return path


def filesystem_path(path: Path) -> Path:
    if os.name != "nt" or str(path).startswith("\\\\?\\"):
        return path
    if str(path).startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + str(path)[2:])
    return Path("\\\\?\\" + str(path))


def identity(payload: bytes | None) -> dict:
    if payload is None:
        return {"size_bytes": None, "sha256": None, "missing": True}
    return {
        "size_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "missing": False,
        "crlf_count": payload.count(b"\r\n"),
        "bare_lf_count": payload.count(b"\n") - payload.count(b"\r\n"),
        "utf8_bom": payload.startswith(b"\xef\xbb\xbf"),
    }


def matches(payload: bytes | None, expected: dict) -> bool:
    actual = identity(payload)
    return all(actual[key] == expected[key] for key in ("size_bytes", "sha256"))


def classify(payload: bytes | None, expected: dict, verified_original: bytes | None = None) -> str:
    """Name only transformations that exactly recover the frozen identity."""
    if payload is None:
        return "missing"
    if matches(payload, expected):
        return "exact"
    lf = payload.replace(b"\r\n", b"\n")
    candidates = {
        "LF_to_CRLF": lf.replace(b"\n", b"\r\n"),
        "CRLF_to_LF": lf,
        "remove_UTF8_BOM": payload.removeprefix(b"\xef\xbb\xbf"),
        "add_UTF8_BOM": b"\xef\xbb\xbf" + payload,
    }
    for label, candidate in candidates.items():
        if matches(candidate, expected):
            return label
    if (
        verified_original is not None and matches(verified_original, expected)
        and lf == verified_original.replace(b"\r\n", b"\n")
    ):
        return "mixed_line_endings_verified_original"
    for encoding in ("utf-16", "utf-16-le", "utf-16-be", "latin-1"):
        try:
            candidate = payload.decode(encoding).encode("utf-8")
        except (UnicodeError, LookupError):
            continue
        if matches(candidate, expected):
            return f"{encoding}_to_utf8"
    return "content_or_other_unresolved"


def safe_path(root: Path, relative: str) -> Path:
    root = filesystem_path(root.resolve())
    path = PurePosixPath(relative)
    if (
        path.is_absolute() or ".." in path.parts or "\\" in relative
        or ":" in relative or "\n" in relative or "\r" in relative
        or not relative.startswith("data/raw/")
    ):
        raise ValueError(f"Unsafe RAW path: {relative!r}")
    target = root / path
    if any(part.is_symlink() for part in (target, *target.parents) if part != root.parent):
        raise ValueError(f"Symlink is not immutable RAW payload: {relative}")
    plain_path(target.resolve()).relative_to(plain_path(root.resolve()))
    # Some Windows Python builds still need extended-length paths; treating a
    # MAX_PATH access failure as a missing astronomical input is misleading.
    return target


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(plain_path(root)), *args], check=True, capture_output=True,
    ).stdout


@contextmanager
def git_blob_reader(root: Path):
    """One Git process, avoiding hundreds of platform-dependent startups."""
    process = subprocess.Popen(
        ["git", "-C", str(root), "cat-file", "--batch"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert process.stdin is not None and process.stdout is not None

    def read(spec: str) -> bytes | None:
        if "\n" in spec or "\r" in spec:
            raise ValueError("Git object specification contains a newline")
        process.stdin.write(spec.encode("utf-8") + b"\n")
        process.stdin.flush()
        header = process.stdout.readline().split()
        if len(header) == 2 and header[1] == b"missing":
            return None
        if len(header) != 3 or header[1] != b"blob":
            raise ValueError(f"Not a Git blob: {spec}")
        data = process.stdout.read(int(header[2]))
        if process.stdout.read(1) != b"\n":
            raise RuntimeError("Malformed Git batch response")
        return data

    try:
        yield read
    finally:
        process.stdin.close()
        process.stdout.close()
        assert process.stderr is not None
        error = process.stderr.read()
        process.stderr.close()
        if process.wait() != 0:
            raise RuntimeError(f"Git batch failed: {error.decode(errors='replace')}")


def manifest_rows(payload: bytes) -> list[dict]:
    rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))))
    paths = [row["local_path"] for row in rows]
    if len(set(paths)) != len(paths):
        raise ValueError("Duplicate current-state RAW paths")
    for row in rows:
        digest = row["sha256"]
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise ValueError("Invalid expected RAW checksum")
        if int(row["file_size_bytes"]) < 0:
            raise ValueError("Invalid expected RAW size")
    return rows


def materialize_checkout(source: Path, destination: Path, commit: str, autocrlf: bool) -> None:
    """Real sparse Git checkout; shared objects, never source worktree copies."""
    if destination.exists():
        raise FileExistsError(destination)
    git(source, "clone", "--shared", "--no-checkout", "--local", str(plain_path(source)), str(plain_path(destination)))
    git(destination, "config", "core.autocrlf", str(autocrlf).lower())
    git(destination, "config", "core.safecrlf", "false")
    git(destination, "config", "core.longpaths", "true")
    git(destination, "sparse-checkout", "set", "data/raw")
    git(destination, "checkout", "--detach", commit)


def audit(root: Path, revision: str = "HEAD", checkouts: dict[str, Path] | None = None) -> dict:
    root = root.resolve()
    commit = git(root, "rev-parse", "--verify", f"{revision}^{{commit}}").decode().strip()
    records = []
    with git_blob_reader(root) as blob:
        committed_manifest = blob(f"{commit}:{MANIFEST}")
        if committed_manifest is None:
            raise ValueError("RAW current-state manifest is not committed")
        local_manifest = (root / MANIFEST).read_bytes()
        rows = manifest_rows(committed_manifest)
        if manifest_rows(local_manifest) != rows:
            raise ValueError("Local manifest fields differ from the selected Git revision")
        for row in rows:
            relative = row["local_path"]
            path = safe_path(root, relative)
            expected = {"sha256": row["sha256"], "size_bytes": int(row["file_size_bytes"])}
            surfaces = {
                "worktree": path.read_bytes() if path.is_file() else None,
                "git_blob": blob(f"{commit}:{relative}"),
            }
            for name, checkout in (checkouts or {}).items():
                candidate = safe_path(checkout, relative)
                surfaces[name] = candidate.read_bytes() if candidate.is_file() else None
            records.append({
                "path": relative, "expected": expected,
                "surfaces": {name: {**identity(data), "classification": classify(data, expected, surfaces["worktree"])}
                             for name, data in surfaces.items()},
            })
    counts = {
        name: dict(Counter(row["surfaces"][name]["classification"] for row in records))
        for name in (records[0]["surfaces"] if records else {})
    }
    return {
        "schema_version": 1, "audit_version": "raw-git-byte-audit-v1",
        "commit": commit, "manifest": MANIFEST,
        "manifest_worktree_identity": identity(local_manifest),
        "manifest_git_identity": identity(committed_manifest),
        "manifest_fields_identical": True, "raw_files": len(records),
        "counts_by_surface": counts,
        "passed": all(set(count) <= {"exact"} for count in counts.values()),
        "checkout_method": (
            "isolated sparse Git clones; shared read-only object store; no worktree payload copies"
            if checkouts else "not requested"
        ),
        "records": records,
    }


def run_audit(root: Path, revision: str, real_checkouts: bool) -> dict:
    if not real_checkouts:
        return audit(root, revision)
    commit = git(root, "rev-parse", "--verify", f"{revision}^{{commit}}").decode().strip()
    temporary_parent = filesystem_path(Path(tempfile.gettempdir()).resolve())
    with tempfile.TemporaryDirectory(prefix="raw-byte-checkout-", dir=str(temporary_parent)) as temporary:
        checkouts = {}
        for setting in (False, True):
            name = f"checkout_autocrlf_{str(setting).lower()}"
            destination = Path(temporary) / name
            materialize_checkout(root, destination, commit, setting)
            checkouts[name] = destination
        return audit(root, commit, checkouts)


def write_report(path: Path, result: dict) -> None:
    """Evidence reports cannot silently overwrite an earlier audit."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
