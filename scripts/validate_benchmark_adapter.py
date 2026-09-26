"""Generate M5 numerical fixtures OR check them in the isolated juliet environment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--generate-fixture", type=Path)
    mode.add_argument("--validate-fixture", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.generate_fixture:
        import numpy as np

        from publication.simulation import TransitTruth, physical_flux

        cases = []
        for name, r, b, a, period, exposure in (
            ("deep_long", .1, .2, 8., 2., 1800.),
            ("shallow_short", .0125, .7, 3.5, .84, 60.),
            ("grazing_long", .1, .98, 10., 2., 1800.),
        ):
            parameters = {"r": r, "b": b, "a": a, "t0": .002, "q1": .25, "q2": .3, "baseline": 1.0003}
            truth = TransitTruth(**parameters, period_days=period)
            phases = np.linspace(-.11, .11, 61)
            flux = physical_flux(phases, exposure, truth, oversample=15)
            cases.append({"case_id": name, "parameters": parameters, "period_days": period,
                          "exposure_seconds": exposure, "phase_days": phases.tolist(),
                          "oversample": 15, "expected_flux": flux.tolist()})
        fixture = {"schema_version": "benchmark-forward-fixture-v1", "tolerance_fraction": 2e-8,
                   "evidence_class": "engineering_fixture_not_final_scientific_batch",
                   "generator": "exoplanet physical_flux with midpoint Riemann n=15",
                   "cases": cases}
        args.generate_fixture.parent.mkdir(parents=True, exist_ok=True)
        with args.generate_fixture.open("x", encoding="utf-8") as handle:
            json.dump(fixture, handle, indent=2, allow_nan=False)
        print(args.generate_fixture)
    else:
        from publication.benchmark import numeric_fixture_check

        if not args.output:
            parser.error("--output is required with --validate-fixture")
        result = numeric_fixture_check(args.validate_fixture)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, allow_nan=False)
        print(json.dumps(result, indent=2))
        if result["status"] != "passed":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
