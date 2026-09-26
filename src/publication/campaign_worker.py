"""One isolated campaign attempt; truth never enters the inference subprocess."""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

from publication.campaign_plan import DEFAULT_CONFIG, build_plan, read_json
from publication.contracts import sha256_file


def write_json(path: Path, payload: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def classify_result(result: dict, *, expected_identity_rejection: bool = False) -> str:
    if result.get("status") in {"completed", "rejected", "not_interpretable"}:
        return "COMPLETED" if all(result.get("gates", {}).get(key) is True for key in
                                  ("provenance", "sampler", "ppc", "scientific")) else "COMPLETED_REJECTED"
    if expected_identity_rejection and result.get("failure_stage") == "input_validation":
        return "COMPLETED_REJECTED"
    return "FAILED_TECHNICAL"


def accept_child_result(attempt: Path, return_code: int, intervention: str | None) -> tuple[dict, bool]:
    """A produced posterior is not a successful process exit or control proof."""
    path = attempt / "result.json"
    result = read_json(path)
    expected_code = {"invalid_input_hash": "input_sha256_mismatch",
                     "dataset_identity_mismatch": "dataset_identity_mismatch"}.get(intervention)
    expected = (expected_code is not None and result.get("failure_stage") == "input_validation"
                and result.get("failure_code") == expected_code)
    if return_code != 0 and not expected and result.get("status") != "failed":
        preserved = attempt / "child_result.json"
        if preserved.exists():
            raise FileExistsError("Preserved child result already exists")
        path.rename(preserved)
        result = {"status": "failed", "failure_stage": "child_process_exit",
                  "error": f"Inference exited {return_code} after writing an unsealed result",
                  "preserved_child_result": "child_result.json",
                  "gates": {"provenance": result.get("gates", {}).get("provenance", False),
                            "sampler": False, "ppc": False, "scientific": False}}
        write_json(path, result)
    return result, expected


def prepare_synthetic(job: dict, attempt: Path) -> tuple[Path, dict]:
    from publication.simulation import simulate

    payload = job["payload"]
    scenario = payload["scenario"]
    frame, truth = simulate(scenario["truth"], scenario["design"], job["seeds"]["generation"])
    write_json(attempt / "truth.json", truth)
    config = copy.deepcopy(payload["inference"])
    if payload["kind"] == "ablation":
        from publication.ablations import apply_ablation
        frame.to_csv(attempt / "generated.csv", index=False, float_format="%.17g", lineterminator="\n")
        frame, config = apply_ablation(frame, config, payload["intervention"])
        write_json(attempt / "preprocessing.json", frame.attrs["normalization_metadata"])
        write_json(attempt / "ablation.json", frame.attrs["ablation"])
    input_path = attempt / "input.csv"
    frame.to_csv(input_path, index=False, float_format="%.17g", lineterminator="\n")
    digest = sha256_file(input_path)
    if payload["kind"] == "synthetic":
        if digest != truth["data_sha256"]:
            raise ValueError("Synthetic serialization differs from generated identity")
        config.update(input_sha256=digest, dataset_id=f"synthetic-{digest[:20]}",
                      expected_dataset_id=f"synthetic-{digest[:20]}", input_kind="synthetic")
    elif payload["intervention"] != "invalid_input_hash" and digest != config["input_sha256"]:
        raise ValueError("Ablation serialization differs from preprocessing identity")
    return input_path, config


def prepare_observational(root: Path, plan: dict, job: dict, attempt: Path) -> tuple[Path, dict]:
    from publication.observational import prepare_observational_target

    payload = job["payload"]
    protocol_path = root / payload["protocol"]
    protocol = read_json(protocol_path)
    run_id = f"{plan['campaign_id']}_{payload['target_slug']}_{attempt.name}"
    preparation = prepare_observational_target(root, protocol_path, payload["target_slug"], run_id,
        expected_protocol_sha256=plan["protocols"]["PUB-05"]["sha256"])
    write_json(attempt / "preparation.json", preparation)
    source = root / preparation["input_path"]
    target = next(item["config"] for item in protocol["targets"] if item["config"]["planet_slug"] == payload["target_slug"])
    config = copy.deepcopy(protocol["inference"])
    config.update(period_days=target["orbital_period_days"], target_name=target["planet_name"],
                  dataset_id=preparation["dataset_id"], expected_dataset_id=preparation["dataset_id"],
                  input_sha256=preparation["input_sha256"], input_kind="observational",
                  preprocessing_status="segment_normalized")
    destination = attempt / "input.csv"
    shutil.copyfile(source, destination)
    if sha256_file(destination) != preparation["input_sha256"]:
        raise ValueError("Prepared observational copy identity mismatch")
    return destination, config


def prepare_benchmark(root: Path, plan: dict, job: dict, attempt: Path) -> tuple[Path, dict]:
    protocol = read_json(root / job["payload"]["protocol"])
    source = root / protocol["dataset"]["input_path"]
    if sha256_file(source) != protocol["dataset"]["input_sha256"]:
        raise ValueError("Protected benchmark input changed")
    destination = attempt / "input.csv"
    shutil.copyfile(source, destination)
    config = copy.deepcopy(protocol["inference"])
    config.setdefault("radius_prior_log_sigma", .9)  # unused by the matched Uniform radius prior
    config.update(input_kind="observational", dataset_id=protocol["dataset"]["dataset_id"],
                  expected_dataset_id=protocol["dataset"]["dataset_id"], input_sha256=sha256_file(destination))
    if job["payload"]["kind"] == "benchmark_external":
        config.update(mode="final", protocol_path=job["payload"]["protocol"],
                      protocol_sha256=plan["protocols"]["PUB-03"]["sha256"],
                      benchmark_sampling=protocol["benchmark_sampling"],
                      benchmark_environment_sha256=protocol["benchmark_environment_sha256"])
    return destination, config


def execute_attempt(root: Path, plan: dict, job: dict, attempt: Path) -> dict:
    """The engine reserves an empty directory. A completion manifest seals it."""
    if not attempt.is_dir() or any(attempt.iterdir()):
        raise FileExistsError("Worker requires an already reserved EMPTY attempt directory")
    if plan["preflight_errors"]:
        raise ValueError("Campaign preflight: " + "; ".join(plan["preflight_errors"]))
    from publication.campaign import process_identity
    write_json(attempt / "worker_metadata.json", {"process_identity": process_identity(os.getpid())})
    write_json(attempt / "job.json", job)
    started = time.monotonic()
    completion = {"status": "FAILED_TECHNICAL", "technical_retryable": False,
                  "gates": {}, "input_sha256": None, "dataset_id": None}
    try:
        if plan["mode"] == "final":
            from publication.environment_guard import require_scientific_environment
            environment_identity = require_scientific_environment(root)
            write_json(attempt / "environment_preflight.json", environment_identity)
        payload = job["payload"]
        if payload["kind"] == "fixture":
            if plan["mode"] != "smoke":
                raise ValueError("Fixtures cannot appear in a final campaign")
            time.sleep(payload.get("delay_seconds", 0))
            action = payload.get("action", "completed")
            # Only this explicitly labelled infrastructure fixture is auto-retryable.
            fail = action == "technical_fail_once" and len(list(attempt.parent.glob("attempt*"))) == 1
            accepted = action != "scientific_rejection" and not fail
            result = {"status": "failed" if fail else "completed" if accepted else "rejected",
                      "fixture": True, "gates": {key: accepted for key in ("provenance", "sampler", "ppc", "scientific")},
                      "error": "Simulated transient I/O failure" if fail else None}
            write_json(attempt / "result.json", result)
            completion.update(status=classify_result(result), gates=result["gates"],
                              technical_retryable=fail, error=result["error"])
        else:
            if payload["kind"] in {"synthetic", "ablation"}:
                input_path, config = prepare_synthetic(job, attempt)
            elif payload["kind"] == "observational":
                input_path, config = prepare_observational(root, plan, job, attempt)
            elif payload["kind"] in {"benchmark_local", "benchmark_external"}:
                input_path, config = prepare_benchmark(root, plan, job, attempt)
            else:
                raise ValueError(f"Unsupported worker kind: {payload['kind']}")
            for stream in ("inference", "predictive", "resampling"):
                config[f"{stream}_seed"] = job["seeds"][stream]
            config["campaign_mode"] = plan["mode"]
            # Scientific chain count is frozen; scheduling may lower simultaneous cores.
            config["sampling"]["cores"] = min(config["sampling"]["cores"], job["cores"])
            write_json(attempt / "inference_config.json", config)
            environment = dict(os.environ, PYTHONPATH=str(root / "src"), OMP_NUM_THREADS="1",
                               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1")
            external = payload["kind"] == "benchmark_external"
            interpreter = plan["runtime"]["benchmark_python"] if external else sys.executable
            module = "publication.benchmark_runner" if external else "publication.inference"
            command = [interpreter, "-m", module, "--input", str(input_path), "--config",
                       str(attempt / "inference_config.json"), "--output", str(attempt)]
            write_json(attempt / "inference_command.json", {"argv": command, "truth_file_passed": False})
            completed = subprocess.run(command, cwd=root, env=environment, check=False)
            result, expected_rejection = accept_child_result(attempt, completed.returncode, payload.get("intervention"))
            completion.update(status=classify_result(result, expected_identity_rejection=expected_rejection),
                              gates=result.get("gates", {}), gate_evaluation=result.get("gate_evaluation"),
                              input_sha256=sha256_file(input_path), dataset_id=config["dataset_id"],
                              inference_return_code=completed.returncode, error=result.get("error"),
                              expected_identity_rejection=expected_rejection)
    except Exception as exc:
        completion.update(error=repr(exc), traceback=traceback.format_exc())
        if not (attempt / "result.json").exists():
            write_json(attempt / "result.json", {"status": "failed", "failure_stage": "worker_preparation",
                       "error": repr(exc), "traceback": traceback.format_exc(), "gates": {}})
    completion["wall_seconds"] = time.monotonic() - started
    completion["artifacts"] = {path.relative_to(attempt).as_posix(): sha256_file(path)
                               for path in sorted(attempt.rglob("*")) if path.is_file()}
    write_json(attempt / "completion_manifest.json", completion)
    return completion


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(DEFAULT_CONFIG))
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--attempt-dir", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    plan = build_plan(root, args.config)
    job = next(item for item in plan["jobs"] if item["job_id"] == args.job_id)
    attempt = args.attempt_dir.resolve()
    attempt.relative_to(root / job["output_dir"])
    result = execute_attempt(root, plan, job, attempt)
    print(json.dumps({"job_id": job["job_id"], "status": result["status"]}), flush=True)
    raise SystemExit(1 if result["status"] == "FAILED_TECHNICAL" else 0)


if __name__ == "__main__":
    main()
