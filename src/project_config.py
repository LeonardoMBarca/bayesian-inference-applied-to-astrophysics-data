"""Authoritative scientific target configuration for the supported pipeline.

Every executable layer imports target identity and target-specific physical
assumptions from this module.  Generated catalog values remain provenance
evidence; the values here define the supported, versioned workflow and are
checked against generated reference artifacts during validation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final, Literal


CadencePreference = Literal["short", "long", "any"]


def hours_to_days(hours: float) -> float:
    """Convert an explicitly hour-valued duration to days."""

    return float(hours) / 24.0


def percent_to_fraction(percent: float) -> float:
    """Convert percent units (one hundred means unity) to a fraction."""

    return float(percent) / 100.0


@dataclass(frozen=True, slots=True)
class TargetConfig:
    """Configuration shared by ingestion, Gold preparation, and M5."""

    planet_name: str
    host_star: str
    planet_slug: str
    mission: str
    priority: int
    orbital_period_days: float
    transit_midpoint_bjd: float
    transit_duration_hours: float
    transit_depth_percent: float
    planet_radius_earth: float
    stellar_radius_solar: float
    cadence_preference: CadencePreference
    phase_window_days: float = 0.15
    baseline_min_abs_phase_days: float = 0.08
    baseline_max_abs_phase_days: float = 0.15
    exposure_oversample: int = 15

    @property
    def transit_duration_days(self) -> float:
        return hours_to_days(self.transit_duration_hours)

    @property
    def transit_depth_fraction(self) -> float:
        return percent_to_fraction(self.transit_depth_percent)

    @property
    def reference_radius_ratio_from_depth(self) -> float:
        return self.transit_depth_fraction**0.5

    @property
    def source_gold_path(self) -> Path:
        return (
            Path("data")
            / "gold"
            / self.planet_slug
            / "modeling"
            / "transit_window_lightcurve.csv"
        )

    def pipeline_dict(self) -> dict[str, object]:
        """Return the stable target subset expected by legacy pipeline APIs."""

        return {
            "planet_name": self.planet_name,
            "host_star": self.host_star,
            "planet_slug": self.planet_slug,
            "priority": self.priority,
            "mission": self.mission,
            "cadence_preference": self.cadence_preference,
        }

    def metadata(self) -> dict[str, object]:
        """Serializable complete target metadata for generated artifacts."""

        payload = asdict(self)
        payload.update(
            {
                "transit_duration_days": self.transit_duration_days,
                "transit_depth_fraction": self.transit_depth_fraction,
                "reference_radius_ratio_from_depth": self.reference_radius_ratio_from_depth,
                "source_gold_path": self.source_gold_path.as_posix(),
            }
        )
        return payload


TARGETS: Final[tuple[TargetConfig, ...]] = (
    TargetConfig(
        planet_name="HAT-P-7 b",
        host_star="HAT-P-7",
        planet_slug="hat_p_7_b",
        mission="Kepler",
        priority=1,
        orbital_period_days=2.2047400,
        transit_midpoint_bjd=2454954.358572,
        transit_duration_hours=3.88216,
        transit_depth_percent=0.600000,
        planet_radius_earth=16.92559,
        stellar_radius_solar=2.0,
        cadence_preference="long",
        phase_window_days=0.30,
        baseline_min_abs_phase_days=0.20,
        baseline_max_abs_phase_days=0.30,
        exposure_oversample=15,
    ),
    TargetConfig(
        planet_name="Kepler-10 b",
        host_star="Kepler-10",
        planet_slug="kepler_10_b",
        mission="Kepler",
        priority=2,
        orbital_period_days=0.8374907,
        transit_midpoint_bjd=2455034.086870,
        transit_duration_hours=1.811,
        transit_depth_percent=0.019190,
        planet_radius_earth=1.47,
        stellar_radius_solar=1.065,
        cadence_preference="short",
        phase_window_days=0.15,
        baseline_min_abs_phase_days=0.08,
        baseline_max_abs_phase_days=0.15,
        exposure_oversample=15,
    ),
)

TARGETS_BY_SLUG: Final[dict[str, TargetConfig]] = {
    target.planet_slug: target for target in TARGETS
}
TARGETS_BY_NAME: Final[dict[str, TargetConfig]] = {
    target.planet_name: target for target in TARGETS
}
DEFAULT_TARGET_SLUG: Final[str] = "hat_p_7_b"
PRIMARY_GOLD_TARGET_SLUG: Final[str] = "kepler_10_b"
BACKUP_GOLD_TARGET_SLUG: Final[str] = "hat_p_7_b"
GOLD_DATASET_SCHEMA_VERSION: Final[str] = "gold-v2-segment-normalized"
M5_MODEL_VERSION: Final[str] = "m5-v2-exposure-integrated"
M5_DEFAULT_RUN_ID: Final[str] = "002_hardened"


def get_target(slug: str) -> TargetConfig:
    """Return a supported target or fail loudly with the accepted slugs."""

    try:
        return TARGETS_BY_SLUG[slug]
    except KeyError as exc:
        supported = ", ".join(sorted(TARGETS_BY_SLUG))
        raise ValueError(f"Unsupported target {slug!r}; expected one of: {supported}") from exc


def pipeline_planets() -> list[dict[str, object]]:
    """Return fresh dictionaries so layer-specific code cannot mutate config."""

    return [target.pipeline_dict() for target in TARGETS]
