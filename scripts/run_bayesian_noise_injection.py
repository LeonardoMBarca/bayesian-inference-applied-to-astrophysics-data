"""Generate an explicit, run-isolated noise-injection dataset and metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bayesian_modeling.noise_experiments import (  # noqa: E402
    NoiseInjectionConfig,
    inject_noise,
)
from project_config import get_target  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="kepler_10_b")
    parser.add_argument(
        "--kind",
        choices=["white_gaussian", "deterministic_sinusoid", "correlated_ar1"],
        required=True,
    )
    parser.add_argument("--amplitude", type=float, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ar1-rho", type=float, default=0.8)
    parser.add_argument("--sinusoid-period-days", type=float, default=0.1)
    parser.add_argument("--experiment-id", required=True)
    args = parser.parse_args()

    target = get_target(args.target)
    source = PROJECT_ROOT / target.source_gold_path
    frame = pd.read_csv(source, low_memory=False)
    config = NoiseInjectionConfig(
        kind=args.kind,
        amplitude_fraction=args.amplitude,
        seed=args.seed,
        ar1_rho=args.ar1_rho,
        sinusoid_period_days=args.sinusoid_period_days,
    )
    injected, metrics = inject_noise(frame, config)
    output_dir = (
        PROJECT_ROOT
        / "data"
        / "experiments"
        / "noise_injection"
        / target.planet_slug
        / args.experiment_id
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    injected.to_csv(output_dir / "injected_lightcurve.csv", index=False)
    payload = {
        "experiment_id": args.experiment_id,
        "target": target.metadata(),
        "source_gold_path": target.source_gold_path.as_posix(),
        "source_dataset_id": str(frame["dataset_id"].iloc[0]),
        "injection": metrics,
        "output_path": (
            output_dir / "injected_lightcurve.csv"
        ).relative_to(PROJECT_ROOT).as_posix(),
    }
    (output_dir / "experiment_config.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
