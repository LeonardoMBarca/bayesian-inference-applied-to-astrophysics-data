"""Lightweight version/lock guards run inside the actual inference interpreter."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
from pathlib import Path
from typing import Callable


def parse_exact_requirements(text: str) -> dict[str, str]:
    expected = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+!-]+)", line)
        if not match or match.group(1).lower() in {name.lower() for name in expected}:
            raise ValueError(f"Not a unique exact requirement: {line!r}")
        expected[match.group(1)] = match.group(2)
    if not expected:
        raise ValueError("Empty scientific requirements lock")
    return expected


def inspect_scientific_environment(root: Path, *, python_version: str | None = None,
                                   version_lookup: Callable[[str], str] = importlib.metadata.version) -> dict:
    """Compare actual interpreter metadata to protected baseline pins, not PATH."""
    root = root.resolve()
    manifest_path = root / "publication/baseline/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    declared_hash = manifest.pop("manifest_content_sha256")
    content = json.dumps(manifest, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    if hashlib.sha256(content).hexdigest() != declared_hash:
        raise ValueError("Baseline environment manifest content hash mismatch")
    relative = "publication/baseline/environment/requirements.txt"
    artifact = next(item for item in manifest["environment_lock_artifacts"] if item["path"] == relative)
    lock = (root / relative).read_bytes()
    if hashlib.sha256(lock).hexdigest() != artifact["sha256"]:
        raise ValueError("Protected requirements snapshot checksum mismatch")
    required = parse_exact_requirements(lock.decode("utf-8"))
    expected_python = manifest["environment"]["python_version"]
    actual_python = python_version or platform.python_version()
    errors = [] if actual_python == expected_python else [f"Python {actual_python} != locked {expected_python}"]
    packages = {}
    for name, expected in required.items():
        try:
            actual = version_lookup(name)
        except importlib.metadata.PackageNotFoundError:
            actual = None
        packages[name] = {"expected": expected, "actual": actual, "matched": actual == expected}
        if actual != expected:
            errors.append(f"{name}: installed {actual!r} != locked {expected!r}")
    return {"schema_version": "scientific-environment-preflight-v1", "passed": not errors,
            "python_expected": expected_python, "python_actual": actual_python,
            "platform": platform.platform(), "packages": packages, "errors": errors,
            "requirements_sha256": artifact["sha256"], "baseline_manifest_content_sha256": declared_hash,
            "limitations": "Exact direct pinned distributions and Python version; not a proof of bit-identical native libraries, compiler or complete transitive environment. Package code integrity requires separately frozen source/environment artifacts."}


def require_scientific_environment(root: Path) -> dict:
    result = inspect_scientific_environment(root)
    if not result["passed"]:
        raise ValueError("Scientific environment mismatch: " + "; ".join(result["errors"]))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    result = inspect_scientific_environment(args.root)
    print(json.dumps(result, indent=2, allow_nan=False))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
