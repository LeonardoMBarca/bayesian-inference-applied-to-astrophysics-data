"""Inspect time-coordinate initialization; never re-fit historical results."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from publication.t0_mechanism_audit import main  # noqa: E402

if __name__ == "__main__":
    main()
