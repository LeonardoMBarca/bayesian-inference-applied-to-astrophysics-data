"""Collect original light-curve products from MAST via Lightkurve/Astroquery."""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

from lightcurve_selection import product_ranking

from .utils import (
    RawDataManifest,
    atomic_write_json,
    csv_bytes,
    register_error,
    safe_slug,
    save_artifact,
    sha256_file,
    utc_now,
)


LIGHTKURVE_SOURCE = "MAST / Lightkurve"
ASTROQUERY_SOURCE = "MAST / Astroquery"
SEARCH_COLUMNS = (
    "mission",
    "year",
    "author",
    "exptime",
    "target_name",
    "distance",
    "productFilename",
    "dataURI",
)
DOWNLOAD_MANIFEST_COLUMNS = (
    "collected_at_utc",
    "planet_name",
    "host_star",
    "mission",
    "author",
    "target_name",
    "product_filename",
    "data_uri",
    "exptime_seconds",
    "cadence_preference",
    "local_path",
    "status",
    "error_message",
    "sha256",
    "file_size_bytes",
)


def _astropy_table_bytes(table: Any) -> bytes:
    output = io.StringIO(newline="")
    table.write(output, format="ascii.csv")
    return output.getvalue().encode("utf-8")


def _mast_download_url(data_uri: str) -> str:
    if not data_uri:
        return "https://mast.stsci.edu/"
    return (
        "https://mast.stsci.edu/api/v0.1/Download/file?uri="
        f"{quote(data_uri, safe=':/')}"
    )


def _value(table: Any, column: str, index: int) -> str:
    if column not in table.colnames:
        return ""
    value = table[column][index]
    if getattr(value, "mask", False):
        return ""
    return str(value)


def _preferred_indexes(
    table: Any,
    limit: int,
    cadence_preference: str = "any",
) -> list[int]:
    def ranking(index: int) -> tuple[int, int, float, int]:
        author = _value(table, "author", index)
        try:
            exptime = float(_value(table, "exptime", index))
        except ValueError:
            exptime = 0.0
        return product_ranking(
            author=author,
            exposure_time_seconds=exptime,
            index=index,
            cadence_preference=cadence_preference,
        )

    return sorted(range(len(table)), key=ranking)[:limit]


def _find_downloaded_path(lightcurve: Any, directory: Path) -> Path | None:
    if lightcurve is None:
        return None
    filename = getattr(lightcurve, "filename", None)
    if filename:
        candidate = Path(filename)
        if candidate.is_file():
            return candidate
    fits_files = sorted(directory.rglob("*.fits"), key=lambda path: path.stat().st_mtime)
    return fits_files[-1] if fits_files else None


def _save_lightkurve_metadata(
    metadata_path: Path,
    payload: dict[str, Any],
    manifest: RawDataManifest,
    *,
    planet_name: str,
    host_star: str,
    mission: str,
    search_term: str,
) -> None:
    created = atomic_write_json(metadata_path, payload)
    manifest.record_artifact(
        path=metadata_path,
        created=created,
        source_name=LIGHTKURVE_SOURCE,
        source_url="https://mast.stsci.edu/",
        planet_name=planet_name,
        host_star=host_star,
        file_type="json",
        mission=mission,
        product_type="search_metadata",
        query_or_search_term=search_term,
    )


def _collect_lightkurve_mission(
    config: Any,
    manifest: RawDataManifest,
    logger: logging.Logger,
    planet: dict[str, Any],
    mission: str,
) -> bool:
    """Return True when Astroquery fallback should be attempted."""
    planet_name = planet["planet_name"]
    host_star = planet["host_star"]
    mission_slug = safe_slug(mission)
    directory = (
        config.RAW_DATA_DIR
        / "mast"
        / "lightkurve"
        / safe_slug(planet_name)
        / mission_slug
    )
    directory.mkdir(parents=True, exist_ok=True)
    search_path = directory / "search_results.csv"
    cadence_preference = str(planet.get("cadence_preference", "any"))
    policy_id = f"cadence_{safe_slug(cadence_preference)}_v2"
    download_manifest_path = directory / f"download_manifest_{policy_id}.csv"
    metadata_path = directory / f"metadata_{policy_id}.json"
    search_term = f'target="{host_star}", mission="{mission}"'

    if download_manifest_path.exists() and search_path.exists():
        logger.info(
            "Lightkurve %s/%s skipped (complete manifest exists)",
            planet_name,
            mission,
        )
        for path, product_type in (
            (search_path, "search_results"),
            (download_manifest_path, "download_manifest"),
            (metadata_path, "search_metadata"),
        ):
            if path.exists():
                manifest.record_artifact(
                    path=path,
                    created=False,
                    source_name=LIGHTKURVE_SOURCE,
                    source_url="https://mast.stsci.edu/",
                    planet_name=planet_name,
                    host_star=host_star,
                    file_type=path.suffix.lstrip("."),
                    mission=mission,
                    product_type=product_type,
                    query_or_search_term=search_term,
                )
        for fits_path in directory.rglob("*.fits"):
            manifest.record_artifact(
                path=fits_path,
                created=False,
                source_name=LIGHTKURVE_SOURCE,
                source_url="https://mast.stsci.edu/",
                planet_name=planet_name,
                host_star=host_star,
                file_type="fits",
                mission=mission,
                product_type="light_curve",
                query_or_search_term=search_term,
            )
        return False

    try:
        import lightkurve as lk
    except ImportError as exc:
        empty_search = csv_bytes([], SEARCH_COLUMNS)
        save_artifact(
            manifest,
            search_path,
            empty_search,
            source_name=LIGHTKURVE_SOURCE,
            source_url="https://mast.stsci.edu/",
            planet_name=planet_name,
            host_star=host_star,
            file_type="csv",
            mission=mission,
            product_type="search_results",
            query_or_search_term=search_term,
            notes="Empty result file because Lightkurve is not installed.",
        )
        _save_lightkurve_metadata(
            metadata_path,
            {
                "collected_at_utc": utc_now(),
                "planet_name": planet_name,
                "host_star": host_star,
                "mission": mission,
                "search_term": search_term,
                "status": "failed",
                "error": str(exc),
            },
            manifest,
            planet_name=planet_name,
            host_star=host_star,
            mission=mission,
            search_term=search_term,
        )
        register_error(
            manifest,
            logger,
            source_name=LIGHTKURVE_SOURCE,
            source_url="https://mast.stsci.edu/",
            planet_name=planet_name,
            host_star=host_star,
            mission=mission,
            product_type="light_curve_search",
            query_or_search_term=search_term,
            error=exc,
        )
        return True

    try:
        search_result = lk.search_lightcurve(host_star, mission=mission)
        table = search_result.table
        save_artifact(
            manifest,
            search_path,
            _astropy_table_bytes(table),
            source_name=LIGHTKURVE_SOURCE,
            source_url="https://mast.stsci.edu/",
            planet_name=planet_name,
            host_star=host_star,
            file_type="csv",
            mission=mission,
            product_type="search_results",
            query_or_search_term=search_term,
            notes="Full Lightkurve search result table; no analytical processing applied.",
        )
        logger.info(
            "Lightkurve search %s/%s returned %d products",
            planet_name,
            mission,
            len(table),
        )
    except Exception as exc:
        if not search_path.exists():
            save_artifact(
                manifest,
                search_path,
                csv_bytes([], SEARCH_COLUMNS),
                source_name=LIGHTKURVE_SOURCE,
                source_url="https://mast.stsci.edu/",
                planet_name=planet_name,
                host_star=host_star,
                file_type="csv",
                mission=mission,
                product_type="search_results",
                query_or_search_term=search_term,
                notes="Empty result file because the Lightkurve search failed.",
            )
        _save_lightkurve_metadata(
            metadata_path,
            {
                "collected_at_utc": utc_now(),
                "planet_name": planet_name,
                "host_star": host_star,
                "mission": mission,
                "search_term": search_term,
                "status": "failed",
                "error": str(exc),
            },
            manifest,
            planet_name=planet_name,
            host_star=host_star,
            mission=mission,
            search_term=search_term,
        )
        register_error(
            manifest,
            logger,
            source_name=LIGHTKURVE_SOURCE,
            source_url="https://mast.stsci.edu/",
            planet_name=planet_name,
            host_star=host_star,
            mission=mission,
            product_type="light_curve_search",
            query_or_search_term=search_term,
            error=exc,
        )
        return True

    download_rows: list[dict[str, Any]] = []
    selected_indexes = _preferred_indexes(
        table,
        config.MAX_LIGHTCURVES_PER_MISSION,
        cadence_preference,
    )
    any_download_failed = False
    for index in selected_indexes:
        author = _value(table, "author", index)
        target_name = _value(table, "target_name", index)
        product_filename = _value(table, "productFilename", index)
        data_uri = _value(table, "dataURI", index)
        try:
            exptime_seconds = float(_value(table, "exptime", index))
        except ValueError:
            exptime_seconds = 0.0
        source_url = _mast_download_url(data_uri)
        try:
            lightcurve = search_result[index].download(
                download_dir=str(directory),
                quality_bitmask="default",
            )
            downloaded_path = _find_downloaded_path(lightcurve, directory)
            if downloaded_path is None:
                raise RuntimeError(
                    f"Lightkurve returned no local FITS path for {product_filename}"
                )
            manifest.add(
                source_name=LIGHTKURVE_SOURCE,
                source_url=source_url,
                planet_name=planet_name,
                host_star=host_star,
                path=downloaded_path,
                file_type="fits",
                mission=mission,
                product_type="light_curve",
                query_or_search_term=search_term,
                status="downloaded_or_cached",
                notes=(
                    f"MAST author={author}; exptime={exptime_seconds}; "
                    f"cadence_preference={cadence_preference}; original archive FITS product."
                ),
            )
            download_rows.append(
                {
                    "collected_at_utc": utc_now(),
                    "planet_name": planet_name,
                    "host_star": host_star,
                    "mission": mission,
                    "author": author,
                    "target_name": target_name,
                    "product_filename": product_filename or downloaded_path.name,
                    "data_uri": data_uri,
                    "exptime_seconds": exptime_seconds,
                    "cadence_preference": cadence_preference,
                    "local_path": (
                        downloaded_path.resolve().relative_to(
                            config.PROJECT_ROOT.resolve()
                        ).as_posix()
                    ),
                    "status": "downloaded_or_cached",
                    "error_message": "",
                    "sha256": sha256_file(downloaded_path),
                    "file_size_bytes": downloaded_path.stat().st_size,
                }
            )
            logger.info(
                "Lightkurve FITS available: %s/%s/%s",
                planet_name,
                mission,
                downloaded_path.name,
            )
        except Exception as exc:
            any_download_failed = True
            register_error(
                manifest,
                logger,
                source_name=LIGHTKURVE_SOURCE,
                source_url=source_url,
                planet_name=planet_name,
                host_star=host_star,
                mission=mission,
                product_type="light_curve",
                query_or_search_term=search_term,
                error=exc,
                notes=f"author={author}; product={product_filename}",
            )
            download_rows.append(
                {
                    "collected_at_utc": utc_now(),
                    "planet_name": planet_name,
                    "host_star": host_star,
                    "mission": mission,
                    "author": author,
                    "target_name": target_name,
                    "product_filename": product_filename,
                    "data_uri": data_uri,
                    "exptime_seconds": exptime_seconds,
                    "cadence_preference": cadence_preference,
                    "local_path": "",
                    "status": "failed",
                    "error_message": str(exc),
                    "sha256": "",
                    "file_size_bytes": "",
                }
            )

    download_manifest_created = save_artifact(
        manifest,
        download_manifest_path,
        csv_bytes(download_rows, DOWNLOAD_MANIFEST_COLUMNS),
        source_name=LIGHTKURVE_SOURCE,
        source_url="https://mast.stsci.edu/",
        planet_name=planet_name,
        host_star=host_star,
        file_type="csv",
        mission=mission,
        product_type="download_manifest",
        query_or_search_term=search_term,
    )
    status = "completed"
    if not selected_indexes:
        status = "no_results"
    elif any_download_failed:
        status = "completed_with_errors"
    _save_lightkurve_metadata(
        metadata_path,
        {
            "collected_at_utc": utc_now(),
            "planet_name": planet_name,
            "host_star": host_star,
            "mission": mission,
            "search_term": search_term,
            "search_result_count": len(table),
            "selected_product_count": len(selected_indexes),
            "download_limit": config.MAX_LIGHTCURVES_PER_MISSION,
            "cadence_preference": cadence_preference,
            "download_manifest_created": download_manifest_created,
            "status": status,
            "selection_policy": (
                "Prefer official SPOC/Kepler/K2 authors, then the target-specific "
                "cadence preference, capped per planet and mission."
            ),
        },
        manifest,
        planet_name=planet_name,
        host_star=host_star,
        mission=mission,
        search_term=search_term,
    )
    return any_download_failed


def _collect_astroquery_fallback(
    config: Any,
    manifest: RawDataManifest,
    logger: logging.Logger,
    planet: dict[str, Any],
    mission: str,
) -> None:
    planet_name = planet["planet_name"]
    host_star = planet["host_star"]
    directory = (
        config.RAW_DATA_DIR
        / "mast"
        / "astroquery"
        / safe_slug(planet_name)
        / safe_slug(mission)
    )
    directory.mkdir(parents=True, exist_ok=True)
    search_term = f'query_object("{host_star}"); obs_collection="{mission}"'

    try:
        from astroquery.mast import Observations
    except ImportError as exc:
        register_error(
            manifest,
            logger,
            source_name=ASTROQUERY_SOURCE,
            source_url="https://mast.stsci.edu/",
            planet_name=planet_name,
            host_star=host_star,
            mission=mission,
            product_type="fallback_search",
            query_or_search_term=search_term,
            error=exc,
        )
        return

    try:
        observations = Observations.query_object(host_star, radius="0.002 deg")
        if "obs_collection" in observations.colnames:
            mission_mask = [
                str(value).strip().lower() == mission.lower()
                for value in observations["obs_collection"]
            ]
            observations = observations[mission_mask]
        observations_path = directory / "observations_query.csv"
        save_artifact(
            manifest,
            observations_path,
            _astropy_table_bytes(observations),
            source_name=ASTROQUERY_SOURCE,
            source_url="https://mast.stsci.edu/",
            planet_name=planet_name,
            host_star=host_star,
            file_type="csv",
            mission=mission,
            product_type="observations_query",
            query_or_search_term=search_term,
        )

        products = Observations.get_product_list(observations)
        products_path = directory / "products_available.csv"
        save_artifact(
            manifest,
            products_path,
            _astropy_table_bytes(products),
            source_name=ASTROQUERY_SOURCE,
            source_url="https://mast.stsci.edu/",
            planet_name=planet_name,
            host_star=host_star,
            file_type="csv",
            mission=mission,
            product_type="products_available",
            query_or_search_term=search_term,
        )

        selected_indexes: list[int] = []
        for index in range(len(products)):
            filename = _value(products, "productFilename", index).lower()
            subgroup = _value(products, "productSubGroupDescription", index).upper()
            extension = _value(products, "extension", index).lower()
            is_fits = extension == "fits" or filename.endswith((".fits", ".fits.gz"))
            is_lightcurve = subgroup in {"LC", "LLC"} or filename.endswith(
                ("_lc.fits", "_llc.fits", "_lc.fits.gz", "_llc.fits.gz")
            )
            if is_fits and is_lightcurve:
                selected_indexes.append(index)
            if len(selected_indexes) >= config.MAX_ASTROQUERY_PRODUCTS_PER_MISSION:
                break

        download_rows: list[dict[str, Any]] = []
        if selected_indexes:
            selected_products = products[selected_indexes]
            downloaded = Observations.download_products(
                selected_products,
                download_dir=str(directory),
                cache=True,
            )
            for row in downloaded:
                local_path = Path(str(row["Local Path"]))
                status = str(row["Status"])
                error_message = str(row["Message"])
                if local_path.is_file():
                    manifest.add(
                        source_name=ASTROQUERY_SOURCE,
                        source_url=str(row["URL"]),
                        planet_name=planet_name,
                        host_star=host_star,
                        path=local_path,
                        file_type="fits",
                        mission=mission,
                        product_type="light_curve",
                        query_or_search_term=search_term,
                        status=status.lower(),
                        notes="Original MAST FITS product downloaded by Astroquery fallback.",
                    )
                    checksum = sha256_file(local_path)
                    file_size = local_path.stat().st_size
                    relative = str(
                        local_path.resolve().relative_to(config.PROJECT_ROOT.resolve())
                    )
                else:
                    checksum = ""
                    file_size = ""
                    relative = str(local_path)
                download_rows.append(
                    {
                        "collected_at_utc": utc_now(),
                        "planet_name": planet_name,
                        "host_star": host_star,
                        "mission": mission,
                        "author": "",
                        "target_name": "",
                        "product_filename": local_path.name,
                        "data_uri": str(row["URL"]),
                        "local_path": relative,
                        "status": status,
                        "error_message": error_message,
                        "sha256": checksum,
                        "file_size_bytes": file_size,
                    }
                )

        fallback_manifest_path = directory / "download_manifest.csv"
        save_artifact(
            manifest,
            fallback_manifest_path,
            csv_bytes(download_rows, DOWNLOAD_MANIFEST_COLUMNS),
            source_name=ASTROQUERY_SOURCE,
            source_url="https://mast.stsci.edu/",
            planet_name=planet_name,
            host_star=host_star,
            file_type="csv",
            mission=mission,
            product_type="download_manifest",
            query_or_search_term=search_term,
        )
        logger.info(
            "Astroquery fallback %s/%s: %d observations, %d selected products",
            planet_name,
            mission,
            len(observations),
            len(selected_indexes),
        )
    except Exception as exc:
        register_error(
            manifest,
            logger,
            source_name=ASTROQUERY_SOURCE,
            source_url="https://mast.stsci.edu/",
            planet_name=planet_name,
            host_star=host_star,
            mission=mission,
            product_type="fallback_search_or_download",
            query_or_search_term=search_term,
            error=exc,
        )


def collect_mast_lightcurves(
    config: Any,
    session: requests.Session,
    manifest: RawDataManifest,
    logger: logging.Logger,
) -> None:
    del session  # Lightkurve and Astroquery manage their own archive sessions.
    logger.info("Starting MAST light-curve collection")
    for planet in sorted(config.PLANETS, key=lambda item: item["priority"]):
        logger.info("MAST processing planet: %s", planet["planet_name"])
        for mission in config.PREFERRED_MISSIONS:
            fallback_needed = _collect_lightkurve_mission(
                config,
                manifest,
                logger,
                planet,
                mission,
            )
            if fallback_needed:
                _collect_astroquery_fallback(
                    config,
                    manifest,
                    logger,
                    planet,
                    mission,
                )
    logger.info("Finished MAST light-curve collection")
