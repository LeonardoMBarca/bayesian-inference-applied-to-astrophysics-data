"""Independent, read-only posterior/coverage audit of frozen P2 campaigns.

No producer, inference, calibration or synthesis functions are imported. Means
and variances use Python's compensated summation, quantiles explicit sorted
linear interpolation, and Wilson limits the score-test quadratic. NetCDF is a
data input, never a reason to resample or repair rejected chains.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import subprocess
from collections import Counter
from pathlib import Path, PurePosixPath

import numpy as np

PARAMETERS = ("r", "depth", "b", "a", "t0", "full_duration", "extra_sigma")
LEVELS = (0.5, 0.8, 0.94)
SUBSETS = ("all_numeric", "sampler_passed", "joint_gate_passed")
CAMPAIGNS = ("tcc_campaign_v1", "tcc_calibration_confirmatory_v1")
SCHEMA = "independent-posterior-trace-audit-v1"
REL_TOL = 5e-12
ABS_TOL = 5e-14


def safe_file(root: Path, relative: str, *, checked_directories: set[Path] | None = None) -> Path:
    """Only explicit repository-relative paths; never follow a symbolic link."""
    path = PurePosixPath(relative)
    if not relative or path.is_absolute() or ".." in path.parts or "\\" in relative or ":" in relative:
        raise ValueError(f"Unsafe source path: {relative}")
    # Sources resolves the root once. The optional prefix cache is scoped to
    # this read-only audit of frozen evidence, not a hostile concurrently
    # changing filesystem. File bytes are hashed on every access regardless.
    root = root.resolve() if checked_directories is None else root
    candidate = root / relative
    checked = []
    for parent in (candidate, *candidate.parents):
        if parent == root:
            break
        if parent != candidate and checked_directories is not None and parent in checked_directories:
            break
        if parent.is_symlink() or (os.name == "nt" and parent.is_junction()):
            raise ValueError(f"Symbolic source path: {relative}")
        if parent != candidate:
            checked.append(parent)
    if checked_directories is not None:
        checked_directories.update(checked)
    return candidate


class Sources:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.checksums: dict[str, str] = {}
        self.checked_directories: set[Path] = set()

    def read(self, relative: str, expected: str | None = None) -> bytes:
        content = safe_file(self.root, relative, checked_directories=self.checked_directories).read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        if expected is not None and digest != expected:
            raise ValueError(f"Source checksum mismatch: {relative}")
        if relative in self.checksums and self.checksums[relative] != digest:
            raise ValueError(f"Source changed during audit: {relative}")
        self.checksums[relative] = digest
        return content

    def json(self, relative: str, expected: str | None = None):
        return json.loads(self.read(relative, expected))


def linear_quantile(ordered: list[float], probability: float) -> float:
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def summarize_draws(values) -> dict:
    values = [float(value) for value in np.asarray(values).reshape(-1)]
    if len(values) < 2 or not all(math.isfinite(value) for value in values):
        raise ValueError("Trace requires at least two finite draws; no invalid-draw removal")
    center = math.fsum(values) / len(values)
    variance = math.fsum((value - center) ** 2 for value in values) / (len(values) - 1)
    ordered = sorted(values)
    return {
        "draw_count": len(values), "mean": center, "sd": math.sqrt(variance),
        "interval_method": "equal_tailed",
        "intervals": {str(level): [linear_quantile(ordered, (1 - level) / 2),
                                    linear_quantile(ordered, (1 + level) / 2)]
                      for level in LEVELS},
    }


def score_interval(successes: int, total: int) -> list[float] | None:
    """95% Wilson interval by solving the inverted score-test quadratic."""
    if type(total) is not int or type(successes) is not int or not 0 <= successes <= total:
        raise ValueError("Invalid binomial counts")
    if total == 0:
        return None
    z_squared = 1.959963984540054 ** 2
    a, b, c = total + z_squared, -(2 * successes + z_squared), successes**2 / total
    discriminant = max(0.0, b * b - 4 * a * c)
    return [max(0.0, (-b - math.sqrt(discriminant)) / (2 * a)),
            min(1.0, (-b + math.sqrt(discriminant)) / (2 * a))]


def close(actual, expected) -> bool:
    if actual is None or expected is None:
        return actual is expected
    return math.isfinite(actual) and math.isfinite(expected) and math.isclose(
        actual, expected, rel_tol=REL_TOL, abs_tol=ABS_TOL)


def compare_parameter(actual: dict, stored: dict) -> dict:
    differences = []
    matched = stored.get("interval_method") == "equal_tailed"
    for field in ("mean", "sd"):
        value = stored.get(field)
        matched = matched and value is not None and close(actual[field], value)
        if value is not None:
            differences.append(abs(actual[field] - value))
    for level in LEVELS:
        bounds = stored.get("intervals", {}).get(str(level), [])
        if len(bounds) != 2:
            matched = False
        else:
            for actual_bound, stored_bound in zip(actual["intervals"][str(level)], bounds, strict=True):
                matched = matched and close(actual_bound, stored_bound)
                differences.append(abs(actual_bound - stored_bound))
    return {"matched": matched, "max_absolute_difference": max(differences, default=None)}


def joint_pass(record: dict) -> bool:
    return record.get("status") == "COMPLETED" and all(
        record.get("gates", {}).get(gate) is True
        for gate in ("provenance", "sampler", "ppc", "scientific"))


def average(values: list[float]) -> float | None:
    return math.fsum(values) / len(values) if values else None


def aggregate(records: list[dict], parameter: str, subset: str) -> dict:
    """All records are declared jobs; absent values remain unavailable, not zero."""
    if subset not in SUBSETS:
        raise ValueError("Unknown subset")
    included = [row for row in records if parameter in row.get("parameters", {})
                and (subset != "sampler_passed" or row.get("gates", {}).get("sampler") is True)
                and (subset != "joint_gate_passed" or joint_pass(row))]
    values = [row["parameters"][parameter] for row in included]
    errors = [row["mean"] - row["truth"] for row in values]
    bias = average(errors)
    result = {
        "subset": subset, "parameter": parameter, "declared_count": len(records),
        "numeric_count": len(values), "not_in_subset_count": len(records) - len(values),
        "bias": bias, "absolute_bias": abs(bias) if bias is not None else None,
        "relative_bias": average([(row["mean"] - row["truth"]) / row["truth"]
                                  for row in values if row["truth"] != 0]),
        "relative_bias_nonzero_truth_count": sum(row["truth"] != 0 for row in values),
        "mae": average([abs(error) for error in errors]),
        "rmse": math.sqrt(average([error**2 for error in errors])) if errors else None,
        "mean_posterior_sd": average([row["sd"] for row in values]),
        "coverage": {},
    }
    for level in LEVELS:
        key = str(level)
        count = sum(row["intervals"][key][0] <= row["truth"] <= row["intervals"][key][1]
                    for row in values)
        empirical = count / len(values) if values else None
        result["coverage"][key] = {
            "nominal": level, "covered_count": count, "denominator": len(values),
            "empirical_coverage": empirical, "wilson95": score_interval(count, len(values)),
            "mean_interval_width": average([row["intervals"][key][1] - row["intervals"][key][0]
                                             for row in values]),
            "calibration_error": empirical - level if empirical is not None else None,
        }
    result["mean_absolute_calibration_error"] = average([
        abs(row["calibration_error"]) for row in result["coverage"].values()
        if row["calibration_error"] is not None])
    return result


def operational_yield(records: list[dict], parameter: str) -> dict:
    result = {}
    for level in LEVELS:
        count = sum(joint_pass(row) and (value := row.get("parameters", {}).get(parameter)) is not None
                    and value["intervals"][str(level)][0] <= value["truth"] <= value["intervals"][str(level)][1]
                    for row in records)
        result[str(level)] = {"covered_and_joint_passed": count, "all_declared": len(records),
                              "rate": count / len(records) if records else None,
                              "wilson95": score_interval(count, len(records))}
    return result


def audit_trace(content: bytes, period: float) -> tuple[dict, dict]:
    import xarray as xr

    with xr.open_dataset(io.BytesIO(content), group="posterior", engine="h5netcdf") as dataset:
        arrays = {}
        for name in PARAMETERS:
            if dataset[name].dims != ("chain", "draw"):
                raise ValueError(f"Unexpected scalar posterior dimensions: {name}")
            arrays[name] = np.asarray(dataset[name].values, dtype=float)
        if any(value.shape != arrays["r"].shape for value in arrays.values()):
            raise ValueError("Posterior dimensions differ by parameter")
        radius, impact, scale = (arrays[name] for name in ("r", "b", "a"))
        argument = np.sqrt(((1 + radius) ** 2 - impact**2) / (scale**2 - impact**2))
        duration = period / math.pi * np.arcsin(np.clip(argument, 0, 1))
        derived = {
            "depth_equals_squared_radius": bool(np.allclose(arrays["depth"], radius**2, atol=ABS_TOL, rtol=REL_TOL)),
            "duration_equals_circular_contact_formula": bool(np.allclose(arrays["full_duration"], duration, atol=ABS_TOL, rtol=REL_TOL)),
            "chains": arrays["r"].shape[0], "draws_per_chain": arrays["r"].shape[1],
            "t0_chain_means_days": [math.fsum(chain) / len(chain) for chain in arrays["t0"]],
        }
        return {name: summarize_draws(values) for name, values in arrays.items()}, derived


def compare_aggregate(metrics: dict, historical: dict, yields: dict) -> list[str]:
    errors = []
    for parameter in PARAMETERS:
        new = metrics[parameter]["all_numeric"]
        old = historical["parameters"][parameter]
        for key in ("bias", "absolute_bias", "relative_bias", "mae", "rmse", "mean_posterior_sd", "mean_absolute_calibration_error", "numeric_count"):
            if not close(new[key], old.get(key)):
                errors.append(f"{parameter}.{key}")
        sampler = metrics[parameter]["sampler_passed"]
        for key, old_key in (("bias", "bias_conditional_on_sampler"), ("rmse", "rmse_conditional_on_sampler")):
            if not close(sampler[key], old.get(old_key)):
                errors.append(f"{parameter}.{old_key}")
        for level in LEVELS:
            key = str(level)
            before = old["coverage"][key]
            for subset, coverage_key, denominator_key, interval_key in (
                ("all_numeric", "empirical_coverage_numeric", "numeric_count", "wilson95_numeric"),
                ("sampler_passed", "coverage_conditional_on_sampler", "sampler_passed_numeric_count", "wilson95_conditional_on_sampler"),
                ("joint_gate_passed", "coverage_conditional_on_scientific_gate", "scientific_gate_passed_numeric_count", "wilson95_conditional_on_scientific_gate"),
            ):
                after = metrics[parameter][subset]["coverage"][key]
                for actual, expected in ((after["empirical_coverage"], before.get(coverage_key)),
                                         (after["denominator"], before.get(denominator_key))):
                    if not close(actual, expected):
                        errors.append(f"{parameter}.{key}.{subset}.coverage_or_denominator")
                if after["wilson95"] is None or before.get(interval_key) is None:
                    if after["wilson95"] != before.get(interval_key):
                        errors.append(f"{parameter}.{key}.{subset}.wilson")
                elif not all(close(a, b) for a, b in zip(after["wilson95"], before[interval_key], strict=True)):
                    errors.append(f"{parameter}.{key}.{subset}.wilson")
            if not close(new["coverage"][key]["mean_interval_width"], before.get("mean_interval_width")):
                errors.append(f"{parameter}.{key}.width")
            if not close(yields[parameter][key]["rate"], before.get("operational_covered_and_passed_rate_all_declared")):
                errors.append(f"{parameter}.{key}.operational_yield")
    return errors


def audit_campaign(sources: Sources, campaign: str) -> dict:
    report_dir = f"reports/publication_campaign/{campaign}"
    manifest = sources.json(f"{report_dir}/artifact_manifest.json")
    summary = sources.json(f"{report_dir}/summary.json", manifest["artifacts"]["summary.json"])
    ledger_path = f"configs/publication/{campaign}_plan.json"
    ledger = sources.json(ledger_path, manifest["source_checksums"][ledger_path])
    calibration_path = f"{report_dir}/PUB-02/calibration.json"
    family_manifest = sources.json(f"{report_dir}/PUB-02/artifact_manifest.json", manifest["artifacts"]["PUB-02/artifact_manifest.json"])
    historical = sources.json(calibration_path, family_manifest["artifacts"]["calibration.json"])
    jobs = {row["job_id"]: row for row in summary["jobs"]}
    if len(jobs) != len(summary["jobs"]) or set(jobs) != {row["job_id"] for row in ledger["declared_jobs"]}:
        raise ValueError("Duplicate, missing or undeclared campaign jobs")
    declared = [row for row in ledger["declared_jobs"] if row["experiment_id"] == "PUB-02"]
    if not declared or len({row["job_id"] for row in declared}) != len(declared):
        raise ValueError("Empty or duplicate P2 declaration")
    records, errors = [], []
    attempts = [row for row in summary["attempts"] if row["experiment_id"] == "PUB-02"]
    for index, planned in enumerate(declared):
        job = jobs[planned["job_id"]]
        for key in ("experiment_id", "scenario_id", "replicate_id", "run_id", "seeds"):
            if job[key] != planned[key]:
                raise ValueError(f"Changed declared identity: {planned['job_id']}:{key}")
        own_attempts = [row for row in attempts if row["job_id"] == planned["job_id"]]
        if len(own_attempts) != job["attempt_count"] or not own_attempts:
            raise ValueError("Attempt denominator mismatch")
        for ordinal, attempt in enumerate(own_attempts):
            if attempt["attempt_index"] != ordinal or attempt["seeds"] != planned["seeds"]:
                raise ValueError("Attempt order or seed changed")
        record = {key: planned[key] for key in ("job_id", "scenario_id", "replicate_id", "run_id", "seeds")}
        record.update(status=job["status"], attempt_count=len(own_attempts), gates={}, parameters={})
        directory = job.get("authoritative_attempt_dir")
        if directory is not None:
            expected_dir = (f"artifacts/publication_campaign/{campaign}/runs/PUB-02/"
                            f"{planned['scenario_id']}/{planned['replicate_id']}/attempt_{len(own_attempts)-1:03d}")
            if directory != expected_dir:
                raise ValueError("Authoritative attempt path mismatch")
            def read(name):
                return sources.read(f"{directory}/{name}", manifest["source_checksums"][f"{directory}/{name}"])
            completion = json.loads(read("completion_manifest.json"))
            result, truth, payload = (json.loads(read(name)) for name in ("result.json", "truth.json", "job.json"))
            if any(payload[key] != value for key, value in planned.items()):
                raise ValueError("Executed job differs from frozen ledger")
            for name in ("result.json", "truth.json", "job.json", "trace.nc"):
                if completion["artifacts"][name] != manifest["source_checksums"][f"{directory}/{name}"]:
                    raise ValueError("Completion and report disagree on source identity")
            trace_bytes = read("trace.nc")
            if result["trace_sha256"] != sources.checksums[f"{directory}/trace.nc"]:
                raise ValueError("Trace differs from sealed result")
            if truth["seed"] != planned["seeds"]["generation"] or result["input_sha256"] != truth["data_sha256"]:
                raise ValueError("Truth generation/input identity mismatch")
            if any(truth["truth"].get(key) != value for key, value in planned["payload"]["scenario"]["truth"].items()):
                raise ValueError("Stored generating truth differs from the frozen ledger")
            if completion["status"] != job["status"] or completion["gates"] != result["gates"]:
                raise ValueError("Status/gate identity mismatch")
            parameters, derived = audit_trace(trace_bytes, planned["payload"]["inference"]["period_days"])
            for name, values in parameters.items():
                values["truth"] = truth["truth"][name]
                if not math.isfinite(values["truth"]):
                    raise ValueError("Nonfinite simulation truth")
                values["stored_comparison"] = compare_parameter(values, result["parameters"].get(name, {}))
                if not values["stored_comparison"]["matched"]:
                    errors.append(f"{planned['job_id']}:{name}:stored_summary_mismatch")
            if not derived["depth_equals_squared_radius"] or not derived["duration_equals_circular_contact_formula"]:
                errors.append(f"{planned['job_id']}:derived_parameter_mismatch")
            record.update(gates=result["gates"], parameters=parameters, trace_path=f"{directory}/trace.nc", derived_checks=derived)
        records.append(record)
        if (index + 1) % 20 == 0:
            print(f"{campaign}: {index + 1}/{len(declared)} traces audited", flush=True)
    scenarios = {}
    for scenario in sorted({row["scenario_id"] for row in records}):
        rows = [row for row in records if row["scenario_id"] == scenario]
        metrics = {parameter: {subset: aggregate(rows, parameter, subset) for subset in SUBSETS}
                   for parameter in PARAMETERS}
        yields = {parameter: operational_yield(rows, parameter) for parameter in PARAMETERS}
        discrepancies = compare_aggregate(metrics, historical["scenarios"][scenario], yields)
        errors.extend(f"{scenario}:aggregate:{item}" for item in discrepancies)
        scenarios[scenario] = {"metrics": metrics, "operational_yield": yields,
                               "counts": summarize_counts(rows), "historical_aggregate_discrepancies": discrepancies}
    return {"campaign_id": campaign, "counts": summarize_counts(records),
            "campaign_all_families_declared_jobs": len(ledger["declared_jobs"]),
            "campaign_all_families_attempts": len(summary["attempts"]),
            "p2_attempts": len(attempts), "p2_attempt_status_counts": dict(Counter(row["status"] for row in attempts)),
            "attempt_inventory": [{key: row.get(key) for key in ("job_id", "scenario_id", "replicate_id", "attempt_index", "status", "authoritative", "output_dir", "seeds")} for row in attempts],
            "runs": records, "scenarios": scenarios, "discrepancies": errors}


def summarize_counts(records: list[dict]) -> dict:
    return {"declared_jobs": len(records), "status_counts": dict(Counter(row["status"] for row in records)),
            "numeric_jobs": sum(bool(row.get("parameters")) for row in records),
            "technical_failure_jobs": sum(row["status"] == "FAILED_TECHNICAL" for row in records),
            "rejected_jobs": sum(row["status"] == "COMPLETED_REJECTED" for row in records),
            "joint_gate_passed_jobs": sum(joint_pass(row) for row in records),
            "gates": {gate: {"passed": sum(row.get("gates", {}).get(gate) is True for row in records),
                              "rejected": sum(row.get("gates", {}).get(gate) is False for row in records),
                              "unassessed": sum(row.get("gates", {}).get(gate) is None for row in records)}
                      for gate in ("provenance", "sampler", "ppc", "scientific")}}


def write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows({key: json.dumps(value, sort_keys=True) if isinstance(value, (list, dict)) else value
                         for key, value in row.items()} for row in rows)


def build_audit(root: Path, output: Path, campaigns=CAMPAIGNS) -> dict:
    if output.exists():
        raise FileExistsError("Audit output exists; preserve it and select a new version")
    sources = Sources(root)
    cohorts = {campaign: audit_campaign(sources, campaign) for campaign in campaigns}
    for name in ("src/publication/trace_audit.py", "scripts/audit_publication_traces.py"):
        sources.read(name)
    report = {"schema_version": SCHEMA, "status": "PASS" if not any(row["discrepancies"] for row in cohorts.values()) else "FAIL",
              "source_code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
              "code_identity_semantics": "HEAD is context, not a clean-checkout claim; exact executed auditor source hashes are bound below.",
              "comparison_tolerance": {"relative": REL_TOL, "absolute": ABS_TOL},
              "independence": "Direct NetCDF values; no shared producer/aggregator imports. math.fsum, sample variance, sorted linear quantiles and inverted score quadratic.",
              "limits": ["Fixed-truth repeated-sampling ETI coverage, not SBC or observational PPC.",
                         "All-numeric metrics retain nonconverged/rejected MCMC outputs, which need not estimate exact posterior quantities reliably.",
                         "Sampler/joint-gate conditioning is selection, not repair of unconditional coverage.",
                         "Covered-and-joint-passed/all-declared is operational yield, not coverage.",
                         "r and geometric depth r^2 coverage events are not independent confirmations.",
                         "95% Wilson limits are pointwise, not simultaneous across parameter/scenario/level comparisons.",
                         "Unavailable diagnostics are null/unassessed, not numerical zero or a measured failure.",
                         "This read-only audit verifies summaries/derived geometry, not the scientific adequacy of the forward model."],
              "filesystem_assumption": "Inputs and directory topology remain immutable during the read-only audit; checked directory prefixes are cached. This is not an adversarial concurrent-filesystem sandbox.",
              "cohorts": cohorts, "source_checksums": sources.checksums}
    output.mkdir(parents=True)
    write_json(output / "audit.json", report)
    calibration_rows, posterior_rows, attempt_rows = [], [], []
    for campaign, cohort in cohorts.items():
        attempt_rows.extend({"campaign_id": campaign, **row} for row in cohort["attempt_inventory"])
        for scenario, values in cohort["scenarios"].items():
            for parameter, subsets in values["metrics"].items():
                for subset, metrics in subsets.items():
                    for level, coverage in metrics["coverage"].items():
                        calibration_rows.append({"campaign_id": campaign, "scenario_id": scenario,
                                                 **{key: value for key, value in metrics.items() if key != "coverage"},
                                                 **coverage, "operational_yield_all_declared": values["operational_yield"][parameter][level]["rate"]})
        for run in cohort["runs"]:
            for parameter, values in run["parameters"].items():
                posterior_rows.append({"campaign_id": campaign, "job_id": run["job_id"], "scenario_id": run["scenario_id"],
                                       "parameter": parameter, "status": run["status"], "gates": run["gates"], **values})
    write_csv(output / "calibration.csv", calibration_rows)
    write_csv(output / "posterior_audit.csv", posterior_rows)
    write_csv(output / "attempt_inventory.csv", attempt_rows)
    lines = ["# Independent posterior trace audit", "", f"Status: {report['status']}. No inference executed; historical artifacts unchanged.", "",
             "Means, sample SD and ETI50/80/94 were reconstructed directly from every declared available trace, including rejected draws/chains.", "",
             "| Cohort | P2 declared | P2 attempts | Numeric | Sampler pass | Joint pass | Rejected | Discrepancies |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for campaign, cohort in cohorts.items():
        counts = cohort["counts"]
        lines.append(f"| {campaign} | {counts['declared_jobs']} | {cohort['p2_attempts']} | {counts['numeric_jobs']} | {counts['gates']['sampler']['passed']} | {counts['joint_gate_passed_jobs']} | {counts['rejected_jobs']} | {len(cohort['discrepancies'])} |")
    lines += ["", "## Interpretation", "", *[f"- {item}" for item in report["limits"]], "",
              "The JSON/CSV retain three separate estimands (all numeric, sampler-selected, joint-gate-selected), explicit denominators, unavailable values, bias/RMSE/widths, Wilson limits and operational yield. Cohorts are never pooled.", "",
              "Reproduction: `python scripts/audit_publication_traces.py --output publication/validation/trace_audit_new_version`.",
              "Byte freshness: `python scripts/audit_publication_traces.py --check --output publication/validation/trace_audit_v1`.", ""]
    (output / "REPORT.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    artifacts = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in output.iterdir() if path.is_file()}
    write_json(output / "artifact_manifest.json", {"schema_version": SCHEMA, "source_checksums": sources.checksums, "artifacts": artifacts})
    return report


def verify_audit(root: Path, output: Path) -> None:
    manifest = json.loads((output / "artifact_manifest.json").read_text(encoding="utf-8"))
    sources = Sources(root)
    for relative, digest in manifest["source_checksums"].items():
        sources.read(relative, digest)
    artifacts = Sources(output)
    for relative, digest in manifest["artifacts"].items():
        artifacts.read(relative, digest)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, default=Path("publication/validation/trace_audit_v1"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    if args.check:
        verify_audit(root, output)
        print("Trace audit sources and artifacts match their exact bytes.")
    else:
        report = build_audit(root, output)
        print(json.dumps({"status": report["status"], "output": str(output)}))
        if report["status"] != "PASS":
            raise SystemExit(1)
