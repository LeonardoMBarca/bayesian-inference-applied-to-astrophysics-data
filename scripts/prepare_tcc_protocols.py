"""Generate reviewed TCC protocol candidates from preserved pre-result drafts.

Preparation only, no sampling. Refuses to alter an initialized final campaign.
Commit and freeze the full campaign ledger separately after tests pass.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    if (ROOT / "artifacts/publication_campaign/tcc_campaign_v1/campaign_state.json").exists():
        raise SystemExit("An initialized campaign cannot be refrozen")
    amendment = {
        "date_utc": "2026-09-26", "stage": "before any final scientific attempt",
        "reason": "User imposed 36h compute ceiling and TCC deadline; pilot timing only, never posterior quality, determines replication reduction.",
        "reference": "docs/publication/COMPUTE_BUDGET_AMENDMENT.md"
    }
    seeds = "publication.campaign_plan.seed: first32bits of canonical SHA256 ['campaign-seed-v1',campaign_id,experiment_id,scenario_id,replicate_id,stream]. PUB-04 generation substitutes pair_id for scenario_id. Frozen integer ledger is authoritative. Retries retain seeds; different campaigns have separate namespaces."
    for experiment in ("PUB-02", "PUB-04"):
        protocol = json.loads((ROOT / f"publication/protocols/{experiment}-draft.json").read_text(encoding="utf-8"))
        protocol.update(protocol_version="tcc-1.0.0", protocol_status="FROZEN", seed_policy=seeds,
                        freeze_note="Reviewed pre-result TCC specification. Execution requires committed exact protocol and frozen campaign ledger; no final result informed this design.")
        protocol["amendments"].append(amendment)
        protocol["temporal_diagnostic_scope"] = "Within-segment gap-filtered selected-observation lags1-5, not native cadence after thinning. Spacing proxy is median selected time gap. Degenerate/nonfinite/insufficient pairs are unavailable; positive PPC requires at least one finite evaluable lag and no flagged lag. This does not establish absence of correlations at unobserved timescales."
        protocol["inference"]["sampling"]["linker"] = "auto"
        if experiment == "PUB-02":
            protocol["deferred_scenarios"] = [item for item in protocol["scenarios"] if "_ou_" in item["scenario_id"]]
            protocol["scenarios"] = [item for item in protocol["scenarios"] if "_ou_" not in item["scenario_id"]]
            protocol.update(replicates_per_scenario=20,
                scenario_replicates={}, total_declared_final_attempts=80,
                deferred_scenario_reason="OU exploration deferred to a separate future campaign before any final results: full estimate40.75h exceeded36h, whereas four primary regimes plus P3/P4/P5 estimate31.86h. No correlated-noise calibration claim from this TCC batch.",
                replication_precision="Four main white-noise regimes: n=20 each. At n=20 binomial SE(.5/.8/.94)=.112/.089/.053. Wilson95 always; no proof of precise calibration from compatibility with nominal. No selection by results.")
        else:
            protocol["execution_authorized"] = True
            protocol["replication_plan"].update(replicates_per_pair=3, replicate_count_status="FROZEN_COMPUTE_LIMITED",
                total_declared_attempts_if_frozen_unchanged=30, expected_sampling_attempts=24,
                expected_pre_sampling_identity_rejections=6,
                precision_note="Three pairs per design support descriptive paired effects, NOT precise gate-error frequencies. SE at p=.5 is .289. Retain all effects/uncertainty; larger paper study is deferred, not selected after results.")
            protocol["interpretation_rules"][-1] = "Final claims require all frozen identities and diagnostics, not just the existence of this protocol."
        destination = ROOT / f"publication/protocols/{experiment}.json"
        destination.write_text(json.dumps(protocol, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(destination.relative_to(ROOT))


if __name__ == "__main__":
    main()
