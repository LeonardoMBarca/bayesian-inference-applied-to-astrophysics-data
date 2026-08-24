"""Rebuild Silver/Gold from versioned RAW in an isolated temporary workspace."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bayesian_modeling.physical_transit import (  # noqa: E402
    build_paths,
    ensure_directories,
    prepare_modeling_input,
    read_gold_transit_window,
    sha256_file,
)
from project_config import TARGETS  # noqa: E402


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(sha256_file(path).encode("ascii"))
    return digest.hexdigest()


def run(command: list[str], root: Path) -> dict[str, object]:
    started = time.monotonic()
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    completed = subprocess.run(
        command,
        cwd=root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Clean rebuild failed ({completed.returncode}): {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return {
        "command": command,
        "returncode": completed.returncode,
        "elapsed_seconds": time.monotonic() - started,
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }


def main() -> None:
    current_metadata = {
        target.planet_slug: json.loads(
            (
                PROJECT_ROOT
                / "data"
                / "gold"
                / target.planet_slug
                / "modeling"
                / "dataset_metadata.json"
            ).read_text(encoding="utf-8")
        )
        for target in TARGETS
    }
    raw_digest = tree_digest(PROJECT_ROOT / "data" / "raw")
    with tempfile.TemporaryDirectory(prefix="astro-clean-rebuild-") as directory:
        clean_root = Path(directory)
        shutil.copytree(PROJECT_ROOT / "src", clean_root / "src")
        shutil.copytree(PROJECT_ROOT / "scripts", clean_root / "scripts")
        shutil.copytree(PROJECT_ROOT / "data" / "raw", clean_root / "data" / "raw")
        if (clean_root / "data" / "silver").exists() or (
            clean_root / "data" / "gold"
        ).exists():
            raise AssertionError("Clean workspace unexpectedly contains derived data")
        commands = [
            run([sys.executable, "scripts/build_silver_data.py"], clean_root),
            run([sys.executable, "scripts/build_gold_data.py"], clean_root),
        ]
        targets: dict[str, object] = {}
        for target in TARGETS:
            metadata_path = (
                clean_root
                / "data"
                / "gold"
                / target.planet_slug
                / "modeling"
                / "dataset_metadata.json"
            )
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            expected = current_metadata[target.planet_slug]
            if metadata["dataset_id"] != expected["dataset_id"]:
                raise AssertionError(f"Clean dataset ID mismatch for {target.planet_slug}")
            paths = build_paths(target, "clean-rebuild-validation", clean_root)
            ensure_directories(paths)
            prepared, summary = prepare_modeling_input(
                read_gold_transit_window(paths), paths
            )
            targets[target.planet_slug] = {
                "dataset_id": metadata["dataset_id"],
                "gold_rows": metadata["row_count"],
                "segments": metadata["segment_count"],
                "m5_rows": len(prepared),
                "m5_modeling_input_sha256": sha256_file(paths.modeling_input_path),
                "preprocessing_status": summary["preprocessing_status"],
            }
        evidence = {
            "status": "passed",
            "isolation": "temporary workspace initially containing only src, scripts, and RAW",
            "network_used": False,
            "python_executable": sys.executable,
            "python_version": sys.version.split()[0],
            "source_raw_tree_sha256": raw_digest,
            "commands": commands,
            "targets": targets,
        }
    output = PROJECT_ROOT / "reports" / "clean_rebuild_validation.json"
    output.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(evidence, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
