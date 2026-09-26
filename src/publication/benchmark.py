"""Independent juliet adapter; no imports from the simulator or inference graph.

The adapter preserves row identity and groups only by *exact* exposure duration.
All nuisance parameters remain shared between those technical instrument groups.
Numerical engineering checks are not final posterior-comparison evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from publication.inference import file_hash, read_input

SECONDS_PER_DAY = 86400.0
BENCHMARK_VERSION = "juliet-2.2.10-adapter-v2"


def exposure_argument_seconds(physical_seconds: float, oversample: int) -> float:
    """Match M5's midpoint-Riemann nodes using batman's endpoint stencil.

    For n nodes, exoplanet order=0 uses (k+1/2)/n-1/2, while batman
    uses k/(n-1)-1/2. Scaling its *stencil span* by (n-1)/n produces
    identical nodes. Physical exposure metadata must not be altered.
    """
    if isinstance(oversample, bool) or not isinstance(oversample, int) or oversample < 1 or oversample % 2 != 1:
        raise ValueError("oversample must be a positive odd integer")
    if not np.isfinite(physical_seconds) or physical_seconds < 0:
        raise ValueError("physical exposure must be finite and nonnegative")
    return float(physical_seconds * (oversample - 1) / oversample)


def array_identity(frame: pd.DataFrame) -> str:
    """Hash exact ordered numerical inputs independently of CSV formatting."""
    digest = hashlib.sha256()
    for column in ("phase", "time", "normalized_flux", "normalized_flux_err", "exposure_time_seconds"):
        digest.update(column.encode() + b"\0")
        digest.update(np.asarray(frame[column], dtype="<f8").tobytes())
    digest.update(json.dumps(frame.segment_id.astype(str).tolist(), ensure_ascii=True, separators=(",", ":")).encode())
    return digest.hexdigest()


def exposure_groups(frame: pd.DataFrame) -> dict[str, np.ndarray]:
    """Never replace heterogeneous exposures by an undeclared median."""
    exposure = frame.exposure_time_seconds.to_numpy(dtype=float)
    if not len(exposure) or not np.isfinite(exposure).all() or (exposure <= 0).any():
        raise ValueError("input exposure must be positive and finite")
    values = np.unique(exposure)
    if len(values) > 32:
        raise ValueError("More than 32 exact exposure groups; an explicit new adapter contract is required")
    return {f"B{index:03d}": np.flatnonzero(exposure == value) for index, value in enumerate(values)}


def _prior(distribution: str, hyperparameters: Any) -> dict[str, Any]:
    return {"distribution": distribution, "hyperparameters": hyperparameters}


def juliet_arguments(frame: pd.DataFrame, config: Mapping[str, Any]) -> tuple[dict, dict]:
    """Construct a matched uniform-radius companion model, not historical M5.

    `config` contains declared inference assumptions only. The protected
    scientific_003 uses a different radius prior and is not reinterpreted here.
    """
    radius = config.get("radius_prior_uniform")
    if radius is None or config.get("radius_prior_median") is not None:
        raise ValueError("Benchmark requires an explicit uniform-radius companion prior")
    lower, upper = map(float, radius)
    if not 0 <= lower < upper < 1:
        raise ValueError("invalid radius prior support")
    for key in ("period_days", "baseline_prior_sigma", "t0_prior_sigma_days", "jitter_error_multiplier", "jitter_floor_fraction"):
        if not np.isfinite(config[key]) or config[key] <= 0:
            raise ValueError(f"{key} must be finite and positive")
    groups = exposure_groups(frame)
    instruments = list(groups)
    shared = "_".join(instruments)
    jitter_scale = max(float(frame.normalized_flux_err.median()) * config["jitter_error_multiplier"], config["jitter_floor_fraction"])
    priors = {
        "P_p1": _prior("fixed", config["period_days"]),
        "t0_p1": _prior("normal", [0.0, config["t0_prior_sigma_days"]]),
        "p_p1": _prior("uniform", [lower, upper]),
        "b_p1": _prior("uniform", [0.0, 1.0]),
        "a_p1": _prior("uniform", [2.0, 50.0]),
        "ecc_p1": _prior("fixed", 0.0),
        "omega_p1": _prior("fixed", 90.0),
        f"q1_{shared}": _prior("uniform", [0.0, 1.0]),
        f"q2_{shared}": _prior("uniform", [0.0, 1.0]),
        f"mdilution_{shared}": _prior("fixed", 1.0),
        f"mflux_{shared}": _prior("fixed", 0.0),
        f"theta0_{shared}": _prior("normal", [0.0, config["baseline_prior_sigma"]]),
        f"sigma_w_{shared}": _prior("truncatednormal", [0.0, jitter_scale * 1e6, 0.0, np.inf])
        if config["infer_jitter"] else _prior("fixed", 0.0),
    }
    arguments = {
        "priors": priors,
        "t_lc": {name: frame.iloc[index].phase.to_numpy(dtype=float) for name, index in groups.items()},
        "y_lc": {name: frame.iloc[index].normalized_flux.to_numpy(dtype=float) for name, index in groups.items()},
        "yerr_lc": {name: frame.iloc[index].normalized_flux_err.to_numpy(dtype=float) for name, index in groups.items()},
        "linear_regressors_lc": {name: np.ones((len(index), 1)) for name, index in groups.items()},
        "ld_laws": "quadratic", "lctimedef": "TDB",
    }
    oversample = config["oversample"]
    # Validate n even when integration is disabled, so malformed contracts fail.
    exposure_argument_seconds(1.0, oversample)
    if config["integrate_exposure"] and oversample > 1:
        arguments.update(
            lc_instrument_supersamp=instruments,
            lc_n_supersamp=[oversample] * len(instruments),
            lc_exptime_supersamp=[exposure_argument_seconds(float(frame.iloc[index[0]].exposure_time_seconds), oversample) / SECONDS_PER_DAY for index in groups.values()],
        )
    metadata = {
        "adapter_version": BENCHMARK_VERSION,
        "row_count": len(frame), "array_sha256": array_identity(frame),
        "row_indices_by_instrument": {name: index.tolist() for name, index in groups.items()},
        "physical_exposure_seconds_by_instrument": {name: float(frame.iloc[index[0]].exposure_time_seconds) for name, index in groups.items()},
        "shared_instrument_suffix": shared,
        "phase_unit": "day", "flux_unit": "relative fraction", "jitter_unit_in_juliet": "ppm",
        "time_transformation": "input phase days passed unchanged; fixed-period white likelihood",
        "exposure_quadrature": "M5 midpoint-Riemann matched by contracting batman stencil span (n-1)/n; no physical-exposure change",
        "jitter_prior_scale_fraction": jitter_scale,
        "baseline_mapping": "B=1+theta0; mflux=0, mdilution=1, constant regressor",
        "radius_prior": {"distribution": "Uniform", "support": [lower, upper]},
        "historical_baseline_comparison": "different radius prior; requires new companion run",
    }
    return arguments, metadata


def load_dataset(input_path: Path, config: Mapping[str, Any], *, out_folder: Path | None = None):
    """Validate identity before importing the independent numerical engine."""
    frame = read_input(input_path, dict(config))
    arguments, metadata = juliet_arguments(frame, config)
    if out_folder is not None:
        # Atomic reservation: two processes must never both own a run folder.
        out_folder.mkdir(parents=True, exist_ok=False)
        arguments["out_folder"] = str(out_folder)
    import juliet

    dataset = juliet.load(**arguments)
    metadata.update(dataset_id=config["dataset_id"], input_sha256=config["input_sha256"])
    return dataset, metadata


def posterior_parameters(samples: Mapping[str, Any], shared_suffix: str, period_days: float, *, infer_jitter: bool = True) -> dict[str, np.ndarray]:
    """Map external samples; preserve joint draw alignment and derived geometry."""
    mapped = {local: np.asarray(samples[external], dtype=float).reshape(-1)
              for local, external in {"r": "p_p1", "b": "b_p1", "a": "a_p1", "t0": "t0_p1",
                                      "q1": f"q1_{shared_suffix}", "q2": f"q2_{shared_suffix}"}.items()}
    mapped["baseline"] = 1 + np.asarray(samples[f"theta0_{shared_suffix}"], dtype=float).reshape(-1)
    mapped["extra_sigma"] = np.asarray(samples[f"sigma_w_{shared_suffix}"], dtype=float).reshape(-1) / 1e6 if infer_jitter else np.zeros_like(mapped["r"])
    if len({len(value) for value in mapped.values()}) != 1 or not all(np.isfinite(value).all() for value in mapped.values()):
        raise ValueError("External posterior samples are nonfinite or misaligned")
    r, b, a = mapped["r"], mapped["b"], mapped["a"]
    if not len(r) or (r <= 0).any() or (b < 0).any() or (b >= 1 + r).any() or (a <= 1 + r).any() or (mapped["extra_sigma"] < 0).any():
        raise ValueError("External posterior has invalid transit geometry or noise scale")
    mapped["depth"] = r**2
    mapped["full_duration"] = period_days / np.pi * np.arcsin(np.sqrt(((1 + r)**2 - b**2) / (a**2 - b**2)))
    return mapped


def compare_posterior_arrays(local: Mapping[str, np.ndarray], external: Mapping[str, np.ndarray]) -> dict:
    """Distribution-aware descriptive metrics; no iid KS p-values for MCMC draws."""
    from scipy.stats import ks_2samp, wasserstein_distance

    required = ("r", "depth", "b", "a", "t0", "full_duration", "extra_sigma")
    metrics = {}
    for name in required:
        left, right = np.asarray(local[name]).reshape(-1), np.asarray(external[name]).reshape(-1)
        if min(len(left), len(right)) < 2 or not np.isfinite(left).all() or not np.isfinite(right).all():
            raise ValueError("Comparison requires finite posterior arrays from both engines")
        combined = float(np.sqrt(np.var(left, ddof=1) + np.var(right, ddof=1)))
        if combined == 0:
            raise ValueError("Degenerate posterior scale cannot support standardized comparison")
        intervals = {}
        for level in (.5, .8, .94):
            llo, lhi = np.quantile(left, [(1-level)/2, (1+level)/2])
            rlo, rhi = np.quantile(right, [(1-level)/2, (1+level)/2])
            width = float(lhi - llo)
            if width <= 0:
                raise ValueError("Degenerate local interval width")
            union = float(max(lhi, rhi) - min(llo, rlo))
            intersection = max(0., float(min(lhi, rhi) - max(llo, rlo)))
            intervals[str(level)] = {"local": [float(llo), float(lhi)], "external": [float(rlo), float(rhi)],
                                     "overlap_jaccard": intersection / union,
                                     "width_ratio_external_local": float((rhi-rlo) / width)}
        center = float(abs(np.mean(left) - np.mean(right)) / combined)
        wasserstein = float(wasserstein_distance(left, right) / (combined / np.sqrt(2)))
        cdf = float(ks_2samp(left, right).statistic)
        width_ratio = intervals["0.94"]["width_ratio_external_local"]
        metrics[name] = {"standardized_mean_difference": center, "intervals": intervals,
                         "wasserstein1_over_pooled_sd": wasserstein, "empirical_cdf_distance": cdf,
                         "local_draws": len(left), "external_draws": len(right),
                         "material_discrepancy_flag": bool(center > 2 or intervals["0.94"]["overlap_jaccard"] == 0
                                                           or not .5 <= width_ratio <= 2 or wasserstein > 1 or cdf > .2)}
    return {"parameters": metrics, "interval_method": "equal_tailed_not_HDI",
            "interpretation": "Descriptive discrepancy triggers only. No iid KS p-values, equivalence test or automatic promotion. Check both engine diagnostics, contract and Monte Carlo precision separately."}


def batman_flux(frame: pd.DataFrame, parameters: Mapping[str, float], period_days: float, *, oversample: int, integrate_exposure: bool = True) -> np.ndarray:
    """Independent numerical forward check only; does not fit/read ground truth."""
    import batman

    params = batman.TransitParams()
    params.t0, params.per = parameters["t0"], period_days
    params.rp, params.a = parameters["r"], parameters["a"]
    params.inc = float(np.degrees(np.arccos(parameters["b"] / params.a)))
    params.ecc, params.w, params.limb_dark = 0.0, 90.0, "quadratic"
    root = np.sqrt(parameters["q1"])
    params.u = [2 * root * parameters["q2"], root * (1 - 2 * parameters["q2"])]
    result = np.empty(len(frame))
    for positions in exposure_groups(frame).values():
        exposure = float(frame.iloc[positions[0]].exposure_time_seconds)
        span = exposure_argument_seconds(exposure, oversample) / SECONDS_PER_DAY if integrate_exposure else 0.0
        model = batman.TransitModel(params, frame.iloc[positions].phase.to_numpy(),
                                   supersample_factor=oversample if integrate_exposure else 1,
                                   exp_time=span, nthreads=1)
        result[positions] = model.light_curve(params) + parameters.get("baseline", 1.0) - 1.0
    return result


def numeric_fixture_check(fixture_path: Path) -> dict:
    """Run independent numerical fixtures; never call a posterior sampler."""
    import importlib.metadata

    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    outcomes = []
    for case in fixture["cases"]:
        frame = pd.DataFrame({"phase": case["phase_days"], "exposure_time_seconds": case["exposure_seconds"]})
        actual = batman_flux(frame, case["parameters"], case["period_days"], oversample=case["oversample"])
        expected = np.asarray(case["expected_flux"], dtype=float)
        error = float(np.max(np.abs(actual - expected)))
        outcomes.append({"case_id": case["case_id"], "max_abs_flux_difference": error,
                         "tolerance_fraction": fixture["tolerance_fraction"], "passed": error <= fixture["tolerance_fraction"]})
    contract = installed_contract_check()
    return {"status": "passed" if all(case["passed"] for case in outcomes) and contract["passed"] else "failed",
            "evidence_class": "engineering_numeric_check_not_final_inference",
            "fixture_sha256": file_hash(fixture_path), "adapter_version": BENCHMARK_VERSION,
            "versions": {name: importlib.metadata.version(name) for name in ("juliet", "batman-package", "numpy", "scipy")},
            "cases": outcomes, "installed_contract": contract}


def installed_contract_check() -> dict:
    """Verify installed juliet wiring against analytic expectations, without fitting."""
    import inspect

    import dynesty
    import juliet
    from scipy.stats import halfnorm

    phase = np.linspace(-.12, .12, 60)
    frame = pd.DataFrame({"phase": phase, "time": phase + 5,
                          "normalized_flux": np.ones(60),
                          "normalized_flux_err": np.linspace(.0001, .0003, 60),
                          "exposure_time_seconds": np.tile([60., 1800.], 30),
                          "segment_id": ["engineering"] * 60})
    physical = {"r": .09, "b": .7, "a": 8., "t0": .001,
                "q1": .25, "q2": .3, "baseline": 1.002}
    expected_flux = batman_flux(frame, physical, 2., oversample=15)
    frame["normalized_flux"] = expected_flux + .0002 * np.sin(np.arange(len(frame)))
    config = {"period_days": 2., "radius_prior_uniform": [.001, .2],
              "baseline_prior_sigma": .02, "t0_prior_sigma_days": .025,
              "jitter_error_multiplier": 5., "jitter_floor_fraction": .0005,
              "infer_jitter": True, "integrate_exposure": True, "oversample": 15}
    arguments, metadata = juliet_arguments(frame, config)
    data = juliet.load(**arguments)
    model = juliet.model(data, modeltype="lc", log_like_calc=True)
    suffix = metadata["shared_instrument_suffix"]
    parameters = {name: prior["hyperparameters"] for name, prior in arguments["priors"].items()
                  if prior["distribution"] == "fixed"}
    parameters.update(p_p1=physical["r"], b_p1=physical["b"], a_p1=physical["a"], t0_p1=physical["t0"])
    parameters.update({f"q1_{suffix}": physical["q1"], f"q2_{suffix}": physical["q2"],
                       f"theta0_{suffix}": physical["baseline"] - 1, f"sigma_w_{suffix}": 150.})
    model.generate(parameters)
    actual_flux = np.empty(len(frame))
    for name, positions in metadata["row_indices_by_instrument"].items():
        actual_flux[positions] = model.model[name]["deterministic"]
    flux_error = float(np.max(np.abs(expected_flux - actual_flux)))
    variance = frame.normalized_flux_err.to_numpy()**2 + .00015**2
    residual = frame.normalized_flux.to_numpy() - expected_flux
    expected_loglike = float(-.5 * np.sum(np.log(2 * np.pi * variance) + residual**2 / variance))
    actual_loglike = float(model.get_log_likelihood(parameters))
    likelihood_error = abs(actual_loglike - expected_loglike)
    quantiles = np.array([1e-8, .01, .5, .94, .999999])
    scale = metadata["jitter_prior_scale_fraction"] * 1e6
    prior_actual = np.array([juliet.utils.transform_truncated_normal(q, [0., scale, 0., np.inf]) for q in quantiles])
    prior_expected = halfnorm.ppf(quantiles, scale=scale)
    prior_error = float(np.max(np.abs(prior_actual - prior_expected)))
    # Extreme-tail inverse CDFs amplify rounding by 1/pdf(x). A fixed ppm
    # tolerance is not uniformly meaningful; verify the defining CDF identity
    # and its floating-point-conditioned quantile bound. V1 failure is retained.
    cdf_tolerance = 32 * np.finfo(float).eps
    cdf_error = float(np.max(np.abs(halfnorm.cdf(prior_actual, scale=scale) - quantiles)))
    quantile_bound = cdf_tolerance / halfnorm.pdf(prior_expected, scale=scale)
    conditioned_prior_ok = bool(np.all(np.abs(prior_actual - prior_expected) <= quantile_bound))
    incorrect_prior = np.array([juliet.utils.transform_truncated_normal(q, [0., 1.01 * scale, 0., np.inf]) for q in quantiles])
    wrong_scale_rejected = bool(np.max(np.abs(halfnorm.cdf(incorrect_prior, scale=scale) - quantiles)) > cdf_tolerance)
    return {"passed": bool(model.modelOK and flux_error <= 1e-12 and likelihood_error <= 1e-7 and cdf_error <= cdf_tolerance and conditioned_prior_ok and wrong_scale_rejected),
            "model_ok": bool(model.modelOK), "rows": len(frame), "exposure_groups": 2,
            "shared_nuisances": True, "max_abs_flux_error": flux_error,
            "flux_tolerance": 1e-12, "absolute_log_likelihood_error": likelihood_error,
            "likelihood_tolerance": 1e-7, "max_halfnormal_quantile_error_ppm": prior_error,
            "half_normal_cdf_error": cdf_error, "half_normal_cdf_tolerance": cdf_tolerance,
            "half_normal_quantile_bounds_ppm": quantile_bound.tolist(),
            "conditioned_quantile_bound_passed": conditioned_prior_ok,
            "mis_scaled_prior_negative_control_rejected": wrong_scale_rejected,
            "half_normal_quantiles_tested": quantiles.tolist(),
            "dynesty_accepts_rstate": "rstate" in inspect.signature(dynesty.NestedSampler).parameters,
            "sampler_executed": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--numeric-fixture", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = numeric_fixture_check(args.numeric_fixture)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2, allow_nan=False))
    if result["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
