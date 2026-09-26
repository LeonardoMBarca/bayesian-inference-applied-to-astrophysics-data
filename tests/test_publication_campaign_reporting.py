from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from publication.campaign_reporting import (  # noqa: E402
    _known_white_noise_snr,
    ablation_report,
    aggregate_campaign,
    benchmark_report,
    calibration_report,
    collect_campaign,
    state_fingerprint,
    validate_campaign_report,
)
from publication.contracts import sha256_file  # noqa: E402


def dump(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


class PublicationCampaignReportingTests(unittest.TestCase):
    def benchmark_fixture(self, root: Path) -> list[dict]:
        import numpy as np
        import pandas as pd
        import xarray as xr

        phase = np.linspace(-.1, .1, 12)
        latent = 1 - .001 * np.exp(-(phase/.03)**2)
        data = pd.DataFrame({"phase": phase, "time": 100 + np.arange(12)*.001,
                             "segment_id": ["first"] * 6 + ["second"] * 6,
                             "normalized_flux": latent + .00001 * np.sin(np.arange(12)),
                             "normalized_flux_err": .0001, "exposure_time_seconds": 60.})
        samples = {name: np.linspace(value*.9, value*1.1, 20) for name, value in
                   {"r": .1, "depth": .01, "b": .4, "a": 8., "t0": .001, "full_duration": .08, "extra_sigma": .0001}.items()}
        rows = []
        for engine in ("local", "external"):
            path = root / engine
            path.mkdir()
            data.to_csv(path / "input.csv", index=False, float_format="%.17g")
            digest = sha256_file(path / "input.csv")
            dump(path / "inference_config.json", {"period_days": 1., "oversample": 15})
            curve = data[["time", "phase", "segment_id"]].copy()
            curve["observed"] = data.normalized_flux
            curve["posterior_mean"] = latent if engine == "local" else latent + 3e-6 + phase*2e-6
            if engine == "external":
                curve = curve.iloc[::-1]
            curve.to_csv(path / "predictive_summary.csv", index=False)
            if engine == "local":
                xr.Dataset({name: (("chain", "draw"), values.reshape(2, 10)) for name, values in samples.items()}).to_netcdf(path / "trace.nc", group="posterior", engine="h5netcdf")
            else:
                np.savez_compressed(path / "posterior_samples.npz", **{name: values*1.01 for name, values in samples.items()})
            rows.append({"payload": {"kind": f"benchmark_{engine}"}, "result": {"status": "rejected", "dataset_id": "fixture", "input_sha256": digest},
                         "scientifically_interpretable": False, "authoritative_attempt_dir": engine,
                         "completion": {"artifacts": {p.name: sha256_file(p) for p in path.iterdir()}}})
        return rows

    def fixture(self, root: Path) -> tuple[dict, dict]:
        jobs = []
        for replicate in range(4):
            identifier = f"PUB-02__fixture__rep_{replicate:04d}"
            jobs.append({"job_id": identifier, "experiment_id": "PUB-02", "scenario_id": "fixture",
                         "replicate_id": f"rep_{replicate:04d}", "run_id": "report_fixture", "seeds": {"inference": replicate + 1},
                         "output_dir": f"artifacts/publication_campaign/report_fixture/runs/{identifier}",
                         "payload": {"kind": "synthetic"}})
        plan = {"campaign_id": "report_fixture", "mode": "smoke", "scientific_config_sha256": "config",
                "jobs": jobs, "config_path": "config.json", "protocols": {}, "phase_order": ["PUB-02", "PUB-03", "PUB-04", "PUB-05"], "preflight_errors": []}
        state = {"campaign_id": plan["campaign_id"], "scientific_config_sha256": "config", "status": "STOPPED", "jobs": {}}
        for index, job in enumerate(jobs):
            row = {**job, "status": ["COMPLETED", "COMPLETED_REJECTED", "FAILED_TECHNICAL", "PLANNED"][index], "attempts": []}
            state["jobs"][job["job_id"]] = row
            if index == 3:
                continue
            attempt_dir = root / job["output_dir"] / "attempt_000"
            attempt_dir.mkdir(parents=True)
            (attempt_dir / "input.csv").write_text("value\n1\n", encoding="utf-8")
            checksum = sha256_file(attempt_dir / "input.csv")
            parameter = {"mean": [.1, .11, .1][index], "median": .1, "sd": .01,
                         "intervals": {"0.5": [.095, .105], "0.8": [.09, .11], "0.94": [.08, .12]}}
            result = {"status": ["completed", "rejected", "failed"][index], "input_sha256": checksum, "dataset_id": "fixture-data",
                      "gates": {"provenance": True, "sampler": index < 2, "ppc": index == 0, "scientific": index == 0},
                      "parameters": {"r": parameter} if index < 2 else {}}
            dump(attempt_dir / "result.json", result)
            dump(attempt_dir / "truth.json", {"truth": {"r": .1}, "data_sha256": checksum})
            completion = {"status": row["status"], "gates": result["gates"], "input_sha256": checksum, "dataset_id": "fixture-data",
                          "artifacts": {name: sha256_file(attempt_dir / name) for name in ("result.json", "truth.json", "input.csv")}}
            dump(attempt_dir / "completion_manifest.json", completion)
            row["attempts"].append({"attempt_index": 0, "status": row["status"], "output_dir": attempt_dir.relative_to(root).as_posix(),
                                    "seeds": job["seeds"], "completion_manifest_sha256": sha256_file(attempt_dir / "completion_manifest.json")})
        dump(root / "config.json", {"campaign_id": plan["campaign_id"]})
        dump(root / "artifacts/publication_campaign/report_fixture/campaign_state.json", state)
        return plan, state

    def test_full_denominator_and_all_attempts_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan, state = self.fixture(root)
            evidence = collect_campaign(root, plan, state)
            self.assertEqual(len(evidence["jobs"]), 4)
            self.assertEqual(len(evidence["attempts"]), 3)
            self.assertEqual(evidence["integrity_errors"], [])
            self.assertEqual(sum(row["scientifically_interpretable"] for row in evidence["jobs"]), 0)
            self.assertEqual(sum(row["computational_gates_passed"] for row in evidence["jobs"]), 1)
            self.assertEqual(evidence["jobs"][3]["status"], "PLANNED")

    def test_changed_artifact_never_promotes_but_is_retained(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan, state = self.fixture(root)
            target = root / plan["jobs"][0]["output_dir"] / "attempt_000/result.json"
            target.write_text("{}", encoding="utf-8")
            evidence = collect_campaign(root, plan, state)
            self.assertTrue(evidence["integrity_errors"])
            self.assertIsNone(evidence["jobs"][0]["result"])
            self.assertFalse(evidence["jobs"][0]["scientifically_interpretable"])
            self.assertEqual(len(evidence["attempts"]), 3)

    def test_current_blocked_and_latest_partial_never_fall_back_to_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan, state = self.fixture(root)
            row = state["jobs"][plan["jobs"][0]["job_id"]]
            row["status"] = "BLOCKED"
            evidence = collect_campaign(root, plan, state)
            self.assertIsNone(evidence["jobs"][0]["result"])
            row["status"] = "CANCELLED"
            row["attempts"].append({"attempt_index": 1, "status": "CANCELLED", "output_dir": row["output_dir"] + "/attempt_001", "seeds": row["seeds"]})
            evidence = collect_campaign(root, plan, state)
            self.assertEqual(len(evidence["attempts"]), 4)
            self.assertIsNone(evidence["jobs"][0]["result"])

    def test_regeneration_coverage_and_bookkeeping_freshness(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan, state = self.fixture(root)
            with patch("publication.campaign_reporting.build_plan", return_value=plan):
                output = aggregate_campaign(root, Path("config.json"))
            summary = json.loads((output / "summary.json").read_text())
            self.assertEqual(summary["declared_jobs"], 4)
            self.assertEqual(summary["total_attempts"], 3)
            self.assertEqual(summary["scientifically_interpretable_count"], 0)
            self.assertEqual(summary["computational_gates_passed_count"], 1)
            self.assertTrue((output / "campaign_summary.md").exists())
            metrics = summary["families"]["PUB-02"]["scenarios"]["fixture"]
            self.assertEqual(metrics["declared_count"], 4)
            self.assertEqual(metrics["parameters"]["r"]["numeric_count"], 2)
            self.assertAlmostEqual(metrics["parameters"]["r"]["bias"], .005)
            self.assertEqual(metrics["parameters"]["r"]["coverage"]["0.94"]["operational_covered_and_passed_rate_all_declared"], .25)
            validate_campaign_report(root, output)
            state["aggregate"] = {"status": "COMPLETED"}
            state_path = root / "artifacts/publication_campaign/report_fixture/campaign_state.json"
            dump(state_path, state)
            validate_campaign_report(root, output)
            state["jobs"][plan["jobs"][3]["job_id"]]["status"] = "RUNNING"
            dump(state_path, state)
            with self.assertRaisesRegex(ValueError, "job state changed"):
                validate_campaign_report(root, output)

    def test_fingerprint_order_independent_but_seed_sensitive(self) -> None:
        first = {"jobs": {"b": {"job_id": "b", "attempts": [], "seeds": {"generation": 1}},
                          "a": {"job_id": "a", "attempts": []}}}
        second = {"jobs": dict(reversed(list(first["jobs"].items())))}
        self.assertEqual(state_fingerprint(first), state_fingerprint(second))
        second = copy.deepcopy(second)
        second["jobs"]["b"]["seeds"]["generation"] = 2
        self.assertNotEqual(state_fingerprint(first), state_fingerprint(second))

    def test_presampling_negative_control_is_rejected_not_technical_or_sampler_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan, state = self.fixture(root)
            job = plan["jobs"][1]
            job["payload"] = {"kind": "ablation", "intervention": "invalid_input_hash", "variant_id": "invalid_input_hash", "pair_id": "fixture"}
            row = state["jobs"][job["job_id"]]
            attempt = root / row["attempts"][0]["output_dir"]
            result = {"status": "failed", "failure_stage": "input_validation", "failure_code": "input_sha256_mismatch", "gates": {name: False for name in ("provenance", "sampler", "ppc", "scientific")}}
            dump(attempt / "result.json", result)
            completion = json.loads((attempt / "completion_manifest.json").read_text())
            completion.update(expected_identity_rejection=True, gates=result["gates"])
            completion["artifacts"]["result.json"] = sha256_file(attempt / "result.json")
            dump(attempt / "completion_manifest.json", completion)
            row["attempts"][0]["completion_manifest_sha256"] = sha256_file(attempt / "completion_manifest.json")
            evidence = collect_campaign(root, plan, state)
            self.assertEqual(evidence["integrity_errors"], [])
            self.assertIsNotNone(evidence["jobs"][1]["result"])
            report = ablation_report([evidence["jobs"][1]], root / "ablation")
            self.assertEqual(report["gate_matrix"][0]["gate_provenance"], False)
            self.assertIsNone(report["gate_matrix"][0]["gate_sampler"])
            self.assertIsNone(report["gate_matrix"][0]["gate_ppc"])
            calibration = calibration_report([evidence["jobs"][1]], root / "calibration", mode="smoke")
            self.assertEqual(calibration["scenarios"]["fixture"]["execution_failure_rate_all_declared"], 0)
            self.assertEqual(calibration["scenarios"]["fixture"]["gates"]["sampler"]["evaluated_count"], 0)

    def test_failed_benchmark_is_unavailable_not_false_agreement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = [{"payload": {"kind": f"benchmark_{engine}"}, "result": {"status": "failed"}} for engine in ("local", "external")]
            report = benchmark_report(root, rows, root)
            self.assertEqual(report["status"], "unavailable")
            self.assertNotIn("comparison", report)
            self.assertEqual(report["predictive_comparison"]["status"], "unavailable")
            self.assertIsNone(report["predictive_comparison"]["rms_mean_difference_ppm"])
            for filename in ("posterior_comparison.png", "predictive_comparison.png"):
                self.assertEqual(report["figures"][filename]["status"], "unavailable")
                self.assertGreater((root / filename).stat().st_size, 5000)

    def test_benchmark_figures_and_predictive_rows_map_to_original_input(self) -> None:
        import numpy as np
        import pandas as pd

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = self.benchmark_fixture(root)
            report = benchmark_report(root, rows, root)
            self.assertEqual(report["status"], "compared_descriptively")
            self.assertFalse(report["both_scientifically_interpretable"])
            self.assertEqual(report["predictive_comparison"]["status"], "compared_descriptively")
            self.assertTrue(report["predictive_comparison"]["row_mapping"]["engines"]["external"]["reordered"])
            self.assertFalse(report["predictive_comparison"]["row_mapping"]["engines"]["local"]["reordered"])
            table = pd.read_csv(root / "predictive_comparison.csv")
            np.testing.assert_allclose(table.external_minus_local_ppm, 3 + table.phase*2, rtol=0, atol=1e-8)
            np.testing.assert_array_equal(table.input_row_index, np.arange(12))
            for filename in ("posterior_comparison.png", "predictive_comparison.png"):
                self.assertEqual(report["figures"][filename]["status"], "available")
                self.assertGreater((root / filename).stat().st_size, 10000)

    def test_predictive_identity_mismatch_is_unavailable_not_zero_disagreement(self) -> None:
        import pandas as pd

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = self.benchmark_fixture(root)
            curve_path = root / "external/predictive_summary.csv"
            curve = pd.read_csv(curve_path)
            curve.loc[0, "observed"] += .001
            curve.to_csv(curve_path, index=False)
            report = benchmark_report(root, rows, root)
            self.assertEqual(report["predictive_comparison"]["status"], "unavailable")
            self.assertIn("phase/observed", report["validation_errors"][0])
            self.assertIsNone(report["predictive_comparison"]["rms_mean_difference_ppm"])
            self.assertEqual(report["figures"]["predictive_comparison.png"]["status"], "unavailable")

    def test_missing_benchmark_figures_are_bound_by_campaign_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan, state = self.fixture(root)
            for index, job in enumerate(plan["jobs"]):
                job["experiment_id"] = "PUB-03"
                job["payload"] = {"kind": "benchmark_local" if index == 0 else "benchmark_external"}
            plan["jobs"] = plan["jobs"][:2]
            state["jobs"] = {job["job_id"]: {**job, "status": "PLANNED", "attempts": []} for job in plan["jobs"]}
            dump(root / "artifacts/publication_campaign/report_fixture/campaign_state.json", state)
            with patch("publication.campaign_reporting.build_plan", return_value=plan):
                output = aggregate_campaign(root, Path("config.json"))
            manifest = json.loads((output / "artifact_manifest.json").read_text())
            for filename in ("posterior_comparison.png", "predictive_comparison.png", "predictive_comparison.csv"):
                relative = "PUB-03/" + filename
                self.assertEqual(manifest["artifacts"][relative], sha256_file(output / relative))
            validate_campaign_report(root, output)

    def test_known_white_snr_is_posthoc_scaled_and_excludes_correlated_variance(self) -> None:
        import math

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "input.csv"
            path.write_text("normalized_flux_err\n0.003\n0.004\n", encoding="utf-8")
            truth = {"truth": {"baseline": 1., "extra_sigma": .004},
                     "components": {"physical_signal": [.99, .98], "correlated_noise": [10., -10.]}}
            expected = math.sqrt(.01**2/(.003**2+.004**2) + .02**2/(.004**2+.004**2))
            self.assertAlmostEqual(_known_white_noise_snr(path, truth), expected)
            truth["components"]["correlated_noise"] = [0., 0.]
            self.assertAlmostEqual(_known_white_noise_snr(path, truth), expected)
            truth["components"]["physical_signal"] = [.99]
            with self.assertRaisesRegex(ValueError, "signal/error arrays"):
                _known_white_noise_snr(path, truth)

    def test_global_refreshes_family_metadata_and_every_manifest_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan, _ = self.fixture(root)
            with patch("publication.campaign_reporting.build_plan", return_value=plan):
                family_dir = aggregate_campaign(root, Path("config.json"), family="PUB-02")
                original_manifest = json.loads((family_dir / "artifact_manifest.json").read_text())
                dump(root / "config.json", {"campaign_id": plan["campaign_id"], "description": "Updated report metadata"})
                (family_dir / "REPORT.md").write_text("STALE REPORT", encoding="utf-8")
                (family_dir / "calibration.csv").write_text("STALE TABLE", encoding="utf-8")
                dump(family_dir / "summary.json", {"stale": True})
                with patch("publication.campaign_reporting.collect_campaign", wraps=collect_campaign) as collect:
                    output = aggregate_campaign(root, Path("config.json"))
                self.assertEqual(collect.call_count, 1)
            self.assertNotIn("STALE REPORT", (family_dir / "REPORT.md").read_text())
            self.assertNotIn("STALE TABLE", (family_dir / "calibration.csv").read_text())
            family_summary = json.loads((family_dir / "summary.json").read_text())
            self.assertEqual(family_summary["family_filter"], "PUB-02")
            self.assertEqual(family_summary["declared_jobs"], 4)
            manifest = json.loads((family_dir / "artifact_manifest.json").read_text())
            self.assertNotEqual(manifest["source_checksums"]["config.json"], original_manifest["source_checksums"]["config.json"])
            self.assertEqual(manifest["source_checksums"]["config.json"], sha256_file(root / "config.json"))
            validate_campaign_report(root, output)
            validate_campaign_report(root, family_dir)
            parent_manifest_path = output / "artifact_manifest.json"
            parent_manifest = json.loads(parent_manifest_path.read_text())
            omitted = copy.deepcopy(parent_manifest)
            omitted["child_manifests"] = []
            dump(parent_manifest_path, omitted)
            with self.assertRaisesRegex(ValueError, "omits a required family manifest"):
                validate_campaign_report(root, output)
            dump(parent_manifest_path, parent_manifest)
            (family_dir / "REPORT.md").write_text("tampered family report", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "REPORT.md"):
                validate_campaign_report(root, output)

    def test_global_checks_family_contract_not_only_its_manifest_file_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan, _ = self.fixture(root)
            with patch("publication.campaign_reporting.build_plan", return_value=plan):
                output = aggregate_campaign(root, Path("config.json"))
            family_manifest_path = output / "PUB-02/artifact_manifest.json"
            family_manifest = json.loads(family_manifest_path.read_text())
            family_manifest["source_checksums"]["config.json"] = "0" * 64
            dump(family_manifest_path, family_manifest)
            root_manifest = json.loads((output / "artifact_manifest.json").read_text())
            # Rebinding the opaque child file is not enough: its own scientific
            # source contract must still be evaluated recursively.
            root_manifest["artifacts"]["PUB-02/artifact_manifest.json"] = sha256_file(family_manifest_path)
            dump(output / "artifact_manifest.json", root_manifest)
            with self.assertRaisesRegex(ValueError, "Stale campaign source: config.json"):
                validate_campaign_report(root, output)

    def test_pub05_target_report_survives_global_and_family_metadata_generation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            protocol = json.loads((PROJECT_ROOT / "publication/protocols/PUB-05.json").read_text(encoding="utf-8"))
            dump(root / "protocol.json", protocol)
            dump(root / "config.json", {"campaign_id": "targets_fixture"})
            jobs = [{"job_id": slug, "experiment_id": "PUB-05", "scenario_id": slug, "replicate_id": "rep_0000",
                     "run_id": "targets_fixture", "seeds": {}, "output_dir": f"artifacts/publication_campaign/targets_fixture/runs/{slug}",
                     "payload": {"kind": "observational"}} for slug in protocol["declared_target_ids"]]
            plan = {"campaign_id": "targets_fixture", "mode": "smoke", "scientific_config_sha256": "config", "config_path": "config.json",
                    "protocols": {"PUB-05": {"path": "protocol.json", "sha256": sha256_file(root / "protocol.json")}},
                    "jobs": jobs, "phase_order": ["PUB-05"], "preflight_errors": []}
            state = {"campaign_id": "targets_fixture", "status": "PLANNED", "scientific_config_sha256": "config",
                     "jobs": {job["job_id"]: {**job, "status": "PLANNED", "attempts": []} for job in jobs}}
            dump(root / "artifacts/publication_campaign/targets_fixture/campaign_state.json", state)
            with patch("publication.campaign_reporting.build_plan", return_value=plan):
                family = aggregate_campaign(root, Path("config.json"), family="PUB-05")
                target_report = (family / "REPORT.md").read_bytes()
                validate_campaign_report(root, family)
                output = aggregate_campaign(root, Path("config.json"))
            self.assertEqual((family / "REPORT.md").read_bytes(), target_report)
            self.assertIn("| Target | Status |", target_report.decode())
            self.assertTrue((family / "CAMPAIGN_REPORT.md").exists())
            family_manifest = json.loads((family / "artifact_manifest.json").read_text())
            self.assertIn("target_artifact_manifest.json", family_manifest["child_manifests"])
            self.assertIn("REPORT.md", family_manifest["artifacts"])
            self.assertIn("CAMPAIGN_REPORT.md", family_manifest["artifacts"])
            target_manifest = json.loads((family / "target_artifact_manifest.json").read_text())
            self.assertEqual(target_manifest["artifacts"]["REPORT.md"], sha256_file(family / "REPORT.md"))
            validate_campaign_report(root, output)
            validate_campaign_report(root, family)

    def test_incomplete_ablation_pairs_are_unavailable_not_zero(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan, state = self.fixture(root)
            rows = collect_campaign(root, plan, state)["jobs"]
            for index, row in enumerate(rows[:2]):
                row["payload"] = {"pair_id": "fixture", "variant_id": "baseline" if index == 0 else "global"}
                row["replicate_id"] = "rep_0000"
            rows[1]["result"] = None
            output = root / "derived"
            report = ablation_report(rows[:2], output)
            effects = [row for row in report["paired_effects"] if row["variant_id"] == "global"]
            self.assertEqual(len(effects), 7)
            self.assertTrue(all(not row["pair_complete_numeric"] and row["mean_shift"] is None for row in effects))


if __name__ == "__main__":
    unittest.main()
