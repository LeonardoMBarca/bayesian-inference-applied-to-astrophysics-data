"""Thin executable for one reserved publication campaign attempt."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from publication.campaign_worker import main  # noqa: E402

if __name__ == "__main__":
    main()
