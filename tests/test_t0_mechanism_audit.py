"""Standalone diagnosis must reject historical tampering before model use."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from publication.t0_mechanism_audit import verify_historical_inputs  # noqa: E402


class MechanismAuditTests(unittest.TestCase):
    def test_compiling_does_not_precede_historical_identity_check(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hashes = {}
            for name in ("inference_config.json", "input.csv", "trace.nc", "result.json", "completion_manifest.json"):
                data = name.encode()
                (root / name).write_bytes(data)
                hashes[name] = hashlib.sha256(data).hexdigest()
            summary = {"source_checksums": hashes}
            self.assertEqual(verify_historical_inputs(root, root, summary), hashes)
            (root / "input.csv").write_bytes(b"other")
            with self.assertRaisesRegex(ValueError, "Historical input changed"):
                verify_historical_inputs(root, root, summary)


if __name__ == "__main__":
    unittest.main()
