"""Summarize three completed and independently gated M5 prior profiles."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bayesian_modeling.sensitivity import summarize_sensitivity  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="kepler_10_b")
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--catalog-tighter-run", required=True)
    parser.add_argument("--baseline-run", required=True)
    parser.add_argument("--weak-run", required=True)
    args = parser.parse_args()
    result = summarize_sensitivity(
        project_root=PROJECT_ROOT,
        target_slug=args.target,
        experiment_id=args.experiment_id,
        run_by_profile={
            "catalog_tighter": args.catalog_tighter_run,
            "baseline": args.baseline_run,
            "weak": args.weak_run,
        },
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
