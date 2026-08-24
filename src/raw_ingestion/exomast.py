"""Collect public Exo.MAST resolver and target metadata as unmodified JSON."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

from .utils import (
    RawDataManifest,
    atomic_write_text,
    register_error,
    safe_slug,
    save_artifact,
    utc_now,
)

SOURCE_NAME = "Exo.MAST"


def _save_response(
    response: requests.Response,
    path: Path,
    manifest: RawDataManifest,
    *,
    planet_name: str,
    host_star: str,
    product_type: str,
    search_term: str,
) -> None:
    response.raise_for_status()
    save_artifact(
        manifest,
        path,
        response.content,
        source_name=SOURCE_NAME,
        source_url=response.url,
        planet_name=planet_name,
        host_star=host_star,
        file_type="json",
        product_type=product_type,
        query_or_search_term=search_term,
        notes="Unmodified JSON response returned by the public Exo.MAST API.",
    )


def collect_exomast(
    config: Any,
    session: requests.Session,
    manifest: RawDataManifest,
    logger: logging.Logger,
) -> None:
    logger.info("Starting Exo.MAST metadata collection")
    for planet in sorted(config.PLANETS, key=lambda item: item["priority"]):
        planet_name = planet["planet_name"]
        host_star = planet["host_star"]
        directory = config.RAW_DATA_DIR / "exomast" / safe_slug(planet_name)
        directory.mkdir(parents=True, exist_ok=True)
        outcomes: list[str] = []

        identifiers_url = (
            f"{config.EXOMAST_API_BASE_URL}/exoplanets/identifiers/"
        )
        identifiers_path = directory / "identifiers.json"
        identifiers: dict[str, Any] = {}
        try:
            if identifiers_path.exists():
                identifiers = json.loads(identifiers_path.read_text(encoding="utf-8"))
                manifest.record_artifact(
                    path=identifiers_path,
                    created=False,
                    source_name=SOURCE_NAME,
                    source_url=identifiers_url,
                    planet_name=planet_name,
                    host_star=host_star,
                    file_type="json",
                    product_type="planet_identifiers",
                    query_or_search_term=planet_name,
                )
                outcomes.append("identifiers: skipped_existing")
            else:
                response = session.get(
                    identifiers_url,
                    params={"name": planet_name},
                    timeout=config.REQUEST_TIMEOUT_SECONDS,
                )
                _save_response(
                    response,
                    identifiers_path,
                    manifest,
                    planet_name=planet_name,
                    host_star=host_star,
                    product_type="planet_identifiers",
                    search_term=planet_name,
                )
                identifiers = response.json()
                outcomes.append("identifiers: downloaded")
        except Exception as exc:
            outcomes.append(f"identifiers: failed ({exc})")
            register_error(
                manifest,
                logger,
                source_name=SOURCE_NAME,
                source_url=identifiers_url,
                planet_name=planet_name,
                host_star=host_star,
                product_type="planet_identifiers",
                query_or_search_term=planet_name,
                error=exc,
            )

        canonical_name = identifiers.get("canonicalName") or planet_name
        properties_url = (
            f"{config.EXOMAST_API_BASE_URL}/exoplanets/"
            f"{quote(str(canonical_name), safe='')}/properties"
        )
        properties_path = directory / "properties.json"
        try:
            if properties_path.exists():
                manifest.record_artifact(
                    path=properties_path,
                    created=False,
                    source_name=SOURCE_NAME,
                    source_url=properties_url,
                    planet_name=planet_name,
                    host_star=host_star,
                    file_type="json",
                    product_type="planet_properties",
                    query_or_search_term=str(canonical_name),
                )
                outcomes.append("properties: skipped_existing")
            else:
                response = session.get(
                    properties_url,
                    timeout=config.REQUEST_TIMEOUT_SECONDS,
                )
                _save_response(
                    response,
                    properties_path,
                    manifest,
                    planet_name=planet_name,
                    host_star=host_star,
                    product_type="planet_properties",
                    search_term=str(canonical_name),
                )
                outcomes.append("properties: downloaded")
        except Exception as exc:
            outcomes.append(f"properties: failed ({exc})")
            register_error(
                manifest,
                logger,
                source_name=SOURCE_NAME,
                source_url=properties_url,
                planet_name=planet_name,
                host_star=host_star,
                product_type="planet_properties",
                query_or_search_term=str(canonical_name),
                error=exc,
            )

        for archive, identifier_key in (("kepler", "keplerID"), ("tess", "tessID")):
            archive_id = identifiers.get(identifier_key)
            if archive_id in (None, ""):
                continue
            tces_url = (
                f"{config.EXOMAST_API_BASE_URL}/dvdata/{archive}/{archive_id}/tces/"
            )
            tces_path = directory / f"{archive}_tces.json"
            try:
                if tces_path.exists():
                    manifest.record_artifact(
                        path=tces_path,
                        created=False,
                        source_name=SOURCE_NAME,
                        source_url=tces_url,
                        planet_name=planet_name,
                        host_star=host_star,
                        file_type="json",
                        mission=archive.upper(),
                        product_type="tce_list",
                        query_or_search_term=str(archive_id),
                    )
                    outcomes.append(f"{archive} TCEs: skipped_existing")
                else:
                    response = session.get(
                        tces_url,
                        timeout=config.REQUEST_TIMEOUT_SECONDS,
                    )
                    _save_response(
                        response,
                        tces_path,
                        manifest,
                        planet_name=planet_name,
                        host_star=host_star,
                        product_type="tce_list",
                        search_term=str(archive_id),
                    )
                    outcomes.append(f"{archive} TCEs: downloaded")
            except Exception as exc:
                outcomes.append(f"{archive} TCEs: failed ({exc})")
                register_error(
                    manifest,
                    logger,
                    source_name=SOURCE_NAME,
                    source_url=tces_url,
                    planet_name=planet_name,
                    host_star=host_star,
                    mission=archive.upper(),
                    product_type="tce_list",
                    query_or_search_term=str(archive_id),
                    error=exc,
                )

        notes = (
            f"# Exo.MAST collection notes for {planet_name}\n\n"
            f"- Collected at (UTC): {utc_now()}\n"
            "- Role in this RAW pipeline: auxiliary resolver and target metadata.\n"
            "- Original mission light-curve FITS products are collected through "
            "MAST using Lightkurve or Astroquery.\n"
            f"- API documentation: https://exo.mast.stsci.edu/docs/\n"
            f"- Results: {'; '.join(outcomes) if outcomes else 'no endpoint result'}.\n"
        )
        notes_path = directory / "notes.md"
        created = atomic_write_text(notes_path, notes)
        manifest.record_artifact(
            path=notes_path,
            created=created,
            source_name=SOURCE_NAME,
            source_url="https://exo.mast.stsci.edu/docs/",
            planet_name=planet_name,
            host_star=host_star,
            file_type="md",
            product_type="collection_notes",
            query_or_search_term=planet_name,
        )
        logger.info("Exo.MAST processed planet: %s", planet_name)
    logger.info("Finished Exo.MAST metadata collection")
