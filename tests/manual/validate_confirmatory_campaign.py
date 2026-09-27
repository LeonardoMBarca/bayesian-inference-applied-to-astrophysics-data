"""Create immutable prelaunch evidence without starting scientific inference."""

import argparse
import contextlib
import json
import subprocess
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from publication.campaign import verify_report  # noqa: E402
from publication.campaign_plan import build_plan  # noqa: E402
from publication.campaign_preflight import validate_execution_environment  # noqa: E402
from publication.contracts import sha256_file  # noqa: E402

CONFIG = "configs/publication/tcc_calibration_confirmatory_v1.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    output.relative_to(ROOT)
    output.mkdir(parents=True, exist_ok=False)
    report = {"schema_version": "confirmatory-prelaunch-v1", "passed": False,
              "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "config_path": CONFIG, "no_final_inference_started_by_validation": True}
    try:
        report["commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        report["parent_report_validation"] = verify_report(ROOT, "tcc_campaign_v1")
        plan = build_plan(ROOT, Path(CONFIG))
        if plan["preflight_errors"]:
            raise ValueError(plan["preflight_errors"])
        report["execution_preflight"] = validate_execution_environment(ROOT, plan)
        with (output / "dry_run.json").open("x", encoding="utf-8") as stdout, (output / "dry_run.stderr.log").open("x", encoding="utf-8") as stderr:
            subprocess.run([sys.executable, "scripts/run_publication_campaign.py", "--config", CONFIG, "--dry-run"],
                           cwd=ROOT, stdout=stdout, stderr=stderr, check=True)
        dry = json.loads((output / "dry_run.json").read_text())
        if dry["preflight_errors"] or len(dry["jobs"]) != 400:
            raise ValueError("CLI dry-run did not validate all 400 declared jobs")
        report["dry_run"] = {"jobs": len(dry["jobs"]), "preflight_errors": dry["preflight_errors"],
                             "estimated_hours": dry["estimated_total_hours"], "resources": dry["resources"]}
        patterns = ["test_confirmatory_campaign.py", "test_publication_campaign_plan.py",
                    "test_publication_campaign.py", "test_campaign_checkpoint_io.py",
                    "test_publication_campaign_preflight.py", "test_publication_campaign_reporting.py",
                    "test_publication_simulation.py", "test_publication_inference.py"]
        suite = unittest.TestSuite(unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern=p) for p in patterns)
        with (output / "tests.log").open("x", encoding="utf-8") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
        report["tests"] = {"patterns": patterns, "run": result.testsRun, "failures": len(result.failures),
                           "errors": len(result.errors), "skips": len(result.skipped)}
        if not result.wasSuccessful() or result.skipped:
            raise ValueError("Focused tests failed or skipped; inspect tests.log")
        checks = [CONFIG, plan["frozen_plan_path"], plan["protocols"]["PUB-02"]["path"],
                  "publication/protocols/PUB-02.json", "configs/publication/tcc_campaign_v1_plan.json",
                  "tests/test_confirmatory_campaign.py", "tests/manual/validate_confirmatory_campaign.py"]
        report["checked_sha256"] = {p: sha256_file(ROOT / p) for p in checks}
        report["passed"] = True
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        report["evidence_sha256"] = {p.name: sha256_file(p) for p in output.iterdir() if p.is_file()}
        (output / "validation.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
