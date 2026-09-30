# Publication campaign: tcc_campaign_v1

Smoke campaign is infrastructure evidence only. Missing, blocked, failed and rejected jobs remain visible. Numeric metrics are descriptive until complete frozen-protocol scientific evidence, sampler/PPC checks and independent review support stronger claims. No M6 or paper-ready claim is inferred from implementation.

Mode: final; family: PUB-04; controller state: AGGREGATING.
Declared jobs: 30. Preserved attempts: 30. Scientifically interpretable: 1.
Computational gate passes (includes explicitly labeled smoke fixtures, not science): 1.
Statuses: `{"COMPLETED": 1, "COMPLETED_REJECTED": 29}`.
Complete declared batch (including terminal failures): True. All scientific jobs finished: True.

## Evidence and negative outcomes

`jobs.csv` includes every planned job, including not started. `attempts.csv` retains every earlier interrupted/failed attempt. Only the last registered, sealed and hash-verified attempt supplies numerical evidence; no best-run selection. `failures.csv` and `rejections.csv` separate technical/integrity failures from scientific rejection.

Synthetic metrics include 50/80/94% equal-tailed coverage and Wilson intervals, bias, absolute/relative bias, RMSE, SD and interval widths. Rejected numeric posteriors remain, with conditional sampler metrics separated. Operational covered-and-passed fraction is not an interval-calibration estimand. Missing intervals are not measured noncoverage. Fixed-truth repeated coverage is not SBC.

## Family artifacts

- `PUB-04/`: machine-readable results/tables and available figures; absent evidence remains unavailable, not zero.

| Scenario | Declared | Numeric r | r bias | r RMSE | r 94% numeric coverage |
|---|---:|---:|---:|---:|---:|
| long_segment_offsets__baseline | 3 | 3 | -0.000466664 | 0.00226368 | 1 |
| long_segment_offsets__exposure_off | 3 | 3 | 0.0170908 | 0.0244333 | 0.666667 |
| long_segment_offsets__global_normalization | 3 | 3 | -0.0237077 | 0.0237276 | 1 |
| long_segment_offsets__no_jitter | 3 | 3 | 0.00648342 | 0.0091789 | 0.666667 |
| long_segment_offsets__strong_wrong_radius_prior | 3 | 3 | -0.0447923 | 0.0447923 | 0 |
| long_segment_offsets__invalid_input_hash | 3 | 0 | unavailable | unavailable | unavailable |
| long_segment_offsets__dataset_identity_mismatch | 3 | 0 | unavailable | unavailable | unavailable |
| long_segment_offsets__insufficient_sampling | 3 | 3 | 0.0126423 | 0.0288153 | 0.666667 |
| short_temporal_systematic__baseline | 3 | 3 | -0.000972692 | 0.0010315 | 1 |
| short_temporal_systematic__deterministic_sine | 3 | 3 | -0.000245444 | 0.000308157 | 1 |


## Validation issues

No detected artifact-integrity or preflight errors. This is not proof of scientific validity.

## Regeneration

```sh
python scripts/aggregate_publication_campaign.py --config configs/publication/tcc_final_campaign.json --family PUB-04
```

This command only reads sealed scientific artifacts and regenerates derived reports; it never samples. Live controller bookkeeping is not a scientific input: the read snapshot is preserved, and freshness checks use the jobs-only fingerprint plus artifact hashes.
