"""Historical-byte protection must reject changes, not rewrite expectations."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from publication.audit_protection import verify  # noqa: E402


class ProtectionTests(unittest.TestCase):
    def test_check_is_read_only_and_detects_same_size_content_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "historic.json"
            content = b'{"gate":true}\r\n'
            artifact.write_bytes(content)
            snapshot = {"files": [{"path": artifact.name, "size_bytes": len(content),
                                    "sha256": hashlib.sha256(content).hexdigest()}]}
            original = json.dumps(snapshot, sort_keys=True)
            self.assertEqual(verify(root, snapshot)["status"], "passed")
            self.assertEqual(artifact.read_bytes(), content)
            artifact.write_bytes(content.replace(b"true", b"null"))
            self.assertEqual(verify(root, snapshot)["errors"][0]["error"], "bytes_changed")
            self.assertEqual(json.dumps(snapshot, sort_keys=True), original)
            artifact.unlink()
            self.assertEqual(verify(root, snapshot)["errors"][0]["error"], "missing_or_symlink")

    def test_manifest_paths_cannot_escape_or_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in ("../outside", "/outside", "C:/outside", "a/../b", "a\\b", "a//b"):
                snapshot = {"files": [{"path": name, "size_bytes": 0, "sha256": "0" * 64}]}
                self.assertEqual(verify(Path(directory), snapshot)["errors"][0]["error"], "unsafe_path")


if __name__ == "__main__":
    unittest.main()
