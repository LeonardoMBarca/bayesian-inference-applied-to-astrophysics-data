"""Configuration for the local SILVER data processing pipeline."""

from __future__ import annotations

from pathlib import Path

from project_config import pipeline_planets


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
SILVER_DATA_DIR = PROJECT_ROOT / "data" / "silver"
RAW_MANIFEST_PATH = RAW_DATA_DIR / "_manifests" / "raw_data_current_state.csv"
RAW_EVENT_LOG_PATH = RAW_DATA_DIR / "_manifests" / "raw_data_manifest.csv"

PLANETS = pipeline_planets()

EXPECTED_MISSIONS = ("Kepler", "K2", "TESS")
MISSION_SLUGS = ("kepler", "k2", "tess")

FITS_PREFERRED_COLUMNS = (
    "TIME",
    "SAP_FLUX",
    "SAP_FLUX_ERR",
    "PDCSAP_FLUX",
    "PDCSAP_FLUX_ERR",
    "QUALITY",
    "SAP_QUALITY",
    "CADENCENO",
    "MOM_CENTR1",
    "MOM_CENTR2",
    "POS_CORR1",
    "POS_CORR2",
)

FITS_OUTPUT_COLUMNS = (
    "planet_name",
    "host_star",
    "planet_slug",
    "source_name",
    "source_raw_path",
    "source_raw_sha256",
    "source_raw_file_name",
    "mission",
    "source_fits_file",
    "hdu_name",
    "hdu_index",
    "time",
    "time_unit",
    "time_reference",
    "cadence_type",
    "exposure_time_seconds",
    "exposure_time_source",
    "sap_flux",
    "sap_flux_err",
    "pdcsap_flux",
    "pdcsap_flux_err",
    "quality",
    "cadence_number",
    "mom_centr1",
    "mom_centr2",
    "pos_corr1",
    "pos_corr2",
    "quarter",
    "sector",
    "campaign",
    "camera",
    "ccd",
    "object",
    "telescope",
    "instrument",
    "data_origin",
    "quality_is_zero",
    "quality_is_missing",
    "has_pdcsap_flux",
    "has_sap_flux",
    "silver_created_at_utc",
)

QUALITY_FLAG_STRATEGY = (
    "Do not filter in Silver. Preserve QUALITY/SAP_QUALITY values and add "
    "quality_is_zero and quality_is_missing helper columns."
)
TIME_METADATA_STRATEGY = (
    "Preserve mission-provided TIME values. Record TIMEUNIT, TIMESYS, and "
    "BJDREFI+BJDREFF in metadata instead of converting to phase or absolute "
    "datetime in Silver."
)

STRICT_VALIDATION = False
INSPECTION_SAMPLE_ROW_LIMIT = 1000

