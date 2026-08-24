"""Inventory model configs without upgrading historical diagnostics into current validity."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def nested(mapping: dict[str, Any], *keys: str) -> Any:
    value: Any = mapping
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def main() -> None:
    rows: list[dict[str, Any]] = []
    model_root = PROJECT_ROOT / "models"
    run_directories = {
        path.parent for path in model_root.rglob("model_config.json")
    } | {path.parent for path in model_root.rglob("run_status.json")}
    for directory in sorted(run_directories):
        config_path = directory / "model_config.json"
        status_path = directory / "run_status.json"
        try:
            config = (
                json.loads(config_path.read_text(encoding="utf-8"))
                if config_path.exists()
                else {}
            )
            status = (
                json.loads(status_path.read_text(encoding="utf-8"))
                if status_path.exists()
                else {}
            )
        except (json.JSONDecodeError, UnicodeError) as exc:
            rows.append(
                {
                    "config_path": (
                        config_path.relative_to(PROJECT_ROOT).as_posix()
                        if config_path.exists()
                        else None
                    ),
                    "status_path": (
                        status_path.relative_to(PROJECT_ROOT).as_posix()
                        if status_path.exists()
                        else None
                    ),
                    "classification": "unreadable_config",
                    "error": str(exc),
                }
            )
            continue
        gate = config.get("interpretation_gate") or status.get("interpretation_gate")
        if status.get("status") == "failed":
            classification = "failed_preserved_for_traceability"
        elif gate and gate.get("scientifically_interpretable") is True:
            classification = "current_scientifically_interpretable"
        elif gate:
            classification = "rejected_by_current_gate"
        else:
            classification = "historical_ungated_not_currently_interpretable"
        target = config.get("target") or status.get("target") or {}
        if isinstance(target, str):
            target_name = target
        else:
            target_name = target.get("planet_name") or config.get("planet_name")
        diagnostics = config.get("diagnostics", {})
        rows.append(
            {
                "config_path": (
                    config_path.relative_to(PROJECT_ROOT).as_posix()
                    if config_path.exists()
                    else None
                ),
                "status_path": (
                    status_path.relative_to(PROJECT_ROOT).as_posix()
                    if status_path.exists()
                    else None
                ),
                "model_name": config.get("model_name") or status.get("model_name"),
                "run_id": config.get("run_id") or status.get("run_id") or directory.name,
                "target": target_name,
                "dataset_id": nested(config, "input_summary", "dataset_id"),
                "run_status": status.get("status", "historical_no_status_file"),
                "max_r_hat": diagnostics.get("max_r_hat"),
                "min_ess": diagnostics.get("min_ess"),
                "divergences": diagnostics.get("divergences"),
                "bfmi_min": diagnostics.get("bfmi_min"),
                "scientifically_interpretable": (
                    gate.get("scientifically_interpretable") if gate else False
                ),
                "classification": classification,
            }
        )
    payload = {
        "inventory_rule": (
            "Only an explicit current interpretation gate can mark a run scientifically "
            "interpretable. Historical convergence summaries remain ungated snapshots."
        ),
        "runs": rows,
    }
    json_path = PROJECT_ROOT / "reports" / "model_run_inventory.json"
    markdown_path = PROJECT_ROOT / "reports" / "model_run_inventory.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    columns = [
        "model_name",
        "run_id",
        "target",
        "max_r_hat",
        "min_ess",
        "divergences",
        "bfmi_min",
        "classification",
    ]
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    lines = [header, separator]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    markdown_path.write_text(
        "# Inventário de runs\n\n"
        + payload["inventory_rule"]
        + "\n\n"
        + "\n".join(lines)
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"runs": len(rows), "json": json_path.name, "markdown": markdown_path.name}))


if __name__ == "__main__":
    main()
