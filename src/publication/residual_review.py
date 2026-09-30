"""Read-only selected-time/segment residual review; no refit or gate revision."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

VERSION = "observational-residual-review-v2"


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def corr(x, y):
    if len(x) < 4 or np.std(x) == 0 or np.std(y) == 0:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def verify_prediction_input(inputs: pd.DataFrame, curve: pd.DataFrame) -> None:
    """Time/segment identity alone does not identify the actually fitted flux."""
    if len(inputs) != len(curve) or not np.allclose(inputs.time, curve.time, atol=1e-10, rtol=0) or not np.allclose(inputs.phase, curve.phase, atol=1e-12, rtol=0):
        raise ValueError("Prediction rows/time/phase no longer match actual inference input")
    if not inputs.segment_id.equals(curve.segment_id):
        raise ValueError("Prediction segment identity differs")
    np.testing.assert_allclose(curve.observed, inputs.normalized_flux, atol=5e-15, rtol=0, equal_nan=False)
    np.testing.assert_allclose(curve.residual, curve.observed - curve.posterior_mean, atol=5e-15, rtol=0, equal_nan=False)


def segment_review(frame: pd.DataFrame, *, half_duration: float) -> dict:
    """Chronological diagnostics; masked lags never connect segments or gaps."""
    if frame.segment_id.nunique() != 1:
        raise ValueError("Expected exactly one segment")
    data = frame.sort_values("time", kind="stable")
    t, r = data.time.to_numpy(), data.residual.to_numpy()
    dt = np.diff(t)
    if len(dt) == 0 or np.any(dt <= 0):
        raise ValueError("Segment time must contain distinct chronological observations")
    exposure = float(data.exposure_time_seconds.median()) / 86400
    selected = float(np.median(dt))
    x = t - np.mean(t)
    slope = float(np.dot(x, r - r.mean()) / np.dot(x, x))
    detrended = r - np.mean(r) - slope * x
    in_transit = np.abs(data.phase.to_numpy()) <= half_duration
    rows = {}
    for label, mask in (("all", np.ones(len(data), dtype=bool)), ("in_transit", in_transit), ("out_of_transit", ~in_transit)):
        z = r[mask]
        pairs = mask[:-1] & mask[1:] & (dt <= 1.5 * selected)
        native_pairs = mask[:-1] & mask[1:] & (dt <= 1.5 * exposure)
        rows[label] = {"rows": int(mask.sum()), "median_residual": float(np.median(z)) if len(z) else None,
                       "rms": float(np.sqrt(np.mean(z**2))) if len(z) else None,
                       "selected_lag_pairs": int(pairs.sum()), "selected_lag1": corr(r[:-1][pairs], r[1:][pairs]),
                       "native_exposure_neighbor_pairs": int(native_pairs.sum()),
                       "native_exposure_neighbor_correlation": corr(r[:-1][native_pairs], r[1:][native_pairs]),
                       "selected_lag1_after_linear_trend_removal": corr(detrended[:-1][pairs], detrended[1:][pairs])}
    # Linearized shift of the existing template: diagnostic, not an ephemeris fit.
    order = np.argsort(data.phase.to_numpy(), kind="stable")
    phase = data.phase.to_numpy()[order]
    unique, inverse = np.unique(phase, return_inverse=True)
    template = data.posterior_mean.to_numpy()[order]
    means = np.bincount(inverse, weights=template) / np.bincount(inverse)
    derivative_sorted = np.interp(phase, unique, np.gradient(means, unique))
    derivative = np.empty(len(data))
    derivative[order] = derivative_sorted
    blocks = []
    for indices in np.array_split(np.arange(len(data)), 3):
        selected_indices = indices[in_transit[indices]]
        gradient = derivative[selected_indices]
        denominator = float(np.dot(gradient, gradient))
        shift = -float(np.dot(r[selected_indices], gradient)) / denominator if denominator > 0 else None
        blocks.append({"mean_time_days": float(np.mean(t[indices])), "rows": len(indices),
                       "in_transit_rows": len(selected_indices), "linearized_template_shift_days": shift})
    return {"segment_id": str(data.segment_id.iloc[0]), "rows": len(data),
            "time_span_days": float(t[-1] - t[0]), "median_exposure_days": exposure,
            "selected_spacing_quantiles_days": np.quantile(dt, [0, .25, .5, .75, 1]).tolist(),
            "gaps_larger_than_1_5_selected_median": int(np.sum(dt > 1.5 * selected)),
            "offset_mean": float(np.mean(r)), "linear_trend_per_day": slope,
            "partitions": rows, "time_blocks": blocks}


def audit(root: Path) -> dict:
    summary_path = root / "reports/publication_campaign/tcc_campaign_v1/campaign_summary.json"
    summary = json.loads(summary_path.read_text())
    protocol_path = root / "publication/protocols/PUB-05.json"
    protocol = json.loads(protocol_path.read_text())
    targets = {item["config"]["planet_slug"]: item["config"] for item in protocol["targets"]}
    sources = {p.relative_to(root).as_posix(): sha(p) for p in (summary_path, protocol_path)}
    rows = []
    for attempt in summary["attempts"]:
        if attempt["experiment_id"] != "PUB-05" or not attempt["authoritative"]:
            continue
        directory = root / attempt["output_dir"]
        for name in ("input.csv", "predictive_summary.csv", "result.json", "inference_config.json"):
            path = directory / name
            relative = path.relative_to(root).as_posix()
            digest = sha(path)
            if digest != summary["source_checksums"][relative]:
                raise ValueError(f"Historical source changed: {relative}")
            sources[relative] = digest
        inputs = pd.read_csv(directory / "input.csv")
        curve = pd.read_csv(directory / "predictive_summary.csv")
        verify_prediction_input(inputs, curve)
        curve["exposure_time_seconds"] = inputs.exposure_time_seconds
        target = targets[attempt["scenario_id"]]
        half_duration = target["transit_duration_hours"] / 48
        result = json.loads((directory / "result.json").read_text())
        rows.append({"target": target["planet_name"], "job_id": attempt["job_id"],
                     "output_dir": attempt["output_dir"], "historical_gates": result["gates"],
                     "mask_half_duration_days": half_duration,
                     "mask_origin": "predeclared catalog duration; descriptive conditioning, not independent validation",
                     "segments": [segment_review(g, half_duration=half_duration) for _, g in curve.groupby("segment_id", sort=True)],
                     "historical_temporal_screen": result["residual_correlation"]})
    generators = ("src/publication/residual_review.py", "scripts/audit_observational_residuals.py")
    return {"schema_version": VERSION, "targets": rows, "source_checksums": sources,
            "generator_source_checksums": {name: sha(root / name) for name in generators},
            "numeric_environment": {"numpy": np.__version__, "pandas": pd.__version__},
            "interpretation": "Post-result diagnostics of unchanged selected observations; no gate thresholds revised and no physical posterior promoted.",
            "limitations": ["Selected gaps are not native cadence. Exposure proximity is descriptive, not universal cadence.",
                            "Linear trend removal is diagnostic only; historical inputs/fits are unchanged.",
                            "Time-block template shifts may reflect variability, offsets and shape mismatch, not measured ephemeris drift.",
                            "Catalog duration defines masks; in/out results are not independent validation.",
                            "Residuals alone cannot distinguish stochastic covariance from deterministic structure or establish GP benefit."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    if args.output.exists():
        raise FileExistsError(args.output)
    report = audit(root)
    args.output.mkdir(parents=True)
    (args.output / "audit.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"targets": len(report["targets"]), "output": str(args.output)}))


if __name__ == "__main__":
    main()
