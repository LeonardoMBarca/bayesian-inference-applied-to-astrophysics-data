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

PROJECT_ROOT = Path(__file__).resolve().parents[2]
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


def guarded_environment(root: Path, log_path: Path) -> dict[str, str]:
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    environment.pop("PYTHONPATH", None)
    environment["PYTHONPATH"] = str(root / "scripts" / "_network_guard")
    environment["CLEAN_REBUILD_NETWORK_GUARD_LOG"] = str(log_path)
    return environment


def verify_network_guard(root: Path, log_path: Path) -> dict[str, object]:
    log_path.unlink(missing_ok=True)
    probes = {
        "socket.socket.connect": (
            "import socket; socket.socket().connect(('127.0.0.1', 9))"
        ),
        "socket.socket.connect_ex": (
            "import socket; socket.socket().connect_ex(('127.0.0.1', 9))"
        ),
        "socket.create_connection": (
            "import socket; socket.create_connection(('example.com', 443), timeout=0.1)"
        ),
        "socket.getaddrinfo": "import socket; socket.getaddrinfo('example.com', 443)",
    }
    returncodes: dict[str, int] = {}
    for api_name, probe in probes.items():
        completed = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=root,
            env=guarded_environment(root, log_path),
            text=True,
            capture_output=True,
            check=False,
        )
        returncodes[api_name] = completed.returncode
        if completed.returncode == 0:
            raise AssertionError(
                f"The clean-rebuild Python socket guard did not block {api_name}."
            )
    attempts = log_path.read_text(encoding="utf-8").splitlines() if log_path.exists() else []
    if attempts != list(probes):
        raise AssertionError(
            "The clean-rebuild Python socket guard probe log is incomplete: "
            f"expected {list(probes)}, found {attempts}."
        )
    return {
        "verified": True,
        "blocked_apis": list(probes),
        "probe_returncodes": returncodes,
    }


def run(
    command: list[str],
    root: Path,
    environment: dict[str, str],
) -> dict[str, object]:
    started = time.monotonic()
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
        preflight_log = clean_root / "network_guard_preflight.log"
        guard_verification = verify_network_guard(clean_root, preflight_log)
        pipeline_network_log = clean_root / "network_guard_pipeline_attempts.log"
        pipeline_environment = guarded_environment(clean_root, pipeline_network_log)
        commands = [
            run(
                [sys.executable, "scripts/build_silver_data.py"],
                clean_root,
                pipeline_environment,
            ),
            run(
                [sys.executable, "scripts/build_gold_data.py"],
                clean_root,
                pipeline_environment,
            ),
        ]
        attempted_network_calls = (
            pipeline_network_log.read_text(encoding="utf-8").splitlines()
            if pipeline_network_log.exists()
            else []
        )
        if attempted_network_calls:
            raise AssertionError(
                "Clean rebuild attempted standard Python socket networking: "
                f"{attempted_network_calls}"
            )
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
            "network_isolation": {
                "enforcement": "verified Python socket guard",
                "scope": (
                    "Standard Python socket connect, connect_ex, create_connection, "
                    "and getaddrinfo APIs in Silver/Gold subprocesses; this is not an "
                    "operating-system network namespace."
                ),
                "verification": guard_verification,
                "pipeline_attempted_network_calls": attempted_network_calls,
            },
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
