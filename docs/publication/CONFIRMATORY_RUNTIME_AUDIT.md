# Confirmatory campaign runtime audit — 2026-09-30

This is a retrospective operational record. The prospective scientific
protocol and its original compute-planning statement remain unchanged in
`publication/protocols/PUB-02-confirmatory-v1.json`. The user subsequently
authorized resource changes, a safe pause and a lower-resource resume while
other applications remained active. These decisions did not depend on
coverage, bias, sampler diagnostics or acceptance rates.

The machine-readable authority is
`artifacts/publication_campaign/tcc_calibration_confirmatory_v1/campaign_state.json`,
whose hash-linked journal records:

| UTC | Event sequence | Workers | Cores per run | Soft budget |
|---|---:|---:|---:|---:|
| 2026-09-27 17:31:04 | initialization | 1 | 4 | 22 h |
| 2026-09-28 01:43:01 | 607, runtime_resource_change | 2 | 4 | 22 h |
| 2026-09-30 02:01:49 | 832, runtime_resource_change | 1 | 2 | 36 h |

The last change reduced simultaneous CPU demand for coexistence with the
user's other workloads. Increasing the soft dispatch budget allowed slower
completion of the same frozen remainder. It did not add replicates, replace
seeds, rerun scientific rejections or extend the campaign until a favorable
result appeared. The cap was changed with user authorization, not automatically.
`memory_limit_gb=null` is not a hard memory limit. WSL RAM allocation is separate
from this runner configuration.

An independent scan of all 400 `inference_config.json` files found four chains,
1,000 tuning steps and 1,000 posterior draws per chain in every run. The first
274 used four cores and the final 126 used two cores; core concurrency is not
chain count. The observed last-run configuration is
`artifacts/publication_campaign/tcc_calibration_confirmatory_v1/runs/PUB-02/near_limit_long/rep_0099/attempt_000/inference_config.json`.

The fixed scientific configuration identity remains
`440f5bca9b21051cb83550c13b1c2e7158da00aea75fc8ee2b38824fd34ab96e`.
The immutable ledger remains
`configs/publication/tcc_calibration_confirmatory_v1_plan.json`, SHA-256
`b6dbb7738211e5a4ef11b217721fdb35acd68201beee3be6bbb728e34f4c7ff7`.
Tests compare all job IDs, run IDs, payloads, protocols and seeds against this
ledger, while permitting independently recorded runtime resource limits.

The final checkpoint records completion at `2026-09-30T11:03:47.478315+00:00`
with `71734.74689026605` active seconds (approximately 19.93 h), 400 terminal
jobs, 337 `COMPLETED` and 63 `COMPLETED_REJECTED`. No extra attempts were
created in this campaign. Active controller time includes operational overhead;
it is neither CPU-hours nor uninterrupted wall-clock time from initial launch.
Execution completion does not establish scientific calibration or release readiness.

The initial code commit was `a2b8d8a02ed636fd3d821aa3a4c60207dc6733ed` for
one attempt; the remaining 399 record
`5b616201477251b7999f72fdfd1065a38f4a9fe1`. Their difference records the launch
in documentation. The scientific environment preflight reports Python 3.14.6
and all 19 directly pinned distributions matching the baseline requirements.
This is not a complete transitive/native-library attestation.

Later synthesis code is outside the frozen execution source map. Its addition
does not authorize restarting this old final cohort. Reproduction of scientific
inference requires the frozen execution revision and a distinct run namespace;
auditing already sealed evidence uses the read-only command:

```sh
python scripts/verify_publication_campaign.py --config configs/publication/tcc_calibration_confirmatory_v1.json
```

The existing campaign aggregates are preserved, including their bookkeeping
snapshot taken while the controller was `AGGREGATING`. Their scientific job
fingerprint is stable after final controller bookkeeping changes to `COMPLETED`.
