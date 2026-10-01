"""Prospective, bounded numerical follow-up using the existing campaign engine.

No historical run is replaced. This module declares paired new simulations,
three local Monte Carlo repetitions on one observational input, and explicit
reuse of the old external fit. It never starts sampling when preparing a plan.
"""

from __future__ import annotations

import copy
import csv
import json
import math
import statistics
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from publication.contracts import sha256_file

STUDY_KIND = "numerical_complement_v1"
CAMPAIGN_ID = "tcc_numerical_complement_v1"
EXTERNAL_ATTEMPT = "artifacts/publication_campaign/tcc_campaign_v1/runs/PUB-03/kepler_10_b_external/rep_0000/attempt_000"
CLAIM_LIMIT = (
    "Small prospective numerical study, not precise calibration or universal alias prevention. "
    "All new realizations and rejected attempts remain. Three local benchmark repetitions "
    "share one observational dataset and the SAME historical external posterior; they are "
    "not three independent external validations. Numerical agreement is not astrophysical adequacy."
)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_new(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def historical_costs(root: Path, *, cores: int = 2) -> dict:
    """Use all historical attempts in the selected regimes, never gate filtering."""
    inventory = root / "reports/publication_synthesis/tcc_evidence_v1/attempt_inventory.csv"
    wanted = {"deep_short", "intermediate_long", "long_segment_offsets__baseline", "kepler_10_b_local"}
    groups = {name: [] for name in wanted}
    sources = {inventory.relative_to(root).as_posix(): sha256_file(inventory)}
    with inventory.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["campaign_id"] != "tcc_campaign_v1" or row["scenario_id"] not in wanted:
                continue
            attempt = root / row["output_dir"]
            completion_path, configuration_path = attempt / "completion_manifest.json", attempt / "inference_config.json"
            completion, configuration = _read(completion_path), _read(configuration_path)
            for path in (completion_path, configuration_path):
                sources[path.relative_to(root).as_posix()] = sha256_file(path)
            groups[row["scenario_id"]].append({
                "run_id": row["job_id"], "status": row["status"],
                "wall_seconds": completion["wall_seconds"], "sampling": configuration["sampling"],
            })
    estimates = {}
    for name, rows in groups.items():
        if not rows:
            raise ValueError(f"Historical runtime evidence unavailable: {name}")
        # A resource-scaling sensitivity calculation, not a measured speedup law.
        adjusted = [row["wall_seconds"] * max(1, row["sampling"]["cores"] / cores) for row in rows]
        estimates[name] = {
            "historical_attempts": rows, "historical_count": len(rows),
            "historical_median_seconds": statistics.median(row["wall_seconds"] for row in rows),
            "resource_adjusted_median_seconds": statistics.median(adjusted),
            "resource_adjusted_max_seconds": max(adjusted),
        }
    return {
        "groups": estimates, "source_checksums": sources, "planned_cores_per_run": cores,
        "method": "All original-cohort attempts in selected designs; median and maximum measured worker wall time, multiplied by max(1,historical_cores/planned_cores) as a conservative planning sensitivity, not a performance law.",
        "high_accuracy_multiplier": 4,
        "high_accuracy_rationale": "Twice tune+draw count and an unvalidated additional factor two for target_accept .99 versus .95. NUTS tree growth can exceed this; no probabilistic completion guarantee.",
        "benchmark_precision": "Only one historical local benchmark cost is available; it does not estimate a runtime distribution.",
    }


def prepare_study(root: Path, campaign_id: str = CAMPAIGN_ID) -> Path:
    """Create NEW protocol/config files only; a separate committed freeze is required."""
    from publication.campaign_plan import _safe

    _safe(campaign_id)
    root = root.resolve()
    config_path = root / f"configs/publication/{campaign_id}.json"
    protocol_paths = {family: f"publication/protocols/{family}-{campaign_id}.json" for family in ("PUB-02", "PUB-03", "PUB-04")}
    destinations = [config_path, *(root / path for path in protocol_paths.values())]
    if any(path.exists() for path in destinations) or (root / f"artifacts/publication_campaign/{campaign_id}/campaign_state.json").exists():
        raise FileExistsError("Complementary study identity already exists; preserve it and use a new ID")
    originals = {family: _read(root / f"publication/protocols/{family}.json") for family in protocol_paths}
    original_hashes = {f"publication/protocols/{family}.json": sha256_file(root / f"publication/protocols/{family}.json") for family in originals}
    budget = historical_costs(root)
    common = {
        "protocol_version": "numerical-complement-1.0.0", "protocol_status": "FROZEN",
        "date_specified_utc": datetime.now(UTC).isoformat(), "study_kind": STUDY_KIND,
        "campaign_id": campaign_id, "historical_protocol_checksums": original_hashes,
        "model_versions": {"direct": "M5-publication-v1", "standardized": "M5-publication-v2-standardized-t0"},
        "selection_timing": "Post-historical-results hypothesis, prospectively fixed NEW datasets and inference seeds. Historical failures motivate the study but are not its independent final validation.",
        "pilot_policy": "All t0_coordinate_pilot_v1/debug outcomes excluded from final counts; no seed selected by pilot quality.",
        "replicates": 3, "seed_policy": "Existing campaign_plan.seed with this NEW campaign namespace. Within synthetic pairs only generation seed is shared via pair_id; independent inference/predictive/resampling streams are fixed in the committed ledger. No reseeding after rejection.",
        "gates": copy.deepcopy(originals["PUB-02"]["gates"]),
        "inclusion": "All 24 declared jobs, all attempts, all seeds, all failed or rejected outcomes. No posterior-based selection or exclusion.",
        "exclusion": "Engineering pilots and historical campaigns are not new final replicates. No other exclusions.",
        "failure_policy": "Zero automatic retries. Technical failure remains technical; completed numerical/scientific rejection remains rejected. Missing metrics are unavailable, never zero or measured noncoverage.",
        "primary_metrics": ["t0 chain means relative to physical period without wrapping", "max R-hat", "minimum ESS bulk/tail", "divergences", "minimum BFMI", "sampler pass count", "wall_seconds", "paired parameter center/SD/ETI94-width shifts"],
        "secondary_metrics": ["PPC point coverage", "temporal residual screen", "physical scale checks", "fixed-truth bias and ETI50/80/94 coverage (descriptive, n=3)", "historical external posterior distribution distances"],
        "primary_parameters": ["r", "depth", "b", "a", "t0", "full_duration", "extra_sigma"],
        "alias_review_rule": "Flag abs(unwrapped chain mean t0)>period/2 for mechanism review only; this is not a replacement gate, no draw is wrapped/removed, and false positives are possible for unusual ephemeris geometry.",
        "statistical_interpretation": "Paired descriptive numerical robustness, not a powered rate-comparison test. At n=3 rate precision is poor; report every pair and missing pair. ETI is not HDI, fixed-truth coverage is not SBC, and r/depth=r^2 are not independent confirmations.",
        "hypothesis_rejection_conditions": ["standardization does not improve or worsens numerical diagnostics in tested controls", "alias trapping persists under standardized coordinates", "higher accuracy retains divergent/nonconverged ablation baselines", "validly matched sampler-passing local fits materially disagree with the external posterior"],
        "forbidden_changes": ["no chain removal", "no modulo t0 wrapping", "no prior narrowing", "no truth initialization", "no threshold weakening", "no seed/target substitution"],
        "invalidation_conditions": ["truth enters inference", "input or frozen config identity changes", "unrecorded source changes", "historical result overwrite", "missing attempts hidden"],
        "outputs": ["config/protocol/seed ledger", "all registered attempt configs, truth (synthetic only), traces including warmup, diagnostics, PPC and completion checksums", "numeric job table", "paired effect table", "family figures", "all-attempt inventory", "hash-bound campaign summary"],
        "claim_limit": CLAIM_LIMIT, "amendments": [],
        "execution_note": "Prepared but not automatically launched by the agent. Commit tested sources and freeze/commit ledger before user-authorized execution. Soft budget pauses between jobs; extending the operational budget does not change scientific configuration.",
    }
    p2 = {**copy.deepcopy(common), "experiment_id": "PUB-02", "total_declared_final_attempts": 12,
          "question": "Does an equivalent standardized t0 coordinate reduce alias initialization/trapping without changing physical posterior targets?",
          "hypothesis": "z~Normal(0,1), t0=.025*z preserves the physical prior while default coordinate-space jitter starts nearer its physical scale; benefit is empirical, not guaranteed.",
          "scenarios": [copy.deepcopy(s) for s in originals["PUB-02"]["scenarios"] if s["scenario_id"] in {"deep_short", "intermediate_long"}],
          "inference": copy.deepcopy(originals["PUB-02"]["inference"]),
          "inference_assumptions": copy.deepcopy(originals["PUB-02"]["inference_assumptions"]),
          "variants": ["direct", "standardized"]}
    p2["inference"]["sampling"]["save_warmup"] = True
    p2["inference_assumptions"]["model_version"] = copy.deepcopy(common["model_versions"])
    p4 = {**copy.deepcopy(common), "experiment_id": "PUB-04", "total_declared_final_attempts": 9,
          "question": "Does increased numerical accuracy resolve baseline divergence, and is the exposure effect interpretable when both high-accuracy fits pass?",
          "hypothesis": "2000 tune/2000 draws at target_accept .99 may improve numerical geometry; it is not allowed to erase original divergent baselines or rescue PPC by threshold changes.",
          "truth": copy.deepcopy(originals["PUB-04"]["truth"]),
          "design": copy.deepcopy(next(p["design"] for p in originals["PUB-04"]["paired_designs"] if p["pair_id"] == "long_segment_offsets")),
          "normalization": copy.deepcopy(originals["PUB-04"]["normalization"]),
          "inference": copy.deepcopy(originals["PUB-04"]["inference"]),
          "variants": ["baseline_standardized", "baseline_high_accuracy", "exposure_off_high_accuracy"],
          "contrasts": {"baseline_high_accuracy": "baseline_standardized", "exposure_off_high_accuracy": "baseline_high_accuracy"}}
    p4["inference"].update(transit_center_parameterization="standardized")
    p4["inference"]["model_family"] = "M5-publication-v2-standardized-t0"
    p4["inference"]["sampling"]["save_warmup"] = True
    p3 = {**copy.deepcopy(common), "experiment_id": "PUB-03", "total_declared_final_attempts": 3,
          "question": "Are three prospectively seeded standardized local chains numerically stable on the unchanged matched benchmark input?",
          "hypothesis": "Equivalent scaled t0 coordinates may avoid the historical local orbital alias. Even numerical recovery would not cure observed temporal predictive inadequacy.",
          "dataset": copy.deepcopy(originals["PUB-03"]["dataset"]),
          "inference": copy.deepcopy(originals["PUB-03"]["inference"]),
          "comparison_contract": copy.deepcopy(originals["PUB-03"]["comparison_contract"]),
          "primary_benchmark": originals["PUB-03"]["primary_benchmark"],
          "independence_limit": "One unchanged observational dataset, three local MC streams, one REUSED historical external posterior. Not three independent external replicates; not external validation of scientific_003, whose radius prior differs.",
          "external_reference": {"attempt_dir": EXTERNAL_ATTEMPT, "completion_manifest_sha256": sha256_file(root / EXTERNAL_ATTEMPT / "completion_manifest.json"), "new_external_inference": False},
          "equivalence_evidence_required": "tests/test_t0_parameterization.py verifies transformed log density including Jacobian, physical likelihood and gradients before any final run."}
    p3["inference"].update(transit_center_parameterization="standardized")
    p3["inference"]["sampling"]["save_warmup"] = True
    config = {
        "campaign_id": campaign_id, "mode": "final", "study_kind": STUDY_KIND,
        "description": "Optional bounded numerical follow-up; never reruns/replaces 517 historical jobs. Prepared, not agent-launched.",
        "protocols": protocol_paths, "technical_retries": 0,
        "resources": {"max_workers": 1, "cores_per_run": 2, "max_campaign_hours": 20, "stop_margin_minutes": 5, "memory_limit_gb": None, "max_runtime_hours": None},
        "runtime": {"scientific_python": "/home/leonardo_barca/mc3/bin/python3.14", "wsl_distribution": "Ubuntu-24.04"},
        "numerical_study": {"replicates_per_design": 3, "high_accuracy_sampling": {"draws": 2000, "tune": 2000, "target_accept": .99}},
        "budget_evidence": budget,
    }
    for family, payload in (("PUB-02", p2), ("PUB-03", p3), ("PUB-04", p4)):
        _write_new(root / protocol_paths[family], payload)
    _write_new(config_path, config)
    return config_path


def add_numerical_jobs(config: dict, protocols: dict, add, errors: list[str]) -> None:
    """Expand into the engine's existing immutable job/seed/path contract."""
    count = config["numerical_study"]["replicates_per_design"]
    if type(count) is not int or count < 1:
        raise ValueError("Numerical replicate count must be a positive integer")
    for family in ("PUB-02", "PUB-03", "PUB-04"):
        if family not in protocols:
            errors.append(f"Missing required numerical protocol: {family}")
            continue
        protocol = protocols[family]["payload"]
        if protocol["replicates"] != count:
            errors.append(f"{family} replicate count differs from frozen numerical protocol")
        path = protocols[family]["path"]
        costs = config["budget_evidence"]["groups"]
        if family == "PUB-02":
            for scenario in protocol["scenarios"]:
                pair = f"t0_{scenario['scenario_id']}"
                for variant in protocol["variants"]:
                    inference = copy.deepcopy(protocol["inference"])
                    inference["transit_center_parameterization"] = variant
                    for index in range(count):
                        add(family, f"{pair}__{variant}", index,
                            {"scenario": scenario, "inference": inference, "protocol": path,
                             "pair_id": pair, "variant_id": variant, "reference_variant": "direct"},
                            kind="synthetic", generation_group=pair,
                            estimate=costs[scenario["scenario_id"]]["resource_adjusted_median_seconds"])
        elif family == "PUB-03":
            for index in range(count):
                add(family, "kepler_10_b_standardized", index, {"protocol": path}, kind="benchmark_local",
                    estimate=costs["kepler_10_b_local"]["resource_adjusted_median_seconds"])
        else:
            pair = "long_segment_offsets_numerical"
            for variant in protocol["variants"]:
                inference = copy.deepcopy(protocol["inference"])
                high = variant.endswith("high_accuracy")
                if high:
                    inference["sampling"].update(config["numerical_study"]["high_accuracy_sampling"])
                for index in range(count):
                    add(family, f"{pair}__{variant}", index,
                        {"scenario": {"truth": protocol["truth"], "design": protocol["design"]},
                         "inference": inference, "protocol": path, "pair_id": pair, "variant_id": variant,
                         "reference_variant": protocol["contrasts"].get(variant, variant),
                         "intervention": "exposure_off" if variant.startswith("exposure_off") else "baseline"},
                        kind="ablation", generation_group=pair,
                        estimate=costs["long_segment_offsets__baseline"]["resource_adjusted_median_seconds"] * (4 if high else 1))


def paired_numeric_metrics(rows: list[dict]) -> list[dict]:
    """Retain missing/rejected pairs and separate numeric from sampler support."""
    effects = []
    indexed = {(row["payload"].get("pair_id"), row["replicate_id"], row["payload"].get("variant_id")): row for row in rows}
    for row in rows:
        variant, reference = row["payload"].get("variant_id"), row["payload"].get("reference_variant")
        if not reference or variant == reference:
            continue
        baseline = indexed.get((row["payload"]["pair_id"], row["replicate_id"], reference))
        for parameter in ("r", "depth", "b", "a", "t0", "full_duration", "extra_sigma"):
            left = ((baseline or {}).get("result") or {}).get("parameters", {}).get(parameter)
            right = (row.get("result") or {}).get("parameters", {}).get(parameter)
            record = {"pair_id": row["payload"]["pair_id"], "replicate_id": row["replicate_id"], "variant": variant,
                      "reference_variant": reference, "parameter": parameter, "both_numeric": bool(left and right),
                      "both_sampler_pass": bool(baseline and all(
                          r.get("gate_assessment", {}).get("components", {}).get("sampler", {}).get("current_status") == "passed"
                          if r.get("gate_assessment") else (r.get("result") or {}).get("gates", {}).get("sampler") is True
                          for r in (baseline, row))),
                      "same_input": None, "mean_shift": None, "shift_over_reference_sd": None, "eti94_width_ratio": None}
            if left and right:
                first, second = baseline["result"], row["result"]
                record["same_input"] = first.get("input_sha256") == second.get("input_sha256") and bool(first.get("input_sha256"))
                if not record["same_input"]:
                    raise ValueError("Paired numerical comparison has mismatched physical inputs")
                width = left["intervals"]["0.94"][1] - left["intervals"]["0.94"][0]
                record.update(mean_shift=right["mean"] - left["mean"],
                              shift_over_reference_sd=(right["mean"]-left["mean"])/left["sd"] if left["sd"] > 0 else None,
                              eti94_width_ratio=(right["intervals"]["0.94"][1]-right["intervals"]["0.94"][0])/width if width > 0 else None)
            effects.append(record)
    return effects


def numerical_family_report(root: Path, rows: list[dict], output: Path, protocol: dict) -> tuple[dict, list[Path], dict]:
    """Use audited engine records; historical external reuse is explicit and bound."""
    from publication.campaign_reporting import _table, _write, benchmark_report, calibration_report

    family = protocol["experiment_id"]
    files, extra_sources = [], {}
    summary = {"declared_jobs": len(rows), "status_counts": dict(Counter(row["status"] for row in rows)),
               "claim_limit": CLAIM_LIMIT, "new_external_replicates": 0}
    if family in {"PUB-02", "PUB-04"}:
        summary["calibration"] = calibration_report(rows, output, mode="final")
        files.extend(output / name for name in ("calibration.json", "calibration.csv", "posterior_recovery.csv", "coverage.png", "bias.png", "bias_vs_snr.png", "width.png", "recovery.png", "gate_rates.png"))
        effects = paired_numeric_metrics(rows)
        _table(output / "numerical_paired_effects.csv", effects)
        summary["paired_effects"] = effects
        files.append(output / "numerical_paired_effects.csv")
    else:
        from publication.campaign import validate_completion

        reference = protocol["external_reference"]
        directory = root / reference["attempt_dir"]
        completion = validate_completion(directory, expected_manifest_sha256=reference["completion_manifest_sha256"])
        external = {"payload": {"kind": "benchmark_external"}, "result": _read(directory / "result.json"),
                    "completion": completion, "authoritative_attempt_dir": reference["attempt_dir"],
                    "scientifically_interpretable": False}
        extra_sources[f"{reference['attempt_dir']}/completion_manifest.json"] = reference["completion_manifest_sha256"]
        extra_sources.update({f"{reference['attempt_dir']}/{path}": digest for path, digest in completion["artifacts"].items()})
        comparisons = []
        for row in rows:
            destination = output / row["replicate_id"]
            destination.mkdir(exist_ok=True)
            item = benchmark_report(root, [row, external], destination)
            item.update(local_job_id=row["job_id"], external_reference_reused=True, new_external_replicates=0,
                        claim_limit=CLAIM_LIMIT + " External temporal PPC rejection remains unchanged.")
            _write(destination / "benchmark.json", item)
            comparisons.append(item)
            files.extend(destination / name for name in ("benchmark.json", "posterior_comparison.csv", "predictive_comparison.csv", "posterior_comparison.png", "predictive_comparison.png"))
        summary["comparisons"] = comparisons
    metrics = []
    for row in rows:
        result = row.get("result") or {}
        diagnostic = result.get("diagnostics", {})
        metrics.append({"job_id": row["job_id"], "replicate_id": row["replicate_id"], "status": row["status"],
                        "historical_gate_status": result.get("gates", {}), "diagnostics": diagnostic,
                        "gate_assessment": row.get("gate_assessment"),
                        "worker_wall_seconds": (row.get("completion") or {}).get("wall_seconds"),
                        "numeric_available": bool(result.get("parameters")),
                        "interpretation": "Sampler-passing output still requires claim-specific predictive/physical evaluation."})
    summary["job_metrics"] = metrics
    _write(output / "numerical_study.json", summary)
    _table(output / "numerical_job_metrics.csv", metrics)
    files.extend([output / "numerical_study.json", output / "numerical_job_metrics.csv"])
    # Per-run chain locations expose periodic aliases without transforming draws.
    chain_records = []
    for row in rows:
        if (
            not (row.get("result") or {}).get("parameters")
            or not row.get("authoritative_attempt_dir")
            or "trace.nc" not in (row.get("completion") or {}).get("artifacts", {})
        ):
            continue
        import xarray as xr
        with xr.open_dataset(root / row["authoritative_attempt_dir"] / "trace.nc", group="posterior", engine="h5netcdf") as trace:
            period = float(protocol.get("inference", {}).get("period_days", 1.0))
            for chain, values in enumerate(trace["t0"].values):
                center = float(values.mean())
                chain_records.append({"job_id": row["job_id"], "chain": chain, "t0_mean_days": center,
                                      "period_days": period, "absolute_mean_over_period": abs(center)/period,
                                      "alias_review_flag": abs(center) > period/2,
                                      "sampler_pass": row["result"].get("gates", {}).get("sampler")})
    _table(output / "t0_chain_locations.csv", chain_records, ["job_id", "chain", "t0_mean_days", "period_days", "absolute_mean_over_period", "alias_review_flag", "sampler_pass"])
    files.append(output / "t0_chain_locations.csv")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    figure, axis = plt.subplots(figsize=(9, 4), constrained_layout=True)
    for index, row in enumerate(chain_records):
        if math.isfinite(row["t0_mean_days"]):
            axis.scatter(index, row["t0_mean_days"]/row["period_days"], color="#27724d" if row["sampler_pass"] else "#a94d42", s=15)
    axis.axhline(0, color="black", linewidth=.7)
    axis.set(xlabel="All declared available chain locations (unwrapped)", ylabel="Chain mean t0 / period",
             title="Numerical follow-up; empty means not yet available, not zero alias incidence")
    figure.savefig(output / "t0_chain_locations.png", dpi=150)
    plt.close(figure)
    files.append(output / "t0_chain_locations.png")
    return summary, files, extra_sources
