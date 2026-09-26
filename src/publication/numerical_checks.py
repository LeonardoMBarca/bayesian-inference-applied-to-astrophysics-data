"""Pre-final deterministic compiler checks; never posterior evidence."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from publication.inference import make_model


def compare_linkers(input_path: Path, config_path: Path, output: Path) -> dict:
    from pytensor.compile.mode import Mode

    frame = pd.read_csv(input_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    model, _ = make_model(frame, config)
    point = model.initial_point()
    result = {"purpose": "deterministic compiler equivalence and timing; no posterior inference", "linkers": {}}
    evaluations = {}
    for name, mode in [("auto", None), ("cvm", Mode(linker="cvm", optimizer="fast_run"))]:
        start = time.perf_counter()
        try:
            kwargs = {} if mode is None else {"mode": mode}
            logp = model.compile_logp(**kwargs)
            gradient = model.compile_dlogp(**kwargs)
            compile_seconds = time.perf_counter() - start
            value, derivative = float(logp(point)), np.asarray(gradient(point))
            start = time.perf_counter()
            for _ in range(100):
                logp(point)
                gradient(point)
            result["linkers"][name] = {"status": "evaluated", "compile_seconds": compile_seconds,
                                       "seconds_per_logp_gradient": (time.perf_counter() - start)/100,
                                       "logp": value, "gradient": derivative.tolist()}
            evaluations[name] = (value, derivative)
        except Exception as exc:
            result["linkers"][name] = {"status": "failed", "error": repr(exc)}
    if len(evaluations) == 2:
        left, right = evaluations["auto"], evaluations["cvm"]
        result["equivalent"] = bool(np.isclose(left[0], right[0], rtol=1e-10, atol=1e-8) and np.allclose(left[1], right[1], rtol=1e-10, atol=1e-8))
    else:
        result["equivalent"] = False
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("config", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(compare_linkers(args.input, args.config, args.output), indent=2))


if __name__ == "__main__":
    main()
