"""Diagnose initializer scale and periodic likelihood without refitting evidence."""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
from pathlib import Path

import numpy as np
import pandas as pd


def verify_historical_inputs(root: Path, directory: Path, summary: dict) -> dict:
    """Check against independently sealed historical expectations before use."""
    sources = {}
    for name in ("inference_config.json", "input.csv", "trace.nc", "result.json", "completion_manifest.json"):
        path = directory / name
        relative = path.relative_to(root).as_posix()
        with path.open("rb") as handle:
            actual = hashlib.file_digest(handle, "sha256").hexdigest()
        if actual != summary["source_checksums"][relative]:
            raise ValueError(f"Historical input changed: {relative}")
        sources[relative] = actual
    return sources


def audit(root: Path) -> dict:
    import pymc as pm
    import pymc.initial_point as ip
    import xarray as xr

    from publication.campaign import validate_completion
    from publication.environment_guard import require_scientific_environment
    from publication.inference import make_model

    relative = "artifacts/publication_campaign/tcc_campaign_v1/runs/PUB-03/kepler_10_b_local/rep_0000/attempt_000"
    directory = root / relative
    summary_name = "reports/publication_campaign/tcc_campaign_v1/campaign_summary.json"
    summary = json.loads((root / summary_name).read_text())
    sources = verify_historical_inputs(root, directory, summary)
    sources[summary_name] = hashlib.sha256((root / summary_name).read_bytes()).hexdigest()
    validate_completion(directory, expected_manifest_sha256=sources[relative + "/completion_manifest.json"])
    environment = require_scientific_environment(root)
    config = json.loads((directory / "inference_config.json").read_text())
    frame = pd.read_csv(directory / "input.csv")
    model, specification = make_model(frame, config)
    logp = model.compile_logp()
    loglike = model.compile_logp(vars=model.observed_RVs, jacobian=False)
    point = model.initial_point()
    sigma, period = config["t0_prior_sigma_days"], config["period_days"]
    aliases = []
    for multiple in (-1, 0, 1):
        point["t0"] = np.asarray(multiple * period)
        aliases.append({"period_multiple": multiple, "t0_days": float(point["t0"]),
                        "joint_log_density_at_other_prior_support_points": float(logp(point)),
                        "likelihood_log_density": float(loglike(point)),
                        "t0_log_prior_relative_to_zero": -.5 * (multiple * period / sigma)**2,
                        "t0_log_prior_gradient_per_day": -multiple * period / sigma**2})
    init_points = {}
    for coordinates in ("direct", "standardized"):
        selected_model, _ = make_model(frame, {**config, "transit_center_parameterization": coordinates})
        fn = ip.make_initial_point_fn(model=selected_model, jitter_rvs=set(selected_model.free_RVs), return_transformed=True)
        # A deterministic diagnostic sample of the initializer, NOT a sample
        # from the posterior and not the unrecoverable historical initial state.
        values = []
        for seed in range(26093000, 26093100):
            start = fn(seed)
            values.append(float(start["t0"]) if coordinates == "direct" else sigma * float(start["t0_standardized"]))
        init_points[coordinates] = {"seeds": list(range(26093000, 26093100)),
                                   "initial_t0_days": values,
                                   "beyond_half_period": sum(abs(x) > period/2 for x in values)}
    with xr.open_dataset(directory / "trace.nc", group="posterior", engine="h5netcdf") as trace:
        centers = trace.t0.values.copy()
    import h5py
    with h5py.File(directory / "trace.nc", "r") as handle:
        groups = list(handle.keys())
    source_text = inspect.getsource(ip.make_initial_point_expression)
    generators = ("src/publication/t0_mechanism_audit.py", "scripts/audit_t0_initialization.py",
                  "src/publication/inference.py", "src/bayesian_modeling/physical_transit.py")
    generator_hashes = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in generators}
    return {"schema_version": "t0-initialization-mechanism-v3", "source_checksums": sources,
            "generator_source_checksums": generator_hashes, "scientific_environment": environment,
            "pymc_version": pm.__version__, "initializer_source_sha256": hashlib.sha256(source_text.encode()).hexdigest(),
            "initializer_source": source_text, "model": specification, "aliases": aliases,
            "initializer_draws": init_points, "historical_chain_means_days": centers.mean(axis=1).tolist(),
            "historical_trace_groups": groups, "historical_warmup_saved": "warmup_posterior" in groups,
            "conclusion": "Direct Normal t0 is untransformed: initializer jitter acts in days, not prior-SD units. Periodic likelihood admits adjacent-period aliases despite a very small prior density. This is an experimentally checked mechanism capable of seeding aliases, not reconstruction of missing historical warmup trajectories.",
            "non_claims": ["No historical chain discarded or wrapped", "No final success rate for standardized sampling established by this diagnostic", "Prior remains Normal(0,.025 days); no truth-informed initialization"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    report = audit(Path(__file__).resolve().parents[2])
    args.output.mkdir(parents=True)
    (args.output / "audit.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"output": str(args.output), "chain_means": report["historical_chain_means_days"],
                      "initializer_beyond_half_period": {k: v["beyond_half_period"] for k, v in report["initializer_draws"].items()}}))


if __name__ == "__main__":
    main()
