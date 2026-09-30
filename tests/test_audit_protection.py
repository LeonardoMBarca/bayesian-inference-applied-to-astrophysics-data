"""Historical-byte protection must reject changes, not rewrite expectations."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from publication.audit_protection import verify, verify_portable  # noqa: E402
from publication.evidence_archive import SCHEMA, digest_json  # noqa: E402


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

    def test_portable_mode_binds_external_without_claiming_zip_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            content = b"protected\r\n"
            (root / "tracked.bin").write_bytes(content)
            file_hash = hashlib.sha256(content).hexdigest()
            snapshot = {"files": [
                {"path": "tracked.bin", "sha256": file_hash, "size_bytes": len(content)},
                {"path": "external.bin", "sha256": file_hash, "size_bytes": len(content)},
            ]}
            payload = {"schema_version": SCHEMA, "files": [
                {"path": "external.bin", "sha256": file_hash,
                 "size_bytes": len(content), "storage": "local_external_bundle"}]}
            inventory = {**payload, "inventory_content_sha256": digest_json(payload)}
            result = verify_portable(root, snapshot, inventory, {"tracked.bin"})
            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["git_bytes_checked"], 1)
            self.assertEqual(result["external_inventory_bound"], 1)
            self.assertEqual(result["external_bundle_bytes_checked"], 0)
            (root / "tracked.bin").write_bytes(b"corrupted\r\n")
            self.assertEqual(verify_portable(root, snapshot, inventory, {"tracked.bin"})["status"], "failed")
            (root / "tracked.bin").write_bytes(content)
            (root / "external.bin").write_bytes(b"corrupted\r\n")
            self.assertEqual(verify_portable(root, snapshot, inventory, {"tracked.bin"})["errors"][0]["error"],
                             "external_bytes_changed")
            (root / "external.bin").unlink()
            inventory["files"][0]["sha256"] = "0" * 64
            self.assertEqual(verify_portable(root, snapshot, inventory, {"tracked.bin"})["errors"][0]["error"],
                             "inventory_identity_mismatch")
            inventory["inventory_content_sha256"] = digest_json(payload)
            self.assertEqual(verify_portable(root, snapshot, inventory, {"tracked.bin"})["errors"][0]["error"],
                             "external_inventory_mismatch")


if __name__ == "__main__":
    unittest.main()
