"""Deterministic checkpoint I/O regressions; no campaign jobs or MCMC."""

from __future__ import annotations

import errno
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from publication.campaign import _atomic_json  # noqa: E402


class FakeClock:
    def __init__(self) -> None:
        self.elapsed = 0.0
        self.delays: list[float] = []

    def monotonic(self) -> float:
        return self.elapsed

    def sleep(self, delay: float) -> None:
        self.delays.append(delay)
        self.elapsed += delay


class CampaignCheckpointIOTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.path = self.directory / "campaign_state.json"
        self.old = {"status": "RUNNING", "jobs": {"old": [1, 2, 3]}}
        self.new = {"status": "RUNNING", "jobs": {"new": list(range(2000))}, "unicode": "valida\u00e7\u00e3o"}
        self.old_bytes = (json.dumps(self.old, sort_keys=True) + "\n").encode()
        self.path.write_bytes(self.old_bytes)
        self.clock = FakeClock()
        self.replace = os.replace

    def check_old_intact(self) -> None:
        self.assertEqual(self.path.read_bytes(), self.old_bytes)
        self.assertEqual(json.loads(self.path.read_text()), self.old)

    def test_uncontended_write_is_fsynced_before_one_atomic_replace(self) -> None:
        events = []
        actual_fsync = os.fsync

        def fsync(descriptor: int) -> None:
            events.append("fsync")
            actual_fsync(descriptor)

        def replace(source: Path, destination: Path) -> None:
            self.assertEqual(events, ["fsync"])
            self.assertEqual(json.loads(Path(source).read_text(encoding="utf-8")), self.new)
            self.check_old_intact()
            events.append("replace")
            self.replace(source, destination)

        stderr = io.StringIO()
        with patch("publication.campaign.os.replace", side_effect=replace), patch("publication.campaign.os.fsync", side_effect=fsync), patch("publication.campaign.time.sleep") as sleep, redirect_stderr(stderr):
            _atomic_json(self.path, self.new)
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), self.new)
        self.assertEqual(events, ["fsync", "replace"])
        self.assertEqual(list(self.directory.glob("*.tmp")), [])
        self.assertEqual(stderr.getvalue(), "")
        sleep.assert_not_called()

    def test_each_transient_code_retries_same_complete_candidate_and_recovers(self) -> None:
        errors = [PermissionError(errno.EACCES, "reader holds destination"),
                  PermissionError(errno.EPERM, "operation temporarily denied"),
                  OSError(errno.EBUSY, "resource busy")]
        for code in (32, 33):
            error = OSError("Windows sharing violation")
            error.winerror = code
            errors.append(error)
        for error in errors:
            with self.subTest(errno=error.errno, winerror=getattr(error, "winerror", None)):
                self.path.write_bytes(self.old_bytes)
                clock, sources, candidates, reads = FakeClock(), [], [], []

                def replace(source: Path, destination: Path) -> None:
                    sources.append(Path(source))
                    candidate = Path(source).read_bytes()
                    candidates.append(candidate)
                    self.assertEqual(json.loads(candidate), self.new)
                    reads.append(json.loads(self.path.read_bytes()))
                    self.check_old_intact()
                    if len(sources) <= 3:
                        raise error
                    self.replace(source, destination)
                    reads.append(json.loads(self.path.read_bytes()))

                stderr = io.StringIO()
                with patch("publication.campaign.os.replace", side_effect=replace), patch("publication.campaign.time.monotonic", side_effect=clock.monotonic), patch("publication.campaign.time.sleep", side_effect=clock.sleep), redirect_stderr(stderr):
                    _atomic_json(self.path, self.new)
                self.assertEqual(len(sources), 4)
                self.assertEqual(len(set(sources)), 1)
                self.assertTrue(all(candidate == candidates[0] for candidate in candidates))
                self.assertEqual(clock.delays, [.025, .05, .1])
                self.assertEqual(reads, [self.old] * 4 + [self.new])
                self.assertEqual(stderr.getvalue().count("temporarily blocked"), 1)
                self.assertEqual(stderr.getvalue().count("recovered"), 1)
                self.assertEqual(json.loads(self.path.read_bytes()), self.new)
                self.assertFalse(sources[0].exists())

    def test_persistent_access_denial_exhausts_bounded_budget_and_preserves_old_json(self) -> None:
        candidate_paths, candidate_bytes = [], []
        error = PermissionError(errno.EACCES, "persistent sharing violation")

        def replace(source: Path, _destination: Path) -> None:
            self.check_old_intact()
            candidate_paths.append(Path(source))
            candidate_bytes.append(Path(source).read_bytes())
            self.assertEqual(json.loads(candidate_bytes[-1]), self.new)
            raise error

        stderr = io.StringIO()
        with patch("publication.campaign.os.replace", side_effect=replace), patch("publication.campaign.time.monotonic", side_effect=self.clock.monotonic), patch("publication.campaign.time.sleep", side_effect=self.clock.sleep), redirect_stderr(stderr):
            with self.assertRaises(PermissionError) as caught:
                _atomic_json(self.path, self.new)
        self.assertIs(caught.exception, error)
        self.assertAlmostEqual(self.clock.elapsed, 12.0)
        self.assertLessEqual(len(candidate_paths), 35)
        self.assertLessEqual(max(self.clock.delays), .5)
        self.assertEqual(len(set(candidate_paths)), 1)
        self.assertTrue(all(value == candidate_bytes[0] for value in candidate_bytes))
        self.check_old_intact()
        self.assertEqual(stderr.getvalue().count("temporarily blocked"), 1)
        self.assertEqual(stderr.getvalue().count("remains blocked"), 1)
        self.assertNotIn("recovered", stderr.getvalue())
        self.assertFalse(candidate_paths[0].exists())

    def test_nontransient_replace_errors_never_retry_or_touch_destination(self) -> None:
        for code in (errno.ENOSPC, errno.EIO, errno.ENOENT, errno.EINVAL):
            for windows_attribute in (None, 32) if code in {errno.ENOSPC, errno.EIO} else (None,):
                with self.subTest(errno=code, winerror=windows_attribute):
                    error = OSError(code, "nontransient I/O failure")
                    if windows_attribute is not None:
                        error.winerror = windows_attribute
                    stderr = io.StringIO()
                    with patch("publication.campaign.os.replace", side_effect=error) as replace, patch("publication.campaign.time.sleep") as sleep, redirect_stderr(stderr):
                        with self.assertRaises(OSError) as caught:
                            _atomic_json(self.path, self.new)
                    self.assertIs(caught.exception, error)
                    replace.assert_called_once()
                    sleep.assert_not_called()
                    self.check_old_intact()
                    self.assertEqual(stderr.getvalue(), "")

    def test_fsync_failure_never_attempts_replace(self) -> None:
        with patch("publication.campaign.os.fsync", side_effect=OSError(errno.EIO, "fsync failed")), patch("publication.campaign.os.replace") as replace, patch("publication.campaign.time.sleep") as sleep:
            with self.assertRaises(OSError):
                _atomic_json(self.path, self.new)
        replace.assert_not_called()
        sleep.assert_not_called()
        self.check_old_intact()

    def test_exclusive_existing_destination_remains_untouched(self) -> None:
        with patch("publication.campaign.os.replace") as replace, patch("publication.campaign.time.sleep") as sleep:
            with self.assertRaises(FileExistsError):
                _atomic_json(self.path, self.new, exclusive=True)
        replace.assert_not_called()
        sleep.assert_not_called()
        self.check_old_intact()

    def test_exclusive_retry_does_not_replace_newly_created_destination(self) -> None:
        self.path.unlink()
        error = PermissionError(errno.EACCES, "temporarily blocked")

        def sleep(delay: float) -> None:
            self.clock.sleep(delay)
            self.path.write_bytes(self.old_bytes)

        with patch("publication.campaign.os.replace", side_effect=error) as replace, patch("publication.campaign.time.monotonic", side_effect=self.clock.monotonic), patch("publication.campaign.time.sleep", side_effect=sleep), redirect_stderr(io.StringIO()):
            with self.assertRaises(FileExistsError):
                _atomic_json(self.path, self.new, exclusive=True)
        replace.assert_called_once()
        self.check_old_intact()


if __name__ == "__main__":
    unittest.main()
