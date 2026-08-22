"""Pipeline orchestration shared by all command-line entry points."""

from __future__ import annotations

import logging
from typing import Any, Iterable

from .etd import collect_etd_varastro
from .exomast import collect_exomast
from .mast import collect_mast_lightcurves
from .nasa_exoplanet_archive import collect_nasa_exoplanet_archive
from .utils import (
    RawDataManifest,
    build_http_session,
    ensure_raw_directories,
    setup_logging,
    utc_now,
)


COLLECTORS = {
    "nasa": collect_nasa_exoplanet_archive,
    "mast": collect_mast_lightcurves,
    "exomast": collect_exomast,
    "etd": collect_etd_varastro,
}


def run_pipeline(config: Any, sources: Iterable[str]) -> int:
    ensure_raw_directories(config.RAW_DATA_DIR)
    logger = setup_logging(
        config.RAW_DATA_DIR / "_logs" / "download_raw_data.log"
    )
    manifest = RawDataManifest(config.RAW_DATA_DIR, config.PROJECT_ROOT)
    session = build_http_session(config)
    requested_sources = list(sources)

    logger.info(
        "RAW pipeline started at %s | sources=%s",
        utc_now(),
        ",".join(requested_sources),
    )
    failures = 0
    try:
        for source in requested_sources:
            collector = COLLECTORS[source]
            try:
                collector(config, session, manifest, logger)
            except Exception:
                failures += 1
                logger.exception("Unhandled source-level failure: %s", source)
            finally:
                manifest.flush()
    finally:
        session.close()
        manifest.flush()
        logger.info(
            "RAW pipeline finished at %s | source_level_failures=%d",
            utc_now(),
            failures,
        )
    return 1 if failures else 0

