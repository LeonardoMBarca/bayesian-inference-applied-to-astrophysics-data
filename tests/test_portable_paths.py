from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from portable_paths import repo_relative_posix  # noqa: E402


class PortablePathTests(unittest.TestCase):
    def test_manifests_use_posix_repo_relative_paths(self) -> None:
        artifact = PROJECT_ROOT / "data" / "gold" / "target" / "artifact.csv"
        rendered = repo_relative_posix(artifact, PROJECT_ROOT)
        self.assertEqual(rendered, "data/gold/target/artifact.csv")
        self.assertNotIn("\\", rendered)

    def test_path_outside_repository_fails_loudly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            external = Path(directory) / "outside.csv"
            with self.assertRaisesRegex(ValueError, "outside"):
                repo_relative_posix(external, PROJECT_ROOT)


if __name__ == "__main__":
    unittest.main()
