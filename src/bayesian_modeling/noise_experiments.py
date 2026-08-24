"""Explicit deterministic generators for distinct noise experiment classes."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

import numpy as np
import pandas as pd

NoiseKind = Literal["white_gaussian", "deterministic_sinusoid", "correlated_ar1"]


@dataclass(frozen=True, slots=True)
class NoiseInjectionConfig:
    kind: NoiseKind
    amplitude_fraction: float
    seed: int = 42
    ar1_rho: float = 0.8
    sinusoid_period_days: float = 0.1

    def metadata(self) -> dict[str, object]:
        payload = asdict(self)
        payload["claim"] = {
            "white_gaussian": "independent stochastic white-noise injection",
            "deterministic_sinusoid": "deterministic systematic signal; not stochastic noise",
            "correlated_ar1": "stochastic correlated AR(1) injection within each segment",
        }[self.kind]
        return payload


def inject_noise(
    frame: pd.DataFrame,
    config: NoiseInjectionConfig,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Return a new array-backed frame; never mutate or alias the input flux."""

    required = {"segment_id", "time", "flux"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Noise injection missing columns: {missing}")
    if config.amplitude_fraction <= 0:
        raise ValueError("amplitude_fraction must be positive")
    if config.kind == "correlated_ar1" and not -1.0 < config.ar1_rho < 1.0:
        raise ValueError("ar1_rho must lie strictly between -1 and 1")
    if config.kind == "deterministic_sinusoid" and config.sinusoid_period_days <= 0:
        raise ValueError("sinusoid_period_days must be positive")
    output = frame.copy(deep=True)
    output["base_flux"] = pd.to_numeric(output["flux"], errors="coerce").to_numpy(copy=True)
    if output[["time", "base_flux"]].isna().any().any():
        raise ValueError("time and flux must be finite numeric values")
    injected = np.zeros(len(output), dtype=float)
    rng = np.random.default_rng(config.seed)
    # Positional indexes keep this correct for arbitrary DataFrame labels.
    for _, indexes in output.groupby("segment_id", sort=True).indices.items():
        positions = np.asarray(indexes, dtype=int)
        times = pd.to_numeric(output.iloc[positions]["time"], errors="coerce").to_numpy()
        order = np.argsort(times, kind="mergesort")
        ordered_positions = positions[order]
        size = len(ordered_positions)
        if config.kind == "white_gaussian":
            values = rng.normal(0.0, config.amplitude_fraction, size=size)
        elif config.kind == "deterministic_sinusoid":
            values = config.amplitude_fraction * np.sin(
                2.0 * np.pi * times[order] / config.sinusoid_period_days
            )
        elif config.kind == "correlated_ar1":
            innovations = rng.normal(
                0.0,
                config.amplitude_fraction * np.sqrt(1.0 - config.ar1_rho**2),
                size=size,
            )
            values = np.empty(size, dtype=float)
            values[0] = rng.normal(0.0, config.amplitude_fraction)
            for index in range(1, size):
                values[index] = config.ar1_rho * values[index - 1] + innovations[index]
        else:  # pragma: no cover - Literal plus argparse prevents this
            raise ValueError(f"Unsupported noise kind: {config.kind}")
        injected[ordered_positions] = values
    output["injected_component_fraction"] = injected
    output["flux"] = output["base_flux"].to_numpy(copy=True) + injected
    output["noise_injection_kind"] = config.kind
    output["noise_injection_seed"] = config.seed
    lag1_values = []
    for _, segment in output.sort_values("time").groupby("segment_id", sort=True):
        values = segment["injected_component_fraction"].to_numpy(dtype=float)
        if len(values) > 2 and np.std(values[:-1]) > 0 and np.std(values[1:]) > 0:
            lag1_values.append(float(np.corrcoef(values[:-1], values[1:])[0, 1]))
    metrics = {
        **config.metadata(),
        "row_count": len(output),
        "segment_count": int(output["segment_id"].nunique()),
        "injected_mean_fraction": float(injected.mean()),
        "injected_std_fraction": float(injected.std(ddof=1)),
        "median_segment_lag1_autocorrelation": (
            float(np.median(lag1_values)) if lag1_values else None
        ),
        "inference_status": "not_run",
        "correlated_likelihood_implemented_by_this_generator": False,
        "interpretation": (
            "This artifact validates injection mechanics only. M5's default likelihood "
            "contains independent white jitter and must not be described as recovering "
            "or modeling correlated noise."
        ),
    }
    return output, metrics
