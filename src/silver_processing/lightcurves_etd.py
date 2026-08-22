"""ETD / VarAstro consolidation for SILVER."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

from .manifests import SilverManifest
from .utils import (
    atomic_write_dataframe,
    compact_json,
    get_raw_info,
    relative_path,
    sorted_planets,
    utc_now,
)


ETD_OBSERVATION_COLUMNS = (
    "planet_name",
    "host_star",
    "planet_slug",
    "source_name",
    "source_raw_path",
    "source_raw_sha256",
    "source_raw_file_name",
    "obs_id",
    "trans_id",
    "epoch",
    "hjd_mid",
    "jd_mid_err",
    "duration",
    "duration_err",
    "depth",
    "depth_err",
    "dqi",
    "band",
    "observer",
    "reference",
    "reference_url",
    "data_version",
    "is_private",
    "raw_metadata_json",
    "silver_created_at_utc",
)

ETD_POINT_COLUMNS = (
    "planet_name",
    "host_star",
    "planet_slug",
    "source_name",
    "source_raw_path",
    "source_raw_sha256",
    "source_raw_file_name",
    "obs_id",
    "trans_id",
    "point_index",
    "jd",
    "mag",
    "mag_error",
    "filter",
    "airmass",
    "mag_band",
    "source_json_file",
    "silver_created_at_utc",
)

ETD_METADATA_COLUMNS = (
    "planet_name",
    "host_star",
    "planet_slug",
    "source_name",
    "source_json_file",
    "source_raw_path",
    "source_raw_sha256",
    "source_raw_file_name",
    "obs_id",
    "trans_id",
    "point_count",
    "has_photometry",
    "has_airmass",
    "has_minimas",
    "has_transits",
    "mag_band",
    "time_span",
    "orig_raw_header_present",
    "status",
    "error_message",
    "silver_created_at_utc",
)


def build_etd_tables(
    *,
    config: Any,
    raw_lookup: dict[str, dict[str, str]],
    manifest: SilverManifest,
    logger: logging.Logger,
) -> dict[str, pd.DataFrame]:
    """Build SILVER ETD observation and light-curve point tables."""

    logger.info("Building ETD / VarAstro SILVER tables")
    created_at = utc_now()
    output_dir = config.SILVER_DATA_DIR / "etd"
    observation_rows: list[dict[str, Any]] = []
    point_rows: list[dict[str, Any]] = []
    metadata_rows: list[dict[str, Any]] = []
    private_record_counts: dict[str, int] = {}

    for planet in sorted_planets(config):
        slug = planet["planet_slug"]
        observations, private_count = _read_planet_observations(
            config=config,
            raw_lookup=raw_lookup,
            planet=planet,
            created_at=created_at,
            logger=logger,
            manifest=manifest,
        )
        observation_rows.extend(observations)
        private_record_counts[slug] = private_count

        curve_dir = config.RAW_DATA_DIR / "etd_varastro" / "downloaded_lightcurves" / slug
        for curve_path in sorted(curve_dir.glob("*.json")):
            try:
                rows, metadata = _read_curve_json(
                    config=config,
                    raw_lookup=raw_lookup,
                    planet=planet,
                    path=curve_path,
                    created_at=created_at,
                )
                point_rows.extend(rows)
                metadata_rows.append(metadata)
                logger.info(
                    "ETD curve processed for %s: file=%s points=%s",
                    slug,
                    curve_path.name,
                    len(rows),
                )
            except Exception as exc:
                logger.exception("Failed to process ETD curve JSON: %s", curve_path)
                raw_info = get_raw_info(curve_path, config, raw_lookup)
                ids = _ids_from_curve_filename(curve_path.name)
                metadata_rows.append(
                    {
                        "planet_name": planet["planet_name"],
                        "host_star": planet["host_star"],
                        "planet_slug": slug,
                        "source_name": raw_info["source_name"] or "ETD / VarAstro",
                        "source_json_file": curve_path.name,
                        "source_raw_path": relative_path(curve_path, config.PROJECT_ROOT),
                        "source_raw_sha256": raw_info["source_raw_sha256"],
                        "source_raw_file_name": curve_path.name,
                        "obs_id": ids["obs_id"],
                        "trans_id": ids["trans_id"],
                        "point_count": 0,
                        "has_photometry": False,
                        "has_airmass": False,
                        "has_minimas": False,
                        "has_transits": False,
                        "mag_band": "",
                        "time_span": "",
                        "orig_raw_header_present": False,
                        "status": "failed",
                        "error_message": str(exc),
                        "silver_created_at_utc": created_at,
                    }
                )
                manifest.add_failure(
                    source_raw_path=relative_path(curve_path, config.PROJECT_ROOT),
                    source_name=raw_info["source_name"] or "ETD / VarAstro",
                    planet_name=planet["planet_name"],
                    host_star=planet["host_star"],
                    raw_file_type="json",
                    transformation_type="etd_lightcurve_points",
                    error_message=str(exc),
                )

    observations = pd.DataFrame(observation_rows, columns=ETD_OBSERVATION_COLUMNS)
    observations_path = output_dir / "etd_observations.csv"
    atomic_write_dataframe(observations_path, observations)
    manifest.add_artifact(
        path=observations_path,
        source_name="ETD / VarAstro",
        transformation_type="etd_observations",
        row_count=len(observations),
        column_count=len(observations.columns),
        notes=(
            "Consolidated public ETD transit observations. Private records are "
            f"excluded from this table; counts by planet: {private_record_counts}."
        ),
    )

    points = pd.DataFrame(point_rows, columns=ETD_POINT_COLUMNS)
    points_path = output_dir / "etd_lightcurve_points.csv"
    atomic_write_dataframe(points_path, points)
    manifest.add_artifact(
        path=points_path,
        source_name="ETD / VarAstro",
        transformation_type="etd_lightcurve_points",
        row_count=len(points),
        column_count=len(points.columns),
        notes="Photometric points extracted from public ETD curve JSONs; magnitudes are not converted to flux.",
    )

    metadata = pd.DataFrame(metadata_rows, columns=ETD_METADATA_COLUMNS)
    metadata_path = output_dir / "etd_lightcurve_metadata.csv"
    atomic_write_dataframe(metadata_path, metadata)
    manifest.add_artifact(
        path=metadata_path,
        source_name="ETD / VarAstro",
        transformation_type="etd_lightcurve_metadata",
        row_count=len(metadata),
        column_count=len(metadata.columns),
        notes="One metadata row per public ETD curve JSON processed.",
    )
    logger.info(
        "ETD SILVER tables finished: observations=%s points=%s curve_metadata=%s",
        len(observations),
        len(points),
        len(metadata),
    )
    return {
        "observations": observations,
        "lightcurve_points": points,
        "lightcurve_metadata": metadata,
    }


def _read_planet_observations(
    *,
    config: Any,
    raw_lookup: dict[str, dict[str, str]],
    planet: dict[str, Any],
    created_at: str,
    logger: logging.Logger,
    manifest: SilverManifest,
) -> tuple[list[dict[str, Any]], int]:
    slug = planet["planet_slug"]
    json_path = (
        config.RAW_DATA_DIR
        / "etd_varastro"
        / "extracted_metadata"
        / slug
        / "observations_raw.json"
    )
    if not json_path.exists():
        fallback_rows = _read_observation_csv_fallback(config, raw_lookup, planet, created_at)
        return fallback_rows, 0

    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        transits = payload.get("transits", []) if isinstance(payload, dict) else []
        raw_info = get_raw_info(json_path, config, raw_lookup)
        rows: list[dict[str, Any]] = []
        private_count = 0
        for transit in transits:
            is_private = _as_bool(_value(transit, "isPrivate", "is_private"))
            if is_private:
                private_count += 1
                continue
            rows.append(
                {
                    "planet_name": planet["planet_name"],
                    "host_star": planet["host_star"],
                    "planet_slug": slug,
                    "source_name": raw_info["source_name"] or "ETD / VarAstro",
                    "source_raw_path": raw_info["source_raw_path"],
                    "source_raw_sha256": raw_info["source_raw_sha256"],
                    "source_raw_file_name": raw_info["source_raw_file_name"],
                    "obs_id": _value(transit, "obsId", "obs_id"),
                    "trans_id": _value(transit, "transId", "trans_id"),
                    "epoch": _value(transit, "epoch"),
                    "hjd_mid": _value(transit, "hjdMid", "hjd_mid"),
                    "jd_mid_err": _value(transit, "jdMidErr", "jd_mid_err"),
                    "duration": _value(transit, "duration"),
                    "duration_err": _value(transit, "durationErr", "duration_err"),
                    "depth": _value(transit, "depth"),
                    "depth_err": _value(transit, "depthErr", "depth_err"),
                    "dqi": _value(transit, "dqi", "DQI"),
                    "band": _value(transit, "band", "filter"),
                    "observer": _value(transit, "observer"),
                    "reference": _value(transit, "reference"),
                    "reference_url": _value(transit, "referenceUrl", "reference_url"),
                    "data_version": _value(transit, "dataVersion", "data_version"),
                    "is_private": False,
                    "raw_metadata_json": compact_json(transit),
                    "silver_created_at_utc": created_at,
                }
            )
        logger.info(
            "ETD observations processed for %s: public=%s private=%s",
            slug,
            len(rows),
            private_count,
        )
        return rows, private_count
    except Exception as exc:
        logger.exception("Failed to process ETD observations JSON for %s", slug)
        manifest.add_failure(
            source_raw_path=relative_path(json_path, config.PROJECT_ROOT),
            source_name="ETD / VarAstro",
            planet_name=planet["planet_name"],
            host_star=planet["host_star"],
            raw_file_type="json",
            transformation_type="etd_observations",
            error_message=str(exc),
        )
        return [], 0


def _read_observation_csv_fallback(
    config: Any,
    raw_lookup: dict[str, dict[str, str]],
    planet: dict[str, Any],
    created_at: str,
) -> list[dict[str, Any]]:
    slug = planet["planet_slug"]
    directory = config.RAW_DATA_DIR / "etd_varastro" / "extracted_metadata" / slug
    candidates = sorted(directory.glob("observations_api_*.csv")) + sorted(
        directory.glob("observations.csv")
    )
    if not candidates:
        return []
    path = candidates[0]
    raw = pd.read_csv(path, dtype=str).fillna("")
    raw_info = get_raw_info(path, config, raw_lookup)
    rows = []
    for _, row in raw.iterrows():
        rows.append(
            {
                "planet_name": planet["planet_name"],
                "host_star": planet["host_star"],
                "planet_slug": slug,
                "source_name": raw_info["source_name"] or "ETD / VarAstro",
                "source_raw_path": raw_info["source_raw_path"],
                "source_raw_sha256": raw_info["source_raw_sha256"],
                "source_raw_file_name": raw_info["source_raw_file_name"],
                "obs_id": _value(row, "obsId", "obs_id"),
                "trans_id": _value(row, "transId", "trans_id"),
                "epoch": _value(row, "epoch"),
                "hjd_mid": _value(row, "hjdMid", "hjd_mid"),
                "jd_mid_err": _value(row, "jdMidErr", "jd_mid_err"),
                "duration": _value(row, "duration"),
                "duration_err": _value(row, "durationErr", "duration_err"),
                "depth": _value(row, "depth"),
                "depth_err": _value(row, "depthErr", "depth_err"),
                "dqi": _value(row, "dqi", "DQI"),
                "band": _value(row, "band", "filter"),
                "observer": _value(row, "observer"),
                "reference": _value(row, "reference"),
                "reference_url": _value(row, "referenceUrl", "reference_url"),
                "data_version": _value(row, "dataVersion", "data_version"),
                "is_private": False,
                "raw_metadata_json": compact_json(row.to_dict()),
                "silver_created_at_utc": created_at,
            }
        )
    return rows


def _read_curve_json(
    *,
    config: Any,
    raw_lookup: dict[str, dict[str, str]],
    planet: dict[str, Any],
    path: Path,
    created_at: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_info = get_raw_info(path, config, raw_lookup)
    ids = _ids_from_curve_filename(path.name)
    photometry = payload.get("photometry", []) if isinstance(payload, dict) else []
    airmass = payload.get("airmass", []) if isinstance(payload, dict) else []
    mag_band = payload.get("magBand", "") if isinstance(payload, dict) else ""
    time_span = payload.get("timeSpan", "") if isinstance(payload, dict) else ""

    point_rows: list[dict[str, Any]] = []
    for index, point in enumerate(photometry if isinstance(photometry, list) else []):
        point_rows.append(
            {
                "planet_name": planet["planet_name"],
                "host_star": planet["host_star"],
                "planet_slug": planet["planet_slug"],
                "source_name": raw_info["source_name"] or "ETD / VarAstro",
                "source_raw_path": raw_info["source_raw_path"],
                "source_raw_sha256": raw_info["source_raw_sha256"],
                "source_raw_file_name": raw_info["source_raw_file_name"],
                "obs_id": ids["obs_id"],
                "trans_id": ids["trans_id"],
                "point_index": index,
                "jd": _value(point, "jd", "time"),
                "mag": _value(point, "mag", "magnitude"),
                "mag_error": _value(point, "magError", "mag_error"),
                "filter": _value(point, "filter", "band"),
                "airmass": _airmass_for_point(airmass, index, _value(point, "jd", "time")),
                "mag_band": mag_band,
                "source_json_file": path.name,
                "silver_created_at_utc": created_at,
            }
        )

    metadata = {
        "planet_name": planet["planet_name"],
        "host_star": planet["host_star"],
        "planet_slug": planet["planet_slug"],
        "source_name": raw_info["source_name"] or "ETD / VarAstro",
        "source_json_file": path.name,
        "source_raw_path": raw_info["source_raw_path"],
        "source_raw_sha256": raw_info["source_raw_sha256"],
        "source_raw_file_name": raw_info["source_raw_file_name"],
        "obs_id": ids["obs_id"],
        "trans_id": ids["trans_id"],
        "point_count": len(point_rows),
        "has_photometry": bool(photometry),
        "has_airmass": bool(airmass),
        "has_minimas": bool(payload.get("minimas")) if isinstance(payload, dict) else False,
        "has_transits": bool(payload.get("transits")) if isinstance(payload, dict) else False,
        "mag_band": mag_band,
        "time_span": compact_json(time_span) if isinstance(time_span, (dict, list)) else time_span,
        "orig_raw_header_present": bool(payload.get("origRawHeader")) if isinstance(payload, dict) else False,
        "status": "created",
        "error_message": "",
        "silver_created_at_utc": created_at,
    }
    return point_rows, metadata


def _ids_from_curve_filename(filename: str) -> dict[str, str]:
    match = re.search(r"observation_(?P<obs>\d+)_transit_(?P<trans>\d+)", filename)
    if not match:
        return {"obs_id": "", "trans_id": ""}
    return {"obs_id": match.group("obs"), "trans_id": match.group("trans")}


def _airmass_for_point(airmass: Any, index: int, jd: Any) -> Any:
    if isinstance(airmass, list) and len(airmass) > index:
        item = airmass[index]
        if isinstance(item, dict):
            return _value(item, "value", "airmass", "alt")
        return item
    if isinstance(airmass, list):
        jd_text = str(jd)
        for item in airmass:
            if isinstance(item, dict) and str(_value(item, "jd", "time")) == jd_text:
                return _value(item, "value", "airmass", "alt")
    return ""


def _value(record: Any, *keys: str) -> Any:
    if isinstance(record, pd.Series):
        record = record.to_dict()
    if not isinstance(record, dict):
        return ""
    lower_lookup = {str(key).lower(): key for key in record.keys()}
    for key in keys:
        if key in record:
            return record[key]
        matched = lower_lookup.get(key.lower())
        if matched is not None:
            return record[matched]
    return ""


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}
