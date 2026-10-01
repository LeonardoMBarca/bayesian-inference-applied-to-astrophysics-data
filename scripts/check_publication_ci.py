"""Read GitHub Actions for an exact SHA without printing credentials."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import urllib.request
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="Never")
    credential = subprocess.run(["git", "credential", "fill"], cwd=root, env=env,
                                input="protocol=https\nhost=github.com\n\n", text=True,
                                capture_output=True, check=True)
    fields = dict(line.split("=", 1) for line in credential.stdout.splitlines() if "=" in line)
    token = fields["password"]
    base = "https://api.github.com/repos/LeonardoMBarca/bayesian-inference-applied-to-astrophysics-data"

    def get(path):
        request = urllib.request.Request(base + path, headers={"Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json", "User-Agent": "publication-evidence-readonly"})
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)

    runs = get("/actions/runs?head_sha=" + args.sha + "&per_page=100")["workflow_runs"]
    rows = []
    for run in runs:
        if run["head_sha"] != args.sha:
            continue
        jobs = get(f"/actions/runs/{run['id']}/jobs?per_page=100")["jobs"]
        rows.append({key: run[key] for key in ("id", "head_sha", "status", "conclusion", "html_url", "event")}
                    | {"jobs": [{key: job[key] for key in ("name", "status", "conclusion", "steps")} for job in jobs]})
    report = {"schema_version": "exact-sha-ci-observation-v1", "sha": args.sha,
              "runs": rows, "no_write_or_dispatch": True,
              "meaning": "A green workflow only verifies steps actually executed; skipped conditional steps remain explicit."}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8", newline="\n") as file:
            file.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
