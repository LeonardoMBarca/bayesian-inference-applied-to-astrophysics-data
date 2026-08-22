"""Build SILVER ETD / VarAstro tables from RAW JSON and CSV files."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import silver_data_config as config  # noqa: E402
from silver_processing.pipeline import run_pipeline  # noqa: E402


def main() -> None:
    run_pipeline(config, steps=("raw_validation", "etd", "silver_validation"))


if __name__ == "__main__":
    main()
