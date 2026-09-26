"""Integration validation: graceful interruption, resume, physical smoke, no reruns.

Never invokes the final config. Outputs are immutable; use a new smoke config/ID
to repeat engineering validation instead of overwriting the previous evidence.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from publication.campaign import request_stop  # noqa: E402
from publication.campaign_plan import build_plan, read_json  # noqa: E402
from publication.campaign_worker import write_json  # noqa: E402
from publication.contracts import sha256_file  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/publication/smoke_campaign.json"))
    parser.add_argument("--new-campaign-id", help="Preserve earlier engineering attempts under a new explicit identity")
    args = parser.parse_args()
    if args.new_campaign_id:
        import re
        if not re.fullmatch(r"[A-Za-z0-9_]+", args.new_campaign_id):
            raise ValueError("Unsafe smoke campaign ID")
        config = read_json(ROOT / args.config)
        config["campaign_id"] = args.new_campaign_id
        args.config = Path(f"configs/publication/{args.new_campaign_id}.json")
        write_json(ROOT / args.config, config)
    plan = build_plan(ROOT, args.config)
    if plan["mode"] != "smoke":
        raise ValueError("Engineering smoke refuses any final campaign")
    state_path = ROOT / f"artifacts/publication_campaign/{plan['campaign_id']}/campaign_state.json"
    if state_path.exists():
        raise FileExistsError("Prior smoke evidence exists; inspect it or declare a new smoke campaign")
    command = [sys.executable, "scripts/run_publication_campaign.py", "--config", str(args.config), "--resume"]
    first = subprocess.Popen(command, cwd=ROOT)
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        if first.poll() is not None:
            raise RuntimeError("Controller exited before intentional interruption")
        if state_path.exists():
            try:
                state = read_json(state_path)
            except FileNotFoundError:  # brief DrvFS rename visibility gap
                time.sleep(.1)
                continue
            delayed = state["jobs"].get("PUB-02__delay_checkpoint__rep_0000", {})
            if delayed.get("status") == "RUNNING":
                request_stop(ROOT, plan["campaign_id"])
                break
        time.sleep(.1)
    else:
        raise TimeoutError("Did not observe the checkpoint fixture")
    if first.wait(timeout=120) != 0:
        raise RuntimeError("Graceful stop returned failure")
    interrupted = read_json(state_path)
    if interrupted["status"] != "STOPPED":
        raise AssertionError("Stop did not leave pending jobs")
    finished = {key: (len(row["attempts"]), row["attempts"][-1]["completion_manifest_sha256"])
                for key, row in interrupted["jobs"].items() if row["status"] == "COMPLETED"}
    subprocess.run(command, cwd=ROOT, check=True)
    resumed = read_json(state_path)
    for key, identity in finished.items():
        row = resumed["jobs"][key]
        assert identity == (len(row["attempts"]), row["attempts"][-1]["completion_manifest_sha256"])
    technical = resumed["jobs"]["PUB-02__retry_technical__rep_0000"]
    rejected = resumed["jobs"]["PUB-02__scientific_rejection__rep_0000"]
    physical = resumed["jobs"]["PUB-02__tiny_physical__rep_0000"]
    assert [item["status"] for item in technical["attempts"]] == ["FAILED_TECHNICAL", "COMPLETED"]
    assert rejected["status"] == "COMPLETED_REJECTED" and len(rejected["attempts"]) == 1
    assert physical["status"] == "COMPLETED_REJECTED" and len(physical["attempts"]) == 1
    before = {key: len(row["attempts"]) for key, row in resumed["jobs"].items()}
    subprocess.run(command, cwd=ROOT, check=True)
    after = read_json(state_path)
    assert before == {key: len(row["attempts"]) for key, row in after["jobs"].items()}
    result = {"status": "PASS", "mode": "engineering_smoke_not_final_science",
              "campaign_id": plan["campaign_id"], "state_path": state_path.relative_to(ROOT).as_posix(),
              "state_sha256": sha256_file(state_path), "declared_jobs": len(plan["jobs"]),
              "total_attempts": sum(before.values()), "checks": {
                  "intentional_graceful_stop": True, "resume_completed_unchanged": True,
                  "idempotent_second_resume": True, "technical_failure_retry_preserved": True,
                  "scientific_rejection_not_retried": True, "real_physical_smoke_rejected_not_technical": True},
              "scientific_claim": "None: 20-draw smoke cannot establish scientific validity."}
    destination = ROOT / f"publication/validation/{plan['campaign_id']}_validation.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    write_json(destination, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
