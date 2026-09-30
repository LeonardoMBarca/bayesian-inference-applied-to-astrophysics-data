# PUB-05: tcc_campaign_v1

Five purposively selected systems: descriptive method-scope evidence only, no population rate, no empirical coverage without known truth, no independent catalog validation.

All selected targets: 5. Complete declared batch: True.
Statuses: `{"rejected": 5}`.
Joint scientific passes: 0 / 5 (descriptive denominator; missing is not measured rejection).

| Target | Status | Provenance | Sampler | PPC | Joint scientific | Failure stage |
|---|---|---|---|---|---|---|
| HAT-P-7 b | rejected | True | True | False | False |  |
| Kepler-10 b | rejected | True | True | False | False |  |
| TrES-2 b | rejected | True | True | False | False |  |
| HD 189733 b | rejected | True | True | False | False |  |
| Kepler-4 b | rejected | True | False | False | False |  |

`targets.csv` preserves every selected system; `posterior_intervals.csv` preserves numeric summaries, including rejected fits. Equal-tailed intervals are not coverage measurements for these unknown-truth observations.

`posterior_intervals.png` shows all available 94% intervals. Red denotes an unpromotable result, not a reliable physical estimate. Missing intervals are explicitly marked. `gate_outcomes.png` separates unavailable diagnostics from observed rejections. `regime_precision.png` compares the posterior interval width with exposure, without treating precision as accuracy or detection SNR.

## Limits

PDCSAP and catalog ephemerides/durations condition these results. Catalog agreement is contextual rather than independent validation. The model is circular and white-jitter only; stellar activity, fixed-period drift and normalization error are not explicit covariance models. Segment median uncertainty is not propagated. Phase thinning weakens short-time residual checks. Geometric depth r squared differs from limb-darkened observed depth. No LOO/WAIC ranking or population-level claim is made.

Source checksums and output freshness: `artifact_manifest.json`. Final scientific conclusions require the full campaign's provenance and release validation, not just this generated report.
