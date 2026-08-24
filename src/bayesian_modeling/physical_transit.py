"""Shared, target-safe M5 physical-transit workflow.

The model consumes only Gold datasets certified as segment-normalized.  It
uses one authoritative target configuration, a quadratic limb-darkened
Keplerian transit, exposure-time integration, NUTS, pointwise log likelihood,
posterior predictive checks, and explicit interpretation gates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MPLCONFIGDIR = Path("/tmp") / "matplotlib-cache"
MPLCONFIGDIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPLCONFIGDIR))
PYTENSOR_CACHE = Path("/tmp") / "pytensor-cache-m5-physical"
PYTENSOR_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("PYTENSOR_FLAGS", f"base_compiledir={PYTENSOR_CACHE}")

import arviz as az  # noqa: E402
import exoplanet as xo  # noqa: E402
import matplotlib  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pymc as pm  # noqa: E402
import pytensor  # noqa: E402
import pytensor.tensor as pt  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from bayesian_modeling.contracts import (  # noqa: E402
    M5Paths,
    PriorProfile,
    build_m5_paths,
    evaluate_interpretation_gate,
    get_prior_profile,
    jitter_prior_scale,
    physical_model_spec,
)
from project_config import (  # noqa: E402
    DEFAULT_TARGET_SLUG,
    M5_DEFAULT_RUN_ID,
    TargetConfig,
    get_target,
)

MODEL_NAME = "M5_bayesian_physical_transit"
PREDICTION_GRID_POINTS = 300
MAX_MODELING_POINTS_PER_SEGMENT = 1000
RANDOM_SEED = 42
HDI_PROB = 0.94
HDI_LOW_Q = 0.03
HDI_HIGH_Q = 0.97
DEFAULT_SAMPLING: dict[str, Any] = {
    "sampler": "NUTS",
    "draws": 2000,
    "tune": 2000,
    "chains": 4,
    "cores": 4,
    "target_accept": 0.90,
    "random_seed": RANDOM_SEED,
}
SUMMARY_VAR_NAMES = [
    "baseline",
    "r",
    "b",
    "a",
    "t0",
    "q1",
    "q2",
    "u",
    "extra_sigma",
    "depth",
    "rp_rs",
    "full_duration",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_project_root(project_root: Path | None = None) -> Path:
    if project_root is not None:
        return project_root.resolve()
    candidate = Path(__file__).resolve().parents[2]
    if (candidate / "data" / "gold").exists():
        return candidate
    cwd = Path.cwd().resolve()
    if (cwd / "data" / "gold").exists():
        return cwd
    raise FileNotFoundError("Could not locate project root containing data/gold.")


def build_paths(
    target: TargetConfig,
    run_id: str = M5_DEFAULT_RUN_ID,
    project_root: Path | None = None,
) -> M5Paths:
    return build_m5_paths(resolve_project_root(project_root), target, run_id)


def ensure_directories(paths: M5Paths) -> None:
    for directory in {
        paths.model_dir,
        paths.table_dir,
        paths.figure_dir,
        paths.report_path.parent,
        paths.docs_dir,
    }:
        directory.mkdir(parents=True, exist_ok=True)


def relative_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_gold_transit_window(paths: M5Paths) -> pd.DataFrame:
    if not paths.source_gold.exists():
        raise FileNotFoundError(f"Missing Gold input: {paths.source_gold}")
    frame = pd.read_csv(paths.source_gold, low_memory=False)
    for column in ["phase", "flux", "flux_err", "quality", "time", "exposure_time_seconds"]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def stratified_phase_thin(
    frame: pd.DataFrame,
    *,
    max_points_per_segment: int = MAX_MODELING_POINTS_PER_SEGMENT,
) -> pd.DataFrame:
    """Select reproducible, phase-uniform rows independently per segment."""

    if max_points_per_segment < 2:
        raise ValueError("max_points_per_segment must be at least 2")
    selected: list[pd.DataFrame] = []
    for _, segment in frame.groupby("segment_id", sort=True, dropna=False):
        segment = segment.sort_values(["phase", "time"], kind="mergesort")
        if len(segment) > max_points_per_segment:
            positions = np.linspace(0, len(segment) - 1, max_points_per_segment)
            indexes = np.unique(np.rint(positions).astype(int))
            segment = segment.iloc[indexes]
        selected.append(segment)
    return pd.concat(selected, ignore_index=True).sort_values("phase").reset_index(drop=True)


def prepare_modeling_input(
    dataframe: pd.DataFrame,
    paths: M5Paths,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    target = paths.target
    required = {
        "planet_name",
        "host_star",
        "mission",
        "phase",
        "flux",
        "flux_err",
        "segment_id",
        "source_fits_file",
        "exposure_time_seconds",
        "preprocessing_status",
        "dataset_id",
    }
    missing = sorted(required.difference(dataframe.columns))
    if missing:
        raise ValueError(f"Missing required columns in Gold input: {missing}")

    prepared = dataframe.copy()
    for identity_column, expected in {
        "planet_name": target.planet_name,
        "host_star": target.host_star,
        "mission": target.mission,
    }.items():
        observed = set(prepared[identity_column].dropna().astype(str))
        if observed != {expected}:
            raise ValueError(
                f"Target identity mismatch for {identity_column}: expected {expected!r}; "
                f"observed {sorted(observed)!r}"
            )
    preprocessing = set(prepared["preprocessing_status"].dropna().astype(str))
    if preprocessing != {"segment_normalized"}:
        raise ValueError(
            "M5 requires preprocessing_status='segment_normalized'; "
            f"observed {sorted(preprocessing)!r}"
        )
    dataset_ids = set(prepared["dataset_id"].dropna().astype(str))
    if len(dataset_ids) != 1:
        raise ValueError(f"M5 requires exactly one dataset_id; observed {sorted(dataset_ids)!r}")

    counts: dict[str, int] = {"initial_rows_gold_window": len(prepared)}
    prepared = prepared.loc[prepared["phase"].abs() <= target.phase_window_days].copy()
    counts["rows_after_phase_filter"] = len(prepared)
    if "quality" in prepared.columns:
        prepared = prepared.loc[prepared["quality"].fillna(0) == 0].copy()
    counts["rows_after_quality_filter"] = len(prepared)
    prepared = prepared.dropna(
        subset=["phase", "flux", "flux_err", "exposure_time_seconds"]
    ).copy()
    counts["rows_after_missing_filter"] = len(prepared)
    prepared = prepared.loc[
        (prepared["flux_err"] > 0) & (prepared["exposure_time_seconds"] > 0)
    ].copy()
    counts["rows_after_positive_scale_filter"] = len(prepared)
    if prepared.empty:
        raise ValueError("No valid observations remain after M5 input validation.")
    rows_before_stratified_thinning = len(prepared)
    prepared = stratified_phase_thin(prepared)
    counts["rows_before_stratified_phase_thinning"] = rows_before_stratified_thinning
    counts["rows_after_stratified_phase_thinning"] = len(prepared)

    prepared["normalized_flux"] = prepared["flux"]
    prepared["normalized_flux_err"] = prepared["flux_err"]
    prepared["is_baseline_region"] = prepared["phase"].abs().between(
        target.baseline_min_abs_phase_days,
        target.baseline_max_abs_phase_days,
    )
    prepared["source_gold_path"] = target.source_gold_path.as_posix()
    ordered_columns = [
        "planet_name",
        "host_star",
        "mission",
        "dataset_id",
        "segment_id",
        "quarter",
        "sector",
        "campaign",
        "source_fits_file",
        "source_fits_sha256",
        "cadence_type",
        "exposure_time_seconds",
        "preprocessing_status",
        "segment_normalization_method",
        "time",
        "phase",
        "flux",
        "flux_err",
        "normalized_flux",
        "normalized_flux_err",
        "quality",
        "is_baseline_region",
        "source_gold_path",
    ]
    prepared = prepared.loc[
        :, [column for column in ordered_columns if column in prepared.columns]
    ].sort_values("phase").reset_index(drop=True)
    prepared.to_csv(paths.modeling_input_path, index=False)

    metadata: dict[str, Any] = {
        **counts,
        "rows_used": len(prepared),
        "sampling_of_gold_rows": {
            "method": "deterministic phase-uniform selection within each segment",
            "max_points_per_segment": MAX_MODELING_POINTS_PER_SEGMENT,
            "preserves": ["segment_id", "source_fits_file", "exposure_time_seconds"],
        },
        "dataset_id": next(iter(dataset_ids)),
        "preprocessing_status": "segment_normalized",
        "segment_count": int(prepared["segment_id"].nunique()),
        "source_fits_count": int(prepared["source_fits_file"].nunique()),
        "median_exposure_seconds": float(prepared["exposure_time_seconds"].median()),
        "baseline_region_count": int(prepared["is_baseline_region"].sum()),
        "phase_min_days": float(prepared["phase"].min()),
        "phase_max_days": float(prepared["phase"].max()),
        "normalized_flux_median": float(prepared["normalized_flux"].median()),
        "normalized_flux_mean": float(prepared["normalized_flux"].mean()),
        "normalized_flux_std": float(prepared["normalized_flux"].std(ddof=1)),
        "normalized_flux_err_median": float(prepared["normalized_flux_err"].median()),
    }
    return prepared, metadata


def build_model(
    prepared: pd.DataFrame,
    phase_grid: np.ndarray,
    target: TargetConfig,
    prior_profile: PriorProfile | None = None,
) -> pm.Model:
    selected_profile = prior_profile or get_prior_profile("baseline")
    phase = prepared["phase"].to_numpy(dtype=float)
    observed = prepared["normalized_flux"].to_numpy(dtype=float)
    sigma_observed = prepared["normalized_flux_err"].to_numpy(dtype=float)
    exposure_days = prepared["exposure_time_seconds"].to_numpy(dtype=float) / 86_400.0
    grid_exposure_days = float(np.median(exposure_days))
    coords = {"observation": np.arange(len(prepared)), "grid": np.arange(len(phase_grid))}

    with pm.Model(coords=coords) as model:
        baseline = pm.Normal("baseline", mu=1.0, sigma=0.02)
        radius_ratio = pm.LogNormal(
            "r",
            mu=np.log(target.reference_radius_ratio_from_depth),
            sigma=selected_profile.radius_ratio_log_sigma,
        )
        impact_parameter = pm.Uniform("b", lower=0.0, upper=1.0)
        scaled_semimajor_axis = pm.Uniform("a", lower=2.0, upper=50.0)
        transit_center = pm.Normal(
            "t0", mu=0.0, sigma=target.transit_duration_days / 4.0
        )
        # Kipping's triangular parameterization: uniform q1/q2 maps to the
        # physically allowed quadratic limb-darkening region.
        q1 = pm.Uniform("q1", lower=0.0, upper=1.0)
        q2 = pm.Uniform("q2", lower=0.0, upper=1.0)
        sqrt_q1 = pt.sqrt(q1)
        limb_darkening = pm.Deterministic(
            "u",
            pt.stack([2.0 * sqrt_q1 * q2, sqrt_q1 * (1.0 - 2.0 * q2)]),
        )
        orbit = xo.orbits.KeplerianOrbit(
            period=target.orbital_period_days,
            t0=transit_center,
            b=impact_parameter,
            a=scaled_semimajor_axis,
        )
        light_curve = xo.LimbDarkLightCurve(limb_darkening[0], limb_darkening[1])
        latent_train = pm.Deterministic(
            "latent_train",
            baseline
            + light_curve.get_light_curve(
                orbit=orbit,
                r=radius_ratio,
                t=phase,
                texp=exposure_days,
                oversample=target.exposure_oversample,
            ).flatten(),
            dims="observation",
        )
        pm.Deterministic(
            "latent_grid",
            baseline
            + light_curve.get_light_curve(
                orbit=orbit,
                r=radius_ratio,
                t=phase_grid,
                texp=grid_exposure_days,
                oversample=target.exposure_oversample,
            ).flatten(),
            dims="grid",
        )
        extra_sigma = pm.HalfNormal(
            "extra_sigma",
            sigma=jitter_prior_scale(float(np.median(sigma_observed)), selected_profile),
        )
        sigma_effective = pm.math.sqrt(sigma_observed**2 + extra_sigma**2)
        pm.Normal(
            "obs",
            mu=latent_train,
            sigma=sigma_effective,
            observed=observed,
            dims="observation",
        )
        pm.Deterministic("depth", radius_ratio**2)
        pm.Deterministic("rp_rs", radius_ratio)
        duration_argument = pt.sqrt(
            (1.0 + radius_ratio) ** 2 - impact_parameter**2
        ) / pt.sqrt(scaled_semimajor_axis**2 - impact_parameter**2)
        pm.Deterministic(
            "full_duration",
            (target.orbital_period_days / np.pi)
            * pt.arcsin(pt.clip(duration_argument, 0.0, 1.0)),
        )
    return model


def count_divergences(idata: az.InferenceData) -> int:
    if not hasattr(idata, "sample_stats") or "diverging" not in idata.sample_stats:
        return 0
    return int(np.asarray(idata.sample_stats["diverging"].values).sum())


def _draw(model: pm.Model, config: dict[str, Any]) -> az.InferenceData:
    with model:
        return pm.sample(
            draws=int(config["draws"]),
            tune=int(config["tune"]),
            chains=int(config["chains"]),
            cores=int(config["cores"]),
            target_accept=float(config["target_accept"]),
            random_seed=int(config["random_seed"]),
            init="jitter+adapt_diag",
            return_inferencedata=True,
            progressbar=True,
        )


def sample_nuts(
    model: pm.Model,
    sampling_overrides: dict[str, Any] | None = None,
) -> tuple[az.InferenceData, dict[str, Any]]:
    config = {**DEFAULT_SAMPLING, **(sampling_overrides or {})}
    config["cores"] = min(int(config["cores"]), os.cpu_count() or 1)
    config["retry_history"] = []
    idata = _draw(model, config)
    for target_accept in (0.95, 0.99):
        divergences = count_divergences(idata)
        if divergences == 0:
            break
        if target_accept <= float(config["target_accept"]):
            continue
        config["retry_history"].append(
            {
                "reason": f"{divergences} divergences",
                "previous_target_accept": config["target_accept"],
                "new_target_accept": target_accept,
            }
        )
        config["target_accept"] = target_accept
        idata = _draw(model, config)
    with model:
        idata = pm.compute_log_likelihood(
            idata,
            model=model,
            extend_inferencedata=True,
            progressbar=True,
        )
    return idata, config


def sample_posterior_predictive(
    model: pm.Model,
    idata: az.InferenceData,
) -> tuple[az.InferenceData, str]:
    try:
        with model:
            idata = pm.sample_posterior_predictive(
                idata,
                var_names=["obs"],
                random_seed=RANDOM_SEED,
                extend_inferencedata=True,
                progressbar=True,
            )
        return idata, "created"
    except Exception as exc:  # pragma: no cover - retained in artifact for traceability
        return idata, f"failed: {exc!r}"


def save_prior_predictive_summary(
    paths: M5Paths,
    model: pm.Model,
    target: TargetConfig,
    prepared: pd.DataFrame,
    samples: int = 500,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Persist a compact prior-predictive scale check before inference."""

    with model:
        prior = pm.sample_prior_predictive(
            draws=samples,
            var_names=["r", "extra_sigma", "baseline", "latent_grid", "obs"],
            random_seed=RANDOM_SEED,
        )
    radius = np.asarray(prior.prior["r"].values).reshape(-1)
    extra_sigma = np.asarray(prior.prior["extra_sigma"].values).reshape(-1)
    baseline = np.asarray(prior.prior["baseline"].values).reshape(-1)
    latent_raw = np.asarray(prior.prior["latent_grid"].values)
    latent = latent_raw.reshape((-1, latent_raw.shape[-1]))
    simulated_raw = np.asarray(prior.prior_predictive["obs"].values)
    simulated = simulated_raw.reshape((-1, simulated_raw.shape[-1]))
    table = pd.DataFrame(
        {
            "sample_id": np.arange(len(radius)),
            "radius_ratio": radius,
            "geometric_depth_fraction": radius**2,
            "extra_sigma_fraction": extra_sigma,
            "baseline": baseline,
            "minimum_model_flux": latent.min(axis=1),
            "maximum_model_flux": latent.max(axis=1),
            "minimum_simulated_flux": simulated.min(axis=1),
            "maximum_simulated_flux": simulated.max(axis=1),
        }
    )
    table.to_csv(paths.prior_predictive_summary_path, index=False)
    low, high = np.quantile(radius, [HDI_LOW_Q, HDI_HIGH_Q])
    reference = target.reference_radius_ratio_from_depth
    predictive_low, predictive_high = quantile_interval(simulated)
    observed = prepared["normalized_flux"].to_numpy(dtype=float)
    metrics = {
        "samples": len(table),
        "radius_ratio_median": float(np.median(radius)),
        "radius_ratio_interval_94": [float(low), float(high)],
        "catalog_reference_radius_ratio": reference,
        "catalog_reference_inside_94_interval": bool(low <= reference <= high),
        "radius_ratio_fraction_outside_review_range_0.001_to_0.25": float(
            ((radius < 0.001) | (radius > 0.25)).mean()
        ),
        "finite_model_fraction": float(np.isfinite(latent).all(axis=1).mean()),
        "finite_simulated_observation_fraction": float(
            np.isfinite(simulated).all(axis=1).mean()
        ),
        "prior_predictive_interval_94_coverage_observed_points": float(
            ((observed >= predictive_low) & (observed <= predictive_high)).mean()
        ),
    }
    return table, metrics


def flatten_posterior_variable(idata: az.InferenceData, variable: str) -> np.ndarray:
    values = np.asarray(idata.posterior[variable].values)
    if values.ndim <= 2:
        return values.reshape(-1)
    return values.reshape((-1, *values.shape[2:]))


def quantile_interval(values: np.ndarray, axis: int = 0) -> tuple[np.ndarray, np.ndarray]:
    return np.quantile(values, HDI_LOW_Q, axis=axis), np.quantile(
        values, HDI_HIGH_Q, axis=axis
    )


def summary_value(summary: pd.DataFrame, parameter: str, column: str) -> float:
    row = summary.loc[summary["parameter"] == parameter]
    if row.empty or column not in row.columns:
        return float("nan")
    value = pd.to_numeric(row[column], errors="coerce").iloc[0]
    return float(value) if not pd.isna(value) else float("nan")


def normalize_arviz_hdi_columns(summary: pd.DataFrame) -> pd.DataFrame:
    """Normalize HDI names across ArviZ 0.x and 1.x table schemas."""

    aliases = {
        "hdi_3.0%": "hdi_3%",
        "hdi_97.0%": "hdi_97%",
        "hdi94_lb": "hdi_3%",
        "hdi94_ub": "hdi_97%",
    }
    return summary.rename(
        columns={source: destination for source, destination in aliases.items() if source in summary}
    )


def save_posterior_summary(paths: M5Paths, idata: az.InferenceData) -> pd.DataFrame:
    summary = az.summary(
        idata,
        var_names=SUMMARY_VAR_NAMES,
        ci_prob=HDI_PROB,
        ci_kind="hdi",
        kind="all",
        round_to=8,
    ).reset_index().rename(columns={"index": "parameter"})
    summary = normalize_arviz_hdi_columns(summary)
    summary.to_csv(paths.posterior_summary_path, index=False)
    return summary


def diagnostics_from_summary(
    summary: pd.DataFrame,
    idata: az.InferenceData,
) -> dict[str, Any]:
    r_hat = pd.to_numeric(summary.get("r_hat"), errors="coerce")
    ess_bulk = pd.to_numeric(summary.get("ess_bulk"), errors="coerce")
    ess_tail = pd.to_numeric(summary.get("ess_tail"), errors="coerce")
    ess_values = pd.concat([ess_bulk, ess_tail])
    max_r_hat = float(r_hat.max()) if not r_hat.dropna().empty else float("nan")
    min_ess = float(ess_values.min()) if not ess_values.dropna().empty else float("nan")
    acceptance_mean = float("nan")
    if hasattr(idata, "sample_stats"):
        for candidate in ("acceptance_rate", "accept_stat"):
            if candidate in idata.sample_stats:
                acceptance_mean = float(
                    np.asarray(idata.sample_stats[candidate].values).mean()
                )
                break
    bfmi_min: float | None = None
    try:
        bfmi_result = az.bfmi(idata)
        # ArviZ 1.3 returns an xarray DataTree, while older supported releases
        # return an ndarray.  Extract the sole diagnostic variable explicitly.
        if hasattr(bfmi_result, "dataset"):
            dataset = bfmi_result.dataset
            variables = list(dataset.data_vars)
            if not variables:
                raise ValueError("ArviZ BFMI result contains no data variables")
            bfmi_values = np.asarray(dataset[variables[0]].values, dtype=float)
        else:
            bfmi_values = np.asarray(bfmi_result, dtype=float)
        if bfmi_values.size and not np.isnan(bfmi_values).all():
            bfmi_min = float(np.nanmin(bfmi_values))
    except Exception:
        pass
    return {
        "max_r_hat": max_r_hat,
        "min_ess": min_ess,
        "divergences": count_divergences(idata),
        "acceptance_mean": acceptance_mean,
        "bfmi_min": bfmi_min,
    }


def save_derived_summary(paths: M5Paths, summary: pd.DataFrame) -> pd.DataFrame:
    row = {
        "depth_fraction_mean": summary_value(summary, "depth", "mean"),
        "depth_fraction_hdi_3": summary_value(summary, "depth", "hdi_3%"),
        "depth_fraction_hdi_97": summary_value(summary, "depth", "hdi_97%"),
        "depth_percent_mean": summary_value(summary, "depth", "mean") * 100.0,
        "rp_rs_mean": summary_value(summary, "rp_rs", "mean"),
        "rp_rs_hdi_3": summary_value(summary, "rp_rs", "hdi_3%"),
        "rp_rs_hdi_97": summary_value(summary, "rp_rs", "hdi_97%"),
        "transit_center_days_mean": summary_value(summary, "t0", "mean"),
        "transit_center_days_hdi_3": summary_value(summary, "t0", "hdi_3%"),
        "transit_center_days_hdi_97": summary_value(summary, "t0", "hdi_97%"),
        "impact_parameter_mean": summary_value(summary, "b", "mean"),
        "scaled_semimajor_axis_mean": summary_value(summary, "a", "mean"),
        "full_duration_days_mean": summary_value(summary, "full_duration", "mean"),
        "full_duration_days_hdi_3": summary_value(summary, "full_duration", "hdi_3%"),
        "full_duration_days_hdi_97": summary_value(summary, "full_duration", "hdi_97%"),
        "full_duration_hours_mean": summary_value(summary, "full_duration", "mean") * 24.0,
        "orbital_period_days_used": paths.target.orbital_period_days,
        "interpretation_note": (
            "Quadratic limb-darkened circular Keplerian transit with fixed orbital period "
            "and exposure integration; scientific interpretation is conditional on the gates."
        ),
    }
    derived = pd.DataFrame([row])
    derived.to_csv(paths.derived_summary_path, index=False)
    return derived


def save_curve_summary(
    paths: M5Paths,
    idata: az.InferenceData,
    phase_grid: np.ndarray,
    median_observation_sigma: float,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    latent_grid = flatten_posterior_variable(idata, "latent_grid")
    extra_sigma = flatten_posterior_variable(idata, "extra_sigma")
    rng = np.random.default_rng(RANDOM_SEED)
    sigma_grid = np.sqrt(median_observation_sigma**2 + extra_sigma**2)[:, None]
    predictive_grid = rng.normal(latent_grid, sigma_grid)
    model_low, model_high = quantile_interval(latent_grid)
    predictive_low, predictive_high = quantile_interval(predictive_grid)
    curve = pd.DataFrame(
        {
            "phase_days": phase_grid,
            "model_mean": latent_grid.mean(axis=0),
            "model_hdi_3": model_low,
            "model_hdi_97": model_high,
            "predictive_mean": predictive_grid.mean(axis=0),
            "predictive_hdi_3": predictive_low,
            "predictive_hdi_97": predictive_high,
        }
    )
    curve.to_csv(paths.physical_curve_summary_path, index=False)
    return curve, {
        "grid_rows": len(curve),
        "model_min_mean": float(curve["model_mean"].min()),
        "phase_at_min_model_mean_days": float(
            curve.loc[curve["model_mean"].idxmin(), "phase_days"]
        ),
    }


def posterior_predictive_samples(idata: az.InferenceData) -> np.ndarray | None:
    if not hasattr(idata, "posterior_predictive") or "obs" not in idata.posterior_predictive:
        return None
    values = np.asarray(idata.posterior_predictive["obs"].values)
    return values.reshape((-1, values.shape[-1]))


def save_predictive_and_residual_summaries(
    paths: M5Paths,
    idata: az.InferenceData,
    prepared: pd.DataFrame,
    posterior_summary: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], str]:
    predicted_mean = flatten_posterior_variable(idata, "latent_train").mean(axis=0)
    observed = prepared["normalized_flux"].to_numpy(dtype=float)
    predictive = posterior_predictive_samples(idata)
    if predictive is None:
        predictive_low = np.full_like(observed, np.nan)
        predictive_high = np.full_like(observed, np.nan)
        status = "posterior predictive samples unavailable"
    else:
        predictive_low, predictive_high = quantile_interval(predictive)
        status = "created"
    residual = observed - predicted_mean
    extra_sigma_mean = summary_value(posterior_summary, "extra_sigma", "mean")
    measurement_sigma = prepared["normalized_flux_err"].to_numpy(dtype=float)
    sigma_effective = np.sqrt(measurement_sigma**2 + extra_sigma_mean**2)
    standardized = residual / sigma_effective
    common = {
        "phase_days": prepared["phase"].to_numpy(dtype=float),
        "segment_id": prepared["segment_id"].astype(str).to_numpy(),
        "observed_flux": observed,
        "predicted_mean": predicted_mean,
    }
    predictive_table = pd.DataFrame(
        {
            **common,
            "predicted_hdi_3": predictive_low,
            "predicted_hdi_97": predictive_high,
            "residual": residual,
        }
    ).sort_values("phase_days")
    predictive_table.to_csv(paths.posterior_predictive_summary_path, index=False)
    residual_table = pd.DataFrame(
        {
            **common,
            "residual": residual,
            "normalized_flux_err": measurement_sigma,
            "sigma_effective_mean": sigma_effective,
            "standardized_residual": standardized,
        }
    ).sort_values("phase_days")
    residual_table.to_csv(paths.residual_summary_path, index=False)
    coverage = float("nan")
    if predictive is not None:
        coverage = float(
            ((observed >= predictive_low) & (observed <= predictive_high)).mean()
        )
    metrics = {
        "residual_mean": float(residual.mean()),
        "residual_median": float(np.median(residual)),
        "residual_std": float(residual.std(ddof=1)),
        "rmse": float(np.sqrt(np.mean(residual**2))),
        "mae": float(np.mean(np.abs(residual))),
        "standardized_residual_mean": float(standardized.mean()),
        "standardized_residual_std": float(standardized.std(ddof=1)),
        "posterior_predictive_interval_94_coverage_observed_points": coverage,
    }
    return predictive_table, residual_table, metrics, status


def posterior_scale_checks(
    idata: az.InferenceData,
    posterior_summary: pd.DataFrame,
    input_summary: dict[str, Any],
) -> dict[str, Any]:
    radius_ratio = flatten_posterior_variable(idata, "r")
    lower, upper = 0.001, 0.25
    boundary_width = 0.01 * (upper - lower)
    boundary_fraction = float(
        ((radius_ratio <= lower + boundary_width) | (radius_ratio >= upper - boundary_width)).mean()
    )
    extra_sigma_mean = summary_value(posterior_summary, "extra_sigma", "mean")
    measurement_sigma = float(input_summary["normalized_flux_err_median"])
    return {
        "extra_sigma_mean": extra_sigma_mean,
        "measurement_sigma_median": measurement_sigma,
        "extra_sigma_to_measurement_sigma": extra_sigma_mean / measurement_sigma,
        "radius_ratio_review_lower": lower,
        "radius_ratio_review_upper": upper,
        "radius_ratio_boundary_width": boundary_width,
        "radius_ratio_boundary_fraction": boundary_fraction,
        "reference_radius_ratio_from_catalog_depth": (
            input_summary.get("reference_radius_ratio_from_catalog_depth")
        ),
    }


def build_environment_summary() -> dict[str, Any]:
    return {
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "gcc": shutil.which("gcc"),
        "gxx": shutil.which("g++"),
        "pymc": pm.__version__,
        "arviz": az.__version__,
        "exoplanet": xo.__version__,
        "pytensor": pytensor.__version__,
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "matplotlib": matplotlib.__version__,
    }


def save_artifact_metadata(
    paths: M5Paths,
    input_summary: dict[str, Any],
    sampling: dict[str, Any],
    diagnostics: dict[str, Any],
    curve_metrics: dict[str, Any],
    residual_metrics: dict[str, Any],
    ppc_status: str,
    scale_checks: dict[str, Any],
    gate: dict[str, Any],
    posterior_summary: pd.DataFrame,
    derived_summary: pd.DataFrame,
    prior_profile: PriorProfile,
    prior_predictive_metrics: dict[str, Any],
) -> dict[str, Any]:
    target = paths.target
    config = {
        "created_at_utc": utc_now(),
        "model_name": MODEL_NAME,
        "run_id": paths.run_id,
        "target": target.metadata(),
        "source_gold_path": relative_path(paths.source_gold, paths.project_root),
        "input_contract": {
            "required_preprocessing_status": "segment_normalized",
            "quality_filter": "quality == 0 when present",
            "phase_filter_days": [-target.phase_window_days, target.phase_window_days],
            "normalization": "performed per segment by Gold; M5 does not renormalize globally",
        },
        "model": physical_model_spec(
            target,
            input_summary["median_exposure_seconds"],
            input_summary["normalized_flux_err_median"],
            prior_profile,
        ),
        "sampling": sampling,
        "log_likelihood": {
            "available": True,
            "pointwise_variable": "obs",
            "valid_comparison_requires_same_observations_and_likelihood_target": True,
        },
        "posterior_predictive_status": ppc_status,
        "prior_predictive_metrics": prior_predictive_metrics,
        "diagnostics": diagnostics,
        "posterior_scale_checks": scale_checks,
        "interpretation_gate": gate,
        "input_summary": input_summary,
        "curve_metrics": curve_metrics,
        "residual_metrics": residual_metrics,
        "environment": build_environment_summary(),
        "artifacts": {
            "trace": relative_path(paths.trace_path, paths.project_root),
            "posterior_summary": relative_path(paths.posterior_summary_path, paths.project_root),
            "derived_summary": relative_path(paths.derived_summary_path, paths.project_root),
            "curve_summary": relative_path(paths.physical_curve_summary_path, paths.project_root),
            "posterior_predictive_summary": relative_path(
                paths.posterior_predictive_summary_path, paths.project_root
            ),
            "residual_summary": relative_path(paths.residual_summary_path, paths.project_root),
            "prior_predictive_summary": relative_path(
                paths.prior_predictive_summary_path, paths.project_root
            ),
            "report": relative_path(paths.report_path, paths.project_root),
        },
        "artifact_checksums_sha256": {
            "trace": sha256_file(paths.trace_path),
            "modeling_input": sha256_file(paths.modeling_input_path),
            "posterior_summary": sha256_file(paths.posterior_summary_path),
            "derived_summary": sha256_file(paths.derived_summary_path),
            "curve_summary": sha256_file(paths.physical_curve_summary_path),
            "posterior_predictive_summary": sha256_file(
                paths.posterior_predictive_summary_path
            ),
            "residual_summary": sha256_file(paths.residual_summary_path),
            "prior_predictive_summary": sha256_file(
                paths.prior_predictive_summary_path
            ),
        },
    }
    paths.model_config_path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    inference_summary = {
        "created_at_utc": config["created_at_utc"],
        "model_name": MODEL_NAME,
        "run_id": paths.run_id,
        "target": target.metadata(),
        "sampling": sampling,
        "input_summary": input_summary,
        "diagnostics": diagnostics,
        "posterior_scale_checks": scale_checks,
        "prior_predictive_metrics": prior_predictive_metrics,
        "interpretation_gate": gate,
        "posterior_summary": posterior_summary.to_dict(orient="records"),
        "derived_parameters": derived_summary.iloc[0].to_dict(),
        "curve_metrics": curve_metrics,
        "residual_metrics": residual_metrics,
        "artifacts": config["artifacts"],
        "artifact_checksums_sha256": config["artifact_checksums_sha256"],
    }
    paths.inference_summary_path.write_text(
        json.dumps(inference_summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return config


def dataframe_to_markdown(dataframe: pd.DataFrame, max_rows: int = 16) -> str:
    rendered = dataframe.head(max_rows).copy()
    rendered = rendered.astype(object).where(pd.notna(rendered), "")
    columns = [str(column) for column in rendered.columns]
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = [
        "| " + " | ".join(str(row[column]).replace("\n", " ") for column in rendered.columns) + " |"
        for _, row in rendered.iterrows()
    ]
    return "\n".join([header, separator, *rows])


def save_report(
    paths: M5Paths,
    config: dict[str, Any],
    posterior_summary: pd.DataFrame,
    derived_summary: pd.DataFrame,
) -> None:
    target = paths.target
    gate = config["interpretation_gate"]
    diagnostics = config["diagnostics"]
    residual = config["residual_metrics"]
    derived = derived_summary.iloc[0]
    selected = posterior_summary.loc[
        posterior_summary["parameter"].isin(
            ["baseline", "r", "b", "a", "t0", "u[0]", "u[1]", "extra_sigma", "depth", "full_duration"]
        ),
        [
            column
            for column in ["parameter", "mean", "hdi_3%", "hdi_97%", "r_hat", "ess_bulk", "ess_tail"]
            if column in posterior_summary.columns
        ],
    ]
    rejection = (
        "Nenhum." if not gate["rejection_reasons"] else "\n".join(
            f"- {reason}" for reason in gate["rejection_reasons"]
        )
    )
    figure_rel = relative_path(paths.figure_dir, paths.project_root)
    report = f"""# M5 — trânsito físico bayesiano — {target.planet_name}

## Escopo e identidade

- alvo: `{target.planet_name}` (`{target.planet_slug}`)
- estrela: `{target.host_star}`
- missão: `{target.mission}`
- run: `{paths.run_id}`
- dataset Gold: `{config['input_summary']['dataset_id']}`
- entrada: `{config['source_gold_path']}`
- segmentos: `{config['input_summary']['segment_count']}`
- exposição mediana: `{config['input_summary']['median_exposure_seconds']:.6f} s`

O M5 só aceita Gold certificado como `segment_normalized`. A normalização foi
feita separadamente por segmento antes da concatenação; o M5 não aplica uma
segunda normalização global.

## Modelo executado

O modelo é um trânsito Kepleriano circular com escurecimento de bordo
quadrático, implementado por `exoplanet.KeplerianOrbit` e
`exoplanet.LimbDarkLightCurve`. O período fixado foi
`{target.orbital_period_days:.7f} d`, proveniente da configuração autoritativa
do alvo. Cada ponto é integrado pelo seu tempo de exposição com oversampling
`{target.exposure_oversample}`.

Parâmetros livres: baseline, `Rp/Rs` (`r`), parâmetro de impacto (`b`),
semieixo maior escalado (`a/Rs`), centro do trânsito (`t0`), coeficientes de
limb darkening e jitter branco adicional (`extra_sigma`). A likelihood é
Normal com `sqrt(flux_err² + extra_sigma²)`. Isso não é um modelo de ruído
vermelho ou correlacionado.

## Posterior

{dataframe_to_markdown(selected)}

Valores derivados principais:

- profundidade geométrica média: `{derived['depth_fraction_mean']:.10f}` em fração de fluxo (`{derived['depth_percent_mean']:.8f}%`)
- `Rp/Rs`: `{derived['rp_rs_mean']:.8f}`
- duração total: `{derived['full_duration_days_mean']:.8f} d` (`{derived['full_duration_hours_mean']:.5f} h`)
- centro do trânsito: `{derived['transit_center_days_mean']:.8f} d` na fase centrada

## Prior predictive check

- amostras: `{config['prior_predictive_metrics']['samples']}`
- referência catalogada de `Rp/Rs` dentro do intervalo prior de 94%: `{config['prior_predictive_metrics']['catalog_reference_inside_94_interval']}`
- fração de curvas prior com valores finitos: `{config['prior_predictive_metrics']['finite_model_fraction']}`
- cobertura das observações pelo intervalo prior-preditivo de 94%: `{config['prior_predictive_metrics']['prior_predictive_interval_94_coverage_observed_points']}`
- tabela: `{relative_path(paths.prior_predictive_summary_path, paths.project_root)}`

## Diagnósticos e gates

- R-hat máximo: `{diagnostics['max_r_hat']}`
- ESS mínimo: `{diagnostics['min_ess']}`
- divergências: `{diagnostics['divergences']}`
- BFMI mínimo: `{diagnostics['bfmi_min']}`
- cobertura PPC de 94%: `{residual['posterior_predictive_interval_94_coverage_observed_points']}`
- desvio dos resíduos padronizados: `{residual['standardized_residual_std']}`
- sampler convergiu: `{gate['sampler_converged']}`
- PPC adequado: `{gate['posterior_predictive_adequate']}`
- cientificamente interpretável: `{gate['scientifically_interpretable']}`

Motivos de rejeição:

{rejection}

Uma cadeia convergida não basta para interpretação física. O status científico
também exige Gold segmentado, exposição conhecida, PPC adequado e ausência de
sinais graves de dominância do jitter ou saturação do prior de `Rp/Rs`.

## Artefatos

- configuração executada: `{relative_path(paths.model_config_path, paths.project_root)}`
- trace com log-likelihood pontual: `{relative_path(paths.trace_path, paths.project_root)}`
- resumo posterior: `{relative_path(paths.posterior_summary_path, paths.project_root)}`
- resumo derivado: `{relative_path(paths.derived_summary_path, paths.project_root)}`
- PPC: `{relative_path(paths.posterior_predictive_summary_path, paths.project_root)}`
- resíduos: `{relative_path(paths.residual_summary_path, paths.project_root)}`

![Ajuste físico](../{figure_rel}/05_physical_fit_phase.png)

![Posterior predictive check](../{figure_rel}/06_posterior_predictive_check.png)

## Limitações

O período é fixo; a órbita assume excentricidade zero; parâmetros estelares não
são inferidos conjuntamente; o jitter é branco e independente; e a
profundidade `r²` é uma referência geométrica, não necessariamente a
profundidade aparente sob limb darkening. Comparações LOO/WAIC só são válidas
entre execuções que usam exatamente as mesmas observações e o mesmo alvo da
likelihood.
"""
    paths.report_path.write_text(report, encoding="utf-8")


def save_figures(
    paths: M5Paths,
    prepared: pd.DataFrame,
    idata: az.InferenceData,
    curve: pd.DataFrame,
    residuals: pd.DataFrame,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(prepared["phase"], prepared["normalized_flux"], s=8, alpha=0.3)
    ax.set(xlabel="Phase (days)", ylabel="Normalized flux", title="M5 modeling input")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "01_modeling_input.png", dpi=200)
    plt.close(fig)

    variables = ["baseline", "t0", "r", "b", "a", "extra_sigma"]
    fig, axes = plt.subplots(len(variables), 2, figsize=(12, 2.2 * len(variables)))
    for row_index, variable in enumerate(variables):
        values = np.asarray(idata.posterior[variable].values)
        flat = values.reshape(-1)
        axes[row_index, 0].hist(flat, bins=min(40, max(5, len(flat) // 2)), alpha=0.85)
        axes[row_index, 0].set_ylabel(variable)
        axes[row_index, 0].grid(alpha=0.25)
        for chain_index in range(values.shape[0]):
            axes[row_index, 1].plot(values[chain_index].reshape(-1), linewidth=0.7)
        axes[row_index, 1].set_ylabel(variable)
        axes[row_index, 1].grid(alpha=0.25)
    axes[0, 0].set_title("Posterior distribution")
    axes[0, 1].set_title("Trace by chain")
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "02_trace_plot.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for axis, variable, title in zip(
        axes,
        ("depth", "full_duration", "rp_rs"),
        ("Depth fraction", "Full duration (days)", "Rp/Rs"),
        strict=True,
    ):
        values = flatten_posterior_variable(idata, variable)
        axis.hist(values, bins=50, alpha=0.85)
        axis.axvline(values.mean(), linestyle="--")
        axis.set_title(title)
        axis.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "03_posterior_depth_duration.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(prepared["phase"], prepared["normalized_flux"], s=8, alpha=0.25, label="observed")
    ax.plot(curve["phase_days"], curve["model_mean"], label="physical model")
    ax.fill_between(curve["phase_days"], curve["model_hdi_3"], curve["model_hdi_97"], alpha=0.22)
    ax.set(xlabel="Phase (days)", ylabel="Normalized flux", title="M5 physical fit")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "05_physical_fit_phase.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(prepared["phase"], prepared["normalized_flux"], s=8, alpha=0.25, label="observed")
    ax.plot(curve["phase_days"], curve["predictive_mean"], label="predictive mean")
    ax.fill_between(
        curve["phase_days"], curve["predictive_hdi_3"], curve["predictive_hdi_97"], alpha=0.22
    )
    ax.set(xlabel="Phase (days)", ylabel="Normalized flux", title="M5 posterior predictive check")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "06_posterior_predictive_check.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(residuals["phase_days"], residuals["residual"], s=9, alpha=0.4)
    ax.axhline(0, linestyle="--")
    ax.set(xlabel="Phase (days)", ylabel="Observed - predicted", title="M5 residuals")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "07_residuals_by_phase.png", dpi=200)
    plt.close(fig)


def _run_m5_unchecked(
    *,
    target_slug: str = DEFAULT_TARGET_SLUG,
    run_id: str = M5_DEFAULT_RUN_ID,
    project_root: Path | None = None,
    sampling_overrides: dict[str, Any] | None = None,
    prior_profile_name: str = "baseline",
) -> dict[str, Any]:
    target = get_target(target_slug)
    prior_profile = get_prior_profile(prior_profile_name)
    paths = build_paths(target, run_id, project_root)
    ensure_directories(paths)
    raw = read_gold_transit_window(paths)
    prepared, input_summary = prepare_modeling_input(raw, paths)
    input_summary["modeling_input_sha256"] = sha256_file(paths.modeling_input_path)
    input_summary["reference_radius_ratio_from_catalog_depth"] = (
        target.reference_radius_ratio_from_depth
    )
    phase_grid = np.linspace(
        -target.phase_window_days, target.phase_window_days, PREDICTION_GRID_POINTS
    )
    model = build_model(prepared, phase_grid, target, prior_profile)
    _, prior_predictive_metrics = save_prior_predictive_summary(
        paths, model, target, prepared
    )
    idata, sampling = sample_nuts(model, sampling_overrides)
    idata, ppc_sampling_status = sample_posterior_predictive(model, idata)
    paths.trace_path.unlink(missing_ok=True)
    idata.to_netcdf(paths.trace_path)
    posterior_summary = save_posterior_summary(paths, idata)
    derived_summary = save_derived_summary(paths, posterior_summary)
    diagnostics = diagnostics_from_summary(posterior_summary, idata)
    curve, curve_metrics = save_curve_summary(
        paths, idata, phase_grid, input_summary["normalized_flux_err_median"]
    )
    _, residuals, residual_metrics, ppc_table_status = save_predictive_and_residual_summaries(
        paths, idata, prepared, posterior_summary
    )
    ppc_status = ppc_table_status if ppc_sampling_status == "created" else ppc_sampling_status
    scale_checks = posterior_scale_checks(idata, posterior_summary, input_summary)
    gate = evaluate_interpretation_gate(
        diagnostics=diagnostics,
        residual_metrics=residual_metrics,
        input_summary=input_summary,
        posterior_scale_checks=scale_checks,
        posterior_predictive_status=ppc_status,
    )
    config = save_artifact_metadata(
        paths,
        input_summary,
        sampling,
        diagnostics,
        curve_metrics,
        residual_metrics,
        ppc_status,
        scale_checks,
        gate,
        posterior_summary,
        derived_summary,
        prior_profile,
        prior_predictive_metrics,
    )
    save_figures(paths, prepared, idata, curve, residuals)
    save_report(paths, config, posterior_summary, derived_summary)
    result = {
        "model_name": MODEL_NAME,
        "run_id": paths.run_id,
        "target": target.planet_name,
        "prior_profile": prior_profile.name,
        "dataset_id": input_summary["dataset_id"],
        "points_used": input_summary["rows_used"],
        "trace": relative_path(paths.trace_path, paths.project_root),
        "trace_sha256": sha256_file(paths.trace_path),
        "report": relative_path(paths.report_path, paths.project_root),
        "interpretation_gate": gate,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def run_m5(
    *,
    target_slug: str = DEFAULT_TARGET_SLUG,
    run_id: str = M5_DEFAULT_RUN_ID,
    project_root: Path | None = None,
    sampling_overrides: dict[str, Any] | None = None,
    prior_profile_name: str = "baseline",
) -> dict[str, Any]:
    """Run M5 and persist a machine-readable status even when it fails."""

    target = get_target(target_slug)
    paths = build_paths(target, run_id, project_root)
    ensure_directories(paths)
    status_path = paths.model_dir / "run_status.json"
    started_at = utc_now()
    status_path.write_text(
        json.dumps(
            {
                "status": "running",
                "started_at_utc": started_at,
                "model_name": MODEL_NAME,
                "run_id": run_id,
                "target": target.metadata(),
                "prior_profile": prior_profile_name,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    try:
        result = _run_m5_unchecked(
            target_slug=target_slug,
            run_id=run_id,
            project_root=project_root,
            sampling_overrides=sampling_overrides,
            prior_profile_name=prior_profile_name,
        )
    except BaseException as exc:
        status_path.write_text(
            json.dumps(
                {
                    "status": "failed",
                    "started_at_utc": started_at,
                    "finished_at_utc": utc_now(),
                    "model_name": MODEL_NAME,
                    "run_id": run_id,
                    "target": target.metadata(),
                    "prior_profile": prior_profile_name,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "interrupted": isinstance(exc, (KeyboardInterrupt, SystemExit)),
                    "traceback": traceback.format_exc(),
                    "scientifically_interpretable": False,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        raise
    status_path.write_text(
        json.dumps(
            {
                "status": "completed",
                "started_at_utc": started_at,
                "finished_at_utc": utc_now(),
                **result,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return result


def rebuild_m5_artifacts_from_trace(
    *,
    target_slug: str,
    run_id: str,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Rebuild summaries/reports from an unchanged trace and exact observations."""

    target = get_target(target_slug)
    paths = build_paths(target, run_id, project_root)
    if not paths.trace_path.exists() or not paths.model_config_path.exists():
        raise FileNotFoundError("Rebuild requires both trace.nc and model_config.json")
    previous = json.loads(paths.model_config_path.read_text(encoding="utf-8"))
    raw = read_gold_transit_window(paths)
    prepared, input_summary = prepare_modeling_input(raw, paths)
    input_summary["modeling_input_sha256"] = sha256_file(paths.modeling_input_path)
    input_summary["reference_radius_ratio_from_catalog_depth"] = (
        target.reference_radius_ratio_from_depth
    )
    previous_input = previous.get("input_summary", {})
    if input_summary["dataset_id"] != previous_input.get("dataset_id"):
        raise ValueError("Refusing rebuild: dataset_id differs from the sampled run")
    if input_summary["modeling_input_sha256"] != previous_input.get(
        "modeling_input_sha256"
    ):
        raise ValueError("Refusing rebuild: modeling-input checksum differs from the trace")

    idata = az.from_netcdf(paths.trace_path)
    phase_grid = np.linspace(
        -target.phase_window_days, target.phase_window_days, PREDICTION_GRID_POINTS
    )
    posterior_summary = save_posterior_summary(paths, idata)
    derived_summary = save_derived_summary(paths, posterior_summary)
    diagnostics = diagnostics_from_summary(posterior_summary, idata)
    curve, curve_metrics = save_curve_summary(
        paths, idata, phase_grid, input_summary["normalized_flux_err_median"]
    )
    _, residuals, residual_metrics, ppc_status = save_predictive_and_residual_summaries(
        paths, idata, prepared, posterior_summary
    )
    scale_checks = posterior_scale_checks(idata, posterior_summary, input_summary)
    gate = evaluate_interpretation_gate(
        diagnostics=diagnostics,
        residual_metrics=residual_metrics,
        input_summary=input_summary,
        posterior_scale_checks=scale_checks,
        posterior_predictive_status=ppc_status,
    )
    profile_name = previous.get("model", {}).get("priors", {}).get("profile", {}).get(
        "name", "baseline"
    )
    config = save_artifact_metadata(
        paths,
        input_summary,
        previous["sampling"],
        diagnostics,
        curve_metrics,
        residual_metrics,
        ppc_status,
        scale_checks,
        gate,
        posterior_summary,
        derived_summary,
        get_prior_profile(profile_name),
        previous["prior_predictive_metrics"],
    )
    save_figures(paths, prepared, idata, curve, residuals)
    save_report(paths, config, posterior_summary, derived_summary)

    status_path = paths.model_dir / "run_status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    status.update(
        {
            "artifacts_rebuilt_from_unchanged_trace_at_utc": utc_now(),
            "trace_sha256": sha256_file(paths.trace_path),
            "interpretation_gate": gate,
        }
    )
    status_path.write_text(
        json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return {
        "status": "rebuilt",
        "run_id": run_id,
        "target": target.planet_name,
        "trace_sha256": sha256_file(paths.trace_path),
        "modeling_input_sha256": input_summary["modeling_input_sha256"],
        "interpretation_gate": gate,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default=DEFAULT_TARGET_SLUG)
    parser.add_argument("--run-id", default=M5_DEFAULT_RUN_ID)
    parser.add_argument("--draws", type=int, default=DEFAULT_SAMPLING["draws"])
    parser.add_argument("--tune", type=int, default=DEFAULT_SAMPLING["tune"])
    parser.add_argument("--chains", type=int, default=DEFAULT_SAMPLING["chains"])
    parser.add_argument("--cores", type=int, default=DEFAULT_SAMPLING["cores"])
    parser.add_argument("--target-accept", type=float, default=DEFAULT_SAMPLING["target_accept"])
    parser.add_argument(
        "--prior-profile",
        choices=["catalog_tighter", "baseline", "weak"],
        default="baseline",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    run_m5(
        target_slug=args.target,
        run_id=args.run_id,
        sampling_overrides={
            "draws": args.draws,
            "tune": args.tune,
            "chains": args.chains,
            "cores": args.cores,
            "target_accept": args.target_accept,
        },
        prior_profile_name=args.prior_profile,
    )


if __name__ == "__main__":
    main()
