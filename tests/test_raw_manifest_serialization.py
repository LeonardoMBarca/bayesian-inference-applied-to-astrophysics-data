"""Regression tests for portable RAW manifest serialization."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from raw_ingestion.utils import csv_bytes  # noqa: E402


class RawManifestSerializationTests(unittest.TestCase):
    def test_csv_bytes_uses_repository_portable_lf_endings(self) -> None:
        serialized = csv_bytes([{"path": "data/raw/example.fits", "status": "ok"}])

        self.assertNotIn(b"\r\n", serialized)
        self.assertEqual(serialized.count(b"\n"), 2)


if __name__ == "__main__":
    unittest.main()
