"""Run M4 model comparison for HAT-P-7 b.

M4 does not fit a new Bayesian model. It reads the validated artifacts from
M1, M2 and M3, compares parameters, diagnostics, predictive behavior and
residuals, and writes a documented comparison layer under the model_comparison
family.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MPLCONFIGDIR = Path("/tmp") / "matplotlib-cache"
MPLCONFIGDIR.mkdir(parents=True, exist_ok=True)
os.environ["MPLCONFIGDIR"] = str(MPLCONFIGDIR)

import arviz as az  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


PLANET_NAME = "HAT-P-7 b"
PLANET_SLUG = "hat_p_7_b"
HOST_STAR = "HAT-P-7"
MISSION = "Kepler"
MODEL_NAME = "M4_model_comparison"
SOURCE_GOLD_PATH = "data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv"
HDI_PROB = 0.94

MODEL_ORDER = ["M1", "M2", "M3"]
MODEL_DISPLAY = {
    "M1": "M1 - Box transit",
    "M2": "M2 - Predictive phase regression",
    "M3": "M3 - Trapezoid transit",
}


@dataclass(frozen=True)
class M4Paths:
    """Filesystem paths for M4 artifacts."""

    project_root: Path
    source_gold: Path
    model_dir: Path
    table_dir: Path
    figure_dir: Path
    report_path: Path
    notebook_path: Path
    docs_dir: Path
    config_path: Path
    summary_path: Path
    parameter_comparison_path: Path
    diagnostic_comparison_path: Path
    predictive_metric_comparison_path: Path
    residual_comparison_path: Path
    recommendation_summary_path: Path
    loo_waic_path: Path
    m1_trace_path: Path
    m1_config_path: Path
    m1_summary_path: Path
    m1_posterior_summary_path: Path
    m1_derived_path: Path
    m1_ppc_path: Path
    m1_input_path: Path
    m2_trace_path: Path
    m2_config_path: Path
    m2_summary_path: Path
    m2_posterior_summary_path: Path
    m2_curve_path: Path
    m2_residual_path: Path
    m3_trace_path: Path
    m3_config_path: Path
    m3_summary_path: Path
    m3_posterior_summary_path: Path
    m3_derived_path: Path
    m3_curve_path: Path
    m3_ppc_path: Path
    m3_residual_path: Path


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


def build_paths(project_root: Path | None = None) -> M4Paths:
    root = resolve_project_root(project_root)
    model_dir = root / "models" / "model_comparison" / PLANET_SLUG
    table_dir = root / "tables" / "model_comparison" / PLANET_SLUG
    figure_dir = root / "figures" / "model_comparison" / PLANET_SLUG
    m1_run = root / "models" / "bayesian_baseline" / PLANET_SLUG / "runs" / "002_nuts_robust"
    m1_tables = root / "tables" / "bayesian_baseline" / PLANET_SLUG / "runs" / "002_nuts_robust"
    m2_run = (
        root
        / "models"
        / "bayesian_predictive_phase_regression"
        / PLANET_SLUG
        / "runs"
        / "001_nuts"
    )
    m2_tables = root / "tables" / "bayesian_predictive_phase_regression" / PLANET_SLUG
    m3_run = (
        root / "models" / "bayesian_trapezoid_transit" / PLANET_SLUG / "runs" / "001_nuts"
    )
    m3_tables = root / "tables" / "bayesian_trapezoid_transit" / PLANET_SLUG
    return M4Paths(
        project_root=root,
        source_gold=root / SOURCE_GOLD_PATH,
        model_dir=model_dir,
        table_dir=table_dir,
        figure_dir=figure_dir,
        report_path=root / "reports" / "model_comparison_hat_p_7_b_report.md",
        notebook_path=root / "notebooks" / "06_model_comparison_hat_p_7_b.ipynb",
        docs_dir=root / "docs" / "modeling" / "model_comparison_hat_p_7_b",
        config_path=model_dir / "model_comparison_config.json",
        summary_path=model_dir / "model_comparison_summary.json",
        parameter_comparison_path=table_dir / "parameter_comparison.csv",
        diagnostic_comparison_path=table_dir / "diagnostic_comparison.csv",
        predictive_metric_comparison_path=table_dir / "predictive_metric_comparison.csv",
        residual_comparison_path=table_dir / "residual_comparison.csv",
        recommendation_summary_path=table_dir / "model_recommendation_summary.csv",
        loo_waic_path=table_dir / "loo_waic_comparison.csv",
        m1_trace_path=m1_run / "trace.nc",
        m1_config_path=m1_run / "model_config.json",
        m1_summary_path=m1_run / "inference_data_summary.json",
        m1_posterior_summary_path=m1_tables / "posterior_summary.csv",
        m1_derived_path=m1_tables / "derived_parameters_summary.csv",
        m1_ppc_path=m1_tables / "posterior_predictive_summary.csv",
        m1_input_path=m1_tables / "modeling_input_baseline.csv",
        m2_trace_path=m2_run / "trace.nc",
        m2_config_path=m2_run / "model_config.json",
        m2_summary_path=m2_run / "inference_data_summary.json",
        m2_posterior_summary_path=m2_tables / "posterior_summary.csv",
        m2_curve_path=m2_tables / "predictive_curve_summary.csv",
        m2_residual_path=m2_tables / "residual_summary.csv",
        m3_trace_path=m3_run / "trace.nc",
        m3_config_path=m3_run / "model_config.json",
        m3_summary_path=m3_run / "inference_data_summary.json",
        m3_posterior_summary_path=m3_tables / "posterior_summary.csv",
        m3_derived_path=m3_tables / "derived_parameters_summary.csv",
        m3_curve_path=m3_tables / "trapezoid_curve_summary.csv",
        m3_ppc_path=m3_tables / "posterior_predictive_summary.csv",
        m3_residual_path=m3_tables / "residual_summary.csv",
    )


def ensure_directories(paths: M4Paths) -> None:
    for directory in [
        paths.model_dir,
        paths.table_dir,
        paths.figure_dir,
        paths.report_path.parent,
        paths.notebook_path.parent,
        paths.docs_dir,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


def relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def write_csv(dataframe: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(path, index=False)


def finite_or_nan(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return numeric if math.isfinite(numeric) else float("nan")


def posterior_mean(posterior_summary: pd.DataFrame, parameter: str) -> float:
    row = posterior_summary.loc[posterior_summary["parameter"] == parameter]
    if row.empty:
        return float("nan")
    return finite_or_nan(row.iloc[0]["mean"])


def build_parameter_comparison(paths: M4Paths, summaries: dict[str, dict[str, Any]]) -> pd.DataFrame:
    m1 = read_csv(paths.m1_derived_path).iloc[0]
    m2_summary = summaries["M2"]
    m3 = read_csv(paths.m3_derived_path).iloc[0]
    m2_depth = m2_summary.get("derived_predictive_depth", {})

    rows = [
        {
            "model_id": "M1",
            "model_name": MODEL_DISPLAY["M1"],
            "model_family": "box_transit_baseline",
            "depth_type": "direct_parameter_depth",
            "depth_mean": finite_or_nan(m1.get("depth_mean")),
            "depth_hdi_3": finite_or_nan(m1.get("depth_hdi_3")),
            "depth_hdi_97": finite_or_nan(m1.get("depth_hdi_97")),
            "rp_rs_mean": finite_or_nan(m1.get("rp_rs_mean")),
            "rp_rs_hdi_3": finite_or_nan(m1.get("rp_rs_hdi_3")),
            "rp_rs_hdi_97": finite_or_nan(m1.get("rp_rs_hdi_97")),
            "duration_hours": float("nan"),
            "ingress_hours": float("nan"),
            "interpretation_note": "Baseline box-shaped model. Depth is direct but shape is rigid and transit half-width is fixed.",
        },
        {
            "model_id": "M2",
            "model_name": MODEL_DISPLAY["M2"],
            "model_family": "smooth_predictive_phase_regression",
            "depth_type": "exploratory_predicted_depth",
            "depth_mean": finite_or_nan(m2_depth.get("predicted_depth_mean")),
            "depth_hdi_3": finite_or_nan(m2_depth.get("predicted_depth_hdi_3")),
            "depth_hdi_97": finite_or_nan(m2_depth.get("predicted_depth_hdi_97")),
            "rp_rs_mean": float("nan"),
            "rp_rs_hdi_3": float("nan"),
            "rp_rs_hdi_97": float("nan"),
            "duration_hours": float("nan"),
            "ingress_hours": float("nan"),
            "interpretation_note": "Predictive depth is exploratory and derived from the smooth curve; it is not a direct physical depth parameter and does not define Rp/Rs.",
        },
        {
            "model_id": "M3",
            "model_name": MODEL_DISPLAY["M3"],
            "model_family": "approximate_trapezoid_transit",
            "depth_type": "direct_parameter_depth",
            "depth_mean": finite_or_nan(m3.get("depth_mean")),
            "depth_hdi_3": finite_or_nan(m3.get("depth_hdi_3")),
            "depth_hdi_97": finite_or_nan(m3.get("depth_hdi_97")),
            "rp_rs_mean": finite_or_nan(m3.get("rp_rs_mean")),
            "rp_rs_hdi_3": finite_or_nan(m3.get("rp_rs_hdi_3")),
            "rp_rs_hdi_97": finite_or_nan(m3.get("rp_rs_hdi_97")),
            "duration_hours": finite_or_nan(m3.get("full_duration_mean_hours")),
            "ingress_hours": finite_or_nan(m3.get("ingress_duration_mean_hours")),
            "interpretation_note": "Approximate trapezoid model. Depth and Rp/Rs are direct derived quantities under a simplified transit geometry.",
        },
    ]
    dataframe = pd.DataFrame(rows)
    write_csv(dataframe, paths.parameter_comparison_path)
    return dataframe


def build_diagnostic_comparison(paths: M4Paths, summaries: dict[str, dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for model_id in MODEL_ORDER:
        summary = summaries[model_id]
        sampling = summary.get("sampling", {})
        diagnostics = summary.get("diagnostics", {})
        max_rhat = finite_or_nan(diagnostics.get("max_r_hat"))
        min_ess = finite_or_nan(diagnostics.get("min_ess"))
        divergences = int(diagnostics.get("divergences", -1))
        status = "good" if max_rhat <= 1.01 and min_ess >= 1000 and divergences == 0 else "review_needed"
        rows.append(
            {
                "model_id": model_id,
                "sampler": sampling.get("sampler", "unknown"),
                "draws": sampling.get("draws"),
                "tune": sampling.get("tune"),
                "chains": sampling.get("chains"),
                "target_accept": sampling.get("target_accept"),
                "r_hat_max": max_rhat,
                "ess_min": min_ess,
                "divergences": divergences,
                "bfmi_min": finite_or_nan(diagnostics.get("bfmi_min")),
                "diagnostic_status": status,
                "notes": diagnostics.get("convergence_note", ""),
            }
        )
    dataframe = pd.DataFrame(rows)
    write_csv(dataframe, paths.diagnostic_comparison_path)
    return dataframe


def build_residual_comparison(paths: M4Paths) -> pd.DataFrame:
    residual_rows: list[pd.DataFrame] = []

    m1_ppc = read_csv(paths.m1_ppc_path)
    m1_input = read_csv(paths.m1_input_path)
    m1_post = read_csv(paths.m1_posterior_summary_path)
    m1_extra_sigma = posterior_mean(m1_post, "extra_sigma")
    m1 = m1_ppc.copy()
    m1["normalized_flux_err"] = m1_input["normalized_flux_err"].to_numpy()
    sigma_eff = np.sqrt(m1["normalized_flux_err"].to_numpy() ** 2 + m1_extra_sigma**2)
    m1["standardized_residual"] = m1["residual"].to_numpy() / sigma_eff
    m1["model_id"] = "M1"
    m1 = m1[
        [
            "model_id",
            "phase",
            "observed_flux",
            "predicted_mean",
            "residual",
            "standardized_residual",
            "normalized_flux_err",
        ]
    ]
    residual_rows.append(m1)

    for model_id, path in [("M2", paths.m2_residual_path), ("M3", paths.m3_residual_path)]:
        df = read_csv(path).copy()
        df["model_id"] = model_id
        df["observed_flux"] = df["normalized_flux"]
        residual_rows.append(
            df[
                [
                    "model_id",
                    "phase",
                    "observed_flux",
                    "predicted_mean",
                    "residual",
                    "standardized_residual",
                    "normalized_flux_err",
                ]
            ]
        )

    dataframe = pd.concat(residual_rows, ignore_index=True)
    dataframe = dataframe.sort_values(["model_id", "phase"]).reset_index(drop=True)
    write_csv(dataframe, paths.residual_comparison_path)
    return dataframe


def coverage_from_interval(dataframe: pd.DataFrame) -> float:
    required = {"observed_flux", "predicted_hdi_3", "predicted_hdi_97"}
    if not required.issubset(dataframe.columns):
        return float("nan")
    inside = (
        (dataframe["observed_flux"] >= dataframe["predicted_hdi_3"])
        & (dataframe["observed_flux"] <= dataframe["predicted_hdi_97"])
    )
    return float(inside.mean())


def build_predictive_metric_comparison(
    paths: M4Paths,
    summaries: dict[str, dict[str, Any]],
    residuals: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    for model_id in MODEL_ORDER:
        df = residuals.loc[residuals["model_id"] == model_id].copy()
        residual = df["residual"].to_numpy(dtype=float)
        standardized = df["standardized_residual"].to_numpy(dtype=float)
        if model_id == "M1":
            ppc = read_csv(paths.m1_ppc_path)
            coverage = coverage_from_interval(ppc)
            note = "Coverage computed from M1 posterior predictive intervals at observed phases."
        elif model_id == "M2":
            coverage = finite_or_nan(
                summaries["M2"].get("residual_metrics", {}).get(
                    "posterior_predictive_interval_94_coverage_observed_points"
                )
            )
            note = "Coverage read from M2 validated summary; pointwise predictive interval table was not stored separately."
        else:
            ppc = read_csv(paths.m3_ppc_path)
            coverage = coverage_from_interval(ppc)
            note = "Coverage computed from M3 posterior predictive intervals at observed phases."
        rows.append(
            {
                "model_id": model_id,
                "model_name": MODEL_DISPLAY[model_id],
                "rmse": float(np.sqrt(np.mean(residual**2))),
                "mae": float(np.mean(np.abs(residual))),
                "median_absolute_error": float(np.median(np.abs(residual))),
                "mean_residual": float(np.mean(residual)),
                "residual_std": float(np.std(residual, ddof=1)),
                "standardized_residual_std": float(np.std(standardized, ddof=1)),
                "coverage_94": coverage,
                "n_points": int(len(df)),
                "notes": note,
            }
        )
    dataframe = pd.DataFrame(rows)
    write_csv(dataframe, paths.predictive_metric_comparison_path)
    return dataframe


def build_loo_waic_comparison(paths: M4Paths) -> pd.DataFrame:
    rows = []
    trace_paths = {
        "M1": paths.m1_trace_path,
        "M2": paths.m2_trace_path,
        "M3": paths.m3_trace_path,
    }
    for model_id, trace_path in trace_paths.items():
        base = {
            "model_id": model_id,
            "loo_elpd": float("nan"),
            "loo_se": float("nan"),
            "waic_elpd": float("nan"),
            "waic_se": float("nan"),
            "status": "not_attempted",
            "notes": "",
        }
        try:
            idata = az.from_netcdf(trace_path)
            if "log_likelihood" not in idata.groups:
                base["status"] = "unavailable"
                base["notes"] = "trace.nc does not contain a log_likelihood group; LOO/WAIC were not forced."
            else:
                loo = az.loo(idata)
                waic = az.waic(idata)
                base.update(
                    {
                        "loo_elpd": finite_or_nan(getattr(loo, "elpd_loo", np.nan)),
                        "loo_se": finite_or_nan(getattr(loo, "se", np.nan)),
                        "waic_elpd": finite_or_nan(getattr(waic, "elpd_waic", np.nan)),
                        "waic_se": finite_or_nan(getattr(waic, "se", np.nan)),
                        "status": "created",
                        "notes": "LOO and WAIC computed by ArviZ.",
                    }
                )
        except Exception as exc:  # noqa: BLE001
            base["status"] = "failed"
            base["notes"] = f"{type(exc).__name__}: {exc}"
        rows.append(base)
    dataframe = pd.DataFrame(rows)
    write_csv(dataframe, paths.loo_waic_path)
    return dataframe


def build_recommendation_summary(
    paths: M4Paths,
    diagnostics: pd.DataFrame,
    predictive_metrics: pd.DataFrame,
) -> pd.DataFrame:
    rmse_rank = predictive_metrics.set_index("model_id")["rmse"].rank(ascending=True, method="min")
    max_rank = float(rmse_rank.max())
    predictive_score = {
        model_id: int(round(2 + 3 * (max_rank - rmse_rank.loc[model_id]) / max(max_rank - 1, 1)))
        for model_id in MODEL_ORDER
    }
    diagnostic_score = {}
    for row in diagnostics.to_dict(orient="records"):
        if row["diagnostic_status"] == "good":
            diagnostic_score[row["model_id"]] = 5
        elif row["divergences"] == 0:
            diagnostic_score[row["model_id"]] = 3
        else:
            diagnostic_score[row["model_id"]] = 1

    rows = [
        {
            "model_id": "M1",
            "interpretability_score": 4,
            "predictive_score": predictive_score["M1"],
            "physical_structure_score": 2,
            "diagnostic_score": diagnostic_score["M1"],
            "complexity_score": 5,
            "recommended_role": "baseline_reference",
            "notes": "Best used as transparent baseline; direct depth is easy to explain, but the fixed box shape is too rigid for the main preliminary result.",
        },
        {
            "model_id": "M2",
            "interpretability_score": 2,
            "predictive_score": predictive_score["M2"],
            "physical_structure_score": 1,
            "diagnostic_score": diagnostic_score["M2"],
            "complexity_score": 3,
            "recommended_role": "predictive_description",
            "notes": "Best used to describe the smooth phase-flux relation and predictive uncertainty; predicted_depth is exploratory and should not be reported as a physical depth.",
        },
        {
            "model_id": "M3",
            "interpretability_score": 5,
            "predictive_score": predictive_score["M3"],
            "physical_structure_score": 4,
            "diagnostic_score": diagnostic_score["M3"],
            "complexity_score": 4,
            "recommended_role": "primary_preliminary_result",
            "notes": "Recommended as the main preliminary result because it balances diagnostics, predictive behavior, direct depth/RpRs and approximate duration/ingress parameters.",
        },
    ]
    dataframe = pd.DataFrame(rows)
    write_csv(dataframe, paths.recommendation_summary_path)
    return dataframe


def save_parameter_plot(paths: M4Paths, params: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(params))
    means = params["depth_mean"].to_numpy(dtype=float)
    low = means - params["depth_hdi_3"].to_numpy(dtype=float)
    high = params["depth_hdi_97"].to_numpy(dtype=float) - means
    ax.errorbar(x, means, yerr=[low, high], fmt="o", capsize=4)
    ax.set_xticks(x)
    ax.set_xticklabels(params["model_id"])
    ax.set_ylabel("Depth / predicted depth")
    ax.set_title("M4 - Depth comparison")
    ax.grid(alpha=0.3)
    for idx, row in params.iterrows():
        note = "exploratory" if row["model_id"] == "M2" else "direct"
        ax.annotate(note, (idx, row["depth_mean"]), textcoords="offset points", xytext=(0, 10), ha="center")
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "01_depth_comparison.png", dpi=300)
    plt.close(fig)


def save_rp_rs_plot(paths: M4Paths, params: pd.DataFrame) -> None:
    subset = params.loc[params["rp_rs_mean"].notna()].copy()
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(subset))
    means = subset["rp_rs_mean"].to_numpy(dtype=float)
    low = means - subset["rp_rs_hdi_3"].to_numpy(dtype=float)
    high = subset["rp_rs_hdi_97"].to_numpy(dtype=float) - means
    ax.errorbar(x, means, yerr=[low, high], fmt="o", capsize=4)
    ax.set_xticks(x)
    ax.set_xticklabels(subset["model_id"])
    ax.set_ylabel("Rp/Rs")
    ax.set_title("M4 - Rp/Rs comparison")
    ax.text(0.5, 0.03, "M2 omitted: Rp/Rs is not directly estimated.", transform=ax.transAxes, ha="center")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "02_rp_rs_comparison.png", dpi=300)
    plt.close(fig)


def save_fit_comparison_plot(paths: M4Paths) -> None:
    m1_ppc = read_csv(paths.m1_ppc_path).sort_values("phase")
    m2_curve = read_csv(paths.m2_curve_path)
    m3_curve = read_csv(paths.m3_curve_path)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.scatter(m1_ppc["phase"], m1_ppc["observed_flux"], s=8, alpha=0.25, label="Observed")
    ax.plot(m1_ppc["phase"], m1_ppc["predicted_mean"], label="M1 box mean", linewidth=1.8)
    ax.plot(m2_curve["phase"], m2_curve["latent_mean"], label="M2 latent mean", linewidth=1.8)
    ax.plot(m3_curve["phase"], m3_curve["model_mean"], label="M3 trapezoid mean", linewidth=1.8)
    ax.set_xlabel("Phase (days)")
    ax.set_ylabel("Normalized flux")
    ax.set_title("M4 - Model fit comparison")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "03_model_fit_comparison.png", dpi=300)
    plt.close(fig)


def save_residual_comparison_plot(paths: M4Paths, residuals: pd.DataFrame) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    for ax, model_id in zip(axes, MODEL_ORDER, strict=True):
        df = residuals.loc[residuals["model_id"] == model_id]
        ax.scatter(df["phase"], df["residual"], s=8, alpha=0.35)
        ax.axhline(0, linewidth=1)
        ax.set_ylabel(model_id)
        ax.grid(alpha=0.3)
    axes[-1].set_xlabel("Phase (days)")
    fig.suptitle("M4 - Residual comparison by phase")
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "04_residual_comparison.png", dpi=300)
    plt.close(fig)


def save_predictive_interval_plot(paths: M4Paths) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(9, 9), sharex=True)
    m1 = read_csv(paths.m1_ppc_path).sort_values("phase")
    m2 = read_csv(paths.m2_curve_path)
    m3 = read_csv(paths.m3_curve_path)
    rows = [
        ("M1", m1, "observed_flux", "predicted_mean", "predicted_hdi_3", "predicted_hdi_97"),
        ("M2", m2, None, "predictive_mean", "predictive_hdi_3", "predictive_hdi_97"),
        ("M3", m3, None, "predictive_mean", "predictive_hdi_3", "predictive_hdi_97"),
    ]
    for ax, (model_id, df, obs_col, mean_col, low_col, high_col) in zip(axes, rows, strict=True):
        if obs_col:
            ax.scatter(df["phase"], df[obs_col], s=8, alpha=0.25, label="Observed")
        else:
            observed = read_csv(paths.m1_ppc_path)
            ax.scatter(observed["phase"], observed["observed_flux"], s=8, alpha=0.20, label="Observed")
        ax.plot(df["phase"], df[mean_col], label=f"{model_id} predictive mean")
        ax.fill_between(df["phase"], df[low_col], df[high_col], alpha=0.25)
        ax.set_ylabel(model_id)
        ax.grid(alpha=0.3)
    axes[-1].set_xlabel("Phase (days)")
    axes[0].legend()
    fig.suptitle("M4 - Predictive interval comparison")
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "05_predictive_interval_comparison.png", dpi=300)
    plt.close(fig)


def save_diagnostic_plot(paths: M4Paths, diagnostics: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(11, 4))
    axes[0].bar(diagnostics["model_id"], diagnostics["r_hat_max"])
    axes[0].axhline(1.01, linestyle="--", linewidth=1)
    axes[0].set_title("Max R-hat")
    axes[1].bar(diagnostics["model_id"], diagnostics["ess_min"])
    axes[1].set_title("Min ESS")
    axes[2].bar(diagnostics["model_id"], diagnostics["divergences"])
    axes[2].set_title("Divergences")
    for ax in axes:
        ax.grid(axis="y", alpha=0.3)
    fig.suptitle("M4 - Diagnostic comparison")
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "06_diagnostic_comparison.png", dpi=300)
    plt.close(fig)


def save_complexity_map(paths: M4Paths) -> None:
    points = pd.DataFrame(
        [
            {"model_id": "M1", "flexibility": 1.5, "physical_interpretability": 3.0},
            {"model_id": "M2", "flexibility": 4.5, "physical_interpretability": 2.0},
            {"model_id": "M3", "flexibility": 3.0, "physical_interpretability": 4.5},
        ]
    )
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(points["flexibility"], points["physical_interpretability"], s=120)
    for row in points.to_dict(orient="records"):
        ax.annotate(row["model_id"], (row["flexibility"], row["physical_interpretability"]), xytext=(8, 8), textcoords="offset points")
    ax.set_xlim(1, 5)
    ax.set_ylim(1, 5)
    ax.set_xlabel("Flexibility")
    ax.set_ylabel("Physical interpretability")
    ax.set_title("M4 - Complexity and interpretability map")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(paths.figure_dir / "07_model_complexity_interpretability_map.png", dpi=300)
    plt.close(fig)


def save_all_figures(
    paths: M4Paths,
    params: pd.DataFrame,
    diagnostics: pd.DataFrame,
    residuals: pd.DataFrame,
) -> None:
    save_parameter_plot(paths, params)
    save_rp_rs_plot(paths, params)
    save_fit_comparison_plot(paths)
    save_residual_comparison_plot(paths, residuals)
    save_predictive_interval_plot(paths)
    save_diagnostic_plot(paths, diagnostics)
    save_complexity_map(paths)


def build_report(
    paths: M4Paths,
    params: pd.DataFrame,
    diagnostics: pd.DataFrame,
    predictive: pd.DataFrame,
    recommendations: pd.DataFrame,
    loo_waic: pd.DataFrame,
) -> None:
    p = params.set_index("model_id")
    d = diagnostics.set_index("model_id")
    pred = predictive.set_index("model_id")
    primary = recommendations.loc[
        recommendations["recommended_role"] == "primary_preliminary_result", "model_id"
    ].iloc[0]
    loo_status = ", ".join(f"{row.model_id}: {row.status}" for row in loo_waic.itertuples())
    text = f"""# M4 - Comparação de Modelos - HAT-P-7 b

## 1. Objetivo do M4

O M4 compara os modelos M1, M2 e M3 já ajustados para HAT-P-7 b. Ele não cria
um novo modelo bayesiano e não altera RAW, Silver, Gold ou os artefatos dos
modelos anteriores.

Perguntas centrais:

- como os pressupostos de cada modelo afetam a profundidade inferida;
- qual modelo descreve melhor o formato observado do trânsito;
- qual modelo apresenta melhor comportamento preditivo;
- qual modelo oferece melhor equilíbrio entre interpretabilidade e
  flexibilidade;
- qual modelo deve ser usado como resultado principal preliminar.

## 2. Modelos Comparados

| Modelo | Papel | Hipótese principal |
|---|---|---|
| M1 | Baseline | Trânsito box-shaped com meia largura fixa |
| M2 | Descrição preditiva | Fluxo suave em função da fase por bases radiais |
| M3 | Resultado preliminar | Trânsito trapezoidal aproximado |

## 3. Critérios de Comparação

Foram comparados:

- profundidade e `Rp/Rs`, quando definidos;
- diagnósticos MCMC;
- resíduos;
- métricas preditivas simples;
- cobertura de intervalos preditivos de 94%;
- equilíbrio entre interpretabilidade física e flexibilidade.

## 4. Comparação de Parâmetros

Arquivo:

```text
{relative_path(paths.parameter_comparison_path, paths.project_root)}
```

| Modelo | Tipo de profundidade | Profundidade média | HDI 3% | HDI 97% | Rp/Rs médio |
|---|---|---:|---:|---:|---:|
| M1 | direta | {p.loc['M1','depth_mean']:.8f} | {p.loc['M1','depth_hdi_3']:.8f} | {p.loc['M1','depth_hdi_97']:.8f} | {p.loc['M1','rp_rs_mean']:.8f} |
| M2 | exploratória | {p.loc['M2','depth_mean']:.8f} | {p.loc['M2','depth_hdi_3']:.8f} | {p.loc['M2','depth_hdi_97']:.8f} | não estimado diretamente |
| M3 | direta aproximada | {p.loc['M3','depth_mean']:.8f} | {p.loc['M3','depth_hdi_3']:.8f} | {p.loc['M3','depth_hdi_97']:.8f} | {p.loc['M3','rp_rs_mean']:.8f} |

Figura:

![Comparação de profundidade](../figures/model_comparison/hat_p_7_b/01_depth_comparison.png)

![Comparação de Rp/Rs](../figures/model_comparison/hat_p_7_b/02_rp_rs_comparison.png)

## 5. Comparação de Diagnósticos

Arquivo:

```text
{relative_path(paths.diagnostic_comparison_path, paths.project_root)}
```

| Modelo | R-hat máximo | ESS mínimo | Divergências | Status |
|---|---:|---:|---:|---|
| M1 | {d.loc['M1','r_hat_max']:.8f} | {d.loc['M1','ess_min']:.2f} | {int(d.loc['M1','divergences'])} | {d.loc['M1','diagnostic_status']} |
| M2 | {d.loc['M2','r_hat_max']:.8f} | {d.loc['M2','ess_min']:.2f} | {int(d.loc['M2','divergences'])} | {d.loc['M2','diagnostic_status']} |
| M3 | {d.loc['M3','r_hat_max']:.8f} | {d.loc['M3','ess_min']:.2f} | {int(d.loc['M3','divergences'])} | {d.loc['M3','diagnostic_status']} |

Figura:

![Comparação de diagnósticos](../figures/model_comparison/hat_p_7_b/06_diagnostic_comparison.png)

## 6. Comparação Preditiva

Arquivo:

```text
{relative_path(paths.predictive_metric_comparison_path, paths.project_root)}
```

| Modelo | RMSE | MAE | Desvio padrão dos resíduos | Cobertura 94% |
|---|---:|---:|---:|---:|
| M1 | {pred.loc['M1','rmse']:.8f} | {pred.loc['M1','mae']:.8f} | {pred.loc['M1','residual_std']:.8f} | {pred.loc['M1','coverage_94']:.6f} |
| M2 | {pred.loc['M2','rmse']:.8f} | {pred.loc['M2','mae']:.8f} | {pred.loc['M2','residual_std']:.8f} | {pred.loc['M2','coverage_94']:.6f} |
| M3 | {pred.loc['M3','rmse']:.8f} | {pred.loc['M3','mae']:.8f} | {pred.loc['M3','residual_std']:.8f} | {pred.loc['M3','coverage_94']:.6f} |

Figura:

![Intervalos preditivos](../figures/model_comparison/hat_p_7_b/05_predictive_interval_comparison.png)

## 7. Comparação Visual dos Ajustes

Figura:

![Comparação dos ajustes](../figures/model_comparison/hat_p_7_b/03_model_fit_comparison.png)

Leitura:

- M1 é transparente, mas rígido;
- M2 acompanha uma forma suave, mas sua profundidade é derivada de modo
  exploratório;
- M3 captura uma forma intermediária, com ingresso e egresso explícitos.

## 8. Resíduos

Arquivo:

```text
{relative_path(paths.residual_comparison_path, paths.project_root)}
```

Figura:

![Comparação de resíduos](../figures/model_comparison/hat_p_7_b/04_residual_comparison.png)

## 9. LOO/WAIC

Arquivo:

```text
{relative_path(paths.loo_waic_path, paths.project_root)}
```

Status:

```text
{loo_status}
```

Os arquivos `trace.nc` atuais não contêm grupo `log_likelihood`, portanto
LOO/WAIC não foram forçados nesta etapa. O M4 registra essa limitação em vez
de inventar valores.

## 10. Discussão dos Pressupostos

A profundidade muda porque cada modelo define a forma do trânsito de maneira
diferente:

- M1 usa uma caixa fixa e estima uma profundidade média;
- M2 usa uma curva suave e deriva uma profundidade exploratória pela diferença
  entre baseline de borda e mínimo da curva;
- M3 estima profundidade dentro de uma forma trapezoidal com centro, duração e
  ingresso/egresso.

O `predicted_depth` do M2 não deve ser comparado diretamente como parâmetro
físico equivalente ao `depth` de M1/M3. Ele é útil como diagnóstico de forma,
não como estimativa final de `Rp/Rs`.

## 11. Recomendação de Modelo Principal Preliminar

Arquivo:

```text
{relative_path(paths.recommendation_summary_path, paths.project_root)}
```

Modelo recomendado:

```text
{primary}
```

Justificativa:

M3 é recomendado como resultado principal preliminar porque combina bons
diagnósticos, profundidade direta, `Rp/Rs` derivado, duração total aproximada
e ingresso/egresso. M1 deve permanecer como baseline de referência e M2 como
descrição preditiva da curva suave.

Figura conceitual:

![Mapa flexibilidade interpretabilidade](../figures/model_comparison/hat_p_7_b/07_model_complexity_interpretability_map.png)

## 12. Limitações

Mesmo com a recomendação de M3, ainda não há caracterização física final.

Limitações principais:

- nenhum modelo usa limb darkening;
- nenhum modelo usa Mandel & Agol;
- nenhum modelo usa geometria orbital completa;
- LOO/WAIC não foram calculados porque os traces não têm log likelihood;
- todos os modelos usam apenas Kepler para HAT-P-7 b;
- M2 não estima `Rp/Rs` diretamente;
- M3 ainda é uma aproximação trapezoidal.

## 13. Próximos Passos

O próximo passo natural é um modelo físico completo ou semi-físico:

- gerar log likelihood nos próximos modelos para comparação formal;
- considerar `batman` ou formulação Mandel & Agol;
- incluir limb darkening com priors informativos;
- avaliar integração por tempo de exposição;
- comparar modelos com posterior predictive checks e, se possível, LOO/WAIC.
"""
    paths.report_path.write_text(text, encoding="utf-8")


def save_config_and_summary(
    paths: M4Paths,
    params: pd.DataFrame,
    diagnostics: pd.DataFrame,
    predictive: pd.DataFrame,
    recommendations: pd.DataFrame,
    loo_waic: pd.DataFrame,
) -> None:
    config = {
        "created_at_utc": utc_now(),
        "model_name": MODEL_NAME,
        "planet_name": PLANET_NAME,
        "planet_slug": PLANET_SLUG,
        "host_star": HOST_STAR,
        "mission": MISSION,
        "source_gold_path": SOURCE_GOLD_PATH,
        "models_compared": MODEL_ORDER,
        "inputs": {
            "m1_trace": relative_path(paths.m1_trace_path, paths.project_root),
            "m2_trace": relative_path(paths.m2_trace_path, paths.project_root),
            "m3_trace": relative_path(paths.m3_trace_path, paths.project_root),
            "m1_derived": relative_path(paths.m1_derived_path, paths.project_root),
            "m2_curve": relative_path(paths.m2_curve_path, paths.project_root),
            "m3_derived": relative_path(paths.m3_derived_path, paths.project_root),
        },
        "comparison_criteria": [
            "parameter_comparison",
            "mcmc_diagnostics",
            "predictive_metrics",
            "residuals",
            "loo_waic_if_available",
            "interpretability_flexibility_balance",
        ],
        "notes": "M4 is a comparison stage and does not sample a new Bayesian model.",
    }
    paths.config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

    recommended = recommendations.loc[
        recommendations["recommended_role"] == "primary_preliminary_result"
    ].iloc[0]
    summary = {
        "created_at_utc": utc_now(),
        "model_name": MODEL_NAME,
        "planet_name": PLANET_NAME,
        "models_compared": MODEL_ORDER,
        "parameter_comparison_path": relative_path(paths.parameter_comparison_path, paths.project_root),
        "diagnostic_comparison_path": relative_path(paths.diagnostic_comparison_path, paths.project_root),
        "predictive_metric_comparison_path": relative_path(
            paths.predictive_metric_comparison_path, paths.project_root
        ),
        "residual_comparison_path": relative_path(paths.residual_comparison_path, paths.project_root),
        "loo_waic_path": relative_path(paths.loo_waic_path, paths.project_root),
        "recommendation_summary_path": relative_path(
            paths.recommendation_summary_path, paths.project_root
        ),
        "figures_dir": relative_path(paths.figure_dir, paths.project_root),
        "report_path": relative_path(paths.report_path, paths.project_root),
        "depth_comparison": params.to_dict(orient="records"),
        "diagnostic_comparison": diagnostics.to_dict(orient="records"),
        "predictive_metric_comparison": predictive.to_dict(orient="records"),
        "loo_waic_status": loo_waic.to_dict(orient="records"),
        "recommended_primary_preliminary_model": recommended["model_id"],
        "recommendation_note": recommended["notes"],
    }
    paths.summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def run_model_comparison(project_root: Path | None = None) -> dict[str, Any]:
    paths = build_paths(project_root)
    ensure_directories(paths)

    summaries = {
        "M1": read_json(paths.m1_summary_path),
        "M2": read_json(paths.m2_summary_path),
        "M3": read_json(paths.m3_summary_path),
    }

    params = build_parameter_comparison(paths, summaries)
    diagnostics = build_diagnostic_comparison(paths, summaries)
    residuals = build_residual_comparison(paths)
    predictive = build_predictive_metric_comparison(paths, summaries, residuals)
    loo_waic = build_loo_waic_comparison(paths)
    recommendations = build_recommendation_summary(paths, diagnostics, predictive)
    save_all_figures(paths, params, diagnostics, residuals)
    build_report(paths, params, diagnostics, predictive, recommendations, loo_waic)
    save_config_and_summary(paths, params, diagnostics, predictive, recommendations, loo_waic)

    primary = recommendations.loc[
        recommendations["recommended_role"] == "primary_preliminary_result"
    ].iloc[0]
    return {
        "model_name": MODEL_NAME,
        "planet_name": PLANET_NAME,
        "parameter_comparison": relative_path(paths.parameter_comparison_path, paths.project_root),
        "diagnostic_comparison": relative_path(paths.diagnostic_comparison_path, paths.project_root),
        "predictive_metric_comparison": relative_path(
            paths.predictive_metric_comparison_path, paths.project_root
        ),
        "residual_comparison": relative_path(paths.residual_comparison_path, paths.project_root),
        "loo_waic_comparison": relative_path(paths.loo_waic_path, paths.project_root),
        "recommended_primary_preliminary_model": primary["model_id"],
        "report": relative_path(paths.report_path, paths.project_root),
    }


def main() -> None:
    result = run_model_comparison()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
