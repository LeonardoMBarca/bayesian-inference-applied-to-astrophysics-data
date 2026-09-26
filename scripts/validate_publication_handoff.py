"""Thin CLI for persisted runner handoff validation, never final science."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from publication.handoff_validation import main  # noqa: E402

if __name__ == "__main__":
    main()
