"""Run the complete local SILVER data processing pipeline."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import silver_data_config as config  # noqa: E402
from silver_processing.pipeline import ALL_STEPS, run_pipeline  # noqa: E402


def main() -> None:
    run_pipeline(config, steps=ALL_STEPS)


if __name__ == "__main__":
    main()
