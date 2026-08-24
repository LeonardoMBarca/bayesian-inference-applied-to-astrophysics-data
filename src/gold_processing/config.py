"""Configuration for the local GOLD data preparation pipeline."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

from project_config import (
    BACKUP_GOLD_TARGET_SLUG,
    GOLD_DATASET_SCHEMA_VERSION,
    PRIMARY_GOLD_TARGET_SLUG,
    TARGETS_BY_SLUG,
    pipeline_planets,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
SILVER_DATA_DIR = PROJECT_ROOT / "data" / "silver"
GOLD_DATA_DIR = PROJECT_ROOT / "data" / "gold"

SUPPORTED_TARGETS = pipeline_planets()
PRIMARY_CANDIDATE = TARGETS_BY_SLUG[PRIMARY_GOLD_TARGET_SLUG].pipeline_dict()
BACKUP_CANDIDATE = TARGETS_BY_SLUG[BACKUP_GOLD_TARGET_SLUG].pipeline_dict()
DATASET_SCHEMA_VERSION = GOLD_DATASET_SCHEMA_VERSION

PREFERRED_MISSIONS = ("Kepler", "TESS")
EXPECTED_MISSIONS = ("Kepler", "K2", "TESS")

PREFERRED_FLUX_COLUMN = "pdcsap_flux"
PREFERRED_FLUX_ERR_COLUMN = "pdcsap_flux_err"
FALLBACK_FLUX_COLUMN = "sap_flux"
FALLBACK_FLUX_ERR_COLUMN = "sap_flux_err"

QUALITY_GOOD_VALUE = 0

# Phase and transit-window policy.
TRANSIT_WINDOW_DURATION_MULTIPLIER = 3.0
TRANSIT_WINDOW_MIN_HALF_WIDTH_DAYS = 0.2
MAX_POINTS_PER_DATASET: int | None = None

SEGMENT_NORMALIZATION_METHOD = "out_of_transit_median"
SEGMENT_BASELINE_DURATION_MULTIPLIER = 1.5
SEGMENT_MIN_BASELINE_POINTS = 20
NORMALIZATION_POLICY = (
    "Quality-filtered flux is phase-folded with segment identity preserved, "
    "then divided by the out-of-transit median of each source FITS segment. "
    "No polynomial detrending is applied because PDCSAP_FLUX is already "
    "systematics-corrected; before/after segment diagnostics are persisted."
)

SILVER_PATHS = {
    "summary_by_planet": SILVER_DATA_DIR / "validation" / "silver_summary_by_planet.csv",
    "mast_quality_summary": SILVER_DATA_DIR / "validation" / "silver_mast_quality_summary.csv",
    "mast_fits_metadata": SILVER_DATA_DIR / "lightcurves" / "mast" / "mast_fits_metadata.csv",
    "nasa_pscomppars": SILVER_DATA_DIR / "catalogs" / "nasa" / "pscomppars_selected_planets.csv",
    "exomast_tces": SILVER_DATA_DIR / "catalogs" / "exomast" / "exomast_tces.csv",
    "etd_observations": SILVER_DATA_DIR / "etd" / "etd_observations.csv",
    "etd_lightcurve_metadata": SILVER_DATA_DIR / "etd" / "etd_lightcurve_metadata.csv",
}


def load_default_config() -> ModuleType:
    """Return this canonical configuration module for legacy callers."""

    return sys.modules[__name__]
