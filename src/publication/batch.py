"""Protocol-driven, append-only scientific attempts. Never select a best retry."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from publication.contracts import (
    RunIdentity,
    committed_protocol,
    deterministic_seed,
    reserve_run,
    sha256_file,
    update_run_status,
    verify_run_artifacts,
)


def write_new(path: Path, payload: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def run_synthetic(root: Path, protocol_path: Path, *, pilot: bool = False,
                  run_id: str = "final_001", only_scenario: str | None = None) -> list[dict]:
    from publication.simulation import simulate

    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    expected_status = "PILOT" if pilot else "FROZEN"
    if protocol["protocol_status"] != expected_status:
        raise ValueError(f"Expected protocol_status={expected_status}")
    protocol_identity = None if pilot else committed_protocol(root, protocol_path.relative_to(root).as_posix())
    outcomes = []
    for scenario in protocol["scenarios"]:
        if only_scenario is not None and only_scenario != scenario["scenario_id"]:
            continue
        for index in range(protocol.get("replicates_per_scenario", 1)):
            replicate = f"rep_{index:04d}"
            identity = RunIdentity(protocol["experiment_id"], scenario["scenario_id"], replicate, run_id)
            destination = root / identity.relative_path
            if destination.exists():
                # Resume ONLY skips an immutable terminal attempt; never resamples.
                if (destination / "result.json").exists() and (destination / "checksums.json").exists():
                    verify_run_artifacts(destination)
                    print(f"PRESERVED {identity.relative_path}", flush=True)
                    continue
                raise FileExistsError(f"Interrupted attempt remains reserved; classify before a new run ID: {destination}")
            seed_args = (protocol["experiment_id"], scenario["scenario_id"], replicate)
            seeds = {stream: deterministic_seed(*seed_args, stream=stream) for stream in ("generation", "inference", "predictive")}
            destination = reserve_run(root, identity, {"scenario": scenario, "inference": protocol["inference"],
                                      "seeds": seeds, "protocol_sha256": sha256_file(protocol_path)}, protocol_identity, pilot=pilot)
            print(f"START {identity.relative_path}", flush=True)
            started = time.perf_counter()
            try:
                frame, truth = simulate(scenario["truth"], scenario["design"], seeds["generation"])
                input_path = destination / "input.csv"
                frame.to_csv(input_path, index=False, float_format="%.17g", lineterminator="\n")
                input_hash = sha256_file(input_path)
                if input_hash != truth["data_sha256"]:
                    raise ValueError("Serialized simulation does not match declared content hash")
                write_new(destination / "truth.json", truth)
                dataset_id = f"synthetic-{input_hash[:20]}"
                config = {**protocol["inference"], **scenario.get("inference_overrides", {}),
                          "input_kind": "synthetic", "input_sha256": input_hash, "dataset_id": dataset_id, "expected_dataset_id": dataset_id,
                          "inference_seed": seeds["inference"], "predictive_seed": seeds["predictive"]}
                write_new(destination / "inference_config.json", config)
                env = os.environ.copy()
                env["PYTHONPATH"] = str(root / "src")
                env["OMP_NUM_THREADS"] = env["OPENBLAS_NUM_THREADS"] = "1"
                with (destination / "execution.log").open("x", encoding="utf-8") as log:
                    process = subprocess.run(
                        [sys.executable, "-m", "publication.inference", "--input", str(input_path),
                         "--config", str(destination / "inference_config.json"), "--output", str(destination)],
                        cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, check=False,
                    )
                if not (destination / "result.json").exists():
                    write_new(destination / "result.json", {"status": "failed", "error": f"worker exit={process.returncode} without result",
                                                           "gates": {"provenance": False, "sampler": False, "ppc": False, "scientific": False}})
                result = json.loads((destination / "result.json").read_text(encoding="utf-8"))
            except Exception as exc:
                import traceback
                result = {"status": "failed", "error": repr(exc), "traceback": traceback.format_exc(),
                          "gates": {"provenance": False, "sampler": False, "ppc": False, "scientific": False}}
                if not (destination / "result.json").exists():
                    write_new(destination / "result.json", result)
            hashes = {path.name: sha256_file(path) for path in sorted(destination.iterdir()) if path.is_file()}
            write_new(destination / "checksums.json", {"artifacts": hashes, "total_wall_seconds": time.perf_counter() - started})
            update_run_status(destination, result["status"], reason="Truth-blind worker result; no retries or seed selection",
                              evidence={"result_sha256": sha256_file(destination / "result.json"),
                                        "checksums_sha256": sha256_file(destination / "checksums.json")})
            outcomes.append({"identity": identity.relative_path, "status": result["status"]})
            print(f"END {identity.relative_path} {result['status']} wall={time.perf_counter()-started:.1f}s", flush=True)
    return outcomes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("protocol", type=Path)
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--run-id", default="final_001")
    parser.add_argument("--scenario")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    result = run_synthetic(root, args.protocol.resolve(), pilot=args.pilot, run_id=args.run_id, only_scenario=args.scenario)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
