"""Paired, truth-blind preprocessing/configuration interventions for PUB-04.

No model copy, inference execution or gate relaxation lives here. All controls
start from the same supplied raw realization; normalization is estimated using
a fixed out-of-transit mask, never the simulator's hidden segment factors.
"""

from __future__ import annotations

import copy
import hashlib
from typing import Any, Mapping

import numpy as np
import pandas as pd

from publication.contracts import canonical_hash, deterministic_seed

INTERVENTIONS = frozenset({
    "baseline", "exposure_off", "global_normalization", "no_jitter",
    "strong_wrong_radius_prior", "invalid_input_hash", "dataset_identity_mismatch",
    "insufficient_sampling",
})


def frame_sha256(frame: pd.DataFrame) -> str:
    """Match the persisted inference CSV contract exactly, including LF endings."""
    return hashlib.sha256(frame.to_csv(index=False, float_format="%.17g", lineterminator="\n").encode("utf-8")).hexdigest()


def paired_generation_seed(experiment_id: str, pair_id: str, replicate_id: str) -> int:
    """Variants share one base realization, independently of their variant IDs."""
    return deterministic_seed(experiment_id, pair_id, replicate_id, stream="generation")


def estimate_normalization(frame: pd.DataFrame, *, method: str = "per_segment",
                            oot_min_abs_phase_days: float = 0.10,
                            min_oot_points: int = 3) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Estimate noisy OOT medians and scale flux/error consistently.

    The strict inequality ``abs(phase) > cutoff`` is protocol-defined, not
    selected from true duration, transit depth or fitted posteriors. Uncertainty
    in each estimated median is NOT propagated by M5; this is an explicit
    controlled limitation, common to the compared normalization variants.
    """
    if method not in {"per_segment", "global"}:
        raise ValueError("Normalization method must be per_segment or global")
    if not np.isfinite(oot_min_abs_phase_days) or oot_min_abs_phase_days <= 0:
        raise ValueError("The fixed OOT cutoff must be finite and positive")
    if isinstance(min_oot_points, bool) or not isinstance(min_oot_points, int) or min_oot_points < 1:
        raise ValueError("min_oot_points must be a positive integer")
    required = {"raw_flux", "raw_flux_err", "phase", "segment_id"}
    if not required.issubset(frame):
        raise ValueError(f"Raw empirical normalization requires {sorted(required - set(frame))}")
    if frame.empty or frame.segment_id.isna().any():
        raise ValueError("Nonempty data with complete segment identity are required")
    for column in ("raw_flux", "raw_flux_err", "phase"):
        values = frame[column].to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError(f"Nonfinite {column}")
        if column == "raw_flux_err" and np.any(values <= 0):
            raise ValueError("Measured raw errors must be positive")
    result = frame.copy(deep=True)
    flux = frame.raw_flux.to_numpy(dtype=float)
    error = frame.raw_flux_err.to_numpy(dtype=float)
    oot = np.abs(frame.phase.to_numpy(dtype=float)) > oot_min_abs_phase_days
    factors = np.empty(len(frame), dtype=float)
    groups = (frame.groupby("segment_id", sort=True).indices if method == "per_segment"
              else {"all_segments": np.arange(len(frame))})
    estimates = []
    for group, positions in groups.items():
        selected = positions[oot[positions]]
        if len(selected) < min_oot_points:
            raise ValueError(f"Insufficient predeclared OOT observations in {group!r}")
        median = float(np.median(flux[selected]))
        if not np.isfinite(median) or median <= 0:
            raise ValueError(f"Invalid empirical OOT median for {group!r}")
        factors[positions] = median
        estimates.append({"group": str(group), "oot_count": len(selected), "row_count": len(positions),
                          "raw_oot_median": median})
    result["normalized_flux"] = flux / factors
    result["normalized_flux_err"] = error / factors
    metadata = {"method": f"empirical_{method}_oot_median", "oot_rule": "abs(phase_days) > cutoff_days",
                "oot_cutoff_days": float(oot_min_abs_phase_days), "minimum_oot_count": min_oot_points,
                "estimated_factors": estimates, "source_frame_sha256": frame_sha256(frame),
                "output_frame_sha256": frame_sha256(result),
                "normalization_uncertainty_propagated": False,
                "truth_access": "none; raw observed flux and predeclared phase mask only"}
    result.attrs["normalization_metadata"] = metadata
    return result, metadata


def apply_ablation(frame: pd.DataFrame, base_inference_config: Mapping[str, Any],
                   intervention: str | Mapping[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Empirically normalize a common raw realization, then apply one intervention.

    Baseline and model-only variants produce BYTE-IDENTICAL input frames. Compare
    configuration differences to the returned ``baseline`` config, because all
    variants first replace the simulator's exact-calibration normalized columns
    with empirical OOT estimates and bind that resulting data identity.

    Persist ``frame.attrs['normalization_metadata']`` as preprocessing metadata;
    it is deliberately not an inference input or a CSV truth column.
    """
    specification = {"name": intervention} if isinstance(intervention, str) else dict(intervention)
    allowed = {"name", "oot_min_abs_phase_days", "min_oot_points"}
    if set(specification) - allowed:
        raise ValueError("Unknown intervention fields; declare a new protocol intervention explicitly")
    name = specification.get("name")
    if name not in INTERVENTIONS:
        raise ValueError(f"Unknown ablation: {name!r}")
    config = copy.deepcopy(dict(base_inference_config))
    if config.get("input_kind", "synthetic") != "synthetic":
        raise ValueError("PUB-04 helpers require explicitly synthetic controlled inputs")
    if config.get("radius_prior_uniform") is not None:
        raise ValueError("This protocol declares a LogNormal radius prior, not a Uniform prior")
    normalized, _ = estimate_normalization(
        frame, method="global" if name == "global_normalization" else "per_segment",
        oot_min_abs_phase_days=specification.get("oot_min_abs_phase_days", 0.10),
        min_oot_points=specification.get("min_oot_points", 3),
    )
    input_hash = frame_sha256(normalized)
    config.update(input_kind="synthetic", input_sha256=input_hash,
                  dataset_id=f"synthetic-{input_hash[:20]}", expected_dataset_id=f"synthetic-{input_hash[:20]}",
                  preprocessing_status="global_normalized_negative_control" if name == "global_normalization" else "segment_normalized")
    if name == "exposure_off":
        config["integrate_exposure"] = False
    elif name == "no_jitter":
        config["infer_jitter"] = False
    elif name == "strong_wrong_radius_prior":
        config["radius_prior_median"] = 0.025
        config["radius_prior_log_sigma"] = 0.01
    elif name == "invalid_input_hash":
        config["input_sha256"] = "0" * 64
    elif name == "dataset_identity_mismatch":
        config["expected_dataset_id"] += "-deliberate-mismatch"
    elif name == "insufficient_sampling":
        config["sampling"]["draws"] = 20
        config["sampling"]["tune"] = 20
    normalized.attrs["ablation"] = {"name": name, "specification_sha256": canonical_hash(specification),
                                   "inference_config_sha256": canonical_hash(config),
                                   "data_identity_deliberately_invalid": name in {"invalid_input_hash", "dataset_identity_mismatch"}}
    return normalized, config
