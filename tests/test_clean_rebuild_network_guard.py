"""Functional regression test for the clean-rebuild Python network guard."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.validate_clean_rebuild import verify_network_guard

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CleanRebuildNetworkGuardTests(unittest.TestCase):
    def test_standard_socket_apis_are_blocked_and_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "attempts.log"
            result = verify_network_guard(PROJECT_ROOT, log_path)

            self.assertTrue(result["verified"])
            self.assertEqual(
                result["blocked_apis"],
                [
                    "socket.socket.connect",
                    "socket.socket.connect_ex",
                    "socket.create_connection",
                    "socket.getaddrinfo",
                ],
            )
            self.assertEqual(
                log_path.read_text(encoding="utf-8").splitlines(),
                result["blocked_apis"],
            )


if __name__ == "__main__":
    unittest.main()
