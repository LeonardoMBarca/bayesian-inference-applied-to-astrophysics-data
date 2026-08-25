---
name: independent-benchmark-validation
description: Compare the repository's Bayesian transit inference with an independent published implementation under a documented comparability contract.
---

# Independent Benchmark Validation

Use this skill for P3.

## Scientific objective

Determine whether an independent exoplanet-inference implementation reaches compatible or meaningfully different posterior conclusions on the same statistical prediction task.

## Tool-selection rule

Evaluate at least `juliet` and `allesfitter` for current compatibility, maintainability, model support and reproducibility. Select the primary benchmark before comparing final outputs. Never choose the tool because it gives the closest answer.

Record:

- publication/citation;
- exact software version/commit;
- installation environment;
- supported transit/noise/limb-darkening features;
- incompatibilities with the repository's M5 assumptions.

## Environment isolation

Do not add benchmark-only packages to the canonical validated M5 environment unless scientifically necessary. Prefer a separate locked benchmark environment and record its identity.

## Comparability contract

Before final benchmark runs freeze a table covering:

- exact observational rows/dataset hash;
- flux/error units;
- period and eccentricity;
- transit-time convention;
- radius-ratio parameterization;
- impact parameter and `a/Rs` conventions;
- limb-darkening law and priors;
- exposure integration;
- jitter/noise model;
- prior support/scale;
- likelihood family;
- sampler/evidence method.

Classify each item as `matched`, `approximately matched`, or `not matchable`, with rationale.

## Comparison metrics

Do not compare only posterior means. Include:

- posterior center difference standardized by combined uncertainty;
- credible-interval overlap;
- posterior width ratios;
- parameter correlations where important;
- predictive residual/PPC behavior;
- derived depth and duration using consistent definitions.

If chains/samples from the external tool are available, use distribution-aware comparisons. Do not pretend independent methods should be numerically identical.

## Failure interpretation

Disagreement is not automatically a defect in this repository. Investigate, in order:

1. input mismatch;
2. parameter-definition mismatch;
3. prior mismatch;
4. exposure/limb-darkening mismatch;
5. likelihood/noise mismatch;
6. sampler/pathology;
7. genuine implementation or modeling discrepancy.

Preserve unresolved disagreement as a publication result/limitation.

## Testing

Validate adapters for:

- unit conversion;
- time/phase convention;
- parameter-name conversion;
- derived-quantity definitions;
- exact dataset/input identity;
- benchmark artifact parsing.

## Done

P3 is complete when at least one independent published implementation has been run in a locked environment under a precommitted comparability contract and the final report explains both agreements and remaining differences without benchmark-specific tuning.