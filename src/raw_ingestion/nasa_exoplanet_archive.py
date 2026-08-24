"""Collect unmodified CSV responses from the NASA Exoplanet Archive TAP API."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
from pathlib import Path
from typing import Any

import requests

from .utils import (
    RawDataManifest,
    atomic_write_json,
    atomic_write_text,
    register_error,
    safe_slug,
    save_artifact,
    utc_now,
    versioned_path,
)

SOURCE_NAME = "NASA Exoplanet Archive"


def _tap_request(
    session: requests.Session,
    config: Any,
    query: str,
) -> requests.Response:
    response = session.get(
        config.NASA_TAP_SYNC_URL,
        params={"query": query, "format": "csv"},
        timeout=config.REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    prefix = response.content[:500].lower()
    if b"query_status" in prefix and b"error" in prefix:
        raise RuntimeError(response.text[:1000])
    if prefix.lstrip().startswith((b"<?xml", b"<votable", b"<!doctype html", b"<html")):
        raise RuntimeError(
            f"TAP returned non-CSV content ({response.headers.get('content-type', '')})"
        )
    return response


def _load_table_columns(
    session: requests.Session,
    config: Any,
    manifest: RawDataManifest,
    table_name: str,
    raw_dir: Path,
    logger: logging.Logger,
) -> set[str]:
    query = (
        "SELECT column_name FROM TAP_SCHEMA.columns "
        f"WHERE table_name = '{table_name}'"
    )
    schema_path = (
        raw_dir
        / "nasa_exoplanet_archive"
        / "manifests"
        / f"{table_name}_schema.csv"
    )
    if schema_path.exists():
        content = schema_path.read_bytes()
        manifest.record_artifact(
            path=schema_path,
            created=False,
            source_name=SOURCE_NAME,
            source_url=config.NASA_TAP_SYNC_URL,
            file_type="csv",
            product_type="tap_schema",
            query_or_search_term=query,
        )
    else:
        response = _tap_request(session, config, query)
        content = response.content
        save_artifact(
            manifest,
            schema_path,
            content,
            source_name=SOURCE_NAME,
            source_url=response.url,
            file_type="csv",
            product_type="tap_schema",
            query_or_search_term=query,
        )
        logger.info("NASA TAP schema saved for table %s", table_name)

    columns: set[str] = set()
    try:
        text = content.decode("utf-8-sig")
        for row in csv.DictReader(io.StringIO(text)):
            value = row.get("column_name") or row.get("COLUMN_NAME")
            if value:
                columns.add(value.strip().lower())
    except (UnicodeDecodeError, csv.Error) as exc:
        logger.warning("Could not parse TAP schema for %s: %s", table_name, exc)
    return columns


def _selected_columns(config: Any, available_columns: set[str]) -> list[str]:
    if not available_columns:
        return ["*"]
    selected = [
        column
        for column in config.NASA_DESIRED_COLUMNS
        if column.lower() in available_columns
    ]
    return selected or ["*"]


def _save_sidecars(
    directory: Path,
    query: str,
    metadata: dict[str, Any],
    manifest: RawDataManifest,
    *,
    source_url: str,
    planet_name: str = "",
    host_star: str = "",
) -> None:
    query_content = (query.rstrip() + "\n").encode("utf-8")
    query_path = versioned_path(directory / "query.sql", query_content, "query")
    query_created = atomic_write_text(query_path, query_content.decode("utf-8"))
    manifest.record_artifact(
        path=query_path,
        created=query_created,
        source_name=SOURCE_NAME,
        source_url=source_url,
        planet_name=planet_name,
        host_star=host_star,
        file_type="sql",
        product_type="tap_query",
        query_or_search_term=query,
    )

    metadata_content = (
        json.dumps(metadata, indent=2, ensure_ascii=False, default=str) + "\n"
    ).encode("utf-8")
    metadata_path = directory / "metadata.json"
    if metadata_path.exists() and metadata_path.read_bytes() != metadata_content:
        query_digest = hashlib.sha256(query.encode("utf-8")).hexdigest()[:12]
        metadata_path = directory / f"metadata_query_{query_digest}.json"
    metadata_created = atomic_write_json(metadata_path, metadata)
    manifest.record_artifact(
        path=metadata_path,
        created=metadata_created,
        source_name=SOURCE_NAME,
        source_url=source_url,
        planet_name=planet_name,
        host_star=host_star,
        file_type="json",
        product_type="collection_metadata",
        query_or_search_term=query,
    )


def _collect_planet_table(
    session: requests.Session,
    config: Any,
    manifest: RawDataManifest,
    logger: logging.Logger,
    table_name: str,
    columns: list[str],
    planet: dict[str, Any],
) -> None:
    planet_name = planet["planet_name"]
    host_star = planet["host_star"]
    planet_slug = safe_slug(planet_name)
    directory = (
        config.RAW_DATA_DIR
        / "nasa_exoplanet_archive"
        / table_name
        / planet_slug
    )
    directory.mkdir(parents=True, exist_ok=True)
    escaped_name = planet_name.replace("'", "''")
    query = (
        f"SELECT {', '.join(columns)} FROM {table_name} "
        f"WHERE pl_name = '{escaped_name}'"
    )
    response_path = directory / "response.csv"

    if response_path.exists():
        logger.info("NASA %s skipped (exists): %s", table_name, planet_name)
        manifest.record_artifact(
            path=response_path,
            created=False,
            source_name=SOURCE_NAME,
            source_url=config.NASA_TAP_SYNC_URL,
            planet_name=planet_name,
            host_star=host_star,
            file_type="csv",
            product_type=table_name,
            query_or_search_term=query,
        )
        metadata = {
            "collected_at_utc": utc_now(),
            "table": table_name,
            "planet_name": planet_name,
            "host_star": host_star,
            "query": query,
            "status": "skipped_existing",
            "selected_columns": columns,
        }
        _save_sidecars(
            directory,
            query,
            metadata,
            manifest,
            source_url=config.NASA_TAP_SYNC_URL,
            planet_name=planet_name,
            host_star=host_star,
        )
        return

    try:
        response = _tap_request(session, config, query)
        save_artifact(
            manifest,
            response_path,
            response.content,
            source_name=SOURCE_NAME,
            source_url=response.url,
            planet_name=planet_name,
            host_star=host_star,
            file_type="csv",
            product_type=table_name,
            query_or_search_term=query,
            notes="Unmodified CSV response returned by the TAP sync endpoint.",
        )
        row_count = max(response.text.count("\n") - 1, 0)
        logger.info(
            "NASA %s saved for %s (%s data rows)",
            table_name,
            planet_name,
            row_count,
        )
        metadata = {
            "collected_at_utc": utc_now(),
            "table": table_name,
            "planet_name": planet_name,
            "host_star": host_star,
            "request_url": response.url,
            "query": query,
            "status": "downloaded",
            "http_status": response.status_code,
            "content_type": response.headers.get("content-type"),
            "selected_columns": columns,
            "estimated_data_rows": row_count,
        }
    except Exception as exc:
        register_error(
            manifest,
            logger,
            source_name=SOURCE_NAME,
            source_url=config.NASA_TAP_SYNC_URL,
            planet_name=planet_name,
            host_star=host_star,
            product_type=table_name,
            query_or_search_term=query,
            error=exc,
        )
        metadata = {
            "collected_at_utc": utc_now(),
            "table": table_name,
            "planet_name": planet_name,
            "host_star": host_star,
            "query": query,
            "status": "failed",
            "error": str(exc),
            "selected_columns": columns,
        }

    _save_sidecars(
        directory,
        query,
        metadata,
        manifest,
        source_url=config.NASA_TAP_SYNC_URL,
        planet_name=planet_name,
        host_star=host_star,
    )


def _collect_transiting_snapshot(
    session: requests.Session,
    config: Any,
    manifest: RawDataManifest,
    logger: logging.Logger,
    columns: list[str],
    available_columns: set[str],
) -> None:
    base_dir = config.RAW_DATA_DIR / "nasa_exoplanet_archive" / "pscomppars"
    response_path = base_dir / "all_transiting_planets_snapshot.csv"
    query_path = base_dir / "all_transiting_planets_snapshot.query.sql"
    metadata_path = base_dir / "all_transiting_planets_snapshot.metadata.json"

    conditions = []
    if not available_columns:
        conditions = [
            "discoverymethod = 'Transit'",
            "pl_orbper IS NOT NULL",
            "(pl_rade IS NOT NULL OR pl_trandep IS NOT NULL)",
        ]
    if "discoverymethod" in available_columns:
        conditions.append("discoverymethod = 'Transit'")
    elif "tran_flag" in available_columns:
        conditions.append("tran_flag = 1")
    if "pl_orbper" in available_columns:
        conditions.append("pl_orbper IS NOT NULL")
    radius_conditions = [
        f"{column} IS NOT NULL"
        for column in ("pl_rade", "pl_trandep")
        if column in available_columns
    ]
    if radius_conditions:
        conditions.append(f"({' OR '.join(radius_conditions)})")

    where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    query = (
        f"SELECT {', '.join(columns)} FROM pscomppars"
        f"{where_clause} ORDER BY pl_name"
    )

    query_content = (query + "\n").encode("utf-8")
    query_path = versioned_path(query_path, query_content, "query")
    query_created = atomic_write_text(query_path, query_content.decode("utf-8"))
    manifest.record_artifact(
        path=query_path,
        created=query_created,
        source_name=SOURCE_NAME,
        source_url=config.NASA_TAP_SYNC_URL,
        file_type="sql",
        product_type="tap_query",
        query_or_search_term=query,
    )

    if response_path.exists():
        logger.info("NASA transiting planets snapshot skipped (exists)")
        manifest.record_artifact(
            path=response_path,
            created=False,
            source_name=SOURCE_NAME,
            source_url=config.NASA_TAP_SYNC_URL,
            file_type="csv",
            product_type="pscomppars_transiting_snapshot",
            query_or_search_term=query,
        )
        status = "skipped_existing"
        error_message = ""
        request_url = config.NASA_TAP_SYNC_URL
    else:
        try:
            response = _tap_request(session, config, query)
            save_artifact(
                manifest,
                response_path,
                response.content,
                source_name=SOURCE_NAME,
                source_url=response.url,
                file_type="csv",
                product_type="pscomppars_transiting_snapshot",
                query_or_search_term=query,
                notes="Unmodified CSV response returned by the TAP sync endpoint.",
            )
            logger.info("NASA transiting planets snapshot saved")
            status = "downloaded"
            error_message = ""
            request_url = response.url
        except Exception as exc:
            register_error(
                manifest,
                logger,
                source_name=SOURCE_NAME,
                source_url=config.NASA_TAP_SYNC_URL,
                product_type="pscomppars_transiting_snapshot",
                query_or_search_term=query,
                error=exc,
            )
            status = "failed"
            error_message = str(exc)
            request_url = config.NASA_TAP_SYNC_URL

    metadata = {
        "collected_at_utc": utc_now(),
        "table": "pscomppars",
        "request_url": request_url,
        "query": query,
        "status": status,
        "error": error_message,
        "selected_columns": columns,
        "purpose": (
            "Snapshot of transiting confirmed planets with orbital period and "
            "planet radius or transit depth where supported by the current schema."
        ),
    }
    metadata_content = (
        json.dumps(metadata, indent=2, ensure_ascii=False, default=str) + "\n"
    ).encode("utf-8")
    if metadata_path.exists() and metadata_path.read_bytes() != metadata_content:
        query_digest = hashlib.sha256(query.encode("utf-8")).hexdigest()[:12]
        metadata_path = metadata_path.with_name(
            f"{metadata_path.stem}_query_{query_digest}{metadata_path.suffix}"
        )
    metadata_created = atomic_write_json(metadata_path, metadata)
    manifest.record_artifact(
        path=metadata_path,
        created=metadata_created,
        source_name=SOURCE_NAME,
        source_url=request_url,
        file_type="json",
        product_type="collection_metadata",
        query_or_search_term=query,
    )


def collect_nasa_exoplanet_archive(
    config: Any,
    session: requests.Session,
    manifest: RawDataManifest,
    logger: logging.Logger,
) -> None:
    logger.info("Starting NASA Exoplanet Archive collection")
    schemas: dict[str, set[str]] = {}
    for table_name in ("pscomppars", "ps"):
        try:
            schemas[table_name] = _load_table_columns(
                session,
                config,
                manifest,
                table_name,
                config.RAW_DATA_DIR,
                logger,
            )
        except Exception as exc:
            logger.warning(
                "NASA TAP schema lookup failed for %s; using configured columns: %s",
                table_name,
                exc,
            )
            schemas[table_name] = set()

    for planet in sorted(config.PLANETS, key=lambda item: item["priority"]):
        logger.info("NASA processing planet: %s", planet["planet_name"])
        for table_name in ("pscomppars", "ps"):
            columns = _selected_columns(config, schemas[table_name])
            _collect_planet_table(
                session,
                config,
                manifest,
                logger,
                table_name,
                columns,
                planet,
            )

    snapshot_columns = _selected_columns(config, schemas["pscomppars"])
    _collect_transiting_snapshot(
        session,
        config,
        manifest,
        logger,
        snapshot_columns,
        schemas["pscomppars"],
    )
    logger.info("Finished NASA Exoplanet Archive collection")
