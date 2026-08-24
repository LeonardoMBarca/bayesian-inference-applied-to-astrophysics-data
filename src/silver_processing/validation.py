"""Validation helpers for the SILVER layer."""

from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from .manifests import SilverManifest
from .utils import (
    atomic_write_dataframe,
    atomic_write_json,
    relative_path,
    sha256_file,
    sorted_planets,
    utc_now,
)


def _existing_local_file_rows(raw_manifest: pd.DataFrame, config: Any) -> pd.DataFrame:
    if "local_path" not in raw_manifest.columns:
        return pd.DataFrame()
    rows = raw_manifest[raw_manifest["local_path"].astype(str).str.len() > 0].copy()
    if "status" in rows.columns:
        rows = rows[rows["status"].astype(str).str.lower() != "failed"]
    rows["absolute_path"] = rows["local_path"].map(lambda value: config.PROJECT_ROOT / value)
    return rows


def validate_raw_manifest(
    *,
    config: Any,
    raw_manifest: pd.DataFrame,
    manifest: SilverManifest,
    logger: logging.Logger,
) -> dict[str, Any]:
    """Validate the RAW manifest and write SILVER validation summaries."""

    logger.info("Validating RAW manifest before SILVER processing")
    created_at = utc_now()
    validation_dir = config.SILVER_DATA_DIR / "validation"
    summary_path = validation_dir / "raw_manifest_summary.csv"
    json_path = validation_dir / "raw_manifest_validation.json"

    local_rows = _existing_local_file_rows(raw_manifest, config)
    missing_paths: list[str] = []
    checksum_mismatches: list[dict[str, str]] = []
    checked_files = 0
    unique_paths = sorted(set(local_rows["local_path"].astype(str))) if not local_rows.empty else []

    for local_path in unique_paths:
        absolute_path = config.PROJECT_ROOT / local_path
        matching = local_rows[local_rows["local_path"] == local_path]
        expected_checksums = {
            str(value)
            for value in matching.get("sha256", pd.Series(dtype=str)).astype(str)
            if str(value)
        }
        if not absolute_path.exists():
            missing_paths.append(local_path)
            continue
        if expected_checksums:
            actual_checksum = sha256_file(absolute_path)
            checked_files += 1
            if actual_checksum not in expected_checksums:
                checksum_mismatches.append(
                    {
                        "local_path": local_path,
                        "expected_sha256_values": "|".join(sorted(expected_checksums)),
                        "actual_sha256": actual_checksum,
                    }
                )

    summary_rows: list[dict[str, Any]] = [
        {"summary_type": "total_records", "value": "all", "count": len(raw_manifest)},
        {
            "summary_type": "unique_local_paths",
            "value": "all",
            "count": len(unique_paths),
        },
        {
            "summary_type": "local_paths_missing",
            "value": "all",
            "count": len(missing_paths),
        },
        {
            "summary_type": "checksums_checked",
            "value": "all",
            "count": checked_files,
        },
        {
            "summary_type": "checksum_mismatches",
            "value": "all",
            "count": len(checksum_mismatches),
        },
    ]

    for column in ("source_name", "status", "product_type", "planet_name"):
        if column not in raw_manifest.columns:
            continue
        counts = raw_manifest[column].fillna("").astype(str).replace("", "(blank)").value_counts()
        summary_rows.extend(
            {
                "summary_type": f"by_{column}",
                "value": value,
                "count": int(count),
            }
            for value, count in counts.items()
        )

    summary = pd.DataFrame(summary_rows, columns=("summary_type", "value", "count"))
    atomic_write_dataframe(summary_path, summary)

    validation_payload = {
        "created_at_utc": created_at,
        "raw_manifest_path": relative_path(config.RAW_MANIFEST_PATH, config.PROJECT_ROOT),
        "raw_manifest_exists": config.RAW_MANIFEST_PATH.exists(),
        "raw_manifest_record_count": int(len(raw_manifest)),
        "unique_local_paths": int(len(unique_paths)),
        "checked_files": int(checked_files),
        "missing_local_paths_count": int(len(missing_paths)),
        "missing_local_paths": missing_paths,
        "checksum_mismatch_count": int(len(checksum_mismatches)),
        "checksum_mismatches": checksum_mismatches,
        "status_counts": raw_manifest.get("status", pd.Series(dtype=str))
        .fillna("")
        .astype(str)
        .value_counts()
        .to_dict(),
        "notes": (
            "Historical failed rows in the RAW manifest are accepted and do not "
            "stop SILVER processing."
        ),
    }
    atomic_write_json(json_path, validation_payload)

    manifest.add_artifact(
        path=summary_path,
        source_raw_path=relative_path(config.RAW_MANIFEST_PATH, config.PROJECT_ROOT),
        source_name="RAW manifest",
        transformation_type="raw_manifest_validation_summary",
        row_count=len(summary),
        column_count=len(summary.columns),
        notes="Counts by source, status, product_type, and planet_name.",
    )
    manifest.add_artifact(
        path=json_path,
        source_raw_path=relative_path(config.RAW_MANIFEST_PATH, config.PROJECT_ROOT),
        source_name="RAW manifest",
        transformation_type="raw_manifest_validation_detail",
        row_count=1,
        column_count=len(validation_payload),
        notes="Existence and checksum validation for local RAW files.",
    )
    logger.info(
        "RAW manifest validation finished: records=%s unique_files=%s missing=%s checksum_mismatches=%s",
        len(raw_manifest),
        len(unique_paths),
        len(missing_paths),
        len(checksum_mismatches),
    )
    return validation_payload


def _read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str, low_memory=False).fillna("")


def _count_rows(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return int(sum(1 for _ in path.open("r", encoding="utf-8")) - 1)
    except UnicodeDecodeError:
        return 0


def build_silver_validations(
    *,
    config: Any,
    manifest: SilverManifest,
    logger: logging.Logger,
) -> dict[str, Path]:
    """Create cross-source validation summaries for generated SILVER tables."""

    logger.info("Building SILVER validation summaries")
    validation_dir = config.SILVER_DATA_DIR / "validation"
    created_at = utc_now()

    nasa_pscomppars = _read_csv_if_exists(
        config.SILVER_DATA_DIR / "catalogs" / "nasa" / "pscomppars_selected_planets.csv"
    )
    nasa_ps = _read_csv_if_exists(
        config.SILVER_DATA_DIR / "catalogs" / "nasa" / "ps_all_solutions.csv"
    )
    mast_metadata = _read_csv_if_exists(
        config.SILVER_DATA_DIR / "lightcurves" / "mast" / "mast_fits_metadata.csv"
    )
    etd_observations = _read_csv_if_exists(config.SILVER_DATA_DIR / "etd" / "etd_observations.csv")
    etd_points = _read_csv_if_exists(config.SILVER_DATA_DIR / "etd" / "etd_lightcurve_points.csv")
    etd_metadata = _read_csv_if_exists(config.SILVER_DATA_DIR / "etd" / "etd_lightcurve_metadata.csv")

    summary_rows: list[dict[str, Any]] = []
    for planet in sorted_planets(config):
        slug = planet["planet_slug"]
        mast_rows = mast_metadata[mast_metadata.get("planet_slug", "") == slug] if not mast_metadata.empty else pd.DataFrame()
        missions = []
        if not mast_rows.empty and "mission" in mast_rows.columns:
            mission_rows = mast_rows.copy()
            mission_rows["extracted_rows_numeric"] = pd.to_numeric(
                mission_rows.get("extracted_rows", pd.Series(dtype=float)),
                errors="coerce",
            ).fillna(0)
            missions = sorted(
                value
                for value, group in mission_rows.groupby("mission")
                if value and group["extracted_rows_numeric"].sum() > 0
            )
        mast_lightcurve_rows = 0
        for mission_slug in config.MISSION_SLUGS:
            mast_lightcurve_rows += _count_rows(
                config.SILVER_DATA_DIR
                / "lightcurves"
                / "mast"
                / slug
                / f"{mission_slug}_lightcurve.csv"
            )
        exomast_json_count = len(list((config.RAW_DATA_DIR / "exomast" / slug).glob("*.json")))
        etd_obs_rows = (
            etd_observations[etd_observations.get("planet_slug", "") == slug]
            if not etd_observations.empty
            else pd.DataFrame()
        )
        etd_point_rows = (
            etd_points[etd_points.get("planet_slug", "") == slug]
            if not etd_points.empty
            else pd.DataFrame()
        )
        etd_curve_rows = (
            etd_metadata[etd_metadata.get("planet_slug", "") == slug]
            if not etd_metadata.empty
            else pd.DataFrame()
        )
        summary_rows.append(
            {
                "planet_name": planet["planet_name"],
                "host_star": planet["host_star"],
                "planet_slug": slug,
                "nasa_pscomppars_rows": int(
                    (nasa_pscomppars.get("planet_slug", pd.Series(dtype=str)) == slug).sum()
                )
                if not nasa_pscomppars.empty
                else 0,
                "nasa_ps_rows": int((nasa_ps.get("planet_slug", pd.Series(dtype=str)) == slug).sum())
                if not nasa_ps.empty
                else 0,
                "mast_fits_count": int(len(mast_rows)),
                "mast_lightcurve_rows": int(mast_lightcurve_rows),
                "mast_missions_available": "|".join(missions),
                "exomast_json_count": int(exomast_json_count),
                "etd_observation_count": int(len(etd_obs_rows)),
                "etd_lightcurve_json_count": int(len(etd_curve_rows)),
                "etd_lightcurve_point_count": int(len(etd_point_rows)),
            }
        )

    summary_by_planet = pd.DataFrame(summary_rows)
    summary_path = validation_dir / "silver_summary_by_planet.csv"
    atomic_write_dataframe(summary_path, summary_by_planet)
    manifest.add_artifact(
        path=summary_path,
        transformation_type="silver_summary_by_planet",
        row_count=len(summary_by_planet),
        column_count=len(summary_by_planet.columns),
        notes="Cross-source row and file counts by planet.",
    )

    mast_quality_rows: list[dict[str, Any]] = []
    for planet in sorted_planets(config):
        slug = planet["planet_slug"]
        for mission_slug in config.MISSION_SLUGS:
            path = (
                config.SILVER_DATA_DIR
                / "lightcurves"
                / "mast"
                / slug
                / f"{mission_slug}_lightcurve.csv"
            )
            curve = _read_csv_if_exists(path)
            metadata_rows = (
                mast_metadata[
                    (mast_metadata.get("planet_slug", "") == slug)
                    & (mast_metadata.get("mission", "").str.lower() == mission_slug)
                ]
                if not mast_metadata.empty and "mission" in mast_metadata.columns
                else pd.DataFrame()
            )
            if curve.empty and metadata_rows.empty:
                continue
            quality = pd.to_numeric(curve.get("quality", pd.Series(dtype=float)), errors="coerce")
            mast_quality_rows.append(
                {
                    "planet_name": planet["planet_name"],
                    "mission": mission_slug,
                    "fits_count": int(len(metadata_rows)),
                    "total_rows": int(len(curve)),
                    "rows_with_quality_zero": int((quality == 0).sum()),
                    "rows_with_quality_nonzero": int(((quality != 0) & quality.notna()).sum()),
                    "rows_with_missing_quality": int(quality.isna().sum()) if not curve.empty else 0,
                    "pdcsap_flux_non_null_count": int(
                        pd.to_numeric(curve.get("pdcsap_flux", pd.Series(dtype=float)), errors="coerce")
                        .notna()
                        .sum()
                    ),
                    "sap_flux_non_null_count": int(
                        pd.to_numeric(curve.get("sap_flux", pd.Series(dtype=float)), errors="coerce")
                        .notna()
                        .sum()
                    ),
                    "time_min": pd.to_numeric(curve.get("time", pd.Series(dtype=float)), errors="coerce").min()
                    if not curve.empty
                    else "",
                    "time_max": pd.to_numeric(curve.get("time", pd.Series(dtype=float)), errors="coerce").max()
                    if not curve.empty
                    else "",
                }
            )

    mast_quality = pd.DataFrame(mast_quality_rows)
    mast_quality_path = validation_dir / "silver_mast_quality_summary.csv"
    atomic_write_dataframe(mast_quality_path, mast_quality)
    manifest.add_artifact(
        path=mast_quality_path,
        transformation_type="silver_mast_quality_summary",
        row_count=len(mast_quality),
        column_count=len(mast_quality.columns),
        notes="Quality flag and flux availability counts by planet and mission.",
    )

    etd_summary_rows: list[dict[str, Any]] = []
    private_counts = _read_private_record_counts(config)
    for planet in sorted_planets(config):
        slug = planet["planet_slug"]
        obs = (
            etd_observations[etd_observations.get("planet_slug", "") == slug]
            if not etd_observations.empty
            else pd.DataFrame()
        )
        points = (
            etd_points[etd_points.get("planet_slug", "") == slug]
            if not etd_points.empty
            else pd.DataFrame()
        )
        curves = (
            etd_metadata[etd_metadata.get("planet_slug", "") == slug]
            if not etd_metadata.empty
            else pd.DataFrame()
        )
        filters = sorted(
            {
                value
                for value in pd.concat(
                    [
                        points.get("filter", pd.Series(dtype=str)).astype(str),
                        points.get("mag_band", pd.Series(dtype=str)).astype(str),
                    ],
                    ignore_index=True,
                )
                if value
            }
        )
        dqi = pd.to_numeric(obs.get("dqi", pd.Series(dtype=float)), errors="coerce")
        etd_summary_rows.append(
            {
                "planet_name": planet["planet_name"],
                "observation_count": int(len(obs)),
                "private_records_count": int(private_counts.get(slug, 0)),
                "downloaded_curve_count": int(len(curves)),
                "photometry_points_count": int(len(points)),
                "filters_observed": "|".join(filters),
                "dqi_min": dqi.min() if dqi.notna().any() else "",
                "dqi_max": dqi.max() if dqi.notna().any() else "",
            }
        )
    etd_summary = pd.DataFrame(etd_summary_rows)
    etd_summary_path = validation_dir / "silver_etd_summary.csv"
    atomic_write_dataframe(etd_summary_path, etd_summary)
    manifest.add_artifact(
        path=etd_summary_path,
        transformation_type="silver_etd_summary",
        row_count=len(etd_summary),
        column_count=len(etd_summary.columns),
        notes="ETD observation, curve, point, filter, and DQI counts.",
    )

    column_report = _build_column_presence_report(config, mast_metadata)
    column_report_path = validation_dir / "silver_column_presence_report.csv"
    atomic_write_dataframe(column_report_path, column_report)
    manifest.add_artifact(
        path=column_report_path,
        transformation_type="silver_column_presence_report",
        row_count=len(column_report),
        column_count=len(column_report.columns),
        notes="Presence of expected columns in generated SILVER tables and FITS metadata.",
    )

    logger.info("SILVER validation summaries finished")
    return {
        "summary_by_planet": summary_path,
        "mast_quality_summary": mast_quality_path,
        "etd_summary": etd_summary_path,
        "column_presence_report": column_report_path,
    }


def _read_private_record_counts(config: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for planet in sorted_planets(config):
        slug = planet["planet_slug"]
        path = (
            config.RAW_DATA_DIR
            / "etd_varastro"
            / "extracted_metadata"
            / slug
            / "observations_raw.json"
        )
        if not path.exists():
            counts[slug] = 0
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            transits = payload.get("transits", []) if isinstance(payload, dict) else []
            counts[slug] = int(
                sum(1 for item in transits if bool(item.get("isPrivate")) or str(item.get("isPrivate")).lower() == "true")
            )
        except Exception:
            counts[slug] = 0
    return counts


def _build_column_presence_report(config: Any, mast_metadata: pd.DataFrame) -> pd.DataFrame:
    expected_tables: dict[str, tuple[Path, tuple[str, ...]]] = {
        "nasa_pscomppars_selected_planets": (
            config.SILVER_DATA_DIR / "catalogs" / "nasa" / "pscomppars_selected_planets.csv",
            (
                "planet_name",
                "host_star",
                "orbital_period_days",
                "transit_midpoint_bjd",
                "transit_depth_percent",
                "transit_depth_fraction",
                "source_raw_path",
                "source_raw_sha256",
                "silver_created_at_utc",
            ),
        ),
        "nasa_ps_all_solutions": (
            config.SILVER_DATA_DIR / "catalogs" / "nasa" / "ps_all_solutions.csv",
            ("planet_name", "host_star", "planet_slug", "source_raw_path", "solution_row_index"),
        ),
        "exomast_identifiers": (
            config.SILVER_DATA_DIR / "catalogs" / "exomast" / "exomast_identifiers.csv",
            ("planet_name", "host_star", "planet_slug", "exomast_file_type", "source_raw_path"),
        ),
        "exomast_properties": (
            config.SILVER_DATA_DIR / "catalogs" / "exomast" / "exomast_properties.csv",
            ("planet_name", "host_star", "planet_slug", "exomast_file_type", "source_raw_path"),
        ),
        "exomast_tces": (
            config.SILVER_DATA_DIR / "catalogs" / "exomast" / "exomast_tces.csv",
            ("planet_name", "host_star", "planet_slug", "exomast_file_type", "source_raw_path"),
        ),
        "mast_fits_metadata": (
            config.SILVER_DATA_DIR / "lightcurves" / "mast" / "mast_fits_metadata.csv",
            ("planet_name", "host_star", "planet_slug", "mission", "available_columns", "status"),
        ),
        "etd_observations": (
            config.SILVER_DATA_DIR / "etd" / "etd_observations.csv",
            ("planet_name", "host_star", "planet_slug", "obs_id", "trans_id", "source_raw_path"),
        ),
        "etd_lightcurve_points": (
            config.SILVER_DATA_DIR / "etd" / "etd_lightcurve_points.csv",
            ("planet_name", "host_star", "planet_slug", "point_index", "jd", "mag", "source_raw_path"),
        ),
        "etd_lightcurve_metadata": (
            config.SILVER_DATA_DIR / "etd" / "etd_lightcurve_metadata.csv",
            ("planet_name", "host_star", "planet_slug", "point_count", "status", "source_raw_path"),
        ),
    }
    rows: list[dict[str, Any]] = []
    for table_name, (path, expected_columns) in expected_tables.items():
        dataframe = _read_csv_if_exists(path)
        existing = set(dataframe.columns)
        for column in expected_columns:
            rows.append(
                {
                    "source_or_table": table_name,
                    "column_name": column,
                    "expected": True,
                    "present": column in existing,
                    "non_null_count": int(dataframe[column].replace("", pd.NA).notna().sum())
                    if column in existing
                    else 0,
                    "row_count": int(len(dataframe)),
                    "notes": relative_path(path, config.PROJECT_ROOT),
                    "created_at_utc": utc_now(),
                }
            )

    if not mast_metadata.empty and "available_columns" in mast_metadata.columns:
        available_counter: Counter[str] = Counter()
        missing_counter: Counter[str] = Counter()
        for _, row in mast_metadata.iterrows():
            available = {
                value.strip()
                for value in str(row.get("available_columns", "")).split("|")
                if value.strip()
            }
            missing = {
                value.strip()
                for value in str(row.get("missing_preferred_columns", "")).split("|")
                if value.strip()
            }
            available_counter.update(available)
            missing_counter.update(missing)
        for column in config.FITS_PREFERRED_COLUMNS:
            rows.append(
                {
                    "source_or_table": "mast_fits_preferred_columns",
                    "column_name": column,
                    "expected": True,
                    "present": available_counter.get(column, 0) > 0,
                    "non_null_count": int(available_counter.get(column, 0)),
                    "row_count": int(len(mast_metadata)),
                    "notes": f"missing_in_fits_count={missing_counter.get(column, 0)}",
                    "created_at_utc": utc_now(),
                }
            )
    return pd.DataFrame(rows)
