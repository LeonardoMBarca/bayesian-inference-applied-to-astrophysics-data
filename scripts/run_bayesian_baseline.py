"""Run Bayesian baseline model M1 for HAT-P-7 b.

This script reads the existing GOLD transit-window table, prepares a local
normalization, fits a simple box-shaped transit model with PyMC, and writes
derived modeling artifacts outside data/raw, data/silver, and data/gold.
"""

from __future__ import annotations

import json
import math
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MPLCONFIGDIR = Path("/tmp") / "matplotlib-cache"
MPLCONFIGDIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPLCONFIGDIR))

PYTENSOR_CACHE = Path("/tmp") / "pytensor-cache"
PYTENSOR_CACHE.mkdir(parents=True, exist_ok=True)
existing_pytensor_flags = os.environ.get("PYTENSOR_FLAGS", "")
required_pytensor_flags = {
    "base_compiledir": str(PYTENSOR_CACHE),
    "linker": "py",
    "cxx": "",
}
flag_parts = [part for part in existing_pytensor_flags.split(",") if part]
for key, value in required_pytensor_flags.items():
    if not any(part.startswith(f"{key}=") for part in flag_parts):
        flag_parts.append(f"{key}={value}")
os.environ["PYTENSOR_FLAGS"] = ",".join(flag_parts)

import arviz as az  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pymc as pm  # noqa: E402


PLANET_NAME = "HAT-P-7 b"
PLANET_SLUG = "hat_p_7_b"
MISSION = "Kepler"
MODEL_NAME = "M1_box_transit_baseline"
SOURCE_GOLD_PATH = "data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv"

PHASE_WINDOW = 0.15
BASELINE_MIN_ABS_PHASE = 0.08
BASELINE_MAX_ABS_PHASE = 0.15
TRANSIT_HALF_WIDTH = 0.05
RANDOM_SEED = 42

REQUESTED_SAMPLING = {
    "draws": 2000,
    "tune": 2000,
    "chains": 4,
    "target_accept": 0.90,
}

# The project-level preference is NUTS with 2000/2000. In this sandbox PyTensor
# must use the pure-Python linker because Python.h is unavailable, so the first
# validated run uses PyMC Metropolis with reduced tuning and records it.
PREFERRED_SAMPLING = {
    "draws": 300,
    "tune": 300,
    "chains": 4,
    "target_accept": 0.90,
    "sampler": "Metropolis",
}
FALLBACK_SAMPLING = dict(PREFERRED_SAMPLING)


@dataclass(frozen=True)
class BaselinePaths:
    """Filesystem paths for the M1 Bayesian baseline artifacts."""

    project_root: Path
    source_gold: Path
    eda_summary: Path
    figures_dir: Path
    tables_dir: Path
    model_dir: Path
    reports_dir: Path
    notebooks_dir: Path
    trace_path: Path
    model_config_path: Path
    inference_summary_path: Path
    modeling_input_path: Path
    posterior_summary_path: Path
    derived_summary_path: Path
    posterior_predictive_summary_path: Path
    report_path: Path
    roadmap_path: Path


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
    if (cwd.parent / "data" / "gold").exists():
        return cwd.parent
    raise FileNotFoundError("Could not locate project root containing data/gold.")


def build_paths(project_root: Path | None = None) -> BaselinePaths:
    root = resolve_project_root(project_root)
    model_dir = root / "models" / "bayesian_baseline" / PLANET_SLUG
    tables_dir = root / "tables" / "bayesian_baseline" / PLANET_SLUG
    figures_dir = root / "figures" / "bayesian_baseline" / PLANET_SLUG
    return BaselinePaths(
        project_root=root,
        source_gold=root / SOURCE_GOLD_PATH,
        eda_summary=root / "tables" / "gold_eda" / PLANET_SLUG / "gold_eda_summary.csv",
        figures_dir=figures_dir,
        tables_dir=tables_dir,
        model_dir=model_dir,
        reports_dir=root / "reports",
        notebooks_dir=root / "notebooks",
        trace_path=model_dir / "trace.nc",
        model_config_path=model_dir / "model_config.json",
        inference_summary_path=model_dir / "inference_data_summary.json",
        modeling_input_path=tables_dir / "modeling_input_baseline.csv",
        posterior_summary_path=tables_dir / "posterior_summary.csv",
        derived_summary_path=tables_dir / "derived_parameters_summary.csv",
        posterior_predictive_summary_path=tables_dir / "posterior_predictive_summary.csv",
        report_path=root / "reports" / "bayesian_baseline_hat_p_7_b_report.md",
        roadmap_path=root / "models" / "modeling_roadmap.md",
    )


def relative_path(path: Path, project_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(path.resolve())


def ensure_directories(paths: BaselinePaths) -> None:
    for directory in [
        paths.figures_dir,
        paths.tables_dir,
        paths.model_dir,
        paths.reports_dir,
        paths.notebooks_dir,
        paths.roadmap_path.parent,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


def read_gold_transit_window(paths: BaselinePaths) -> pd.DataFrame:
    if not paths.source_gold.exists():
        raise FileNotFoundError(f"Missing GOLD input: {paths.source_gold}")
    dataframe = pd.read_csv(paths.source_gold, low_memory=False)
    for column in ["phase", "flux", "flux_err", "quality", "time"]:
        if column in dataframe.columns:
            dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")
    return dataframe


def read_visual_depth_from_eda(paths: BaselinePaths) -> float | None:
    if not paths.eda_summary.exists():
        return None
    eda = pd.read_csv(paths.eda_summary)
    if "approximate_depth_visual" not in eda.columns or eda.empty:
        return None
    value = pd.to_numeric(eda["approximate_depth_visual"], errors="coerce").iloc[0]
    if pd.isna(value):
        return None
    return float(value)


def prepare_modeling_input(dataframe: pd.DataFrame, paths: BaselinePaths) -> tuple[pd.DataFrame, dict[str, Any]]:
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

    prepared = prepared.dropna(subset=["flux", "flux_err", "phase"]).copy()
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
    for column in ["planet_name", "host_star", "mission", "quality", "time"]:
        if column not in prepared.columns:
            if column == "planet_name":
                prepared[column] = PLANET_NAME
            elif column == "mission":
                prepared[column] = MISSION
            else:
                prepared[column] = np.nan

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
    phase = prepared["phase"].to_numpy(dtype=float)
    y = prepared["normalized_flux"].to_numpy(dtype=float)
    sigma_obs = prepared["normalized_flux_err"].to_numpy(dtype=float)
    in_transit = (np.abs(phase) <= TRANSIT_HALF_WIDTH).astype(float)

    with pm.Model(coords={"observation": np.arange(len(prepared))}) as model:
        baseline = pm.Normal("baseline", mu=1.0, sigma=0.01)
        depth = pm.HalfNormal("depth", sigma=0.02)
        extra_sigma = pm.HalfNormal("extra_sigma", sigma=0.005)
        mu = baseline - depth * in_transit
        sigma_eff = pm.math.sqrt(np.square(sigma_obs) + extra_sigma**2)
        pm.Normal("obs", mu=mu, sigma=sigma_eff, observed=y, dims="observation")
        pm.Deterministic("rp_rs", pm.math.sqrt(depth))
    return model


def sample_model(model: pm.Model) -> tuple[az.InferenceData, dict[str, Any]]:
    sample_config = dict(PREFERRED_SAMPLING)
    sample_config["random_seed"] = RANDOM_SEED
    sample_config["cores"] = min(sample_config["chains"], os.cpu_count() or 1)
    sample_config["fallback_used"] = False
    sample_config["fallback_reason"] = ""
    sample_config["requested_draws"] = REQUESTED_SAMPLING["draws"]
    sample_config["requested_tune"] = REQUESTED_SAMPLING["tune"]
    sample_config["reduced_from_requested"] = (
        sample_config["draws"] != REQUESTED_SAMPLING["draws"]
        or sample_config["tune"] != REQUESTED_SAMPLING["tune"]
        or sample_config.get("sampler") != "NUTS"
    )
    sample_config["reduction_reason"] = (
        "PyTensor is forced to use linker=py because Python.h is unavailable "
        "in this sandbox; a short Metropolis run is used to validate the full "
        "M1 pipeline and artifacts. Re-run with NUTS 2000/2000 in an environment "
        "with Python development headers for stronger final diagnostics."
        if sample_config["reduced_from_requested"]
        else ""
    )

    try:
        with model:
            step = pm.Metropolis()
            idata = pm.sample(
                draws=sample_config["draws"],
                tune=sample_config["tune"],
                chains=sample_config["chains"],
                random_seed=sample_config["random_seed"],
                cores=sample_config["cores"],
                step=step,
                return_inferencedata=True,
            )
    except Exception as exc:
        sample_config = dict(FALLBACK_SAMPLING)
        sample_config["random_seed"] = RANDOM_SEED
        sample_config["cores"] = min(sample_config["chains"], os.cpu_count() or 1)
        sample_config["fallback_used"] = True
        sample_config["fallback_reason"] = repr(exc)
        sample_config["requested_draws"] = REQUESTED_SAMPLING["draws"]
        sample_config["requested_tune"] = REQUESTED_SAMPLING["tune"]
        sample_config["reduced_from_requested"] = True
        sample_config["reduction_reason"] = (
            "Preferred sampling failed; using the permitted fallback size."
        )
        sample_config["sampler"] = "Metropolis"
        with model:
            step = pm.Metropolis()
            idata = pm.sample(
                draws=sample_config["draws"],
                tune=sample_config["tune"],
                chains=sample_config["chains"],
                random_seed=sample_config["random_seed"],
                cores=sample_config["cores"],
                step=step,
                return_inferencedata=True,
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
            )
        return idata, "created"
    except Exception as exc:
        return idata, f"failed: {exc!r}"


def load_existing_trace(paths: BaselinePaths) -> tuple[az.InferenceData, dict[str, Any], str] | None:
    if not paths.trace_path.exists():
        return None
    try:
        idata = az.from_netcdf(paths.trace_path)
    except Exception:
        return None

    sample_config = dict(PREFERRED_SAMPLING)
    if paths.model_config_path.exists():
        try:
            previous_config = json.loads(paths.model_config_path.read_text(encoding="utf-8"))
            sample_config.update(previous_config.get("sampling", {}))
        except Exception:
            pass
    sample_config.setdefault("random_seed", RANDOM_SEED)
    sample_config.setdefault("cores", min(sample_config["chains"], os.cpu_count() or 1))
    sample_config.setdefault("fallback_used", False)
    sample_config.setdefault("fallback_reason", "")
    sample_config.setdefault("requested_draws", REQUESTED_SAMPLING["draws"])
    sample_config.setdefault("requested_tune", REQUESTED_SAMPLING["tune"])
    sample_config.setdefault("reduced_from_requested", True)
    sample_config.setdefault("reduction_reason", "Existing trace reused.")
    sample_config["trace_reused"] = True

    posterior_predictive_status = (
        "created"
        if hasattr(idata, "posterior_predictive") and "obs" in idata.posterior_predictive
        else "posterior predictive samples unavailable in reused trace"
    )
    return idata, sample_config, posterior_predictive_status


def save_model_config(
    paths: BaselinePaths,
    prepared_metadata: dict[str, Any],
    sample_config: dict[str, Any],
    posterior_predictive_status: str,
) -> dict[str, Any]:
    config = {
        "model_name": MODEL_NAME,
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
        "software_versions": {
            "python": sys.version.split()[0],
            "pymc": pm.__version__,
            "arviz": az.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "input_summary": prepared_metadata,
    }
    paths.model_config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    return config


def posterior_samples(idata: az.InferenceData, variable: str) -> np.ndarray:
    values = idata.posterior[variable].values
    return values.reshape(-1)


def save_posterior_summary(paths: BaselinePaths, idata: az.InferenceData) -> pd.DataFrame:
    summary = az.summary(
        idata,
        var_names=["baseline", "depth", "extra_sigma", "rp_rs"],
        ci_prob=0.94,
        ci_kind="hdi",
        kind="all",
        round_to=8,
    )
    summary = summary.reset_index().rename(columns={"index": "parameter"})
    summary = summary.rename(
        columns={
            "hdi94_lb": "hdi_3%",
            "hdi94_ub": "hdi_97%",
        }
    )
    summary.to_csv(paths.posterior_summary_path, index=False)
    return summary


def value_from_summary(summary: pd.DataFrame, parameter: str, column: str) -> float:
    row = summary.loc[summary["parameter"] == parameter]
    if row.empty or column not in row.columns:
        return float("nan")
    value = pd.to_numeric(row[column], errors="coerce").iloc[0]
    return float(value) if not pd.isna(value) else float("nan")


def save_derived_summary(
    paths: BaselinePaths,
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
                    "M1 is a Bayesian box-transit baseline; depth is posterior "
                    "for a simplified mean flux decrement, not a complete "
                    "physical transit characterization."
                ),
            }
        ]
    )
    derived.to_csv(paths.derived_summary_path, index=False)
    return derived


def save_posterior_predictive_summary(
    paths: BaselinePaths,
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


def save_trace(paths: BaselinePaths, idata: az.InferenceData) -> None:
    paths.trace_path.unlink(missing_ok=True)
    idata.to_netcdf(paths.trace_path)


def save_inference_summary_json(
    paths: BaselinePaths,
    config: dict[str, Any],
    posterior_summary: pd.DataFrame,
    derived_summary: pd.DataFrame,
    ppc_status: str,
) -> dict[str, Any]:
    r_hat = pd.to_numeric(posterior_summary.get("r_hat"), errors="coerce")
    ess_bulk = pd.to_numeric(posterior_summary.get("ess_bulk"), errors="coerce")
    ess_tail = pd.to_numeric(posterior_summary.get("ess_tail"), errors="coerce")
    max_r_hat = float(r_hat.max()) if not r_hat.dropna().empty else float("nan")
    min_ess = float(pd.concat([ess_bulk, ess_tail]).min()) if not pd.concat([ess_bulk, ess_tail]).dropna().empty else float("nan")
    convergence_note = (
        "Diagnostics are acceptable for a preliminary baseline."
        if math.isfinite(max_r_hat) and max_r_hat < 1.01 and math.isfinite(min_ess) and min_ess > 400
        else "Review diagnostics before scientific interpretation."
    )

    payload = {
        "created_at_utc": utc_now(),
        "model_name": MODEL_NAME,
        "planet_name": PLANET_NAME,
        "trace_path": relative_path(paths.trace_path, paths.project_root),
        "model_config_path": relative_path(paths.model_config_path, paths.project_root),
        "posterior_summary_path": relative_path(paths.posterior_summary_path, paths.project_root),
        "derived_parameters_summary_path": relative_path(paths.derived_summary_path, paths.project_root),
        "posterior_predictive_summary_path": relative_path(paths.posterior_predictive_summary_path, paths.project_root),
        "posterior_predictive_status": ppc_status,
        "sampling": config["sampling"],
        "input_summary": config["input_summary"],
        "diagnostics": {
            "max_r_hat": max_r_hat,
            "min_ess": min_ess,
            "convergence_note": convergence_note,
        },
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


def save_modeling_input_plot(paths: BaselinePaths, prepared: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(prepared["phase"], prepared["normalized_flux"], s=8, alpha=0.5, linewidths=0)
    ax.axvspan(-TRANSIT_HALF_WIDTH, TRANSIT_HALF_WIDTH, alpha=0.15, label="core transit used by M1")
    ax.axvline(0, linestyle="--", linewidth=1)
    ax.set_title("M1 input - normalized flux by phase")
    ax.set_xlabel("Phase in days, centered on transit")
    ax.set_ylabel("Normalized flux")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(paths.figures_dir / "01_modeling_input.png", dpi=300)
    plt.close(fig)


def save_trace_plot(paths: BaselinePaths, idata: az.InferenceData) -> None:
    az.plot_trace(idata, var_names=["baseline", "depth", "extra_sigma", "rp_rs"])
    fig = plt.gcf()
    fig.tight_layout()
    fig.savefig(paths.figures_dir / "02_trace_plot.png", dpi=300)
    plt.close(fig)


def save_posterior_histogram(paths: BaselinePaths, idata: az.InferenceData, variable: str, filename: str, title: str, xlabel: str) -> None:
    samples = posterior_samples(idata, variable)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(samples, bins=50, alpha=0.85)
    ax.axvline(np.mean(samples), linestyle="--", linewidth=1.4, label="posterior mean")
    hdi = az.hdi(samples, prob=0.94)
    ax.axvline(hdi[0], linestyle=":", linewidth=1.2, label="94% HDI")
    ax.axvline(hdi[1], linestyle=":", linewidth=1.2)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Count")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(paths.figures_dir / filename, dpi=300)
    plt.close(fig)


def save_model_fit_plot(paths: BaselinePaths, prepared: pd.DataFrame, posterior_summary: pd.DataFrame) -> None:
    baseline_mean = value_from_summary(posterior_summary, "baseline", "mean")
    depth_mean = value_from_summary(posterior_summary, "depth", "mean")
    phase_grid = np.linspace(-PHASE_WINDOW, PHASE_WINDOW, 600)
    mu_grid = np.where(np.abs(phase_grid) <= TRANSIT_HALF_WIDTH, baseline_mean - depth_mean, baseline_mean)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(prepared["phase"], prepared["normalized_flux"], s=8, alpha=0.35, linewidths=0, label="observed")
    ax.plot(phase_grid, mu_grid, linewidth=2, label="posterior mean box model")
    ax.axvline(0, linestyle="--", linewidth=1)
    ax.set_title("M1 model fit by phase")
    ax.set_xlabel("Phase in days, centered on transit")
    ax.set_ylabel("Normalized flux")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(paths.figures_dir / "05_model_fit_phase.png", dpi=300)
    plt.close(fig)


def save_posterior_predictive_plot(paths: BaselinePaths, ppc: pd.DataFrame) -> None:
    sorted_ppc = ppc.sort_values("phase")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(sorted_ppc["phase"], sorted_ppc["observed_flux"], s=8, alpha=0.35, linewidths=0, label="observed")
    if sorted_ppc["predicted_mean"].notna().any():
        ax.plot(sorted_ppc["phase"], sorted_ppc["predicted_mean"], linewidth=1.6, label="posterior predictive mean")
        ax.fill_between(
            sorted_ppc["phase"].to_numpy(dtype=float),
            sorted_ppc["predicted_hdi_3"].to_numpy(dtype=float),
            sorted_ppc["predicted_hdi_97"].to_numpy(dtype=float),
            alpha=0.2,
            label="94% predictive interval",
        )
    ax.axvline(0, linestyle="--", linewidth=1)
    ax.set_title("M1 posterior predictive check")
    ax.set_xlabel("Phase in days, centered on transit")
    ax.set_ylabel("Normalized flux")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(paths.figures_dir / "06_posterior_predictive_check.png", dpi=300)
    plt.close(fig)


def save_figures(paths: BaselinePaths, prepared: pd.DataFrame, idata: az.InferenceData, posterior_summary: pd.DataFrame, ppc: pd.DataFrame) -> None:
    save_modeling_input_plot(paths, prepared)
    save_trace_plot(paths, idata)
    save_posterior_histogram(
        paths,
        idata,
        "depth",
        "03_posterior_depth.png",
        "Posterior distribution of transit depth",
        "depth",
    )
    save_posterior_histogram(
        paths,
        idata,
        "rp_rs",
        "04_posterior_rp_rs.png",
        "Posterior distribution of Rp/Rs",
        "Rp/Rs = sqrt(depth)",
    )
    save_model_fit_plot(paths, prepared, posterior_summary)
    save_posterior_predictive_plot(paths, ppc)


def save_modeling_roadmap(paths: BaselinePaths) -> None:
    content = """# Roadmap de Modelagem Bayesiana

## 1. Objetivo Geral

O objetivo da sequência de modelos é demonstrar como inferência bayesiana pode
representar incerteza observacional em curvas de luz de trânsito, passando de
um baseline simples para modelos com maior estrutura física e preditiva.

## 2. M1 - Baseline Box Transit

Objetivo:

- estimar uma profundidade média de trânsito como distribuição posterior;
- derivar `Rp/Rs = sqrt(depth)`;
- criar um baseline comparativo simples.

Parâmetros:

- `baseline`;
- `depth`;
- `extra_sigma`;
- `rp_rs`.

Limitações:

- forma box-shaped fixa;
- meia largura de trânsito fixa;
- sem limb darkening;
- sem geometria orbital;
- sem ingresso/egresso;
- assume independência condicional dos erros.

## 3. M2 - Modelo Bayesiano Preditivo

Objetivo:

- prever fluxo em função da fase;
- avaliar distribuição preditiva;
- permitir forma mais flexível do trânsito.

Possibilidades:

- spline bayesiana;
- base radial;
- regressão local em fase;
- GP simples, se o custo computacional e a interpretação forem adequados.

## 4. M3 - Modelo Trapezoidal ou Físico Aproximado

Objetivo:

- representar profundidade;
- duração;
- ingresso;
- egresso;
- baseline local.

Esse modelo aproxima melhor a geometria de trânsito, mas ainda evita, em uma
primeira versão, a complexidade completa de Mandel & Agol.

## 5. M4 - Comparação de Modelos

Objetivo:

- comparar M1, M2 e M3;
- usar posterior predictive checks;
- avaliar erro preditivo;
- considerar LOO ou WAIC, se as hipóteses forem adequadas.

## 6. Observação Metodológica

M1 não é a conclusão final do TCC.

M1 serve como baseline transparente para mostrar a ideia central:

```text
um parâmetro astrofísico de interesse pode ser descrito por uma distribuição
posterior, não apenas por um ponto estimado.
```
"""
    paths.roadmap_path.write_text(content, encoding="utf-8")


def markdown_table(dataframe: pd.DataFrame, columns: list[str]) -> str:
    subset = dataframe.loc[:, columns].copy()
    for column in subset.columns:
        if pd.api.types.is_float_dtype(subset[column]):
            subset[column] = subset[column].map(lambda value: "" if pd.isna(value) else f"{value:.6g}")
        else:
            subset[column] = subset[column].astype(str)
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = ["| " + " | ".join(row) + " |" for row in subset.astype(str).values.tolist()]
    return "\n".join([header, separator, *rows])


def fmt(value: Any, digits: int = 6) -> str:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return "n/a"
    return f"{float(numeric):.{digits}g}"


def save_report(
    paths: BaselinePaths,
    config: dict[str, Any],
    posterior_summary: pd.DataFrame,
    derived_summary: pd.DataFrame,
    inference_summary: dict[str, Any],
    ppc_status: str,
) -> None:
    input_summary = config["input_summary"]
    diagnostics = inference_summary["diagnostics"]
    posterior = inference_summary["posterior"]
    sampling = config["sampling"]
    approx_depth = derived_summary.loc[0, "approximate_depth_visual_from_eda"]
    depth_mean = posterior["depth_mean"]
    compatible = (
        "sim"
        if pd.notna(approx_depth)
        and posterior["depth_hdi_3"] <= approx_depth <= posterior["depth_hdi_97"]
        else "parcialmente; a ordem de grandeza é semelhante, mas revisar a simplificação box"
    )
    convergence = (
        "sim"
        if diagnostics["max_r_hat"] < 1.01 and diagnostics["min_ess"] > 400
        else "requer revisão cautelosa"
    )

    content = f"""# Modelo Bayesiano M1 - Box Transit Baseline - HAT-P-7 b

## 1. Objetivo

Este relatório documenta o primeiro modelo bayesiano preliminar do projeto:
um baseline simples do tipo `box transit` para HAT-P-7 b.

O objetivo é estimar a profundidade média do trânsito como distribuição
posterior e derivar:

```text
Rp/Rs = sqrt(depth)
```

Este modelo não é a caracterização física final do planeta.

## 2. Papel do M1 na Sequência de Modelos

M1 é o baseline comparativo da sequência planejada:

- M1: box transit bayesiano simples;
- M2: modelo bayesiano preditivo de fluxo em função da fase;
- M3: modelo trapezoidal ou fisicamente mais estruturado;
- M4: comparação entre modelos.

M1 demonstra a lógica central do TCC: em vez de obter apenas um ponto estimado,
a inferência bayesiana fornece uma distribuição posterior para parâmetros de
interesse sob incerteza observacional.

## 3. Dataset Usado

Entrada Gold:

```text
{SOURCE_GOLD_PATH}
```

Dataset efetivo do modelo:

```text
{relative_path(paths.modeling_input_path, paths.project_root)}
```

Número de pontos usados:

```text
{input_summary["rows_used"]}
```

Janela de fase usada:

```text
abs(phase) <= {PHASE_WINDOW}
```

## 4. Pré-processamento

Foram aplicados os seguintes filtros:

1. `abs(phase) <= {PHASE_WINDOW}`;
2. `quality == 0`, quando a coluna existe;
3. remoção de linhas sem `flux`;
4. remoção de linhas sem `flux_err`;
5. remoção de linhas com `flux_err <= 0`.

Resumo:

| Etapa | Linhas |
|---|---:|
| Janela Gold original | {input_summary["initial_rows_gold_window"]} |
| Após filtro de fase | {input_summary["rows_after_phase_filter"]} |
| Após filtro de qualidade | {input_summary["rows_after_quality_filter"]} |
| Após remoção de ausências | {input_summary["rows_after_missing_filter"]} |
| Após exigir `flux_err > 0` | {input_summary["rows_after_positive_flux_err_filter"]} |

## 5. Normalização Local

Região de baseline local:

```text
{BASELINE_MIN_ABS_PHASE} <= abs(phase) <= {BASELINE_MAX_ABS_PHASE}
```

Mediana usada:

```text
baseline_median = {fmt(input_summary["baseline_median"], 10)}
```

Transformações:

```text
normalized_flux = flux / baseline_median
normalized_flux_err = flux_err / baseline_median
```

## 6. Especificação Probabilística

Para cada ponto `i`:

```text
y_i = normalized_flux_i
sigma_obs_i = normalized_flux_err_i
```

Se:

```text
abs(phase_i) <= {TRANSIT_HALF_WIDTH}
```

então:

```text
mu_i = baseline - depth
```

caso contrário:

```text
mu_i = baseline
```

## 7. Priors

```text
baseline ~ Normal(1.0, 0.01)
depth ~ HalfNormal(0.02)
extra_sigma ~ HalfNormal(0.005)
rp_rs = sqrt(depth)
```

## 8. Likelihood

```text
sigma_eff_i = sqrt(sigma_obs_i^2 + extra_sigma^2)
y_i ~ Normal(mu_i, sigma_eff_i)
```

## 9. Resultados Posteriores

Resumo posterior:

{markdown_table(posterior_summary, ["parameter", "mean", "sd", "hdi_3%", "hdi_97%", "ess_bulk", "ess_tail", "r_hat"])}

Profundidade posterior média:

```text
{fmt(posterior["depth_mean"], 8)}
```

Intervalo de credibilidade de 94% para profundidade:

```text
[{fmt(posterior["depth_hdi_3"], 8)}, {fmt(posterior["depth_hdi_97"], 8)}]
```

`Rp/Rs` posterior médio:

```text
{fmt(posterior["rp_rs_mean"], 8)}
```

Intervalo de credibilidade de 94% para `Rp/Rs`:

```text
[{fmt(posterior["rp_rs_hdi_3"], 8)}, {fmt(posterior["rp_rs_hdi_97"], 8)}]
```

## 10. Diagnósticos MCMC

Configuração de amostragem:

```text
draws = {sampling["draws"]}
tune = {sampling["tune"]}
chains = {sampling["chains"]}
sampler = {sampling.get("sampler", "NUTS")}
target_accept = {sampling["target_accept"]} (not used by Metropolis)
random_seed = {sampling["random_seed"]}
requested_draws = {sampling["requested_draws"]}
requested_tune = {sampling["requested_tune"]}
reduced_from_requested = {sampling["reduced_from_requested"]}
fallback_used = {sampling["fallback_used"]}
```

Maior R-hat:

```text
{fmt(diagnostics["max_r_hat"], 6)}
```

Menor ESS:

```text
{fmt(diagnostics["min_ess"], 6)}
```

O modelo convergiu adequadamente?

```text
{convergence}
```

## 11. Posterior Predictive Check

Status:

```text
{ppc_status}
```

Tabela:

```text
{relative_path(paths.posterior_predictive_summary_path, paths.project_root)}
```

Figura:

![Posterior predictive check](../figures/bayesian_baseline/hat_p_7_b/06_posterior_predictive_check.png)

## 12. Interpretação Astrofísica Preliminar

A profundidade visual exploratória da EDA foi:

```text
{fmt(approx_depth, 8)}
```

O resultado é compatível com a profundidade visual exploratória?

```text
{compatible}
```

Interpretação:

O modelo estima uma profundidade média simplificada de trânsito para uma forma
box-shaped. A distribuição posterior de `depth` mostra a incerteza associada a
essa simplificação e aos erros observacionais usados na likelihood.

## 13. Limitações

Este modelo:

- é um baseline bayesiano;
- usa forma box-shaped;
- fixa a meia largura do trânsito em `{TRANSIT_HALF_WIDTH}` dias;
- ignora limb darkening;
- ignora geometria orbital completa;
- ignora ingresso e egresso;
- assume independência condicional dos erros;
- usa apenas Kepler PDCSAP;
- não compara modelos;
- não deve ser interpretado como caracterização física final.

## 14. Próximos Modelos Planejados

Próxima etapa recomendada:

```text
M2 - modelo bayesiano preditivo de fluxo em função da fase
```

O M2 deve avaliar se uma forma mais flexível melhora a capacidade preditiva e
os posterior predictive checks em relação ao baseline M1.

## Figuras Geradas

![Input de modelagem](../figures/bayesian_baseline/hat_p_7_b/01_modeling_input.png)

![Trace plot](../figures/bayesian_baseline/hat_p_7_b/02_trace_plot.png)

![Posterior de depth](../figures/bayesian_baseline/hat_p_7_b/03_posterior_depth.png)

![Posterior de Rp/Rs](../figures/bayesian_baseline/hat_p_7_b/04_posterior_rp_rs.png)

![Ajuste box por fase](../figures/bayesian_baseline/hat_p_7_b/05_model_fit_phase.png)
"""
    paths.report_path.write_text(content, encoding="utf-8")


def run_pipeline(project_root: Path | None = None) -> dict[str, Any]:
    paths = build_paths(project_root)
    ensure_directories(paths)

    gold = read_gold_transit_window(paths)
    prepared, prepared_metadata = prepare_modeling_input(gold, paths)
    model = build_model(prepared)
    existing_trace = load_existing_trace(paths)
    if existing_trace is None:
        idata, sample_config = sample_model(model)
        idata, posterior_predictive_status = sample_posterior_predictive(model, idata)
        sample_config["trace_reused"] = False
        save_trace(paths, idata)
    else:
        idata, sample_config, posterior_predictive_status = existing_trace

    posterior_summary = save_posterior_summary(paths, idata)
    approximate_depth_visual = read_visual_depth_from_eda(paths)
    derived_summary = save_derived_summary(paths, posterior_summary, approximate_depth_visual)
    ppc, ppc_status = save_posterior_predictive_summary(paths, idata, prepared)
    final_ppc_status = posterior_predictive_status if posterior_predictive_status != "created" else ppc_status

    config = save_model_config(paths, prepared_metadata, sample_config, final_ppc_status)
    inference_summary = save_inference_summary_json(
        paths,
        config,
        posterior_summary,
        derived_summary,
        final_ppc_status,
    )
    save_figures(paths, prepared, idata, posterior_summary, ppc)
    save_modeling_roadmap(paths)
    save_report(paths, config, posterior_summary, derived_summary, inference_summary, final_ppc_status)

    return {
        "modeling_input_path": relative_path(paths.modeling_input_path, paths.project_root),
        "trace_path": relative_path(paths.trace_path, paths.project_root),
        "model_config_path": relative_path(paths.model_config_path, paths.project_root),
        "inference_summary_path": relative_path(paths.inference_summary_path, paths.project_root),
        "posterior_summary_path": relative_path(paths.posterior_summary_path, paths.project_root),
        "derived_summary_path": relative_path(paths.derived_summary_path, paths.project_root),
        "posterior_predictive_summary_path": relative_path(paths.posterior_predictive_summary_path, paths.project_root),
        "report_path": relative_path(paths.report_path, paths.project_root),
        "roadmap_path": relative_path(paths.roadmap_path, paths.project_root),
        "figures_dir": relative_path(paths.figures_dir, paths.project_root),
        "rows_used": prepared_metadata["rows_used"],
        "phase_window": PHASE_WINDOW,
        "normalization_baseline_median": prepared_metadata["baseline_median"],
        "posterior": inference_summary["posterior"],
        "diagnostics": inference_summary["diagnostics"],
        "posterior_predictive_status": final_ppc_status,
        "sampling": config["sampling"],
    }


def main() -> None:
    results = run_pipeline()
    print("Bayesian baseline M1 completed for HAT-P-7 b.")
    print(f"Rows used: {results['rows_used']}")
    print(f"Phase window: abs(phase) <= {results['phase_window']}")
    print(f"Trace: {results['trace_path']}")
    print(f"Report: {results['report_path']}")
    print(f"Posterior depth mean: {results['posterior']['depth_mean']:.8f}")
    print(f"Posterior Rp/Rs mean: {results['posterior']['rp_rs_mean']:.8f}")
    print(f"Max R-hat: {results['diagnostics']['max_r_hat']:.6f}")
    print(f"Min ESS: {results['diagnostics']['min_ess']:.2f}")
    print(f"Posterior predictive: {results['posterior_predictive_status']}")


if __name__ == "__main__":
    main()
