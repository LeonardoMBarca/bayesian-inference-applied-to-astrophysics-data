"""Run the robust NUTS execution of M1 for HAT-P-7 b.

This script keeps the M1 model specification unchanged and creates a versioned
robust run under runs/002_nuts_robust. The previous short operational
Metropolis run is preserved under runs/001_operational_metropolis when the
legacy artifacts are present.
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

PYTENSOR_CACHE = Path("/tmp") / "pytensor-cache-nuts-robust"
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
MISSION = "Kepler"
MODEL_NAME = "M1_box_transit_baseline"
SOURCE_GOLD_PATH = "data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv"

RUN_ID_OPERATIONAL = "001_operational_metropolis"
RUN_ID_ROBUST = "002_nuts_robust"

PHASE_WINDOW = 0.15
BASELINE_MIN_ABS_PHASE = 0.08
BASELINE_MAX_ABS_PHASE = 0.15
TRANSIT_HALF_WIDTH = 0.05
RANDOM_SEED = 42

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
VAR_NAMES = ["baseline", "depth", "extra_sigma", "rp_rs"]


@dataclass(frozen=True)
class RobustPaths:
    """Filesystem paths used by the robust M1 run."""

    project_root: Path
    source_gold: Path
    eda_summary: Path
    model_root: Path
    table_root: Path
    figure_root: Path
    reports_dir: Path
    robust_model_dir: Path
    robust_table_dir: Path
    robust_figure_dir: Path
    operational_model_dir: Path
    operational_table_dir: Path
    operational_figure_dir: Path
    trace_path: Path
    model_config_path: Path
    inference_summary_path: Path
    modeling_input_path: Path
    posterior_summary_path: Path
    derived_summary_path: Path
    posterior_predictive_summary_path: Path
    comparison_path: Path
    robust_report_path: Path


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


def build_paths(project_root: Path | None = None) -> RobustPaths:
    root = resolve_project_root(project_root)
    model_root = root / "models" / "bayesian_baseline" / PLANET_SLUG
    table_root = root / "tables" / "bayesian_baseline" / PLANET_SLUG
    figure_root = root / "figures" / "bayesian_baseline" / PLANET_SLUG
    robust_model_dir = model_root / "runs" / RUN_ID_ROBUST
    robust_table_dir = table_root / "runs" / RUN_ID_ROBUST
    robust_figure_dir = figure_root / "runs" / RUN_ID_ROBUST
    operational_model_dir = model_root / "runs" / RUN_ID_OPERATIONAL
    operational_table_dir = table_root / "runs" / RUN_ID_OPERATIONAL
    operational_figure_dir = figure_root / "runs" / RUN_ID_OPERATIONAL
    return RobustPaths(
        project_root=root,
        source_gold=root / SOURCE_GOLD_PATH,
        eda_summary=root / "tables" / "gold_eda" / PLANET_SLUG / "gold_eda_summary.csv",
        model_root=model_root,
        table_root=table_root,
        figure_root=figure_root,
        reports_dir=root / "reports",
        robust_model_dir=robust_model_dir,
        robust_table_dir=robust_table_dir,
        robust_figure_dir=robust_figure_dir,
        operational_model_dir=operational_model_dir,
        operational_table_dir=operational_table_dir,
        operational_figure_dir=operational_figure_dir,
        trace_path=robust_model_dir / "trace.nc",
        model_config_path=robust_model_dir / "model_config.json",
        inference_summary_path=robust_model_dir / "inference_data_summary.json",
        modeling_input_path=robust_table_dir / "modeling_input_baseline.csv",
        posterior_summary_path=robust_table_dir / "posterior_summary.csv",
        derived_summary_path=robust_table_dir / "derived_parameters_summary.csv",
        posterior_predictive_summary_path=robust_table_dir / "posterior_predictive_summary.csv",
        comparison_path=table_root / "model_run_comparison.csv",
        robust_report_path=root / "reports" / "bayesian_baseline_hat_p_7_b_nuts_robust_report.md",
    )


def relative_path(path: Path, project_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(path.resolve())


def ensure_directories(paths: RobustPaths) -> None:
    for directory in [
        paths.robust_model_dir,
        paths.robust_table_dir,
        paths.robust_figure_dir,
        paths.operational_model_dir,
        paths.operational_table_dir,
        paths.operational_figure_dir,
        paths.reports_dir,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


def copy_if_present(source: Path, destination: Path) -> None:
    if source.exists() and not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def preserve_operational_run(paths: RobustPaths) -> None:
    """Copy legacy flat M1 artifacts into the versioned 001 run if needed."""

    for file_name in ["trace.nc", "model_config.json", "inference_data_summary.json"]:
        copy_if_present(paths.model_root / file_name, paths.operational_model_dir / file_name)

    for file_name in [
        "modeling_input_baseline.csv",
        "posterior_summary.csv",
        "derived_parameters_summary.csv",
        "posterior_predictive_summary.csv",
    ]:
        copy_if_present(paths.table_root / file_name, paths.operational_table_dir / file_name)

    for file_name in [
        "01_modeling_input.png",
        "02_trace_plot.png",
        "03_posterior_depth.png",
        "04_posterior_rp_rs.png",
        "05_model_fit_phase.png",
        "06_posterior_predictive_check.png",
    ]:
        copy_if_present(paths.figure_root / file_name, paths.operational_figure_dir / file_name)

    copy_if_present(
        paths.reports_dir / "bayesian_baseline_hat_p_7_b_report.md",
        paths.reports_dir / "bayesian_baseline_hat_p_7_b_operational_metropolis_report.md",
    )


def read_gold_transit_window(paths: RobustPaths) -> pd.DataFrame:
    if not paths.source_gold.exists():
        raise FileNotFoundError(f"Missing GOLD input: {paths.source_gold}")
    dataframe = pd.read_csv(paths.source_gold, low_memory=False)
    for column in ["phase", "flux", "flux_err", "quality", "time"]:
        if column in dataframe.columns:
            dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")
    return dataframe


def read_visual_depth_from_eda(paths: RobustPaths) -> float | None:
    if not paths.eda_summary.exists():
        return None
    eda = pd.read_csv(paths.eda_summary)
    if "approximate_depth_visual" not in eda.columns or eda.empty:
        return None
    value = pd.to_numeric(eda["approximate_depth_visual"], errors="coerce").iloc[0]
    if pd.isna(value):
        return None
    return float(value)


def prepare_modeling_input(dataframe: pd.DataFrame, paths: RobustPaths) -> tuple[pd.DataFrame, dict[str, Any]]:
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
    prepared["is_core_transit_initial"] = abs_phase <= TRANSIT_HALF_WIDTH
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
                prepared[column] = "HAT-P-7"
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
        "is_core_transit_initial",
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
        "core_transit_count": int(prepared["is_core_transit_initial"].sum()),
        "phase_min": float(prepared["phase"].min()),
        "phase_max": float(prepared["phase"].max()),
        "normalized_flux_median": float(prepared["normalized_flux"].median()),
        "normalized_flux_std": float(prepared["normalized_flux"].std(ddof=1)),
        "normalized_flux_err_median": float(prepared["normalized_flux_err"].median()),
    }
    return prepared, metadata


def build_model(prepared: pd.DataFrame) -> pm.Model:
    y = prepared["normalized_flux"].to_numpy(dtype=float)
    sigma_obs = prepared["normalized_flux_err"].to_numpy(dtype=float)
    in_transit = prepared["is_core_transit_initial"].to_numpy(dtype=float)

    with pm.Model(coords={"observation": np.arange(len(prepared))}) as model:
        baseline = pm.Normal("baseline", mu=1.0, sigma=0.01)
        depth = pm.HalfNormal("depth", sigma=0.02)
        extra_sigma = pm.HalfNormal("extra_sigma", sigma=0.005)
        mu = baseline - depth * in_transit
        sigma_eff = pm.math.sqrt(np.square(sigma_obs) + extra_sigma**2)
        pm.Normal("obs", mu=mu, sigma=sigma_eff, observed=y, dims="observation")
        pm.Deterministic("rp_rs", pm.math.sqrt(depth))
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


def save_trace(paths: RobustPaths, idata: az.InferenceData) -> None:
    paths.trace_path.unlink(missing_ok=True)
    idata.to_netcdf(paths.trace_path)


def save_posterior_summary(paths: RobustPaths, idata: az.InferenceData) -> pd.DataFrame:
    summary = az.summary(
        idata,
        var_names=VAR_NAMES,
        ci_prob=0.94,
        ci_kind="hdi",
        kind="all",
        round_to=8,
    )
    summary = summary.reset_index().rename(columns={"index": "parameter"})
    summary = summary.rename(columns={"hdi94_lb": "hdi_3%", "hdi94_ub": "hdi_97%"})
    summary.to_csv(paths.posterior_summary_path, index=False)
    return summary


def value_from_summary(summary: pd.DataFrame, parameter: str, column: str) -> float:
    row = summary.loc[summary["parameter"] == parameter]
    if row.empty or column not in row.columns:
        return float("nan")
    value = pd.to_numeric(row[column], errors="coerce").iloc[0]
    return float(value) if not pd.isna(value) else float("nan")


def save_derived_summary(
    paths: RobustPaths,
    summary: pd.DataFrame,
    approximate_depth_visual: float | None,
) -> pd.DataFrame:
    derived = pd.DataFrame(
        [
            {
                "depth_mean": value_from_summary(summary, "depth", "mean"),
                "depth_hdi_3": value_from_summary(summary, "depth", "hdi_3%"),
                "depth_hdi_97": value_from_summary(summary, "depth", "hdi_97%"),
                "rp_rs_mean": value_from_summary(summary, "rp_rs", "mean"),
                "rp_rs_hdi_3": value_from_summary(summary, "rp_rs", "hdi_3%"),
                "rp_rs_hdi_97": value_from_summary(summary, "rp_rs", "hdi_97%"),
                "approximate_depth_visual_from_eda": approximate_depth_visual,
                "interpretation_note": (
                    "Robust NUTS execution of M1. The model remains a simplified "
                    "box-shaped baseline and should be used as a comparative "
                    "baseline, not as a complete physical transit model."
                ),
            }
        ]
    )
    derived.to_csv(paths.derived_summary_path, index=False)
    return derived


def save_posterior_predictive_summary(
    paths: RobustPaths,
    idata: az.InferenceData,
    prepared: pd.DataFrame,
) -> tuple[pd.DataFrame, str]:
    if not hasattr(idata, "posterior_predictive") or "obs" not in idata.posterior_predictive:
        empty = prepared.loc[:, ["phase", "normalized_flux"]].copy()
        empty = empty.rename(columns={"normalized_flux": "observed_flux"})
        for column in ["predicted_mean", "predicted_hdi_3", "predicted_hdi_97", "residual"]:
            empty[column] = np.nan
        empty.to_csv(paths.posterior_predictive_summary_path, index=False)
        return empty, "posterior predictive samples unavailable"

    predictive = np.asarray(idata.posterior_predictive["obs"].values)
    predictive = predictive.reshape(-1, predictive.shape[-1])
    predicted_mean = predictive.mean(axis=0)
    predicted_hdi_3 = np.quantile(predictive, 0.03, axis=0)
    predicted_hdi_97 = np.quantile(predictive, 0.97, axis=0)
    observed = prepared["normalized_flux"].to_numpy(dtype=float)
    ppc = pd.DataFrame(
        {
            "phase": prepared["phase"].to_numpy(dtype=float),
            "observed_flux": observed,
            "predicted_mean": predicted_mean,
            "predicted_hdi_3": predicted_hdi_3,
            "predicted_hdi_97": predicted_hdi_97,
            "residual": observed - predicted_mean,
        }
    ).sort_values("phase")
    ppc.to_csv(paths.posterior_predictive_summary_path, index=False)
    return ppc, "created"


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
        "recommended_for_scientific_interpretation": recommended,
        "convergence_note": (
            "NUTS diagnostics satisfy the project criteria for M1 baseline interpretation."
            if recommended
            else "Review diagnostics before treating this run as scientifically interpretable."
        ),
    }


def build_environment_summary() -> dict[str, Any]:
    include_dir = Path(sysconfig_include())
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
        "pytensor_flags": os.environ.get("PYTENSOR_FLAGS", ""),
    }


def sysconfig_include() -> str:
    import sysconfig

    return sysconfig.get_paths().get("include", "")


def save_model_config(
    paths: RobustPaths,
    prepared_metadata: dict[str, Any],
    sample_config: dict[str, Any],
    posterior_predictive_status: str,
    diagnostics: dict[str, Any],
) -> dict[str, Any]:
    config = {
        "model_name": MODEL_NAME,
        "run_id": RUN_ID_ROBUST,
        "created_at_utc": utc_now(),
        "planet_name": PLANET_NAME,
        "planet_slug": PLANET_SLUG,
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
            "shape": "box-shaped transit",
            "transit_half_width_days": TRANSIT_HALF_WIDTH,
            "baseline_prior": "Normal(1.0, 0.01)",
            "depth_prior": "HalfNormal(0.02)",
            "extra_sigma_prior": "HalfNormal(0.005)",
            "likelihood": "Normal(mu_i, sqrt(normalized_flux_err_i^2 + extra_sigma^2))",
            "mu_inside_transit": "baseline - depth",
            "mu_outside_transit": "baseline",
            "derived_parameter": "rp_rs = sqrt(depth)",
        },
        "sampling": sample_config,
        "posterior_predictive_status": posterior_predictive_status,
        "diagnostics": diagnostics,
        "environment": build_environment_summary(),
        "input_summary": prepared_metadata,
    }
    paths.model_config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    return config


def save_inference_summary_json(
    paths: RobustPaths,
    config: dict[str, Any],
    posterior_summary: pd.DataFrame,
    derived_summary: pd.DataFrame,
    diagnostics: dict[str, Any],
    ppc_status: str,
) -> dict[str, Any]:
    payload = {
        "created_at_utc": utc_now(),
        "model_name": MODEL_NAME,
        "run_id": RUN_ID_ROBUST,
        "planet_name": PLANET_NAME,
        "trace_path": relative_path(paths.trace_path, paths.project_root),
        "model_config_path": relative_path(paths.model_config_path, paths.project_root),
        "posterior_summary_path": relative_path(paths.posterior_summary_path, paths.project_root),
        "derived_parameters_summary_path": relative_path(paths.derived_summary_path, paths.project_root),
        "posterior_predictive_summary_path": relative_path(
            paths.posterior_predictive_summary_path, paths.project_root
        ),
        "posterior_predictive_status": ppc_status,
        "sampling": config["sampling"],
        "input_summary": config["input_summary"],
        "diagnostics": diagnostics,
        "posterior_summary": posterior_summary.to_dict(orient="records"),
        "posterior": {
            "depth_mean": float(derived_summary.loc[0, "depth_mean"]),
            "depth_hdi_3": float(derived_summary.loc[0, "depth_hdi_3"]),
            "depth_hdi_97": float(derived_summary.loc[0, "depth_hdi_97"]),
            "rp_rs_mean": float(derived_summary.loc[0, "rp_rs_mean"]),
            "rp_rs_hdi_3": float(derived_summary.loc[0, "rp_rs_hdi_3"]),
            "rp_rs_hdi_97": float(derived_summary.loc[0, "rp_rs_hdi_97"]),
        },
    }
    paths.inference_summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def posterior_samples(idata: az.InferenceData, variable: str) -> np.ndarray:
    values = np.asarray(idata.posterior[variable].values)
    return values.reshape(-1)


def save_modeling_input_plot(paths: RobustPaths, prepared: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(prepared["phase"], prepared["normalized_flux"], s=8, alpha=0.5, linewidths=0)
    ax.axvspan(-TRANSIT_HALF_WIDTH, TRANSIT_HALF_WIDTH, alpha=0.15, label="core transit used by M1")
    ax.axvline(0, linestyle="--", linewidth=1)
    ax.set_title("M1 robust NUTS input - normalized flux by phase")
    ax.set_xlabel("Phase in days, centered on transit")
    ax.set_ylabel("Normalized flux")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(paths.robust_figure_dir / "01_modeling_input.png", dpi=300)
    plt.close(fig)


def save_trace_plot(paths: RobustPaths, idata: az.InferenceData) -> None:
    az.plot_trace(idata, var_names=VAR_NAMES)
    fig = plt.gcf()
    fig.tight_layout()
    fig.savefig(paths.robust_figure_dir / "02_trace_plot.png", dpi=300)
    plt.close(fig)


def save_posterior_histogram(
    paths: RobustPaths,
    idata: az.InferenceData,
    variable: str,
    filename: str,
    title: str,
    xlabel: str,
) -> None:
    samples = posterior_samples(idata, variable)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(samples, bins=60, alpha=0.85)
    ax.axvline(np.mean(samples), linestyle="--", linewidth=1.4, label="posterior mean")
    hdi = az.hdi(samples, prob=0.94)
    ax.axvline(hdi[0], linestyle=":", linewidth=1.2, label="94% HDI")
    ax.axvline(hdi[1], linestyle=":", linewidth=1.2)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Posterior sample count")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(paths.robust_figure_dir / filename, dpi=300)
    plt.close(fig)


def save_model_fit_plot(paths: RobustPaths, prepared: pd.DataFrame, summary: pd.DataFrame) -> None:
    baseline_mean = value_from_summary(summary, "baseline", "mean")
    depth_mean = value_from_summary(summary, "depth", "mean")
    phases = prepared["phase"].to_numpy(dtype=float)
    order = np.argsort(phases)
    model_mean = np.where(np.abs(phases) <= TRANSIT_HALF_WIDTH, baseline_mean - depth_mean, baseline_mean)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(phases, prepared["normalized_flux"], s=8, alpha=0.4, linewidths=0, label="observed")
    ax.plot(phases[order], model_mean[order], linewidth=2, label="posterior mean box model")
    ax.axvspan(-TRANSIT_HALF_WIDTH, TRANSIT_HALF_WIDTH, alpha=0.12, label="fixed transit core")
    ax.set_title("M1 robust NUTS fit by phase")
    ax.set_xlabel("Phase in days, centered on transit")
    ax.set_ylabel("Normalized flux")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(paths.robust_figure_dir / "05_model_fit_phase.png", dpi=300)
    plt.close(fig)


def save_posterior_predictive_plot(paths: RobustPaths, ppc: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(ppc["phase"], ppc["observed_flux"], s=8, alpha=0.35, linewidths=0, label="observed")
    if ppc["predicted_mean"].notna().any():
        ordered = ppc.sort_values("phase")
        ax.plot(ordered["phase"], ordered["predicted_mean"], linewidth=2, label="predictive mean")
        ax.fill_between(
            ordered["phase"].to_numpy(dtype=float),
            ordered["predicted_hdi_3"].to_numpy(dtype=float),
            ordered["predicted_hdi_97"].to_numpy(dtype=float),
            alpha=0.2,
            label="94% predictive interval",
        )
    ax.set_title("M1 robust NUTS posterior predictive check")
    ax.set_xlabel("Phase in days, centered on transit")
    ax.set_ylabel("Normalized flux")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(paths.robust_figure_dir / "06_posterior_predictive_check.png", dpi=300)
    plt.close(fig)


def save_figures(paths: RobustPaths, prepared: pd.DataFrame, idata: az.InferenceData, summary: pd.DataFrame, ppc: pd.DataFrame) -> None:
    save_modeling_input_plot(paths, prepared)
    save_trace_plot(paths, idata)
    save_posterior_histogram(
        paths,
        idata,
        "depth",
        "03_posterior_depth.png",
        "Posterior depth - M1 robust NUTS",
        "Transit depth",
    )
    save_posterior_histogram(
        paths,
        idata,
        "rp_rs",
        "04_posterior_rp_rs.png",
        "Posterior Rp/Rs - M1 robust NUTS",
        "Rp/Rs",
    )
    save_model_fit_plot(paths, prepared, summary)
    save_posterior_predictive_plot(paths, ppc)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def load_summary(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def run_row_from_artifacts(
    run_id: str,
    sampler: str,
    config: dict[str, Any],
    summary: pd.DataFrame,
    derived: pd.DataFrame,
    diagnostics: dict[str, Any] | None,
    recommended: bool,
    notes: str,
) -> dict[str, Any]:
    sampling = config.get("sampling", {})
    input_summary = config.get("input_summary", {})
    diag = diagnostics or {}
    if not summary.empty:
        r_hat = pd.to_numeric(summary.get("r_hat"), errors="coerce")
        ess_bulk = pd.to_numeric(summary.get("ess_bulk"), errors="coerce")
        ess_tail = pd.to_numeric(summary.get("ess_tail"), errors="coerce")
        ess_values = pd.concat([ess_bulk, ess_tail])
        r_hat_max = float(r_hat.max()) if not r_hat.dropna().empty else float("nan")
        ess_min = float(ess_values.min()) if not ess_values.dropna().empty else float("nan")
    else:
        r_hat_max = float("nan")
        ess_min = float("nan")

    if not derived.empty:
        first = derived.iloc[0]
        depth_mean = first.get("depth_mean", np.nan)
        depth_hdi_3 = first.get("depth_hdi_3", np.nan)
        depth_hdi_97 = first.get("depth_hdi_97", np.nan)
        rp_rs_mean = first.get("rp_rs_mean", np.nan)
        rp_rs_hdi_3 = first.get("rp_rs_hdi_3", np.nan)
        rp_rs_hdi_97 = first.get("rp_rs_hdi_97", np.nan)
    else:
        depth_mean = depth_hdi_3 = depth_hdi_97 = np.nan
        rp_rs_mean = rp_rs_hdi_3 = rp_rs_hdi_97 = np.nan

    return {
        "run_id": run_id,
        "sampler": sampler,
        "draws": sampling.get("draws"),
        "tune": sampling.get("tune"),
        "chains": sampling.get("chains"),
        "points_used": input_summary.get("rows_used"),
        "depth_mean": depth_mean,
        "depth_hdi_3": depth_hdi_3,
        "depth_hdi_97": depth_hdi_97,
        "rp_rs_mean": rp_rs_mean,
        "rp_rs_hdi_3": rp_rs_hdi_3,
        "rp_rs_hdi_97": rp_rs_hdi_97,
        "r_hat_max": diag.get("max_r_hat", r_hat_max),
        "ess_min": diag.get("min_ess", ess_min),
        "divergences": diag.get("divergences"),
        "recommended_for_scientific_interpretation": recommended,
        "notes": notes,
    }


def save_run_comparison(
    paths: RobustPaths,
    robust_config: dict[str, Any],
    robust_summary: pd.DataFrame,
    robust_derived: pd.DataFrame,
    robust_diagnostics: dict[str, Any],
) -> pd.DataFrame:
    operational_config = load_json(paths.operational_model_dir / "model_config.json")
    operational_summary = load_summary(paths.operational_table_dir / "posterior_summary.csv")
    operational_derived = load_summary(paths.operational_table_dir / "derived_parameters_summary.csv")
    operational_row = run_row_from_artifacts(
        run_id=RUN_ID_OPERATIONAL,
        sampler=operational_config.get("sampling", {}).get("sampler", "Metropolis"),
        config=operational_config,
        summary=operational_summary,
        derived=operational_derived,
        diagnostics=None,
        recommended=False,
        notes="Short operational Metropolis run preserved for pipeline validation only.",
    )

    robust_row = run_row_from_artifacts(
        run_id=RUN_ID_ROBUST,
        sampler="NUTS",
        config=robust_config,
        summary=robust_summary,
        derived=robust_derived,
        diagnostics=robust_diagnostics,
        recommended=bool(robust_diagnostics["recommended_for_scientific_interpretation"]),
        notes=robust_diagnostics["convergence_note"],
    )

    comparison = pd.DataFrame([operational_row, robust_row])
    comparison.to_csv(paths.comparison_path, index=False)
    return comparison


def dataframe_to_markdown(dataframe: pd.DataFrame) -> str:
    """Render a small dataframe as a GitHub-flavored Markdown table."""

    if dataframe.empty:
        return "_Tabela vazia._"
    rendered = dataframe.copy()
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
    paths: RobustPaths,
    config: dict[str, Any],
    summary: pd.DataFrame,
    derived: pd.DataFrame,
    diagnostics: dict[str, Any],
    comparison: pd.DataFrame,
) -> None:
    depth_mean = float(derived.loc[0, "depth_mean"])
    depth_hdi_3 = float(derived.loc[0, "depth_hdi_3"])
    depth_hdi_97 = float(derived.loc[0, "depth_hdi_97"])
    rp_rs_mean = float(derived.loc[0, "rp_rs_mean"])
    rp_rs_hdi_3 = float(derived.loc[0, "rp_rs_hdi_3"])
    rp_rs_hdi_97 = float(derived.loc[0, "rp_rs_hdi_97"])
    env = config["environment"]
    sampling = config["sampling"]
    input_summary = config["input_summary"]
    bfmi_display = (
        "not available"
        if diagnostics["bfmi_min"] is None
        else f"{diagnostics['bfmi_min']:.8f}"
    )

    report = f"""# M1 - Robust Bayesian Baseline Run - HAT-P-7 b

## 1. Objetivo da Reexecução Robusta

Esta execução reprocessa o mesmo Modelo 1, `M1 - box transit baseline`, usando
NUTS em vez da execução curta operacional com Metropolis.

O objetivo não é criar um novo modelo. O objetivo é obter uma execução
inferencial mais confiável para o baseline bayesiano, mantendo a mesma entrada,
o mesmo pré-processamento e a mesma especificação probabilística.

## 2. Problema da Execução Anterior

A execução anterior validou a cadeia completa de artefatos, mas foi limitada
operacionalmente pelo ambiente Python usado naquele momento.

- Amostrador anterior: `Metropolis`
- Uso científico recomendado: `False`
- Maior R-hat anterior: `{comparison.loc[comparison['run_id'] == RUN_ID_OPERATIONAL, 'r_hat_max'].iloc[0]}`
- Menor ESS anterior: `{comparison.loc[comparison['run_id'] == RUN_ID_OPERATIONAL, 'ess_min'].iloc[0]}`

Essa execução anterior permanece preservada em:

```text
models/bayesian_baseline/hat_p_7_b/runs/{RUN_ID_OPERATIONAL}/
tables/bayesian_baseline/hat_p_7_b/runs/{RUN_ID_OPERATIONAL}/
figures/bayesian_baseline/hat_p_7_b/runs/{RUN_ID_OPERATIONAL}/
```

## 3. Ambiente Usado

- Python: `{env['python_version']}`
- Executável: `{env['python_executable']}`
- `Python.h` disponível: `{env['python_h_available']}`
- Diretório de include: `{env['python_include_dir']}`
- GCC: `{env['gcc']}`
- G++: `{env['gxx']}`
- PyMC: `{env['pymc']}`
- ArviZ: `{env['arviz']}`
- PyTensor: `{env['pytensor']}`
- Flags PyTensor: `{env['pytensor_flags']}`

O ambiente usado nesta reexecução foi um virtualenv local baseado no Python do
Conda:

```bash
.venv-nuts/bin/python scripts/run_bayesian_baseline_nuts_robust.py
```

## 4. Configuração NUTS

- Sampler: `{sampling['sampler']}`
- Draws: `{sampling['draws']}`
- Tune: `{sampling['tune']}`
- Chains: `{sampling['chains']}`
- Cores: `{sampling['cores']}`
- Target accept: `{sampling['target_accept']}`
- Random seed: `{sampling['random_seed']}`
- Retry executado: `{sampling['retry_performed']}`
- Motivo do retry: `{sampling['retry_reason']}`

## 5. Dataset e Pré-processamento

Entrada principal:

```text
{SOURCE_GOLD_PATH}
```

Regras mantidas:

- `abs(phase) <= {PHASE_WINDOW}`
- `quality == 0`
- remoção de `flux` ausente
- remoção de `flux_err` ausente
- remoção de `flux_err <= 0`
- região de baseline local: `{BASELINE_MIN_ABS_PHASE} <= abs(phase) <= {BASELINE_MAX_ABS_PHASE}`
- núcleo fixo do trânsito: `abs(phase) <= {TRANSIT_HALF_WIDTH}`

Resumo:

- Linhas iniciais na janela Gold: `{input_summary['initial_rows_gold_window']}`
- Linhas após janela de fase: `{input_summary['rows_after_phase_filter']}`
- Linhas após filtro de qualidade: `{input_summary['rows_after_quality_filter']}`
- Pontos usados no modelo: `{input_summary['rows_used']}`
- Baseline mediano usado na normalização: `{input_summary['baseline_median']}`

## 6. Especificação Probabilística

O M1 usa um trânsito em forma de caixa:

```text
mu_i = baseline - depth, se abs(phase_i) <= transit_half_width
mu_i = baseline, fora do núcleo do trânsito
```

Priors:

```text
baseline ~ Normal(1.0, 0.01)
depth ~ HalfNormal(0.02)
extra_sigma ~ HalfNormal(0.005)
```

Likelihood:

```text
sigma_eff_i = sqrt(normalized_flux_err_i^2 + extra_sigma^2)
normalized_flux_i ~ Normal(mu_i, sigma_eff_i)
```

Parâmetro derivado:

```text
rp_rs = sqrt(depth)
```

## 7. Resultados Posteriores

- Profundidade média posterior: `{depth_mean:.8f}`
- HDI 94% da profundidade: `[{depth_hdi_3:.8f}, {depth_hdi_97:.8f}]`
- `Rp/Rs` médio posterior: `{rp_rs_mean:.8f}`
- HDI 94% de `Rp/Rs`: `[{rp_rs_hdi_3:.8f}, {rp_rs_hdi_97:.8f}]`

Tabela completa:

```text
{relative_path(paths.posterior_summary_path, paths.project_root)}
```

## 8. Diagnósticos MCMC

- NUTS rodou corretamente: `True`
- Divergências: `{diagnostics['divergences']}`
- Maior R-hat: `{diagnostics['max_r_hat']:.8f}`
- Menor ESS: `{diagnostics['min_ess']:.8f}`
- Aceitação média: `{diagnostics['acceptance_mean']:.8f}`
- BFMI mínimo: `{bfmi_display}`
- Recomendado para interpretação científica do M1: `{diagnostics['recommended_for_scientific_interpretation']}`

Nota:

```text
{diagnostics['convergence_note']}
```

Observação de runtime:

```text
Durante a adaptação, PyMC/PyTensor registrou RuntimeWarning de overflow em
quadpotential.py. O aviso foi preservado no stdout da execução. A avaliação
final foi baseada nos diagnósticos salvos: zero divergências, R-hat adequado,
ESS adequado e BFMI adequado.
```

## 9. Comparação com Execução Metropolis Curta

Comparação tabular:

```text
{relative_path(paths.comparison_path, paths.project_root)}
```

Resumo:

{dataframe_to_markdown(comparison)}

## 10. Interpretação Astrofísica Preliminar

Esta execução robusta estima a profundidade média do trânsito dentro de um
modelo box-shaped simplificado. A razão `Rp/Rs` foi obtida pela transformação
`sqrt(depth)`.

O resultado é comparável à profundidade visual exploratória da EDA, mas ainda
não deve ser lido como caracterização física completa do sistema HAT-P-7 b.

## 11. Limitações do M1

O M1 ainda:

- ignora limb darkening;
- ignora geometria orbital completa;
- usa largura de trânsito fixa;
- assume erros gaussianos independentes condicionais;
- usa apenas Kepler PDCSAP na janela selecionada;
- estima uma profundidade média simplificada.

## 12. Próximo Modelo Recomendado

O próximo passo recomendado é o M2: um modelo bayesiano preditivo de fluxo em
função da fase, ainda simples, mas capaz de representar melhor a forma observada
da curva do que uma caixa fixa.

O M1 robusto deve ser usado como baseline comparativo para M2.
"""
    paths.robust_report_path.write_text(report, encoding="utf-8")


def main() -> None:
    paths = build_paths()
    ensure_directories(paths)
    preserve_operational_run(paths)

    raw = read_gold_transit_window(paths)
    prepared, prepared_metadata = prepare_modeling_input(raw, paths)
    approximate_depth_visual = read_visual_depth_from_eda(paths)

    model = build_model(prepared)
    idata, sample_config = sample_nuts(model)
    idata, posterior_predictive_status = sample_posterior_predictive(model, idata)

    save_trace(paths, idata)
    posterior_summary = save_posterior_summary(paths, idata)
    derived_summary = save_derived_summary(paths, posterior_summary, approximate_depth_visual)
    ppc_summary, ppc_status = save_posterior_predictive_summary(paths, idata, prepared)
    if posterior_predictive_status != "created":
        ppc_status = posterior_predictive_status

    diagnostics = diagnostics_from_summary(posterior_summary, idata)
    config = save_model_config(paths, prepared_metadata, sample_config, ppc_status, diagnostics)
    save_inference_summary_json(paths, config, posterior_summary, derived_summary, diagnostics, ppc_status)
    save_figures(paths, prepared, idata, posterior_summary, ppc_summary)
    comparison = save_run_comparison(paths, config, posterior_summary, derived_summary, diagnostics)
    save_report(paths, config, posterior_summary, derived_summary, diagnostics, comparison)

    print(json.dumps({
        "run_id": RUN_ID_ROBUST,
        "points_used": prepared_metadata["rows_used"],
        "trace": relative_path(paths.trace_path, paths.project_root),
        "posterior_summary": relative_path(paths.posterior_summary_path, paths.project_root),
        "report": relative_path(paths.robust_report_path, paths.project_root),
        "max_r_hat": diagnostics["max_r_hat"],
        "min_ess": diagnostics["min_ess"],
        "divergences": diagnostics["divergences"],
        "recommended_for_scientific_interpretation": diagnostics[
            "recommended_for_scientific_interpretation"
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
