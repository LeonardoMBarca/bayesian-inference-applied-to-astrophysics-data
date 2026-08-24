"""Compatibility CLI that runs the shared M5 workflow for Kepler-10 b."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bayesian_modeling.physical_transit import main  # noqa: E402

if __name__ == "__main__":
    main(["--target", "kepler_10_b", *sys.argv[1:]])
