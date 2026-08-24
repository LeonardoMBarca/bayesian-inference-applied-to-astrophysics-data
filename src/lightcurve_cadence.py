"""Pure helpers for explicit light-curve cadence and exposure metadata."""

from __future__ import annotations

import math
from pathlib import Path


KEPLER_SHORT_CADENCE_SECONDS = 58.84876
KEPLER_LONG_CADENCE_SECONDS = 1765.4632


def cadence_type(exposure_time_seconds: float) -> str:
    if exposure_time_seconds <= 0 or not math.isfinite(exposure_time_seconds):
        return "unknown"
    if exposure_time_seconds <= 120:
        return "short"
    if exposure_time_seconds >= 600:
        return "long"
    return "intermediate"


def infer_exposure_metadata(
    *,
    filename: str,
    timedel: object = None,
    median_time_delta_days: object = None,
) -> tuple[float, str, str]:
    """Return exposure seconds, cadence label, and evidence source.

    FITS ``TIMEDEL`` is preferred. Mission filename conventions are used for
    Kepler short/long cadence when the header omits it. A robust median time
    step is the final fallback and is explicitly labelled as an approximation.
    """

    try:
        value = float(timedel)
    except (TypeError, ValueError):
        value = math.nan
    if math.isfinite(value) and value > 0:
        seconds = value * 86_400.0 if value <= 1.5 else value
        return seconds, cadence_type(seconds), "FITS_TIMEDEL"

    lowered = Path(filename).name.lower()
    if "_slc" in lowered or "short-cadence" in lowered or "short_cadence" in lowered:
        return KEPLER_SHORT_CADENCE_SECONDS, "short", "KEPLER_FILENAME_SLC"
    if "_llc" in lowered or "long-cadence" in lowered or "long_cadence" in lowered:
        return KEPLER_LONG_CADENCE_SECONDS, "long", "KEPLER_FILENAME_LLC"

    try:
        delta = float(median_time_delta_days)
    except (TypeError, ValueError):
        delta = math.nan
    if math.isfinite(delta) and delta > 0:
        seconds = delta * 86_400.0
        return seconds, cadence_type(seconds), "MEDIAN_TIME_DELTA_APPROXIMATION"
    return math.nan, "unknown", "unavailable"
