"""Audit every campaign job and regenerate evidence without rerunning inference."""

from __future__ import annotations

import argparse
import copy
import csv
import importlib.metadata
import json
import platform
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from publication.calibration import PARAMETERS, coverage_metrics
from publication.campaign import CampaignIntegrityError, validate_completion
from publication.campaign import _read as read_campaign_json
from publication.campaign_plan import DEFAULT_CONFIG, build_plan, source_identity
from publication.contracts import canonical_hash, safe_path, sha256_file

SCIENTIFIC_TERMINAL = {"COMPLETED", "COMPLETED_REJECTED"}
TERMINAL = SCIENTIFIC_TERMINAL | {"FAILED_TECHNICAL", "BLOCKED", "CANCELLED"}


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def _table(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    fields = fields or list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({key: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value for key, value in row.items()} for row in rows)


def state_fingerprint(state: dict, family: str | None = None) -> str:
    """Match controller fingerprint, excluding its own aggregation bookkeeping."""
    return canonical_hash([
        {key: row.get(key) for key in ("job_id", "status", "seeds", "input_sha256", "dataset_id", "gates")}
        | {"attempts": [(item["status"], item.get("completion_manifest_sha256")) for item in row["attempts"]]}
        for job_id in sorted(state.get("jobs", {})) for row in [state["jobs"][job_id]]
        if family is None or row["experiment_id"] == family
    ])


def collect_campaign(root: Path, plan: dict, state: dict | None) -> dict:
    """Read only registered attempts; last attempt authoritative, all retained.

    A result is numerically usable only after its completion manifest and every
    bound artifact verify. An interrupted partial posterior is never promoted.
    Integrity failures are reported and excluded, not repaired or ignored.
    """
    root = root.resolve()
    state = state or {"jobs": {}, "campaign_id": plan["campaign_id"], "status": "NOT_INITIALIZED"}
    errors: list[str] = []
    if state.get("campaign_id") != plan["campaign_id"]:
        errors.append("Campaign identity differs between plan and state")
    if state.get("scientific_config_sha256", plan["scientific_config_sha256"]) != plan["scientific_config_sha256"]:
        errors.append("Scientific configuration differs between plan and state")
    declared = {job["job_id"]: job for job in plan["jobs"]}
    for unknown in set(state.get("jobs", {})) - set(declared):
        errors.append(f"Undeclared state job retained in snapshot: {unknown}")
    jobs, attempts, sources = [], [], {}
    for job_id, definition in declared.items():
        registered = state.get("jobs", {}).get(job_id, {})
        local_errors = []
        for key in ("experiment_id", "scenario_id", "replicate_id", "run_id", "seeds", "output_dir"):
            if key in registered and registered[key] != definition[key]:
                local_errors.append(f"State job {job_id} changed declared {key}")
        row = {key: definition[key] for key in ("job_id", "experiment_id", "scenario_id", "replicate_id", "run_id", "seeds", "output_dir")}
        row.update(status=registered.get("status", "PLANNED"), attempt_count=len(registered.get("attempts", [])),
                   error=registered.get("error"), result=None, truth=None, preparation=None,
                   completion=None, authoritative_attempt_dir=None, source_paths=[], payload=definition.get("payload", {}))
        previous = registered.get("attempts", [])
        for index, attempt in enumerate(previous):
            audit = {"job_id": job_id, "experiment_id": definition["experiment_id"],
                     "scenario_id": definition["scenario_id"], "replicate_id": definition["replicate_id"],
                     "authoritative": index == len(previous)-1, **copy.deepcopy(attempt), "integrity_valid": False}
            try:
                if attempt.get("attempt_index") != index:
                    raise ValueError("Attempt indices must preserve append order")
                path = safe_path(root, attempt["output_dir"])
                if path.parent != safe_path(root, definition["output_dir"]):
                    raise ValueError("Attempt directory escaped declared job namespace")
                if attempt.get("seeds", definition["seeds"]) != definition["seeds"]:
                    raise ValueError("Retry changed declared seeds")
                completion_path = path / "completion_manifest.json"
                digest = attempt.get("completion_manifest_sha256")
                if not digest:
                    if attempt.get("status") in SCIENTIFIC_TERMINAL:
                        raise ValueError("Scientific terminal attempt lacks registered completion hash")
                    audit["integrity_note"] = "Unsealed/partial attempt is retained but unavailable as scientific evidence"
                    attempts.append(audit)
                    continue
                completion = validate_completion(path, expected_manifest_sha256=digest,
                                                 declared_intervention=definition.get("payload", {}).get("intervention"))
                if completion["status"] != attempt["status"]:
                    raise ValueError("Completion/attempt status mismatch")
                result = _read(path / "result.json")
                if completion.get("gates", {}) != result.get("gates", {}):
                    raise ValueError("Completion/result gates mismatch")
                input_sha = completion.get("input_sha256")
                if result.get("input_sha256") is not None and result["input_sha256"] != input_sha:
                    raise ValueError("Completion/result input identity mismatch")
                if result.get("dataset_id") is not None and result["dataset_id"] != completion.get("dataset_id"):
                    raise ValueError("Completion/result dataset identity mismatch")
                if attempt["status"] == "COMPLETED" and (result.get("status") != "completed" or not all(result.get("gates", {}).get(key) is True for key in ("provenance", "sampler", "ppc", "scientific"))):
                    raise ValueError("Completed campaign job lacks completed result and four passed gates")
                if any(key in completion["artifacts"] for key in ("truth.json", "input.csv")):
                    if definition.get("payload", {}).get("kind") == "synthetic":
                        truth = _read(path / "truth.json")
                        if truth.get("data_sha256") != input_sha:
                            raise ValueError("Synthetic ground truth/input identity mismatch")
                paths = [completion_path.relative_to(root).as_posix()]
                sources[paths[0]] = digest
                for relative, checksum in completion["artifacts"].items():
                    name = (path / relative).relative_to(root).as_posix()
                    sources[name] = checksum
                    paths.append(name)
                audit.update(integrity_valid=True, result_status=result.get("status"),
                             dataset_id=completion.get("dataset_id"), input_sha256=input_sha,
                             gates=result.get("gates", {}))
                if index == len(previous)-1 and not local_errors and row["status"] == attempt["status"]:
                    row.update(result=result, completion=completion, authoritative_attempt_dir=path.relative_to(root).as_posix(), source_paths=paths)
                    for key, filename in (("truth", "truth.json"), ("preparation", "preparation.json")):
                        if filename in completion["artifacts"]:
                            row[key] = _read(path / filename)
            except (OSError, ValueError, KeyError, TypeError, CampaignIntegrityError) as exc:
                message = f"{job_id} attempt {index}: {exc}"
                local_errors.append(message)
                audit["integrity_error"] = message
            attempts.append(audit)
        if local_errors:
            row.update(integrity_errors=local_errors, result=None, truth=None, preparation=None)
            errors.extend(local_errors)
        if row["status"] in SCIENTIFIC_TERMINAL and row["result"] is None and not local_errors:
            message = f"Scientific terminal job has no authoritative sealed result: {job_id}"
            row["integrity_errors"] = [message]
            errors.append(message)
        row["computational_gates_passed"] = row["status"] == "COMPLETED" and row["result"] is not None
        row["scientifically_interpretable"] = (
            row["computational_gates_passed"] and plan.get("mode") == "final"
            and row["payload"].get("kind") != "fixture" and not row["result"].get("fixture", False)
        )
        jobs.append(row)
    return {"jobs": jobs, "attempts": attempts, "source_checksums": sources, "integrity_errors": errors}


def _scientific_summary(row: dict) -> dict | None:
    result = row.get("result")
    if not result:
        if row["status"] in {"FAILED_TECHNICAL", "BLOCKED", "CANCELLED"} or row.get("integrity_errors"):
            return {"replicate_id": row["replicate_id"], "status": "failed", "gates": {}}
        return None
    summary = copy.deepcopy(result)
    summary["replicate_id"] = row["replicate_id"]
    if (row.get("completion") or {}).get("expected_identity_rejection") and summary.get("failure_stage") == "input_validation":
        summary.update(status="rejected", gates={"provenance": False})
    # Truth is attached here ONLY, after inference produced a sealed result.
    truth = (row.get("truth") or {}).get("truth", {})
    for parameter, values in summary.get("parameters", {}).items():
        if parameter in truth:
            values["truth"] = truth[parameter]
    if summary.get("status") not in {"completed", "rejected", "not_interpretable", "failed"}:
        summary.update(status="failed", parameters={})
    return summary


def calibration_report(rows: list[dict], output: Path, *, mode: str) -> dict:
    """P2/P4 fixed-truth calibration including every declared replicate."""
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["scenario_id"]].append(row)
    scenarios, table, recovery = {}, [], []
    for scenario, declared in grouped.items():
        summaries = [summary for row in declared if (summary := _scientific_summary(row)) is not None]
        metrics = coverage_metrics(summaries, [row["replicate_id"] for row in declared])
        scenarios[scenario] = metrics
        for name, parameter in metrics["parameters"].items():
            for level, coverage in parameter["coverage"].items():
                table.append({"scenario_id": scenario, "parameter": name, "nominal": float(level),
                              **{key: value for key, value in parameter.items() if key != "coverage"}, **coverage})
        for summary in summaries:
            for name, parameter in summary.get("parameters", {}).items():
                if "truth" in parameter:
                    recovery.append({"scenario_id": scenario, "replicate_id": summary["replicate_id"], "parameter": name,
                                     "status": summary["status"], "truth": parameter["truth"], "mean": parameter["mean"],
                                     "sd": parameter["sd"], "scientific_gate": summary.get("gates", {}).get("scientific")})
    payload = {"scenarios": scenarios, "mode": mode, "declared_jobs": len(rows),
               "claim_limit": "Smoke is engineering only. Final fixed-truth coverage is not SBC. Numeric posteriors include rejected/nonconverged outputs; sampler-conditioned coverage is separately reported. Missing intervals are not measured noncoverage. Expected presampling identity rejections are rejected, not technical failures, with downstream diagnostics unavailable. Zero-jitter boundary truth under a continuous prior need not be inside positive equal-tailed intervals."}
    output.mkdir(parents=True, exist_ok=True)
    _write(output / "calibration.json", payload)
    _table(output / "calibration.csv", table)
    _table(output / "posterior_recovery.csv", recovery, ["scenario_id", "replicate_id", "parameter", "status", "truth", "mean", "sd", "scientific_gate"])
    _calibration_figures(scenarios, recovery, output)
    return payload


def _calibration_figures(scenarios: dict, recovery: list[dict], output: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = list(scenarios)
    for category in ("coverage", "bias", "width", "recovery"):
        fig, axes = plt.subplots(2, 4, figsize=(15, 8), constrained_layout=True)
        for ax, parameter in zip(axes.flat, PARAMETERS, strict=False):
            ax.set_title(parameter)
            if category == "coverage":
                ax.plot([.45, 1], [.45, 1], "k--", linewidth=.8)
                for name, result in scenarios.items():
                    entries = [value for value in result["parameters"][parameter]["coverage"].values() if value["empirical_coverage_numeric"] is not None]
                    if entries:
                        x = np.array([value["nominal"] for value in entries])
                        y = np.array([value["empirical_coverage_numeric"] for value in entries])
                        bounds = np.array([value["wilson95_numeric"] for value in entries]).T
                        ax.errorbar(x, y, yerr=np.maximum([y-bounds[0], bounds[1]-y], 0), marker="o", label=name, alpha=.7)
                ax.set(xlabel="Nominal equal-tailed interval", ylabel="Numeric coverage (Wilson 95%)", ylim=(-.03, 1.03), xlim=(.45, 1.02))
            elif category in {"bias", "width"}:
                values = [scenarios[name]["parameters"][parameter]["bias"] if category == "bias" else scenarios[name]["parameters"][parameter]["coverage"]["0.94"]["mean_interval_width"] for name in names]
                ax.bar(names, [np.nan if value is None else value for value in values])
                ax.set_ylabel("Posterior mean minus truth" if category == "bias" else "Mean 94% interval width")
                if category == "bias":
                    ax.axhline(0, color="black", linewidth=.7)
                else:
                    ax.set_ylim(bottom=0)
                ax.tick_params(axis="x", rotation=65, labelsize=6)
            else:
                selected = [row for row in recovery if row["parameter"] == parameter]
                for name in names:
                    points = [row for row in selected if row["scenario_id"] == name]
                    if points:
                        ax.errorbar([row["truth"] for row in points], [row["mean"] for row in points], yerr=[row["sd"] for row in points], fmt=".", alpha=.6, label=name)
                if selected:
                    extent = [min(min(row["truth"], row["mean"]) for row in selected), max(max(row["truth"], row["mean"]) for row in selected)]
                    ax.plot(extent, extent, "k--", linewidth=.7)
                ax.set(xlabel="Injected truth", ylabel="Posterior mean +/- SD (not interval)")
        axes.flat[-1].axis("off")
        handles, labels = axes.flat[0].get_legend_handles_labels()
        if handles:
            axes.flat[-1].legend(handles, labels, fontsize=7, loc="center")
        fig.suptitle("All declared scenarios; rejected numeric posteriors retained; missing values not fabricated")
        fig.savefig(output / f"{category}.png", dpi=160)
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(11, 4), constrained_layout=True)
    for gate in ("sampler", "ppc", "scientific"):
        ax.plot(names, [scenarios[name]["gates"][gate]["pass_rate_all_declared"] for name in names], "o-", label=gate)
    ax.set(ylim=(-.03, 1.03), ylabel="Passed / all declared", title="All-declared gate pass fractions; missing is not measured rejection")
    ax.tick_params(axis="x", rotation=45, labelsize=7)
    ax.legend()
    fig.savefig(output / "gate_rates.png", dpi=160)
    plt.close(fig)


def ablation_report(rows: list[dict], output: Path) -> dict:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        groups[(row["payload"].get("pair_id", row["scenario_id"]), row["replicate_id"])].append(row)
    effects, gates = [], []
    for (pair, replicate), variants in groups.items():
        baseline = next((row for row in variants if row["payload"].get("variant_id") == "baseline"), None)
        for row in variants:
            result = row.get("result") or {}
            observed = result.get("gates", {})
            presampling = result.get("failure_stage") == "input_validation"
            gates.append({"pair_id": pair, "replicate_id": replicate, "variant_id": row["payload"].get("variant_id"),
                          "job_id": row["job_id"], "status": row["status"],
                          **{f"gate_{name}": None if presampling and name != "provenance" else observed.get(name) for name in ("provenance", "sampler", "ppc", "scientific")},
                          "failure_stage": result.get("failure_stage"), "expected_identity_rejection": (row.get("completion") or {}).get("expected_identity_rejection", False),
                          "sampler_pass_but_ppc_or_science_fail": observed.get("sampler") is True and (observed.get("ppc") is False or observed.get("scientific") is False)})
            for parameter in PARAMETERS:
                reference = ((baseline or {}).get("result") or {}).get("parameters", {}).get(parameter)
                current = result.get("parameters", {}).get(parameter)
                effect = {"pair_id": pair, "replicate_id": replicate, "variant_id": row["payload"].get("variant_id"),
                          "parameter": parameter, "pair_complete_numeric": bool(reference and current),
                          "both_scientifically_interpretable": bool(baseline and baseline["scientifically_interpretable"] and row["scientifically_interpretable"]),
                          "mean_shift": None, "median_shift": None, "mean_shift_over_baseline_sd": None, "sd_ratio": None, "interval94_width_ratio": None}
                if reference and current:
                    base_sd = reference["sd"]
                    lo, hi = reference["intervals"]["0.94"]
                    low, high = current["intervals"]["0.94"]
                    effect.update(mean_shift=current["mean"]-reference["mean"],
                                  median_shift=current["median"]-reference["median"] if "median" in current and "median" in reference else None,
                                  mean_shift_over_baseline_sd=(current["mean"]-reference["mean"])/base_sd if base_sd > 0 else None,
                                  sd_ratio=current["sd"]/base_sd if base_sd > 0 else None,
                                  interval94_width_ratio=(high-low)/(hi-lo) if hi > lo else None)
                effects.append(effect)
    payload = {"declared_jobs": len(rows), "declared_pair_realizations": len(groups), "paired_effects": effects,
               "gate_matrix": gates, "sampler_pass_but_ppc_or_science_fail_count": sum(row["sampler_pass_but_ppc_or_science_fail"] for row in gates),
               "claim_limit": "Paired effects require two available numeric outputs; incomplete pairs are unavailable, not zero. Rejected posteriors are retained with diagnostics, not promoted. A negative control only demonstrates detection when the declared mechanism and evaluated gate support that interpretation."}
    output.mkdir(parents=True, exist_ok=True)
    _write(output / "ablation.json", payload)
    _table(output / "paired_effects.csv", effects)
    _table(output / "gate_matrix.csv", gates)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    radius = [row for row in effects if row["parameter"] == "r"]
    for index, row in enumerate(radius):
        if row["mean_shift_over_baseline_sd"] is not None:
            axes[0].scatter(index, row["mean_shift_over_baseline_sd"], color="#24784a" if row["both_scientifically_interpretable"] else "#b64a42", s=15)
        if row["interval94_width_ratio"] is not None:
            axes[1].scatter(index, row["interval94_width_ratio"], s=15)
        if len(radius) <= 15:
            for ax in axes:
                ax.set_xticks(range(len(radius)), [f"{r['pair_id']}/{r['variant_id']}" for r in radius], rotation=80, fontsize=6)
    axes[0].axhline(0, color="black", linewidth=.7)
    axes[1].axhline(1, color="black", linewidth=.7)
    axes[0].set(ylabel="Paired r mean shift / baseline SD", xlabel="Declared pair/variant index")
    axes[1].set(ylabel="94% r interval width / baseline width", xlabel="Declared pair/variant index", ylim=(0, None))
    fig.suptitle("Paired intervention effects; unavailable pairs absent numerically, retained in CSV")
    fig.savefig(output / "paired_effects.png", dpi=160)
    plt.close(fig)
    return payload


def benchmark_report(root: Path, rows: list[dict], output: Path) -> dict:
    """Compare sealed distributions only under matched input/inference contract."""
    payload: dict = {"status": "unavailable", "declared_jobs": len(rows), "reason": "Both sealed benchmark engine results and posterior arrays are required"}
    local = next((row for row in rows if row["payload"].get("kind") == "benchmark_local"), None)
    external = next((row for row in rows if row["payload"].get("kind") == "benchmark_external"), None)
    if (local and external and local.get("result") and external.get("result")
            and local["result"].get("status") in {"completed", "rejected", "not_interpretable"}
            and external["result"].get("status") in {"completed", "rejected", "not_interpretable"}):
        left, right = local["result"], external["result"]
        if not left.get("input_sha256") or not left.get("dataset_id") or left.get("input_sha256") != right.get("input_sha256") or left.get("dataset_id") != right.get("dataset_id"):
            raise ValueError("Independent benchmark inputs differ")
        local_dir, external_dir = root / local["authoritative_attempt_dir"], root / external["authoritative_attempt_dir"]
        left_config, right_config = _read(local_dir / "inference_config.json"), _read(external_dir / "inference_config.json")
        for key in ("period_days", "radius_prior_uniform", "baseline_prior_sigma", "t0_prior_sigma_days", "jitter_error_multiplier", "jitter_floor_fraction", "infer_jitter", "integrate_exposure", "oversample"):
            if left_config.get(key) != right_config.get(key):
                raise ValueError(f"Independent benchmark inference contract differs: {key}")
        local_artifacts, external_artifacts = local["completion"]["artifacts"], external["completion"]["artifacts"]
        if "trace.nc" in local_artifacts and "posterior_samples.npz" in external_artifacts:
            import xarray as xr

            from publication.benchmark import compare_posterior_arrays

            with xr.open_dataset(local_dir / "trace.nc", group="posterior", engine="h5netcdf") as trace:
                local_arrays = {name: trace[name].values.reshape(-1).copy() for name in PARAMETERS}
            with np.load(external_dir / "posterior_samples.npz", allow_pickle=False) as posterior:
                external_arrays = {name: posterior[name].copy() for name in PARAMETERS}
            comparison = compare_posterior_arrays(local_arrays, external_arrays)
            payload.update(status="compared_descriptively", reason=None, comparison=comparison,
                           both_scientifically_interpretable=local["scientifically_interpretable"] and external["scientifically_interpretable"],
                           material_discrepancy_parameters=[name for name, values in comparison["parameters"].items() if values["material_discrepancy_flag"]],
                           claim_limit="Distribution agreement is not proof of correctness; inspect both engines' diagnostics, prior conditioning, Monte Carlo uncertainty and preserved discrepancies.")
            _table(output / "posterior_comparison.csv", [{"parameter": name, **values} for name, values in comparison["parameters"].items()])
    if payload["status"] == "unavailable":
        _table(output / "posterior_comparison.csv", [], ["parameter", "status"])
    _write(output / "benchmark.json", payload)
    return payload


def aggregate_campaign(root: Path, config_path: Path, *, family: str | None = None) -> Path:
    root = root.resolve()
    plan = build_plan(root, config_path)
    if family is not None and family not in plan["phase_order"]:
        raise ValueError("Unknown requested experiment family")
    state_path = safe_path(root, f"artifacts/publication_campaign/{plan['campaign_id']}/campaign_state.json")
    try:
        state = read_campaign_json(state_path)
    except FileNotFoundError:
        state = None
    evidence = collect_campaign(root, plan, state)
    output = safe_path(root, f"reports/publication_campaign/{plan['campaign_id']}" + (f"/{family}" if family else ""))
    output.mkdir(parents=True, exist_ok=True)
    # The controller updates its aggregation bookkeeping immediately after us.
    # Freeze the state actually read; use a jobs-only fingerprint for freshness.
    snapshot = state or {"campaign_id": plan["campaign_id"], "status": "NOT_INITIALIZED", "jobs": {}}
    _write(output / "campaign_state_snapshot.json", snapshot)
    sources = dict(evidence["source_checksums"])
    generator_sources = source_identity(root)
    sources.update(generator_sources)
    identity_paths = ["publication/baseline/manifest.json", "publication/baseline/environment/requirements.txt",
                      "publication/environments/benchmark-environment.json", "publication/environments/benchmark-requirements.txt",
                      "publication/environments/benchmark-conda-explicit.txt"]
    if plan.get("frozen_plan_path"):
        identity_paths.append(plan["frozen_plan_path"])
    for relative in identity_paths:
        if (root / relative).is_file():
            sources[relative] = sha256_file(root / relative)
    aggregate_environment = {"python_version": platform.python_version(), "packages": {}}
    for package in ("numpy", "pandas", "scipy", "matplotlib", "xarray", "h5netcdf"):
        try:
            aggregate_environment["packages"][package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            aggregate_environment["packages"][package] = None
    _write(output / "aggregation_environment.json", aggregate_environment)
    sources[(output / "campaign_state_snapshot.json").relative_to(root).as_posix()] = sha256_file(output / "campaign_state_snapshot.json")
    sources[plan["config_path"]] = sha256_file(root / plan["config_path"])
    for protocol in plan["protocols"].values():
        sources[protocol["path"]] = protocol["sha256"]
    rows = [row for row in evidence["jobs"] if family is None or row["experiment_id"] == family]
    attempts = [row for row in evidence["attempts"] if family is None or row["experiment_id"] == family]
    summaries, generation_errors, family_artifacts = {}, [], []
    for name in dict.fromkeys(row["experiment_id"] for row in rows):
        selected = [row for row in rows if row["experiment_id"] == name]
        destination = output if family else output / name
        destination.mkdir(exist_ok=True)
        try:
            if name in {"PUB-02", "PUB-04"}:
                summaries[name] = calibration_report(selected, destination, mode=plan["mode"])
                family_artifacts += [destination / filename for filename in ("calibration.json", "calibration.csv", "posterior_recovery.csv", "coverage.png", "bias.png", "width.png", "recovery.png", "gate_rates.png")]
                if name == "PUB-04":
                    summaries[name]["ablations"] = ablation_report(selected, destination)
                    family_artifacts += [destination / filename for filename in ("ablation.json", "paired_effects.csv", "gate_matrix.csv", "paired_effects.png")]
            elif name == "PUB-03":
                summaries[name] = benchmark_report(root, selected, destination)
                family_artifacts += [destination / filename for filename in ("benchmark.json", "posterior_comparison.csv")]
            elif name == "PUB-05":
                from publication.target_reporting import write_target_report

                outcomes = []
                for row in selected:
                    result = row.get("result")
                    status = result["status"] if result else "failed" if row["status"] in TERMINAL else "missing"
                    outcomes.append({"target_id": row["scenario_id"], "status": status, "result": result,
                                     "preparation": row.get("preparation"), "source_paths": row["source_paths"],
                                     "error": row.get("error"), "failure_stage": (result or {}).get("failure_stage")})
                write_target_report(root, Path(plan["protocols"][name]["path"]), outcomes, destination, campaign_id=plan["campaign_id"],
                                    regenerate_command=f"python scripts/aggregate_publication_campaign.py --config {plan['config_path']} --family PUB-05")
                summaries[name] = _read(destination / "aggregate.json")
                family_artifacts += [destination / filename for filename in ("aggregate.json", "targets.csv", "posterior_intervals.csv", "posterior_intervals.png", "gate_outcomes.png", "regime_precision.png")]
                if destination != output:
                    family_artifacts += [destination / "REPORT.md", destination / "artifact_manifest.json"]
            else:
                summaries[name] = {"status": "not_implemented", "declared_jobs": len(selected)}
        except (OSError, ValueError, KeyError, TypeError, ImportError) as exc:
            message = f"{name} aggregate unavailable: {exc}"
            generation_errors.append(message)
            summaries[name] = {"status": "aggregate_error", "error": message}
            _write(destination / "aggregate_error.json", summaries[name])
            family_artifacts.append(destination / "aggregate_error.json")
    compact = [{key: value for key, value in row.items() if key not in {"result", "truth", "preparation", "completion", "payload"}} for row in rows]
    status_counts = dict(sorted(Counter(row["status"] for row in rows).items()))
    failures = [row for row in compact if row["status"] in {"FAILED_TECHNICAL", "BLOCKED", "CANCELLED"} or row.get("integrity_errors")]
    rejections = [row for row in compact if row["status"] == "COMPLETED_REJECTED"]
    errors = evidence["integrity_errors"] + generation_errors
    summary = {"schema_version": "publication-campaign-aggregate-v1", "campaign_id": plan["campaign_id"],
               "mode": plan["mode"], "family_filter": family, "campaign_state_status": snapshot["status"],
               "declared_jobs": len(rows), "total_attempts": len(attempts), "status_counts": status_counts,
               "scientifically_interpretable_count": sum(row["scientifically_interpretable"] for row in rows),
               "computational_gates_passed_count": sum(row["computational_gates_passed"] for row in rows),
               "complete_declared_batch": bool(rows) and all(row["status"] in TERMINAL for row in rows),
               "all_declared_scientific_jobs_finished": bool(rows) and all(row["status"] in SCIENTIFIC_TERMINAL for row in rows),
               "integrity_errors": errors, "preflight_errors": plan["preflight_errors"],
               "source_state_jobs_fingerprint": state_fingerprint(snapshot, family),
               "source_state_path": state_path.relative_to(root).as_posix(), "source_checksums": sources,
               "generator_source_checksums": generator_sources, "aggregation_environment": aggregate_environment,
               "campaign_initial_code_commit": snapshot.get("code_commit"),
               "jobs": compact, "attempts": attempts, "families": summaries,
               "claim_limit": "Smoke campaign is infrastructure evidence only. Missing, blocked, failed and rejected jobs remain visible. Numeric metrics are descriptive until complete frozen-protocol scientific evidence, sampler/PPC checks and independent review support stronger claims. No M6 or paper-ready claim is inferred from implementation."}
    _write(output / "summary.json", summary)
    if family is None:
        _write(output / "campaign_summary.json", summary)
    _table(output / "jobs.csv", compact)
    _table(output / "attempts.csv", attempts)
    _table(output / "failures.csv", failures, list(compact[0]) if compact else ["job_id", "status"])
    _table(output / "rejections.csv", rejections, list(compact[0]) if compact else ["job_id", "status"])
    lines = [f"# Publication campaign: {plan['campaign_id']}", "", summary["claim_limit"], "",
             f"Mode: {plan['mode']}; family: {family or 'all'}; controller state: {snapshot['status']}.",
             f"Declared jobs: {len(rows)}. Preserved attempts: {len(attempts)}. Scientifically interpretable: {summary['scientifically_interpretable_count']}.",
             f"Computational gate passes (includes explicitly labeled smoke fixtures, not science): {summary['computational_gates_passed_count']}.",
             f"Statuses: `{json.dumps(status_counts, sort_keys=True)}`.",
             f"Complete declared batch (including terminal failures): {summary['complete_declared_batch']}. All scientific jobs finished: {summary['all_declared_scientific_jobs_finished']}.", "",
             "## Evidence and negative outcomes", "", "`jobs.csv` includes every planned job, including not started. `attempts.csv` retains every earlier interrupted/failed attempt. Only the last registered, sealed and hash-verified attempt supplies numerical evidence; no best-run selection. `failures.csv` and `rejections.csv` separate technical/integrity failures from scientific rejection.",
             "", "Synthetic metrics include 50/80/94% equal-tailed coverage and Wilson intervals, bias, absolute/relative bias, RMSE, SD and interval widths. Rejected numeric posteriors remain, with conditional sampler metrics separated. Operational covered-and-passed fraction is not an interval-calibration estimand. Missing intervals are not measured noncoverage. Fixed-truth repeated coverage is not SBC.",
             "", "## Family artifacts", ""]
    for name in summaries:
        lines.append(f"- `{name}/`: machine-readable results/tables and available figures; absent evidence remains unavailable, not zero.")
        if "scenarios" in summaries[name]:
            lines += ["", "| Scenario | Declared | Numeric r | r bias | r RMSE | r 94% numeric coverage |", "|---|---:|---:|---:|---:|---:|"]
            for scenario, metrics in summaries[name]["scenarios"].items():
                r = metrics["parameters"]["r"]
                values = ["unavailable" if number is None else f"{number:.6g}" for number in (r["bias"], r["rmse"], r["coverage"]["0.94"]["empirical_coverage_numeric"])]
                lines.append(f"| {scenario} | {metrics['declared_count']} | {r['numeric_count']} | {' | '.join(values)} |")
            lines.append("")
    lines += ["", "## Validation issues", ""]
    lines.extend(f"- {error}" for error in errors + plan["preflight_errors"])
    if not errors and not plan["preflight_errors"]:
        lines.append("No detected artifact-integrity or preflight errors. This is not proof of scientific validity.")
    lines += ["", "## Regeneration", "", "```sh", f"python scripts/aggregate_publication_campaign.py --config {plan['config_path']}" + (f" --family {family}" if family else ""), "```", "", "This command only reads sealed scientific artifacts and regenerates derived reports; it never samples. Live controller bookkeeping is not a scientific input: the read snapshot is preserved, and freshness checks use the jobs-only fingerprint plus artifact hashes."]
    (output / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    if family is None:
        (output / "campaign_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    active_files = family_artifacts + [output / filename for filename in ("campaign_state_snapshot.json", "aggregation_environment.json", "summary.json", "jobs.csv", "attempts.csv", "failures.csv", "rejections.csv", "REPORT.md")]
    if family is None:
        active_files += [output / "campaign_summary.json", output / "campaign_summary.md"]
    artifacts = {path.relative_to(output).as_posix(): sha256_file(path) for path in sorted(active_files)}
    _write(output / "artifact_manifest.json", {"schema_version": "publication-derived-v1", "source_checksums": sources,
        "artifacts": artifacts, "source_state_jobs_fingerprint": summary["source_state_jobs_fingerprint"],
        "source_state_path": summary["source_state_path"], "family_filter": family,
        "regenerate_command": f"python scripts/aggregate_publication_campaign.py --config {plan['config_path']}" + (f" --family {family}" if family else "")})
    return output


def validate_campaign_report(root: Path, output: Path) -> None:
    """Fail on stale source/output hashes or changed declared job outcomes."""
    root = root.resolve()
    output = output.resolve()
    manifest = _read(output / "artifact_manifest.json")
    for name, checksum in manifest["source_checksums"].items():
        if sha256_file(safe_path(root, name)) != checksum:
            raise ValueError(f"Stale campaign source: {name}")
    for name, checksum in manifest["artifacts"].items():
        if sha256_file(safe_path(output, name)) != checksum:
            raise ValueError(f"Stale campaign report: {name}")
    state_path = safe_path(root, manifest["source_state_path"])
    try:
        state = read_campaign_json(state_path)
    except FileNotFoundError:
        state = {"jobs": {}}
    if state_fingerprint(state, manifest["family_filter"]) != manifest["source_state_jobs_fingerprint"]:
        raise ValueError("Campaign job state changed since aggregation")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(DEFAULT_CONFIG))
    parser.add_argument("--family", choices=("PUB-02", "PUB-03", "PUB-04", "PUB-05", "PUB-06"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    output = aggregate_campaign(root, args.config, family=args.family)
    summary = _read(output / "summary.json")
    print(json.dumps({"output": output.relative_to(root).as_posix(), "declared_jobs": summary["declared_jobs"], "status_counts": summary["status_counts"], "integrity_errors": summary["integrity_errors"]}))
    if summary["integrity_errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
