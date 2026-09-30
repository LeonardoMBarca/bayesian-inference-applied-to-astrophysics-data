# Publication campaign: tcc_calibration_confirmatory_v1

Smoke campaign is infrastructure evidence only. Missing, blocked, failed and rejected jobs remain visible. Numeric metrics are descriptive until complete frozen-protocol scientific evidence, sampler/PPC checks and independent review support stronger claims. No M6 or paper-ready claim is inferred from implementation.

Mode: final; family: PUB-02; controller state: AGGREGATING.
Declared jobs: 400. Preserved attempts: 400. Scientifically interpretable: 337.
Computational gate passes (includes explicitly labeled smoke fixtures, not science): 337.
Statuses: `{"COMPLETED": 337, "COMPLETED_REJECTED": 63}`.
Complete declared batch (including terminal failures): True. All scientific jobs finished: True.

## Evidence and negative outcomes

`jobs.csv` includes every planned job, including not started. `attempts.csv` retains every earlier interrupted/failed attempt. Only the last registered, sealed and hash-verified attempt supplies numerical evidence; no best-run selection. `failures.csv` and `rejections.csv` separate technical/integrity failures from scientific rejection.

Synthetic metrics include 50/80/94% equal-tailed coverage and Wilson intervals, bias, absolute/relative bias, RMSE, SD and interval widths. Rejected numeric posteriors remain, with conditional sampler metrics separated. Operational covered-and-passed fraction is not an interval-calibration estimand. Missing intervals are not measured noncoverage. Fixed-truth repeated coverage is not SBC.

## Family artifacts

- `PUB-02/`: machine-readable results/tables and available figures; absent evidence remains unavailable, not zero.

| Scenario | Declared | Numeric r | r bias | r RMSE | r 94% numeric coverage |
|---|---:|---:|---:|---:|---:|
| deep_short | 100 | 100 | -0.000250703 | 0.00105578 | 1 |
| intermediate_long | 100 | 100 | 0.00286056 | 0.00638198 | 0.98 |
| shallow_short | 100 | 100 | -9.46365e-05 | 0.000620796 | 1 |
| near_limit_long | 100 | 100 | 0.0139836 | 0.0144081 | 0.98 |


## Validation issues

No detected artifact-integrity or preflight errors. This is not proof of scientific validity.

## Regeneration

```sh
python scripts/aggregate_publication_campaign.py --config configs/publication/tcc_calibration_confirmatory_v1.json --family PUB-02
```

This command only reads sealed scientific artifacts and regenerates derived reports; it never samples. Live controller bookkeeping is not a scientific input: the read snapshot is preserved, and freshness checks use the jobs-only fingerprint plus artifact hashes.
