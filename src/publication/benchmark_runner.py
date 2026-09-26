"""Isolated juliet/dynesty worker with canonical seeded posterior artifacts."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
import time
import traceback
import warnings
from contextlib import contextmanager
from pathlib import Path

import numpy as np

from publication.benchmark import batman_flux, load_dataset, posterior_parameters
from publication.inference import (
    file_hash,
    finite_json,
    posterior_intervals,
    read_input,
    residual_correlations,
)


@contextmanager
def dynesty_rng_bridge():
    """Expose inherited constructor RNG to juliet's co_varnames introspection.

    juliet 2.2.10 silently loses rstate with dynesty 3.1.0's inherited __init__.
    A transparent subclass makes that one keyword explicit; all computation
    delegates unchanged to the installed sampler. Single-process worker only.
    No package source is edited, and the original class is always restored.
    """
    import dynesty

    original = dynesty.NestedSampler

    class ExplicitRNGNestedSampler(original):
        def __init__(self, *args, rstate=None, **kwargs):
            if rstate is None:
                raise ValueError("Benchmark dynesty requires an explicit seeded Generator")
            super().__init__(*args, rstate=rstate, **kwargs)

    dynesty.NestedSampler = ExplicitRNGNestedSampler
    try:
        yield
    finally:
        dynesty.NestedSampler = original


def validate_execution_contract(config: dict) -> None:
    """Final workers require an unchanged committed protocol and locked imports."""
    from publication.contracts import committed_protocol, safe_path

    root = Path(__file__).resolve().parents[2]
    if config.get("mode") not in {"pilot", "final"}:
        raise ValueError("Declare benchmark mode pilot or final")
    if config["mode"] == "final":
        identity = committed_protocol(root, config["protocol_path"])
        if identity["sha256"] != config["protocol_sha256"]:
            raise ValueError("Final benchmark protocol identity mismatch")
        protocol = json.loads(safe_path(root, config["protocol_path"]).read_text(encoding="utf-8"))
        if config["benchmark_sampling"] != protocol["benchmark_sampling"]:
            raise ValueError("Final benchmark sampling differs from frozen protocol")
        for key, value in protocol["inference"].items():
            if key != "sampling" and config.get(key) != value:
                raise ValueError(f"Final benchmark inference differs from frozen protocol: {key}")
        for key in ("dataset_id", "input_sha256"):
            if config[key] != protocol["dataset"][key]:
                raise ValueError(f"Final benchmark dataset contract mismatch: {key}")
    environment_path = safe_path(root, "publication/environments/benchmark-environment.json")
    if file_hash(environment_path) != config["benchmark_environment_sha256"]:
        raise ValueError("Benchmark environment manifest identity mismatch")
    environment = json.loads(environment_path.read_text(encoding="utf-8"))
    if platform.python_version() != environment["python_version"]:
        raise ValueError("Benchmark Python version differs from lock")
    for item in environment["packages"]:
        if importlib.metadata.version(item["name"]) != item["version"]:
            raise ValueError(f"Benchmark dependency differs from lock: {item['name']}")
    for relative, expected_hash in environment["source_sha256"].items():
        module, filename = relative.split("/", 1)
        specification = importlib.util.find_spec(module)
        if specification is None or specification.origin is None:
            raise ValueError(f"Benchmark source unavailable: {relative}")
        actual_path = Path(specification.origin).parent / filename
        if file_hash(actual_path) != expected_hash:
            raise ValueError(f"Benchmark installed source checksum mismatch: {relative}")


def nested_diagnostics(raw, sampling: dict) -> tuple[dict, np.ndarray]:
    log_weights = np.asarray(raw.logwt, dtype=float)
    weights = np.exp(log_weights - np.max(log_weights))
    weights /= weights.sum()
    calls = int(np.asarray(raw.ncall).sum())
    iterations = int(raw.niter)
    budget_stopped = calls >= sampling["maxcall"] or (
        sampling.get("maxiter") is not None and iterations >= sampling["maxiter"])
    ess = float(1 / np.sum(weights**2))
    logz_error = float(np.asarray(raw.logzerr)[-1])
    passed = not budget_stopped and ess >= sampling["minimum_weighted_ess"] and logz_error <= sampling["maximum_logz_error"]
    return {"sampler": "dynesty-static", "likelihood_calls": calls, "iterations": iterations,
            "budget_stopped": budget_stopped, "weighted_ess": ess,
            "logz": float(raw.logz[-1]), "logz_error": logz_error,
            "passed": passed,
            "termination_reason": "budget_limit" if budget_stopped else "declared_dlogz_stop",
            "termination_semantics": "Natural-stop eligibility requires neither maxcall nor maxiter reached; otherwise the attempt is rejected. This numerical screen does not prove exhaustive multimodal exploration.",
            "rhat_bfmi": "not applicable to unordered nested samples"}, weights


def predictive_gate(metrics: dict, correlations: dict) -> bool:
    """No evidence of residual correlation is not evidence when unassessable."""
    return bool(.8 <= metrics["posterior_predictive_interval_94_coverage_observed_points"] <= .99
                and .5 <= metrics["standardized_residual_std"] <= 2
                and correlations.get("assessable") is True and not correlations["flagged"])


def run_benchmark(input_path: Path, config: dict, output: Path) -> dict:
    """Run one predeclared attempt; campaign owns/reserves the parent directory."""
    from dynesty.utils import resample_equal

    started = time.perf_counter()
    validate_execution_contract(config)
    sampling = config["benchmark_sampling"]
    frame = read_input(input_path, config)
    dataset, metadata = load_dataset(input_path, config, out_folder=output / "juliet_native")
    rng = np.random.default_rng(config["inference_seed"])
    fit_arguments = {"sampler": "dynesty", "n_live_points": sampling["nlive"],
                     "dlogz": sampling["dlogz"], "maxcall": sampling["maxcall"],
                     "bound": "multi", "sample": "rwalk", "rstate": rng,
                     "print_progress": False, "nthreads": None}
    if sampling.get("maxiter") is not None:
        fit_arguments["maxiter"] = sampling["maxiter"]
    with warnings.catch_warnings(record=True) as captured, dynesty_rng_bridge():
        warnings.simplefilter("always")
        fitted = dataset.fit(**fit_arguments)
    raw = fitted.posteriors["dynesty_output"]
    diagnostics, weights = nested_diagnostics(raw, sampling)
    names = [name for name, prior in dataset.priors.items() if prior["distribution"] != "fixed"]
    np.savez_compressed(output / "weighted_nested_samples.npz", samples=raw.samples, weights=weights,
                        parameter_names=np.asarray(names), loglikelihood=raw.logl,
                        logweight=raw.logwt, logz=raw.logz, logz_error=raw.logzerr, ncall=raw.ncall)
    # juliet's native resample_equal call has no RNG argument. Ignore that
    # noncanonical equal-weight array and reproducibly resample raw weights here.
    equal = resample_equal(raw.samples, weights, rstate=np.random.default_rng(config["resampling_seed"]))
    arrays = posterior_parameters({name: equal[:, index] for index, name in enumerate(names)},
                                  metadata["shared_instrument_suffix"], config["period_days"],
                                  infer_jitter=config["infer_jitter"])
    np.savez_compressed(output / "posterior_samples.npz", **arrays)
    parameters = {name: posterior_intervals(values) for name, values in arrays.items()}
    predictive_rng = np.random.default_rng(config["predictive_seed"])
    selected = predictive_rng.choice(len(equal), size=min(sampling["predictive_draws"], len(equal)), replace=False)
    latent, noisy = [], []
    error = frame.normalized_flux_err.to_numpy()
    for index in selected:
        values = {name: float(array[index]) for name, array in arrays.items()}
        flux = batman_flux(frame, values, config["period_days"], oversample=config["oversample"],
                           integrate_exposure=config["integrate_exposure"])
        latent.append(flux)
        noisy.append(flux + predictive_rng.normal(size=len(frame)) * np.sqrt(error**2 + values["extra_sigma"]**2))
    predicted_mean = np.mean(latent, axis=0)
    low, high = np.quantile(noisy, [.03, .97], axis=0)
    observed = frame.normalized_flux.to_numpy()
    residual = observed - predicted_mean
    total_sd = np.sqrt(error**2 + parameters["extra_sigma"]["mean"]**2)
    metrics = {"posterior_predictive_interval_94_coverage_observed_points": float(np.mean((observed >= low) & (observed <= high))),
               "standardized_residual_std": float(np.std(residual / total_sd, ddof=1)),
               "rmse": float(np.sqrt(np.mean(residual**2)))}
    correlations = residual_correlations(frame, residual / total_sd)
    ppc_ok = predictive_gate(metrics, correlations)
    scale = {"extra_sigma_to_measurement_sigma": parameters["extra_sigma"]["mean"] / float(np.median(error)),
             "radius_ratio_boundary_fraction": float(np.mean((arrays["r"] < .00349) | (arrays["r"] > .24751)))}
    scale_ok = scale["extra_sigma_to_measurement_sigma"] <= 20 and scale["radius_ratio_boundary_fraction"] <= .05
    gates = {"provenance": True, "sampler": diagnostics["passed"], "ppc": ppc_ok,
             "scientific": diagnostics["passed"] and ppc_ok and scale_ok}
    curve = frame[["time", "phase", "segment_id"]].copy()
    curve["observed"], curve["posterior_mean"], curve["residual"] = observed, predicted_mean, residual
    curve["predictive_q03"], curve["predictive_q97"] = low, high
    curve.to_csv(output / "predictive_summary.csv", index=False)
    return {"status": "completed" if gates["scientific"] else "rejected", "gates": gates,
            "dataset_id": config["dataset_id"], "input_sha256": config["input_sha256"],
            "model": metadata, "parameters": parameters, "diagnostics": diagnostics,
            "sampling": sampling, "residual_metrics": metrics, "residual_correlation": correlations,
            "scale_checks": scale, "wall_seconds": time.perf_counter() - started,
            "warnings": [str(item.message) for item in captured],
            "rng_bridge": "ExplicitRNGNestedSampler delegates unchanged to installed dynesty; exposes inherited rstate to juliet 2.2.10 introspection. Required by reproducibility pilot v1 failure.",
            "determinism": "Seeded dynesty weighted samples; separate seeded canonical resampling and PPC. Native juliet resampled arrays/pickle are retained but not canonical deterministic posterior artifacts.",
            "canonical_array_sha256": hashlib.sha256(np.asarray(equal, dtype="<f8").tobytes()).hexdigest(),
            "artifact_sha256": {name: file_hash(output / name) for name in
                                ("weighted_nested_samples.npz", "posterior_samples.npz", "predictive_summary.csv")},
            "interpretation": "Matched companion implementation check only; historical scientific_003 has a different radius prior. Nested-sampler and predictive gates do not prove calibration."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    with (args.output / "benchmark_started.json").open("x", encoding="utf-8") as handle:
        json.dump({"input_sha256": config["input_sha256"], "config_sha256": file_hash(args.config)}, handle)
    try:
        read_input(args.input, config)
        provenance_valid = True
        result = run_benchmark(args.input, config, args.output)
    except Exception as exc:
        result = {"status": "failed", "error": repr(exc), "traceback": traceback.format_exc(),
                  "failure_stage": "benchmark_execution" if locals().get("provenance_valid", False) else "input_validation",
                  "gates": {"provenance": locals().get("provenance_valid", False), "sampler": False, "ppc": False, "scientific": False}}
    with (args.output / "result.json").open("x", encoding="utf-8") as handle:
        json.dump(finite_json(result), handle, indent=2, allow_nan=False)
    print(json.dumps({"status": result["status"], "output": str(args.output)}))
    if result["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
