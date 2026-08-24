"""Summarize a prior-sensitivity family without overstating robustness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from bayesian_modeling.contracts import (
    PRIOR_PROFILES,
    build_m5_paths,
    validate_formal_comparison_contract,
)
from project_config import get_target

PARAMETERS = ("r", "depth", "extra_sigma", "full_duration")


def summarize_sensitivity(
    *,
    project_root: Path,
    target_slug: str,
    run_by_profile: dict[str, str],
    experiment_id: str,
) -> dict[str, Any]:
    expected = set(PRIOR_PROFILES)
    if set(run_by_profile) != expected:
        raise ValueError(f"Sensitivity requires exactly profiles {sorted(expected)}")
    target = get_target(target_slug)
    configs: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for profile in PRIOR_PROFILES:
        run_id = run_by_profile[profile]
        paths = build_m5_paths(project_root, target, run_id)
        config = json.loads(paths.model_config_path.read_text(encoding="utf-8"))
        status = json.loads((paths.model_dir / "run_status.json").read_text(encoding="utf-8"))
        configured_profile = config["model"]["priors"]["profile"]["name"]
        if configured_profile != profile:
            raise ValueError(
                f"Run {run_id} records profile {configured_profile!r}, expected {profile!r}"
            )
        posterior = pd.read_csv(paths.posterior_summary_path)
        row: dict[str, Any] = {
            "profile": profile,
            "run_id": run_id,
            "run_status": status["status"],
            "scientifically_interpretable": config["interpretation_gate"][
                "scientifically_interpretable"
            ],
            "max_r_hat": config["diagnostics"]["max_r_hat"],
            "min_ess": config["diagnostics"]["min_ess"],
            "divergences": config["diagnostics"]["divergences"],
            "bfmi_min": config["diagnostics"]["bfmi_min"],
            "prior_predictive_catalog_reference_inside_94_interval": config[
                "prior_predictive_metrics"
            ]["catalog_reference_inside_94_interval"],
        }
        for parameter in PARAMETERS:
            value = posterior.loc[posterior["parameter"] == parameter]
            if value.empty:
                raise ValueError(f"Run {run_id} is missing posterior parameter {parameter}")
            row[f"{parameter}_mean"] = float(value.iloc[0]["mean"])
            row[f"{parameter}_hdi_3"] = float(value.iloc[0]["hdi_3%"])
            row[f"{parameter}_hdi_97"] = float(value.iloc[0]["hdi_97%"])
        rows.append(row)
        configs.append(config)

    table = pd.DataFrame(rows)
    baseline = table.loc[table["profile"] == "baseline"].iloc[0]
    for parameter in PARAMETERS:
        denominator = abs(float(baseline[f"{parameter}_mean"]))
        table[f"{parameter}_relative_shift_from_baseline"] = (
            (table[f"{parameter}_mean"] - float(baseline[f"{parameter}_mean"])).abs()
            / denominator
            if denominator > 0
            else float("nan")
        )
        table[f"{parameter}_hdi_overlaps_baseline_mean"] = (
            (table[f"{parameter}_hdi_3"] <= float(baseline[f"{parameter}_mean"]))
            & (table[f"{parameter}_hdi_97"] >= float(baseline[f"{parameter}_mean"]))
        )

    comparison_contract = validate_formal_comparison_contract(configs)
    completed = table["run_status"].eq("completed")
    valid = completed & table["scientifically_interpretable"]
    all_runs_completed = bool(completed.all())
    all_gates_pass = bool(valid.all())
    if not all_runs_completed:
        incomplete_runs = table.loc[~completed, "run_id"].astype(str).tolist()
        comparison_contract["formal_comparison_valid"] = False
        comparison_contract["allowed_metrics"] = []
        comparison_contract["rejection_reasons"] = [
            *comparison_contract["rejection_reasons"],
            f"runs are not completed: {incomplete_runs}",
        ]
    maximum_shifts = {
        parameter: float(table[f"{parameter}_relative_shift_from_baseline"].max())
        for parameter in PARAMETERS
    }
    if not all_gates_pass:
        conclusion = (
            "Sensitivity interpretation rejected because at least one run is not "
            "completed or failed its scientific gate. No robustness claim is permitted."
        )
    else:
        conclusion = (
            "All runs passed independent gates. Posterior shifts and interval overlap are "
            "reported descriptively; no universal robustness threshold was post-selected."
        )
    payload = {
        "experiment_id": experiment_id,
        "target": target.metadata(),
        "dataset_id": configs[0]["input_summary"]["dataset_id"],
        "modeling_input_sha256": configs[0]["input_summary"]["modeling_input_sha256"],
        "profiles": table.to_dict(orient="records"),
        "all_runs_completed": all_runs_completed,
        "all_scientific_gates_pass": all_gates_pass,
        "formal_comparison_contract": comparison_contract,
        "maximum_relative_shifts_from_baseline": maximum_shifts,
        "conclusion": conclusion,
    }
    output_dir = project_root / "reports" / "sensitivity" / target_slug / experiment_id
    output_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(output_dir / "posterior_sensitivity_summary.csv", index=False)
    (output_dir / "sensitivity_summary.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    markdown = (
        f"# Sensibilidade de priors — {target.planet_name}\n\n"
        f"Dataset: `{payload['dataset_id']}`  \n"
        f"Checksum da entrada: `{payload['modeling_input_sha256']}`\n\n"
        f"{conclusion}\n\n"
        + "```text\n"
        + table.to_string(index=False)
        + "\n```\n"
    )
    (output_dir / "sensitivity_report.md").write_text(markdown, encoding="utf-8")
    return payload
