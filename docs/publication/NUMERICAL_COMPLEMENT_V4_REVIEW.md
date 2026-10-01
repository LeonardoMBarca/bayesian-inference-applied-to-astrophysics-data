# Corrected numerical complement v4: post-campaign review

Date: 2026-10-01. Campaign mode: `final`. Frozen source/ledger commit:
`96787f27b45aa019ceb9fe52c2b90971a2ebae1a`. This review interprets
machine-readable evidence; it does not modify or relabel any sealed run.

## Completion and integrity

The controller finished all 24 declared jobs in about 3 hours 20 minutes.
There were 24 preserved attempts, 10 `COMPLETED`, 14
`COMPLETED_REJECTED`, zero technical failures and zero pending jobs. The
supervisor exited with return code zero. The campaign's read-only `--verify`
command passed artifact-integrity validation, including its report hashes.
The final state is `COMPLETED`; generated report headers saying
`AGGREGATING` describe the state at the moment aggregation read its snapshot,
not a currently running process. The generated `REPORT.md` also retains a
generic smoke-campaign caveat despite this campaign's `final` mode. Its
substantive warning against automatic claim promotion remains appropriate,
but that label must not be interpreted as changing the campaign mode.

| Family | Declared | Accepted | Scientific rejection | Rejection mechanism |
|---|---:|---:|---:|---|
| PUB-02 synthetic coordinate comparison | 12 | 7 | 5 | Sampler diagnostics |
| PUB-03 observational benchmark refits | 3 | 0 | 3 | Temporal PPC, despite sampler pass |
| PUB-04 numerical ablations | 9 | 3 | 6 | Sampler diagnostics |
| **Total** | **24** | **10** | **14** | No technical failures |

These counts come from the sealed campaign
[`summary.json`](../../reports/publication_campaign/tcc_numerical_complement_v4/summary.json)
and [`campaign_state.json`](../../artifacts/publication_campaign/tcc_numerical_complement_v4/campaign_state.json),
not hand-selected runs. The full [`jobs.csv`](../../reports/publication_campaign/tcc_numerical_complement_v4/jobs.csv),
[`attempts.csv`](../../reports/publication_campaign/tcc_numerical_complement_v4/attempts.csv),
[`rejections.csv`](../../reports/publication_campaign/tcc_numerical_complement_v4/rejections.csv)
and family reports retain every declared replicate and rejection.

## Corrective check for the v3 predictive defect

The prior v3 incident is documented in
[`numerical_v3_predictive_incident.md`](../../publication/validation/external_audit_closure_v1/numerical_v3_predictive_incident.md).
The v4 runs use the corrected posterior variable selection and a separate
campaign identity. A read-only inspection of all 24 NetCDF posterior groups
found `t0_standardized` in all 18 standardized-coordinate traces and in none
of the six direct-coordinate traces. Across those 18 traces, the maximum
absolute stored difference between `t0` and
`t0_prior_sigma_days × t0_standardized` was zero at the stored numerical
precision. The focused regression tests and pre-run exact-environment suite
passed before v4 launch. This is evidence that the specific v3 PPC
conditioning mistake is absent from v4; it does **not** imply that PPC itself
passes or that the transit model is physically adequate.

## Scientific interpretation

PUB-02 contains three new, paired synthetic datasets per regime. All 12
provenance and PPC gates passed, but five posteriors failed sampler gates.
Accepted counts are four of six direct-coordinate and three of six
standardized-coordinate fits. This small prospective comparison supplies no
defensible claim that standardization improves sampler reliability, and its
three-per-regime coverage rates have very low precision. Rejected numeric
posteriors remain in the aggregate with separate gate-conditioned metrics;
they are not silently dropped or counted as accepted calibration evidence.

All three PUB-03 local standardized fits passed sampler diagnostics but
failed temporal PPC. They share the same Kepler-10 b observational input and
the same historical external juliet posterior. This is one benchmark
comparison with three local refits, not three independent external
validations. Posterior proximity, if present, cannot rescue either side's
predictive inadequacy. The finding directly demonstrates in this setting
that MCMC convergence is insufficient for scientific promotion. No claim of
external validation is authorized by these three rejected runs.

In PUB-04, all three high-accuracy integrated baselines passed. All three
standardized-baseline and all three exposure-off high-accuracy fits failed
sampler diagnostics, while their PPC gates passed. The exposure-off numeric
point shifts are preserved in the paired-effect tables, but none is a
both-sampler-pass contrast; interpret them as failure-case descriptions, not
validated effect-size estimates. The ablation does not justify changing gates
or choosing a favorable run.

The v3 partial campaign and its invalid standardized PPC remain historical
and excluded from v4 inference. The protected `scientific_003` baseline is
untouched. V4 does not supersede the 400-replicate P2 confirmatory campaign,
prove a new astrophysical result, establish M6, or make the repository
paper-release ready. Downstream TCC/manuscript claim synthesis should use
this study as a numerical-method and failure-transparency supplement, with
the narrow denominators and dependence stated explicitly.

## Audit and reproduction

Use the frozen config and manifest, without rerunning MCMC:

```sh
python scripts/run_publication_campaign.py --config configs/publication/tcc_numerical_complement_v4.json --status
python scripts/run_publication_campaign.py --config configs/publication/tcc_numerical_complement_v4.json --verify
```

The compact evidence is under
`artifacts/publication_campaign/tcc_numerical_complement_v4/` and
`reports/publication_campaign/tcc_numerical_complement_v4/`; run logs are
under `logs/publication_campaign/tcc_numerical_complement_v4/`. NetCDF traces
are excluded from ordinary Git and require checksum-bound archival for
third-party byte-for-byte restoration. Successful local verification is not
proof of public archival availability or independent MCMC reproduction.
