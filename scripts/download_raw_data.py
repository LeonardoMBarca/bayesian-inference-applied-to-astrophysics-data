#!/usr/bin/env python3
"""Run all RAW astronomical data collectors."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import raw_data_config as config
from raw_ingestion.pipeline import run_pipeline


if __name__ == "__main__":
    raise SystemExit(run_pipeline(config, ("nasa", "mast", "exomast", "etd")))

