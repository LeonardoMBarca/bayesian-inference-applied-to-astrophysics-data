"""Post-result, claim-scoped evaluation; never rewrites a historical gate.

Information ratios are exploratory descriptions, not an identifiability gate.
This module never accepts truth values when assessing an observational run.
"""
from __future__ import annotations

import math
from copy import deepcopy

from publication.gate_accounting import assess_gates

EVALUATOR_VERSION = "claim-scope-review-v3"
PARAMETERS = ("r", "depth", "b", "a", "t0", "full_duration", "extra_sigma")


def _status(value: bool | None) -> str:
    return "unassessed" if value is None else "passed" if value else "rejected"


def prior_sd(parameter: str, config: dict) -> float | None:
    """Analytic marginal prior SD where the inference contract is explicit."""
    if parameter in {"b", "a"}:
        return (1.0 if parameter == "b" else 48.0) / math.sqrt(12)
    if parameter == "t0":
        return config.get("t0_prior_sigma_days")
    if parameter == "r":
        if config.get("radius_prior_uniform"):
            low, high = config["radius_prior_uniform"]
            return (high - low) / math.sqrt(12)
        median, sigma = config.get("radius_prior_median"), config.get("radius_prior_log_sigma")
        if median is not None and sigma is not None:
            return median * math.exp(sigma**2 / 2) * math.sqrt(math.expm1(sigma**2))
    # Derived duration/depth and error-dependent jitter require their full prior.
    return None


def evaluate_run(result: dict, config: dict, *, run_identity: dict,
                 verified_sources: dict[str, str], provenance_verified: bool | None,
                 family: str, scenario: str, declared_intervention: str | None = None,
                 status: str | None = None, mode: str = "final",
                 invalidated: dict | None = None, fixture: bool = False) -> dict:
    """Return six distinct evidence dimensions and purpose-specific permissions.

    ``provenance_verified`` is a NEW explicit byte-verification result supplied
    by the caller, not inferred from a stored scientific approval. Null denotes
    unavailable evidence. Historical flags are copied without reinterpretation.
    """
    if not verified_sources:
        raise ValueError("A review requires identified source artifacts")
    historical = deepcopy(result.get("gates", {}))
    numeric = bool(result.get("parameters"))
    inferred_status = "COMPLETED_REJECTED" if numeric and result.get("status") != "failed" else "FAILED_TECHNICAL"
    assessment = assess_gates(result, status=status or inferred_status,
                              verified=provenance_verified is True, mode=mode,
                              fixture=fixture, invalidated=invalidated)
    sampler_status = assessment["components"]["sampler"]["current_status"]
    ppc_status = assessment["components"]["ppc"]["current_status"]
    sampler = True if sampler_status == "passed" else False if sampler_status == "rejected" else None
    ppc = True if ppc_status == "passed" else False if ppc_status == "rejected" else None
    reasons = result.get("inherited_m5_gate", {}).get("component_reasons", {})
    scale = not reasons["scientific"] if numeric and "scientific" in reasons else None
    expected_code = {"invalid_input_hash": "input_sha256_mismatch",
                     "dataset_identity_mismatch": "dataset_identity_mismatch"}.get(declared_intervention)
    identity_control = (expected_code is not None and result.get("failure_stage") == "input_validation"
                        and result.get("failure_code") == expected_code)
    information = {}
    for name in PARAMETERS:
        posterior = result.get("parameters", {}).get(name, {})
        sd0, sd1 = prior_sd(name, config), posterior.get("sd")
        ratio = sd1 / sd0 if sd0 and sd1 is not None and math.isfinite(sd1) else None
        information[name] = {
            "posterior_sd": sd1, "prior_sd": sd0,
            "posterior_to_prior_sd_ratio": ratio,
            "status": "exploratory_computable" if ratio is not None else "unassessed",
            "precision_qualified_by_sampler": sampler is True,
            "validated_identifiability": "not_established",
            "scope": f"{family}/{scenario}/{name}",
        }
    descriptive = provenance_verified is True
    final_evidence = descriptive and not assessment["engineering_only"]
    permissions = {
        "report_attempt_and_historical_rejection": descriptive,
        "describe_numerical_output_with_sampler_caveat": descriptive and numeric,
        "claim_computational_screen_passed": final_evidence and sampler is True,
        "claim_tested_predictive_screens_passed": final_evidence and ppc is True,
        "demonstrate_identity_control_blocked_before_sampling": descriptive and identity_control and not numeric,
        "demonstrate_convergence_insufficient_for_ppc": final_evidence and sampler is True and ppc is False,
        # No run-level gate, even a positive one, licenses these broader claims.
        "claim_all_parameters_accurately_recovered": False,
        "claim_universal_calibration": False,
        "claim_independent_astrophysical_validation": False,
        "claim_gp_resolves_observed_residuals": False,
    }
    return {
        "schema_version": EVALUATOR_VERSION, "run_identity": deepcopy(run_identity),
        "source_checksums": dict(sorted(verified_sources.items())),
        "historical_gate": historical,
        "gate_assessment": assessment,
        "declared_intervention": declared_intervention,
        "evaluation_timing": "post_result_exploratory; not a prospective new gate",
        "dimensions": {
            "provenance_integrity": _status(provenance_verified),
            "provenance_scope": "Integrity of preserved evidence bytes, including deliberately invalid inputs in negative controls.",
            "historical_input_provenance_contract": _status(historical.get("provenance")),
            "computational_screen": sampler_status,
            "predictive_screen": ppc_status,
            "physical_scale_screen": _status(scale),
            "parameter_information": information,
            "manuscript_claim_permissions": permissions,
        },
        "limitations": [
            "A passed numerical screen does not establish posterior exactness or identifiability.",
            "Historical joint scientific Boolean is retained, not a parameter-recovery guarantee.",
            "Variance contraction is exploratory, can reflect prior influence, and has no tuned cutoff.",
            "Parameter/regime recovery claims require separate repeated-simulation evidence.",
            "Negative-control detection is not physical parameter recovery; a single noncoverage event is not a gate false positive.",
        ],
    }


def authorize_claim(evaluation: dict, claim: str) -> None:
    """Fail closed for unknown, unsupported or unverified manuscript claims."""
    if evaluation.get("schema_version") not in {EVALUATOR_VERSION, "claim-scope-review-v2"}:
        raise ValueError("Unknown claim evaluator")
    permissions = evaluation["dimensions"]["manuscript_claim_permissions"]
    if permissions.get(claim) is not True:
        raise ValueError(f"Unsupported claim: {claim}")
