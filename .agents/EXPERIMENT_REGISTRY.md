# Publication Experiment Registry

This file is the human-readable index for publication-grade experiments. Machine-readable configs/artifacts are authoritative for numerical values; this registry records intent, protocol status and evidence location.

## Status vocabulary

- `PLANNED`: protocol exists, no final scientific run started.
- `PILOT`: implementation/debug runs only; excluded from final claims unless protocol explicitly states otherwise.
- `RUNNING`: final declared batch has started.
- `COMPLETED`: declared batch finished and required validation artifacts exist.
- `FAILED`: execution failed; preserve evidence.
- `REJECTED`: execution completed but failed one or more interpretation gates.
- `NOT_INTERPRETABLE`: technically available output that must not support scientific conclusions.

Never convert a failed/rejected run to `COMPLETED` by editing its historical artifact. Rerun under a new run ID after fixing the cause.

## Baseline

| Item | Value |
|---|---|
| base branch | `main` |
| base commit | `7489a90689a753bea5243f86c1489329916c98e2` |
| primary observational target | Kepler-10 b |
| canonical baseline run | `scientific_003` |
| Gold dataset | `kepler_10_b-b4d1e6ec961c1f4d` |
| M5 input SHA-256 | `6653fced1df0b3a29be96d181daa695f86ef709a7aa459bc1b3f837d48ad8791` |
| baseline model version | `m5-v2-exposure-integrated` |

## Final experiment families

| ID | Family | Core question | Protocol | Status | Final evidence |
|---|---|---|---|---|---|
| PUB-00 | baseline freeze | Can the validated TCC baseline be cryptographically and semantically frozen? | `publication/baseline/README.md` (identity-verification contract, not a scientific batch) | COMPLETED | 26 artifacts verified; 12 contract tests; `publication/baseline/VALIDATION.md`; commit `06003cf` |
| PUB-01 | novelty/literature map | What is genuinely new relative to published tools/workflows? | `docs/publication/NOVELTY_MATRIX.json` search scope | COMPLETED | 24 primary-source records; scoped integration/evaluation positioning, not priority proof |
| PUB-02 | injection–recovery calibration | Does the workflow recover known truths with calibrated uncertainty? | `publication/protocols/PUB-02.json`; `PUB-02-confirmatory-v1.json` | COMPLETED (bounded/negative findings) | Parent 80 plus independent 400, reported separately; severe low-information geometric undercoverage; `reports/publication_synthesis/tcc_evidence_v1/` |
| PUB-03 | independent benchmark | Does an independent published implementation obtain compatible inference? | `publication/protocols/PUB-03.json` | REJECTED (both fits executed) | Local alias/nonconvergence and external temporal PPC failure; descriptive comparison only |
| PUB-04 | ablations/failure gates | Which design choices matter and do gates reject invalid cases? | `publication/protocols/PUB-04.json` | COMPLETED (interpretation limited) | All 30 attempted; nine sampler-pass/PPC-fail cases; six identity controls rejected; paired effects limited by baseline divergences |
| PUB-05 | multi-target validation | Across which real observational regimes does the workflow succeed/fail? | `publication/protocols/PUB-05.json` | REJECTED (all targets attempted) | All five retained; all fail temporal PPC; four pass sampler; no positive generalization |
| PUB-06 | correlated-noise M6 | When temporal correlation exists, does explicit covariance improve calibration? | `docs/publication/COMPUTE_BUDGET_AMENDMENT.md` | PLANNED (deferred) | Disabled in TCC campaign by user compute/deadline priority; no GP claim |
| PUB-07 | paper reproducibility release | Can every publication-critical artifact be traced and regenerated? | to create | PLANNED (not release-approved) | Local synthesis checksums available; archival restoration, clean release and campaign-aware release gate remain |
| PUB-08 | TCC/paper synthesis | Do final written claims match the validated experiment registry? | post-result analysis | COMPLETED (TCC evidence handoff, not final manuscript submission) | Generated metrics, report, figures, claims and source inventory in `reports/publication_synthesis/tcc_evidence_v1/`; scientific reviews in `docs/publication/` |

## Required fields for every final experiment protocol

`PUB-01 COMPLETED` refers only to the scoped literature snapshot, not proof of
novelty. Protocol candidates PUB-02–05 are frozen before the user-launched batch;
the runner requires their exact committed bytes and the tested-source ledger.
No pilot or infrastructure fixture is final scientific evidence.

## Autonomous TCC campaign handoff (historical prelaunch snapshot)

At this historical handoff, the user instruction deferred execution of the large final
batch to the user. The deliverable now is a validated autonomous runner, not
fabricated completion of the research program. The final ledger
`configs/publication/tcc_campaign_v1_plan.json` declares 117 jobs and seeds;
after launch the machine-readable status authority is
`artifacts/publication_campaign/tcc_campaign_v1/campaign_state.json`.
Legacy `publication/registry.json` links that campaign ledger; its older
`expected_runs` fields are not the new campaign denominator.

`runner_smoke_v2` validated interruption/resume/idempotence and the physical
worker with 20 draws. Five jobs and six attempts include the preserved
technical failure and two rejections; none is a final science result.
`runner_smoke_v1` remains an interrupted engineering attempt, including its
state-read/harness failure. See `docs/publication/CAMPAIGN_RUNBOOK.md`.

Each protocol must record:

- `experiment_id`;
- protocol version and commit SHA;
- scientific question/hypothesis;
- primary outcome metrics;
- secondary metrics;
- scenario/target selection rule;
- inclusion/exclusion rule;
- model and likelihood identity;
- prior profiles;
- sampler settings;
- random-seed policy;
- diagnostic thresholds;
- missing/failed-run handling;
- statistical summary/uncertainty for aggregate metrics;
- planned figures/tables;
- amendment history.

## Anti-cherry-picking rule

Once a final batch begins, its declared scenario/target list is immutable except through an explicit amendment. An amendment must state whether the original batch remains valid, and removed/failed cases remain visible in the registry.

## Evidence promotion rule

A result may support the paper/TCC only when:

1. its protocol existed before its final batch;
2. its input identity is valid;
3. its execution status is `completed`;
4. applicable sampler/PPC/scientific gates pass, or the result is explicitly used as a negative/failure case;
5. aggregate reports include declared failed/missing runs in the denominator where relevant;
6. documentation is generated from or cross-checked against machine-readable artifacts.

This registry must be updated as work progresses, but never by erasing unfavorable outcomes.

## Independent P2 confirmatory extension, 2026-09-27

`tcc_calibration_confirmatory_v1` was registered **PLANNED** before its first
final attempt and is now **COMPLETED**. Protocol:
`publication/protocols/PUB-02-confirmatory-v1.json`;
config: `configs/publication/tcc_calibration_confirmatory_v1.json`.
It declares 100 NEW replicates per each of the four original P2 scenarios
(400 total), under unchanged truth/design, priors, likelihood, sampler and gates.
All streams use the new campaign namespace. The primary cohort is independent;
parent and new results must be reported separately. No best-seed selection or
outcome-driven stopping is permitted. The 22h additional soft budget and
post-parent-result decision are documented in
`docs/publication/CONFIRMATORY_CALIBRATION_CAMPAIGN.md`.

The parent `tcc_campaign_v1` machine state records COMPLETED with 117 terminal
jobs (66 COMPLETED, 51 COMPLETED_REJECTED) and final aggregation. This is
execution completion, not completion of scientific audit or evidence promotion;
the final family dispositions above include the post-campaign scientific audit.
The extension does not rerun or replace the parent's rejected P3/P5 outcomes.
After launch, status authority is
`artifacts/publication_campaign/tcc_calibration_confirmatory_v1/campaign_state.json`.
The exact 400-job ledger was committed as `ad3514a` (SHA-256
`b6dbb7738211e5a4ef11b217721fdb35acd68201beee3be6bbb728e34f4c7ff7`).
Prelaunch validation passed 124 focused tests with zero skips, exact environment
and baseline checks, parent-report integrity and the CLI dry-run; evidence is
`publication/validation/confirmatory_launch_v1/validation.json`. The Windows
supervisor launched at `2026-09-27T17:30:18Z`; the first final job was recorded
RUNNING under Linux controller PID 780. Live counts must always be read from the
state rather than this launch snapshot.

## Post-campaign evidence audit, 2026-09-30

Both frozen cohorts completed: 517 declared jobs, 518 preserved attempts,
including one parent cancellation before a posterior existed. The new cohort
contains 337 gate passes and 63 rejections; no extra attempts or seeds were
introduced. The parent contains 66 passes and 51 rejections across P2–P5.
Counts and scientific quantities are generated in
`reports/publication_synthesis/tcc_evidence_v1/summary.json`; do not treat the
combined job count as a calibration denominator across heterogeneous families.

The protected baseline's 26 checksum-bound artifacts remain unchanged. Protocol
and ledger commits predate both batches. Metrics were independently checked
against every registered P2 result/truth pair. Read
`docs/publication/CALIBRATION_REVIEW.md` and
`docs/publication/POST_CAMPAIGN_SCIENTIFIC_REVIEW.md` before promoting claims.
Approval by the historical gate is not a guarantee of parameter identification:
the near-limit regime has severe undercoverage despite many gate passes.

Runtime resource changes were authorized operationally and preserved four
chains and the scientific identity; the original protocol budget remains a
historical snapshot. See `docs/publication/CONFIRMATORY_RUNTIME_AUDIT.md`.
No historical run, gate threshold or final protocol was rewritten in this audit.
M6 remains deferred; positive external agreement and multi-target physical
validity are not established. P7 remains incomplete; no paper tag/DOI is issued.

## Runtime amendment details, 2026-09-27

The ongoing `tcc_campaign_v1` campaign encountered an operational checkpoint
replacement failure on Windows/WSL. This is not a scientific rejection. The
controller exited while its child sealed a valid completion manifest. The
repair preserves the original final ledger and all finished/rejected attempts;
it does not change seeds, models, priors, gates or replicate counts.

See `docs/publication/CHECKPOINT_RELIABILITY_AMENDMENT.md`, the separately
committed `publication/runtime_amendments/tcc_campaign_v1.json`, and the
engineering-only `checkpoint_repair_v1`/`checkpoint_repair_v2` validation bundles.
Operational acceptance does not establish calibration or promote scientific
claims. Current progress remains the live campaign state plus sealed manifests,
not a hand-maintained count in this document.

## External-audit closure and prospective numerical complement, 2026-09-30

The 517 historical jobs and 518 attempts remain frozen. The independent
`publication/validation/trace_audit_v1/` audit recomputed individual and
aggregate P2 summaries directly from all 480 posterior traces, keeping the
80-job parent and 400-job confirmatory cohorts separate. Its PASS status is
an arithmetic verification, not scientific approval of every posterior.
`publication/validation/residual_review_v2/` audits existing observed residuals
without attributing their cause to a GP. The versioned claim review and TCC
source set live in `reports/publication_synthesis/tcc_evidence_v2/`; this does
not replace the protected v1 synthesis.

The two `t0_coordinate_pilot_v1` fits were explicitly **PILOT** runs with only
40 tuning and 40 posterior draws per chain. Both were scientifically rejected
under the existing diagnostics. They are debugging/sizing evidence only, not
an efficacy result or part of the final P2 denominator.

`tcc_numerical_complement_v1` was **PLANNED, NOT EXECUTED**. Its committed
24-job ledger is
`configs/publication/tcc_numerical_complement_v1_plan.json` (commit
`180db76c6ef13ae2e7471220e7b102655efe5079`); the config is
`configs/publication/tcc_numerical_complement_v1.json`. A later audit-only
source edit changed its broad frozen source map. Its preflight correctly
blocked launch. Neither its ledger nor its seeds were modified, and there are
zero v1 final attempts.

The prospective replacement `tcc_numerical_complement_v2` was **PLANNED BUT
NOT EXECUTED** as of the frozen ledger commit `ead9a89`. Its three protocols
and config were committed first in `5bd3975`. The first supervisor launch
failed technically before creating a campaign state or any final attempt:
legacy P3 preflight expected an external environment key even though this is
a local-only refit against one historical external posterior. The error and
launch log identity are preserved in
`publication/validation/external_audit_closure_v1/numerical_v2_preflight_failure.json`.
The v2 ledger remains unchanged.

After a focused preflight repair and regression test (`4f6977a`), the new
`tcc_numerical_complement_v3` protocol/config was committed in `0a869b1`,
followed by the frozen 24-job seed/source ledger in `8febce3`, before any
final result. The scientific design matches v1/v2; the new campaign namespace
deterministically yields new seeds and isolated output paths. Explicit final
preflight passed with zero plan errors, matching hashes for the P3 historical
input and external completion manifest, and no unnecessary external interpreter
probe. After 353 local tests passed without skips and remote CI workflow
`36797666471` passed in both environments, the Windows supervisor launched
v3 at `2026-10-01T00:49:00Z`. The initial state was **RUNNING** on its first
P2 job, not yet a scientific result. Dynamic progress belongs to
`artifacts/publication_campaign/tcc_numerical_complement_v3/campaign_state.json`;
the static receipt is `publication/validation/external_audit_closure_v1/numerical_v3_launch.json`.
Twelve new synthetic
jobs pair direct/standardized coordinates across two regimes and three newly
seeded datasets each; three P3 jobs use one existing observational input and
one historical external posterior reference; nine P4 jobs evaluate declared
numerical ablations. All outputs, including rejections and failures, must be
retained. The soft budget is 20 hours. The 5.4-hour sizing estimate is not a
completion-time guarantee. No claim of numerical improvement is authorized
until this prospective study is run, audited and aggregated. Use the campaign
runner dry-run/status with the **v3** config before `--resume` after a stop;
do not start a second controller while the live state is RUNNING. Do not
restart historical campaigns or start v1/v2.
