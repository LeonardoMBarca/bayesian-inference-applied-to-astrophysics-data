import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from publication.claim_authorization import authorize_claim, evaluate_run, prior_sd  # noqa: E402


class ClaimAuthorizationTests(unittest.TestCase):
    def evaluate(self, result, provenance=True, intervention=None):
        return evaluate_run(result, {"t0_prior_sigma_days": .025},
                            run_identity={"run_id": "fixture"},
                            verified_sources={"result.json": "a" * 64},
                            provenance_verified=provenance, family="PUB-02", scenario="fixture",
                            declared_intervention=intervention)

    def test_passing_historical_gate_does_not_grant_physical_recovery(self):
        result = {"parameters": {"a": {"sd": 13.}},
                  "gates": {"sampler": True, "ppc": True, "scientific": True},
                  "inherited_m5_gate": {"component_reasons": {"scientific": []}}}
        before = copy.deepcopy(result)
        review = self.evaluate(result)
        self.assertEqual(before, result)
        self.assertEqual(review["dimensions"]["physical_scale_screen"], "passed")
        self.assertEqual(review["dimensions"]["parameter_information"]["a"]["validated_identifiability"], "not_established")
        with self.assertRaises(ValueError):
            authorize_claim(review, "claim_all_parameters_accurately_recovered")

    def test_rejected_control_is_valid_negative_evidence_not_recovery(self):
        review = self.evaluate({"parameters": {"r": {"sd": .01}},
                                "gates": {"sampler": True, "ppc": False}})
        authorize_claim(review, "demonstrate_convergence_insufficient_for_ppc")
        self.assertEqual(review["dimensions"]["physical_scale_screen"], "unassessed")

    def test_unavailable_sampler_is_not_measured_failure(self):
        review = self.evaluate({"failure_stage": "input_validation",
                                "gates": {"provenance": False, "sampler": False, "ppc": False}})
        self.assertEqual(review["dimensions"]["computational_screen"], "unassessed")
        with self.assertRaises(ValueError):
            authorize_claim(review, "demonstrate_identity_control_blocked_before_sampling")

    def test_deliberate_control_requires_matching_predeclared_failure(self):
        for intervention, code in (("invalid_input_hash", "input_sha256_mismatch"),
                                   ("dataset_identity_mismatch", "dataset_identity_mismatch")):
            result = {"failure_stage": "input_validation", "failure_code": code,
                      "gates": {"provenance": False}}
            review = self.evaluate(result, intervention=intervention)
            authorize_claim(review, "demonstrate_identity_control_blocked_before_sampling")
            result["failure_code"] = "missing_column"
            with self.assertRaises(ValueError):
                authorize_claim(self.evaluate(result, intervention=intervention),
                                "demonstrate_identity_control_blocked_before_sampling")

    def test_unverified_provenance_and_unknown_claim_fail_closed(self):
        review = self.evaluate({"gates": {"sampler": True}}, None)
        for claim in ("report_attempt_and_historical_rejection", "invented_claim"):
            with self.assertRaises(ValueError):
                authorize_claim(review, claim)

    def test_prior_units_and_derived_na(self):
        self.assertEqual(prior_sd("t0", {"t0_prior_sigma_days": .025}), .025)
        self.assertAlmostEqual(prior_sd("a", {})**2, 192.)
        self.assertIsNone(prior_sd("full_duration", {}))


if __name__ == "__main__":
    unittest.main()
