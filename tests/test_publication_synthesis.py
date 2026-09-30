"""Fail-closed evidence synthesis, including rejected/missing final outcomes."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from publication.calibration import PARAMETERS, coverage_metrics  # noqa: E402
from publication.synthesis import (  # noqa: E402
    CAMPAIGNS,
    SCHEMA,
    coverage_error_lengths,
    figures,
    flatten_calibration,
    publish_rendered_bundle,
    recompute_calibration,
    render_manuscript,
    render_report,
    summarize_gates,
    validate_declared_summary,
    verify_bundle,
    verify_campaign_snapshot,
)


class PublicationSynthesisTests(unittest.TestCase):
    def rendering_fixture(self):
        scenarios = {}
        for index, scenario in enumerate(("shallow_short", "near_limit_long", "intermediate_long", "deep_short")):
            mean = 1. + index * .025
            parameter = {"truth": 1., "mean": mean, "sd": .05,
                         "intervals": {level: [mean - float(level) * .02, mean + float(level) * .02]
                                       for level in ("0.5", "0.8", "0.94")}}
            record = {"replicate_id": "fixture", "status": "completed",
                      "parameters": {name: copy.deepcopy(parameter) for name in PARAMETERS},
                      "gates": {"sampler": True, "ppc": True, "scientific": True}}
            scenarios[scenario] = coverage_metrics([record], ["fixture"])
        comparison = {"standardized_mean_difference": .1, "material_discrepancy_flag": False,
                      "intervals": {"0.94": {"overlap_jaccard": .9, "width_ratio_external_local": 1.1}}}
        return {"campaigns": {campaign: {"declared_jobs": 4, "total_attempts": 4,
                                         "status_counts": {"COMPLETED": 4}} for campaign in CAMPAIGNS},
                "calibration": {campaign: copy.deepcopy(scenarios) for campaign in reversed(CAMPAIGNS)},
                "total_jobs": 8, "total_attempts": 8,
                "benchmark": {"status": "fixture", "comparison": {"parameters": {
                    "r": copy.deepcopy(comparison), "a": copy.deepcopy(comparison)}}},
                "ablation": {"declared_jobs": 0, "sampler_pass_but_ppc_or_science_fail_count": 0},
                "targets": []}

    def test_report_is_invariant_to_json_key_order_and_retains_unknown_keys(self):
        payload = self.rendering_fixture()
        payload["campaigns"]["additional_campaign"] = copy.deepcopy(payload["campaigns"][CAMPAIGNS[0]])
        payload["calibration"][CAMPAIGNS[0]]["additional_scenario"] = copy.deepcopy(
            payload["calibration"][CAMPAIGNS[0]]["deep_short"])
        report = render_report(payload)
        self.assertEqual(report, render_report(json.loads(json.dumps(payload, sort_keys=True))))
        self.assertIn("| additional_campaign |", report)
        self.assertIn("| additional_scenario |", report)
        self.assertLess(report.index("### Coorte " + CAMPAIGNS[0]), report.index("### Coorte " + CAMPAIGNS[1]))
        self.assertLess(report.index("| shallow_short |"), report.index("| near_limit_long |"))

    def test_manuscript_is_invariant_to_json_key_order(self):
        payload = self.rendering_fixture()
        self.assertEqual(render_manuscript(payload), render_manuscript(json.loads(json.dumps(payload, sort_keys=True))))

    def test_figures_are_invariant_to_json_key_order(self):
        calibration = self.rendering_fixture()["calibration"]
        with tempfile.TemporaryDirectory() as temp:
            original, reordered = Path(temp) / "original", Path(temp) / "reordered"
            original.mkdir()
            reordered.mkdir()
            figures(original, calibration)
            figures(reordered, json.loads(json.dumps(calibration, sort_keys=True)))
            for name in ("coverage_all_parameters.png", "radius_bias_and_uncertainty.png"):
                with self.subTest(figure=name):
                    self.assertEqual((original / name).read_bytes(), (reordered / name).read_bytes())

    def test_rendered_bundle_publishes_manifest_last(self):
        import os
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as temp:
            rendered, destination = Path(temp) / "rendered", Path(temp) / "published"
            rendered.mkdir()
            destination.mkdir()
            (destination / "artifact_manifest.json").write_bytes(b"previous seal")
            # Create manifest first to exercise order independently of directory order.
            for name, value in (("artifact_manifest.json", b"new seal"), ("b.csv", b"second"), ("a.csv", b"first")):
                (rendered / name).write_bytes(value)
            replaced = []
            real_replace = os.replace

            def observe_replace(source, target):
                replaced.append(source.name)
                self.assertEqual((destination / "artifact_manifest.json").read_bytes(), b"previous seal")
                if source.name == "artifact_manifest.json":
                    self.assertEqual((destination / "a.csv").read_bytes(), b"first")
                    self.assertEqual((destination / "b.csv").read_bytes(), b"second")
                return real_replace(source, target)

            with patch("publication.synthesis.os.replace", side_effect=observe_replace):
                self.assertEqual(publish_rendered_bundle(rendered, destination), destination)
            self.assertEqual(replaced, ["a.csv", "b.csv", "artifact_manifest.json"])
            self.assertEqual((destination / "artifact_manifest.json").read_bytes(), b"new seal")
            self.assertFalse(rendered.exists())

    def test_interrupted_publication_preserves_previous_seal_and_unpublished_files(self):
        import hashlib
        import os
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as temp:
            rendered, destination = Path(temp) / "rendered", Path(temp) / "published"
            rendered.mkdir()
            destination.mkdir()
            old_manifest = json.dumps({"artifacts": {"a.csv": hashlib.sha256(b"old a").hexdigest()}}).encode()
            (destination / "artifact_manifest.json").write_bytes(old_manifest)
            for name in ("a.csv", "b.csv"):
                (destination / name).write_bytes(f"old {name[0]}".encode())
                (rendered / name).write_bytes(f"new {name[0]}".encode())
            (rendered / "artifact_manifest.json").write_bytes(b"new seal")
            real_replace = os.replace

            def interrupt_replace(source, target):
                if source.name == "b.csv":
                    raise PermissionError("simulated sharing violation")
                return real_replace(source, target)

            with patch("publication.synthesis.os.replace", side_effect=interrupt_replace):
                with self.assertRaisesRegex(PermissionError, "sharing violation"):
                    publish_rendered_bundle(rendered, destination)
            self.assertEqual((destination / "artifact_manifest.json").read_bytes(), old_manifest)
            self.assertEqual((destination / "a.csv").read_bytes(), b"new a")
            self.assertEqual((destination / "b.csv").read_bytes(), b"old b")
            self.assertEqual((rendered / "b.csv").read_bytes(), b"new b")
            self.assertEqual((rendered / "artifact_manifest.json").read_bytes(), b"new seal")
            # The stale seal cannot falsely attest a partially replaced bundle.
            self.assertNotEqual(hashlib.sha256((destination / "a.csv").read_bytes()).hexdigest(),
                                json.loads(old_manifest)["artifacts"]["a.csv"])

    def test_unsealed_render_is_rejected_before_destination_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            rendered, destination = Path(temp) / "rendered", Path(temp) / "published"
            rendered.mkdir()
            (rendered / "a.csv").write_bytes(b"partial rendering")
            with self.assertRaisesRegex(ValueError, "missing its artifact manifest"):
                publish_rendered_bundle(rendered, destination)
            self.assertFalse(destination.exists())
            self.assertEqual((rendered / "a.csv").read_bytes(), b"partial rendering")

    def test_zero_and_full_coverage_roundoff_plots_without_changing_intervals(self):
        from publication.calibration import wilson_interval

        bounds = [wilson_interval(0, 100), wilson_interval(100, 100)]
        preserved = copy.deepcopy(bounds)
        errors = coverage_error_lengths([0., 1.], bounds)
        self.assertTrue(all(value >= 0 for side in errors for value in side))
        self.assertEqual(bounds, preserved)
        self.assertEqual(errors[0][0], 0.)
        self.assertEqual(errors[1][1], 0.)
        with self.assertRaises(ValueError):
            coverage_error_lengths([.5], [[.6, .9]])

    def fixture(self):
        definition = {"job_id": "PUB-02__control__rep_0000", "experiment_id": "PUB-02",
                      "scenario_id": "control", "replicate_id": "rep_0000", "run_id": "fixture_run",
                      "seeds": {"generation": 14, "inference": 27}}
        job = {**definition, "output_dir": "artifacts/publication_campaign/fixture/runs/PUB-02/control/rep_0000",
               "status": "COMPLETED_REJECTED", "attempt_count": 2}
        attempts = [{"job_id": job["job_id"], "attempt_index": 0, "status": "CANCELLED"},
                    {"job_id": job["job_id"], "attempt_index": 1, "status": "COMPLETED_REJECTED"}]
        for index, attempt in enumerate(attempts):
            attempt.update(seeds=copy.deepcopy(job["seeds"]), authoritative=index == 1,
                           output_dir=job["output_dir"] + f"/attempt_{index:03d}")
        job["authoritative_attempt_dir"] = attempts[-1]["output_dir"]
        summary = {"jobs": [job], "attempts": attempts, "total_attempts": 2,
                   "mode": "final", "campaign_id": "fixture", "declared_jobs": 1,
                   "complete_declared_batch": True, "status_counts": {"COMPLETED_REJECTED": 1}}
        ledger = {"campaign_id": "fixture", "declared_jobs": [definition]}
        return summary, ledger

    def test_cancelled_attempt_is_retained_without_inflating_replication(self):
        summary, ledger = self.fixture()
        validate_declared_summary(summary, ledger)
        self.assertEqual(summary["declared_jobs"], 1)
        self.assertEqual(summary["total_attempts"], 2)

    def test_omitted_rejection_duplicate_or_status_relabeling_is_rejected(self):
        original, ledger = self.fixture()
        for mutation in ("omitted", "duplicated", "relabelled", "missing_attempt"):
            with self.subTest(mutation=mutation):
                summary = copy.deepcopy(original)
                if mutation == "omitted":
                    summary["jobs"] = []
                elif mutation == "duplicated":
                    summary["jobs"].append(summary["jobs"][0])
                elif mutation == "relabelled":
                    summary["jobs"][0]["status"] = "COMPLETED"
                else:
                    summary["attempts"].pop(0)
                with self.assertRaises(ValueError):
                    validate_declared_summary(summary, ledger)

    def test_changed_seed_pilot_and_partial_batch_cannot_be_promoted(self):
        original, ledger = self.fixture()
        for mutation in ("seed", "pilot", "partial", "path"):
            with self.subTest(mutation=mutation):
                summary = copy.deepcopy(original)
                if mutation == "seed":
                    summary["jobs"][0]["seeds"]["inference"] += 1
                elif mutation == "pilot":
                    summary["mode"] = "smoke"
                elif mutation == "path":
                    summary["jobs"][0]["output_dir"] = "artifacts/another_run"
                else:
                    summary["complete_declared_batch"] = False
                with self.assertRaises(ValueError):
                    validate_declared_summary(summary, ledger)

    def test_recompute_retains_rejected_numeric_posteriors_and_missing(self):
        jobs = [{"job_id": str(i), "experiment_id": "PUB-02", "scenario_id": "control",
                 "replicate_id": str(i)} for i in range(3)]
        p = {"mean": 2.0, "sd": .5, "intervals": {level: [1.0, 3.0] for level in ("0.5", "0.8", "0.94")}}
        results = {"0": {"status": "completed", "parameters": {"r": p},
                         "gates": {"sampler": True, "ppc": True, "scientific": True}},
                   "1": {"status": "rejected", "parameters": {"r": p},
                         "gates": {"sampler": False, "ppc": True, "scientific": False}}}
        truths = {"0": {"truth": {"r": 2.0}}, "1": {"truth": {"r": 4.0}}}
        records = [{**copy.deepcopy(results[str(i)]), "replicate_id": str(i)} for i in range(2)]
        for i in range(2):
            records[i]["parameters"]["r"]["truth"] = truths[str(i)]["truth"]["r"]
        records.append({"replicate_id": "2", "status": "failed", "gates": {}})
        stored = {"scenarios": {"control": coverage_metrics(records, ["0", "1", "2"])}}
        got = recompute_calibration(jobs, results, truths, stored)["control"]
        self.assertEqual(got["declared_count"], 3)
        self.assertEqual(got["parameters"]["r"]["bias"], -1.0)
        cov = got["parameters"]["r"]["coverage"]["0.94"]
        self.assertEqual(cov["empirical_coverage_numeric"], .5)
        self.assertEqual(cov["coverage_conditional_on_scientific_gate"], 1.)
        self.assertEqual(cov["operational_covered_and_passed_rate_all_declared"], 1 / 3)
        stored["scenarios"]["control"]["parameters"]["r"]["coverage"]["0.94"]["covered_count"] = 2
        with self.assertRaisesRegex(ValueError, "differs"):
            recompute_calibration(jobs, results, truths, stored)
        self.assertNotIn("truth", results["0"]["parameters"]["r"])

    def test_gate_counts_distinguish_unavailable_from_observed_failure(self):
        jobs = [{"job_id": str(i), "experiment_id": "PUB-04", "scenario_id": "control",
                 "status": "COMPLETED_REJECTED"} for i in range(2)]
        results = {"0": {"gates": {"provenance": False}},
                   "1": {"gates": {"provenance": True, "sampler": True, "ppc": False, "scientific": False}}}
        row = summarize_gates("fixture", jobs, results)[0]
        self.assertEqual(row["sampler_unavailable"], 1)
        self.assertEqual(row["sampler_rejected"], 0)
        self.assertEqual(row["sampler_pass_ppc_fail"], 1)

    def test_attempt_swap_seed_change_and_noncontiguous_history_fail(self):
        original, ledger = self.fixture()
        for mutation in ("swap", "seed", "index", "unknown", "authority"):
            with self.subTest(mutation=mutation):
                summary = copy.deepcopy(original)
                if mutation == "swap":
                    summary["jobs"][0]["authoritative_attempt_dir"] = summary["attempts"][0]["output_dir"]
                elif mutation == "seed":
                    summary["attempts"][0]["seeds"]["generation"] += 1
                elif mutation == "index":
                    summary["attempts"][0]["attempt_index"] = 2
                elif mutation == "unknown":
                    summary["attempts"][0]["job_id"] = "unknown"
                else:
                    summary["attempts"][0]["authoritative"] = True
                with self.assertRaises(ValueError):
                    validate_declared_summary(summary, ledger)

    def test_recursive_manifest_detects_stale_source_and_child_output(self):
        from publication.contracts import sha256_file

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = root / "reports"
            child = report / "PUB-02"
            child.mkdir(parents=True)
            source = root / "source.json"
            source.write_text('{"rejected": true}')
            figure = child / "figure.svg"
            figure.write_text("<svg/>")
            child_manifest = child / "artifact_manifest.json"
            child_manifest.write_text(json.dumps({"source_checksums": {"source.json": sha256_file(source)},
                                                 "artifacts": {"figure.svg": sha256_file(figure)}}))
            manifest = {"source_checksums": {"source.json": sha256_file(source)},
                        "artifacts": {"PUB-02/artifact_manifest.json": sha256_file(child_manifest)},
                        "child_manifests": ["PUB-02/artifact_manifest.json"]}
            (report / "artifact_manifest.json").write_text(json.dumps(manifest))
            verify_campaign_snapshot(root, report)
            figure.write_text("<svg>tampered</svg>")
            with self.assertRaisesRegex(ValueError, "Stale"):
                verify_campaign_snapshot(root, report)
            figure.write_text("<svg/>")
            source.write_text('{"rejected": false}')
            with self.assertRaisesRegex(ValueError, "Stale"):
                verify_campaign_snapshot(root, report)

    def test_recursive_manifest_rejects_unbound_child_and_path_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = root / "reports"
            report.mkdir()
            manifest = {"source_checksums": {}, "artifacts": {}, "child_manifests": ["child.json"]}
            (report / "artifact_manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "not checksum-bound"):
                verify_campaign_snapshot(root, report)
            manifest.update(child_manifests=[], source_checksums={"../outside": "0" * 64})
            (report / "artifact_manifest.json").write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                verify_campaign_snapshot(root, report)

    def test_repeated_source_does_not_bypass_narrow_artifact_boundary(self):
        from unittest.mock import patch

        from publication.contracts import safe_path, sha256_file

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = root / "reports"
            report.mkdir()
            artifact = report / "figure.svg"
            artifact.write_text("<svg/>")
            digest = sha256_file(artifact)
            (report / "artifact_manifest.json").write_text(json.dumps({
                "source_checksums": {"reports/figure.svg": digest}, "artifacts": {"figure.svg": digest}}))

            def boundary(base, name):
                if base == report and name == "figure.svg":
                    raise ValueError("Narrow artifact boundary must be evaluated")
                return safe_path(base, name)

            with patch("publication.synthesis.safe_path", side_effect=boundary):
                with self.assertRaisesRegex(ValueError, "Narrow artifact boundary"):
                    verify_campaign_snapshot(root, report)

    def test_flatten_keeps_campaign_identity_and_all_nominal_levels(self):
        data = {"s": coverage_metrics([], ["missing"])}
        rows = flatten_calibration("parent", data) + flatten_calibration("new", data)
        self.assertEqual(len(rows), 42)
        self.assertEqual({r["campaign_id"] for r in rows}, {"parent", "new"})
        self.assertTrue(all(r["declared_count"] == 1 for r in rows))
        self.assertTrue(all(r["empirical_coverage_numeric"] is None for r in rows))

    def test_missing_outputs_or_unsupported_release_promotion_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = {"schema_version": SCHEMA, "release_approved": False,
                        "artifacts": {}, "source_checksums": {}}
            (root / "artifact_manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "Missing required"):
                verify_bundle(root, root)
            manifest["release_approved"] = True
            (root / "artifact_manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "unsupported release"):
                verify_bundle(root, root)

    def test_validation_harness_preserves_receipt_when_source_is_missing(self):
        from types import SimpleNamespace
        from unittest.mock import patch

        from tests.manual import validate_post_campaign_synthesis as audit

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(audit, "ROOT", root), patch.object(sys, "argv", ["audit", "--output", "publication/validation/missing"]), \
                    patch.object(audit.subprocess, "run", return_value=SimpleNamespace(returncode=0)), \
                    patch.object(audit.subprocess, "check_output", return_value=b"a" * 40):
                with self.assertRaises(SystemExit) as caught:
                    audit.main()
            self.assertEqual(caught.exception.code, 1)
            payload = json.loads((root / "publication/validation/missing/validation.json").read_text())
            self.assertEqual(payload["status"], "failed")
            self.assertTrue(payload["missing_sources"])
            self.assertGreaterEqual(len(payload["checks"]), 6)
            self.assertEqual(len(payload["logs"]), 2 * len(payload["checks"]))
            self.assertFalse(next(row["passed"] for row in payload["checks"]
                                  if row["check"] == "paper_release_classified"))


if __name__ == "__main__":
    unittest.main()
