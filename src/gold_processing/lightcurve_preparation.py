"""Prepare initial GOLD catalog and light-curve datasets."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from project_config import get_target

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
    "transit_midpoint_bjd",
    "transit_duration_hours",
    "transit_depth_percent",
    "transit_depth_fraction",
    "planet_radius_earth",
    "planet_radius_jupiter",
    "stellar_radius_solar",
    "stellar_mass_solar",
    "stellar_teff_kelvin",
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
    "quarter",
    "sector",
    "campaign",
    "cadence_type",
    "exposure_time_seconds",
    "exposure_time_source",
    "source_silver_path",
    "source_raw_path",
    "source_raw_sha256",
    "source_fits_file",
    "source_fits_sha256",
    "segment_id",
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
    "segment_id",
    "quarter",
    "sector",
    "campaign",
    "cadence_type",
    "exposure_time_seconds",
    "exposure_time_source",
    "source_raw_path",
    "source_raw_sha256",
    "source_fits_file",
    "source_fits_sha256",
    "orbital_period_days",
    "transit_midpoint_used",
    "phase_formula",
    "source_gold_lightcurve",
    "gold_created_at_utc",
)

DATASET_VOLATILE_COLUMNS = frozenset(
    {"dataset_id", "dataset_schema_version", "gold_created_at_utc"}
)
DATASET_SIGNATURE_NUMERIC_COLUMNS = frozenset(
    {
        "phase",
        "flux",
        "flux_err",
        "exposure_time_seconds",
        "raw_flux",
        "raw_flux_err",
        "segment_baseline_flux",
    }
)


def read_normalized_signature_frame(path: Path) -> pd.DataFrame:
    """Reload persisted Gold with the dtypes used to create its content hash."""

    frame = pd.read_csv(
        path,
        dtype=str,
        low_memory=False,
        float_precision="round_trip",
    ).fillna("")
    for column in sorted(DATASET_SIGNATURE_NUMERIC_COLUMNS.intersection(frame.columns)):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    reconstruction_columns = {
        "flux",
        "flux_err",
        "raw_flux",
        "raw_flux_err",
        "segment_baseline_flux",
    }
    if reconstruction_columns.issubset(frame.columns):
        baseline = frame["segment_baseline_flux"].abs()
        frame["flux"] = frame["raw_flux"] / baseline
        frame["flux_err"] = frame["raw_flux_err"] / baseline
    return frame


def normalized_content_sha256(frame: pd.DataFrame) -> str:
    """Hash normalized scientific content while excluding volatile run metadata."""

    columns = sorted(set(frame.columns).difference(DATASET_VOLATILE_COLUMNS))
    if not columns:
        raise ValueError("Cannot identify a Gold dataset from an empty column set.")
    canonical = frame.loc[:, columns].copy()
    sort_columns = [
        column for column in ("segment_id", "time", "cadence_number") if column in columns
    ]
    if sort_columns:
        canonical = canonical.sort_values(
            sort_columns,
            kind="mergesort",
            na_position="last",
        )
    serialized = canonical.to_csv(
        index=False,
        lineterminator="\n",
        na_rep="",
        float_format="%.17g",
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def build_gold_dataset_signature(
    *,
    normalized: pd.DataFrame,
    diagnostics: pd.DataFrame,
    schema_version: str,
    planet_slug: str,
    orbital_period_days: float | None,
    normalization_method: str,
    transit_exclusion_half_width_days: float,
) -> dict[str, Any]:
    """Return a content-bound signature for a segment-normalized Gold dataset."""

    required = {
        "segment_id",
        "source_fits_file",
        "source_fits_sha256",
        "row_count",
        "exposure_time_seconds",
    }
    missing = sorted(required.difference(diagnostics.columns))
    if missing:
        raise ValueError(f"Dataset signature is missing diagnostic columns: {missing}")
    segments: list[dict[str, Any]] = []
    for row in diagnostics.sort_values("segment_id").to_dict(orient="records"):
        checksum = str(row["source_fits_sha256"]).strip().lower()
        if re.fullmatch(r"[0-9a-f]{64}", checksum) is None:
            raise ValueError(
                f"Segment {row['segment_id']!r} has invalid source_fits_sha256."
            )
        segments.append(
            {
                "segment_id": str(row["segment_id"]),
                "source_fits_file": str(row["source_fits_file"]),
                "source_fits_sha256": checksum,
                "rows": int(row["row_count"]),
                "exposure_time_seconds": float(row["exposure_time_seconds"]),
            }
        )
    return {
        "schema_version": schema_version,
        "planet_slug": planet_slug,
        "orbital_period_days": orbital_period_days,
        "method": normalization_method,
        "transit_exclusion_half_width_days": transit_exclusion_half_width_days,
        "normalized_content_sha256": normalized_content_sha256(normalized),
        "segments": segments,
    }


def dataset_id_from_signature(planet_slug: str, signature: dict[str, Any]) -> str:
    serialized = json.dumps(
        signature,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"{planet_slug}-{hashlib.sha256(serialized).hexdigest()[:16]}"


def construct_centered_phase(
    time: pd.Series,
    *,
    orbital_period_days: float,
    transit_midpoint_in_time_scale: float,
) -> pd.Series:
    """Return phase in days centered on transit, with explicit units."""

    if not np.isfinite(orbital_period_days) or orbital_period_days <= 0:
        raise ValueError("orbital_period_days must be positive and finite")
    numeric_time = to_number(time)
    return (
        (numeric_time - transit_midpoint_in_time_scale + 0.5 * orbital_period_days)
        % orbital_period_days
    ) - 0.5 * orbital_period_days


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
    normalization_result = build_segment_normalized_lightcurve(
        config=config,
        selected=selected,
        reference=reference,
        phase_result=phase_result,
        manifest=manifest,
        logger=logger,
    )
    window_result = build_transit_window_lightcurve(
        config=config,
        selected=selected,
        reference=reference,
        phase_result=normalization_result,
        manifest=manifest,
        logger=logger,
    )
    return {
        "reference": reference,
        "primary": primary_result,
        "quality_filtered": quality_result,
        "phase": phase_result,
        "segment_normalization": normalization_result,
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
    target = get_target(slug)
    row["planet_name"] = target.planet_name
    row["host_star"] = target.host_star
    row["orbital_period_days"] = target.orbital_period_days
    row["transit_midpoint_bjd"] = target.transit_midpoint_bjd
    row["transit_duration_hours"] = target.transit_duration_hours
    row["transit_depth_percent"] = target.transit_depth_percent
    row["transit_depth_fraction"] = target.transit_depth_fraction
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
    cadence_preference = get_target(slug).cadence_preference
    if cadence_preference != "any":
        cadence_values = silver.get(
            "cadence_type", pd.Series("unknown", index=silver.index)
        ).astype(str)
        if not cadence_values.eq(cadence_preference).any():
            raise ValueError(
                f"No {cadence_preference!r}-cadence Silver rows are available for {slug}; "
                "Gold refuses to silently substitute another cadence."
            )
        keep &= cadence_values.eq(cadence_preference)
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
            "quarter": silver.get("quarter", ""),
            "sector": silver.get("sector", ""),
            "campaign": silver.get("campaign", ""),
            "cadence_type": silver.get("cadence_type", "unknown"),
            "exposure_time_seconds": to_number(
                silver.get("exposure_time_seconds", pd.Series(np.nan, index=silver.index))
            ),
            "exposure_time_source": silver.get("exposure_time_source", "unavailable"),
            "source_silver_path": relative_path(source_path, config.PROJECT_ROOT),
            "source_raw_path": silver.get("source_raw_path", ""),
            "source_raw_sha256": silver.get("source_raw_sha256", ""),
            "source_fits_file": silver.get("source_fits_file", ""),
            "source_fits_sha256": silver.get("source_raw_sha256", ""),
            "gold_created_at_utc": utc_now(),
        }
    )
    prepared["segment_id"] = (
        prepared["mission"].astype(str).str.lower()
        + ":"
        + prepared["source_fits_file"].astype(str)
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
        notes=(
            f"Selected {flux_column}; cadence_preference={cadence_preference}; "
            f"removed {removed} rows by missing-value/cadence policy."
        ),
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
        "cadence_preference": cadence_preference,
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
    transit_midpoint = scalar_to_float(reference.iloc[0].get("transit_midpoint_bjd"))
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
    phase = construct_centered_phase(
        time,
        orbital_period_days=period,
        transit_midpoint_in_time_scale=t0_result["transit_midpoint_used"],
    )
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
            "segment_id": lightcurve["segment_id"],
            "quarter": lightcurve["quarter"],
            "sector": lightcurve["sector"],
            "campaign": lightcurve["campaign"],
            "cadence_type": lightcurve["cadence_type"],
            "exposure_time_seconds": to_number(lightcurve["exposure_time_seconds"]),
            "exposure_time_source": lightcurve["exposure_time_source"],
            "source_raw_path": lightcurve["source_raw_path"],
            "source_raw_sha256": lightcurve["source_raw_sha256"],
            "source_fits_file": lightcurve["source_fits_file"],
            "source_fits_sha256": lightcurve["source_fits_sha256"],
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


def normalize_segments_dataframe(
    phase: pd.DataFrame,
    *,
    transit_exclusion_half_width_days: float,
    min_baseline_points: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Normalize each traceable FITS segment by its out-of-transit median."""

    required = {
        "segment_id",
        "source_fits_file",
        "source_fits_sha256",
        "phase",
        "flux",
        "flux_err",
        "exposure_time_seconds",
    }
    missing = sorted(required.difference(phase.columns))
    if missing:
        raise ValueError(f"Segment normalization is missing required columns: {missing}")
    working = phase.copy()
    working["phase"] = to_number(working["phase"])
    working["flux"] = to_number(working["flux"])
    working["flux_err"] = to_number(working["flux_err"])
    working["exposure_time_seconds"] = to_number(working["exposure_time_seconds"])
    if working["segment_id"].fillna("").astype(str).str.strip().eq("").any():
        raise ValueError("Every Gold row must retain a non-empty segment_id.")
    if (
        working["exposure_time_seconds"].isna()
        | (working["exposure_time_seconds"] <= 0)
    ).any():
        raise ValueError("Every Gold row must have positive exposure_time_seconds.")

    normalized_parts: list[pd.DataFrame] = []
    diagnostic_rows: list[dict[str, Any]] = []
    for segment_id, segment in working.groupby("segment_id", sort=True, dropna=False):
        segment = segment.copy()
        source_hashes = {
            str(value).strip().lower()
            for value in segment["source_fits_sha256"].dropna()
            if str(value).strip()
        }
        if len(source_hashes) != 1 or re.fullmatch(
            r"[0-9a-f]{64}", next(iter(source_hashes), "")
        ) is None:
            raise ValueError(
                f"Segment {segment_id!r} must retain exactly one valid FITS SHA-256."
            )
        source_fits_sha256 = next(iter(source_hashes))
        valid = segment["phase"].notna() & segment["flux"].notna()
        baseline_mask = valid & (
            segment["phase"].abs() >= transit_exclusion_half_width_days
        )
        baseline_count = int(baseline_mask.sum())
        if baseline_count < min_baseline_points:
            raise ValueError(
                f"Segment {segment_id!r} has {baseline_count} out-of-transit points; "
                f"at least {min_baseline_points} are required."
            )
        baseline = float(segment.loc[baseline_mask, "flux"].median())
        if not np.isfinite(baseline) or baseline <= 0:
            raise ValueError(f"Segment {segment_id!r} has invalid baseline median {baseline!r}.")
        raw_flux = segment["flux"].copy()
        raw_flux_err = segment["flux_err"].copy()
        segment["raw_flux"] = raw_flux
        segment["raw_flux_err"] = raw_flux_err
        segment["flux"] = raw_flux / baseline
        segment["flux_err"] = raw_flux_err / abs(baseline)
        segment["segment_baseline_flux"] = baseline
        segment["segment_normalization_method"] = "out_of_transit_median"
        segment["preprocessing_status"] = "segment_normalized"
        normalized_parts.append(segment)
        diagnostic_rows.append(
            {
                "segment_id": str(segment_id),
                "source_fits_file": str(segment["source_fits_file"].iloc[0]),
                "source_fits_sha256": source_fits_sha256,
                "quarter": segment.get("quarter", pd.Series([""])).iloc[0],
                "sector": segment.get("sector", pd.Series([""])).iloc[0],
                "campaign": segment.get("campaign", pd.Series([""])).iloc[0],
                "cadence_type": str(segment.get("cadence_type", pd.Series(["unknown"])).iloc[0]),
                "exposure_time_seconds": float(segment["exposure_time_seconds"].median()),
                "row_count": len(segment),
                "baseline_point_count": baseline_count,
                "transit_exclusion_half_width_days": transit_exclusion_half_width_days,
                "raw_flux_median": float(raw_flux.median()),
                "baseline_flux_median": baseline,
                "normalized_flux_median": float(segment["flux"].median()),
                "normalized_baseline_median": float(segment.loc[baseline_mask, "flux"].median()),
            }
        )
    normalized = pd.concat(normalized_parts, ignore_index=True)
    diagnostics = pd.DataFrame(diagnostic_rows).sort_values("segment_id").reset_index(drop=True)
    return normalized, diagnostics


def build_segment_normalized_lightcurve(
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
        return phase_result
    phase = read_csv(phase_result["path"])
    duration_hours = scalar_to_float(reference.iloc[0].get("transit_duration_hours"))
    if duration_hours is None:
        raise ValueError("Segment normalization requires transit_duration_hours.")
    exclusion_half_width = (
        duration_hours
        / 24.0
        * float(config.SEGMENT_BASELINE_DURATION_MULTIPLIER)
        / 2.0
    )
    normalized, diagnostics = normalize_segments_dataframe(
        phase,
        transit_exclusion_half_width_days=exclusion_half_width,
        min_baseline_points=int(config.SEGMENT_MIN_BASELINE_POINTS),
    )
    signature = build_gold_dataset_signature(
        normalized=normalized,
        diagnostics=diagnostics,
        schema_version=config.DATASET_SCHEMA_VERSION,
        planet_slug=slug,
        orbital_period_days=scalar_to_float(
            reference.iloc[0].get("orbital_period_days")
        ),
        normalization_method=config.SEGMENT_NORMALIZATION_METHOD,
        transit_exclusion_half_width_days=exclusion_half_width,
    )
    dataset_id = dataset_id_from_signature(slug, signature)
    normalized["dataset_id"] = dataset_id
    normalized["dataset_schema_version"] = config.DATASET_SCHEMA_VERSION
    diagnostics["dataset_id"] = dataset_id
    diagnostics["dataset_schema_version"] = config.DATASET_SCHEMA_VERSION

    model_dir = config.GOLD_DATA_DIR / slug / "modeling"
    output_path = model_dir / "segment_normalized_lightcurve.csv"
    diagnostics_path = model_dir / "segment_normalization_diagnostics.csv"
    metadata_path = model_dir / "dataset_metadata.json"
    atomic_write_dataframe(output_path, normalized)
    atomic_write_dataframe(diagnostics_path, diagnostics)
    metadata_payload = {
        **signature,
        "dataset_id": dataset_id,
        "preprocessing_status": "segment_normalized",
        "normalization_policy": config.NORMALIZATION_POLICY,
        "row_count": len(normalized),
        "segment_count": len(diagnostics),
        "created_at_utc": utc_now(),
    }
    atomic_write_json(metadata_path, metadata_payload)
    for path, transformation_type, row_count, column_count in (
        (
            output_path,
            "gold_segment_normalized_lightcurve",
            len(normalized),
            len(normalized.columns),
        ),
        (
            diagnostics_path,
            "gold_segment_normalization_diagnostics",
            len(diagnostics),
            len(diagnostics.columns),
        ),
        (metadata_path, "gold_dataset_metadata", 1, len(metadata_payload)),
    ):
        manifest.add_artifact(
            path=path,
            transformation_type=transformation_type,
            planet_name=selected["selected_planet_name"],
            host_star=selected["selected_host_star"],
            planet_slug=slug,
            source_silver_path=relative_path(phase_result["path"], config.PROJECT_ROOT),
            source_raw_path="|".join(sorted(set(normalized["source_raw_path"].astype(str)))),
            row_count=row_count,
            column_count=column_count,
            notes=f"dataset_id={dataset_id}; {config.NORMALIZATION_POLICY}",
        )
    logger.info(
        "Segment-normalized Gold written: slug=%s dataset_id=%s rows=%s segments=%s",
        slug,
        dataset_id,
        len(normalized),
        len(diagnostics),
    )
    return {
        "created": True,
        "path": output_path,
        "diagnostics_path": diagnostics_path,
        "metadata_path": metadata_path,
        "rows": len(normalized),
        "segments": len(diagnostics),
        "dataset_id": dataset_id,
        "warning": "",
    }


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
    half_width = get_target(slug).phase_window_days
    phase_numeric = to_number(phase["phase"])
    window = phase[phase_numeric.abs() <= half_width].copy()
    window["in_transit_window"] = True
    window["transit_window_half_width_days"] = half_width
    window["transit_duration_hours_used"] = duration_hours if duration_hours is not None else ""
    window["source_segment_normalized_lightcurve"] = relative_path(
        phase_result["path"], config.PROJECT_ROOT
    )

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
            f"duration_hours={duration_hours}; configured target phase window."
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
