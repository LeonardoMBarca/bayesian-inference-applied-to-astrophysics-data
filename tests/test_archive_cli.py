from __future__ import annotations

import runpy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class ArchiveCLITests(unittest.TestCase):
    def launch(self, args):
        with patch("sys.argv", ["publication_evidence_archive.py", *args]), patch("publication.evidence_archive.main") as main:
            runpy.run_path(str(ROOT / "scripts/publication_evidence_archive.py"), run_name="__main__")
            main.assert_called_once()
            return list(sys.argv)

    def test_relative_filesystem_paths_become_absolute_before_windows_prefix(self):
        args = self.launch(["restore", "--root", ".", "--inventory", "publication/inventory.json",
                            "--bundle", "../evidence/evidence.zip", "--bundle-manifest", "publication/bundle.json",
                            "--receipt", "publication/receipt.json"])
        for flag in ("--root", "--inventory", "--bundle", "--bundle-manifest", "--receipt"):
            value = args[args.index(flag) + 1]
            self.assertTrue(Path(value).is_absolute())
            self.assertNotIn("..", Path(value).parts)

    def test_logical_roots_and_commit_are_not_normalized(self):
        args = self.launch(["inventory", "--inventory", "inventory.json", "--roots", "reports/artifact_manifest.json",
                            "--snapshot-commit", "HEAD"])
        self.assertEqual(args[args.index("--roots") + 1], "reports/artifact_manifest.json")
        self.assertEqual(args[-1], "HEAD")

    def test_missing_value_is_left_for_argparse_not_made_into_a_path(self):
        args = self.launch(["bundle", "--bundle", "--receipt"])
        self.assertEqual(args[-2:], ["--bundle", "--receipt"])


if __name__ == "__main__":
    unittest.main()
