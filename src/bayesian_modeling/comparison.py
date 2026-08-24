"""Guarded formal and predictive model-comparison workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import arviz as az
import numpy as np
import pandas as pd
from scipy.special import logsumexp

from bayesian_modeling.contracts import validate_formal_comparison_contract


def _read_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _loo_scalar(loo: Any, legacy_name: str, current_name: str) -> float:
    """Read an ELPDData scalar across the ArviZ 0.x and 1.x APIs."""

    value = getattr(loo, legacy_name, None)
    if value is None:
        value = getattr(loo, current_name)
    return float(value)


def _waic_from_pointwise_log_likelihood(idata: Any) -> dict[str, Any]:
    """Compute WAIC from the stored pointwise log likelihood.

    ArviZ 1.3 delegates predictive criteria to ``arviz-stats`` and no longer
    exposes ``az.waic``.  Keeping this small implementation here makes the
    locked environment explicit and follows the standard WAIC definition:
    ``elpd_waic_i = log(mean(exp(log_lik_i))) - var(log_lik_i)``.
    """

    log_likelihood = idata.log_likelihood
    variable_names = list(log_likelihood.data_vars)
    if len(variable_names) != 1:
        raise ValueError(
            "Formal WAIC requires exactly one observed log-likelihood variable; "
            f"found {variable_names}."
        )
    values_array = log_likelihood[variable_names[0]]
    if "chain" not in values_array.dims or "draw" not in values_array.dims:
        raise ValueError("Pointwise log likelihood must have chain and draw dimensions.")
    observation_dims = [
        dimension
        for dimension in values_array.dims
        if dimension not in {"chain", "draw"}
    ]
    ordered = values_array.transpose("chain", "draw", *observation_dims)
    values = np.asarray(ordered, dtype=float).reshape(
        ordered.sizes["chain"] * ordered.sizes["draw"], -1
    )
    if values.shape[0] < 2 or values.shape[1] == 0 or not np.isfinite(values).all():
        raise ValueError("Pointwise log likelihood is empty, non-finite, or undersampled.")

    pointwise_variance = np.var(values, axis=0, ddof=1)
    lppd_pointwise = logsumexp(values, axis=0) - np.log(values.shape[0])
    elpd_pointwise = lppd_pointwise - pointwise_variance
    elpd_waic = float(np.sum(elpd_pointwise))
    standard_error = float(
        np.sqrt(values.shape[1] * np.var(elpd_pointwise, ddof=0))
    )
    max_variance = float(np.max(pointwise_variance))
    high_variance_count = int(np.count_nonzero(pointwise_variance > 0.4))
    return {
        "elpd_waic": elpd_waic,
        "se": standard_error,
        "p_waic": float(np.sum(pointwise_variance)),
        "warning": high_variance_count > 0,
        "pointwise_variance_gt_0_4_count": high_variance_count,
        "max_pointwise_log_likelihood_variance": max_variance,
        "n_posterior_samples": int(values.shape[0]),
        "n_observations": int(values.shape[1]),
        "scale": "log",
    }


def compare_runs(
    *,
    project_root: Path,
    config_paths: list[Path],
    output_dir: Path,
) -> dict[str, Any]:
    configs = [_read_config(path) for path in config_paths]
    contract = validate_formal_comparison_contract(configs)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "comparison_contract": contract,
        "runs": [config.get("run_id") for config in configs],
        "formal_bayesian_metrics": None,
        "predictive_metrics": [
            {
                "run_id": config.get("run_id"),
                "rmse": config.get("residual_metrics", {}).get("rmse"),
                "mae": config.get("residual_metrics", {}).get("mae"),
                "ppc_94_coverage": config.get("residual_metrics", {}).get(
                    "posterior_predictive_interval_94_coverage_observed_points"
                ),
                "scientifically_interpretable": config.get(
                    "interpretation_gate", {}
                ).get("scientifically_interpretable", False),
            }
            for config in configs
        ],
        "heuristic_structural_scores": {
            "status": "not_computed",
            "reason": (
                "No heuristic score is mixed with predictive or formal Bayesian metrics."
            ),
        },
        "interpretation": (
            "Formal comparison rejected; no LOO/WAIC/ELPD ranking was computed."
            if not contract["formal_comparison_valid"]
            else "Formal comparison computed for identical observations and likelihood target."
        ),
    }
    if contract["formal_comparison_valid"]:
        loo_rows: list[dict[str, Any]] = []
        waic_rows: list[dict[str, Any]] = []
        for config in configs:
            run_id = str(config["run_id"])
            trace_relative = config["artifacts"]["trace"]
            idata = az.from_netcdf(project_root / trace_relative)
            loo = az.loo(idata, pointwise=True)
            pareto_k = np.asarray(loo.pareto_k, dtype=float).reshape(-1)
            loo_rows.append(
                {
                    "run_id": run_id,
                    "elpd_loo": _loo_scalar(loo, "elpd_loo", "elpd"),
                    "se": float(loo.se),
                    "p_loo": _loo_scalar(loo, "p_loo", "p"),
                    "warning": bool(loo.warning),
                    "pareto_k_gt_0_7_count": int(np.count_nonzero(pareto_k > 0.7)),
                    "pareto_k_max": float(np.max(pareto_k)),
                }
            )
            waic_rows.append(
                {"run_id": run_id, **_waic_from_pointwise_log_likelihood(idata)}
            )
        pd.DataFrame(loo_rows).to_csv(output_dir / "loo_summary.csv", index=False)
        pd.DataFrame(waic_rows).to_csv(output_dir / "waic_summary.csv", index=False)
        has_warning = any(row["warning"] for row in loo_rows + waic_rows)
        payload["formal_bayesian_metrics"] = {
            "loo": loo_rows,
            "waic": waic_rows,
            "diagnostic_status": "warning" if has_warning else "passed",
            "ranking_status": (
                "not_ranked_due_to_diagnostic_warning" if has_warning else "eligible"
            ),
        }
        if has_warning:
            payload["interpretation"] = (
                "Formal LOO/WAIC values were computed for comparable runs, but at "
                "least one pointwise diagnostic warned. The repository does not "
                "promote these values to a reliable model ranking."
            )
    (output_dir / "comparison_summary.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return payload
