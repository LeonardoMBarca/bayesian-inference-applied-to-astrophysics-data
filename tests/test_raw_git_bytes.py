"""Actual Git transport regressions, not a mock of newline conversion."""

from __future__ import annotations

import csv
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from repository_tools.raw_byte_audit import (  # noqa: E402
    BYTE_POLICY,
    MANIFEST,
    audit,
    classify,
    git,
    identity,
    materialize_checkout,
    safe_path,
    write_report,
)


class RawGitByteTests(unittest.TestCase):
    def make_repository(self, root: Path, protected: bool) -> list[bytes]:
        root.mkdir()
        git(root, "init")
        git(root, "config", "user.name", "Byte integrity fixture")
        git(root, "config", "user.email", "fixture@example.invalid")
        git(root, "config", "core.autocrlf", "true")
        git(root, "config", "core.safecrlf", "false")
        (root / ".gitattributes").write_text(
            "*.md text eol=lf\n" + (BYTE_POLICY + "\n" if protected else ""), encoding="utf-8"
        )
        payloads = [b"raw metadata\r\nunchanged evidence\r\n", b"LF source\n", b"\xef\xbb\xbfBOM source\r\n"]
        manifest = root / MANIFEST
        manifest.parent.mkdir(parents=True)
        with manifest.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["local_path", "sha256", "file_size_bytes"])
            writer.writeheader()
            for index, data in enumerate(payloads):
                relative = f"data/raw/fixture/notes_{index}.md"
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                writer.writerow({"local_path": relative, "sha256": hashlib.sha256(data).hexdigest(),
                                 "file_size_bytes": len(data)})
        git(root, "add", ".")
        git(root, "commit", "-m", "Immutable input fixture")
        return payloads

    def test_old_policy_reproduces_transport_failure_and_new_policy_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for protected in (False, True):
                root = base / f"source_{protected}"
                self.make_repository(root, protected)
                checkouts = {}
                for setting in (False, True):
                    target = base / f"checkout_{protected}_{setting}"
                    materialize_checkout(root, target, "HEAD", setting)
                    checkouts[f"autocrlf_{setting}"] = target
                report = audit(root, checkouts=checkouts)
                self.assertEqual(report["passed"], protected)
                self.assertEqual(report["counts_by_surface"]["worktree"], {"exact": 3})
                if protected:
                    for counts in report["counts_by_surface"].values():
                        self.assertEqual(counts, {"exact": 3})
                else:
                    self.assertEqual(report["counts_by_surface"]["git_blob"]["LF_to_CRLF"], 2)

    def test_real_content_tampering_fails_despite_byte_policy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "source"
            self.make_repository(root, True)
            path = root / "data/raw/fixture/notes_0.md"
            path.write_bytes(path.read_bytes().replace(b"metadata", b"metadatz"))
            result = audit(root)
            self.assertFalse(result["passed"])
            self.assertEqual(result["counts_by_surface"]["worktree"]["content_or_other_unresolved"], 1)
            self.assertEqual(result["counts_by_surface"]["git_blob"], {"exact": 3})

    def test_expected_size_is_not_ignored_and_missing_and_bom_are_classified(self):
        expected = identity(b"abc\r\n")
        self.assertEqual(classify(b"abc\n", expected), "LF_to_CRLF")
        self.assertEqual(classify(None, expected), "missing")
        self.assertEqual(classify(b"\xef\xbb\xbfabc\r\n", expected), "remove_UTF8_BOM")
        expected["size_bytes"] += 1
        self.assertEqual(classify(b"abc\n", expected), "content_or_other_unresolved")

    def test_mixed_eol_requires_an_exact_verified_original(self):
        original = b"a\r\nb\nc\r\n"
        expected = identity(original)
        self.assertEqual(classify(b"a\nb\nc\n", expected, original), "mixed_line_endings_verified_original")
        self.assertEqual(classify(b"a\nb\nc\n", expected, b"tampered"), "content_or_other_unresolved")

    def test_manifest_mutation_is_not_accepted_as_repair(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "source"
            self.make_repository(root, True)
            manifest = root / MANIFEST
            manifest.write_text(manifest.read_text().replace("notes_0", "notes_9"))
            with self.assertRaisesRegex(ValueError, "manifest fields differ"):
                audit(root)

    def test_path_escape_and_report_overwrite_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in ("../secret", "data/raw/../secret", "C:/secret", "data/raw/a\nfile"):
                with self.assertRaises(ValueError):
                    safe_path(root, relative)
            output = root / "audit.json"
            write_report(output, {"passed": True})
            with self.assertRaises(FileExistsError):
                write_report(output, {"passed": False})

    def test_repository_byte_policy_is_final_precedence(self):
        rules = (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
        self.assertIn(BYTE_POLICY, rules)
        self.assertEqual(next(line for line in reversed(rules) if line and not line.startswith("#")), BYTE_POLICY)

    def test_long_raw_path_is_readable_not_reported_missing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            relative = "data/raw/" + "/".join(["a" * 90, "b" * 90, "c" * 70]) + "/source.fits"
            path = safe_path(root, relative)
            path.parent.mkdir(parents=True)
            path.write_bytes(b"immutable FITS fixture")
            try:
                self.assertGreater(len(str(path)), 260)
                self.assertTrue(safe_path(root, relative).is_file())
                self.assertEqual(safe_path(root, relative).read_bytes(), b"immutable FITS fixture")
            finally:
                # tempfile's cleanup uses unprefixed paths on some Windows
                # Python builds. Remove only the fixture's own long suffix.
                path.unlink()
                for parent in list(path.parents)[:3]:
                    parent.rmdir()


if __name__ == "__main__":
    unittest.main()
