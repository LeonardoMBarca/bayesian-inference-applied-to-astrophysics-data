"""Compatibility CLI for the historical M1 baseline implementation."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bayesian_modeling.legacy.baseline import *  # noqa: E402,F401,F403

if __name__ == "__main__":
    main()  # noqa: F405
