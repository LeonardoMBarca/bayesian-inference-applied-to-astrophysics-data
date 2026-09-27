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
| PUB-02 | injection–recovery calibration | Does the workflow recover known truths with calibrated uncertainty? | `publication/protocols/PUB-02.json` | PLANNED | 80 declared final replicates; pilots preserved separately; no final coverage evidence yet |
| PUB-03 | independent benchmark | Does an independent published implementation obtain compatible inference? | `publication/protocols/PUB-03.json` | PLANNED | juliet adapter numerically and reproducibly tested; two final fits not executed |
| PUB-04 | ablations/failure gates | Which design choices matter and do gates reject invalid cases? | `publication/protocols/PUB-04.json` | PLANNED | 30 declared attempts, including six identity-negative controls; no final paired effects yet |
| PUB-05 | multi-target validation | Across which real observational regimes does the workflow succeed/fail? | `publication/protocols/PUB-05.json` | PLANNED | Five targets preselected; all 15 RAW inputs available and hashed; final inference pending |
| PUB-06 | correlated-noise M6 | When temporal correlation exists, does explicit covariance improve calibration? | `docs/publication/COMPUTE_BUDGET_AMENDMENT.md` | PLANNED (deferred) | Disabled in TCC campaign by user compute/deadline priority; no GP claim |
| PUB-07 | paper reproducibility release | Can every publication-critical artifact be traced and regenerated? | to create | PLANNED | — |
| PUB-08 | TCC/paper synthesis | Do final written claims match the validated experiment registry? | to create | PLANNED | — |

## Required fields for every final experiment protocol

`PUB-01 COMPLETED` refers only to the scoped literature snapshot, not proof of
novelty. Protocol candidates PUB-02–05 are frozen before the user-launched batch;
the runner requires their exact committed bytes and the tested-source ledger.
No pilot or infrastructure fixture is final scientific evidence.

## Autonomous TCC campaign handoff

The latest user instruction explicitly defers execution of the large final
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

## Runtime amendment, 2026-09-27

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
