"""Create or verify the versioned external-audit TCC evidence synthesis."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from publication.synthesis_v2 import main  # noqa: E402

if __name__ == "__main__":
    main()
