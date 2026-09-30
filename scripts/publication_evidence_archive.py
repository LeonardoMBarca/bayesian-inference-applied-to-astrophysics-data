"""Audit and restore checksummed evidence without running scientific inference."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from publication.evidence_archive import main  # noqa: E402

if __name__ == "__main__":
    main()
