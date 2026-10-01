"""Audit and restore checksummed evidence without running scientific inference."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from publication.evidence_archive import main  # noqa: E402

if __name__ == "__main__":
    # Extended Windows paths must be absolute. Normalize only CLI filesystem
    # arguments; logical member/reference paths remain repository-relative.
    for flag in ("--root", "--inventory", "--bundle", "--bundle-manifest", "--receipt"):
        if flag in sys.argv:
            index = sys.argv.index(flag) + 1
            if index < len(sys.argv) and not sys.argv[index].startswith("--"):
                sys.argv[index] = str(Path(sys.argv[index]).resolve())
    main()
