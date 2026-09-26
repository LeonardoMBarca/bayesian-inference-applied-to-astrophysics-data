"""Two tiny deterministic nested-sampler PILOTS; no scientific promotion allowed."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from publication.benchmark import batman_flux  # noqa: E402
from publication.inference import file_hash  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    phase = np.linspace(-.12, .12, 60)
    frame = pd.DataFrame({"phase": phase, "time": phase + 10,
                          "normalized_flux_err": np.linspace(.0005, .001, 60),
                          "exposure_time_seconds": np.repeat(120., 60), "segment_id": "pilot"})
    physical = {"r": .08, "a": 6., "b": .4, "q1": .25, "q2": .3, "t0": .002, "baseline": 1.}
    frame["normalized_flux"] = batman_flux(frame, physical, 2., oversample=15) + np.random.default_rng(14891).normal(size=60) * frame.normalized_flux_err
    input_path = args.output / "input.csv"
    frame.to_csv(input_path, index=False)
    input_hash = file_hash(input_path)
    config = {"mode": "pilot", "input_kind": "synthetic", "dataset_id": f"synthetic-{input_hash[:20]}",
              "expected_dataset_id": f"synthetic-{input_hash[:20]}", "input_sha256": input_hash,
              "period_days": 2., "radius_prior_uniform": [.001, .2], "radius_prior_median": None,
              "baseline_prior_sigma": .02, "t0_prior_sigma_days": .025,
              "jitter_error_multiplier": 5., "jitter_floor_fraction": .0005,
              "infer_jitter": True, "integrate_exposure": True, "oversample": 15,
              "inference_seed": 72971, "resampling_seed": 182739, "predictive_seed": 82912,
              "benchmark_environment_sha256": file_hash(ROOT / "publication/environments/benchmark-environment.json"),
              "benchmark_sampling": {"nlive": 20, "dlogz": .1, "maxcall": 100, "maxiter": None,
                                     "minimum_weighted_ess": 400, "maximum_logz_error": .5, "predictive_draws": 20}}
    config_path = args.output / "inference_config.json"
    config_path.write_text(json.dumps(config, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    outcomes = []
    for index in range(2):
        output = args.output / f"pilot_{index:03d}"
        output.mkdir()
        completed = subprocess.run([sys.executable, str(ROOT / "scripts/run_publication_benchmark.py"),
                                    "--input", str(input_path), "--config", str(config_path), "--output", str(output)],
                                   capture_output=True, text=True, timeout=180)
        (output / "worker.stdout.txt").write_text(completed.stdout, encoding="utf-8")
        (output / "worker.stderr.txt").write_text(completed.stderr, encoding="utf-8")
        result = json.loads((output / "result.json").read_text(encoding="utf-8"))
        outcomes.append({"returncode": completed.returncode, "result": result})
    hashes = [item["result"].get("canonical_array_sha256") for item in outcomes]
    passed = (all(item["returncode"] == 0 and item["result"]["status"] == "rejected" for item in outcomes)
              and hashes[0] is not None and hashes[0] == hashes[1]
              and all(item["result"]["diagnostics"]["budget_stopped"] for item in outcomes))
    report = {"evidence_class": "pilot_parser_rng_and_budget_check_not_science", "passed": passed,
              "same_canonical_array_hash": hashes[0] is not None and hashes[0] == hashes[1],
              "canonical_array_sha256": hashes, "outcomes": outcomes}
    (args.output / "smoke_report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"passed": passed, "output": str(args.output)}))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
