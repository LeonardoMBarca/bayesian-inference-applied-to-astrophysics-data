"""Persist engineering acceptance evidence without running the final campaign."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from publication.campaign import _read, _verify_journal, validate_completion  # noqa: E402
from publication.campaign_plan import source_identity  # noqa: E402
from publication.contracts import sha256_file, utc_now  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sharing-evidence", type=Path, required=True)
    parser.add_argument("--smoke-id", required=True)
    parser.add_argument("--reuse-evidence", type=Path,
                        help="Reuse a passing physical smoke only when the sole source change is campaign_plan.py")
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to(ROOT / "publication/validation"):
        raise ValueError("Evidence must be isolated below publication/validation")
    output.mkdir(parents=True, exist_ok=False)
    report = {"kind": "checkpoint_runtime_repair_not_scientific_evidence", "started_at_utc": utc_now(),
              "source_checksums": source_identity(ROOT), "checks": [], "status": "RUNNING"}
    previous = None
    if args.reuse_evidence:
        prior_path = ROOT / args.reuse_evidence
        previous = json.loads(prior_path.read_text())
        changed = {path for path in set(previous["source_checksums"]) | set(report["source_checksums"])
                   if previous["source_checksums"].get(path) != report["source_checksums"].get(path)}
        if previous["status"] != "PASS" or changed != {"src/publication/campaign_plan.py"}:
            raise ValueError("Prior smoke may only be reused for a plan-validator-only change")
        report["reused_smoke_evidence"] = {"path": args.reuse_evidence.as_posix(), "sha256": sha256_file(prior_path),
                                           "reason": "Only plan validation changed; controller/worker/inference byte-identical to prior passing physical smoke"}
    sharing = json.loads((ROOT / args.sharing_evidence).read_text())
    if sharing["status"] != "PASS" or not all(sharing["checks"].values()):
        raise ValueError("Real Windows/WSL test did not pass")
    report["windows_wsl_integration"] = sharing
    state_path = ROOT / "artifacts/publication_campaign/tcc_campaign_v1/campaign_state.json"
    state = _read(state_path)
    _verify_journal(state)
    report["preserved_state_sha256"] = sha256_file(state_path)
    preserved = []
    for job in state["jobs"].values():
        for attempt in job["attempts"]:
            directory = ROOT / attempt["output_dir"]
            manifest = directory / "completion_manifest.json"
            if not manifest.exists():
                continue
            result = validate_completion(directory, expected_manifest_sha256=attempt.get("completion_manifest_sha256"))
            preserved.append({"job_id": job["job_id"], "output_dir": attempt["output_dir"],
                              "completion_manifest_sha256": sha256_file(manifest),
                              "status": result["status"], "artifacts": result["artifacts"]})
    report["preserved_runs"] = preserved
    report["preserved_run_count"] = len(preserved)
    commands = [
        ("lint", [sys.executable, "-m", "ruff", "check", "."]),
        ("static", [sys.executable, "scripts/static_validate.py"]),
        ("full_practical_suite", [sys.executable, "scripts/run_ci_tests.py"]),
        ("baseline", [sys.executable, "scripts/validate_hardened_artifacts.py"]),
    ]
    if previous is None:
        commands.append(("resume_smoke", [sys.executable, "scripts/validate_publication_campaign_smoke.py", "--new-campaign-id", args.smoke_id]))
    try:
        for name, command in commands:
            print(f"CHECK {name}", flush=True)
            stdout_path, stderr_path = output / f"{name}.stdout.txt", output / f"{name}.stderr.txt"
            started = time.monotonic()
            with stdout_path.open("w") as stdout, stderr_path.open("w") as stderr:
                code = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr, check=False).returncode
            report["checks"].append({"name": name, "command": command, "return_code": code,
                                      "seconds": time.monotonic() - started,
                                      "stdout": stdout_path.relative_to(ROOT).as_posix(), "stdout_sha256": sha256_file(stdout_path),
                                      "stderr": stderr_path.relative_to(ROOT).as_posix(), "stderr_sha256": sha256_file(stderr_path)})
            if code:
                raise RuntimeError(f"Acceptance check failed: {name}; inspect persisted logs")
        if sha256_file(state_path) != report["preserved_state_sha256"]:
            raise RuntimeError("Engineering validation modified the scientific campaign checkpoint")
        if source_identity(ROOT) != report["source_checksums"]:
            raise RuntimeError("Python sources changed during acceptance validation")
        report["status"] = "PASS"
    except Exception as exc:
        report.update(status="FAILED", error=str(exc))
        raise
    finally:
        report["finished_at_utc"] = utc_now()
        (output / "validation.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "preserved_runs": len(preserved), "output": str(output)}), flush=True)


if __name__ == "__main__":
    main()
