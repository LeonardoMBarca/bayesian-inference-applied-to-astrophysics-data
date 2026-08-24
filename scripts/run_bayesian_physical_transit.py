"""Run M5 Bayesian physical transit model for HAT-P-7 b.

M5 models the normalized Kepler transit window with an approximate physicalal
shape. It reads the existing GOLD transit-window table and writes new artifacts
under the bayesian_physical_transit family without modifying RAW, Silver,
Gold, M1, or M2 outputs.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MPLCONFIGDIR = Path("/tmp") / "matplotlib-cache"
MPLCONFIGDIR.mkdir(parents=True, exist_ok=True)
os.environ["MPLCONFIGDIR"] = str(MPLCONFIGDIR)

PYTENSOR_CACHE = Path("/tmp") / "pytensor-cache-m5-physical"
PYTENSOR_CACHE.mkdir(parents=True, exist_ok=True)
os.environ["PYTENSOR_FLAGS"] = f"base_compiledir={PYTENSOR_CACHE}"

import arviz as az  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pymc as pm
import exoplanet as xo  # noqa: E402
import pytensor  # noqa: E402
import pytensor.tensor as pt  # noqa: E402


PLANET_NAME = "HAT-P-7 b"
PLANET_SLUG = "hat_p_7_b"
HOST_STAR = "HAT-P-7"
MISSION = "Kepler"
MODEL_NAME = "M5_bayesian_physical_transit"
RUN_ID = "001_nuts"
SOURCE_GOLD_PATH = "data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv"

PHASE_WINDOW = 0.15
BASELINE_MIN_ABS_PHASE = 0.08
BASELINE_MAX_ABS_PHASE = 0.15
PREDICTION_GRID_POINTS = 300
RANDOM_SEED = 42
HDI_PROB = 0.94
HDI_LOW_Q = 0.03
HDI_HIGH_Q = 0.97

REQUESTED_SAMPLING = {
    "sampler": "NUTS",
    "draws": 2000,
    "tune": 2000,
    "chains": 4,
    "cores": 4,
    "target_accept": 0.90,
    "random_seed": RANDOM_SEED,
}
RETRY_TARGET_ACCEPT = 0.95
SECOND_RETRY_TARGET_ACCEPT = 0.99

SUMMARY_VAR_NAMES = [
    "baseline",
    "r",
    "b",
    "a",
    "t0",
    "u",
    "extra_sigma",
    "depth",
    "rp_rs",
    "full_duration",
]


@dataclass(frozen=True)
class M5Paths:
    """Filesystem paths for M5 artifacts."""

    project_root: Path
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
    m1_derived_path: Path
    m1_posterior_summary_path: Path
    m2_curve_path: Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_project_root(project_root: Path | None = None) -> Path:
    if project_root is not None:
        return project_root.resolve()
    candidate = Path(__file__).resolve().parents[1]
    if (candidate / "data" / "gold").exists():
        return candidate
    cwd = Path.cwd().resolve()
    if (cwd / "data" / "gold").exists():
        return cwd
    raise FileNotFoundError("Could not locate project root containing data/gold.")


def build_paths(project_root: Path | None = None) -> M5Paths:
    root = resolve_project_root(project_root)
    model_dir = root / "models" / "bayesian_physical_transit" / PLANET_SLUG / "runs" / RUN_ID
    table_dir = root / "tables" / "bayesian_physical_transit" / PLANET_SLUG
    figure_dir = root / "figures" / "bayesian_physical_transit" / PLANET_SLUG
    return M5Paths(
        project_root=root,
        source_gold=root / SOURCE_GOLD_PATH,
        model_dir=model_dir,
        table_dir=table_dir,
        figure_dir=figure_dir,
        report_path=root / "reports" / "bayesian_physical_transit_hat_p_7_b_report.md",
        notebook_path=root / "notebooks" / "05_bayesian_physical_transit_hat_p_7_b.ipynb",
        docs_dir=root / "docs" / "modeling" / "bayesian_physical_transit_hat_p_7_b",
        trace_path=model_dir / "trace.nc",
        model_config_path=model_dir / "model_config.json",
        inference_summary_path=model_dir / "inference_data_summary.json",
        modeling_input_path=table_dir / "modeling_input_physical.csv",
        posterior_summary_path=table_dir / "posterior_summary.csv",
        derived_summary_path=table_dir / "derived_parameters_summary.csv",
        physical_curve_summary_path=table_dir / "physical_curve_summary.csv",
        posterior_predictive_summary_path=table_dir / "posterior_predictive_summary.csv",
        residual_summary_path=table_dir / "residual_summary.csv",
        m1_derived_path=(
            root
            / "tables"
            / "bayesian_baseline"
            / PLANET_SLUG
            / "runs"
            / "002_nuts_robust"
            / "derived_parameters_summary.csv"
        ),
        m1_posterior_summary_path=(
            root
            / "tables"
            / "bayesian_baseline"
            / PLANET_SLUG
            / "runs"
            / "002_nuts_robust"
            / "posterior_summary.csv"
        ),
        m2_curve_path=(
            root
            / "tables"
            / "bayesian_predictive_phase_regression"
            / PLANET_SLUG
            / "predictive_curve_summary.csv"
        ),
    )


def ensure_directories(paths: M5Paths) -> None:
    for directory in [
        paths.model_dir,
        paths.table_dir,
        paths.figure_dir,
        paths.report_path.parent,
        paths.notebook_path.parent,
        paths.docs_dir,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


def relative_path(path: Path, project_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(path.resolve())


def read_gold_transit_window(paths: M5Paths) -> pd.DataFrame:
    if not paths.source_gold.exists():
        raise FileNotFoundError(f"Missing GOLD input: {paths.source_gold}")
    dataframe = pd.read_csv(paths.source_gold, low_memory=False)
    for column in ["phase", "flux", "flux_err", "quality", "time"]:
        if column in dataframe.columns:
            dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")
    return dataframe


def prepare_modeling_input(dataframe: pd.DataFrame, paths: M5Paths) -> tuple[pd.DataFrame, dict[str, Any]]:
    required = ["phase", "flux", "flux_err"]
    missing = [column for column in required if column not in dataframe.columns]
    if missing:
        raise ValueError(f"Missing required columns in GOLD input: {missing}")

    prepared = dataframe.copy()
    initial_rows = len(prepared)
    prepared = prepared.loc[prepared["phase"].abs() <= PHASE_WINDOW].copy()
    rows_after_phase = len(prepared)

    if "quality" in prepared.columns:
        prepared = prepared.loc[prepared["quality"] == 0].copy()
    rows_after_quality = len(prepared)

    prepared = prepared.dropna(subset=["phase", "flux", "flux_err"]).copy()
    rows_after_missing = len(prepared)
    prepared = prepared.loc[prepared["flux_err"] > 0].copy()
    rows_after_positive_err = len(prepared)

    abs_phase = prepared["phase"].abs()
    prepared["is_baseline_region"] = (
        (abs_phase >= BASELINE_MIN_ABS_PHASE) & (abs_phase <= BASELINE_MAX_ABS_PHASE)
    )

    baseline_flux = prepared.loc[prepared["is_baseline_region"], "flux"].dropna()
    if baseline_flux.empty:
        raise ValueError("Baseline region is empty; cannot normalize local flux.")
    baseline_median = float(baseline_flux.median())
    if not math.isfinite(baseline_median) or baseline_median <= 0:
        raise ValueError(f"Invalid baseline median: {baseline_median}")

    prepared["normalized_flux"] = prepared["flux"] / baseline_median
    prepared["normalized_flux_err"] = prepared["flux_err"] / baseline_median
    prepared["source_gold_path"] = SOURCE_GOLD_PATH

    for column in ["planet_name", "host_star", "mission", "quality", "time"]:
        if column not in prepared.columns:
            if column == "planet_name":
                prepared[column] = PLANET_NAME
            elif column == "host_star":
                prepared[column] = HOST_STAR
            elif column == "mission":
                prepared[column] = MISSION
            else:
                prepared[column] = np.nan

    columns = [
        "planet_name",
        "host_star",
        "mission",
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
    prepared = prepared.loc[:, columns].sort_values("phase").reset_index(drop=True)
    prepared.to_csv(paths.modeling_input_path, index=False)

    metadata = {
        "initial_rows_gold_window": int(initial_rows),
        "rows_after_phase_filter": int(rows_after_phase),
        "rows_after_quality_filter": int(rows_after_quality),
        "rows_after_missing_filter": int(rows_after_missing),
        "rows_after_positive_flux_err_filter": int(rows_after_positive_err),
        "rows_used": int(len(prepared)),
        "baseline_median": baseline_median,
        "baseline_region_count": int(prepared["is_baseline_region"].sum()),
        "phase_min": float(prepared["phase"].min()),
        "phase_max": float(prepared["phase"].max()),
        "normalized_flux_median": float(prepared["normalized_flux"].median()),
        "normalized_flux_mean": float(prepared["normalized_flux"].mean()),
        "normalized_flux_std": float(prepared["normalized_flux"].std(ddof=1)),
        "normalized_flux_err_median": float(prepared["normalized_flux_err"].median()),
    }
    return prepared, metadata


def physical_numpy(
    phase: np.ndarray,
    baseline: np.ndarray | float,
    depth: np.ndarray | float,
    center: np.ndarray | float,
    half_duration: np.ndarray | float,
    ingress_duration: np.ndarray | float,
) -> np.ndarray:
    phase_array = np.asarray(phase, dtype=float)
    d = np.abs(phase_array - np.asarray(center)[..., None])
    shape = np.clip((np.asarray(half_duration)[..., None] - d) / np.asarray(ingress_duration)[..., None], 0, 1)
    return np.asarray(baseline)[..., None] - np.asarray(depth)[..., None] * shape


def build_model(prepared: pd.DataFrame, phase_grid: np.ndarray) -> pm.Model:
    phase = prepared["phase"].to_numpy(dtype=float)
    y = prepared["normalized_flux"].to_numpy(dtype=float)
    sigma_obs = prepared["normalized_flux_err"].to_numpy(dtype=float)
    coords = {"observation": np.arange(len(prepared)), "grid": np.arange(len(phase_grid))}

    with pm.Model(coords=coords) as model:
        baseline = pm.Normal("baseline", mu=1.0, sigma=0.01)
        r = pm.Uniform("r", lower=0.01, upper=0.2)
        b = pm.Uniform("b", lower=0.0, upper=1.0)
        u = xo.distributions.QuadLimbDark("u")
        a = pm.Uniform("a", lower=2.0, upper=10.0)
        t0 = pm.Normal("t0", mu=0.0, sigma=0.01)
        
        orbit = xo.orbits.KeplerianOrbit(period=2.204735, t0=t0, b=b, a=a)
        light_curve = xo.LimbDarkLightCurve(u[0], u[1])
        
        latent_train = pm.Deterministic(
            "latent_train", 
            baseline + light_curve.get_light_curve(orbit=orbit, r=r, t=phase).flatten(), 
            dims="observation"
        )
        pm.Deterministic(
            "latent_grid", 
            baseline + light_curve.get_light_curve(orbit=orbit, r=r, t=phase_grid).flatten(), 
            dims="grid"
        )
        
        extra_sigma = pm.HalfNormal("extra_sigma", sigma=0.005)
        sigma_eff = pm.math.sqrt(np.square(sigma_obs) + extra_sigma**2)
        
        pm.Normal("obs", mu=latent_train, sigma=sigma_eff, observed=y, dims="observation")
        
        pm.Deterministic("depth", r**2)
        pm.Deterministic("rp_rs", r)
        duration = (2.204735 / np.pi) * pt.arcsin(pt.sqrt((1.0 + r)**2 - b**2) / a)
        pm.Deterministic("full_duration", duration)
        
    return model


def count_divergences(idata: az.InferenceData) -> int:
    if not hasattr(idata, "sample_stats") or "diverging" not in idata.sample_stats:
        return 0
    return int(np.asarray(idata.sample_stats["diverging"].values).sum())


def sample_nuts(model: pm.Model) -> tuple[az.InferenceData, dict[str, Any]]:
    sample_config = dict(REQUESTED_SAMPLING)
    sample_config["cores"] = min(sample_config["cores"], os.cpu_count() or 1)
    sample_config["retry_performed"] = False
    sample_config["retry_reason"] = ""

    with model:
        idata = pm.sample(
            draws=sample_config["draws"],
            tune=sample_config["tune"],
            chains=sample_config["chains"],
            cores=sample_config["cores"],
            target_accept=sample_config["target_accept"],
            random_seed=sample_config["random_seed"],
            init="jitter+adapt_diag",
            return_inferencedata=True,
            progressbar=True,
        )

    divergences = count_divergences(idata)
    if divergences > 0:
        sample_config["retry_performed"] = True
        sample_config["retry_reason"] = (
            f"{divergences} divergences with target_accept={sample_config['target_accept']}; "
            f"reran with target_accept={RETRY_TARGET_ACCEPT}."
        )
        sample_config["target_accept"] = RETRY_TARGET_ACCEPT
        with model:
            idata = pm.sample(
                draws=sample_config["draws"],
                tune=sample_config["tune"],
                chains=sample_config["chains"],
                cores=sample_config["cores"],
                target_accept=sample_config["target_accept"],
                random_seed=sample_config["random_seed"],
                init="jitter+adapt_diag",
                return_inferencedata=True,
                progressbar=True,
            )

    divergences = count_divergences(idata)
    if divergences > 0 and sample_config["target_accept"] < SECOND_RETRY_TARGET_ACCEPT:
        previous_reason = sample_config["retry_reason"]
        sample_config["retry_performed"] = True
        sample_config["retry_reason"] = (
            f"{previous_reason} Still found {divergences} divergences with "
            f"target_accept={sample_config['target_accept']}; reran with "
            f"target_accept={SECOND_RETRY_TARGET_ACCEPT}."
        )
        sample_config["target_accept"] = SECOND_RETRY_TARGET_ACCEPT
        with model:
            idata = pm.sample(
                draws=sample_config["draws"],
                tune=sample_config["tune"],
                chains=sample_config["chains"],
                cores=sample_config["cores"],
                target_accept=sample_config["target_accept"],
                random_seed=sample_config["random_seed"],
                init="jitter+adapt_diag",
                return_inferencedata=True,
                progressbar=True,
            )

    return idata, sample_config


def sample_posterior_predictive(model: pm.Model, idata: az.InferenceData) -> tuple[az.InferenceData, str]:
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
    except Exception as exc:  # pragma: no cover
        return idata, f"failed: {exc!r}"


def flatten_posterior_variable(idata: az.InferenceData, variable: str) -> np.ndarray:
    values = np.asarray(idata.posterior[variable].values)
    if values.ndim <= 2:
        return values.reshape(-1)
    return values.reshape((-1, *values.shape[2:]))


def quantile_interval(values: np.ndarray, axis: int = 0) -> tuple[np.ndarray, np.ndarray]:
    return (
        np.quantile(values, HDI_LOW_Q, axis=axis),
        np.quantile(values, HDI_HIGH_Q, axis=axis),
    )


def save_trace(paths: M5Paths, idata: az.InferenceData) -> None:
    paths.trace_path.unlink(missing_ok=True)
    idata.to_netcdf(paths.trace_path)


def save_posterior_summary(paths: M5Paths, idata: az.InferenceData) -> pd.DataFrame:
    summary = az.summary(
        idata,
        var_names=SUMMARY_VAR_NAMES,
        ci_prob=HDI_PROB,
        ci_kind="hdi",
        kind="all",
        round_to=8,
    )
    summary = summary.reset_index().rename(columns={"index": "parameter"})
    summary = summary.rename(columns={"hdi94_lb": "hdi_3%", "hdi94_ub": "hdi_97%"})
    summary.to_csv(paths.posterior_summary_path, index=False)
    return summary


def summary_value(summary: pd.DataFrame, parameter: str, column: str) -> float:
    row = summary.loc[summary["parameter"] == parameter]
    if row.empty or column not in row.columns:
        return float("nan")
    value = pd.to_numeric(row[column], errors="coerce").iloc[0]
    return float(value) if not pd.isna(value) else float("nan")


def diagnostics_from_summary(summary: pd.DataFrame, idata: az.InferenceData) -> dict[str, Any]:
    r_hat = pd.to_numeric(summary.get("r_hat"), errors="coerce")
    ess_bulk = pd.to_numeric(summary.get("ess_bulk"), errors="coerce")
    ess_tail = pd.to_numeric(summary.get("ess_tail"), errors="coerce")
    ess_values = pd.concat([ess_bulk, ess_tail])
    max_r_hat = float(r_hat.max()) if not r_hat.dropna().empty else float("nan")
    min_ess = float(ess_values.min()) if not ess_values.dropna().empty else float("nan")

    divergences = count_divergences(idata)
    sample_stats = idata.sample_stats if hasattr(idata, "sample_stats") else None
    acceptance_mean = float("nan")
    if sample_stats is not None:
        for candidate in ["acceptance_rate", "accept_stat"]:
            if candidate in sample_stats:
                acceptance_mean = float(np.asarray(sample_stats[candidate].values).mean())
                break

    bfmi_min: float | None = None
    try:
        bfmi_result = az.bfmi(idata)
        if hasattr(bfmi_result, "groups") and "/sample_stats" in bfmi_result.groups:
            bfmi_values = np.asarray(bfmi_result["/sample_stats"].dataset["energy"].values, dtype=float)
        else:
            bfmi_values = np.asarray(bfmi_result, dtype=float)
        if bfmi_values.size and not np.isnan(bfmi_values).all():
            bfmi_min = float(np.nanmin(bfmi_values))
    except Exception:
        pass

    recommended = (
        math.isfinite(max_r_hat)
        and max_r_hat <= 1.01
        and math.isfinite(min_ess)
        and min_ess >= 400
        and divergences == 0
    )
    return {
        "max_r_hat": max_r_hat,
        "min_ess": min_ess,
        "divergences": divergences,
        "acceptance_mean": acceptance_mean,
        "bfmi_min": bfmi_min,
        "recommended_for_m5_interpretation": recommended,
        "convergence_note": (
            "NUTS diagnostics satisfy the project criteria for M5 interpretation."
            if recommended
            else "Review diagnostics before treating M5 as reliable."
        ),
    }


def save_derived_summary(paths: M5Paths, summary: pd.DataFrame) -> pd.DataFrame:
    row = {
        "depth_mean": summary_value(summary, "depth", "mean"),
        "depth_hdi_3": summary_value(summary, "depth", "hdi_3%"),
        "depth_hdi_97": summary_value(summary, "depth", "hdi_97%"),
        "rp_rs_mean": summary_value(summary, "rp_rs", "mean"),
        "rp_rs_hdi_3": summary_value(summary, "rp_rs", "hdi_3%"),
        "rp_rs_hdi_97": summary_value(summary, "rp_rs", "hdi_97%"),
        "center_mean": summary_value(summary, "center", "mean"),
        "center_hdi_3": summary_value(summary, "center", "hdi_3%"),
        "center_hdi_97": summary_value(summary, "center", "hdi_97%"),
        "full_duration_mean_days": summary_value(summary, "full_duration", "mean"),
        "full_duration_hdi_3_days": summary_value(summary, "full_duration", "hdi_3%"),
        "full_duration_hdi_97_days": summary_value(summary, "full_duration", "hdi_97%"),
        "full_duration_mean_hours": summary_value(summary, "full_duration", "mean") * 24,
        "ingress_duration_mean_days": summary_value(summary, "ingress_duration", "mean"),
        "ingress_duration_mean_hours": summary_value(summary, "ingress_duration", "mean") * 24,
        "flat_duration_mean_days": summary_value(summary, "flat_duration", "mean"),
        "ingress_egress_total_mean_days": summary_value(summary, "ingress_egress_total", "mean"),
        "interpretation_note": (
            "M5 is an approximate physicalal transit model. It estimates depth, "
            "duration and ingress/egress within a simplified geometry and should "
            "not be treated as a full physical transit characterization."
        ),
    }
    derived = pd.DataFrame([row])
    derived.to_csv(paths.derived_summary_path, index=False)
    return derived


def save_physical_curve_summary(
    paths: M5Paths,
    idata: az.InferenceData,
    phase_grid: np.ndarray,
    median_observation_sigma: float,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    latent_grid = flatten_posterior_variable(idata, "latent_grid")
    extra_sigma = flatten_posterior_variable(idata, "extra_sigma")
    rng = np.random.default_rng(RANDOM_SEED)
    sigma_grid = np.sqrt(np.square(median_observation_sigma) + np.square(extra_sigma))[:, None]
    predictive_grid = rng.normal(loc=latent_grid, scale=sigma_grid)

    model_low, model_high = quantile_interval(latent_grid, axis=0)
    pred_low, pred_high = quantile_interval(predictive_grid, axis=0)
    curve = pd.DataFrame(
        {
            "phase": phase_grid,
            "model_mean": latent_grid.mean(axis=0),
            "model_hdi_3": model_low,
            "model_hdi_97": model_high,
            "predictive_mean": predictive_grid.mean(axis=0),
            "predictive_hdi_3": pred_low,
            "predictive_hdi_97": pred_high,
        }
    )
    curve.to_csv(paths.physical_curve_summary_path, index=False)
    metrics = {
        "grid_rows": int(len(curve)),
        "model_min_mean": float(curve["model_mean"].min()),
        "phase_at_min_model_mean": float(curve.loc[curve["model_mean"].idxmin(), "phase"]),
    }
    return curve, metrics


def posterior_predictive_observed_samples(idata: az.InferenceData) -> np.ndarray | None:
    if not hasattr(idata, "posterior_predictive") or "obs" not in idata.posterior_predictive:
        return None
    values = np.asarray(idata.posterior_predictive["obs"].values)
    return values.reshape((-1, values.shape[-1]))


def save_posterior_predictive_summary(
    paths: M5Paths,
    idata: az.InferenceData,
    prepared: pd.DataFrame,
) -> tuple[pd.DataFrame, str]:
    latent_train = flatten_posterior_variable(idata, "latent_train")
    predicted_mean = latent_train.mean(axis=0)
    observed = prepared["normalized_flux"].to_numpy(dtype=float)
    predictive = posterior_predictive_observed_samples(idata)
    if predictive is None:
        pred_low = np.full_like(predicted_mean, np.nan)
        pred_high = np.full_like(predicted_mean, np.nan)
        status = "posterior predictive samples unavailable"
    else:
        pred_low, pred_high = quantile_interval(predictive, axis=0)
        status = "created"
    ppc = pd.DataFrame(
        {
            "phase": prepared["phase"].to_numpy(dtype=float),
            "observed_flux": observed,
            "predicted_mean": predicted_mean,
            "predicted_hdi_3": pred_low,
            "predicted_hdi_97": pred_high,
            "residual": observed - predicted_mean,
        }
    ).sort_values("phase")
    ppc.to_csv(paths.posterior_predictive_summary_path, index=False)
    return ppc, status


def save_residual_summary(
    paths: M5Paths,
    idata: az.InferenceData,
    prepared: pd.DataFrame,
    posterior_summary: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    latent_train = flatten_posterior_variable(idata, "latent_train")
    predicted_mean = latent_train.mean(axis=0)
    observed = prepared["normalized_flux"].to_numpy(dtype=float)
    residual = observed - predicted_mean
    extra_sigma_mean = summary_value(posterior_summary, "extra_sigma", "mean")
    sigma_eff_mean = np.sqrt(np.square(prepared["normalized_flux_err"].to_numpy(dtype=float)) + extra_sigma_mean**2)
    standardized_residual = residual / sigma_eff_mean
    residual_table = pd.DataFrame(
        {
            "phase": prepared["phase"].to_numpy(dtype=float),
            "normalized_flux": observed,
            "predicted_mean": predicted_mean,
            "residual": residual,
            "normalized_flux_err": prepared["normalized_flux_err"].to_numpy(dtype=float),
            "sigma_eff_mean": sigma_eff_mean,
            "standardized_residual": standardized_residual,
        }
    )
    residual_table.to_csv(paths.residual_summary_path, index=False)

    predictive = posterior_predictive_observed_samples(idata)
    coverage = float("nan")
    if predictive is not None:
        pred_low, pred_high = quantile_interval(predictive, axis=0)
        coverage = float(((observed >= pred_low) & (observed <= pred_high)).mean())
    metrics = {
        "residual_mean": float(residual.mean()),
        "residual_median": float(np.median(residual)),
        "residual_std": float(residual.std(ddof=1)),
        "standardized_residual_mean": float(np.mean(standardized_residual)),
        "standardized_residual_std": float(np.std(standardized_residual, ddof=1)),
        "posterior_predictive_interval_94_coverage_observed_points": coverage,
    }
    return residual_table, metrics


def read_m1_summary(paths: M5Paths) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "m1_available": False,
        "m1_depth_mean": None,
        "m1_rp_rs_mean": None,
        "m1_baseline_mean": None,
        "m1_transit_half_width": 0.05,
        "m1_source": None,
    }
    if paths.m1_derived_path.exists():
        derived = pd.read_csv(paths.m1_derived_path)
        if not derived.empty:
            row = derived.iloc[0]
            payload.update(
                {
                    "m1_available": True,
                    "m1_depth_mean": float(row.get("depth_mean", np.nan)),
                    "m1_rp_rs_mean": float(row.get("rp_rs_mean", np.nan)),
                    "m1_source": relative_path(paths.m1_derived_path, paths.project_root),
                }
            )
    if paths.m1_posterior_summary_path.exists():
        posterior = pd.read_csv(paths.m1_posterior_summary_path)
        baseline_row = posterior.loc[posterior["parameter"] == "baseline"]
        if not baseline_row.empty:
            payload["m1_baseline_mean"] = float(pd.to_numeric(baseline_row["mean"], errors="coerce").iloc[0])
    return payload


def read_m2_curve(paths: M5Paths) -> pd.DataFrame | None:
    if not paths.m2_curve_path.exists():
        return None
    curve = pd.read_csv(paths.m2_curve_path)
    if {"phase", "latent_mean"}.issubset(curve.columns):
        return curve
    return None


def build_environment_summary() -> dict[str, Any]:
    import sysconfig

    include_dir = Path(sysconfig.get_paths().get("include", ""))
    return {
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "python_include_dir": str(include_dir),
        "python_h_available": (include_dir / "Python.h").exists(),
        "gcc": shutil.which("gcc"),
        "gxx": shutil.which("g++"),
        "pymc": pm.__version__,
        "arviz": az.__version__,
        "pytensor": pytensor.__version__,
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "matplotlib": matplotlib.__version__,
        "pytensor_flags": os.environ.get("PYTENSOR_FLAGS", ""),
    }


def save_model_config(
    paths: M5Paths,
    prepared_metadata: dict[str, Any],
    sample_config: dict[str, Any],
    diagnostics: dict[str, Any],
    curve_metrics: dict[str, Any],
    residual_metrics: dict[str, Any],
    posterior_predictive_status: str,
    m1_summary: dict[str, Any],
    m2_available: bool,
) -> dict[str, Any]:
    config = {
        "model_name": MODEL_NAME,
        "run_id": RUN_ID,
        "created_at_utc": utc_now(),
        "planet_name": PLANET_NAME,
        "planet_slug": PLANET_SLUG,
        "host_star": HOST_STAR,
        "mission": MISSION,
        "source_gold_path": SOURCE_GOLD_PATH,
        "phase_filter": f"abs(phase) <= {PHASE_WINDOW}",
        "quality_filter": "quality == 0 when quality column exists",
        "normalization": {
            "baseline_region": (
                f"{BASELINE_MIN_ABS_PHASE} <= abs(phase) <= {BASELINE_MAX_ABS_PHASE}"
            ),
            "baseline_median": prepared_metadata["baseline_median"],
            "normalized_flux": "flux / baseline_median",
            "normalized_flux_err": "flux_err / baseline_median",
        },
        "model": {
            "shape": "approximate physicalal transit",
            "transit_shape": "clip((half_duration - abs(phase - center)) / ingress_duration, 0, 1)",
            "baseline_prior": "Normal(1.0, 0.01)",
            "depth_prior": "HalfNormal(0.02)",
            "center_prior": "Normal(0.0, 0.01)",
            "half_duration_prior": "Uniform(0.03, 0.12)",
            "ingress_fraction_prior": "Beta(2, 5)",
            "ingress_duration": "ingress_fraction * half_duration",
            "extra_sigma_prior": "HalfNormal(0.005)",
            "likelihood": "Normal(mu_i, sqrt(normalized_flux_err_i^2 + extra_sigma^2))",
            "derived_parameters": [
                "rp_rs = sqrt(depth)",
                "full_duration = 2 * half_duration",
                "flat_duration = 2 * max(half_duration - ingress_duration, 0)",
                "ingress_egress_total = 2 * ingress_duration",
            ],
            "prediction_grid_points": PREDICTION_GRID_POINTS,
        },
        "sampling": sample_config,
        "posterior_predictive_status": posterior_predictive_status,
        "diagnostics": diagnostics,
        "environment": build_environment_summary(),
        "input_summary": prepared_metadata,
        "curve_metrics": curve_metrics,
        "residual_metrics": residual_metrics,
        "m1_comparison": m1_summary,
        "m2_comparison": {
            "m2_available": m2_available,
            "m2_source": relative_path(paths.m2_curve_path, paths.project_root) if m2_available else None,
        },
    }
    paths.model_config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    return config


def save_inference_summary_json(
    paths: M5Paths,
    config: dict[str, Any],
    posterior_summary: pd.DataFrame,
    derived_summary: pd.DataFrame,
    diagnostics: dict[str, Any],
    curve_metrics: dict[str, Any],
    residual_metrics: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "created_at_utc": utc_now(),
        "model_name": MODEL_NAME,
        "run_id": RUN_ID,
        "planet_name": PLANET_NAME,
        "trace_path": relative_path(paths.trace_path, paths.project_root),
        "model_config_path": relative_path(paths.model_config_path, paths.project_root),
        "posterior_summary_path": relative_path(paths.posterior_summary_path, paths.project_root),
        "derived_parameters_summary_path": relative_path(paths.derived_summary_path, paths.project_root),
        "physical_curve_summary_path": relative_path(paths.physical_curve_summary_path, paths.project_root),
        "posterior_predictive_summary_path": relative_path(
            paths.posterior_predictive_summary_path, paths.project_root
        ),
        "residual_summary_path": relative_path(paths.residual_summary_path, paths.project_root),
        "sampling": config["sampling"],
        "input_summary": config["input_summary"],
        "diagnostics": diagnostics,
        "posterior_summary": posterior_summary.to_dict(orient="records"),
        "derived_parameters": derived_summary.to_dict(orient="records")[0],
        "curve_metrics": curve_metrics,
        "residual_metrics": residual_metrics,
        "m1_comparison": config["m1_comparison"],
        "m2_comparison": config["m2_comparison"],
    }
    paths.inference_summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def posterior_values(idata: az.InferenceData, variable: str) -> np.ndarray:
    return np.asarray(idata.posterior[variable].values).reshape(-1)


def save_modeling_input_plot(paths: M5Paths, prepared: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(prepared["phase"], prepared["normalized_flux"], s=8, alpha=0.35, linewidths=0)
    ax.axvline(0, linestyle="--", linewidth=1)
    ax.set_title("M5 input - normalized flux by phase")
    ax.set_xlabel("Phase in days, centered on transit")
    ax.set_ylabel("Normalized flux")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "01_modeling_input.png", dpi=300)
    plt.close(fig)


def save_trace_plot(paths: M5Paths, idata: az.InferenceData) -> None:
    # For the Physical Model, the parameters are different from M3
    variables = ["baseline", "t0", "r", "b", "a", "extra_sigma"]
    fig, axes = plt.subplots(len(variables), 2, figsize=(12, 2.2 * len(variables)))
    for row_index, variable in enumerate(variables):
        values = np.asarray(idata.posterior[variable].values)
        chains, draws = values.shape
        flat = values.reshape(-1)
        axes[row_index, 0].hist(flat, bins=40, alpha=0.85)
        axes[row_index, 0].set_ylabel(variable)
        axes[row_index, 0].grid(True, alpha=0.25)
        for chain_index in range(chains):
            axes[row_index, 1].plot(np.arange(draws), values[chain_index], linewidth=0.7, alpha=0.8)
        axes[row_index, 1].set_ylabel(variable)
        axes[row_index, 1].grid(True, alpha=0.25)
    axes[0, 0].set_title("Posterior distribution")
    axes[0, 1].set_title("Trace by chain")
    axes[-1, 0].set_xlabel("Parameter value")
    axes[-1, 1].set_xlabel("Draw")
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "02_trace_plot.png", dpi=300)
    plt.close(fig)


def save_depth_duration_plot(paths: M5Paths, idata: az.InferenceData) -> None:
    variables = [
        ("depth", "Transit depth"),
        ("full_duration", "Full duration, days"),
        ("b", "Impact Parameter"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    for ax, (variable, title) in zip(axes, variables, strict=True):
        samples = posterior_values(idata, variable)
        ax.hist(samples, bins=50, alpha=0.85)
        ax.axvline(samples.mean(), linestyle="--", linewidth=1.2)
        ax.set_title(title)
        ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "03_posterior_depth_duration.png", dpi=300)
    plt.close(fig)


def save_pairs_plot(paths: M5Paths, idata: az.InferenceData) -> None:
    variables = ["t0", "r", "b", "a"]
    axes = az.plot_pair(idata, var_names=variables, figsize=(10, 10), marginals=True)
    plt.savefig(paths.figure_dir / "04_pairs_plot.png", dpi=300)
    plt.close()


def save_rp_rs_plot(paths: M5Paths, idata: az.InferenceData) -> None:
    samples = posterior_values(idata, "rp_rs")
    low, high = quantile_interval(samples, axis=0)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(samples, bins=50, alpha=0.85)
    ax.axvline(samples.mean(), linestyle="--", linewidth=1.2, label="posterior mean")
    ax.axvline(low, linestyle=":", linewidth=1.2, label="94% interval")
    ax.axvline(high, linestyle=":", linewidth=1.2)
    ax.set_title("M5 posterior Rp/Rs")
    ax.set_xlabel("Rp/Rs")
    ax.set_ylabel("Posterior sample count")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "04_posterior_rp_rs.png", dpi=300)
    plt.close(fig)


def save_physical_fit_plot(paths: M5Paths, prepared: pd.DataFrame, curve: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(prepared["phase"], prepared["normalized_flux"], s=8, alpha=0.30, linewidths=0, label="observed")
    ax.plot(curve["phase"], curve["model_mean"], linewidth=2, label="M5 physical mean")
    ax.fill_between(
        curve["phase"].to_numpy(dtype=float),
        curve["model_hdi_3"].to_numpy(dtype=float),
        curve["model_hdi_97"].to_numpy(dtype=float),
        alpha=0.22,
        label="model 94% interval",
    )
    ax.axvline(0, linestyle="--", linewidth=1)
    ax.set_title("M5 physical fit by phase")
    ax.set_xlabel("Phase in days, centered on transit")
    ax.set_ylabel("Normalized flux")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "05_physical_fit_phase.png", dpi=300)
    plt.close(fig)


def save_posterior_predictive_plot(paths: M5Paths, prepared: pd.DataFrame, curve: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(prepared["phase"], prepared["normalized_flux"], s=8, alpha=0.30, linewidths=0, label="observed")
    ax.plot(curve["phase"], curve["predictive_mean"], linewidth=2, label="predictive mean")
    ax.fill_between(
        curve["phase"].to_numpy(dtype=float),
        curve["predictive_hdi_3"].to_numpy(dtype=float),
        curve["predictive_hdi_97"].to_numpy(dtype=float),
        alpha=0.22,
        label="predictive 94% interval",
    )
    ax.axvline(0, linestyle="--", linewidth=1)
    ax.set_title("M5 posterior predictive check")
    ax.set_xlabel("Phase in days, centered on transit")
    ax.set_ylabel("Normalized flux")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "06_posterior_predictive_check.png", dpi=300)
    plt.close(fig)


def save_residuals_plot(paths: M5Paths, residuals: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(residuals["phase"], residuals["residual"], s=10, alpha=0.45, linewidths=0)
    ax.axhline(0, linestyle="--", linewidth=1)
    ax.set_title("M5 residuals by phase")
    ax.set_xlabel("Phase in days, centered on transit")
    ax.set_ylabel("Residual: observed - predicted mean")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "07_residuals_by_phase.png", dpi=300)
    plt.close(fig)


def save_comparison_plot(
    paths: M5Paths,
    prepared: pd.DataFrame,
    curve: pd.DataFrame,
    m1_summary: dict[str, Any],
    m2_curve: pd.DataFrame | None,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(prepared["phase"], prepared["normalized_flux"], s=8, alpha=0.24, linewidths=0, label="observed")
    if m1_summary.get("m1_available") and m1_summary.get("m1_depth_mean") is not None:
        phase = curve["phase"].to_numpy(dtype=float)
        baseline = m1_summary.get("m1_baseline_mean") or 1.0
        depth = float(m1_summary["m1_depth_mean"])
        half_width = float(m1_summary.get("m1_transit_half_width") or 0.05)
        m1_box = np.where(np.abs(phase) <= half_width, baseline - depth, baseline)
        ax.plot(phase, m1_box, linewidth=1.8, linestyle="--", label="M1 box")
    if m2_curve is not None:
        ax.plot(m2_curve["phase"], m2_curve["latent_mean"], linewidth=1.8, label="M2 smooth")
    ax.plot(curve["phase"], curve["model_mean"], linewidth=2.2, label="M5 physical")
    ax.axvline(0, linestyle=":", linewidth=1)
    ax.set_title("Qualitative comparison: M1, M2 and M5")
    ax.set_xlabel("Phase in days, centered on transit")
    ax.set_ylabel("Normalized flux")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "08_comparison_m1_m2_m5.png", dpi=300)
    plt.close(fig)


def save_figures(
    paths: M5Paths,
    prepared: pd.DataFrame,
    idata: az.InferenceData,
    curve: pd.DataFrame,
    residuals: pd.DataFrame,
    m1_summary: dict[str, Any],
    m2_curve: pd.DataFrame | None,
) -> None:
    save_modeling_input_plot(paths, prepared)
    save_trace_plot(paths, idata)
    save_depth_duration_plot(paths, idata)
    save_rp_rs_plot(paths, idata)
    save_physical_fit_plot(paths, prepared, curve)
    save_posterior_predictive_plot(paths, prepared, curve)
    save_residuals_plot(paths, residuals)
    save_comparison_plot(paths, prepared, curve, m1_summary, m2_curve)


def dataframe_to_markdown(dataframe: pd.DataFrame, max_rows: int = 12) -> str:
    if dataframe.empty:
        return "_Tabela vazia._"
    rendered = dataframe.head(max_rows).copy()
    rendered = rendered.astype(object).where(pd.notna(rendered), "")
    columns = [str(column) for column in rendered.columns]
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for _, row in rendered.iterrows():
        values = [str(row[column]).replace("\n", " ") for column in rendered.columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join([header, separator, *rows])


def save_report(
    paths: M5Paths,
    config: dict[str, Any],
    posterior_summary: pd.DataFrame,
    derived_summary: pd.DataFrame,
    residual_metrics: dict[str, Any],
) -> None:
    diagnostics = config["diagnostics"]
    sampling = config["sampling"]
    derived = derived_summary.iloc[0]
    bfmi_display = "not available" if diagnostics["bfmi_min"] is None else f"{diagnostics['bfmi_min']:.8f}"
    selected_summary = posterior_summary.loc[
        posterior_summary["parameter"].isin(
            ["baseline", "depth", "center", "half_duration", "ingress_duration", "extra_sigma", "rp_rs"]
        ),
        ["parameter", "mean", "hdi_3%", "hdi_97%", "r_hat", "ess_bulk", "ess_tail"],
    ]
    m1_depth = config["m1_comparison"].get("m1_depth_mean")
    m2_text = "M2 curve available." if config["m2_comparison"]["m2_available"] else "M2 curve unavailable."
    report = f"""# M5 - Bayesian Physical Transit - HAT-P-7 b

## 1. Objetivo do M5

O M5 aproxima o trânsito de HAT-P-7 b por uma forma physicalal bayesiana. O
modelo estima profundidade, centro, duração total aproximada, ingresso/egresso,
baseline e ruído extra.

## 2. Diferença Entre M1, M2 e M5

- M1 estima uma profundidade em uma forma box-shaped fixa.
- M2 estima uma função suave preditiva em fase, sem parâmetros físicos diretos.
- M5 estima uma forma physicalal paramétrica, mais interpretável que M2 e mais flexível que M1.

## 3. Dataset Usado

Entrada:

```text
{SOURCE_GOLD_PATH}
```

Dataset efetivo:

```text
{relative_path(paths.modeling_input_path, paths.project_root)}
```

Pontos usados:

```text
{config['input_summary']['rows_used']}
```

## 4. Pré-processamento

Foram mantidas as regras de M1/M2:

- `abs(phase) <= {PHASE_WINDOW}`;
- `quality == 0`;
- remoção de `phase`, `flux` ou `flux_err` ausentes;
- remoção de `flux_err <= 0`;
- normalização local pela mediana em `0,08 <= abs(phase) <= 0,15`.

Baseline mediano:

```text
{config['input_summary']['baseline_median']}
```

## 5. Especificação Physicalal

Com `d = abs(phase - center)`:

```text
transit_shape = clip((half_duration - d) / ingress_duration, 0, 1)
mu = baseline - depth * transit_shape
```

Essa forma produz:

- `transit_shape = 1` no fundo plano;
- `0 < transit_shape < 1` no ingresso/egresso;
- `transit_shape = 0` fora do trânsito.

## 6. Priors

```text
baseline ~ Normal(1.0, 0.01)
depth ~ HalfNormal(0.02)
center ~ Normal(0.0, 0.01)
half_duration ~ Uniform(0.03, 0.12)
ingress_fraction ~ Beta(2, 5)
ingress_duration = ingress_fraction * half_duration
extra_sigma ~ HalfNormal(0.005)
```

## 7. Likelihood

```text
sigma_eff_i = sqrt(normalized_flux_err_i^2 + extra_sigma^2)
normalized_flux_i ~ Normal(mu_i, sigma_eff_i)
```

## 8. Resultados Posteriores

Arquivo:

```text
{relative_path(paths.posterior_summary_path, paths.project_root)}
```

Resumo:

{dataframe_to_markdown(selected_summary)}

## 9. Parâmetros Derivados

Arquivo:

```text
{relative_path(paths.derived_summary_path, paths.project_root)}
```

Principais resultados:

```text
depth = {derived['depth_mean']:.8f}, HDI 94% [{derived['depth_hdi_3']:.8f}, {derived['depth_hdi_97']:.8f}]
Rp/Rs = {derived['rp_rs_mean']:.8f}, HDI 94% [{derived['rp_rs_hdi_3']:.8f}, {derived['rp_rs_hdi_97']:.8f}]
center = {derived['center_mean']:.8f}, HDI 94% [{derived['center_hdi_3']:.8f}, {derived['center_hdi_97']:.8f}]
full_duration = {derived['full_duration_mean_days']:.8f} dias = {derived['full_duration_mean_hours']:.4f} horas
ingress_duration = {derived['ingress_duration_mean_days']:.8f} dias = {derived['ingress_duration_mean_hours']:.4f} horas
```

## 10. Posterior Predictive Check

Arquivo:

```text
{relative_path(paths.posterior_predictive_summary_path, paths.project_root)}
```

Cobertura aproximada do intervalo preditivo de 94% nos pontos observados:

```text
{residual_metrics['posterior_predictive_interval_94_coverage_observed_points']:.6f}
```

Figura:

![Posterior predictive M5](../figures/bayesian_physical_transit/hat_p_7_b/06_posterior_predictive_check.png)

## 11. Resíduos

Arquivo:

```text
{relative_path(paths.residual_summary_path, paths.project_root)}
```

Métricas:

- média dos resíduos: `{residual_metrics['residual_mean']:.8f}`
- mediana dos resíduos: `{residual_metrics['residual_median']:.8f}`
- desvio padrão dos resíduos: `{residual_metrics['residual_std']:.8f}`
- desvio padrão dos resíduos padronizados: `{residual_metrics['standardized_residual_std']:.8f}`

Figura:

![Resíduos M5](../figures/bayesian_physical_transit/hat_p_7_b/07_residuals_by_phase.png)

## 12. Comparação Qualitativa com M1 e M2

M1 depth robusto:

```text
{m1_depth}
```

M2:

```text
{m2_text}
```

Figura:

![Comparação M1 M2 M5](../figures/bayesian_physical_transit/hat_p_7_b/08_comparison_m1_m2_m5.png)

## 13. Diagnósticos MCMC

- sampler: `{sampling['sampler']}`
- draws: `{sampling['draws']}`
- tune: `{sampling['tune']}`
- chains: `{sampling['chains']}`
- target_accept final: `{sampling['target_accept']}`
- divergências: `{diagnostics['divergences']}`
- R-hat máximo: `{diagnostics['max_r_hat']:.8f}`
- ESS mínimo: `{diagnostics['min_ess']:.8f}`
- aceitação média: `{diagnostics['acceptance_mean']:.8f}`
- BFMI mínimo: `{bfmi_display}`
- recomendado para interpretação M5: `{diagnostics['recommended_for_m5_interpretation']}`

Nota:

```text
{diagnostics['convergence_note']}
```

## 14. Interpretação Astrofísica Preliminar

M5 é mais interpretável que M2 porque estima explicitamente profundidade,
centro e durações aproximadas. Também é mais flexível que M1 por incluir
ingresso e egresso.

## 15. Limitações

M5 ainda:

- não usa limb darkening;
- não usa geometria orbital completa;
- não usa Mandel & Agol;
- assume erros independentes condicionais;
- usa apenas Kepler;
- não é modelo físico final.

## 16. Próximos Passos

O próximo passo é M4: comparação de M1, M2 e M5 por posterior predictive
checks, erro preditivo e, se adequado, LOO/WAIC.
"""
    paths.report_path.write_text(report, encoding="utf-8")


def main() -> None:
    paths = build_paths()
    ensure_directories(paths)

    raw = read_gold_transit_window(paths)
    prepared, prepared_metadata = prepare_modeling_input(raw, paths)
    phase_grid = np.linspace(-PHASE_WINDOW, PHASE_WINDOW, PREDICTION_GRID_POINTS)

    model = build_model(prepared, phase_grid)
    idata, sample_config = sample_nuts(model)
    idata, posterior_predictive_status = sample_posterior_predictive(model, idata)

    save_trace(paths, idata)
    posterior_summary = save_posterior_summary(paths, idata)
    derived_summary = save_derived_summary(paths, posterior_summary)
    diagnostics = diagnostics_from_summary(posterior_summary, idata)
    curve, curve_metrics = save_physical_curve_summary(
        paths,
        idata,
        phase_grid,
        prepared_metadata["normalized_flux_err_median"],
    )
    ppc_summary, ppc_status = save_posterior_predictive_summary(paths, idata, prepared)
    if posterior_predictive_status != "created":
        ppc_status = posterior_predictive_status
    residuals, residual_metrics = save_residual_summary(paths, idata, prepared, posterior_summary)
    m1_summary = read_m1_summary(paths)
    m2_curve = read_m2_curve(paths)

    config = save_model_config(
        paths,
        prepared_metadata,
        sample_config,
        diagnostics,
        curve_metrics,
        residual_metrics,
        ppc_status,
        m1_summary,
        m2_curve is not None,
    )
    save_inference_summary_json(paths, config, posterior_summary, derived_summary, diagnostics, curve_metrics, residual_metrics)
    save_figures(paths, prepared, idata, curve, residuals, m1_summary, m2_curve)
    save_report(paths, config, posterior_summary, derived_summary, residual_metrics)

    derived = derived_summary.iloc[0]
    print(
        json.dumps(
            {
                "model_name": MODEL_NAME,
                "run_id": RUN_ID,
                "points_used": prepared_metadata["rows_used"],
                "trace": relative_path(paths.trace_path, paths.project_root),
                "posterior_summary": relative_path(paths.posterior_summary_path, paths.project_root),
                "derived_parameters_summary": relative_path(paths.derived_summary_path, paths.project_root),
                "physical_curve_summary": relative_path(paths.physical_curve_summary_path, paths.project_root),
                "posterior_predictive_summary": relative_path(paths.posterior_predictive_summary_path, paths.project_root),
                "residual_summary": relative_path(paths.residual_summary_path, paths.project_root),
                "report": relative_path(paths.report_path, paths.project_root),
                "target_accept": sample_config["target_accept"],
                "max_r_hat": diagnostics["max_r_hat"],
                "min_ess": diagnostics["min_ess"],
                "divergences": diagnostics["divergences"],
                "depth_mean": float(derived["depth_mean"]),
                "rp_rs_mean": float(derived["rp_rs_mean"]),
                "full_duration_mean_days": float(derived["full_duration_mean_days"]),
                "ingress_duration_mean_days": float(derived["ingress_duration_mean_days"]),
                "recommended_for_m5_interpretation": diagnostics["recommended_for_m5_interpretation"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
