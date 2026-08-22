"""Orchestration for the local SILVER data processing pipeline."""

from __future__ import annotations

from typing import Any, Iterable

from .catalogs_exomast import build_exomast_catalogs
from .catalogs_nasa import build_nasa_catalogs
from .lightcurves_etd import build_etd_tables
from .lightcurves_mast import build_mast_lightcurves
from .manifests import SilverManifest
from .utils import (
    ensure_silver_directories,
    raw_manifest_lookup,
    read_raw_manifest,
    setup_logging,
)
from .validation import build_silver_validations, validate_raw_manifest


ALL_STEPS = (
    "raw_validation",
    "catalogs",
    "lightcurves",
    "etd",
    "silver_validation",
)


def run_pipeline(config: Any, steps: Iterable[str] = ALL_STEPS) -> dict[str, Any]:
    """Run selected SILVER pipeline steps."""

    selected_steps = tuple(steps)
    ensure_silver_directories(config.SILVER_DATA_DIR)
    logger = setup_logging(config.SILVER_DATA_DIR / "logs" / "build_silver_data.log")
    logger.info("SILVER pipeline started: steps=%s", ",".join(selected_steps))

    raw_manifest = read_raw_manifest(config)
    lookup = raw_manifest_lookup(raw_manifest)
    manifest = SilverManifest(config)
    results: dict[str, Any] = {
        "raw_manifest_records": len(raw_manifest),
        "raw_manifest_unique_paths": raw_manifest["local_path"].nunique()
        if "local_path" in raw_manifest.columns
        else 0,
    }

    try:
        if "raw_validation" in selected_steps:
            results["raw_validation"] = validate_raw_manifest(
                config=config,
                raw_manifest=raw_manifest,
                manifest=manifest,
                logger=logger,
            )
            manifest.flush()

        if "catalogs" in selected_steps:
            results["nasa"] = build_nasa_catalogs(
                config=config,
                raw_lookup=lookup,
                manifest=manifest,
                logger=logger,
            )
            results["exomast"] = build_exomast_catalogs(
                config=config,
                raw_lookup=lookup,
                manifest=manifest,
                logger=logger,
            )
            manifest.flush()

        if "lightcurves" in selected_steps:
            results["mast"] = build_mast_lightcurves(
                config=config,
                raw_manifest=raw_manifest,
                raw_lookup=lookup,
                manifest=manifest,
                logger=logger,
            )
            manifest.flush()

        if "etd" in selected_steps:
            results["etd"] = build_etd_tables(
                config=config,
                raw_lookup=lookup,
                manifest=manifest,
                logger=logger,
            )
            manifest.flush()

        if "silver_validation" in selected_steps:
            results["silver_validation"] = build_silver_validations(
                config=config,
                manifest=manifest,
                logger=logger,
            )
            manifest.flush()

    finally:
        manifest.flush()

    logger.info(
        "SILVER pipeline finished: manifest_rows=%s raw_manifest_records=%s",
        len(manifest.rows),
        len(raw_manifest),
    )
    return results
