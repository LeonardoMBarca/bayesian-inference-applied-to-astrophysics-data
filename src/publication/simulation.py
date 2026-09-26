"""Known-truth transit simulation, kept structurally separate from inference.

The physical primitive is shared with M5, not claimed as independent validation.
The generator uses a finer exposure quadrature by default; analytic and external
implementation checks are still required before a calibration claim is promoted.
No truth or noise-realization columns are added to the inference frame.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Any, Mapping

import numpy as np
import pandas as pd

SECONDS_PER_DAY = 86_400.0


@dataclass(frozen=True, slots=True)
class TransitTruth:
    """Circular-orbit generative parameters; ``a`` and ``r`` are in stellar radii."""

    r: float
    b: float
    a: float
    period_days: float
    t0: float = 0.0
    q1: float = 0.25
    q2: float = 0.3
    baseline: float = 1.0
    extra_sigma: float = 0.0

    def __post_init__(self) -> None:
        if any(not np.isfinite(value) for value in asdict(self).values()):
            raise ValueError("Truth values must all be finite")
        if not 0 < self.r < 1:
            raise ValueError("r must be strictly between 0 and 1")
        if not 0 <= self.b < 1 + self.r:
            raise ValueError("b must describe a transiting geometry: 0 <= b < 1+r")
        if self.a <= 1 + self.r:
            raise ValueError("a must exceed 1+r (a non-intersecting circular orbit)")
        if self.period_days <= 0 or self.baseline <= 0 or self.extra_sigma < 0:
            raise ValueError("period/baseline must be positive and jitter nonnegative")
        if not 0 <= self.q1 <= 1 or not 0 <= self.q2 <= 1:
            raise ValueError("Kipping q1 and q2 must lie in [0, 1]")

    @property
    def depth(self) -> float:
        """Geometric area ratio, NOT the observed limb-darkened transit depth."""
        return self.r**2

    @property
    def full_duration(self) -> float:
        """Circular first-to-fourth contact duration in days, before integration."""
        argument = np.sqrt(((1 + self.r) ** 2 - self.b**2) / (self.a**2 - self.b**2))
        return float(self.period_days / np.pi * np.arcsin(argument))

    def metadata(self) -> dict[str, float]:
        return {**asdict(self), "depth": self.depth, "full_duration": self.full_duration}


@lru_cache(maxsize=8)
def _compiled_signal(oversample: int):
    """Compile once per quadrature order, never once per synthetic replicate."""
    import exoplanet as xo
    import pytensor
    import pytensor.tensor as pt

    phase, exposure = pt.dvector("phase"), pt.dvector("exposure_days")
    r, b, a, period, t0, q1, q2, baseline = [
        pt.dscalar(name) for name in ("r", "b", "a", "period", "t0", "q1", "q2", "baseline")
    ]
    sqrt_q1 = pt.sqrt(q1)
    curve = xo.LimbDarkLightCurve(2 * sqrt_q1 * q2, sqrt_q1 * (1 - 2 * q2))
    orbit = xo.orbits.KeplerianOrbit(period=period, t0=t0, b=b, a=a)
    signal = baseline + curve.get_light_curve(
        orbit=orbit, r=r, t=phase, texp=exposure, oversample=oversample
    ).flatten()
    return pytensor.function([phase, exposure, r, b, a, period, t0, q1, q2, baseline], signal)


def physical_flux(
    phase_days: np.ndarray,
    exposure_seconds: float | np.ndarray,
    truth: TransitTruth | Mapping[str, float],
    *,
    oversample: int = 31,
) -> np.ndarray:
    """Evaluate the physical signal; zero exposure is allowed only for this helper.

    This is a simulator API, not a mechanism for initializing or constructing
    inference priors. Its configuration must not cross the inference boundary.
    """
    truth = truth if isinstance(truth, TransitTruth) else TransitTruth(**truth)
    phase = np.asarray(phase_days, dtype=float)
    if phase.ndim != 1 or not len(phase) or not np.isfinite(phase).all():
        raise ValueError("phase_days must be a nonempty finite one-dimensional array")
    if isinstance(oversample, bool) or not isinstance(oversample, int) or oversample < 1:
        raise ValueError("oversample must be a positive integer")
    if oversample % 2 != 1:
        raise ValueError("oversample must be odd to include the exposure center")
    exposure = np.broadcast_to(np.asarray(exposure_seconds, dtype=float), phase.shape).copy()
    if not np.isfinite(exposure).all() or (exposure < 0).any():
        raise ValueError("exposure_seconds must be finite and nonnegative")
    return np.asarray(
        _compiled_signal(oversample)(
            phase, exposure / SECONDS_PER_DAY, truth.r, truth.b, truth.a,
            truth.period_days, truth.t0, truth.q1, truth.q2, truth.baseline,
        ),
        dtype=float,
    )


def _positive_integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _normalize_design(design: Mapping[str, Any], truth: TransitTruth) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "segments": 1, "transits_per_segment": 1, "segment_gap_periods": 1,
        "oversample": 31, "heteroscedastic": True, "include_raw_flux": False,
        "noise": {"kind": "none"}, "systematic": None,
    }
    allowed = set(defaults) | {
        "window_days", "cadence_seconds", "measurement_sigma", "exposure_time_seconds",
        "segment_offsets", "cadence_phase_offsets",
    }
    if unknown := set(design) - allowed:
        raise ValueError(f"Unknown simulation design fields: {sorted(unknown)}")
    if missing := {"window_days", "cadence_seconds", "measurement_sigma"} - set(design):
        raise ValueError(f"Missing simulation design fields: {sorted(missing)}")
    # Copy nested values as well: callers may reuse a frozen protocol mapping.
    normalized = json.loads(json.dumps({**defaults, **design}, allow_nan=False))
    for key in ("segments", "transits_per_segment", "segment_gap_periods", "oversample"):
        _positive_integer(normalized[key], key)
    if normalized["oversample"] % 2 != 1:
        raise ValueError("oversample must be odd")
    normalized.setdefault("exposure_time_seconds", normalized["cadence_seconds"])
    for key in ("window_days", "cadence_seconds", "measurement_sigma", "exposure_time_seconds"):
        if not np.isfinite(normalized[key]) or normalized[key] <= 0:
            raise ValueError(f"{key} must be finite and positive")
    if normalized["exposure_time_seconds"] > normalized["cadence_seconds"]:
        raise ValueError("exposure_time_seconds cannot exceed the cadence")
    if normalized["window_days"] >= truth.period_days / 2:
        raise ValueError("window_days must be less than half the orbital period")
    if normalized["cadence_seconds"] / SECONDS_PER_DAY > 2 * normalized["window_days"]:
        raise ValueError("Cadence cannot exceed the full observing window")
    if abs(truth.t0) + truth.full_duration / 2 >= normalized["window_days"]:
        raise ValueError("The declared window must contain the complete instantaneous transit")
    for key in ("heteroscedastic", "include_raw_flux"):
        if not isinstance(normalized[key], bool):
            raise ValueError(f"{key} must be a boolean")
    count = normalized["segments"]
    normalized.setdefault("segment_offsets", [1.0] * count)
    normalized.setdefault("cadence_phase_offsets", [index / count for index in range(count)])
    for key in ("segment_offsets", "cadence_phase_offsets"):
        if len(normalized[key]) != count or not np.isfinite(normalized[key]).all():
            raise ValueError(f"{key} must contain one finite value per segment")
    if any(value <= 0 for value in normalized["segment_offsets"]):
        raise ValueError("segment_offsets are multiplicative positive flux factors")
    if any(not 0 <= value < 1 for value in normalized["cadence_phase_offsets"]):
        raise ValueError("cadence_phase_offsets must be in [0, 1) cadence units")
    noise = normalized["noise"]
    kind = noise.get("kind")
    if kind not in {"none", "ou", "ar1"}:
        raise ValueError("noise.kind must be none, ou or ar1")
    noise_fields = {"kind"} if kind == "none" else {"kind", "amplitude_fraction"}
    noise_fields |= {"timescale_days"} if kind == "ou" else {"rho"} if kind == "ar1" else set()
    if set(noise) != noise_fields:
        raise ValueError(f"noise fields for {kind!r} must be {sorted(noise_fields)}")
    if kind != "none":
        amplitude = noise["amplitude_fraction"]
        if not np.isfinite(amplitude) or amplitude < 0:
            raise ValueError("Correlated-noise amplitude must be finite and nonnegative")
    if kind == "ou" and (not np.isfinite(noise["timescale_days"]) or noise["timescale_days"] <= 0):
        raise ValueError("OU timescale_days must be finite and positive")
    if kind == "ar1" and not 0 <= noise["rho"] < 1:
        raise ValueError("AR(1) rho must lie in [0, 1)")
    systematic = normalized["systematic"]
    if systematic is not None:
        if set(systematic) - {"amplitude_fraction", "period_days", "phase_radians"}:
            raise ValueError("Unknown sinusoidal systematic fields")
        if not {"amplitude_fraction", "period_days"}.issubset(systematic):
            raise ValueError("Sinusoid requires amplitude_fraction and period_days")
        systematic.setdefault("phase_radians", 0.0)
        if not all(np.isfinite(value) for value in systematic.values()):
            raise ValueError("Sinusoid parameters must be finite")
        if systematic["amplitude_fraction"] < 0 or systematic["period_days"] <= 0:
            raise ValueError("Sinusoid amplitude must be nonnegative and period positive")
    return normalized


def _observation_grid(truth: TransitTruth, design: dict[str, Any]) -> pd.DataFrame:
    cadence_days = design["cadence_seconds"] / SECONDS_PER_DAY
    window = design["window_days"]
    segments = []
    for index in range(design["segments"]):
        origin = index * (design["transits_per_segment"] + design["segment_gap_periods"]) * truth.period_days
        start = -window + design["cadence_phase_offsets"][index] * cadence_days
        stop = (design["transits_per_segment"] - 1) * truth.period_days + window
        samples = int(np.floor((stop - start) / cadence_days + 1e-10)) + 1
        local_time = start + np.arange(samples, dtype=float) * cadence_days
        phase = (local_time + truth.period_days / 2) % truth.period_days - truth.period_days / 2
        # Observe real cadence windows rather than artificially phase-centering
        # every transit. Removed samples still count in correlation time gaps.
        keep = np.abs(phase) <= window + 1e-12
        segments.append(pd.DataFrame({
            "phase": phase[keep], "time": origin + local_time[keep],
            "exposure_time_seconds": design["exposure_time_seconds"],
            "segment_id": f"synthetic_segment_{index:03d}",
        }))
    return pd.concat(segments, ignore_index=True)


def simulate(
    truth: Mapping[str, float], design: Mapping[str, Any], seed: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Return an inference-only frame and a SEPARATE serializable truth artifact.

    ``cadence_seconds`` is actual spacing on each continuous segment's sampling
    clock. ``exposure_time_seconds`` is the physical integration width, not the
    count of numerical quadrature substeps. ``phase`` and ``time`` are in days.
    Segment offsets multiply both raw flux and its measured uncertainty. The
    returned normalized columns use the exact declared segment calibration;
    estimation error from empirical normalization is a separate ablation.

    Correlation is segment-local, stationary, and evolves over actual elapsed
    times including gaps between selected transit windows. A sinusoidal term is
    explicitly deterministic; no correlated likelihood is implied by injection.
    """
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    truth_config = TransitTruth(**truth)
    design_config = _normalize_design(design, truth_config)
    frame = _observation_grid(truth_config, design_config)
    n = len(frame)
    signal = physical_flux(
        frame["phase"].to_numpy(), frame["exposure_time_seconds"].to_numpy(),
        truth_config, oversample=design_config["oversample"],
    )
    error_multiplier = np.ones(n)
    if design_config["heteroscedastic"]:
        for positions in frame.groupby("segment_id", sort=True).indices.values():
            error_multiplier[positions] = np.linspace(0.8, 1.2, len(positions))
    measured_sigma = design_config["measurement_sigma"] * error_multiplier
    generators = [np.random.default_rng(child) for child in np.random.SeedSequence(seed).spawn(3)]
    measurement_noise = generators[0].normal(0, measured_sigma)
    jitter = generators[1].normal(0, truth_config.extra_sigma, size=n)
    correlated = np.zeros(n)
    noise = design_config["noise"]
    if noise["kind"] != "none":
        amplitude = noise["amplitude_fraction"]
        for positions in frame.groupby("segment_id", sort=True).indices.values():
            times = frame.iloc[positions]["time"].to_numpy()
            innovations = generators[2].normal(size=len(positions))
            values = np.empty(len(positions))
            values[0] = amplitude * innovations[0]
            for index, elapsed in enumerate(np.diff(times), start=1):
                if noise["kind"] == "ou":
                    rho = np.exp(-elapsed / noise["timescale_days"])
                else:
                    steps = round(elapsed * SECONDS_PER_DAY / design_config["cadence_seconds"])
                    rho = noise["rho"] ** steps
                values[index] = rho * values[index - 1] + amplitude * np.sqrt(1 - rho**2) * innovations[index]
            correlated[positions] = values
    systematic = np.zeros(n)
    if config := design_config["systematic"]:
        systematic = config["amplitude_fraction"] * np.sin(
            2 * np.pi * frame["time"].to_numpy() / config["period_days"] + config["phase_radians"]
        )
    frame["normalized_flux"] = signal + measurement_noise + jitter + correlated + systematic
    frame["normalized_flux_err"] = measured_sigma
    if design_config["include_raw_flux"]:
        factors = {
            f"synthetic_segment_{index:03d}": factor
            for index, factor in enumerate(design_config["segment_offsets"])
        }
        offsets = frame["segment_id"].map(factors).to_numpy()
        frame["raw_flux"] = frame["normalized_flux"].to_numpy() * offsets
        frame["raw_flux_err"] = measured_sigma * offsets
    truth_metadata = truth_config.metadata()
    truth_digest = hashlib.sha256(json.dumps(truth_metadata, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    csv_bytes = frame.to_csv(index=False, float_format="%.17g", lineterminator="\n").encode()
    metadata: dict[str, Any] = {
        "schema_version": "synthetic-transit-v1", "seed": seed,
        "random_generator": "numpy.PCG64; SeedSequence.spawn measurement/jitter/correlation streams",
        "truth": truth_metadata, "truth_sha256": truth_digest,
        "design": design_config, "row_count": n,
        "data_sha256": hashlib.sha256(csv_bytes).hexdigest(),
        "data_hash_encoding": "UTF-8 CSV, index=False, float_format=%.17g, LF",
        "physical_primitive": "exoplanet.KeplerianOrbit+LimbDarkLightCurve; shared with M5",
        "normalization": "exact known multiplicative segment calibration; not estimated from noisy flux",
        "units": {"phase": "day", "time": "day relative to arbitrary epoch", "exposure_time_seconds": "second", "flux": "relative flux fraction"},
        "depth_semantics": "r**2 geometric area ratio, not observed limb-darkened depth",
        "components": {
            "physical_signal": signal.tolist(), "measurement_noise": measurement_noise.tolist(),
            "white_jitter": jitter.tolist(), "correlated_stochastic": correlated.tolist(),
            "deterministic_systematic": systematic.tolist(),
        },
    }
    return frame, metadata
