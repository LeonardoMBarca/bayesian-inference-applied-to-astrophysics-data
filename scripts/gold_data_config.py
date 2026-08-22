"""Configuration for the local GOLD data preparation pipeline."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
SILVER_DATA_DIR = PROJECT_ROOT / "data" / "silver"
GOLD_DATA_DIR = PROJECT_ROOT / "data" / "gold"

PRIMARY_CANDIDATE = {
    "planet_name": "HAT-P-7 b",
    "host_star": "HAT-P-7",
    "planet_slug": "hat_p_7_b",
}
BACKUP_CANDIDATE = {
    "planet_name": "TrES-2 b",
    "host_star": "TrES-2",
    "planet_slug": "tres_2_b",
}

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

NORMALIZATION_POLICY = (
    "No normalization is applied in this initial GOLD layer. Flux values are "
    "selected from PDCSAP_FLUX when available, with SAP_FLUX fallback only if "
    "the preferred column is not usable."
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
