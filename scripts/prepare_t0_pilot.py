"""Prepare tiny, explicitly non-final time-coordinate wiring/timing controls."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    old = json.loads((ROOT / "configs/publication/runner_smoke_v2.json").read_text())
    fixture = old["smoke_jobs"][-1]
    jobs = []
    for coordinates in ("direct", "standardized"):
        job = copy.deepcopy(fixture)
        job["scenario_id"] = "pilot_t0_" + coordinates
        job["inference"]["transit_center_parameterization"] = coordinates
        job["inference"]["sampling"].update(draws=40, tune=40, save_warmup=True)
        jobs.append(job)
    config = {"campaign_id": "t0_coordinate_pilot_v1", "mode": "smoke",
              "description": "PILOT: two tiny wiring/runtime controls, different independent noise draws, NOT final efficacy comparison or calibration.",
              "resources": {"max_workers": 1, "cores_per_run": 1, "max_campaign_hours": 1, "stop_margin_minutes": 0},
              "runtime": {"scientific_python": "/home/leonardo_barca/mc3/bin/python3.14", "wsl_distribution": "Ubuntu-24.04"},
              "smoke_jobs": jobs, "technical_retries": 0}
    destination = ROOT / "configs/publication/t0_coordinate_pilot_v1.json"
    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(config, stream, indent=2)
        stream.write("\n")
    print(destination)


if __name__ == "__main__":
    main()
