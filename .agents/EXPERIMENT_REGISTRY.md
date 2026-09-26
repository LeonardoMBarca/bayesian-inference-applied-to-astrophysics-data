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
| PUB-02 | injection–recovery calibration | Does the workflow recover known truths with calibrated uncertainty? | `publication/protocols/PUB-02-pilot.json` (pilot only; final protocol pending) | PILOT | Physical simulator and full-denominator metrics tested; pilot failures preserved; no final calibration claim |
| PUB-03 | independent benchmark | Does an independent published implementation obtain compatible inference? | to create | PLANNED | — |
| PUB-04 | ablations/failure gates | Which design choices matter and do gates reject invalid cases? | to create | PLANNED | — |
| PUB-05 | multi-target validation | Across which real observational regimes does the workflow succeed/fail? | to create | PLANNED | — |
| PUB-06 | correlated-noise M6 | When temporal correlation exists, does explicit covariance improve calibration? | to create | PLANNED | — |
| PUB-07 | paper reproducibility release | Can every publication-critical artifact be traced and regenerated? | to create | PLANNED | — |
| PUB-08 | TCC/paper synthesis | Do final written claims match the validated experiment registry? | to create | PLANNED | — |

## Required fields for every final experiment protocol

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
