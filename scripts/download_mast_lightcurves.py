#!/usr/bin/env python3
"""Run the MAST/Lightkurve collector and Exo.MAST metadata collector."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from raw_ingestion import config  # noqa: E402 -- project path is initialized above
from raw_ingestion.pipeline import run_pipeline  # noqa: E402 -- project path is initialized above

if __name__ == "__main__":
    raise SystemExit(run_pipeline(config, ("mast", "exomast")))

