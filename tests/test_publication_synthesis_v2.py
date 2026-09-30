from __future__ import annotations

import hashlib
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from publication import synthesis_v2 as module
from publication.claim_authorization import evaluate_run
from publication.trace_audit import SCHEMA


def put_json(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SynthesisV2ReviewTests(unittest.TestCase):
    def fixture(self, root):
        trace = root / "trace.nc"
        trace.write_bytes(b"fixture trace bytes")
        digest = hashlib.sha256(trace.read_bytes()).hexdigest()
        generator = root / "review_generator.py"
        generator.write_bytes(b"# original review generator\n")
        generator_digest = hashlib.sha256(generator.read_bytes()).hexdigest()
        audit = {"schema_version": SCHEMA, "status": "PASS",
                 "cohorts": {name: {"discrepancies": []} for name in module.COHORTS},
                 "source_checksums": {"trace.nc": digest}}
        audit_digest = put_json(root, module.AUDIT, audit)
        put_json(root, str(Path(module.AUDIT).parent / "artifact_manifest.json"),
                 {"artifacts": {"audit.json": audit_digest}, "source_checksums": {"trace.nc": digest}})
        for name in (module.RESIDUAL, module.MECHANISM):
            put_json(root, name, {"source_checksums": {"trace.nc": digest},
                                 "generator_source_checksums": {"review_generator.py": generator_digest}})
        put_json(root, module.TRANSITIVE, {"files": [{"path": "trace.nc", "sha256": digest,
                                                    "resolution": "working_tree_bytes"}]})
        return audit

    def test_actual_uppercase_pass_contract_accepted_and_all_sources_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            with patch.object(module, "verify_inventory") as verifier:
                audit, _, _, sources = module.verified_analysis_inputs(root)
            verifier.assert_called_once()
            self.assertEqual(audit["status"], "PASS")
            self.assertIn("trace.nc", sources)
            self.assertIn(module.TRANSITIVE, sources)
            self.assertIn(str(Path(module.AUDIT).parent / "artifact_manifest.json"), sources)

    def test_stale_trace_fails_even_when_audit_json_and_status_are_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            (root / "trace.nc").write_bytes(b"changed after audit")
            with patch.object(module, "verify_inventory"), self.assertRaisesRegex(ValueError, "checksum mismatch"):
                module.verified_analysis_inputs(root)

    def test_stale_review_generator_cannot_be_rebound_as_if_outputs_were_fresh(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            (root / "review_generator.py").write_bytes(b"# changed algorithm after report\n")
            with patch.object(module, "verify_inventory"), self.assertRaisesRegex(ValueError, "Source changed"):
                module.verified_analysis_inputs(root)

    def test_missing_review_generator_evidence_is_not_assumed_current(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            content = json.loads((root / module.RESIDUAL).read_text(encoding="utf-8"))
            del content["generator_source_checksums"]
            put_json(root, module.RESIDUAL, content)
            with patch.object(module, "verify_inventory"), self.assertRaisesRegex(ValueError, "generator_source_checksums"):
                module.verified_analysis_inputs(root)

    def test_transitive_invalidity_cannot_be_promoted_by_local_four_file_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            with patch.object(module, "verify_inventory", side_effect=ValueError("RAW mismatch")):
                with self.assertRaisesRegex(ValueError, "RAW mismatch"):
                    module.verified_analysis_inputs(root)

    def test_failed_and_unknown_audit_schemas_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for change in ({"status": "FAIL"}, {"schema_version": "unknown"}):
                audit = self.fixture(root)
                put_json(root, module.AUDIT, {**audit, **change})
                with self.assertRaises(ValueError):
                    module.verified_analysis_inputs(root)

    def test_recovery_denominators_use_p2_and_conditioned_parameter_counts(self):
        scenario = {"counts": {"declared_jobs": 20, "numeric_jobs": 19,
                               "gates": {"sampler": {"passed": 17}}, "joint_gate_passed_jobs": 16},
                    "metrics": {"r": {"all_numeric": {"numeric_count": 19},
                                      "sampler_passed": {"numeric_count": 17},
                                      "joint_gate_passed": {"numeric_count": 16}}}}
        audit = {"cohorts": {"parent": {"counts": {"declared_jobs": 80}, "p2_attempts": 81,
                                          "scenarios": {"shallow_short": scenario}}}}
        result = module.claim_denominators("conditional_recovery", audit, {}, [], {})
        self.assertEqual(result["parent"]["p2_declared_jobs"], 80)
        self.assertEqual(result["parent"]["p2_preserved_attempts"], 81)
        self.assertEqual(result["parent"]["by_scenario"]["shallow_short"]["parameter_subset_counts"]["r"]["joint_gate_passed"], 16)
        self.assertNotIn("campaign_context", result)

    def review(self, family, scenario, *, numeric=True, sampler=True, ppc=False):
        result = {"gates": {"sampler": sampler, "ppc": ppc}}
        if numeric:
            result["parameters"] = {"r": {"sd": .01}}
        else:
            result["failure_stage"] = "input_validation"
            result["failure_code"] = "input_sha256_mismatch"
        return evaluate_run(result, {}, run_identity={"job_id": f"{family}__{scenario}__rep_0", "scenario_id": scenario},
                            verified_sources={"fixture": "a" * 64}, provenance_verified=True,
                            family=family, scenario=scenario,
                            declared_intervention="invalid_input_hash" if not numeric else None)

    def test_family_denominators_never_use_other_families(self):
        summary = {"jobs": [{"experiment_id": "PUB-04", "status": "COMPLETED_REJECTED"}] * 3
                   + [{"experiment_id": "PUB-02", "status": "COMPLETED"}] * 80,
                   "attempts": [{"experiment_id": "PUB-04"}] * 3 + [{"experiment_id": "PUB-02"}] * 81}
        reviews = [self.review("PUB-04", "bad_signal"), self.review("PUB-04", "identity", numeric=False),
                   self.review("PUB-04", "insufficient", sampler=False)]
        counts = module.claim_denominators("convergence_insufficient", {}, {module.COHORTS[0]: summary}, reviews, {})
        self.assertEqual(counts["declared_jobs"], 3)
        self.assertEqual(counts["numerical_outputs"], 2)
        self.assertEqual(counts["identity_controls_blocked"], 1)
        self.assertEqual(counts["sampler_unassessed"], 1)
        self.assertEqual(counts["sampler_passed"], 1)

    def test_initializer_points_are_not_final_posterior_replications(self):
        mechanism = {"initializer_draws": {"direct": {"seeds": [1, 2], "initial_t0_days": [.1, .2]},
                                            "standardized": {"seeds": [1, 2], "initial_t0_days": [.0025, .005]}},
                     "historical_chain_means_days": [-.83, 0, 0, 0]}
        result = module.claim_denominators("t0_mechanism", {}, {}, [], mechanism)
        self.assertEqual(result["initializer_only"]["direct"]["initial_points"], 2)
        self.assertEqual(result["new_final_posterior_runs"], 0)
        self.assertEqual(result["historical_chains_retained"], 4)

    def test_parameter_regime_statement_is_descriptive_not_new_universal_gate(self):
        metrics = {"all_numeric": {"bias": 10, "numeric_count": 100}}
        audit = {"cohorts": {"separate_cohort": {"scenarios": {"weak": {
            "metrics": {"a": metrics}, "operational_yield": {"a": {"0.94": {"rate": .07}}}}}}}}
        rows = module.parameter_regime_evidence(audit)
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["campaign"], rows[0]["scenario"], rows[0]["parameter"]), ("separate_cohort", "weak", "a"))
        self.assertEqual(rows[0]["quantitative_evidence"], metrics)
        self.assertIn("universal_identifiability", rows[0]["unsupported_claims"])
        self.assertEqual(rows[0]["support_status"], "trace_verified_descriptive_evidence")

    def test_coverage_plot_keeps_wilson_uncertainty_and_na(self):
        cells = {"0.5": {"empirical_coverage": .5, "wilson95": [.4, .6]},
                 "0.8": {"empirical_coverage": None, "wilson95": None},
                 "0.94": {"empirical_coverage": 1., "wilson95": [.96, 1.]}}
        values, errors = module.coverage_plot_values(cells, ["0.5", "0.8", "0.94"])
        self.assertTrue(math.isnan(values[1]))
        self.assertAlmostEqual(errors[0][0], .1)
        self.assertAlmostEqual(errors[0][2], .04)
        self.assertEqual(errors[1][2], 0)
        cells["0.5"]["wilson95"] = [.7, .9]
        with self.assertRaises(ValueError):
            module.coverage_plot_values(cells, ["0.5"])

    def test_priors_come_from_declared_config_and_recorded_model_not_truth(self):
        config = {"radius_prior_median": .04, "radius_prior_log_sigma": .9,
                  "t0_prior_sigma_days": .025, "sampling": {"draws": 1000, "cores": 2},
                  "truth": {"r": .1}}
        model = {"a_prior": [2, 50], "b_prior": [0, 1], "t0_prior_mean_days": 0}
        profile = module.prior_profile(config, model, {"inference_assumptions": {"radius": "declared LogNormal"},
                                                      "scenarios": [{"truth": {"r": .1}}]}, numeric_output=True)
        self.assertEqual(profile["declared_inference_prior_fields"]["radius_prior_median"], .04)
        self.assertEqual(profile["sealed_model_prior_metadata"]["a_prior"], [2, 50])
        self.assertNotIn("truth", profile["declared_inference_prior_fields"])
        self.assertNotIn("scenarios", profile["frozen_protocol_prior_contracts"])
        self.assertEqual(profile["actual_sampler"]["engine"], "PyMC/NUTS")
        self.assertNotIn("cores", profile["actual_sampler"]["settings"])

    def test_benchmark_native_sampler_and_no_jitter_variant_not_conflated(self):
        config = {"radius_prior_uniform": [.001, .2], "infer_jitter": False,
                  "sampling": {"draws": 2000}, "benchmark_sampling": {"nlive": 500}}
        profile = module.prior_profile(config, {}, {"comparison_contract": [{"item": "geometry", "rule": "matched"}]}, numeric_output=False)
        self.assertEqual(profile["declared_inference_prior_fields"]["radius_prior_uniform"], [.001, .2])
        self.assertFalse(profile["declared_inference_prior_fields"]["infer_jitter"])
        self.assertEqual(profile["actual_sampler"], {"engine": "juliet/dynesty", "settings": {"nlive": 500}})
        self.assertEqual(profile["execution_scope"], "declared_input_only_rejected_before_fit")

    def test_custom_output_inventory_points_to_the_actual_new_version(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "reports" / "review_custom_v3"
            output.mkdir(parents=True)
            (output / "REPORT.md").write_text("new report", encoding="utf-8")
            inventory = module.source_inventory(root, output)
            self.assertEqual(inventory["tcc_sources"], ["reports/review_custom_v3/REPORT.md"])
            self.assertIn("--check --output reports/review_custom_v3", inventory["reproduction"])
            self.assertNotIn(module.OUTPUT, inventory["reproduction"])

    def test_external_output_rejected_before_any_evidence_reads_or_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repository"
            root.mkdir()
            outside = Path(directory) / "outside"
            with self.assertRaisesRegex(ValueError, "inside the repository"):
                module.build(root, outside)
            self.assertFalse(outside.exists())


if __name__ == "__main__":
    unittest.main()
