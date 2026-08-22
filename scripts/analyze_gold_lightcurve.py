"""Exploratory diagnostics for the HAT-P-7 b GOLD light curve.

This script reads the existing GOLD layer and writes only derived EDA artifacts
under notebooks/reports/figures/tables. It does not modify RAW, Silver, or Gold.
"""

from __future__ import annotations

import json
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MPLCONFIGDIR = Path("/tmp") / "matplotlib-cache"
MPLCONFIGDIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPLCONFIGDIR))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


PLANET_SLUG = "hat_p_7_b"
PLANET_NAME = "HAT-P-7 b"
DEFAULT_BINS = 80
WINDOW_HALF_WIDTHS_DAYS = (0.50, 0.25, 0.15, 0.10, 0.05)


@dataclass(frozen=True)
class GoldEdaPaths:
    """Filesystem paths used by the GOLD EDA."""

    project_root: Path
    gold_root: Path
    reference_parameters: Path
    primary_lightcurve: Path
    quality_filtered_lightcurve: Path
    phase_folded_lightcurve: Path
    transit_window_lightcurve: Path
    gold_lightcurve_summary: Path
    figures_dir: Path
    tables_dir: Path
    report_path: Path


def resolve_project_root(project_root: Path | None = None) -> Path:
    """Resolve the repository root from a script, notebook, or explicit path."""

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


def build_paths(project_root: Path | None = None) -> GoldEdaPaths:
    root = resolve_project_root(project_root)
    gold_root = root / "data" / "gold" / PLANET_SLUG
    return GoldEdaPaths(
        project_root=root,
        gold_root=gold_root,
        reference_parameters=gold_root / "catalogs" / "reference_parameters.csv",
        primary_lightcurve=gold_root / "lightcurves" / "primary_lightcurve.csv",
        quality_filtered_lightcurve=gold_root
        / "lightcurves"
        / "primary_lightcurve_quality_filtered.csv",
        phase_folded_lightcurve=gold_root / "modeling" / "phase_folded_lightcurve.csv",
        transit_window_lightcurve=gold_root
        / "modeling"
        / "transit_window_lightcurve.csv",
        gold_lightcurve_summary=gold_root / "validation" / "gold_lightcurve_summary.csv",
        figures_dir=root / "figures" / "gold_eda" / PLANET_SLUG,
        tables_dir=root / "tables" / "gold_eda" / PLANET_SLUG,
        report_path=root / "reports" / "gold_eda_hat_p_7_b_report.md",
    )


def relative_path(path: Path, project_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(path.resolve())


def ensure_output_directories(paths: GoldEdaPaths) -> None:
    paths.figures_dir.mkdir(parents=True, exist_ok=True)
    paths.tables_dir.mkdir(parents=True, exist_ok=True)
    paths.report_path.parent.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required GOLD file not found: {path}")
    return pd.read_csv(path, low_memory=False)


def to_numeric(dataframe: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    copy = dataframe.copy()
    for column in columns:
        if column in copy.columns:
            copy[column] = pd.to_numeric(copy[column], errors="coerce")
    return copy


def require_columns(
    dataframe: pd.DataFrame,
    columns: list[str],
    source_name: str,
    warnings: list[str],
) -> None:
    missing = [column for column in columns if column not in dataframe.columns]
    if missing:
        warnings.append(
            f"{source_name}: missing expected columns: {', '.join(missing)}"
        )


def load_gold_inputs(paths: GoldEdaPaths) -> dict[str, pd.DataFrame]:
    inputs = {
        "reference": read_csv(paths.reference_parameters),
        "primary": read_csv(paths.primary_lightcurve),
        "quality_filtered": read_csv(paths.quality_filtered_lightcurve),
        "phase_folded": read_csv(paths.phase_folded_lightcurve),
        "transit_window": read_csv(paths.transit_window_lightcurve),
        "gold_summary": read_csv(paths.gold_lightcurve_summary),
    }

    numeric_columns = [
        "time",
        "phase",
        "flux",
        "flux_err",
        "quality",
        "orbital_period_days",
        "transit_midpoint_used",
        "transit_window_half_width_days",
        "transit_duration_hours_used",
        "transit_duration_hours",
        "transit_depth",
    ]
    return {
        name: to_numeric(dataframe, numeric_columns)
        for name, dataframe in inputs.items()
    }


def finite_series(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric[np.isfinite(numeric)]


def safe_float(value: Any) -> float:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return float("nan")
    return float(numeric)


def first_non_missing(dataframe: pd.DataFrame, column: str) -> Any:
    if column not in dataframe.columns:
        return None
    series = dataframe[column].dropna()
    if series.empty:
        return None
    return series.iloc[0]


def stats_dict(prefix: str, series: pd.Series) -> dict[str, float | int]:
    finite = finite_series(series)
    if finite.empty:
        return {
            f"{prefix}_min": float("nan"),
            f"{prefix}_max": float("nan"),
            f"{prefix}_median": float("nan"),
            f"{prefix}_mean": float("nan"),
            f"{prefix}_std": float("nan"),
        }
    return {
        f"{prefix}_min": float(finite.min()),
        f"{prefix}_max": float(finite.max()),
        f"{prefix}_median": float(finite.median()),
        f"{prefix}_mean": float(finite.mean()),
        f"{prefix}_std": float(finite.std(ddof=1)),
    }


def transit_duration_days(reference: pd.DataFrame, transit_window: pd.DataFrame) -> float:
    value = first_non_missing(transit_window, "transit_duration_hours_used")
    if value is None:
        value = first_non_missing(reference, "transit_duration_hours")
    duration_hours = safe_float(value)
    if math.isnan(duration_hours) or duration_hours <= 0:
        return float("nan")
    return duration_hours / 24.0


def compute_visual_depth(
    dataframe: pd.DataFrame,
    duration_days: float,
) -> dict[str, float | int | str]:
    """Compute a non-inferential visual depth diagnostic.

    The diagnostic compares the median flux inside one transit-duration core
    with the median flux in the surrounding window. It is not a fitted transit
    depth and should not be interpreted as a scientific estimate.
    """

    required = {"phase", "flux"}
    if not required.issubset(dataframe.columns) or math.isnan(duration_days):
        return {
            "in_transit_count": 0,
            "out_of_transit_count": 0,
            "in_transit_flux_median": float("nan"),
            "out_of_transit_flux_median": float("nan"),
            "out_of_transit_flux_std": float("nan"),
            "approximate_depth_visual": float("nan"),
            "approximate_depth_flux_units": float("nan"),
            "notes": "insufficient columns or transit duration unavailable",
        }

    valid = dataframe.loc[:, ["phase", "flux"]].copy()
    valid["phase"] = pd.to_numeric(valid["phase"], errors="coerce")
    valid["flux"] = pd.to_numeric(valid["flux"], errors="coerce")
    valid = valid.dropna(subset=["phase", "flux"])
    if valid.empty:
        return {
            "in_transit_count": 0,
            "out_of_transit_count": 0,
            "in_transit_flux_median": float("nan"),
            "out_of_transit_flux_median": float("nan"),
            "out_of_transit_flux_std": float("nan"),
            "approximate_depth_visual": float("nan"),
            "approximate_depth_flux_units": float("nan"),
            "notes": "no finite phase/flux values",
        }

    core_half_width = duration_days / 2.0
    in_transit = valid.loc[valid["phase"].abs() <= core_half_width, "flux"]
    out_of_transit = valid.loc[valid["phase"].abs() > core_half_width, "flux"]
    if in_transit.empty or out_of_transit.empty:
        return {
            "in_transit_count": int(len(in_transit)),
            "out_of_transit_count": int(len(out_of_transit)),
            "in_transit_flux_median": float(in_transit.median())
            if not in_transit.empty
            else float("nan"),
            "out_of_transit_flux_median": float(out_of_transit.median())
            if not out_of_transit.empty
            else float("nan"),
            "out_of_transit_flux_std": float(out_of_transit.std(ddof=1))
            if len(out_of_transit) > 1
            else float("nan"),
            "approximate_depth_visual": float("nan"),
            "approximate_depth_flux_units": float("nan"),
            "notes": "window has no usable in-transit or out-of-transit baseline",
        }

    oot_median = float(out_of_transit.median())
    in_median = float(in_transit.median())
    depth_flux_units = oot_median - in_median
    depth_fraction = depth_flux_units / oot_median if oot_median else float("nan")
    return {
        "in_transit_count": int(len(in_transit)),
        "out_of_transit_count": int(len(out_of_transit)),
        "in_transit_flux_median": in_median,
        "out_of_transit_flux_median": oot_median,
        "out_of_transit_flux_std": float(out_of_transit.std(ddof=1)),
        "approximate_depth_visual": float(depth_fraction),
        "approximate_depth_flux_units": float(depth_flux_units),
        "notes": (
            "exploratory median contrast only; not a fitted or Bayesian estimate"
        ),
    }


def build_eda_summary(
    data: dict[str, pd.DataFrame],
    duration_days: float,
    recommended_window: float,
) -> pd.DataFrame:
    primary = data["primary"]
    quality_filtered = data["quality_filtered"]
    phase_folded = data["phase_folded"]
    transit_window = data["transit_window"]

    quality = (
        pd.to_numeric(primary["quality"], errors="coerce")
        if "quality" in primary.columns
        else pd.Series(dtype=float)
    )
    visual_depth = compute_visual_depth(transit_window, duration_days)

    row: dict[str, Any] = {
        "planet_name": first_non_missing(primary, "planet_name") or PLANET_NAME,
        "mission": first_non_missing(primary, "mission") or "Kepler",
        "rows_primary": int(len(primary)),
        "rows_quality_filtered": int(len(quality_filtered)),
        "rows_phase_folded": int(len(phase_folded)),
        "rows_transit_window": int(len(transit_window)),
        "time_min": float(finite_series(primary["time"]).min())
        if "time" in primary.columns and not finite_series(primary["time"]).empty
        else float("nan"),
        "time_max": float(finite_series(primary["time"]).max())
        if "time" in primary.columns and not finite_series(primary["time"]).empty
        else float("nan"),
        "phase_min": float(finite_series(transit_window["phase"]).min())
        if "phase" in transit_window.columns
        and not finite_series(transit_window["phase"]).empty
        else float("nan"),
        "phase_max": float(finite_series(transit_window["phase"]).max())
        if "phase" in transit_window.columns
        and not finite_series(transit_window["phase"]).empty
        else float("nan"),
        "missing_flux_count": int(transit_window["flux"].isna().sum())
        if "flux" in transit_window.columns
        else int(len(transit_window)),
        "missing_flux_err_count": int(transit_window["flux_err"].isna().sum())
        if "flux_err" in transit_window.columns
        else int(len(transit_window)),
        "quality_zero_count": int((quality == 0).sum()) if not quality.empty else 0,
        "quality_nonzero_count": int((quality.notna() & (quality != 0)).sum())
        if not quality.empty
        else 0,
        "transit_duration_days": duration_days,
        "recommended_window_half_width_days": recommended_window,
    }
    row.update(stats_dict("flux", transit_window["flux"]))
    row.update(
        {
            "flux_err_median": stats_dict(
                "flux_err", transit_window["flux_err"]
            )["flux_err_median"],
            "flux_err_mean": stats_dict("flux_err", transit_window["flux_err"])[
                "flux_err_mean"
            ],
            "flux_err_std": stats_dict("flux_err", transit_window["flux_err"])[
                "flux_err_std"
            ],
        }
    )
    row.update(visual_depth)
    return pd.DataFrame([row])


def build_window_comparison(
    phase_folded: pd.DataFrame,
    duration_days: float,
    windows: tuple[float, ...] = WINDOW_HALF_WIDTHS_DAYS,
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for half_width in windows:
        if "phase" not in phase_folded.columns:
            subset = phase_folded.iloc[0:0].copy()
        else:
            phase = pd.to_numeric(phase_folded["phase"], errors="coerce")
            subset = phase_folded.loc[phase.abs() <= half_width].copy()

        depth = compute_visual_depth(subset, duration_days)
        row: dict[str, Any] = {
            "window_half_width_days": half_width,
            "row_count": int(len(subset)),
            "flux_median": float(finite_series(subset["flux"]).median())
            if "flux" in subset.columns and not finite_series(subset["flux"]).empty
            else float("nan"),
            "flux_std": float(finite_series(subset["flux"]).std(ddof=1))
            if "flux" in subset.columns and len(finite_series(subset["flux"])) > 1
            else float("nan"),
        }
        row.update(depth)
        records.append(row)
    return pd.DataFrame(records)


def choose_recommended_window(
    window_comparison: pd.DataFrame,
    duration_days: float,
) -> float:
    if window_comparison.empty or math.isnan(duration_days):
        return float("nan")

    core_half_width = duration_days / 2.0
    viable = window_comparison.copy()
    viable = viable.loc[
        (viable["window_half_width_days"] >= 1.5 * core_half_width)
        & (viable["row_count"] >= 200)
        & (viable["out_of_transit_count"] >= 50)
        & viable["approximate_depth_visual"].notna()
    ]
    if not viable.empty:
        return float(viable.sort_values("window_half_width_days").iloc[0][
            "window_half_width_days"
        ])

    fallback = window_comparison.loc[
        window_comparison["approximate_depth_visual"].notna()
    ]
    if not fallback.empty:
        return float(fallback.sort_values("window_half_width_days").iloc[0][
            "window_half_width_days"
        ])
    return float("nan")


def save_dataframe(dataframe: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(path, index=False)


def save_scatter_plot(
    dataframe: pd.DataFrame,
    x_column: str,
    y_column: str,
    path: Path,
    title: str,
    xlabel: str,
    ylabel: str,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    if x_column in dataframe.columns and y_column in dataframe.columns:
        plot_data = dataframe[[x_column, y_column]].dropna()
        ax.scatter(
            plot_data[x_column],
            plot_data[y_column],
            s=5,
            alpha=0.45,
            linewidths=0,
        )
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def build_binned_phase_statistics(
    transit_window: pd.DataFrame,
    bins: int = DEFAULT_BINS,
) -> pd.DataFrame:
    required = {"phase", "flux"}
    if not required.issubset(transit_window.columns):
        return pd.DataFrame()

    valid = transit_window.loc[:, ["phase", "flux"]].copy()
    valid["phase"] = pd.to_numeric(valid["phase"], errors="coerce")
    valid["flux"] = pd.to_numeric(valid["flux"], errors="coerce")
    valid = valid.dropna(subset=["phase", "flux"])
    if valid.empty:
        return pd.DataFrame()

    edges = np.linspace(valid["phase"].min(), valid["phase"].max(), bins + 1)
    valid["phase_bin"] = pd.cut(valid["phase"], edges, include_lowest=True)
    grouped = valid.groupby("phase_bin", observed=True)["flux"]
    stats = grouped.agg(
        flux_median="median",
        flux_q25=lambda values: values.quantile(0.25),
        flux_q75=lambda values: values.quantile(0.75),
        flux_std="std",
        count="count",
    ).reset_index()
    stats["phase_mid"] = stats["phase_bin"].apply(lambda interval: interval.mid)
    stats["flux_sem"] = stats["flux_std"] / np.sqrt(stats["count"])
    return stats.sort_values("phase_mid")


def save_binned_transit_plot(
    transit_window: pd.DataFrame,
    binned: pd.DataFrame,
    path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    if {"phase", "flux"}.issubset(transit_window.columns):
        valid = transit_window[["phase", "flux"]].dropna()
        ax.scatter(
            valid["phase"],
            valid["flux"],
            s=5,
            alpha=0.16,
            linewidths=0,
            label="pontos individuais",
        )
    if not binned.empty:
        x = pd.to_numeric(binned["phase_mid"], errors="coerce")
        median = pd.to_numeric(binned["flux_median"], errors="coerce")
        q25 = pd.to_numeric(binned["flux_q25"], errors="coerce")
        q75 = pd.to_numeric(binned["flux_q75"], errors="coerce")
        ax.plot(x, median, linewidth=1.6, label="mediana por bin")
        ax.fill_between(x, q25, q75, alpha=0.2, label="intervalo interquartil")
    ax.axvline(0, linestyle="--", linewidth=1)
    ax.set_title("HAT-P-7 b - janela de trânsito com binning visual")
    ax.set_xlabel("Fase orbital em dias, centrada no trânsito")
    ax.set_ylabel("Fluxo")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def save_histogram(
    dataframe: pd.DataFrame,
    column: str,
    path: Path,
    title: str,
    xlabel: str,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    if column in dataframe.columns:
        values = finite_series(dataframe[column])
        if not values.empty:
            ax.hist(values, bins=50, alpha=0.85)
            ax.axvline(values.median(), linestyle="--", linewidth=1.4, label="mediana")
            ax.legend(loc="best")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Contagem")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def save_window_width_comparison_plot(
    phase_folded: pd.DataFrame,
    window_comparison: pd.DataFrame,
    path: Path,
) -> None:
    fig, axes = plt.subplots(
        len(WINDOW_HALF_WIDTHS_DAYS),
        1,
        figsize=(10, 13),
        sharey=True,
    )
    if len(WINDOW_HALF_WIDTHS_DAYS) == 1:
        axes = [axes]

    for ax, half_width in zip(axes, WINDOW_HALF_WIDTHS_DAYS):
        if {"phase", "flux"}.issubset(phase_folded.columns):
            phase = pd.to_numeric(phase_folded["phase"], errors="coerce")
            subset = phase_folded.loc[phase.abs() <= half_width, ["phase", "flux"]]
            subset = subset.dropna()
            ax.scatter(
                subset["phase"],
                subset["flux"],
                s=5,
                alpha=0.35,
                linewidths=0,
            )
        else:
            subset = pd.DataFrame()

        row = window_comparison.loc[
            window_comparison["window_half_width_days"] == half_width
        ]
        depth = (
            row["approximate_depth_visual"].iloc[0]
            if not row.empty and "approximate_depth_visual" in row.columns
            else float("nan")
        )
        depth_text = "n/a" if pd.isna(depth) else f"{depth:.5f}"
        ax.axvline(0, linestyle="--", linewidth=1)
        ax.set_xlim(-half_width, half_width)
        ax.set_title(
            f"±{half_width:.2f} dias | n={len(subset)} | profundidade visual={depth_text}"
        )
        ax.set_ylabel("Fluxo")
        ax.grid(True, alpha=0.25)

    axes[-1].set_xlabel("Fase orbital em dias, centrada no trânsito")
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def save_all_figures(
    data: dict[str, pd.DataFrame],
    binned: pd.DataFrame,
    window_comparison: pd.DataFrame,
    paths: GoldEdaPaths,
) -> list[Path]:
    figures = [
        paths.figures_dir / "01_primary_lightcurve_time.png",
        paths.figures_dir / "02_quality_filtered_lightcurve_time.png",
        paths.figures_dir / "03_phase_folded_lightcurve_full.png",
        paths.figures_dir / "04_transit_window_lightcurve.png",
        paths.figures_dir / "05_transit_window_binned.png",
        paths.figures_dir / "06_flux_distribution.png",
        paths.figures_dir / "07_flux_err_distribution.png",
        paths.figures_dir / "08_window_width_comparison.png",
    ]
    save_scatter_plot(
        data["primary"],
        "time",
        "flux",
        figures[0],
        "HAT-P-7 b - curva primária em função do tempo",
        "Tempo Kepler / BKJD",
        "Fluxo",
    )
    save_scatter_plot(
        data["quality_filtered"],
        "time",
        "flux",
        figures[1],
        "HAT-P-7 b - curva filtrada por qualidade em função do tempo",
        "Tempo Kepler / BKJD",
        "Fluxo",
    )
    save_scatter_plot(
        data["phase_folded"],
        "phase",
        "flux",
        figures[2],
        "HAT-P-7 b - curva faseada completa",
        "Fase orbital em dias, centrada no trânsito",
        "Fluxo",
    )
    save_scatter_plot(
        data["transit_window"],
        "phase",
        "flux",
        figures[3],
        "HAT-P-7 b - janela de trânsito Gold",
        "Fase orbital em dias, centrada no trânsito",
        "Fluxo",
    )
    save_binned_transit_plot(data["transit_window"], binned, figures[4])
    save_histogram(
        data["transit_window"],
        "flux",
        figures[5],
        "HAT-P-7 b - distribuição do fluxo na janela de trânsito",
        "Fluxo",
    )
    save_histogram(
        data["transit_window"],
        "flux_err",
        figures[6],
        "HAT-P-7 b - distribuição de flux_err na janela de trânsito",
        "flux_err",
    )
    save_window_width_comparison_plot(
        data["phase_folded"],
        window_comparison,
        figures[7],
    )
    return figures


def markdown_table(dataframe: pd.DataFrame, columns: list[str]) -> str:
    if dataframe.empty:
        return "_Sem registros._\n"
    subset = dataframe.loc[:, columns].copy()
    for column in subset.columns:
        if pd.api.types.is_float_dtype(subset[column]):
            subset[column] = subset[column].map(
                lambda value: "" if pd.isna(value) else f"{value:.6g}"
            )
        else:
            subset[column] = subset[column].astype(str)
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(row) + " |"
        for row in subset.astype(str).values.tolist()
    ]
    return "\n".join([header, separator, *body]) + "\n"


def fmt(value: Any, digits: int = 6) -> str:
    numeric = safe_float(value)
    if math.isnan(numeric):
        return "n/a"
    return f"{numeric:.{digits}g}"


def write_report(
    data: dict[str, pd.DataFrame],
    summary: pd.DataFrame,
    window_comparison: pd.DataFrame,
    figures: list[Path],
    paths: GoldEdaPaths,
    warnings: list[str],
) -> None:
    row = summary.iloc[0].to_dict()
    recommended_window = row.get("recommended_window_half_width_days")
    current_window = row.get("phase_max", float("nan"))
    duration_days = row.get("transit_duration_days", float("nan"))
    core_half_width = duration_days / 2.0 if not math.isnan(duration_days) else float("nan")
    visual_depth = row.get("approximate_depth_visual", float("nan"))
    out_std = row.get("out_of_transit_flux_std", float("nan"))
    flux_err_missing = int(row.get("missing_flux_err_count", 0))
    flux_err_available = (
        "Sim"
        if "flux_err" in data["transit_window"].columns
        and flux_err_missing < len(data["transit_window"])
        else "Não"
    )
    transit_visible = (
        "Sim"
        if not pd.isna(visual_depth)
        and safe_float(visual_depth) > 0
        and int(row.get("in_transit_count", 0)) > 0
        and int(row.get("out_of_transit_count", 0)) > 0
        else "Inconclusivo"
    )
    current_window_is_wide = (
        "Sim"
        if not math.isnan(current_window)
        and not math.isnan(core_half_width)
        and current_window >= 4.0 * core_half_width
        else "Não"
    )

    warning_text = "\n".join(f"- {item}" for item in warnings) if warnings else "- Nenhum warning crítico registrado."
    figure_text = "\n".join(
        f"- `{relative_path(path, paths.project_root)}`" for path in figures
    )
    source_files = [
        paths.reference_parameters,
        paths.primary_lightcurve,
        paths.quality_filtered_lightcurve,
        paths.phase_folded_lightcurve,
        paths.transit_window_lightcurve,
        paths.gold_lightcurve_summary,
    ]
    source_text = "\n".join(
        f"- `{relative_path(path, paths.project_root)}`" for path in source_files
    )

    content = f"""# EDA Gold - HAT-P-7 b

## 1. Objetivo da EDA

Esta etapa realiza uma análise exploratória e diagnóstica da camada Gold de
HAT-P-7 b antes da modelagem bayesiana. O objetivo é verificar se a curva de
luz preparada na Gold é coerente, rastreável e numericamente adequada para uma
primeira modelagem.

Esta EDA **não** realiza inferência bayesiana, ajuste físico de trânsito,
amostragem posterior ou comparação com literatura. As métricas de profundidade
abaixo são aproximações exploratórias por contraste de medianas.

## 2. Arquivos Gold utilizados

{source_text}

## 3. Resumo dos dados

| Métrica | Valor |
| --- | --- |
| Planeta | {row.get("planet_name", PLANET_NAME)} |
| Missão | {row.get("mission", "Kepler")} |
| Linhas na curva primária | {int(row.get("rows_primary", 0))} |
| Linhas após filtro de qualidade | {int(row.get("rows_quality_filtered", 0))} |
| Linhas na curva faseada | {int(row.get("rows_phase_folded", 0))} |
| Linhas na janela Gold atual | {int(row.get("rows_transit_window", 0))} |
| Intervalo de tempo primário | {fmt(row.get("time_min"))} a {fmt(row.get("time_max"))} |
| Intervalo de fase da janela atual | {fmt(row.get("phase_min"))} a {fmt(row.get("phase_max"))} dias |
| Fluxo mediano na janela | {fmt(row.get("flux_median"))} |
| Desvio padrão do fluxo na janela | {fmt(row.get("flux_std"))} |
| `flux_err` mediano | {fmt(row.get("flux_err_median"))} |
| Valores ausentes em `flux` na janela | {int(row.get("missing_flux_count", 0))} |
| Valores ausentes em `flux_err` na janela | {int(row.get("missing_flux_err_count", 0))} |

Tabela derivada:

- `{relative_path(paths.tables_dir / "gold_eda_summary.csv", paths.project_root)}`

## 4. Qualidade e flags

A curva primária possui `{int(row.get("quality_zero_count", 0))}` pontos com
`quality == 0` e `{int(row.get("quality_nonzero_count", 0))}` pontos com
`quality != 0`. A Gold filtrada por qualidade manteve os pontos com
`quality == 0`, resultando em `{int(row.get("rows_quality_filtered", 0))}`
linhas.

Para a modelagem preliminar, a curva filtrada por qualidade é a base mais
adequada, pois reduz pontos explicitamente marcados por flags instrumentais.

## 5. Curva faseada

A curva faseada foi criada na Gold usando o período orbital e o tempo central
de trânsito convertidos para a escala temporal Kepler. A EDA encontrou
`{int(row.get("rows_phase_folded", 0))}` pontos faseados.

Resposta objetiva: **a curva mostra um trânsito visualmente identificável?**

**{transit_visible}.** A aproximação exploratória por contraste de medianas na
janela atual é `{fmt(visual_depth, 5)}` em fração relativa do fluxo fora do
trânsito. Esse valor não é uma estimativa inferencial; ele serve apenas como
diagnóstico visual.

Figura principal:

- `{relative_path(paths.figures_dir / "03_phase_folded_lightcurve_full.png", paths.project_root)}`

![Curva faseada completa](../figures/gold_eda/hat_p_7_b/03_phase_folded_lightcurve_full.png)

## 6. Janela de trânsito

A janela Gold atual contém `{int(row.get("rows_transit_window", 0))}` pontos e
cobre aproximadamente `{fmt(abs(row.get("phase_min", float("nan"))), 5)}` a
`{fmt(abs(row.get("phase_max", float("nan"))), 5)}` dias em torno da fase zero.

A duração de trânsito usada é `{fmt(duration_days, 5)}` dias
(`{fmt(duration_days * 24.0, 5)}` horas), com meia duração aproximada de
`{fmt(core_half_width, 5)}` dias.

Dispersão fora do núcleo do trânsito, calculada apenas como diagnóstico:
`{fmt(out_std, 6)}` unidades de fluxo.

Figuras:

{figure_text}

Visualizações principais da janela de trânsito:

![Janela de trânsito atual](../figures/gold_eda/hat_p_7_b/04_transit_window_lightcurve.png)

![Janela de trânsito com binning visual](../figures/gold_eda/hat_p_7_b/05_transit_window_binned.png)

## 7. Diagnóstico sobre a largura da janela atual

Resposta objetiva: **a janela atual de ±0.48527 dias parece excessivamente larga?**

**{current_window_is_wide}.** Ela é útil para inspeção ampla, mas inclui muito
baseline fora do trânsito em comparação com a duração do evento. Para uma
primeira modelagem bayesiana, uma janela mais estreita tende a reduzir
estrutura de longo prazo e manter o foco no evento de trânsito.

Comparação de janelas:

{markdown_table(window_comparison, [
        "window_half_width_days",
        "row_count",
        "flux_median",
        "flux_std",
        "approximate_depth_visual",
        "in_transit_count",
        "out_of_transit_count",
        "notes",
    ])}

Tabela derivada:

- `{relative_path(paths.tables_dir / "window_comparison_summary.csv", paths.project_root)}`

![Comparação de larguras de janela](../figures/gold_eda/hat_p_7_b/08_window_width_comparison.png)

## 8. Sugestão preliminar de janela para modelagem

Resposta objetiva: **há dados suficientes em uma janela mais estreita?**

Sim. A comparação indica que existem pontos suficientes em janelas menores que
a Gold atual. Como critério preliminar, a janela recomendada para o primeiro
teste de modelagem é:

**±{fmt(recommended_window, 3)} dias em torno da fase zero.**

Essa recomendação mantém o trânsito e uma região curta de baseline local. Ela
deve ser reavaliada junto com resíduos, normalização local e comportamento da
likelihood no modelo bayesiano.

## 9. Limitações

- A profundidade visual é uma aproximação por contraste de medianas, não uma
  estimativa física nem inferencial.
- Nenhuma normalização adicional foi aplicada nesta EDA.
- Nenhum outlier foi removido nesta etapa.
- A análise usa a curva Gold já filtrada por qualidade para fase e janela.
- A escala temporal já foi tratada na Gold; esta etapa apenas diagnostica o
  resultado preparado.
- O diagnóstico visual não substitui validação posterior do modelo e dos
  resíduos.

Warnings:

{warning_text}

## 10. Próximos passos

Resposta objetiva: **há `flux_err` utilizável para likelihood gaussiana?**

**{flux_err_available}.** A coluna `flux_err` está presente na janela Gold e
tem mediana `{fmt(row.get("flux_err_median"))}`. Ela é numericamente utilizável
para uma likelihood gaussiana preliminar, desde que a próxima etapa avalie a
escala do ruído e a adequação dos resíduos.

Resposta objetiva: **a Gold parece pronta para um modelo bayesiano preliminar?**

Sim, com cautela. A Gold está pronta para um modelo preliminar simples, desde
que a modelagem documente a escolha de janela, trate normalização local de forma
explícita e não interprete esta EDA como resultado inferencial.

Resposta objetiva: **qual arquivo deve ser usado na próxima etapa?**

Use como entrada principal:

`data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv`

Para o primeiro modelo, aplicar no script de modelagem um filtro preliminar:

```python
abs(phase) <= {fmt(recommended_window, 3)}
```

O arquivo Gold não foi alterado nesta EDA.
"""
    paths.report_path.write_text(content, encoding="utf-8")


def validate_inputs(data: dict[str, pd.DataFrame], warnings: list[str]) -> None:
    require_columns(
        data["primary"],
        ["planet_name", "mission", "time", "flux", "flux_err", "quality"],
        "primary_lightcurve.csv",
        warnings,
    )
    require_columns(
        data["quality_filtered"],
        ["time", "flux", "flux_err", "quality"],
        "primary_lightcurve_quality_filtered.csv",
        warnings,
    )
    require_columns(
        data["phase_folded"],
        ["time", "phase", "flux", "flux_err", "quality"],
        "phase_folded_lightcurve.csv",
        warnings,
    )
    require_columns(
        data["transit_window"],
        ["time", "phase", "flux", "flux_err", "quality"],
        "transit_window_lightcurve.csv",
        warnings,
    )


def run_analysis(
    project_root: Path | None = None,
    bins: int = DEFAULT_BINS,
) -> dict[str, Any]:
    paths = build_paths(project_root)
    ensure_output_directories(paths)

    warnings: list[str] = []
    data = load_gold_inputs(paths)
    validate_inputs(data, warnings)

    duration_days = transit_duration_days(
        data["reference"],
        data["transit_window"],
    )
    window_comparison = build_window_comparison(
        data["phase_folded"],
        duration_days,
    )
    recommended_window = choose_recommended_window(
        window_comparison,
        duration_days,
    )
    summary = build_eda_summary(data, duration_days, recommended_window)
    binned = build_binned_phase_statistics(data["transit_window"], bins=bins)

    summary_path = paths.tables_dir / "gold_eda_summary.csv"
    window_path = paths.tables_dir / "window_comparison_summary.csv"
    binned_path = paths.tables_dir / "transit_window_binned_summary.csv"
    save_dataframe(summary, summary_path)
    save_dataframe(window_comparison, window_path)
    save_dataframe(binned, binned_path)

    figures = save_all_figures(data, binned, window_comparison, paths)
    write_report(data, summary, window_comparison, figures, paths, warnings)

    return {
        "summary_path": relative_path(summary_path, paths.project_root),
        "window_comparison_path": relative_path(window_path, paths.project_root),
        "binned_summary_path": relative_path(binned_path, paths.project_root),
        "report_path": relative_path(paths.report_path, paths.project_root),
        "figures": [relative_path(path, paths.project_root) for path in figures],
        "summary": summary.iloc[0].to_dict(),
        "window_comparison": window_comparison.to_dict(orient="records"),
        "warnings": warnings,
    }


def main() -> None:
    results = run_analysis()
    summary = results["summary"]
    print("GOLD EDA completed for HAT-P-7 b.")
    print(f"Report: {results['report_path']}")
    print(f"Summary table: {results['summary_path']}")
    print(f"Window comparison: {results['window_comparison_path']}")
    print(f"Figures: {len(results['figures'])}")
    print(f"Rows in transit window: {int(summary['rows_transit_window'])}")
    print(
        "Recommended modeling half-window: "
        f"±{float(summary['recommended_window_half_width_days']):.3f} days"
    )
    if results["warnings"]:
        print("Warnings:")
        for item in results["warnings"]:
            print(f"- {item}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
