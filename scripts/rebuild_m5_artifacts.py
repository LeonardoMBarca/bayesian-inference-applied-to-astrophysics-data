"""Rebuild M5 tables/reports from an unchanged trace after schema-only fixes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bayesian_modeling.physical_transit import (  # noqa: E402
    rebuild_m5_artifacts_from_trace,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    result = rebuild_m5_artifacts_from_trace(
        target_slug=args.target,
        run_id=args.run_id,
        project_root=PROJECT_ROOT,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
