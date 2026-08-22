"""Prepare initial GOLD catalog and light-curve datasets."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .manifests import GoldManifest
from .utils import (
    atomic_write_dataframe,
    atomic_write_json,
    atomic_write_text,
    read_csv,
    relative_path,
    scalar_to_float,
    to_number,
    utc_now,
)


REFERENCE_COLUMNS = (
    "planet_name",
    "host_star",
    "planet_slug",
    "orbital_period_days",
    "transit_midpoint",
    "transit_duration_hours",
    "transit_depth",
    "planet_radius_earth",
    "planet_radius_jupiter",
    "stellar_radius_solar",
    "stellar_mass_solar",
    "stellar_teff",
    "system_distance_pc",
    "source_raw_path",
    "silver_source_path",
    "gold_created_at_utc",
)

PRIMARY_COLUMNS = (
    "planet_name",
    "host_star",
    "planet_slug",
    "mission",
    "time",
    "flux",
    "flux_err",
    "flux_source",
    "quality",
    "quality_is_zero",
    "cadence_number",
    "source_silver_path",
    "source_raw_path",
    "source_fits_file",
    "gold_created_at_utc",
)

PHASE_COLUMNS = (
    "planet_name",
    "host_star",
    "planet_slug",
    "mission",
    "time",
    "phase",
    "flux",
    "flux_err",
    "quality",
    "flux_source",
    "orbital_period_days",
    "transit_midpoint_used",
    "phase_formula",
    "source_gold_lightcurve",
    "gold_created_at_utc",
)


def build_gold_target_datasets(
    *,
    config: Any,
    selected: dict[str, Any],
    manifest: GoldManifest,
    logger: logging.Logger,
) -> dict[str, Any]:
    """Build all target-specific GOLD datasets."""

    slug = selected["selected_planet_slug"]
    logger.info("Building GOLD target datasets for %s", slug)
    reference = build_reference_parameters(
        config=config,
        selected=selected,
        manifest=manifest,
        logger=logger,
    )
    primary_result = build_primary_lightcurve(
        config=config,
        selected=selected,
        manifest=manifest,
        logger=logger,
    )
    quality_result = build_quality_filtered_lightcurve(
        config=config,
        selected=selected,
        primary_path=primary_result["path"],
        manifest=manifest,
        logger=logger,
    )
    phase_result = build_phase_folded_lightcurve(
        config=config,
        selected=selected,
        reference=reference,
        source_lightcurve_path=quality_result["path"],
        manifest=manifest,
        logger=logger,
    )
    window_result = build_transit_window_lightcurve(
        config=config,
        selected=selected,
        reference=reference,
        phase_result=phase_result,
        manifest=manifest,
        logger=logger,
    )
    return {
        "reference": reference,
        "primary": primary_result,
        "quality_filtered": quality_result,
        "phase": phase_result,
        "transit_window": window_result,
    }


def build_reference_parameters(
    *,
    config: Any,
    selected: dict[str, Any],
    manifest: GoldManifest,
    logger: logging.Logger,
) -> pd.DataFrame:
    source_path = config.SILVER_PATHS["nasa_pscomppars"]
    nasa = read_csv(source_path)
    slug = selected["selected_planet_slug"]
    row = nasa[nasa["planet_slug"] == slug].copy()
    if row.empty:
        raise ValueError(f"No NASA pscomppars row found for selected target: {slug}")

    row = row.head(1)
    row["silver_source_path"] = relative_path(source_path, config.PROJECT_ROOT)
    row["gold_created_at_utc"] = utc_now()
    reference = row.reindex(columns=REFERENCE_COLUMNS)

    output_csv = config.GOLD_DATA_DIR / slug / "catalogs" / "reference_parameters.csv"
    output_json = config.GOLD_DATA_DIR / slug / "catalogs" / "reference_parameters.json"
    atomic_write_dataframe(output_csv, reference)
    atomic_write_json(output_json, reference.iloc[0].to_dict())
    source_raw_path = str(reference.iloc[0].get("source_raw_path", ""))
    manifest.add_artifact(
        path=output_csv,
        transformation_type="gold_reference_parameters_csv",
        planet_name=selected["selected_planet_name"],
        host_star=selected["selected_host_star"],
        planet_slug=slug,
        source_silver_path=relative_path(source_path, config.PROJECT_ROOT),
        source_raw_path=source_raw_path,
        row_count=len(reference),
        column_count=len(reference.columns),
        notes="Selected target reference parameters from SILVER NASA pscomppars.",
    )
    manifest.add_artifact(
        path=output_json,
        transformation_type="gold_reference_parameters_json",
        planet_name=selected["selected_planet_name"],
        host_star=selected["selected_host_star"],
        planet_slug=slug,
        source_silver_path=relative_path(source_path, config.PROJECT_ROOT),
        source_raw_path=source_raw_path,
        row_count=1,
        column_count=len(reference.columns),
        notes="JSON sidecar for selected target reference parameters.",
    )
    logger.info("GOLD reference parameters written for %s", slug)
    return reference


def build_primary_lightcurve(
    *,
    config: Any,
    selected: dict[str, Any],
    manifest: GoldManifest,
    logger: logging.Logger,
) -> dict[str, Any]:
    slug = selected["selected_planet_slug"]
    mission = selected["selected_primary_mission"]
    mission_slug = mission.lower()
    source_path = config.SILVER_DATA_DIR / "lightcurves" / "mast" / slug / f"{mission_slug}_lightcurve.csv"
    silver = read_csv(source_path)

    flux_column, flux_err_column = _choose_flux_columns(config, selected, silver)
    selected_flux = to_number(silver[flux_column])
    selected_flux_err = to_number(silver[flux_err_column]) if flux_err_column in silver.columns else pd.Series(np.nan, index=silver.index)
    time = to_number(silver["time"])
    before = len(silver)
    keep = time.notna() & selected_flux.notna()
    prepared = pd.DataFrame(
        {
            "planet_name": silver.get("planet_name", ""),
            "host_star": silver.get("host_star", ""),
            "planet_slug": silver.get("planet_slug", ""),
            "mission": silver.get("mission", mission),
            "time": time,
            "flux": selected_flux,
            "flux_err": selected_flux_err,
            "flux_source": flux_column,
            "quality": to_number(silver.get("quality", pd.Series(np.nan, index=silver.index))),
            "quality_is_zero": silver.get("quality_is_zero", "").astype(str).str.lower().isin({"true", "1"}),
            "cadence_number": silver.get("cadence_number", ""),
            "source_silver_path": relative_path(source_path, config.PROJECT_ROOT),
            "source_raw_path": silver.get("source_raw_path", ""),
            "source_fits_file": silver.get("source_fits_file", ""),
            "gold_created_at_utc": utc_now(),
        }
    )
    prepared = prepared[keep].copy()
    if config.MAX_POINTS_PER_DATASET:
        prepared = prepared.head(config.MAX_POINTS_PER_DATASET)
    prepared = prepared.reindex(columns=PRIMARY_COLUMNS)

    output_path = config.GOLD_DATA_DIR / slug / "lightcurves" / "primary_lightcurve.csv"
    atomic_write_dataframe(output_path, prepared)
    removed = before - len(prepared)
    manifest.add_artifact(
        path=output_path,
        transformation_type="gold_primary_lightcurve",
        planet_name=selected["selected_planet_name"],
        host_star=selected["selected_host_star"],
        planet_slug=slug,
        source_silver_path=relative_path(source_path, config.PROJECT_ROOT),
        source_raw_path="|".join(sorted(set(prepared["source_raw_path"].astype(str)))),
        row_count=len(prepared),
        column_count=len(prepared.columns),
        notes=f"Selected {flux_column}; removed {removed} rows with missing time or flux.",
    )
    logger.info(
        "Primary GOLD lightcurve written: slug=%s mission=%s rows=%s removed_missing=%s flux=%s",
        slug,
        mission,
        len(prepared),
        removed,
        flux_column,
    )
    return {
        "path": output_path,
        "rows": len(prepared),
        "removed_missing_time_or_flux": removed,
        "flux_column": flux_column,
        "flux_err_column": flux_err_column,
    }


def _choose_flux_columns(config: Any, selected: dict[str, Any], silver: pd.DataFrame) -> tuple[str, str]:
    preferred = config.PREFERRED_FLUX_COLUMN
    preferred_err = config.PREFERRED_FLUX_ERR_COLUMN
    fallback = config.FALLBACK_FLUX_COLUMN
    fallback_err = config.FALLBACK_FLUX_ERR_COLUMN
    if preferred in silver.columns and to_number(silver[preferred]).notna().any():
        return preferred, preferred_err
    if fallback in silver.columns and to_number(silver[fallback]).notna().any():
        return fallback, fallback_err
    raise ValueError(f"No usable flux column found for {selected['selected_planet_slug']}")


def build_quality_filtered_lightcurve(
    *,
    config: Any,
    selected: dict[str, Any],
    primary_path: Path,
    manifest: GoldManifest,
    logger: logging.Logger,
) -> dict[str, Any]:
    slug = selected["selected_planet_slug"]
    primary = read_csv(primary_path)
    quality = to_number(primary["quality"])
    before = len(primary)
    if quality.notna().any():
        filtered = primary[quality == config.QUALITY_GOOD_VALUE].copy()
        note = f"Kept rows with quality == {config.QUALITY_GOOD_VALUE}."
    else:
        filtered = primary.copy()
        note = "Quality is missing; filter not applied."
    after = len(filtered)
    output_path = config.GOLD_DATA_DIR / slug / "lightcurves" / "primary_lightcurve_quality_filtered.csv"
    atomic_write_dataframe(output_path, filtered.reindex(columns=PRIMARY_COLUMNS))
    manifest.add_artifact(
        path=output_path,
        transformation_type="gold_primary_lightcurve_quality_filtered",
        planet_name=selected["selected_planet_name"],
        host_star=selected["selected_host_star"],
        planet_slug=slug,
        source_silver_path=relative_path(primary_path, config.PROJECT_ROOT),
        source_raw_path="|".join(sorted(set(filtered["source_raw_path"].astype(str)))),
        row_count=after,
        column_count=len(PRIMARY_COLUMNS),
        notes=f"{note} rows_before={before}; rows_after={after}; removed={before - after}.",
    )
    logger.info("Quality-filtered GOLD lightcurve written: rows_before=%s rows_after=%s", before, after)
    return {
        "path": output_path,
        "rows_before": before,
        "rows_after": after,
        "removed": before - after,
        "quality_counts": quality.value_counts(dropna=False).to_dict(),
    }


def build_phase_folded_lightcurve(
    *,
    config: Any,
    selected: dict[str, Any],
    reference: pd.DataFrame,
    source_lightcurve_path: Path,
    manifest: GoldManifest,
    logger: logging.Logger,
) -> dict[str, Any]:
    slug = selected["selected_planet_slug"]
    lightcurve = read_csv(source_lightcurve_path)
    period = scalar_to_float(reference.iloc[0].get("orbital_period_days"))
    transit_midpoint = scalar_to_float(reference.iloc[0].get("transit_midpoint"))
    if period is None or transit_midpoint is None:
        return _write_phase_warning(
            config,
            selected,
            manifest,
            "Missing orbital_period_days or transit_midpoint; phase folding was not created.",
        )

    t0_result = _transit_midpoint_in_lightcurve_scale(config, selected, transit_midpoint)
    if not t0_result["compatible"]:
        return _write_phase_warning(config, selected, manifest, t0_result["warning"])

    time = to_number(lightcurve["time"])
    phase = ((time - t0_result["transit_midpoint_used"] + 0.5 * period) % period) - 0.5 * period
    phase_folded = pd.DataFrame(
        {
            "planet_name": lightcurve["planet_name"],
            "host_star": lightcurve["host_star"],
            "planet_slug": lightcurve["planet_slug"],
            "mission": lightcurve["mission"],
            "time": time,
            "phase": phase,
            "flux": to_number(lightcurve["flux"]),
            "flux_err": to_number(lightcurve["flux_err"]),
            "quality": to_number(lightcurve["quality"]),
            "flux_source": lightcurve["flux_source"],
            "orbital_period_days": period,
            "transit_midpoint_used": t0_result["transit_midpoint_used"],
            "phase_formula": "((time - transit_midpoint_used + 0.5 * period) % period) - 0.5 * period",
            "source_gold_lightcurve": relative_path(source_lightcurve_path, config.PROJECT_ROOT),
            "gold_created_at_utc": utc_now(),
        }
    ).reindex(columns=PHASE_COLUMNS)

    output_path = config.GOLD_DATA_DIR / slug / "modeling" / "phase_folded_lightcurve.csv"
    atomic_write_dataframe(output_path, phase_folded)
    manifest.add_artifact(
        path=output_path,
        transformation_type="gold_phase_folded_lightcurve",
        planet_name=selected["selected_planet_name"],
        host_star=selected["selected_host_star"],
        planet_slug=slug,
        source_silver_path=relative_path(source_lightcurve_path, config.PROJECT_ROOT),
        source_raw_path="",
        row_count=len(phase_folded),
        column_count=len(phase_folded.columns),
        notes=t0_result["warning"],
    )
    logger.info("Phase-folded GOLD lightcurve written: rows=%s", len(phase_folded))
    return {
        "path": output_path,
        "created": True,
        "rows": len(phase_folded),
        "period_used": period,
        "transit_midpoint_used": t0_result["transit_midpoint_used"],
        "warning": t0_result["warning"],
    }


def _transit_midpoint_in_lightcurve_scale(
    config: Any,
    selected: dict[str, Any],
    transit_midpoint: float,
) -> dict[str, Any]:
    slug = selected["selected_planet_slug"]
    mission = selected["selected_primary_mission"].lower()
    metadata = read_csv(config.SILVER_PATHS["mast_fits_metadata"])
    rows = metadata[
        (metadata["planet_slug"] == slug)
        & (metadata["mission"].astype(str).str.lower() == mission)
    ]
    if rows.empty:
        return {
            "compatible": False,
            "transit_midpoint_used": None,
            "warning": "No FITS metadata found for selected planet and mission.",
        }
    refs = [value for value in rows["time_reference"].astype(str).unique() if value]
    bjd_reference = _parse_bjd_reference(refs[0] if refs else "")
    time_values_min = to_number(rows["time_min"])
    time_values_max = to_number(rows["time_max"])
    time_min = float(time_values_min.min()) if time_values_min.notna().any() else None
    time_max = float(time_values_max.max()) if time_values_max.notna().any() else None
    if bjd_reference is None:
        return {
            "compatible": False,
            "transit_midpoint_used": None,
            "warning": "Could not parse BJDREFI/BJDREFF from FITS time_reference; phase folding skipped.",
        }
    midpoint_in_scale = transit_midpoint - bjd_reference
    if time_min is not None and time_max is not None and not (time_min - 100000 <= midpoint_in_scale <= time_max + 100000):
        return {
            "compatible": False,
            "transit_midpoint_used": None,
            "warning": (
                "NASA transit_midpoint could not be reconciled with FITS time scale. "
                f"transit_midpoint={transit_midpoint}; BJD_reference={bjd_reference}; "
                f"converted={midpoint_in_scale}; time_range=({time_min}, {time_max})."
            ),
        }
    return {
        "compatible": True,
        "transit_midpoint_used": midpoint_in_scale,
        "warning": (
            "NASA transit_midpoint converted to FITS time scale using "
            f"BJD reference {bjd_reference} from {refs[0] if refs else 'metadata'}."
        ),
    }


def _parse_bjd_reference(reference: str) -> float | None:
    refi = re.search(r"BJDREFI=([0-9.+-]+)", reference)
    reff = re.search(r"BJDREFF=([0-9.+-]+)", reference)
    if not refi and not reff:
        return None
    refi_value = float(refi.group(1)) if refi else 0.0
    reff_value = float(reff.group(1)) if reff else 0.0
    return refi_value + reff_value


def _write_phase_warning(
    config: Any,
    selected: dict[str, Any],
    manifest: GoldManifest,
    warning: str,
) -> dict[str, Any]:
    slug = selected["selected_planet_slug"]
    path = config.GOLD_DATA_DIR / slug / "modeling" / "phase_folded_lightcurve_status.md"
    atomic_write_text(path, f"# Phase Folding Status\n\n{warning}\n")
    manifest.add_artifact(
        path=path,
        transformation_type="gold_phase_folded_lightcurve_status",
        planet_name=selected["selected_planet_name"],
        host_star=selected["selected_host_star"],
        planet_slug=slug,
        status="created",
        row_count=1,
        column_count=1,
        notes=warning,
    )
    return {"created": False, "path": path, "rows": 0, "warning": warning}


def build_transit_window_lightcurve(
    *,
    config: Any,
    selected: dict[str, Any],
    reference: pd.DataFrame,
    phase_result: dict[str, Any],
    manifest: GoldManifest,
    logger: logging.Logger,
) -> dict[str, Any]:
    slug = selected["selected_planet_slug"]
    if not phase_result.get("created"):
        path = config.GOLD_DATA_DIR / slug / "modeling" / "transit_window_lightcurve_status.md"
        warning = "Transit window was not created because phase-folded lightcurve is unavailable."
        atomic_write_text(path, f"# Transit Window Status\n\n{warning}\n")
        manifest.add_artifact(
            path=path,
            transformation_type="gold_transit_window_status",
            planet_name=selected["selected_planet_name"],
            host_star=selected["selected_host_star"],
            planet_slug=slug,
            row_count=1,
            column_count=1,
            notes=warning,
        )
        return {"created": False, "path": path, "rows": 0, "warning": warning}

    phase = read_csv(phase_result["path"])
    duration_hours = scalar_to_float(reference.iloc[0].get("transit_duration_hours"))
    if duration_hours is None:
        half_width = config.TRANSIT_WINDOW_MIN_HALF_WIDTH_DAYS
    else:
        half_width = max(
            config.TRANSIT_WINDOW_DURATION_MULTIPLIER * duration_hours / 24.0,
            config.TRANSIT_WINDOW_MIN_HALF_WIDTH_DAYS,
        )
    phase_numeric = to_number(phase["phase"])
    window = phase[phase_numeric.abs() <= half_width].copy()
    window["in_transit_window"] = True
    window["transit_window_half_width_days"] = half_width
    window["transit_duration_hours_used"] = duration_hours if duration_hours is not None else ""

    output_path = config.GOLD_DATA_DIR / slug / "modeling" / "transit_window_lightcurve.csv"
    atomic_write_dataframe(output_path, window)
    manifest.add_artifact(
        path=output_path,
        transformation_type="gold_transit_window_lightcurve",
        planet_name=selected["selected_planet_name"],
        host_star=selected["selected_host_star"],
        planet_slug=slug,
        source_silver_path=relative_path(phase_result["path"], config.PROJECT_ROOT),
        source_raw_path="",
        row_count=len(window),
        column_count=len(window.columns),
        notes=(
            f"Selected abs(phase) <= {half_width}; "
            f"duration_hours={duration_hours}; multiplier={config.TRANSIT_WINDOW_DURATION_MULTIPLIER}."
        ),
    )
    logger.info("Transit-window GOLD lightcurve written: rows=%s half_width=%s", len(window), half_width)
    return {
        "created": True,
        "path": output_path,
        "rows": len(window),
        "half_width_days": half_width,
        "duration_hours_used": duration_hours,
    }
