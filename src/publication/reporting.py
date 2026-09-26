"""Generate full-denominator calibration evidence, never a curated success list."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd

from publication.calibration import PARAMETERS, coverage_metrics
from publication.contracts import RunIdentity, load_registry, sha256_file, verify_run_artifacts


def dump(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def aggregate(root: Path, protocol_path: Path, *, run_id: str, pilot: bool = False) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    family = protocol["experiment_id"]
    sources = {protocol_path.relative_to(root).as_posix(): sha256_file(protocol_path)}
    if pilot:
        identities = [RunIdentity(family, scenario["scenario_id"], f"rep_{rep:04d}", run_id)
                      for scenario in protocol["scenarios"] for rep in range(protocol.get("replicates_per_scenario", 1))]
    else:
        registry = load_registry(root)
        entry = next(e for e in registry["experiments"] if e["experiment_id"] == family)
        identities = [RunIdentity(**row) for row in entry["expected_runs"] if row["run_id"] == run_id]
        if not identities:
            raise ValueError("No declared final attempts; cannot generate a final evidence report")
        sources["publication/registry.json"] = sha256_file(root / "publication/registry.json")
    scenarios, rows, numeric_rows, attempt_rows = {}, [], [], []
    for scenario_id in sorted({identity.scenario_id for identity in identities}):
        selected = [identity for identity in identities if identity.scenario_id == scenario_id]
        summaries = []
        for identity in selected:
            path = root / identity.relative_path
            if not (path / "result.json").exists():
                attempt_rows.append({"scenario": scenario_id, "replicate_id": identity.replicate_id, "status": "missing"})
                continue
            verify_run_artifacts(path)
            result = json.loads((path / "result.json").read_text(encoding="utf-8"))
            truth_path = path / "truth.json"
            truth = json.loads(truth_path.read_text(encoding="utf-8"))["truth"] if truth_path.exists() else {}
            summary = copy.deepcopy(result)
            summary["replicate_id"] = identity.replicate_id
            for parameter, values in summary.get("parameters", {}).items():
                if parameter in truth:
                    values["truth"] = truth[parameter]
                    numeric_rows.append({"scenario": scenario_id, "replicate_id": identity.replicate_id,
                                         "parameter": parameter, "truth": truth[parameter], "mean": values["mean"],
                                         "sd": values["sd"], "status": result["status"],
                                         "scientific_gate": result["gates"]["scientific"]})
            summaries.append(summary)
            attempt_rows.append({"scenario": scenario_id, "replicate_id": identity.replicate_id,
                                 "status": result["status"], "wall_seconds": result.get("wall_seconds"),
                                 **{f"gate_{key}": value for key, value in result.get("gates", {}).items()},
                                 "error": result.get("error", ""), "path": identity.relative_path})
            for name in ("run_config.json", "inference_config.json", "truth.json", "result.json", "checksums.json"):
                if (path / name).exists():
                    sources[(path / name).relative_to(root).as_posix()] = sha256_file(path / name)
        metrics = coverage_metrics(summaries, [identity.replicate_id for identity in selected])
        scenarios[scenario_id] = metrics
        for parameter, metrics_parameter in metrics["parameters"].items():
            for nominal, coverage in metrics_parameter["coverage"].items():
                rows.append({"scenario": scenario_id, "parameter": parameter, "nominal": float(nominal),
                             "declared_count": metrics["declared_count"],
                             "bias": metrics_parameter["bias"], "absolute_bias": metrics_parameter["absolute_bias"],
                             "relative_bias": metrics_parameter.get("relative_bias"), "rmse": metrics_parameter["rmse"],
                             "mean_posterior_sd": metrics_parameter["mean_posterior_sd"], **coverage})
    output = root / "publication/derived" / family / run_id
    output.mkdir(parents=True, exist_ok=True)
    table, numeric, attempts = pd.DataFrame(rows), pd.DataFrame(numeric_rows), pd.DataFrame(attempt_rows)
    table.to_csv(output / "calibration.csv", index=False, lineterminator="\n")
    numeric.to_csv(output / "posterior_recovery.csv", index=False, lineterminator="\n")
    attempts.to_csv(output / "attempts.csv", index=False, lineterminator="\n")
    all_terminal = all(row["status"] in {"completed", "failed", "rejected", "not_interpretable"} for row in attempt_rows)
    payload = {"experiment_id": family, "run_id": run_id, "mode": "pilot" if pilot else "final",
               "complete_declared_batch": all_terminal, "declared_attempts": len(identities),
               "declared_run_paths": [identity.relative_path for identity in identities],
               "result_source_sha256": {name: digest for name, digest in sources.items() if name.endswith("/result.json")},
               "status_counts": attempts.status.value_counts().to_dict(), "scenarios": scenarios,
               "source_checksums": sources,
               "claim_limit": "Pilot: feasibility only" if pilot else "Fixed-truth coverage in declared regimes; not SBC or global proof of calibration."}
    dump(output / "aggregate.json", payload)
    names = list(scenarios)
    fig, axes = plt.subplots(2, 4, figsize=(15, 7), constrained_layout=True)
    for ax, parameter in zip(axes.flat, PARAMETERS, strict=False):
        ax.plot([.45, 1.], [.45, 1.], color="black", linestyle="--", linewidth=1)
        for scenario, result in scenarios.items():
            p = result["parameters"][parameter]
            coverage = list(p["coverage"].values())
            usable = [row for row in coverage if row["empirical_coverage_numeric"] is not None]
            if usable:
                x = np.array([row["nominal"] for row in usable])
                y = np.array([row["empirical_coverage_numeric"] for row in usable])
                bounds = np.array([row["wilson95_numeric"] for row in usable]).T
                ax.errorbar(x, y, yerr=np.maximum(np.vstack([y-bounds[0], bounds[1]-y]), 0), marker="o", alpha=.7, label=scenario)
        ax.set(title=parameter, xlabel="Nominal equal-tailed coverage", ylabel="Empirical numeric coverage", ylim=(-.03, 1.03), xlim=(.45, 1.))
    axes.flat[-1].axis("off")
    handles, labels = axes.flat[0].get_legend_handles_labels()
    axes.flat[-1].legend(handles, labels, loc="center", fontsize=8)
    fig.suptitle(f"{family} {run_id}: Wilson 95% intervals; {'PILOT — not final evidence' if pilot else 'all available posteriors, including rejected runs'}")
    fig.savefig(output / "coverage.png", dpi=170)
    plt.close(fig)
    fig, axes = plt.subplots(2, 4, figsize=(15, 7), constrained_layout=True)
    for ax, parameter in zip(axes.flat, PARAMETERS, strict=False):
        if not numeric.empty:
            selected = numeric.loc[numeric.parameter == parameter]
            for scenario, group in selected.groupby("scenario", sort=True):
                ax.errorbar(group.truth, group["mean"], yerr=group.sd, fmt=".", alpha=.5, label=scenario)
            if len(selected):
                minimum = float(min(selected.truth.min(), selected["mean"].min()))
                maximum = float(max(selected.truth.max(), selected["mean"].max()))
                ax.plot([minimum, maximum], [minimum, maximum], "k--", linewidth=1)
        ax.set(title=parameter, xlabel="Injected truth", ylabel="Posterior mean ± SD")
    axes.flat[-1].axis("off")
    fig.suptitle("Recovery (SD bars are not coverage intervals); rejected posteriors retained")
    fig.savefig(output / "recovery.png", dpi=170)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True)
    for gate in ("sampler", "ppc", "scientific"):
        axes[0].plot(names, [scenarios[name]["gates"][gate]["pass_rate_all_declared"] for name in names], "o-", label=gate)
    axes[0].set(ylim=(-.03, 1.03), ylabel="Pass count / all declared", title="Unsuccessful/missing attempts remain in denominator")
    axes[0].legend()
    for parameter in ("r", "depth"):
        axes[1].plot(names, [scenarios[name]["parameters"][parameter].get("relative_bias", np.nan) for name in names], "o-", label=parameter)
    axes[1].axhline(0, color="black", linewidth=.7)
    axes[1].set(ylabel="Relative posterior-center bias", title="Scenario-conditioned bias")
    axes[1].legend()
    for ax in axes:
        ax.tick_params(axis="x", rotation=35)
    fig.savefig(output / "failures_bias.png", dpi=170)
    plt.close(fig)
    lines = [f"# {family} — {run_id}", "", payload["claim_limit"], "",
             f"Declared attempts: {len(identities)}. Complete declared batch: {all_terminal}.",
             f"Status counts: `{json.dumps(payload['status_counts'], sort_keys=True)}`.", "",
             "## Coverage and failure interpretation", "",
             "Numeric coverage includes available rejected posteriors and is conditional on numerical output; "
             "it is not trustworthy calibration when sampler diagnostics fail. Gate-conditioned coverage is "
             "a selected estimand. Operational covered-and-passed rate uses every declared replicate; missing "
             "intervals are NOT treated as observed noncoverage. Wilson intervals quantify simulation precision, "
             "not systematic model error. Fixed-truth experiments are not SBC.", "",
             "Exact segment calibration is assumed in this simulator; empirical preprocessing error requires "
             "the separate normalization ablation. Shared physical primitives remain a circularity risk; "
             "independent forward/posterior checks are separate evidence.", "",
             "| Scenario | Declared | Numeric r | r bias | r RMSE | r 94% coverage | Sampler passed | Final gate passed |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name, metrics in scenarios.items():
        r = metrics["parameters"]["r"]
        def formatted(value):
            return "unavailable" if value is None else f"{value:.6g}"
        lines.append(f"| {name} | {metrics['declared_count']} | {r['numeric_count']} | {formatted(r['bias'])} | {formatted(r['rmse'])} | {formatted(r['coverage']['0.94']['empirical_coverage_numeric'])} | {metrics['gates']['sampler']['passed_count']} | {metrics['gates']['scientific']['passed_count']} |")
    lines += ["", "All parameters, interval widths and denominators: `calibration.csv` and `aggregate.json`.",
              "Every attempted/missing identity: `attempts.csv`. Per-run posterior recovery: `posterior_recovery.csv`.",
              "Figures: `coverage.png`, `recovery.png`, `failures_bias.png`.", "",
              "No LOO/WAIC ranking is performed by this report. Quantitative claims must respect sampler and protocol status."]
    (output / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    dump(output / "artifact_manifest.json", {"schema_version": "publication-derived-v1", "source_checksums": sources,
        "artifacts": {path.name: sha256_file(path) for path in sorted(output.iterdir()) if path.is_file() and path.name != "artifact_manifest.json"},
        "regenerate_command": f"python scripts/summarize_publication.py {protocol_path.relative_to(root).as_posix()} --run-id {run_id}" + (" --pilot" if pilot else "")})
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("protocol", type=Path)
    parser.add_argument("--run-id", default="final_001")
    parser.add_argument("--pilot", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    print(aggregate(root, args.protocol.resolve(), run_id=args.run_id, pilot=args.pilot))


if __name__ == "__main__":
    main()
