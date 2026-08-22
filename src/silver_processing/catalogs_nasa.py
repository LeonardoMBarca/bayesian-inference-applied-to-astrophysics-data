"""NASA Exoplanet Archive catalog consolidation for SILVER."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from .manifests import SilverManifest
from .utils import (
    atomic_write_dataframe,
    get_raw_info,
    sorted_planets,
    utc_now,
)


NASA_PSCOMPPARS_COLUMN_MAP = {
    "pl_name": "planet_name",
    "hostname": "host_star",
    "discoverymethod": "discovery_method",
    "disc_facility": "discovery_facility",
    "pl_orbper": "orbital_period_days",
    "pl_orbpererr1": "orbital_period_err_plus",
    "pl_orbpererr2": "orbital_period_err_minus",
    "pl_tranmid": "transit_midpoint",
    "pl_tranmiderr1": "transit_midpoint_err_plus",
    "pl_tranmiderr2": "transit_midpoint_err_minus",
    "pl_trandur": "transit_duration_hours",
    "pl_trandurerr1": "transit_duration_err_plus",
    "pl_trandurerr2": "transit_duration_err_minus",
    "pl_trandep": "transit_depth",
    "pl_trandeperr1": "transit_depth_err_plus",
    "pl_trandeperr2": "transit_depth_err_minus",
    "pl_rade": "planet_radius_earth",
    "pl_radeerr1": "planet_radius_earth_err_plus",
    "pl_radeerr2": "planet_radius_earth_err_minus",
    "pl_radj": "planet_radius_jupiter",
    "st_rad": "stellar_radius_solar",
    "st_raderr1": "stellar_radius_solar_err_plus",
    "st_raderr2": "stellar_radius_solar_err_minus",
    "st_teff": "stellar_teff",
    "st_mass": "stellar_mass_solar",
    "sy_dist": "system_distance_pc",
}

PSCOMPPARS_OUTPUT_COLUMNS = (
    "planet_name",
    "host_star",
    "planet_slug",
    "discovery_method",
    "discovery_facility",
    "orbital_period_days",
    "orbital_period_err_plus",
    "orbital_period_err_minus",
    "transit_midpoint",
    "transit_midpoint_err_plus",
    "transit_midpoint_err_minus",
    "transit_duration_hours",
    "transit_duration_err_plus",
    "transit_duration_err_minus",
    "transit_depth",
    "transit_depth_err_plus",
    "transit_depth_err_minus",
    "planet_radius_earth",
    "planet_radius_earth_err_plus",
    "planet_radius_earth_err_minus",
    "planet_radius_jupiter",
    "stellar_radius_solar",
    "stellar_radius_solar_err_plus",
    "stellar_radius_solar_err_minus",
    "stellar_teff",
    "stellar_mass_solar",
    "system_distance_pc",
    "source_name",
    "source_raw_path",
    "source_raw_sha256",
    "source_raw_file_name",
    "silver_created_at_utc",
)


def build_nasa_catalogs(
    *,
    config: Any,
    raw_lookup: dict[str, dict[str, str]],
    manifest: SilverManifest,
    logger: logging.Logger,
) -> dict[str, pd.DataFrame]:
    """Build SILVER NASA catalog tables."""

    logger.info("Building NASA SILVER catalogs")
    output_dir = config.SILVER_DATA_DIR / "catalogs" / "nasa"
    created_at = utc_now()

    pscomppars_rows: list[pd.DataFrame] = []
    ps_rows: list[pd.DataFrame] = []

    for planet in sorted_planets(config):
        slug = planet["planet_slug"]
        pscomppars_path = (
            config.RAW_DATA_DIR
            / "nasa_exoplanet_archive"
            / "pscomppars"
            / slug
            / "response.csv"
        )
        ps_path = (
            config.RAW_DATA_DIR
            / "nasa_exoplanet_archive"
            / "ps"
            / slug
            / "response.csv"
        )

        try:
            if pscomppars_path.exists():
                raw = pd.read_csv(pscomppars_path, dtype=str).fillna("")
                standardized = _standardize_pscomppars(
                    raw=raw,
                    planet=planet,
                    raw_path=pscomppars_path,
                    raw_lookup=raw_lookup,
                    config=config,
                    created_at=created_at,
                )
                pscomppars_rows.append(standardized)
                logger.info("NASA pscomppars processed for %s: rows=%s", slug, len(raw))
            else:
                message = f"NASA pscomppars response not found: {pscomppars_path}"
                logger.warning(message)
                manifest.add_failure(
                    source_name="NASA Exoplanet Archive",
                    planet_name=planet["planet_name"],
                    host_star=planet["host_star"],
                    transformation_type="nasa_pscomppars_selected_planets",
                    error_message=message,
                )
        except Exception as exc:
            logger.exception("Failed to process NASA pscomppars for %s", slug)
            manifest.add_failure(
                source_raw_path=str(pscomppars_path),
                source_name="NASA Exoplanet Archive",
                planet_name=planet["planet_name"],
                host_star=planet["host_star"],
                raw_file_type="csv",
                transformation_type="nasa_pscomppars_selected_planets",
                error_message=str(exc),
            )

        try:
            if ps_path.exists():
                raw = pd.read_csv(ps_path, dtype=str).fillna("")
                raw_info = get_raw_info(ps_path, config, raw_lookup)
                raw.insert(0, "solution_row_index", range(len(raw)))
                raw.insert(0, "planet_slug", slug)
                raw.insert(0, "host_star", planet["host_star"])
                raw.insert(0, "planet_name", planet["planet_name"])
                raw["source_name"] = raw_info["source_name"] or "NASA Exoplanet Archive"
                raw["source_raw_path"] = raw_info["source_raw_path"]
                raw["source_raw_sha256"] = raw_info["source_raw_sha256"]
                raw["source_raw_file_name"] = raw_info["source_raw_file_name"]
                raw["silver_created_at_utc"] = created_at
                ps_rows.append(raw)
                logger.info("NASA ps processed for %s: rows=%s", slug, len(raw))
            else:
                message = f"NASA ps response not found: {ps_path}"
                logger.warning(message)
                manifest.add_failure(
                    source_name="NASA Exoplanet Archive",
                    planet_name=planet["planet_name"],
                    host_star=planet["host_star"],
                    transformation_type="nasa_ps_all_solutions",
                    error_message=message,
                )
        except Exception as exc:
            logger.exception("Failed to process NASA ps for %s", slug)
            manifest.add_failure(
                source_raw_path=str(ps_path),
                source_name="NASA Exoplanet Archive",
                planet_name=planet["planet_name"],
                host_star=planet["host_star"],
                raw_file_type="csv",
                transformation_type="nasa_ps_all_solutions",
                error_message=str(exc),
            )

    pscomppars = (
        pd.concat(pscomppars_rows, ignore_index=True)
        if pscomppars_rows
        else pd.DataFrame(columns=PSCOMPPARS_OUTPUT_COLUMNS)
    )
    pscomppars = pscomppars.reindex(columns=PSCOMPPARS_OUTPUT_COLUMNS)
    pscomppars_path = output_dir / "pscomppars_selected_planets.csv"
    atomic_write_dataframe(pscomppars_path, pscomppars)
    manifest.add_artifact(
        path=pscomppars_path,
        source_name="NASA Exoplanet Archive",
        transformation_type="nasa_pscomppars_selected_planets",
        row_count=len(pscomppars),
        column_count=len(pscomppars.columns),
        notes="One standardized pscomppars row per configured planet when available.",
    )

    ps_all = pd.concat(ps_rows, ignore_index=True) if ps_rows else pd.DataFrame()
    ps_all_path = output_dir / "ps_all_solutions.csv"
    atomic_write_dataframe(ps_all_path, ps_all)
    manifest.add_artifact(
        path=ps_all_path,
        source_name="NASA Exoplanet Archive",
        transformation_type="nasa_ps_all_solutions",
        row_count=len(ps_all),
        column_count=len(ps_all.columns),
        notes="All NASA ps rows for configured planets, with solution_row_index; no best-solution selection.",
    )

    snapshot = _build_transiting_snapshot(config, raw_lookup, created_at, logger)
    snapshot_path = output_dir / "all_transiting_planets_snapshot.csv"
    atomic_write_dataframe(snapshot_path, snapshot)
    manifest.add_artifact(
        path=snapshot_path,
        source_name="NASA Exoplanet Archive",
        transformation_type="nasa_all_transiting_planets_snapshot",
        row_count=len(snapshot),
        column_count=len(snapshot.columns),
        notes="RAW transiting-planet snapshot copied to SILVER with provenance columns only.",
    )

    logger.info(
        "NASA SILVER catalogs finished: pscomppars=%s ps=%s snapshot=%s",
        len(pscomppars),
        len(ps_all),
        len(snapshot),
    )
    return {
        "pscomppars_selected_planets": pscomppars,
        "ps_all_solutions": ps_all,
        "all_transiting_planets_snapshot": snapshot,
    }


def _standardize_pscomppars(
    *,
    raw: pd.DataFrame,
    planet: dict[str, Any],
    raw_path: Any,
    raw_lookup: dict[str, dict[str, str]],
    config: Any,
    created_at: str,
) -> pd.DataFrame:
    raw_info = get_raw_info(raw_path, config, raw_lookup)
    output = pd.DataFrame()
    for raw_column, silver_column in NASA_PSCOMPPARS_COLUMN_MAP.items():
        output[silver_column] = raw[raw_column] if raw_column in raw.columns else pd.NA

    output["planet_name"] = output["planet_name"].replace("", pd.NA).fillna(planet["planet_name"])
    output["host_star"] = output["host_star"].replace("", pd.NA).fillna(planet["host_star"])
    output.insert(2, "planet_slug", planet["planet_slug"])
    output["source_name"] = raw_info["source_name"] or "NASA Exoplanet Archive"
    output["source_raw_path"] = raw_info["source_raw_path"]
    output["source_raw_sha256"] = raw_info["source_raw_sha256"]
    output["source_raw_file_name"] = raw_info["source_raw_file_name"]
    output["silver_created_at_utc"] = created_at
    return output


def _build_transiting_snapshot(
    config: Any,
    raw_lookup: dict[str, dict[str, str]],
    created_at: str,
    logger: logging.Logger,
) -> pd.DataFrame:
    path = (
        config.RAW_DATA_DIR
        / "nasa_exoplanet_archive"
        / "pscomppars"
        / "all_transiting_planets_snapshot.csv"
    )
    if not path.exists():
        logger.warning("NASA all_transiting_planets_snapshot not found: %s", path)
        return pd.DataFrame()
    snapshot = pd.read_csv(path, dtype=str, low_memory=False).fillna("")
    raw_info = get_raw_info(path, config, raw_lookup)
    snapshot["source_name"] = raw_info["source_name"] or "NASA Exoplanet Archive"
    snapshot["source_raw_path"] = raw_info["source_raw_path"]
    snapshot["source_raw_sha256"] = raw_info["source_raw_sha256"]
    snapshot["source_raw_file_name"] = raw_info["source_raw_file_name"]
    snapshot["silver_created_at_utc"] = created_at
    return snapshot
