# Publication campaign: tcc_numerical_complement_v3

Smoke campaign is infrastructure evidence only. Missing, blocked, failed and rejected jobs remain visible. Numeric metrics are descriptive until complete frozen-protocol scientific evidence, sampler/PPC checks and independent review support stronger claims. No M6 or paper-ready claim is inferred from implementation.

Mode: final; family: PUB-04; controller state: AGGREGATING.
Declared jobs: 9. Preserved attempts: 0. Scientifically interpretable: 0.
Computational gate passes (includes explicitly labeled smoke fixtures, not science): 0.
Statuses: `{"PLANNED": 9}`.
Complete declared batch (including terminal failures): False. All scientific jobs finished: False.

## Evidence and negative outcomes

`jobs.csv` includes every planned job, including not started. `attempts.csv` retains every earlier interrupted/failed attempt. Only the last registered, sealed and hash-verified attempt supplies numerical evidence; no best-run selection. `failures.csv` and `rejections.csv` separate technical/integrity failures from scientific rejection.

Synthetic metrics include 50/80/94% equal-tailed coverage and Wilson intervals, bias, absolute/relative bias, RMSE, SD and interval widths. Rejected numeric posteriors remain, with conditional sampler metrics separated. Operational covered-and-passed fraction is not an interval-calibration estimand. Missing intervals are not measured noncoverage. Fixed-truth repeated coverage is not SBC.

## Family artifacts

- `PUB-04/`: machine-readable results/tables and available figures; absent evidence remains unavailable, not zero.

## Validation issues

No detected artifact-integrity or preflight errors. This is not proof of scientific validity.

## Regeneration

```sh
python scripts/aggregate_publication_campaign.py --config configs/publication/tcc_numerical_complement_v3.json --family PUB-04
```

This command only reads sealed scientific artifacts and regenerates derived reports; it never samples. Live controller bookkeeping is not a scientific input: the read snapshot is preserved, and freshness checks use the jobs-only fingerprint plus artifact hashes.
