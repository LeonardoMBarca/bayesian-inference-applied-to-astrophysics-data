"""Post-processing of recorded gates: evaluation, validity and use are distinct."""
from __future__ import annotations

from collections import Counter

SCHEMA = "component-gate-accounting-v2"
COMPONENTS = ("provenance", "sampler", "ppc", "joint")


def assess_gates(result: dict | None, *, status: str, verified: bool,
                 mode: str, fixture: bool = False, invalidated: dict | None = None) -> dict:
    """Only actual assessed evidence counts; technical fallback flags do not.

    Completed/rejected legacy numeric results explicitly record evaluated gates.
    Pre-sampling input rejection evaluates provenance only. Technical outcomes
    require an explicit component evaluation marker plus its diagnostic payload.
    Incident invalidation preserves the original Boolean and denies current use.
    """
    result = result or {}
    flags = result.get("gates", {})
    numeric = bool(result.get("parameters"))
    final_result = status in {"COMPLETED", "COMPLETED_REJECTED"} and numeric
    input_rejection = (result.get("failure_stage") == "input_validation"
                       and bool(result.get("failure_code")))
    explicit = result.get("diagnostics_evaluated", {})
    engineering = mode != "final" or fixture or result.get("fixture", False)
    invalidated = invalidated or {}
    components = {}
    for component in COMPONENTS:
        flag = flags.get("scientific" if component == "joint" else component)
        evaluated = final_result or (component == "provenance" and input_rejection)
        if explicit.get(component) is True:
            payload = {"sampler": "diagnostics", "ppc": "residual_metrics",
                       "provenance": "input_validation", "joint": "inherited_m5_gate"}[component]
            evaluated = evaluated or bool(result.get(payload))
        evaluated = bool(verified and evaluated and type(flag) is bool)
        reason = invalidated.get(component)
        current = "invalidated" if evaluated and reason else (
            "passed" if flag else "rejected") if evaluated else "unassessed"
        components[component] = {
            "recorded_decision": flag, "recorded_evaluated": evaluated,
            "current_status": current, "invalidation_reason": reason,
            "eligible_final_evidence": not engineering and current in {"passed", "rejected"},
        }
    return {"schema_version": SCHEMA, "mode": mode, "engineering_only": bool(engineering),
            "components": components}


def gate_counts(assessments: list[dict]) -> dict:
    """Disjoint categories; rates name evaluated and all-declared denominators."""
    counts = {}
    for component in COMPONENTS:
        entries = [row["components"][component] for row in assessments]
        categories = Counter(row["current_status"] for row in entries)
        passed, rejected = categories["passed"], categories["rejected"]
        evaluated = passed + rejected
        counts[component] = {
            "declared": len(entries), "evaluated": evaluated,
            "passed": passed, "rejected": rejected,
            "unassessed": categories["unassessed"], "invalidated": categories["invalidated"],
            "recorded_evaluated": sum(row["recorded_evaluated"] for row in entries),
            "recorded_passed": sum(row["recorded_evaluated"] and row["recorded_decision"] is True for row in entries),
            "final_evidence_evaluated": sum(row["eligible_final_evidence"] for row in entries),
            "final_evidence_passed": sum(row["eligible_final_evidence"] and row["current_status"] == "passed" for row in entries),
            "pass_rate_evaluated": passed / evaluated if evaluated else None,
            "pass_rate_all_declared": passed / len(entries) if entries else None,
            "rate_denominators": {"pass_rate_evaluated": evaluated, "pass_rate_all_declared": len(entries)},
        }
    return counts
