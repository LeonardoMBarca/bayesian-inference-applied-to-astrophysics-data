"""Refresh the checksum-verified current-state RAW manifest from its event log."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from raw_ingestion.utils import RawDataManifest  # noqa: E402


def main() -> None:
    manifest = RawDataManifest(PROJECT_ROOT / "data" / "raw", PROJECT_ROOT)
    manifest.flush()
    print(manifest.current_state_csv_path)


if __name__ == "__main__":
    main()
