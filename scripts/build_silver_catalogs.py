"""Build SILVER catalog tables from RAW NASA and Exo.MAST files."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from silver_processing import config  # noqa: E402
from silver_processing.pipeline import run_pipeline  # noqa: E402


def main() -> None:
    run_pipeline(
        config,
        steps=("raw_validation", "catalogs", "silver_validation"),
    )


if __name__ == "__main__":
    main()
