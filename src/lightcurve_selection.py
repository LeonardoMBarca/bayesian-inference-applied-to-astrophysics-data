"""Pure ranking policy for mission light-curve products."""

from __future__ import annotations


AUTHOR_PRIORITY = {
    "SPOC": 0,
    "Kepler": 0,
    "K2": 0,
    "TESS-SPOC": 1,
    "QLP": 2,
    "TASOC": 3,
    "PATHOS": 4,
    "CDIPS": 5,
}


def product_ranking(
    *,
    author: str,
    exposure_time_seconds: float,
    index: int,
    cadence_preference: str,
) -> tuple[int, int, float, int]:
    """Rank by authoritative producer, then explicit cadence preference."""

    exposure = exposure_time_seconds if exposure_time_seconds > 0 else 0.0
    if cadence_preference == "short":
        cadence_bucket = 0 if 0 < exposure <= 120 else 1 if exposure <= 600 else 2
        exposure_order = exposure
    elif cadence_preference == "long":
        cadence_bucket = 0 if exposure >= 600 else 1 if exposure > 120 else 2
        exposure_order = -exposure
    else:
        cadence_bucket = 0 if exposure > 0 else 1
        exposure_order = -exposure
    return AUTHOR_PRIORITY.get(author, 50), cadence_bucket, exposure_order, index
