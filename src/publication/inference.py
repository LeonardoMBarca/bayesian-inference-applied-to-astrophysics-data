"""Truth-blind publication inference using the shared physical M5 graph.

Run in a separate process with only a data path and inference configuration.
This module deliberately does not import the simulator or open truth files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

PARAMETERS = ("baseline", "r", "b", "a", "t0", "q1", "q2", "extra_sigma", "depth", "full_duration")
REQUIRED_COLUMNS = {"phase", "time", "normalized_flux", "normalized_flux_err", "exposure_time_seconds", "segment_id"}


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def read_input(path: Path, config: dict) -> pd.DataFrame:
    """Validate exact observations before graph construction or sampling."""
    if file_hash(path) != config["input_sha256"]:
        raise ValueError("inference input SHA-256 mismatch")
    if not config.get("dataset_id") or config.get("expected_dataset_id") != config["dataset_id"]:
        raise ValueError("inference dataset identity mismatch")
    if config.get("input_kind") == "synthetic" and config["dataset_id"] != f"synthetic-{config['input_sha256'][:20]}":
        raise ValueError("synthetic identity is not content-bound")
    frame = pd.read_csv(path)
    if not REQUIRED_COLUMNS.issubset(frame):
        raise ValueError(f"missing required input columns: {REQUIRED_COLUMNS - set(frame)}")
    if len(frame) < 12 or frame["segment_id"].isna().any():
        raise ValueError("insufficient observations or missing segment identity")
    for column in REQUIRED_COLUMNS - {"segment_id"}:
        values = frame[column].to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError(f"nonfinite input column {column}")
        if column in {"normalized_flux_err", "exposure_time_seconds"} and (values <= 0).any():
            raise ValueError(f"nonpositive input column {column}")
    return frame


def posterior_intervals(values: np.ndarray) -> dict:
    values = np.asarray(values, dtype=float).reshape(-1)
    if len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("invalid posterior samples")
    return {
        "mean": float(np.mean(values)), "median": float(np.median(values)),
        "sd": float(np.std(values, ddof=1)),
        "interval_method": "equal_tailed",
        "intervals": {str(level): np.quantile(values, [(1-level)/2, (1+level)/2]).tolist()
                      for level in (0.5, 0.8, 0.94)},
    }


def sampler_summary(idata, names: list[str]) -> pd.DataFrame:
    """Use the locked ArviZ 1.x API; intervals here are diagnostic, not coverage."""
    import arviz as az
    return az.summary(idata, var_names=names, ci_prob=.94, ci_kind="hdi", round_to=8).reset_index().rename(columns={"index": "parameter"})


def residual_correlations(frame: pd.DataFrame, residual: np.ndarray, max_lag: int = 5) -> dict:
    """Within-segment/cadence pairs only; no phase-folded artificial adjacency.

    Normal-reference bounds are exploratory approximations, not an exact test
    for fitted residuals. Familywise .01 across the declared five lags per run.
    """
    from scipy.stats import norm

    data = frame[["time", "segment_id"]].copy()
    data["residual"] = residual
    data = data.sort_values(["segment_id", "time"])
    entries = []
    for lag in range(1, max_lag + 1):
        left, right = [], []
        for _, segment in data.groupby("segment_id", sort=True):
            t = segment.time.to_numpy()
            z = segment.residual.to_numpy()
            if len(t) <= lag + 2:
                continue
            cadence = float(np.median(np.diff(t)))
            valid = (t[lag:] - t[:-lag]) <= (lag + 0.5) * cadence
            left.extend(z[:-lag][valid])
            right.extend(z[lag:][valid])
        n = len(left)
        correlation = float(np.corrcoef(left, right)[0, 1]) if n > 10 else None
        bound = float(norm.ppf(1 - 0.01 / (2 * max_lag)) / np.sqrt(n)) if n > 10 else None
        entries.append({"lag": lag, "pairs": n, "correlation": correlation,
                        "normal_reference_bound": bound,
                        "flagged": correlation is not None and abs(correlation) > bound})
    return {"method": "within-segment cadence-contiguous Pearson; Bonferroni normal reference",
            "familywise_alpha_per_run": 0.01, "lags": entries,
            "flagged": any(row["flagged"] for row in entries)}


def make_model(frame: pd.DataFrame, config: dict):
    from bayesian_modeling.contracts import PriorProfile, TransitModelOptions
    from bayesian_modeling.physical_transit import build_model
    from project_config import TargetConfig

    # These are declared inference assumptions, NEVER copied from truth artifacts.
    target = TargetConfig(
        planet_name=config.get("target_name", "Synthetic protocol target"),
        host_star="publication", planet_slug="publication", mission="controlled",
        priority=1, orbital_period_days=float(config["period_days"]),
        transit_midpoint_bjd=0., transit_duration_hours=float(config["t0_prior_sigma_days"]) * 96,
        transit_depth_percent=0.16, planet_radius_earth=1., stellar_radius_solar=1.,
        cadence_preference="any", exposure_oversample=int(config["oversample"]),
    )
    options = TransitModelOptions(
        radius_prior_median=config.get("radius_prior_median"),
        radius_prior_uniform=tuple(config["radius_prior_uniform"]) if config.get("radius_prior_uniform") else None,
        baseline_prior_sigma=config["baseline_prior_sigma"],
        transit_center_prior_sigma_days=config["t0_prior_sigma_days"],
        infer_jitter=config["infer_jitter"], integrate_exposure=config["integrate_exposure"],
        mutable_observations=True,
    )
    prior = PriorProfile(
        name="publication_explicit", radius_ratio_log_sigma=config["radius_prior_log_sigma"],
        jitter_error_multiplier=config["jitter_error_multiplier"],
        jitter_floor_fraction=config["jitter_floor_fraction"], purpose="Frozen publication protocol",
    )
    model = build_model(frame, np.linspace(frame.phase.min(), frame.phase.max(), 3), target, prior, options=options)
    return model, {"options": asdict(options), "prior_profile": asdict(prior),
                   "fixed_period_days": config["period_days"], "eccentricity": 0.,
                   "a_prior": [2., 50.], "b_prior": [0., 1.], "q1_q2_prior": [0., 1.],
                   "baseline_prior_mean": 1., "t0_prior_mean_days": 0.,
                   "implementation": "shared bayesian_modeling.physical_transit.build_model",
                   "family": "M5-publication-v1", "likelihood": "independent Normal: measurement variance + white jitter variance"}


def fit(input_path: Path, config: dict, output: Path) -> dict:
    """One declared attempt, no auto-retry or posterior-dependent configuration."""
    import pymc as pm

    from bayesian_modeling.contracts import evaluate_interpretation_gate
    from bayesian_modeling.physical_transit import (
        build_environment_summary,
        diagnostics_from_summary,
    )

    started = time.perf_counter()
    frame = read_input(input_path, config)
    model, specification = make_model(frame, config)
    sampling = config["sampling"]
    diagnostics_names = list(PARAMETERS)
    if not config["infer_jitter"]:
        diagnostics_names.remove("extra_sigma")  # A constant is not a sampled quantity.
    with model:
        compile_kwargs = None
        if sampling.get("linker") == "cvm":
            from pytensor.compile.mode import Mode
            compile_kwargs = {"mode": Mode(linker="cvm", optimizer="fast_run")}
        idata = pm.sample(
            draws=sampling["draws"], tune=sampling["tune"], chains=sampling["chains"],
            cores=sampling["cores"], target_accept=sampling["target_accept"],
            random_seed=config["inference_seed"], init="jitter+adapt_diag",
            nuts_sampler="pymc", var_names=list(PARAMETERS), progressbar=False,
            return_inferencedata=True, blas_cores=1,
            compile_kwargs=compile_kwargs,
        )
    idata.to_netcdf(output / "trace.nc")
    summary = sampler_summary(idata, diagnostics_names)
    summary.to_csv(output / "sampler_summary.csv", index=False)
    diagnostics = diagnostics_from_summary(summary, idata)
    if "tree_depth" in idata.sample_stats:
        tree = np.asarray(idata.sample_stats["tree_depth"].values)
        diagnostics.update(max_tree_depth=int(tree.max()), fraction_tree_depth_ge_10=float(np.mean(tree >= 10)))
    parameters = {name: posterior_intervals(idata.posterior[name].values) for name in PARAMETERS}
    with model:
        predictive = pm.sample_posterior_predictive(
            idata, var_names=["obs", "latent_train"], random_seed=config["predictive_seed"],
            progressbar=False, extend_inferencedata=False,
        )
    observed = frame.normalized_flux.to_numpy()
    ppc = np.asarray(predictive.posterior_predictive["obs"].values).reshape(-1, len(frame))
    latent = np.asarray(predictive.posterior_predictive["latent_train"].values).reshape(-1, len(frame))
    predicted_mean = latent.mean(axis=0)
    residual = observed - predicted_mean
    total_sd = np.sqrt(frame.normalized_flux_err.to_numpy()**2 + parameters["extra_sigma"]["mean"]**2)
    low, high = np.quantile(ppc, [.03, .97], axis=0)
    residual_metrics = {
        "posterior_predictive_interval_94_coverage_observed_points": float(np.mean((low <= observed) & (observed <= high))),
        "standardized_residual_std": float(np.std(residual / total_sd, ddof=1)),
        "rmse": float(np.sqrt(np.mean(residual**2))),
    }
    correlations = residual_correlations(frame, residual / total_sd)
    r = np.asarray(idata.posterior["r"].values).reshape(-1)
    scale = {"extra_sigma_to_measurement_sigma": parameters["extra_sigma"]["mean"] / float(frame.normalized_flux_err.median()),
             "radius_ratio_boundary_fraction": float(np.mean((r < .00349) | (r > .24751))),
             "radius_review_bounds": [.00349, .24751],
             "review_bound_semantics": "Inherited M5 astrophysical review range; NOT LogNormal prior support boundaries."}
    gate = evaluate_interpretation_gate(
        diagnostics=diagnostics, residual_metrics=residual_metrics,
        input_summary={"preprocessing_status": config["preprocessing_status"], "dataset_id": config["dataset_id"],
                       "segment_count": int(frame.segment_id.nunique()), "median_exposure_seconds": float(frame.exposure_time_seconds.median())},
        posterior_scale_checks=scale, posterior_predictive_status="created",
    )
    # Preserve the exact inherited M5 gate separately. The publication gate adds
    # a predeclared temporal check; it never rewrites historical M5 decisions.
    ppc_ok = gate["posterior_predictive_adequate"] and not correlations["flagged"]
    gates = {"provenance": True, "sampler": gate["sampler_converged"], "ppc": ppc_ok,
             "scientific": gate["scientifically_interpretable"] and ppc_ok}
    result = {
        "status": "completed" if gates["scientific"] else "rejected",
        "dataset_id": config["dataset_id"], "input_sha256": config["input_sha256"],
        "parameters": parameters, "diagnostics": diagnostics, "residual_metrics": residual_metrics,
        "residual_correlation": correlations, "scale_checks": scale,
        "inherited_m5_gate": gate, "gates": gates,
        "model": specification, "sampling": sampling, "environment": build_environment_summary(),
        "wall_seconds": time.perf_counter() - started,
        "trace_sha256": file_hash(output / "trace.nc"),
        "interpretation": "Conditional on frozen protocol and aggregate calibration; no automatic physical claim.",
    }
    curve = frame[["time", "phase", "segment_id"]].copy()
    curve["observed"] = observed
    curve["posterior_mean"] = predicted_mean
    curve["predictive_q03"], curve["predictive_q97"] = low, high
    curve["residual"] = residual
    curve.to_csv(output / "predictive_summary.csv", index=False)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    # Exclusive result reservation prevents accidental rerunning into an attempt.
    marker = args.output / "inference_started.json"
    with marker.open("x", encoding="utf-8") as handle:
        json.dump({"input_sha256": config["input_sha256"], "config_sha256": file_hash(args.config)}, handle)
    try:
        read_input(args.input, config)
        provenance_valid = True
        result = fit(args.input, config, args.output)
    except Exception as exc:
        import traceback
        provenance_valid = locals().get("provenance_valid", False)
        result = {"status": "failed", "error": repr(exc), "traceback": traceback.format_exc(),
                  "failure_stage": "inference" if provenance_valid else "input_validation",
                  "gates": {"provenance": provenance_valid, "sampler": False, "ppc": False, "scientific": False},
                  "gate_evaluation": {"provenance": "passed" if provenance_valid else "rejected", "sampler": "unavailable", "ppc": "unavailable", "scientific": "not_promotable"}}
    with (args.output / "result.json").open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
    print(json.dumps({"status": result["status"], "output": str(args.output)}), flush=True)
    if result["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
