"""Read-only scientific campaign preflight before any expensive final job."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path

from publication.contracts import safe_path, sha256_file, verify_baseline
from publication.environment_guard import require_scientific_environment


class ExecutionEnvironmentError(ValueError):
    """Blocking preflight error, with a machine-readable audit report."""

    def __init__(self, report: dict):
        self.report = report
        super().__init__("Execution preflight failed: " + "; ".join(report["errors"]))


def inspect_external_interpreter(interpreter: str, environment: dict) -> dict:
    """Read package metadata and source bytes in the configured interpreter."""
    path = Path(interpreter)
    if not path.is_absolute() or not path.is_file():
        raise ValueError(f"Benchmark interpreter is missing or not absolute: {interpreter}")
    names = [item["name"] for item in environment["packages"]]
    sources = list(environment["source_sha256"])
    code = (
        "import sys,json,platform,hashlib,importlib.metadata,importlib.util\n"
        "from pathlib import Path\n"
        "def version(name):\n"
        " try: return importlib.metadata.version(name)\n"
        " except importlib.metadata.PackageNotFoundError: return None\n"
        "sources={}\n"
        f"for relative in {sources!r}:\n"
        " package,filename=relative.split('/',1)\n"
        " spec=importlib.util.find_spec(package)\n"
        " p=Path(spec.origin).parent/filename if spec and spec.origin else None\n"
        " sources[relative]=hashlib.sha256(p.read_bytes()).hexdigest() if p and p.is_file() else None\n"
        f"print(json.dumps(dict(python_version=platform.python_version(),executable=sys.executable,packages={{name:version(name) for name in {names!r}}},source_sha256=sources)))\n"
    )
    completed = subprocess.run([str(path), "-c", code], capture_output=True, text=True, timeout=60, check=False)
    if completed.returncode:
        raise ValueError(f"Benchmark interpreter metadata probe failed ({completed.returncode}): {completed.stderr[-1500:]}")
    observed = json.loads(completed.stdout)
    errors = []
    if observed["python_version"] != environment["python_version"]:
        errors.append("benchmark Python version differs from locked environment")
    for item in environment["packages"]:
        if observed["packages"].get(item["name"]) != item["version"]:
            errors.append(f"benchmark distribution mismatch: {item['name']}")
    for relative, expected in environment["source_sha256"].items():
        if observed["source_sha256"].get(relative) != expected:
            errors.append(f"benchmark installed source mismatch: {relative}")
    observed.update(passed=not errors, errors=errors)
    return observed


def validate_execution_environment(root: Path, plan: dict) -> dict:
    """Verify identities/availability once before P2 spends the campaign budget.

    Includes the actual protected historical trace, not just its path. Missing
    archived baseline evidence or preselected RAW inputs is a blocker requiring
    restoration, never a trigger to overwrite/regenerate historical evidence.
    No scientific inference, download, environment mutation or registry edit.
    """
    if plan.get("mode") != "final":
        return {"passed": True, "status": "not_applicable_to_nonfinal_mode", "errors": []}
    root = root.resolve()
    report = {"schema_version": "campaign-execution-preflight-v1", "passed": False, "errors": [],
              "campaign_id": plan["campaign_id"], "actual_scientific_interpreter": sys.executable,
              "platform": platform.platform(), "sources": []}
    errors = report["errors"]
    try:
        branch = subprocess.run(["git", "-C", str(root), "branch", "--show-current"],
                                capture_output=True, text=True, check=True, timeout=15).stdout.strip()
        report["branch"] = branch
        if branch != "publication-grade-validation":
            errors.append(f"Final execution requires publication-grade-validation, found {branch!r}")
        declared = Path(plan["runtime"]["scientific_python"])
        if declared.resolve() != Path(sys.executable).resolve():
            errors.append("Campaign preflight is not running in the configured scientific interpreter")
        report["scientific_environment"] = require_scientific_environment(root)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        errors.append(str(exc))
    try:
        report["protected_baseline"] = verify_baseline(root, require_external=True)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        errors.append(str(exc))
    protocols = {}
    for name, identity in plan.get("protocols", {}).items():
        try:
            path = safe_path(root, identity["path"])
            if sha256_file(path) != identity["sha256"]:
                raise ValueError(f"Protocol mutated before execution preflight: {name}")
            protocols[name] = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            errors.append(str(exc))
    if "PUB-03" in protocols:
        try:
            protocol = protocols["PUB-03"]
            environment_path = safe_path(root, "publication/environments/benchmark-environment.json")
            if sha256_file(environment_path) != protocol["benchmark_environment_sha256"]:
                raise ValueError("PUB-03 benchmark environment manifest checksum mismatch")
            environment = json.loads(environment_path.read_text(encoding="utf-8"))
            external = inspect_external_interpreter(plan["runtime"]["benchmark_python"], environment)
            report["benchmark_environment"] = external
            errors.extend(external["errors"])
            report["sources"].append({"role": "PUB-03 exact historical input", "path": protocol["dataset"]["input_path"],
                                      "expected_sha256": protocol["dataset"]["input_sha256"]})
        except (ValueError, OSError, subprocess.SubprocessError) as exc:
            errors.append(str(exc))
    if "PUB-05" in protocols:
        for target in protocols["PUB-05"]["targets"]:
            if len(target["sources"]) != target["expected_source_count"]:
                errors.append(f"PUB-05 source count differs for {target['config']['planet_slug']}")
            for source in target["sources"]:
                report["sources"].append({"role": f"PUB-05 {target['config']['planet_slug']} RAW",
                                          "path": source["path"], "expected_sha256": source["sha256"]})
    for source in report["sources"]:
        try:
            path = safe_path(root, source["path"])
            source["actual_sha256"] = sha256_file(path)
            source["size_bytes"] = path.stat().st_size
            source["matched"] = source["actual_sha256"] == source["expected_sha256"]
            if not source["matched"]:
                errors.append(f"Required scientific input checksum mismatch: {source['path']}")
        except (ValueError, OSError) as exc:
            source["matched"] = False
            errors.append(f"Required scientific input unavailable: {source['path']}: {exc}")
    report["passed"] = not errors
    if errors:
        raise ExecutionEnvironmentError(report)
    return report
