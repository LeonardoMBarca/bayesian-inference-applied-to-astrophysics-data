# Publication campaign: runner_smoke_v2

Smoke campaign is infrastructure evidence only. Missing, blocked, failed and rejected jobs remain visible. Numeric metrics are descriptive until complete frozen-protocol scientific evidence, sampler/PPC checks and independent review support stronger claims. No M6 or paper-ready claim is inferred from implementation.

Mode: smoke; family: all; controller state: COMPLETED.
Declared jobs: 5. Preserved attempts: 6. Scientifically interpretable: 0.
Computational gate passes (includes explicitly labeled smoke fixtures, not science): 3.
Statuses: `{"COMPLETED": 3, "COMPLETED_REJECTED": 2}`.
Complete declared batch (including terminal failures): True. All scientific jobs finished: True.

## Evidence and negative outcomes

`jobs.csv` includes every planned job, including not started. `attempts.csv` retains every earlier interrupted/failed attempt. Only the last registered, sealed and hash-verified attempt supplies numerical evidence; no best-run selection. `failures.csv` and `rejections.csv` separate technical/integrity failures from scientific rejection.

Synthetic metrics include 50/80/94% equal-tailed coverage and Wilson intervals, bias, absolute/relative bias, RMSE, SD and interval widths. Rejected numeric posteriors remain, with conditional sampler metrics separated. Operational covered-and-passed fraction is not an interval-calibration estimand. Missing intervals are not measured noncoverage. Fixed-truth repeated coverage is not SBC.

## Family artifacts

- `PUB-02/`: machine-readable results/tables and available figures; absent evidence remains unavailable, not zero.

| Scenario | Declared | Numeric r | r bias | r RMSE | r 94% numeric coverage |
|---|---:|---:|---:|---:|---:|
| completed_fixture | 1 | 0 | unavailable | unavailable | unavailable |
| delay_checkpoint | 1 | 0 | unavailable | unavailable | unavailable |
| retry_technical | 1 | 0 | unavailable | unavailable | unavailable |
| scientific_rejection | 1 | 0 | unavailable | unavailable | unavailable |
| tiny_physical | 1 | 1 | -0.0213033 | 0.0213033 | 1 |


## Validation issues

No detected artifact-integrity or preflight errors. This is not proof of scientific validity.

## Regeneration

```sh
python scripts/aggregate_publication_campaign.py --config configs/publication/runner_smoke_v2.json
```

This command only reads sealed scientific artifacts and regenerates derived reports; it never samples. Live controller bookkeeping is not a scientific input: the read snapshot is preserved, and freshness checks use the jobs-only fingerprint plus artifact hashes.
