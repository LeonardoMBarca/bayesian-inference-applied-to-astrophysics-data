"""Compare model runs only after verifying statistical comparability."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from bayesian_modeling.comparison import compare_runs  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_configs", nargs="+", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "reports" / "model_comparison",
    )
    args = parser.parse_args()
    payload = compare_runs(
        project_root=PROJECT_ROOT,
        config_paths=[path.resolve() for path in args.model_configs],
        output_dir=args.output_dir.resolve(),
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
