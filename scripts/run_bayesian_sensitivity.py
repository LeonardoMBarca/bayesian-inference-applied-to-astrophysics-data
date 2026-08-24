"""Run a justified M5 prior-sensitivity family with independent gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bayesian_modeling.physical_transit import run_m5  # noqa: E402
from bayesian_modeling.sensitivity import summarize_sensitivity  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="kepler_10_b")
    parser.add_argument("--run-prefix", default="sensitivity_001")
    parser.add_argument(
        "--profiles",
        nargs="+",
        choices=["catalog_tighter", "baseline", "weak"],
        default=["catalog_tighter", "baseline", "weak"],
    )
    parser.add_argument("--draws", type=int, default=800)
    parser.add_argument("--tune", type=int, default=800)
    parser.add_argument("--chains", type=int, default=4)
    parser.add_argument("--cores", type=int, default=4)
    parser.add_argument("--target-accept", type=float, default=0.95)
    args = parser.parse_args()

    results: list[dict[str, object]] = []
    for profile in args.profiles:
        run_id = f"{args.run_prefix}_{profile}"
        try:
            result = run_m5(
                target_slug=args.target,
                run_id=run_id,
                prior_profile_name=profile,
                sampling_overrides={
                    "draws": args.draws,
                    "tune": args.tune,
                    "chains": args.chains,
                    "cores": args.cores,
                    "target_accept": args.target_accept,
                },
            )
            results.append(
                {
                    "run_id": run_id,
                    "prior_profile": profile,
                    "status": "completed",
                    "interpretation_gate": result["interpretation_gate"],
                }
            )
        except Exception as exc:  # failure detail is persisted by run_m5
            results.append(
                {
                    "run_id": run_id,
                    "prior_profile": profile,
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "scientifically_interpretable": False,
                }
            )
    summary = {
        "experiment": "M5 prior sensitivity",
        "target": args.target,
        "profiles": results,
        "interpretation_rule": (
            "Compare posterior shifts only among runs whose sampler, PPC, and scientific "
            "gates all pass; a prior-dominated or non-converged run is a negative result, "
            "not evidence of robustness."
        ),
    }
    output = PROJECT_ROOT / "reports" / f"{args.run_prefix}_{args.target}_summary.json"
    output.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    if all(result.get("status") == "completed" for result in results):
        summary["posterior_sensitivity"] = summarize_sensitivity(
            project_root=PROJECT_ROOT,
            target_slug=args.target,
            experiment_id=args.run_prefix,
            run_by_profile={
                result["prior_profile"]: result["run_id"] for result in results
            },
        )
        output.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
