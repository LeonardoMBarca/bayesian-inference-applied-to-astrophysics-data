"""Compatibility CLI for isolated Silver/Gold rebuild validation."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from repository_tools.clean_rebuild import *  # noqa: E402,F401,F403

if __name__ == "__main__":
    main()  # noqa: F405
