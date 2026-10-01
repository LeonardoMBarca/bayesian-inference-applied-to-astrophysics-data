from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from publication.claim_authorization import evaluate_run  # noqa: E402
from publication.gate_accounting import COMPONENTS, assess_gates, gate_counts  # noqa: E402


def result(sampler=True, ppc=True):
    return {"parameters": {"r": {"mean": .1, "sd": .01}},
            "gates": {"provenance": True, "sampler": sampler, "ppc": ppc, "scientific": sampler and ppc}}


def assessment(value, status="COMPLETED_REJECTED", **kwargs):
    return assess_gates(value, status=status, verified=True, mode=kwargs.pop("mode", "final"), **kwargs)


class ComponentAccountingTests(unittest.TestCase):
    def test_sampler_pass_ppc_fail_not_joint_failure_of_sampler(self):
        c = gate_counts([assessment(result(ppc=False))])
        self.assertEqual((c["sampler"]["passed"], c["ppc"]["rejected"], c["joint"]["rejected"]), (1, 1, 1))

    def test_sampler_fail_ppc_actually_evaluated(self):
        c = gate_counts([assessment(result(sampler=False))])
        self.assertEqual((c["sampler"]["rejected"], c["ppc"]["passed"], c["joint"]["passed"]), (1, 1, 0))

    def test_identity_control_evaluates_only_provenance(self):
        control = {"failure_stage": "input_validation", "failure_code": "input_sha256_mismatch",
                   "gates": dict.fromkeys(("sampler", "ppc", "scientific", "provenance"), False)}
        c = gate_counts([assessment(control)])
        self.assertEqual(c["provenance"]["rejected"], 1)
        self.assertEqual(c["sampler"]["unassessed"], 1)
        self.assertEqual(c["ppc"]["evaluated"], 0)

    def test_pending_and_technical_fallback_never_count_as_evaluated(self):
        c = gate_counts([assessment(None, "PLANNED"), assessment(result(False, False), "FAILED_TECHNICAL")])
        for row in c.values():
            self.assertEqual(row["evaluated"], 0)
            self.assertEqual(row["unassessed"], 2)
            self.assertIsNone(row["pass_rate_evaluated"])
        partial = result(False, False) | {"diagnostics_evaluated": {"sampler": True}, "diagnostics": {"divergences": 8}}
        self.assertEqual(gate_counts([assessment(partial, "FAILED_TECHNICAL")])["sampler"]["rejected"], 1)

    def test_fixture_smoke_pilot_excluded_from_final_evidence(self):
        for mode, fixture in (("smoke", False), ("pilot", False), ("final", True)):
            row = assessment(result(), mode=mode, fixture=fixture)
            c = gate_counts([row])
            self.assertEqual(c["sampler"]["passed"], 1)
            self.assertEqual(c["sampler"]["final_evidence_passed"], 0)
            evaluation = evaluate_run(result(), {}, run_identity={}, verified_sources={"fixture": "hash"},
                                      provenance_verified=True, family="PUB-02", scenario="fixture", mode=mode, fixture=fixture)
            self.assertFalse(evaluation["dimensions"]["manuscript_claim_permissions"]["claim_tested_predictive_screens_passed"])

    def test_incident_preserves_recorded_flag_denies_current_ppc_claim(self):
        row = assessment(result(), invalidated={"ppc": "conditioning", "joint": "depends on PPC"})
        c = gate_counts([row])
        self.assertEqual((c["ppc"]["recorded_passed"], c["ppc"]["invalidated"], c["ppc"]["evaluated"]), (1, 1, 0))
        evaluation = evaluate_run(result(), {}, run_identity={}, verified_sources={"fixture": "hash"}, provenance_verified=True,
                                  family="PUB-02", scenario="fixture", invalidated={"ppc": "conditioning"})
        self.assertEqual(evaluation["dimensions"]["predictive_screen"], "invalidated")
        self.assertTrue(evaluation["historical_gate"]["ppc"])
        self.assertFalse(evaluation["dimensions"]["manuscript_claim_permissions"]["claim_tested_predictive_screens_passed"])

    def test_families_sum_exactly_under_same_population(self):
        families = [[assessment(result(ppc=False)), assessment(result())], [assessment(result(sampler=False)), assessment(None, "PLANNED")]]
        total = gate_counts(sum(families, []))
        for component in COMPONENTS:
            for field in ("declared", "evaluated", "passed", "rejected", "unassessed", "invalidated"):
                self.assertEqual(total[component][field], sum(gate_counts(family)[component][field] for family in families))

    def test_vscode_only_current_postprocessing_or_readonly(self):
        tasks = json.loads((ROOT / ".vscode/tasks.json").read_text())["tasks"]
        for task in tasks:
            args = task.get("args", [])
            self.assertFalse(any(flag in args for flag in ("--resume", "--aggregate", "--dry-run")))
            if "Numerical v4" in task["label"]:
                self.assertTrue(any("v4" in arg for arg in args) or "--verify-original" in args)
            for arg in args:
                if arg.startswith("scripts/"):
                    self.assertTrue((ROOT / arg).is_file(), arg)
        self.assertTrue(any("--build" in task.get("args", []) for task in tasks))


if __name__ == "__main__":
    unittest.main()
