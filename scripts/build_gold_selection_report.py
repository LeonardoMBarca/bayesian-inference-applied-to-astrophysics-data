"""Build only the GOLD candidate selection scorecard and report."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import gold_data_config as config  # noqa: E402
from gold_processing.pipeline import run_pipeline  # noqa: E402


def main() -> None:
    run_pipeline(config, steps=("selection",))


if __name__ == "__main__":
    main()
