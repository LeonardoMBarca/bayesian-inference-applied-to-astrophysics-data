"""Configuration for the local RAW astronomical data ingestion pipeline."""

from __future__ import annotations

from pathlib import Path

from project_config import pipeline_planets

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

PLANETS = pipeline_planets()

PREFERRED_MISSIONS = ("Kepler", "K2", "TESS")
MAX_LIGHTCURVES_PER_MISSION = 3
MAX_ASTROQUERY_PRODUCTS_PER_MISSION = 3
MAX_ETD_LIGHTCURVES_PER_PLANET = 5

NASA_TAP_SYNC_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
EXOMAST_API_BASE_URL = "https://exo.mast.stsci.edu/api/v0.1"
ETD_HOME_URL = "https://var.astro.cz/en/Home/ETD"
ETD_CATALOG_URL = "https://var.astro.cz/en/Exoplanets"

REQUEST_TIMEOUT_SECONDS = 60
ETD_REQUEST_DELAY_SECONDS = 2.0
HTTP_RETRY_COUNT = 3
HTTP_BACKOFF_FACTOR = 1.0
USER_AGENT = (
    "MBA-TCC-Raw-Astronomy-Ingestion/1.0 "
    "(Leonardo Moraes Barca; academic research; public data only)"
)

NASA_DESIRED_COLUMNS = (
    "pl_name",
    "hostname",
    "discoverymethod",
    "disc_facility",
    "pl_orbper",
    "pl_orbpererr1",
    "pl_orbpererr2",
    "pl_tranmid",
    "pl_tranmiderr1",
    "pl_tranmiderr2",
    "pl_trandur",
    "pl_trandurerr1",
    "pl_trandurerr2",
    "pl_trandep",
    "pl_trandeperr1",
    "pl_trandeperr2",
    "pl_rade",
    "pl_radeerr1",
    "pl_radeerr2",
    "pl_radj",
    "st_rad",
    "st_raderr1",
    "st_raderr2",
    "st_teff",
    "st_mass",
    "sy_dist",
    "rowupdate",
    "releasedate",
)

