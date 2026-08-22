"""Exo.MAST JSON flattening for SILVER catalogs."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from .manifests import SilverManifest
from .utils import (
    atomic_write_dataframe,
    compact_json,
    get_raw_info,
    serialize_complex_columns,
    sorted_planets,
    utc_now,
)


EXOMAST_FILE_GROUPS = {
    "identifiers": ("identifiers.json",),
    "properties": ("properties.json",),
    "tces": ("kepler_tces.json", "tess_tces.json"),
}

EXOMAST_REQUIRED_COLUMNS = (
    "planet_name",
    "host_star",
    "planet_slug",
    "exomast_file_type",
    "source_name",
    "source_raw_path",
    "source_raw_sha256",
    "source_raw_file_name",
    "raw_metadata_json",
    "silver_created_at_utc",
)


def build_exomast_catalogs(
    *,
    config: Any,
    raw_lookup: dict[str, dict[str, str]],
    manifest: SilverManifest,
    logger: logging.Logger,
) -> dict[str, pd.DataFrame]:
    """Flatten Exo.MAST JSON sidecars into SILVER tables."""

    logger.info("Building Exo.MAST SILVER catalogs")
    output_dir = config.SILVER_DATA_DIR / "catalogs" / "exomast"
    created_at = utc_now()
    grouped_rows: dict[str, list[pd.DataFrame]] = {
        "identifiers": [],
        "properties": [],
        "tces": [],
    }

    for planet in sorted_planets(config):
        planet_dir = config.RAW_DATA_DIR / "exomast" / planet["planet_slug"]
        for group, filenames in EXOMAST_FILE_GROUPS.items():
            for filename in filenames:
                path = planet_dir / filename
                if not path.exists():
                    logger.info("Exo.MAST file absent for %s: %s", planet["planet_slug"], filename)
                    continue
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    flattened = _flatten_exomast_payload(payload, filename)
                    flattened = serialize_complex_columns(flattened)
                    raw_info = get_raw_info(path, config, raw_lookup)
                    for column, value in (
                        ("planet_name", planet["planet_name"]),
                        ("host_star", planet["host_star"]),
                        ("planet_slug", planet["planet_slug"]),
                        ("exomast_file_type", path.stem),
                        ("source_name", raw_info["source_name"] or "Exo.MAST"),
                        ("source_raw_path", raw_info["source_raw_path"]),
                        ("source_raw_sha256", raw_info["source_raw_sha256"]),
                        ("source_raw_file_name", raw_info["source_raw_file_name"]),
                        ("raw_metadata_json", compact_json(payload)),
                        ("silver_created_at_utc", created_at),
                    ):
                        flattened[column] = value
                    flattened = _move_required_columns_to_front(flattened)
                    grouped_rows[group].append(flattened)
                    logger.info(
                        "Exo.MAST %s processed for %s: rows=%s",
                        filename,
                        planet["planet_slug"],
                        len(flattened),
                    )
                except Exception as exc:
                    logger.exception("Failed to process Exo.MAST file %s", path)
                    manifest.add_failure(
                        source_raw_path=str(path),
                        source_name="Exo.MAST",
                        planet_name=planet["planet_name"],
                        host_star=planet["host_star"],
                        raw_file_type="json",
                        transformation_type=f"exomast_{group}",
                        error_message=str(exc),
                    )

    outputs: dict[str, pd.DataFrame] = {}
    output_names = {
        "identifiers": "exomast_identifiers.csv",
        "properties": "exomast_properties.csv",
        "tces": "exomast_tces.csv",
    }
    for group, filename in output_names.items():
        frames = [
            frame.dropna(axis=1, how="all")
            for frame in grouped_rows[group]
            if not frame.empty
        ]
        dataframe = (
            pd.concat(frames, ignore_index=True)
            if frames
            else pd.DataFrame(columns=EXOMAST_REQUIRED_COLUMNS)
        )
        path = output_dir / filename
        atomic_write_dataframe(path, dataframe)
        manifest.add_artifact(
            path=path,
            source_name="Exo.MAST",
            transformation_type=f"exomast_{group}",
            row_count=len(dataframe),
            column_count=len(dataframe.columns),
            notes="Robust JSON flattening with compact raw JSON retained per source file.",
        )
        outputs[group] = dataframe

    logger.info(
        "Exo.MAST SILVER catalogs finished: identifiers=%s properties=%s tces=%s",
        len(outputs["identifiers"]),
        len(outputs["properties"]),
        len(outputs["tces"]),
    )
    return outputs


def _flatten_exomast_payload(payload: Any, filename: str) -> pd.DataFrame:
    """Flatten a variable-schema Exo.MAST JSON payload."""

    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        if isinstance(payload.get("TCE"), list):
            records = payload["TCE"]
        elif isinstance(payload.get("tce"), list):
            records = payload["tce"]
        elif isinstance(payload.get("results"), list):
            records = payload["results"]
        elif isinstance(payload.get("data"), list):
            records = payload["data"]
        else:
            records = [payload]
    else:
        records = [{"value": payload}]

    try:
        dataframe = pd.json_normalize(records, sep=".")
    except Exception:
        dataframe = pd.DataFrame({"raw_payload": [compact_json(payload)]})

    if dataframe.empty:
        dataframe = pd.DataFrame({"raw_payload": [compact_json(payload)]})
    dataframe.insert(0, "exomast_source_file", filename)
    return dataframe


def _move_required_columns_to_front(dataframe: pd.DataFrame) -> pd.DataFrame:
    ordered = [column for column in EXOMAST_REQUIRED_COLUMNS if column in dataframe.columns]
    ordered.extend(column for column in dataframe.columns if column not in ordered)
    return dataframe.loc[:, ordered]
