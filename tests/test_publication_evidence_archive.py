"""Real filesystem/Git regressions for transitive scientific evidence storage."""

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from publication.evidence_archive import (
    EvidenceWalker,
    bundle_external,
    digest_json,
    rebind_existing_bundle,
    restore_bundle,
    safe_file,
    verify_inventory,
)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "original"
        self.root.mkdir()
        self.git("init")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "user.name", "Fixture")
        self.git("config", "core.autocrlf", "false")
        self.put("README.md", b"fixture\n")
        self.git("add", "README.md")
        self.git("commit", "-m", "fixture")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], stderr=subprocess.PIPE)

    def put(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, dict):
            content = json.dumps(content).encode()
        path.write_bytes(content)
        return hashlib.sha256(content).hexdigest()

    def fixture(self):
        raw = "data/raw/example.fits"
        raw_hash = self.put(raw, b"raw byte fixture\r\n")
        prep = "publication/observational/PUB-05/planet/run"
        gold_hash = self.put(prep + "/gold_lightcurve.csv", b"t,y\n0,1\n")
        silver_hash = self.put(prep + "/silver_lightcurve.csv", b"t,y\n0,100\n")
        manifest = {"schema_version": "publication-observational-v1", "output_directory": prep,
                    "artifacts": {"gold_lightcurve.csv": gold_hash, "silver_lightcurve.csv": silver_hash},
                    "source_artifacts": [{"path": raw, "sha256": raw_hash}]}
        manifest_hash = self.put(prep + "/preparation_manifest.json", manifest)
        report = "reports/fixture/artifact_manifest.json"
        self.put(report, {"schema_version": "publication-derived-v1", "artifacts": {},
                          "source_checksums": {prep + "/preparation_manifest.json": manifest_hash}})
        return report, prep, raw

    def test_transitive_preparation_reaches_unlisted_csv_and_raw(self):
        report, prep, raw = self.fixture()
        manifest = EvidenceWalker(self.root).build([report])
        paths = {row["path"] for row in manifest["files"]}
        self.assertIn(prep + "/gold_lightcurve.csv", paths)
        self.assertIn(prep + "/silver_lightcurve.csv", paths)
        self.assertIn(raw, paths)
        self.assertEqual(verify_inventory(self.root, manifest)["checked_files"], 5)

    def test_missing_and_modified_transitive_child_fail(self):
        report, prep, raw = self.fixture()
        (self.root / raw).unlink()
        with self.assertRaises(FileNotFoundError):
            EvidenceWalker(self.root).build([report])
        self.put(raw, b"raw byte fixture\r\n")
        self.put(prep + "/gold_lightcurve.csv", b"tampered")
        with self.assertRaisesRegex(ValueError, "Scientific artifact checksum mismatch"):
            EvidenceWalker(self.root).build([report])

    def test_conflicting_scientific_references_rejected(self):
        report, _, raw = self.fixture()
        walker = EvidenceWalker(self.root)
        walker.add(raw)
        with self.assertRaisesRegex(ValueError, "Conflicting evidence hashes"):
            walker.add(raw, "0" * 64)
        self.assertTrue(report)

    def test_no_arbitrary_json_path_scan(self):
        self.put("arbitrary.json", {"path": "missing.dat", "nested": {"source": "elsewhere"}})
        self.assertEqual(EvidenceWalker(self.root).build(["arbitrary.json"])["file_count"], 1)

    def test_real_pipeline_dependency_cycle_and_unknown_schema_rejected(self):
        first, second = "data/gold/a.csv", "data/gold/b.csv"
        first_hash, second_hash = self.put(first, b"a\n1\n"), self.put(second, b"b\n2\n")
        rows = [{"gold_file_path": first, "sha256": first_hash, "source_silver_path": second},
                {"gold_file_path": second, "sha256": second_hash, "source_silver_path": first}]
        self.put("data/gold/manifests/gold_data_manifest.json", json.dumps(rows).encode())
        with self.assertRaisesRegex(ValueError, "Cyclic"):
            EvidenceWalker(self.root).build([first])
        self.put("reports/artifact_manifest.json", {"schema_version": "future_unsupported_v999", "artifacts": {}, "source_checksums": {}})
        with self.assertRaisesRegex(ValueError, "Unsupported artifact manifest schema"):
            EvidenceWalker(self.root).build(["reports/artifact_manifest.json"])

    def test_baseline_historical_environment_copies_are_transitive(self):
        reference = "publication/baseline/environment/environment.yml"
        sha = self.put(reference, b"name: original-environment\n")
        self.put("publication/baseline/manifest.json", {"schema_version": "publication-baseline-v1", "artifacts": [],
                 "environment_lock_artifacts": [{"path": reference, "sha256": sha}]})
        inventory = EvidenceWalker(self.root).build(["publication/baseline/manifest.json"])
        self.assertIn(reference, {row["path"] for row in inventory["files"]})
        self.put(reference, b"name: mutated-environment\n")
        with self.assertRaisesRegex(ValueError, "Scientific artifact checksum mismatch"):
            EvidenceWalker(self.root).build(["publication/baseline/manifest.json"])

    def test_paths_symlinks_and_cycles_rejected(self):
        for name in ("../outside", "/absolute", "C:/absolute", "a\\b", "a/../b", ".git/config", "a//b"):
            with self.assertRaises(ValueError):
                safe_file(self.root, name)
        report, _, raw = self.fixture()
        self.put("cycle.json", {"schema_version": "publication-observational-v1", "output_directory": "somewhere", "artifacts": {},
                                "source_artifacts": [{"path": "cycle.json", "sha256": "0" * 64}]})
        walker = EvidenceWalker(self.root)
        walker.active.add((raw, hashlib.sha256((self.root / raw).read_bytes()).hexdigest()))
        with self.assertRaisesRegex(ValueError, "Cyclic"):
            walker.add(raw)
        link = self.root / "link"
        # Windows can restrict symlink creation. Mock only the OS capability,
        # not the actual boundary assertion; Linux integration exercises real links.
        try:
            link.symlink_to(self.root / raw)
        except OSError:
            from unittest.mock import patch
            with patch.object(Path, "is_symlink", return_value=True), self.assertRaises(ValueError):
                safe_file(self.root, "link")
        else:
            with self.assertRaises(ValueError):
                safe_file(self.root, "link")
        self.assertTrue(report)

    def test_historical_source_requires_exact_git_blob_never_science(self):
        old_hash = self.put("src/example.py", b"old = True\n")
        self.git("add", "src/example.py")
        self.git("commit", "-m", "original source")
        self.put("src/example.py", b"new = True\n")
        walker = EvidenceWalker(self.root)
        walker.add("src/example.py", old_hash)
        row = next(iter(walker.rows.values()))
        self.assertEqual(row["resolution"], "historical_git_blob")
        self.assertTrue(row["historical_git"]["blob"])
        science_hash = self.put("input.csv", b"old")
        self.git("add", "input.csv")
        self.git("commit", "-m", "original data")
        self.put("input.csv", b"new")
        with self.assertRaisesRegex(ValueError, "Scientific artifact checksum mismatch"):
            EvidenceWalker(self.root).add("input.csv", science_hash)

    def test_real_clone_bundle_restore_idempotence_and_no_overwrite(self):
        report, _, raw = self.fixture()
        self.git("add", report, raw)
        self.git("commit", "-m", "tracked subset")
        inventory = EvidenceWalker(self.root).build([report])
        archive = Path(self.temporary.name) / "external.zip"
        bundle = bundle_external(self.root, inventory, archive)
        checkout = Path(self.temporary.name) / "checkout"
        subprocess.run(["git", "clone", "--no-hardlinks", str(self.root), str(checkout)], check=True, capture_output=True)
        with self.assertRaises(FileNotFoundError):
            verify_inventory(checkout, inventory)
        receipt = restore_bundle(checkout, inventory, archive, bundle)
        self.assertEqual(receipt["restored_files"], 3)
        self.assertEqual(restore_bundle(checkout, inventory, archive, bundle)["already_present_files"], 3)
        path = checkout / bundle["members"][0]["path"]
        path.write_bytes(b"unrelated user change")
        with self.assertRaisesRegex(ValueError, "Refuse to overwrite"):
            restore_bundle(checkout, inventory, archive, bundle)

    def test_bundle_and_inventory_tampering_fail(self):
        report, _, _ = self.fixture()
        inventory = EvidenceWalker(self.root).build([report])
        archive = Path(self.temporary.name) / "external.zip"
        bundle = bundle_external(self.root, inventory, archive)
        with archive.open("ab") as stream:
            stream.write(b"tampered")
        with self.assertRaisesRegex(ValueError, "bundle identity"):
            restore_bundle(self.root, inventory, archive, bundle)
        inventory["files"][0]["size_bytes"] += 1
        with self.assertRaisesRegex(ValueError, "Inventory identity"):
            verify_inventory(self.root, inventory)

    def test_existing_zip_can_bind_revised_git_only_dependencies(self):
        report, _, _ = self.fixture()
        first = EvidenceWalker(self.root).build([report])
        archive = Path(self.temporary.name) / "external.zip"
        old_manifest = bundle_external(self.root, first, archive)
        extra = "environment.yml"
        self.put(extra, b"name: scientific\n")
        self.git("add", extra)
        self.git("commit", "-m", "environment source")
        revised = EvidenceWalker(self.root).build([report, extra])
        new_manifest = rebind_existing_bundle(revised, archive)
        self.assertEqual(old_manifest["bundle_sha256"], new_manifest["bundle_sha256"])
        self.assertNotEqual(old_manifest["inventory_content_sha256"], new_manifest["inventory_content_sha256"])
        self.assertEqual(old_manifest["members"], new_manifest["members"])
        self.assertTrue(new_manifest["rebound_existing_zip_after_full_member_verification"])
        with self.assertRaisesRegex(ValueError, "Inventory identity"):
            rebind_existing_bundle({**revised, "inventory_content_sha256": "0" * 64}, archive)

    def test_denominator_is_not_claimed_by_availability(self):
        report, _, _ = self.fixture()
        inventory = EvidenceWalker(self.root).build([report])
        self.assertFalse(inventory["release_approved"])
        self.assertIsNone(inventory["public_archive"])
        inventory.pop("inventory_content_sha256")
        self.assertEqual(len(digest_json(inventory)), 64)

    def test_long_windows_paths_are_not_misclassified_missing(self):
        relative = "/".join(["data", "raw", *(["long_component_0123456789"] * 11), "source.fits"])
        path = safe_file(self.root, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"long-path raw bytes")
        def cleanup_long_fixture():
            path.unlink(missing_ok=True)
            directory = path.parent
            # Only these twelve just-created, empty fixture directories.
            for _ in range(12):
                directory.rmdir()
                directory = directory.parent
        self.addCleanup(cleanup_long_fixture)
        inventory = EvidenceWalker(self.root).build([relative])
        self.assertEqual(inventory["file_count"], 1)
        self.assertEqual(verify_inventory(self.root, inventory)["checked_bytes"], 19)


if __name__ == "__main__":
    unittest.main()
