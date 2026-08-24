"""Pure contracts for M5 paths, metadata, and interpretation decisions."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from project_config import M5_MODEL_VERSION, TargetConfig


@dataclass(frozen=True, slots=True)
class PriorProfile:
    name: str
    radius_ratio_log_sigma: float
    jitter_error_multiplier: float
    jitter_floor_fraction: float
    purpose: str


PRIOR_PROFILES: dict[str, PriorProfile] = {
    "catalog_tighter": PriorProfile(
        name="catalog_tighter",
        radius_ratio_log_sigma=0.25,
        jitter_error_multiplier=3.0,
        jitter_floor_fraction=3e-4,
        purpose="Sensitivity bound with a narrower catalog-centered radius prior.",
    ),
    "baseline": PriorProfile(
        name="baseline",
        radius_ratio_log_sigma=0.5,
        jitter_error_multiplier=5.0,
        jitter_floor_fraction=5e-4,
        purpose="Default weakly informative, catalog-justified physical scale.",
    ),
    "weak": PriorProfile(
        name="weak",
        radius_ratio_log_sigma=0.9,
        jitter_error_multiplier=10.0,
        jitter_floor_fraction=1e-3,
        purpose="Sensitivity bound with broader radius and jitter priors.",
    ),
}


def get_prior_profile(name: str) -> PriorProfile:
    try:
        return PRIOR_PROFILES[name]
    except KeyError as exc:
        raise ValueError(
            f"Unknown prior profile {name!r}; expected one of {sorted(PRIOR_PROFILES)}"
        ) from exc


@dataclass(frozen=True, slots=True)
class M5Paths:
    project_root: Path
    target: TargetConfig
    run_id: str
    source_gold: Path
    model_dir: Path
    table_dir: Path
    figure_dir: Path
    report_path: Path
    notebook_path: Path
    docs_dir: Path
    trace_path: Path
    model_config_path: Path
    inference_summary_path: Path
    modeling_input_path: Path
    posterior_summary_path: Path
    derived_summary_path: Path
    physical_curve_summary_path: Path
    posterior_predictive_summary_path: Path
    residual_summary_path: Path
    prior_predictive_summary_path: Path
    m1_derived_path: Path
    m1_posterior_summary_path: Path
    m2_curve_path: Path


def build_m5_paths(root: Path, target: TargetConfig, run_id: str) -> M5Paths:
    """Generate target-safe and run-specific artifact paths."""

    root = root.resolve()
    family = "bayesian_physical_transit"
    model_dir = root / "models" / family / target.planet_slug / "runs" / run_id
    table_dir = root / "tables" / family / target.planet_slug / "runs" / run_id
    figure_dir = root / "figures" / family / target.planet_slug / "runs" / run_id
    return M5Paths(
        project_root=root,
        target=target,
        run_id=run_id,
        source_gold=root / target.source_gold_path,
        model_dir=model_dir,
        table_dir=table_dir,
        figure_dir=figure_dir,
        report_path=root / "reports" / f"{family}_{target.planet_slug}_{run_id}_report.md",
        notebook_path=root / "notebooks" / "07_bayesian_physical_transit.ipynb",
        docs_dir=root / "docs" / "modeling" / family,
        trace_path=model_dir / "trace.nc",
        model_config_path=model_dir / "model_config.json",
        inference_summary_path=model_dir / "inference_data_summary.json",
        modeling_input_path=table_dir / "modeling_input_physical.csv",
        posterior_summary_path=table_dir / "posterior_summary.csv",
        derived_summary_path=table_dir / "derived_parameters_summary.csv",
        physical_curve_summary_path=table_dir / "physical_curve_summary.csv",
        posterior_predictive_summary_path=table_dir / "posterior_predictive_summary.csv",
        residual_summary_path=table_dir / "residual_summary.csv",
        prior_predictive_summary_path=table_dir / "prior_predictive_summary.csv",
        m1_derived_path=(
            root
            / "tables"
            / "bayesian_baseline"
            / target.planet_slug
            / "runs"
            / "002_nuts_robust"
            / "derived_parameters_summary.csv"
        ),
        m1_posterior_summary_path=(
            root
            / "tables"
            / "bayesian_baseline"
            / target.planet_slug
            / "runs"
            / "002_nuts_robust"
            / "posterior_summary.csv"
        ),
        m2_curve_path=(
            root
            / "tables"
            / "bayesian_predictive_phase_regression"
            / target.planet_slug
            / "predictive_curve_summary.csv"
        ),
    )


def jitter_prior_scale(
    measurement_sigma_median: float,
    profile: PriorProfile | None = None,
) -> float:
    """Set a recorded weakly informative jitter scale in normalized flux."""

    selected = profile or PRIOR_PROFILES["baseline"]
    return max(
        selected.jitter_error_multiplier * measurement_sigma_median,
        selected.jitter_floor_fraction,
    )


def physical_model_spec(
    target: TargetConfig,
    median_exposure_seconds: float,
    measurement_sigma_median: float | None = None,
    prior_profile: PriorProfile | None = None,
) -> dict[str, Any]:
    """Machine-readable description of the actual M5 forward model."""

    selected_profile = prior_profile or PRIOR_PROFILES["baseline"]
    return {
        "model_version": M5_MODEL_VERSION,
        "family": "quadratic_limb_darkened_keplerian_transit",
        "implementation": "exoplanet.LimbDarkLightCurve + exoplanet.KeplerianOrbit",
        "orbit": {
            "period_days": target.orbital_period_days,
            "eccentricity": 0.0,
            "period_source": "authoritative target configuration",
        },
        "limb_darkening": {
            "law": "quadratic",
            "parameterization": "Kipping triangular q1/q2 transformed to u1/u2",
            "parameters": ["u[0]", "u[1]"],
            "sampling_parameters": ["q1", "q2"],
        },
        "priors": {
            "profile": {
                "name": selected_profile.name,
                "purpose": selected_profile.purpose,
            },
            "baseline": {"distribution": "Normal", "mu": 1.0, "sigma": 0.02},
            "r": {
                "distribution": "LogNormal",
                "mu_log": math.log(target.reference_radius_ratio_from_depth),
                "sigma_log": selected_profile.radius_ratio_log_sigma,
                "center_source": "sqrt(authoritative catalog transit_depth_fraction)",
            },
            "b": {"distribution": "Uniform", "lower": 0.0, "upper": 1.0},
            "a": {"distribution": "Uniform", "lower": 2.0, "upper": 50.0},
            "t0_days": {
                "distribution": "Normal",
                "mu": 0.0,
                "sigma": target.transit_duration_days / 4.0,
            },
            "q1": {"distribution": "Uniform", "lower": 0.0, "upper": 1.0},
            "q2": {"distribution": "Uniform", "lower": 0.0, "upper": 1.0},
            "extra_sigma": {
                "distribution": "HalfNormal",
                "sigma": (
                    jitter_prior_scale(measurement_sigma_median, selected_profile)
                    if measurement_sigma_median is not None
                    else None
                ),
                "scale_rule": (
                    f"max({selected_profile.jitter_error_multiplier} * median normalized "
                    f"flux error, {selected_profile.jitter_floor_fraction})"
                ),
            },
        },
        "likelihood": {
            "distribution": "Normal",
            "mean": "limb-darkened exposure-integrated transit + baseline",
            "sigma": "sqrt(normalized_flux_err**2 + extra_sigma**2)",
            "conditional_independence": True,
        },
        "exposure_integration": {
            "enabled": median_exposure_seconds > 0,
            "median_exposure_seconds": median_exposure_seconds,
            "oversample": target.exposure_oversample,
            "method": "exoplanet get_light_curve(texp=..., oversample=...)",
        },
        "derived_parameters": {
            "depth": "r**2 (geometric reference; limb-darkened observed depth differs)",
            "rp_rs": "r",
            "full_duration_days": (
                "period/pi * asin(sqrt((1+r)**2-b**2) / sqrt(a**2-b**2))"
            ),
        },
    }


def evaluate_interpretation_gate(
    *,
    diagnostics: dict[str, Any],
    residual_metrics: dict[str, Any],
    input_summary: dict[str, Any],
    posterior_scale_checks: dict[str, Any],
    posterior_predictive_status: str,
) -> dict[str, Any]:
    """Keep sampler, predictive, and scientific validity separate."""

    reasons: dict[str, list[str]] = {"sampler": [], "posterior_predictive": [], "scientific": []}

    max_r_hat = float(diagnostics.get("max_r_hat", math.nan))
    min_ess = float(diagnostics.get("min_ess", math.nan))
    divergences = int(diagnostics.get("divergences", -1))
    bfmi = diagnostics.get("bfmi_min")
    if not math.isfinite(max_r_hat) or max_r_hat > 1.01:
        reasons["sampler"].append(f"max_r_hat={max_r_hat!r} exceeds 1.01")
    if not math.isfinite(min_ess) or min_ess < 400:
        reasons["sampler"].append(f"min_ess={min_ess!r} is below 400")
    if divergences != 0:
        reasons["sampler"].append(f"divergences={divergences} is not zero")
    if bfmi is None or not math.isfinite(float(bfmi)) or float(bfmi) < 0.30:
        reasons["sampler"].append(f"bfmi_min={bfmi!r} is unavailable or below 0.30")

    coverage = float(
        residual_metrics.get("posterior_predictive_interval_94_coverage_observed_points", math.nan)
    )
    standardized_std = float(residual_metrics.get("standardized_residual_std", math.nan))
    if posterior_predictive_status != "created":
        reasons["posterior_predictive"].append(
            f"posterior_predictive_status={posterior_predictive_status!r}"
        )
    if not math.isfinite(coverage) or not 0.80 <= coverage <= 0.99:
        reasons["posterior_predictive"].append(f"94% coverage={coverage!r} is outside [0.80, 0.99]")
    if not math.isfinite(standardized_std) or not 0.5 <= standardized_std <= 2.0:
        reasons["posterior_predictive"].append(
            f"standardized residual std={standardized_std!r} is outside [0.5, 2.0]"
        )

    if input_summary.get("preprocessing_status") != "segment_normalized":
        reasons["scientific"].append("Gold input is not certified as segment_normalized")
    if not input_summary.get("dataset_id"):
        reasons["scientific"].append("dataset_id is missing")
    if int(input_summary.get("segment_count", 0)) < 1:
        reasons["scientific"].append("no traceable light-curve segment is present")
    if float(input_summary.get("median_exposure_seconds", 0.0)) <= 0:
        reasons["scientific"].append("exposure time is missing")

    jitter_ratio = float(posterior_scale_checks.get("extra_sigma_to_measurement_sigma", math.inf))
    boundary_fraction = float(posterior_scale_checks.get("radius_ratio_boundary_fraction", math.inf))
    if not math.isfinite(jitter_ratio) or jitter_ratio > 20.0:
        reasons["scientific"].append(
            f"extra_sigma/measurement_sigma={jitter_ratio!r} exceeds review threshold 20"
        )
    if not math.isfinite(boundary_fraction) or boundary_fraction > 0.05:
        reasons["scientific"].append(
            f"radius-ratio boundary fraction={boundary_fraction!r} exceeds 0.05"
        )

    sampler_ok = not reasons["sampler"]
    posterior_predictive_ok = not reasons["posterior_predictive"]
    scientific_ok = not reasons["scientific"]
    all_reasons = [reason for group in reasons.values() for reason in group]
    return {
        "sampler_converged": sampler_ok,
        "posterior_predictive_adequate": posterior_predictive_ok,
        "scientifically_interpretable": sampler_ok and posterior_predictive_ok and scientific_ok,
        "rejection_reasons": all_reasons,
        "component_reasons": reasons,
        "thresholds": {
            "max_r_hat": 1.01,
            "min_ess": 400,
            "divergences": 0,
            "min_bfmi": 0.30,
            "max_jitter_ratio": 20.0,
            "max_radius_ratio_boundary_fraction": 0.05,
        },
    }


def validate_formal_comparison_contract(configs: list[dict[str, Any]]) -> dict[str, Any]:
    """Decide whether LOO/WAIC compares the same statistical prediction task."""

    reasons: list[str] = []
    if len(configs) < 2:
        reasons.append("at least two model runs are required")
    dataset_ids = {
        str(config.get("input_summary", {}).get("dataset_id", "")) for config in configs
    }
    input_hashes = {
        str(config.get("input_summary", {}).get("modeling_input_sha256", ""))
        for config in configs
    }
    likelihoods = {
        json.dumps(
            config.get("model", {}).get("likelihood", {}),
            sort_keys=True,
            separators=(",", ":"),
        )
        for config in configs
    }
    if "" in dataset_ids or len(dataset_ids) != 1:
        reasons.append(f"dataset IDs differ or are missing: {sorted(dataset_ids)!r}")
    if "" in input_hashes or len(input_hashes) != 1:
        reasons.append("modeling-input checksums differ or are missing")
    if len(likelihoods) != 1:
        reasons.append("likelihood definitions differ")
    for config in configs:
        run_id = str(config.get("run_id", "unknown"))
        if not config.get("log_likelihood", {}).get("available", False):
            reasons.append(f"run {run_id} has no pointwise log likelihood")
        if not config.get("interpretation_gate", {}).get("scientifically_interpretable", False):
            reasons.append(f"run {run_id} did not pass the scientific interpretation gate")
    return {
        "formal_comparison_valid": not reasons,
        "rejection_reasons": reasons,
        "allowed_metrics": ["LOO", "WAIC", "ELPD"] if not reasons else [],
        "always_separate_metrics": ["RMSE", "MAE", "heuristic structural score"],
    }
