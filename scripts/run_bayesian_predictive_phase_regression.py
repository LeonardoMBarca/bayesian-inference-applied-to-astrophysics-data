"""Run M2 Bayesian predictive phase regression for HAT-P-7 b.

M2 models normalized flux as a smooth function of orbital phase using fixed
Gaussian radial basis functions. It reads the existing GOLD transit-window
table and writes new artifacts under the bayesian_predictive_phase_regression
family without modifying RAW, Silver, Gold, or M1 outputs.
"""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MPLCONFIGDIR = Path("/tmp") / "matplotlib-cache"
MPLCONFIGDIR.mkdir(parents=True, exist_ok=True)
os.environ["MPLCONFIGDIR"] = str(MPLCONFIGDIR)

PYTENSOR_CACHE = Path("/tmp") / "pytensor-cache-m2-predictive"
PYTENSOR_CACHE.mkdir(parents=True, exist_ok=True)
os.environ["PYTENSOR_FLAGS"] = f"base_compiledir={PYTENSOR_CACHE}"

import arviz as az  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pymc as pm  # noqa: E402
import pytensor  # noqa: E402


PLANET_NAME = "HAT-P-7 b"
PLANET_SLUG = "hat_p_7_b"
HOST_STAR = "HAT-P-7"
MISSION = "Kepler"
MODEL_NAME = "M2_bayesian_predictive_phase_regression"
RUN_ID = "001_nuts"
SOURCE_GOLD_PATH = "data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv"

PHASE_WINDOW = 0.15
BASELINE_MIN_ABS_PHASE = 0.08
BASELINE_MAX_ABS_PHASE = 0.15
N_BASIS = 12
BASIS_WIDTH = 0.035
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

SUMMARY_VAR_NAMES = ["intercept", "weight_sigma", "extra_sigma", "weights"]
TRACE_WEIGHT_INDICES = [0, 3, 6, 9, 11]


@dataclass(frozen=True)
class M2Paths:
    """Filesystem paths for M2 artifacts."""

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
    prediction_grid_path: Path
    posterior_summary_path: Path
    predictive_curve_summary_path: Path
    residual_summary_path: Path
    m1_derived_path: Path
    m1_posterior_summary_path: Path


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


def build_paths(project_root: Path | None = None) -> M2Paths:
    root = resolve_project_root(project_root)
    model_dir = (
        root
        / "models"
        / "bayesian_predictive_phase_regression"
        / PLANET_SLUG
        / "runs"
        / RUN_ID
    )
    table_dir = root / "tables" / "bayesian_predictive_phase_regression" / PLANET_SLUG
    figure_dir = root / "figures" / "bayesian_predictive_phase_regression" / PLANET_SLUG
    return M2Paths(
        project_root=root,
        source_gold=root / SOURCE_GOLD_PATH,
        model_dir=model_dir,
        table_dir=table_dir,
        figure_dir=figure_dir,
        report_path=root / "reports" / "bayesian_predictive_phase_regression_hat_p_7_b_report.md",
        notebook_path=root / "notebooks" / "04_bayesian_predictive_phase_regression_hat_p_7_b.ipynb",
        docs_dir=root / "docs" / "modeling" / "bayesian_predictive_phase_regression_hat_p_7_b",
        trace_path=model_dir / "trace.nc",
        model_config_path=model_dir / "model_config.json",
        inference_summary_path=model_dir / "inference_data_summary.json",
        modeling_input_path=table_dir / "modeling_input_predictive.csv",
        prediction_grid_path=table_dir / "prediction_grid.csv",
        posterior_summary_path=table_dir / "posterior_summary.csv",
        predictive_curve_summary_path=table_dir / "predictive_curve_summary.csv",
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
    )


def ensure_directories(paths: M2Paths) -> None:
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


def read_gold_transit_window(paths: M2Paths) -> pd.DataFrame:
    if not paths.source_gold.exists():
        raise FileNotFoundError(f"Missing GOLD input: {paths.source_gold}")
    dataframe = pd.read_csv(paths.source_gold, low_memory=False)
    for column in ["phase", "flux", "flux_err", "quality", "time"]:
        if column in dataframe.columns:
            dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")
    return dataframe


def prepare_modeling_input(dataframe: pd.DataFrame, paths: M2Paths) -> tuple[pd.DataFrame, dict[str, Any]]:
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


def radial_basis_matrix(x_values: np.ndarray, centers: np.ndarray, width: float) -> np.ndarray:
    x = np.asarray(x_values, dtype=float)[:, None]
    c = np.asarray(centers, dtype=float)[None, :]
    return np.exp(-0.5 * np.square((x - c) / width))


def save_prediction_grid(
    paths: M2Paths,
    phase_grid: np.ndarray,
    centers: np.ndarray,
    basis_grid: np.ndarray,
) -> pd.DataFrame:
    payload: dict[str, np.ndarray] = {"phase": phase_grid}
    for index, center in enumerate(centers):
        payload[f"rbf_{index:02d}_center_{center:+.5f}"] = basis_grid[:, index]
    grid = pd.DataFrame(payload)
    grid.to_csv(paths.prediction_grid_path, index=False)
    return grid


def build_model(
    prepared: pd.DataFrame,
    basis_train: np.ndarray,
    basis_grid: np.ndarray,
) -> pm.Model:
    y = prepared["normalized_flux"].to_numpy(dtype=float)
    sigma_obs = prepared["normalized_flux_err"].to_numpy(dtype=float)
    coords = {
        "observation": np.arange(len(prepared)),
        "basis": np.arange(N_BASIS),
        "grid": np.arange(basis_grid.shape[0]),
    }

    with pm.Model(coords=coords) as model:
        intercept = pm.Normal("intercept", mu=1.0, sigma=0.01)
        weight_sigma = pm.HalfNormal("weight_sigma", sigma=0.01)
        weights_raw = pm.Normal("weights_raw", mu=0.0, sigma=1.0, dims="basis")
        weights = pm.Deterministic("weights", weights_raw * weight_sigma, dims="basis")
        extra_sigma = pm.HalfNormal("extra_sigma", sigma=0.005)

        latent_train = pm.Deterministic(
            "latent_train",
            intercept + pm.math.dot(basis_train, weights),
            dims="observation",
        )
        pm.Deterministic(
            "latent_grid",
            intercept + pm.math.dot(basis_grid, weights),
            dims="grid",
        )
        sigma_eff = pm.math.sqrt(np.square(sigma_obs) + extra_sigma**2)
        pm.Normal("obs", mu=latent_train, sigma=sigma_eff, observed=y, dims="observation")
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
    except Exception as exc:  # pragma: no cover - explicit runtime safeguard
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


def save_trace(paths: M2Paths, idata: az.InferenceData) -> None:
    paths.trace_path.unlink(missing_ok=True)
    idata.to_netcdf(paths.trace_path)


def save_posterior_summary(paths: M2Paths, idata: az.InferenceData, centers: np.ndarray) -> pd.DataFrame:
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

    def basis_index(parameter: str) -> float:
        match = re.match(r"weights\[(\d+)\]", str(parameter))
        return float(match.group(1)) if match else float("nan")

    summary["basis_index"] = summary["parameter"].map(basis_index)
    summary["basis_center"] = summary["basis_index"].map(
        lambda value: centers[int(value)] if math.isfinite(value) else np.nan
    )
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
        "recommended_for_m2_predictive_interpretation": recommended,
        "convergence_note": (
            "NUTS diagnostics satisfy the project criteria for M2 predictive interpretation."
            if recommended
            else "Review diagnostics before treating M2 as a reliable predictive model."
        ),
    }


def posterior_predictive_observed_samples(idata: az.InferenceData) -> np.ndarray | None:
    if not hasattr(idata, "posterior_predictive") or "obs" not in idata.posterior_predictive:
        return None
    values = np.asarray(idata.posterior_predictive["obs"].values)
    return values.reshape((-1, values.shape[-1]))


def save_predictive_curve_summary(
    paths: M2Paths,
    idata: az.InferenceData,
    phase_grid: np.ndarray,
    median_observation_sigma: float,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    latent_grid = flatten_posterior_variable(idata, "latent_grid")
    extra_sigma = flatten_posterior_variable(idata, "extra_sigma")
    rng = np.random.default_rng(RANDOM_SEED)

    sigma_grid = np.sqrt(np.square(median_observation_sigma) + np.square(extra_sigma))[:, None]
    predictive_grid = rng.normal(loc=latent_grid, scale=sigma_grid)

    latent_low, latent_high = quantile_interval(latent_grid, axis=0)
    predictive_low, predictive_high = quantile_interval(predictive_grid, axis=0)

    curve = pd.DataFrame(
        {
            "phase": phase_grid,
            "latent_mean": latent_grid.mean(axis=0),
            "latent_hdi_3": latent_low,
            "latent_hdi_97": latent_high,
            "predictive_mean": predictive_grid.mean(axis=0),
            "predictive_hdi_3": predictive_low,
            "predictive_hdi_97": predictive_high,
        }
    )
    curve.to_csv(paths.predictive_curve_summary_path, index=False)

    edge_mask = np.abs(phase_grid) >= BASELINE_MIN_ABS_PHASE
    baseline_level_samples = latent_grid[:, edge_mask].mean(axis=1)
    min_flux_samples = latent_grid.min(axis=1)
    predicted_depth_samples = baseline_level_samples - min_flux_samples
    depth_low, depth_high = quantile_interval(predicted_depth_samples, axis=0)
    min_phase_samples = phase_grid[np.argmin(latent_grid, axis=1)]
    depth_summary = {
        "predicted_depth_mean": float(predicted_depth_samples.mean()),
        "predicted_depth_hdi_3": float(depth_low),
        "predicted_depth_hdi_97": float(depth_high),
        "baseline_level_mean": float(baseline_level_samples.mean()),
        "min_latent_flux_mean": float(min_flux_samples.mean()),
        "phase_at_min_latent_median": float(np.median(min_phase_samples)),
        "interpretation_note": (
            "Exploratory depth derived from the smooth predictive curve; not a "
            "direct physical depth parameter and not equivalent to Rp/Rs."
        ),
    }
    return curve, depth_summary


def save_residual_summary(
    paths: M2Paths,
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

    ppc_samples = posterior_predictive_observed_samples(idata)
    coverage = float("nan")
    if ppc_samples is not None:
        pred_low, pred_high = quantile_interval(ppc_samples, axis=0)
        coverage = float(((observed >= pred_low) & (observed <= pred_high)).mean())

    residual_metrics = {
        "residual_mean": float(residual.mean()),
        "residual_median": float(np.median(residual)),
        "residual_std": float(residual.std(ddof=1)),
        "standardized_residual_mean": float(np.mean(standardized_residual)),
        "standardized_residual_std": float(np.std(standardized_residual, ddof=1)),
        "posterior_predictive_interval_94_coverage_observed_points": coverage,
    }
    return residual_table, residual_metrics


def read_m1_summary(paths: M2Paths) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "m1_available": False,
        "m1_depth_mean": None,
        "m1_depth_hdi_3": None,
        "m1_depth_hdi_97": None,
        "m1_rp_rs_mean": None,
        "m1_source": None,
        "m1_baseline_mean": None,
        "m1_transit_half_width": 0.05,
    }
    if paths.m1_derived_path.exists():
        derived = pd.read_csv(paths.m1_derived_path)
        if not derived.empty:
            row = derived.iloc[0]
            payload.update(
                {
                    "m1_available": True,
                    "m1_depth_mean": float(row.get("depth_mean", np.nan)),
                    "m1_depth_hdi_3": float(row.get("depth_hdi_3", np.nan)),
                    "m1_depth_hdi_97": float(row.get("depth_hdi_97", np.nan)),
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
    paths: M2Paths,
    prepared_metadata: dict[str, Any],
    sample_config: dict[str, Any],
    diagnostics: dict[str, Any],
    depth_summary: dict[str, Any],
    residual_metrics: dict[str, Any],
    posterior_predictive_status: str,
    m1_summary: dict[str, Any],
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
        "basis": {
            "type": "fixed Gaussian radial basis functions",
            "n_basis": N_BASIS,
            "basis_width": BASIS_WIDTH,
            "phase_window": [-PHASE_WINDOW, PHASE_WINDOW],
            "centers": np.linspace(-PHASE_WINDOW, PHASE_WINDOW, N_BASIS).tolist(),
        },
        "model": {
            "latent_function": "f(x) = intercept + sum_k weights_k * phi_k(x)",
            "basis_function": "phi_k(x) = exp(-0.5 * ((x - center_k) / basis_width)^2)",
            "intercept_prior": "Normal(1.0, 0.01)",
            "weight_sigma_prior": "HalfNormal(0.01)",
            "weights_prior": "weights_raw ~ Normal(0, 1); weights = weights_raw * weight_sigma",
            "extra_sigma_prior": "HalfNormal(0.005)",
            "likelihood": "Normal(f(phase_i), sqrt(normalized_flux_err_i^2 + extra_sigma^2))",
            "prediction_grid_points": PREDICTION_GRID_POINTS,
            "exploratory_predicted_depth": (
                "baseline_level - min(f_grid), with baseline_level defined as "
                "mean f_grid for abs(phase) >= 0.08"
            ),
        },
        "sampling": sample_config,
        "posterior_predictive_status": posterior_predictive_status,
        "diagnostics": diagnostics,
        "environment": build_environment_summary(),
        "input_summary": prepared_metadata,
        "derived_predictive_depth": depth_summary,
        "residual_metrics": residual_metrics,
        "m1_comparison": m1_summary,
    }
    paths.model_config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    return config


def save_inference_summary_json(
    paths: M2Paths,
    config: dict[str, Any],
    posterior_summary: pd.DataFrame,
    diagnostics: dict[str, Any],
    depth_summary: dict[str, Any],
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
        "predictive_curve_summary_path": relative_path(
            paths.predictive_curve_summary_path, paths.project_root
        ),
        "residual_summary_path": relative_path(paths.residual_summary_path, paths.project_root),
        "sampling": config["sampling"],
        "input_summary": config["input_summary"],
        "diagnostics": diagnostics,
        "posterior_summary": posterior_summary.to_dict(orient="records"),
        "derived_predictive_depth": depth_summary,
        "residual_metrics": residual_metrics,
        "m1_comparison": config["m1_comparison"],
    }
    paths.inference_summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def save_modeling_input_plot(paths: M2Paths, prepared: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    subset = prepared.iloc[:: max(1, len(prepared) // 250)]
    ax.errorbar(
        subset["phase"],
        subset["normalized_flux"],
        yerr=subset["normalized_flux_err"],
        fmt=".",
        markersize=3,
        alpha=0.45,
        linewidth=0.5,
        label="observed normalized flux",
    )
    ax.scatter(prepared["phase"], prepared["normalized_flux"], s=8, alpha=0.35, linewidths=0)
    ax.axvline(0, linestyle="--", linewidth=1)
    ax.set_title("M2 input - normalized flux by phase")
    ax.set_xlabel("Phase in days, centered on transit")
    ax.set_ylabel("Normalized flux")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "01_modeling_input.png", dpi=300)
    plt.close(fig)


def save_basis_functions_plot(
    paths: M2Paths,
    phase_grid: np.ndarray,
    centers: np.ndarray,
    basis_grid: np.ndarray,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    for index, center in enumerate(centers):
        ax.plot(phase_grid, basis_grid[:, index], linewidth=1.2, label=f"c={center:+.3f}")
    ax.set_title("M2 Gaussian radial basis functions")
    ax.set_xlabel("Phase in days, centered on transit")
    ax.set_ylabel("Basis value")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper center", ncol=4, fontsize=8)
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "02_basis_functions.png", dpi=300)
    plt.close(fig)


def save_trace_plot(paths: M2Paths, idata: az.InferenceData) -> None:
    variables: list[tuple[str, np.ndarray]] = [
        ("intercept", np.asarray(idata.posterior["intercept"].values)),
        ("weight_sigma", np.asarray(idata.posterior["weight_sigma"].values)),
        ("extra_sigma", np.asarray(idata.posterior["extra_sigma"].values)),
    ]
    weights = np.asarray(idata.posterior["weights"].values)
    for index in TRACE_WEIGHT_INDICES:
        if index < weights.shape[-1]:
            variables.append((f"weights[{index}]", weights[:, :, index]))

    fig, axes = plt.subplots(len(variables), 2, figsize=(12, 2.2 * len(variables)))
    if len(variables) == 1:
        axes = np.asarray([axes])
    for row_index, (name, values) in enumerate(variables):
        chains, draws = values.shape
        flattened = values.reshape(-1)
        axes[row_index, 0].hist(flattened, bins=40, alpha=0.85)
        axes[row_index, 0].set_ylabel(name)
        axes[row_index, 0].grid(True, alpha=0.25)
        for chain_index in range(chains):
            axes[row_index, 1].plot(np.arange(draws), values[chain_index], linewidth=0.7, alpha=0.8)
        axes[row_index, 1].grid(True, alpha=0.25)
        axes[row_index, 1].set_ylabel(name)
    axes[0, 0].set_title("Posterior distribution")
    axes[0, 1].set_title("Trace by chain")
    axes[-1, 0].set_xlabel("Parameter value")
    axes[-1, 1].set_xlabel("Draw")
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "03_trace_plot.png", dpi=300)
    plt.close(fig)


def save_posterior_weights_plot(paths: M2Paths, posterior_summary: pd.DataFrame) -> None:
    weights = posterior_summary.loc[posterior_summary["parameter"].str.startswith("weights[")].copy()
    weights = weights.sort_values("basis_center")
    centers = weights["basis_center"].to_numpy(dtype=float)
    means = weights["mean"].to_numpy(dtype=float)
    lows = weights["hdi_3%"].to_numpy(dtype=float)
    highs = weights["hdi_97%"].to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axhline(0, linestyle="--", linewidth=1)
    ax.errorbar(
        centers,
        means,
        yerr=[means - lows, highs - means],
        fmt="o",
        capsize=3,
        linewidth=1,
        label="posterior mean and 94% HDI",
    )
    ax.set_title("M2 posterior weights by basis center")
    ax.set_xlabel("Basis center")
    ax.set_ylabel("Weight")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "04_posterior_weights.png", dpi=300)
    plt.close(fig)


def save_predictive_curve_latent_plot(paths: M2Paths, prepared: pd.DataFrame, curve: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(prepared["phase"], prepared["normalized_flux"], s=8, alpha=0.30, linewidths=0, label="observed")
    ax.plot(curve["phase"], curve["latent_mean"], linewidth=2, label="latent mean")
    ax.fill_between(
        curve["phase"].to_numpy(dtype=float),
        curve["latent_hdi_3"].to_numpy(dtype=float),
        curve["latent_hdi_97"].to_numpy(dtype=float),
        alpha=0.22,
        label="latent 94% interval",
    )
    ax.axvline(0, linestyle="--", linewidth=1)
    ax.set_title("M2 latent predictive curve")
    ax.set_xlabel("Phase in days, centered on transit")
    ax.set_ylabel("Normalized flux")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "05_predictive_curve_latent.png", dpi=300)
    plt.close(fig)


def save_posterior_predictive_plot(paths: M2Paths, prepared: pd.DataFrame, curve: pd.DataFrame) -> None:
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
    ax.set_title("M2 posterior predictive observations")
    ax.set_xlabel("Phase in days, centered on transit")
    ax.set_ylabel("Normalized flux")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "06_posterior_predictive_observations.png", dpi=300)
    plt.close(fig)


def save_residuals_plot(paths: M2Paths, residuals: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(residuals["phase"], residuals["residual"], s=10, alpha=0.45, linewidths=0)
    ax.axhline(0, linestyle="--", linewidth=1)
    ax.set_title("M2 residuals by phase")
    ax.set_xlabel("Phase in days, centered on transit")
    ax.set_ylabel("Residual: observed - predicted mean")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "07_residuals_by_phase.png", dpi=300)
    plt.close(fig)


def save_comparison_with_m1_plot(
    paths: M2Paths,
    prepared: pd.DataFrame,
    curve: pd.DataFrame,
    m1_summary: dict[str, Any],
) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(prepared["phase"], prepared["normalized_flux"], s=8, alpha=0.25, linewidths=0, label="observed")
    ax.plot(curve["phase"], curve["latent_mean"], linewidth=2, label="M2 latent mean")
    if m1_summary.get("m1_available") and m1_summary.get("m1_depth_mean") is not None:
        phase = curve["phase"].to_numpy(dtype=float)
        baseline = m1_summary.get("m1_baseline_mean") or 1.0
        depth = float(m1_summary["m1_depth_mean"])
        half_width = float(m1_summary.get("m1_transit_half_width") or 0.05)
        m1_box = np.where(np.abs(phase) <= half_width, baseline - depth, baseline)
        ax.plot(phase, m1_box, linewidth=2, linestyle="--", label="M1 robust box mean")
    ax.axvline(0, linestyle=":", linewidth=1)
    ax.set_title("M2 smooth predictive curve vs M1 box baseline")
    ax.set_xlabel("Phase in days, centered on transit")
    ax.set_ylabel("Normalized flux")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "08_comparison_with_m1.png", dpi=300)
    plt.close(fig)


def save_figures(
    paths: M2Paths,
    prepared: pd.DataFrame,
    phase_grid: np.ndarray,
    centers: np.ndarray,
    basis_grid: np.ndarray,
    idata: az.InferenceData,
    posterior_summary: pd.DataFrame,
    curve: pd.DataFrame,
    residuals: pd.DataFrame,
    m1_summary: dict[str, Any],
) -> None:
    save_modeling_input_plot(paths, prepared)
    save_basis_functions_plot(paths, phase_grid, centers, basis_grid)
    save_trace_plot(paths, idata)
    save_posterior_weights_plot(paths, posterior_summary)
    save_predictive_curve_latent_plot(paths, prepared, curve)
    save_posterior_predictive_plot(paths, prepared, curve)
    save_residuals_plot(paths, residuals)
    save_comparison_with_m1_plot(paths, prepared, curve, m1_summary)


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
    paths: M2Paths,
    config: dict[str, Any],
    posterior_summary: pd.DataFrame,
    depth_summary: dict[str, Any],
    residual_metrics: dict[str, Any],
) -> None:
    diagnostics = config["diagnostics"]
    sampling = config["sampling"]
    basis = config["basis"]
    input_summary = config["input_summary"]
    m1 = config["m1_comparison"]
    bfmi_display = (
        "not available"
        if diagnostics["bfmi_min"] is None
        else f"{diagnostics['bfmi_min']:.8f}"
    )
    m1_depth = m1.get("m1_depth_mean")
    if m1_depth is None or pd.isna(m1_depth):
        depth_difference_text = "M1 robust depth unavailable."
    else:
        difference = depth_summary["predicted_depth_mean"] - float(m1_depth)
        depth_difference_text = (
            f"M2 predicted_depth exploratório = {depth_summary['predicted_depth_mean']:.8f}; "
            f"M1 depth paramétrico = {float(m1_depth):.8f}; "
            f"diferença M2 - M1 = {difference:.8f}."
        )

    weights_preview = posterior_summary.loc[
        posterior_summary["parameter"].str.startswith("weights["),
        ["parameter", "basis_center", "mean", "hdi_3%", "hdi_97%", "r_hat"],
    ]

    report = f"""# M2 - Bayesian Predictive Phase Regression - HAT-P-7 b

## 1. Objetivo do M2

O M2 modela o fluxo normalizado de HAT-P-7 b como uma função suave da fase
orbital. Diferente do M1, ele não assume forma box-shaped e não estima
diretamente uma profundidade física como parâmetro primário.

O objetivo é obter:

- curva preditiva média;
- intervalo de credibilidade da função latente;
- intervalo preditivo para observações futuras;
- diagnóstico de resíduos;
- comparação qualitativa com o M1 robusto.

## 2. Diferença Entre M1 e M2

M1 pergunta:

```text
Qual a profundidade média do trânsito assumindo uma forma box?
```

M2 pergunta:

```text
Qual função suave de fluxo em função da fase é suportada pelos dados?
```

Assim, M2 é preditivo e flexível. Ele ajuda a descrever a forma observada da
curva, mas não substitui um modelo físico de trânsito.

## 3. Dataset Usado

Entrada:

```text
{SOURCE_GOLD_PATH}
```

Dataset efetivo:

```text
{relative_path(paths.modeling_input_path, paths.project_root)}
```

Resumo:

- linhas na janela Gold original: `{input_summary['initial_rows_gold_window']}`
- linhas após `abs(phase) <= {PHASE_WINDOW}`: `{input_summary['rows_after_phase_filter']}`
- linhas após filtro de qualidade: `{input_summary['rows_after_quality_filter']}`
- pontos usados no M2: `{input_summary['rows_used']}`
- baseline mediano: `{input_summary['baseline_median']}`

## 4. Pré-processamento

Foram mantidas as mesmas regras base do M1:

- `abs(phase) <= {PHASE_WINDOW}`;
- `quality == 0`, quando a coluna existe;
- remoção de linhas sem `phase`, `flux` ou `flux_err`;
- remoção de `flux_err <= 0`;
- normalização local por mediana da região `0,08 <= abs(phase) <= 0,15`.

## 5. Especificação do Modelo

A função latente é:

```text
f(x) = intercept + soma_k w_k * phi_k(x)
```

com bases radiais gaussianas fixas:

```text
phi_k(x) = exp(-0.5 * ((x - c_k) / width)^2)
```

Configuração:

- `n_basis = {basis['n_basis']}`
- `basis_width = {basis['basis_width']}`
- centros distribuídos uniformemente em `[-0,15, 0,15]`
- grid preditivo com `{config['model']['prediction_grid_points']}` pontos

## 6. Priors

```text
intercept ~ Normal(1.0, 0.01)
weight_sigma ~ HalfNormal(0.01)
weights_raw_k ~ Normal(0, 1)
weights_k = weights_raw_k * weight_sigma
extra_sigma ~ HalfNormal(0.005)
```

Likelihood:

```text
sigma_eff_i = sqrt(normalized_flux_err_i^2 + extra_sigma^2)
normalized_flux_i ~ Normal(f(phase_i), sigma_eff_i)
```

## 7. Funções de Base Radial

As funções de base foram salvas em:

```text
{relative_path(paths.prediction_grid_path, paths.project_root)}
```

Figura:

![Funções de base](../figures/bayesian_predictive_phase_regression/hat_p_7_b/02_basis_functions.png)

## 8. Resultados Posteriores

Arquivo:

```text
{relative_path(paths.posterior_summary_path, paths.project_root)}
```

Resumo dos pesos:

{dataframe_to_markdown(weights_preview)}

## 9. Curva Preditiva

Arquivo:

```text
{relative_path(paths.predictive_curve_summary_path, paths.project_root)}
```

Profundidade exploratória derivada da curva:

```text
predicted_depth_mean = {depth_summary['predicted_depth_mean']:.8f}
predicted_depth_hdi_3 = {depth_summary['predicted_depth_hdi_3']:.8f}
predicted_depth_hdi_97 = {depth_summary['predicted_depth_hdi_97']:.8f}
```

Essa profundidade é exploratória e não equivale a um parâmetro físico direto.

Figura:

![Curva latente M2](../figures/bayesian_predictive_phase_regression/hat_p_7_b/05_predictive_curve_latent.png)

## 10. Posterior Predictive Check

Status:

```text
{config['posterior_predictive_status']}
```

Cobertura aproximada do intervalo preditivo de 94% nos pontos observados:

```text
{residual_metrics['posterior_predictive_interval_94_coverage_observed_points']:.6f}
```

Figura:

![Posterior predictive M2](../figures/bayesian_predictive_phase_regression/hat_p_7_b/06_posterior_predictive_observations.png)

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

![Resíduos por fase](../figures/bayesian_predictive_phase_regression/hat_p_7_b/07_residuals_by_phase.png)

## 12. Comparação Qualitativa com M1

{depth_difference_text}

Figura:

![Comparação M2 com M1](../figures/bayesian_predictive_phase_regression/hat_p_7_b/08_comparison_with_m1.png)

Interpretação:

- M1 resume o trânsito por uma profundidade box-shaped;
- M2 descreve uma curva suave de fluxo por fase;
- M2 melhora a descrição visual do formato por permitir transição suave;
- a profundidade exploratória do M2 deve ser comparada com cautela à depth do M1.

## 13. Diagnósticos MCMC

- NUTS rodou corretamente: `True`
- sampler: `{sampling['sampler']}`
- draws: `{sampling['draws']}`
- tune: `{sampling['tune']}`
- chains: `{sampling['chains']}`
- target_accept: `{sampling['target_accept']}`
- divergências: `{diagnostics['divergences']}`
- R-hat máximo: `{diagnostics['max_r_hat']:.8f}`
- ESS mínimo: `{diagnostics['min_ess']:.8f}`
- aceitação média: `{diagnostics['acceptance_mean']:.8f}`
- BFMI mínimo: `{bfmi_display}`
- recomendado para interpretação preditiva M2: `{diagnostics['recommended_for_m2_predictive_interpretation']}`

Nota:

```text
{diagnostics['convergence_note']}
```

## 14. Interpretação Científica

O M2 recupera visualmente o trânsito como depressão suave na região de fase
zero e fornece incerteza sobre a função latente e sobre futuras observações.

Ele é adequado como modelo preditivo intermediário para comparar com M1 e
preparar a transição para modelos mais estruturados.

## 15. Limitações

M2:

- não é modelo físico final;
- não estima diretamente `Rp/Rs`;
- não usa limb darkening;
- não modela geometria orbital;
- não estima ingresso, egresso ou duração como parâmetros físicos;
- não usa Gaussian Process;
- não incorpora TESS, ETD ou múltiplas missões;
- não substitui M3.

## 16. Próximos Passos

O próximo modelo recomendado é M3: um modelo trapezoidal ou físico aproximado
que estime explicitamente profundidade, duração e formato de ingresso/egresso.

M4 deve ficar para a comparação formal entre M1, M2 e M3.
"""
    paths.report_path.write_text(report, encoding="utf-8")


def main() -> None:
    paths = build_paths()
    ensure_directories(paths)

    raw = read_gold_transit_window(paths)
    prepared, prepared_metadata = prepare_modeling_input(raw, paths)

    centers = np.linspace(-PHASE_WINDOW, PHASE_WINDOW, N_BASIS)
    phase_grid = np.linspace(-PHASE_WINDOW, PHASE_WINDOW, PREDICTION_GRID_POINTS)
    basis_train = radial_basis_matrix(prepared["phase"].to_numpy(dtype=float), centers, BASIS_WIDTH)
    basis_grid = radial_basis_matrix(phase_grid, centers, BASIS_WIDTH)
    save_prediction_grid(paths, phase_grid, centers, basis_grid)

    model = build_model(prepared, basis_train, basis_grid)
    idata, sample_config = sample_nuts(model)
    idata, posterior_predictive_status = sample_posterior_predictive(model, idata)

    save_trace(paths, idata)
    posterior_summary = save_posterior_summary(paths, idata, centers)
    diagnostics = diagnostics_from_summary(posterior_summary, idata)
    curve, depth_summary = save_predictive_curve_summary(
        paths,
        idata,
        phase_grid,
        prepared_metadata["normalized_flux_err_median"],
    )
    residuals, residual_metrics = save_residual_summary(paths, idata, prepared, posterior_summary)
    m1_summary = read_m1_summary(paths)
    config = save_model_config(
        paths,
        prepared_metadata,
        sample_config,
        diagnostics,
        depth_summary,
        residual_metrics,
        posterior_predictive_status,
        m1_summary,
    )
    save_inference_summary_json(paths, config, posterior_summary, diagnostics, depth_summary, residual_metrics)
    save_figures(paths, prepared, phase_grid, centers, basis_grid, idata, posterior_summary, curve, residuals, m1_summary)
    save_report(paths, config, posterior_summary, depth_summary, residual_metrics)

    print(
        json.dumps(
            {
                "model_name": MODEL_NAME,
                "run_id": RUN_ID,
                "points_used": prepared_metadata["rows_used"],
                "n_basis": N_BASIS,
                "basis_width": BASIS_WIDTH,
                "trace": relative_path(paths.trace_path, paths.project_root),
                "posterior_summary": relative_path(paths.posterior_summary_path, paths.project_root),
                "predictive_curve_summary": relative_path(paths.predictive_curve_summary_path, paths.project_root),
                "residual_summary": relative_path(paths.residual_summary_path, paths.project_root),
                "report": relative_path(paths.report_path, paths.project_root),
                "max_r_hat": diagnostics["max_r_hat"],
                "min_ess": diagnostics["min_ess"],
                "divergences": diagnostics["divergences"],
                "predicted_depth_mean": depth_summary["predicted_depth_mean"],
                "m1_depth_mean": m1_summary.get("m1_depth_mean"),
                "recommended_for_m2_predictive_interpretation": diagnostics[
                    "recommended_for_m2_predictive_interpretation"
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
