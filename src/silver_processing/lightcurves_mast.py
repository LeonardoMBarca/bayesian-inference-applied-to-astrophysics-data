"""MAST/Lightkurve FITS extraction for SILVER light-curve tables."""

from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from astropy.io import fits

from lightcurve_cadence import infer_exposure_metadata

from .manifests import SilverManifest
from .utils import (
    atomic_write_dataframe,
    get_raw_info,
    planet_by_slug,
    relative_path,
    sha256_file,
    utc_now,
)

MAST_METADATA_COLUMNS = (
    "planet_name",
    "host_star",
    "planet_slug",
    "mission",
    "source_name",
    "source_fits_file",
    "source_raw_path",
    "source_raw_sha256",
    "source_raw_file_name",
    "file_size_bytes",
    "sha256",
    "hdu_count",
    "hdu_name",
    "hdu_index",
    "extracted_rows",
    "available_columns",
    "missing_preferred_columns",
    "time_min",
    "time_max",
    "quality_zero_count",
    "quality_nonzero_count",
    "quality_missing_count",
    "has_pdcsap_flux",
    "has_sap_flux",
    "telescope",
    "instrument",
    "object",
    "quarter",
    "sector",
    "campaign",
    "camera",
    "ccd",
    "time_unit",
    "time_reference",
    "cadence_type",
    "exposure_time_seconds",
    "exposure_time_source",
    "tstart",
    "tstop",
    "date_obs",
    "date_end",
    "data_origin",
    "status",
    "error_message",
)


def build_mast_lightcurves(
    *,
    config: Any,
    raw_manifest: pd.DataFrame,
    raw_lookup: dict[str, dict[str, str]],
    manifest: SilverManifest,
    logger: logging.Logger,
) -> dict[str, Any]:
    """Extract tabular light curves from downloaded MAST FITS files."""

    logger.info("Building MAST FITS SILVER light curves")
    created_at = utc_now()
    fits_files = _discover_fits_files(config, raw_manifest)
    logger.info("Discovered MAST FITS files for SILVER extraction: %s", len(fits_files))

    grouped_curves: dict[tuple[str, str], list[pd.DataFrame]] = defaultdict(list)
    metadata_rows: list[dict[str, Any]] = []

    for fits_path in fits_files:
        planet, mission_slug = _infer_context_from_path(config, fits_path)
        mission = _mission_label(mission_slug)
        raw_info = get_raw_info(fits_path, config, raw_lookup)
        try:
            curve, metadata = _extract_one_fits(
                config=config,
                path=fits_path,
                planet=planet,
                mission=mission,
                mission_slug=mission_slug,
                raw_info=raw_info,
                created_at=created_at,
            )
            metadata_rows.append(metadata)
            if not curve.empty:
                grouped_curves[(planet["planet_slug"], mission_slug)].append(curve)
            logger.info(
                "MAST FITS processed: planet=%s mission=%s rows=%s file=%s",
                planet["planet_slug"],
                mission_slug,
                len(curve),
                fits_path.name,
            )
        except Exception as exc:
            logger.exception("Failed to extract MAST FITS file: %s", fits_path)
            metadata_rows.append(
                _failed_metadata_row(
                    config=config,
                    path=fits_path,
                    planet=planet,
                    mission=mission,
                    raw_info=raw_info,
                    error_message=str(exc),
                )
            )
            manifest.add_failure(
                source_raw_path=relative_path(fits_path, config.PROJECT_ROOT),
                source_name=raw_info["source_name"] or "MAST / Lightkurve",
                planet_name=planet["planet_name"],
                host_star=planet["host_star"],
                mission=mission,
                raw_file_type="fits",
                transformation_type="mast_fits_lightcurve_extraction",
                error_message=str(exc),
            )

    output_paths: list[Path] = []
    for planet_slug in [planet["planet_slug"] for planet in config.PLANETS]:
        for mission_slug in config.MISSION_SLUGS:
            rows = grouped_curves.get((planet_slug, mission_slug), [])
            if not rows:
                continue
            curve = pd.concat(rows, ignore_index=True)
            curve = curve.reindex(columns=config.FITS_OUTPUT_COLUMNS)
            path = (
                config.SILVER_DATA_DIR
                / "lightcurves"
                / "mast"
                / planet_slug
                / f"{mission_slug}_lightcurve.csv"
            )
            atomic_write_dataframe(path, curve)
            output_paths.append(path)
            planet = planet_by_slug(config)[planet_slug]
            manifest.add_artifact(
                path=path,
                source_name="MAST / Lightkurve",
                planet_name=planet["planet_name"],
                host_star=planet["host_star"],
                mission=_mission_label(mission_slug),
                raw_file_type="fits",
                transformation_type="mast_fits_to_silver_lightcurve",
                row_count=len(curve),
                column_count=len(curve.columns),
                notes="Concatenated raw FITS table rows for one planet and mission; no quality filtering or normalization.",
            )

    metadata = pd.DataFrame(metadata_rows, columns=MAST_METADATA_COLUMNS)
    metadata_path = config.SILVER_DATA_DIR / "lightcurves" / "mast" / "mast_fits_metadata.csv"
    atomic_write_dataframe(metadata_path, metadata)
    manifest.add_artifact(
        path=metadata_path,
        source_name="MAST / Lightkurve",
        raw_file_type="fits",
        transformation_type="mast_fits_metadata",
        row_count=len(metadata),
        column_count=len(metadata.columns),
        notes="One metadata and extraction-status row per MAST FITS file.",
    )
    logger.info(
        "MAST SILVER extraction finished: fits=%s curve_tables=%s metadata_rows=%s",
        len(fits_files),
        len(output_paths),
        len(metadata),
    )
    return {"fits_count": len(fits_files), "curve_paths": output_paths, "metadata": metadata}


def _discover_fits_files(config: Any, raw_manifest: pd.DataFrame) -> list[Path]:
    candidates: set[Path] = set()
    if "local_path" in raw_manifest.columns:
        for local_path in raw_manifest["local_path"].fillna("").astype(str):
            if not local_path.lower().endswith((".fits", ".fits.gz")):
                continue
            path = config.PROJECT_ROOT / local_path
            if path.exists() and "data/raw/mast/lightkurve" in str(path):
                candidates.add(path)
    if not candidates:
        candidates.update((config.RAW_DATA_DIR / "mast" / "lightkurve").rglob("*.fits"))
        candidates.update((config.RAW_DATA_DIR / "mast" / "lightkurve").rglob("*.fits.gz"))
    return sorted(candidates)


def _infer_context_from_path(config: Any, path: Path) -> tuple[dict[str, Any], str]:
    parts = path.parts
    slug = ""
    mission_slug = ""
    if "lightkurve" in parts:
        index = parts.index("lightkurve")
        if len(parts) > index + 1:
            slug = parts[index + 1]
        if len(parts) > index + 2:
            mission_slug = parts[index + 2].lower()
    planets = planet_by_slug(config)
    planet = planets.get(slug)
    if planet is None:
        planet = {
            "planet_name": "",
            "host_star": "",
            "planet_slug": slug or "unknown",
            "priority": 999,
        }
    if mission_slug not in config.MISSION_SLUGS:
        mission_slug = mission_slug or "unknown"
    return planet, mission_slug


def _mission_label(mission_slug: str) -> str:
    mapping = {"kepler": "Kepler", "k2": "K2", "tess": "TESS"}
    return mapping.get(mission_slug.lower(), mission_slug)


def _extract_one_fits(
    *,
    config: Any,
    path: Path,
    planet: dict[str, Any],
    mission: str,
    mission_slug: str,
    raw_info: dict[str, str],
    created_at: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    with fits.open(path, memmap=True) as hdul:
        hdu_index = _find_lightcurve_hdu_index(hdul)
        if hdu_index is None:
            raise ValueError("No tabular light-curve HDU with TIME-like data was found")
        hdu = hdul[hdu_index]
        primary_header = hdul[0].header if hdul else {}
        header = hdu.header
        names = list(hdu.columns.names or [])
        row_count = len(hdu.data) if hdu.data is not None else 0
        columns_upper = {name.upper(): name for name in names}

        time_values = _column_values(hdu, columns_upper, "TIME", row_count)
        quality_values = _quality_values(hdu, columns_upper, row_count)
        sap_flux = _column_values(hdu, columns_upper, "SAP_FLUX", row_count)
        pdcsap_flux = _column_values(hdu, columns_upper, "PDCSAP_FLUX", row_count)
        time_numeric = pd.to_numeric(time_values, errors="coerce")
        quality_numeric = pd.to_numeric(quality_values, errors="coerce")
        sap_numeric = pd.to_numeric(sap_flux, errors="coerce")
        pdcsap_numeric = pd.to_numeric(pdcsap_flux, errors="coerce")
        finite_times = np.sort(time_numeric.dropna().to_numpy(dtype=float))
        positive_deltas = np.diff(finite_times)
        positive_deltas = positive_deltas[positive_deltas > 0]
        median_time_delta_days = (
            float(np.median(positive_deltas)) if positive_deltas.size else None
        )
        exposure_time_seconds, cadence_label, exposure_source = infer_exposure_metadata(
            filename=path.name,
            timedel=_header_get(header, primary_header, "TIMEDEL"),
            median_time_delta_days=median_time_delta_days,
        )

        data_origin = _header_get(header, primary_header, "AUTHOR") or _header_get(
            header, primary_header, "CREATOR"
        )
        metadata_values = {
            "time_unit": _header_get(header, primary_header, "TIMEUNIT"),
            "time_reference": _time_reference(header, primary_header),
            "quarter": _header_get(header, primary_header, "QUARTER"),
            "sector": _header_get(header, primary_header, "SECTOR"),
            "campaign": _header_get(header, primary_header, "CAMPAIGN"),
            "camera": _header_get(header, primary_header, "CAMERA"),
            "ccd": _header_get(header, primary_header, "CCD"),
            "object": _header_get(header, primary_header, "OBJECT"),
            "telescope": _header_get(header, primary_header, "TELESCOP"),
            "instrument": _header_get(header, primary_header, "INSTRUME"),
            "data_origin": data_origin,
        }

        curve = pd.DataFrame(
            {
                "planet_name": planet["planet_name"],
                "host_star": planet["host_star"],
                "planet_slug": planet["planet_slug"],
                "source_name": raw_info["source_name"] or "MAST / Lightkurve",
                "source_raw_path": raw_info["source_raw_path"],
                "source_raw_sha256": raw_info["source_raw_sha256"],
                "source_raw_file_name": raw_info["source_raw_file_name"],
                "mission": mission,
                "source_fits_file": path.name,
                "hdu_name": getattr(hdu, "name", "") or header.get("EXTNAME", ""),
                "hdu_index": hdu_index,
                "time": time_values,
                "time_unit": metadata_values["time_unit"],
                "time_reference": metadata_values["time_reference"],
                "cadence_type": cadence_label,
                "exposure_time_seconds": exposure_time_seconds,
                "exposure_time_source": exposure_source,
                "sap_flux": sap_flux,
                "sap_flux_err": _column_values(hdu, columns_upper, "SAP_FLUX_ERR", row_count),
                "pdcsap_flux": pdcsap_flux,
                "pdcsap_flux_err": _column_values(
                    hdu,
                    columns_upper,
                    "PDCSAP_FLUX_ERR",
                    row_count,
                ),
                "quality": quality_values,
                "cadence_number": _column_values(hdu, columns_upper, "CADENCENO", row_count),
                "mom_centr1": _column_values(hdu, columns_upper, "MOM_CENTR1", row_count),
                "mom_centr2": _column_values(hdu, columns_upper, "MOM_CENTR2", row_count),
                "pos_corr1": _column_values(hdu, columns_upper, "POS_CORR1", row_count),
                "pos_corr2": _column_values(hdu, columns_upper, "POS_CORR2", row_count),
                "quarter": metadata_values["quarter"],
                "sector": metadata_values["sector"],
                "campaign": metadata_values["campaign"],
                "camera": metadata_values["camera"],
                "ccd": metadata_values["ccd"],
                "object": metadata_values["object"],
                "telescope": metadata_values["telescope"],
                "instrument": metadata_values["instrument"],
                "data_origin": metadata_values["data_origin"],
                "quality_is_zero": quality_numeric == 0,
                "quality_is_missing": quality_numeric.isna(),
                "has_pdcsap_flux": pdcsap_numeric.notna(),
                "has_sap_flux": sap_numeric.notna(),
                "silver_created_at_utc": created_at,
            }
        )
        curve = curve.reindex(columns=config.FITS_OUTPUT_COLUMNS)

        missing_preferred = [
            column for column in config.FITS_PREFERRED_COLUMNS if column not in columns_upper
        ]
        metadata = {
            "planet_name": planet["planet_name"],
            "host_star": planet["host_star"],
            "planet_slug": planet["planet_slug"],
            "mission": mission,
            "source_name": raw_info["source_name"] or "MAST / Lightkurve",
            "source_fits_file": path.name,
            "source_raw_path": raw_info["source_raw_path"],
            "source_raw_sha256": raw_info["source_raw_sha256"],
            "source_raw_file_name": raw_info["source_raw_file_name"],
            "file_size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "hdu_count": len(hdul),
            "hdu_name": getattr(hdu, "name", "") or header.get("EXTNAME", ""),
            "hdu_index": hdu_index,
            "extracted_rows": row_count,
            "available_columns": "|".join(names),
            "missing_preferred_columns": "|".join(missing_preferred),
            "time_min": time_numeric.min() if time_numeric.notna().any() else "",
            "time_max": time_numeric.max() if time_numeric.notna().any() else "",
            "quality_zero_count": int((quality_numeric == 0).sum()),
            "quality_nonzero_count": int(((quality_numeric != 0) & quality_numeric.notna()).sum()),
            "quality_missing_count": int(quality_numeric.isna().sum()),
            "has_pdcsap_flux": bool(pdcsap_numeric.notna().any()),
            "has_sap_flux": bool(sap_numeric.notna().any()),
            "telescope": metadata_values["telescope"],
            "instrument": metadata_values["instrument"],
            "object": metadata_values["object"],
            "quarter": metadata_values["quarter"],
            "sector": metadata_values["sector"],
            "campaign": metadata_values["campaign"],
            "camera": metadata_values["camera"],
            "ccd": metadata_values["ccd"],
            "time_unit": metadata_values["time_unit"],
            "time_reference": metadata_values["time_reference"],
            "cadence_type": cadence_label,
            "exposure_time_seconds": exposure_time_seconds,
            "exposure_time_source": exposure_source,
            "tstart": _header_get(header, primary_header, "TSTART"),
            "tstop": _header_get(header, primary_header, "TSTOP"),
            "date_obs": _header_get(header, primary_header, "DATE-OBS"),
            "date_end": _header_get(header, primary_header, "DATE-END"),
            "data_origin": metadata_values["data_origin"],
            "status": "created",
            "error_message": "",
        }
        return curve, metadata


def _find_lightcurve_hdu_index(hdul: fits.HDUList) -> int | None:
    fallback: int | None = None
    for index, hdu in enumerate(hdul):
        if not isinstance(hdu, fits.BinTableHDU):
            continue
        names = {name.upper() for name in (hdu.columns.names or [])}
        if "TIME" in names and ({"SAP_FLUX", "PDCSAP_FLUX", "FLUX"} & names):
            return index
        if "TIME" in names and fallback is None:
            fallback = index
    return fallback


def _column_values(
    hdu: fits.BinTableHDU,
    columns_upper: dict[str, str],
    preferred_column: str,
    row_count: int,
) -> pd.Series:
    column_name = columns_upper.get(preferred_column.upper())
    if not column_name:
        return pd.Series([pd.NA] * row_count)
    return pd.Series(np.asarray(hdu.data[column_name]))


def _quality_values(
    hdu: fits.BinTableHDU,
    columns_upper: dict[str, str],
    row_count: int,
) -> pd.Series:
    if "QUALITY" in columns_upper:
        return _column_values(hdu, columns_upper, "QUALITY", row_count)
    if "SAP_QUALITY" in columns_upper:
        return _column_values(hdu, columns_upper, "SAP_QUALITY", row_count)
    return pd.Series([pd.NA] * row_count)


def _header_get(header: Any, primary_header: Any, key: str) -> Any:
    value = header.get(key)
    if value in (None, ""):
        value = primary_header.get(key)
    return "" if value is None else value


def _time_reference(header: Any, primary_header: Any) -> str:
    timesys = _header_get(header, primary_header, "TIMESYS")
    bjdrefi = _header_get(header, primary_header, "BJDREFI")
    bjdreff = _header_get(header, primary_header, "BJDREFF")
    parts = []
    if timesys:
        parts.append(f"TIMESYS={timesys}")
    if bjdrefi != "" or bjdreff != "":
        parts.append(f"BJDREFI={bjdrefi}")
        parts.append(f"BJDREFF={bjdreff}")
    return ";".join(parts)


def _failed_metadata_row(
    *,
    config: Any,
    path: Path,
    planet: dict[str, Any],
    mission: str,
    raw_info: dict[str, str],
    error_message: str,
) -> dict[str, Any]:
    row = {
        "planet_name": planet["planet_name"],
        "host_star": planet["host_star"],
        "planet_slug": planet["planet_slug"],
        "mission": mission,
        "source_name": raw_info["source_name"] or "MAST / Lightkurve",
        "source_fits_file": path.name,
        "source_raw_path": relative_path(path, config.PROJECT_ROOT),
        "source_raw_sha256": raw_info["source_raw_sha256"],
        "source_raw_file_name": path.name,
        "file_size_bytes": path.stat().st_size if path.exists() else "",
        "sha256": sha256_file(path) if path.exists() else "",
        "hdu_count": "",
        "hdu_name": "",
        "hdu_index": "",
        "extracted_rows": 0,
        "available_columns": "",
        "missing_preferred_columns": "",
        "time_min": "",
        "time_max": "",
        "quality_zero_count": 0,
        "quality_nonzero_count": 0,
        "quality_missing_count": 0,
        "has_pdcsap_flux": False,
        "has_sap_flux": False,
        "telescope": "",
        "instrument": "",
        "object": "",
        "quarter": "",
        "sector": "",
        "campaign": "",
        "camera": "",
        "ccd": "",
        "time_unit": "",
        "time_reference": "",
        "cadence_type": "unknown",
        "exposure_time_seconds": "",
        "exposure_time_source": "unavailable",
        "tstart": "",
        "tstop": "",
        "date_obs": "",
        "date_end": "",
        "data_origin": "",
        "status": "failed",
        "error_message": error_message,
    }
    return row
