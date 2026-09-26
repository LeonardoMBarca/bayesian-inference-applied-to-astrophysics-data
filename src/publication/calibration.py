"""Deterministic calibration summaries over a predeclared replicate denominator.

These functions are POST-INFERENCE consumers: callers attach ground truth only
after posterior summaries have been written. Equal-tailed intervals are used;
fixed-truth repeated coverage is not simulation-based calibration (SBC).
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

PARAMETERS = ("r", "depth", "b", "a", "t0", "full_duration", "extra_sigma")
LEVELS = (0.5, 0.8, 0.94)
NUMERIC_STATUSES = {"completed", "rejected", "not_interpretable"}
KNOWN_STATUSES = NUMERIC_STATUSES | {"planned", "pilot", "running", "failed"}


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> list[float] | None:
    """Two-sided 95% Wilson interval for a Bernoulli proportion by default."""
    if not isinstance(total, int) or not isinstance(successes, int) or total < 0 or not 0 <= successes <= total:
        raise ValueError("successes and total must be counts with 0 <= successes <= total")
    if not math.isfinite(z) or z <= 0:
        raise ValueError("z must be finite and positive")
    if total == 0:
        return None
    proportion = successes / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    half_width = z * math.sqrt(proportion * (1 - proportion) / total + z * z / (4 * total * total)) / denominator
    return [max(0.0, center - half_width), min(1.0, center + half_width)]


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float, np.number)) and not isinstance(value, bool) and math.isfinite(value)


def _valid_parameter(record: Mapping[str, Any]) -> bool:
    if not all(_finite_number(record.get(key)) for key in ("truth", "mean", "sd")):
        return False
    if record["sd"] < 0:
        return False
    intervals = record.get("intervals", {})
    for level in LEVELS:
        bounds = intervals.get(str(level))
        if not isinstance(bounds, (list, tuple)) or len(bounds) != 2:
            return False
        if not all(_finite_number(value) for value in bounds) or bounds[0] > bounds[1]:
            return False
    return True


def coverage_metrics(
    summaries: Iterable[Mapping[str, Any]],
    declared_ids: Sequence[str],
    *,
    parameter_names: Sequence[str] = PARAMETERS,
) -> dict[str, Any]:
    """Summarize ALL declared final IDs, including failed and absent replicates.

    Each record has ``replicate_id``, ``status``, optional boolean ``gates``
    (sampler/ppc/scientific), and ``parameters``. A parameter record holds
    ``truth``, ``mean``, ``sd``, and ``intervals`` keyed by '0.5', '0.8', '0.94'.

    Posterior-conditional coverage includes valid numerical posteriors even if
    scientific gates reject them. Operational success requires a covered truth
    AND a passed scientific gate and uses ALL declared IDs as denominator.
    Missing/failed/PILOT records never become successful by disappearing.
    Gate-conditional coverage is also reported, with its selected denominator.
    """
    if not declared_ids or len(set(declared_ids)) != len(declared_ids):
        raise ValueError("declared_ids must be nonempty and unique")
    if any(not isinstance(value, str) or not value for value in declared_ids):
        raise ValueError("declared_ids must contain nonempty strings")
    declared = set(declared_ids)
    indexed = {}
    for summary in summaries:
        identifier = summary.get("replicate_id")
        if identifier not in declared:
            raise ValueError(f"Undeclared replicate: {identifier!r}")
        if identifier in indexed:
            raise ValueError(f"Duplicate replicate: {identifier!r}")
        status = str(summary.get("status", "")).lower()
        if status not in KNOWN_STATUSES:
            raise ValueError(f"Unknown status for {identifier!r}: {status!r}")
        gates = summary.get("gates", {})
        if any(not isinstance(value, bool) for value in gates.values()):
            raise ValueError("Gate values must be booleans, never strings or missing sentinels")
        indexed[identifier] = {**summary, "status": status}
    total = len(declared_ids)
    counts = Counter(record["status"] for record in indexed.values())
    missing = [identifier for identifier in declared_ids if identifier not in indexed]
    counts["missing"] = len(missing)
    numeric = [record for record in indexed.values() if record["status"] in NUMERIC_STATUSES]
    gates = {}
    for name in ("sampler", "ppc", "scientific"):
        eligible = [record for record in numeric if name in record.get("gates", {})]
        passed = sum(record["gates"][name] for record in eligible)
        rejected = len(eligible) - passed
        gates[name] = {
            "evaluated_count": len(eligible), "passed_count": passed,
            "rejected_count": rejected, "unevaluated_count": total - len(eligible),
            "pass_rate_all_declared": passed / total,
            "rejection_rate_all_declared": rejected / total,
            "rejection_rate_evaluated": rejected / len(eligible) if eligible else None,
            "pass_rate_all_declared_wilson95": wilson_interval(passed, total),
        }
    parameters: dict[str, Any] = {}
    for parameter in parameter_names:
        available = [
            (record, record.get("parameters", {}).get(parameter, {}))
            for record in numeric
        ]
        valid = [(record, values) for record, values in available if _valid_parameter(values)]
        errors = np.array([values["mean"] - values["truth"] for _, values in valid])
        n_valid = len(valid)
        if not n_valid:
            parameters[parameter] = {
                "numeric_count": 0, "missing_or_invalid_count": total,
                "bias": None, "absolute_bias": None, "relative_bias": None,
                "mae": None, "rmse": None, "mean_posterior_sd": None,
                "mean_absolute_calibration_error": None,
                "coverage": {
                    str(level): {
                        "nominal": level, "covered_count": 0, "numeric_count": 0,
                        "empirical_coverage_numeric": None, "wilson95_numeric": None,
                        "operational_covered_and_passed_rate_all_declared": 0.0,
                        "operational_wilson95_all_declared": wilson_interval(0, total),
                        "mean_interval_width": None,
                    } for level in LEVELS
                },
            }
            continue
        relative_errors = [
            (values["mean"] - values["truth"]) / values["truth"]
            for _, values in valid if values["truth"] != 0
        ]
        result = {
            "numeric_count": n_valid, "missing_or_invalid_count": total - n_valid,
            "bias": float(errors.mean()), "absolute_bias": float(abs(errors.mean())),
            "mae": float(np.abs(errors).mean()), "rmse": float(np.sqrt(np.mean(errors**2))),
            "relative_bias": float(np.mean(relative_errors)) if relative_errors else None,
            "relative_bias_nonzero_truth_count": len(relative_errors),
            "mean_posterior_sd": float(np.mean([values["sd"] for _, values in valid])),
            "coverage": {},
        }
        sampler_errors = [values["mean"] - values["truth"] for record, values in valid if record.get("gates", {}).get("sampler") is True]
        result["sampler_passed_numeric_count"] = len(sampler_errors)
        result["bias_conditional_on_sampler"] = float(np.mean(sampler_errors)) if sampler_errors else None
        result["rmse_conditional_on_sampler"] = float(np.sqrt(np.mean(np.square(sampler_errors)))) if sampler_errors else None
        calibration_errors = []
        for level in LEVELS:
            key = str(level)
            flags = [values["intervals"][key][0] <= values["truth"] <= values["intervals"][key][1] for _, values in valid]
            gate_passed = [
                record["status"] == "completed"
                and all(record.get("gates", {}).get(name) is True for name in ("sampler", "ppc", "scientific"))
                for record, _ in valid
            ]
            covered = sum(flags)
            passed_and_covered = sum(flag and gate for flag, gate in zip(flags, gate_passed, strict=True))
            valid_gate_passed = sum(gate_passed)
            sampler_passed = [record.get("gates", {}).get("sampler") is True for record, _ in valid]
            sampler_covered = sum(flag and passed for flag, passed in zip(flags, sampler_passed, strict=True))
            sampler_count = sum(sampler_passed)
            empirical = covered / n_valid
            calibration_errors.append(abs(empirical - level))
            result["coverage"][key] = {
                "nominal": level, "covered_count": covered, "numeric_count": n_valid,
                "empirical_coverage_numeric": empirical,
                "wilson95_numeric": wilson_interval(covered, n_valid),
                "sampler_passed_numeric_count": sampler_count,
                "coverage_conditional_on_sampler": sampler_covered / sampler_count if sampler_count else None,
                "wilson95_conditional_on_sampler": wilson_interval(sampler_covered, sampler_count),
                "scientific_gate_passed_numeric_count": valid_gate_passed,
                "covered_and_scientific_gate_passed_count": passed_and_covered,
                "coverage_conditional_on_scientific_gate": passed_and_covered / valid_gate_passed if valid_gate_passed else None,
                "wilson95_conditional_on_scientific_gate": wilson_interval(passed_and_covered, valid_gate_passed),
                "operational_covered_and_passed_rate_all_declared": passed_and_covered / total,
                "operational_wilson95_all_declared": wilson_interval(passed_and_covered, total),
                "calibration_error_numeric": empirical - level,
                "absolute_calibration_error_numeric": abs(empirical - level),
                "mean_interval_width": float(np.mean([values["intervals"][key][1] - values["intervals"][key][0] for _, values in valid])),
            }
        result["mean_absolute_calibration_error"] = float(np.mean(calibration_errors))
        parameters[parameter] = result
    return {
        "schema_version": "fixed-truth-calibration-v1", "interval_kind": "equal_tailed",
        "declared_count": total, "present_count": len(indexed),
        "status_counts": dict(sorted(counts.items())), "missing_ids": missing,
        "execution_failure_rate_all_declared": counts["failed"] / total,
        "unavailable_final_rate_all_declared": (total - len(numeric)) / total,
        "gates": gates, "parameters": parameters,
        "interpretation": (
            "Fixed-truth repeated-sampling coverage is not SBC. Numeric coverage includes rejected "
            "posteriors; gate-conditional coverage is selected. Operational covered-and-passed rate "
            "counts all declared replicates and is NOT a credible-interval calibration estimand. "
            "Failures, missing records, and pilot records cannot count as final successes."
        ),
    }
