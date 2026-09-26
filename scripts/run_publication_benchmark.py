"""Thin entry point for the isolated independent benchmark worker."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from publication.benchmark_runner import main  # noqa: E402

if __name__ == "__main__":
    main()
