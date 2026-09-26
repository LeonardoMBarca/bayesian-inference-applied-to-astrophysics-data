"""Full-selection observational reports; no hidden targets or promotion by fit completion."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from publication.contracts import safe_path, sha256_file
from publication.observational import target_outcome_table, target_registry

PARAMETERS = ("r", "depth", "b", "a", "t0", "full_duration", "extra_sigma")
TERMINAL = {"completed", "rejected", "failed", "not_interpretable", "blocked"}


def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None


def aggregate_target_outcomes(protocol: Mapping[str, Any], outcomes: list[Mapping[str, Any]]) -> dict:
    """Summarize exactly the preselected systems, retaining rejected posteriors.

    This is a descriptive, fixed-system table, not a coverage estimator or a
    population estimate. Input status must agree with a supplied result status.
    Missing or inconsistent gates fail closed, even if status says completed.
    """
    registry = target_registry(protocol)
    rows, posterior_rows = [], []
    for declared in target_outcome_table(protocol, outcomes):
        target_id = declared["target_id"]
        entry = registry[target_id]
        result = declared.get("result") or {}
        preparation = declared.get("preparation") or {}
        status = declared.get("status", "missing")
        if result.get("status", status) != status:
            raise ValueError(f"Campaign/result status mismatch for {target_id}")
        if preparation.get("target_id", target_id) != target_id:
            raise ValueError("Preparation belongs to a different target")
        if result and preparation and result.get("dataset_id") is not None:
            if result.get("dataset_id") != preparation.get("dataset_id") or result.get("input_sha256") != preparation.get("input_sha256"):
                raise ValueError("Result/preparation dataset identity mismatch")
        gates = result.get("gates", {})
        promotable = status == "completed" and all(gates.get(key) is True for key in ("provenance", "sampler", "ppc", "scientific"))
        # None = diagnostic unavailable, distinct from an observed rejection.
        evaluated = {name: gates.get(name) if isinstance(gates.get(name), bool) else None
                     for name in ("provenance", "sampler", "ppc", "scientific")}
        if status == "failed":
            # An exception before a diagnostic is evaluated is not an observed
            # sampler/PPC rejection, even if fail-closed booleans are false.
            evaluated.update(sampler=None, ppc=None, scientific=None)
        row = {
            "target_id": target_id, "target_name": entry["config"]["planet_name"],
            "selection_role": entry["selection_role"], "cadence_regime": entry["config"]["cadence_preference"],
            "status": status, "scientifically_interpretable": promotable,
            "dataset_id": result.get("dataset_id", preparation.get("dataset_id")),
            "input_sha256": result.get("input_sha256", preparation.get("input_sha256")),
            "modeling_row_count": preparation.get("modeling_row_count"), "segment_count": preparation.get("segment_count"),
            "median_exposure_seconds": preparation.get("median_exposure_seconds"),
            "wall_seconds": _number(result.get("wall_seconds")),
            "failure_stage": declared.get("failure_stage", result.get("failure_stage")),
            "error": declared.get("error", result.get("error")),
            "gate_provenance": evaluated["provenance"], "gate_sampler": evaluated["sampler"],
            "gate_ppc": evaluated["ppc"], "gate_scientific": evaluated["scientific"],
            "diagnostics": result.get("diagnostics", {}), "residual_metrics": result.get("residual_metrics", {}),
            "residual_correlation": result.get("residual_correlation", {}),
            "scale_checks": result.get("scale_checks", {}), "inherited_m5_gate": result.get("inherited_m5_gate", {}),
        }
        parameters = result.get("parameters", {})
        radius = _number(parameters.get("r", {}).get("mean"))
        radius_sd = _number(parameters.get("r", {}).get("sd"))
        row["posterior_radius_precision_ratio"] = radius / radius_sd if radius is not None and radius_sd is not None and radius_sd > 0 else None
        for name in PARAMETERS:
            parameter = parameters.get(name)
            if not isinstance(parameter, dict):
                continue
            mean, sd = _number(parameter.get("mean")), _number(parameter.get("sd"))
            intervals = parameter.get("intervals", {})
            for level in ("0.5", "0.8", "0.94"):
                interval = intervals.get(level)
                if not isinstance(interval, (list, tuple)) or len(interval) != 2:
                    continue
                low, high = map(_number, interval)
                if mean is None or sd is None or low is None or high is None or low > high or sd < 0:
                    raise ValueError(f"Invalid posterior summary for {target_id}/{name}")
                posterior_rows.append({
                    "target_id": target_id, "parameter": name, "nominal": float(level),
                    "mean": mean, "sd": sd, "low": low, "high": high, "width": high - low,
                    "width_over_abs_mean": (high - low) / abs(mean) if mean != 0 else None,
                    "interval_method": parameter.get("interval_method", "equal_tailed"),
                    "status": status, "scientifically_interpretable": promotable,
                })
        rows.append(row)
    counts = dict(sorted(Counter(row["status"] for row in rows).items()))
    return {
        "schema_version": "publication-multitarget-aggregate-v1", "experiment_id": "PUB-05",
        "declared_targets": len(rows), "status_counts": counts,
        "complete_declared_batch": all(row["status"] in TERMINAL for row in rows),
        "scientifically_interpretable_count": sum(row["scientifically_interpretable"] for row in rows),
        "scientifically_interpretable_fraction_all_selected": sum(row["scientifically_interpretable"] for row in rows) / len(rows),
        "gate_counts": {
            name: {"passed": sum(row[f"gate_{name}"] is True for row in rows),
                   "rejected": sum(row[f"gate_{name}"] is False for row in rows),
                   "unavailable": sum(row[f"gate_{name}"] is None for row in rows)}
            for name in ("provenance", "sampler", "ppc", "scientific")
        },
        "targets": rows, "posterior_intervals": posterior_rows,
        "claim_limit": "Five purposively selected systems: descriptive method-scope evidence only, no population rate, no empirical coverage without known truth, no independent catalog validation.",
        "precision_ratio_definition": "posterior r mean / posterior r SD; descriptive posterior precision, NOT a detection SNR and NOT evidence of accuracy",
        "negative_result_policy": "All selected targets remain; available rejected posteriors are displayed but not promoted as reliable physical estimates.",
    }


def _dump(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def _csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_target_report(
    root: Path, protocol_path: Path, outcomes: list[Mapping[str, Any]], output: Path,
    *, campaign_id: str, regenerate_command: str | None = None,
) -> Path:
    """Generate table/figures/report and source-bound freshness manifest.

    ``outcomes`` includes target_id, status, optional result/preparation dicts,
    and ``source_paths`` for the campaign/result/preparation records. Data-bearing
    dicts must match a source JSON exactly; this avoids hashing unrelated files
    while reporting hand-curated values. The wrapper preparation may add campaign
    identity fields; its dataset/input identity must match the saved manifest.
    The caller aggregates the declared campaign registry, never successful paths.
    """
    root = root.resolve()
    protocol_path = protocol_path if protocol_path.is_absolute() else root / protocol_path
    protocol_path = safe_path(root, protocol_path.resolve().relative_to(root).as_posix())
    output = output if output.is_absolute() else root / output
    output = safe_path(root, output.resolve().relative_to(root).as_posix())
    if not any(output.is_relative_to(base) for base in (root / "publication/derived", root / "reports/publication_campaign")):
        raise ValueError("P5 reports must stay under an isolated publication report namespace")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    sources = {protocol_path.relative_to(root).as_posix(): sha256_file(protocol_path)}
    for outcome in outcomes:
        documents = []
        for relative in outcome.get("source_paths", []):
            source = safe_path(root, relative)
            sources[relative] = sha256_file(source)
            if source.suffix == ".json":
                documents.append(json.loads(source.read_text(encoding="utf-8")))
        if outcome.get("result") is not None and outcome["result"] not in documents:
            raise ValueError("Every supplied result must match an audited source JSON")
        preparation = outcome.get("preparation")
        if preparation and not any(all(document.get(key) == preparation.get(key) for key in
                                      ("target_id", "dataset_id", "input_sha256", "output_directory", "artifacts"))
                                   for document in documents if isinstance(document, dict)):
            raise ValueError("Preparation must match an audited source manifest")
        if preparation:
            base = safe_path(root, preparation["output_directory"])
            for name, digest in preparation.get("artifacts", {}).items():
                artifact = safe_path(root, (base / name).relative_to(root).as_posix())
                if sha256_file(artifact) != digest:
                    raise ValueError("Prepared data artifact checksum mismatch")
                sources[artifact.relative_to(root).as_posix()] = digest
    payload = aggregate_target_outcomes(protocol, outcomes)
    payload.update(campaign_id=campaign_id, protocol_status=protocol.get("protocol_status"), source_checksums=sources)
    if protocol.get("protocol_status") not in {"FROZEN", "AMENDED"}:
        payload["claim_limit"] = "DRAFT protocol: engineering report only. " + payload["claim_limit"]
    output.mkdir(parents=True, exist_ok=True)
    _dump(output / "aggregate.json", payload)
    scalar_fields = [key for key, value in payload["targets"][0].items() if not isinstance(value, dict)]
    _csv(output / "targets.csv", payload["targets"], scalar_fields)
    _csv(output / "posterior_intervals.csv", payload["posterior_intervals"],
         ["target_id", "parameter", "nominal", "mean", "sd", "low", "high", "width", "width_over_abs_mean", "interval_method", "status", "scientifically_interpretable"])
    _figures(output, payload)
    lines = [f"# PUB-05: {campaign_id}", "", payload["claim_limit"], "",
             f"All selected targets: {payload['declared_targets']}. Complete declared batch: {payload['complete_declared_batch']}.",
             f"Statuses: `{json.dumps(payload['status_counts'], sort_keys=True)}`.",
             f"Joint scientific passes: {payload['scientifically_interpretable_count']} / {payload['declared_targets']} (descriptive denominator; missing is not measured rejection).", "",
             "| Target | Status | Provenance | Sampler | PPC | Joint scientific | Failure stage |",
             "|---|---|---|---|---|---|---|"]
    for row in payload["targets"]:
        labels = ["unavailable" if row[f"gate_{gate}"] is None else str(row[f"gate_{gate}"]) for gate in ("provenance", "sampler", "ppc")]
        lines.append(f"| {row['target_name']} | {row['status']} | {' | '.join(labels)} | {row['scientifically_interpretable']} | {row['failure_stage'] or ''} |")
    lines += ["", "`targets.csv` preserves every selected system; `posterior_intervals.csv` preserves numeric summaries, including rejected fits. Equal-tailed intervals are not coverage measurements for these unknown-truth observations.",
              "", "`posterior_intervals.png` shows all available 94% intervals. Red denotes an unpromotable result, not a reliable physical estimate. Missing intervals are explicitly marked. `gate_outcomes.png` separates unavailable diagnostics from observed rejections. `regime_precision.png` compares the posterior interval width with exposure, without treating precision as accuracy or detection SNR.",
              "", "## Limits", "", "PDCSAP and catalog ephemerides/durations condition these results. Catalog agreement is contextual rather than independent validation. The model is circular and white-jitter only; stellar activity, fixed-period drift and normalization error are not explicit covariance models. Segment median uncertainty is not propagated. Phase thinning weakens short-time residual checks. Geometric depth r squared differs from limb-darkened observed depth. No LOO/WAIC ranking or population-level claim is made.",
              "", "Source checksums and output freshness: `artifact_manifest.json`. Final scientific conclusions require the full campaign's provenance and release validation, not just this generated report."]
    (output / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    files = ["aggregate.json", "targets.csv", "posterior_intervals.csv", "posterior_intervals.png", "gate_outcomes.png", "regime_precision.png", "REPORT.md"]
    _dump(output / "artifact_manifest.json", {
        "schema_version": "publication-derived-v1", "source_checksums": sources,
        "artifacts": {name: sha256_file(output / name) for name in files},
        "regenerate_command": regenerate_command or "Call publication.target_reporting.write_target_report with the audited campaign outcomes; no inference is repeated",
        "generator": "publication.target_reporting.write_target_report",
    })
    return output


def _figures(output: Path, payload: Mapping[str, Any]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    rows = payload["targets"]
    labels = [row["target_name"] for row in rows]
    intervals = {(row["target_id"], row["parameter"]): row for row in payload["posterior_intervals"] if row["nominal"] == .94}
    fig, axes = plt.subplots(2, 4, figsize=(15, 8), constrained_layout=True)
    for ax, parameter in zip(axes.flat, PARAMETERS, strict=False):
        for index, row in enumerate(rows):
            interval = intervals.get((row["target_id"], parameter))
            if interval:
                color = "#24784a" if row["scientifically_interpretable"] else "#b64a42"
                ax.plot([interval["low"], interval["high"]], [index, index], color=color, linewidth=2)
                ax.plot(interval["mean"], index, "o", color=color, markersize=4)
            else:
                ax.text(.02, index, "unavailable", transform=ax.get_yaxis_transform(), color="gray", fontsize=8)
        ax.set(yticks=range(len(rows)), yticklabels=labels, ylim=(len(rows)-.5, -.5), title=parameter,
               xlabel="Posterior mean and 94% equal-tailed interval")
    axes.flat[-1].axis("off")
    axes.flat[-1].legend(handles=[Patch(color="#24784a", label="Joint gate passed"), Patch(color="#b64a42", label="Not promotable")], loc="center")
    fig.suptitle("Selected systems; all available posteriors retained, including rejected fits")
    fig.savefig(output / "posterior_intervals.png", dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4), constrained_layout=True)
    names = ["provenance", "sampler", "ppc", "scientific"]
    bottom = [0] * len(names)
    for category, color in (("passed", "#24784a"), ("rejected", "#b64a42"), ("unavailable", "#a0a0a0")):
        counts = [payload["gate_counts"][name][category] for name in names]
        ax.bar(names, counts, bottom=bottom, label=category, color=color)
        bottom = [a + b for a, b in zip(bottom, counts, strict=True)]
    ax.set(ylim=(0, len(rows)), yticks=range(len(rows)+1), ylabel="Number of preselected systems", title="Individual diagnostics; promotion also requires completed status")
    ax.legend()
    fig.savefig(output / "gate_outcomes.png", dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4), constrained_layout=True)
    for row in rows:
        interval = intervals.get((row["target_id"], "r"))
        exposure = _number(row["median_exposure_seconds"])
        if interval and exposure is not None and interval["width_over_abs_mean"] is not None:
            ax.scatter(exposure, interval["width_over_abs_mean"], color="#24784a" if row["scientifically_interpretable"] else "#b64a42")
            ax.annotate(row["target_name"], (exposure, interval["width_over_abs_mean"]), xytext=(4, 4), textcoords="offset points", fontsize=8)
    ax.set(xlabel="Median exposure (second)", ylabel="94% r interval width / |posterior mean|", title="Descriptive uncertainty versus exposure; precision is not accuracy")
    ax.set_ylim(bottom=0)
    fig.savefig(output / "regime_precision.png", dpi=160)
    plt.close(fig)
