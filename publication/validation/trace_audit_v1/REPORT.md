# Independent posterior trace audit

Status: PASS. No inference executed; historical artifacts unchanged.

Means, sample SD and ETI50/80/94 were reconstructed directly from every declared available trace, including rejected draws/chains.

| Cohort | P2 declared | P2 attempts | Numeric | Sampler pass | Joint pass | Rejected | Discrepancies |
|---|---:|---:|---:|---:|---:|---:|---:|
| tcc_campaign_v1 | 80 | 81 | 80 | 66 | 65 | 15 | 0 |
| tcc_calibration_confirmatory_v1 | 400 | 400 | 400 | 339 | 337 | 63 | 0 |

## Interpretation

- Fixed-truth repeated-sampling ETI coverage, not SBC or observational PPC.
- All-numeric metrics retain nonconverged/rejected MCMC outputs, which need not estimate exact posterior quantities reliably.
- Sampler/joint-gate conditioning is selection, not repair of unconditional coverage.
- Covered-and-joint-passed/all-declared is operational yield, not coverage.
- r and geometric depth r^2 coverage events are not independent confirmations.
- 95% Wilson limits are pointwise, not simultaneous across parameter/scenario/level comparisons.
- Unavailable diagnostics are null/unassessed, not numerical zero or a measured failure.
- This read-only audit verifies summaries/derived geometry, not the scientific adequacy of the forward model.

The JSON/CSV retain three separate estimands (all numeric, sampler-selected, joint-gate-selected), explicit denominators, unavailable values, bias/RMSE/widths, Wilson limits and operational yield. Cohorts are never pooled.

Reproduction: `python scripts/audit_publication_traces.py --output publication/validation/trace_audit_new_version`.
Byte freshness: `python scripts/audit_publication_traces.py --check --output publication/validation/trace_audit_v1`.
