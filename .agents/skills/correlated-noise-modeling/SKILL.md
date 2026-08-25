---
name: correlated-noise-modeling
description: Design and validate a separate correlated-noise transit model (M6) using explicit temporal covariance/GP semantics, with synthetic controls before observational claims.
---

# Correlated-Noise Modeling

Use this skill for P6.

## Scientific objective

Determine whether explicitly modeling temporal correlation improves calibration and predictive adequacy when correlation is truly present, while avoiding unnecessary flexibility when white-noise M5 is adequate.

## Model versioning

Do not silently retrofit correlated noise into M5. M5 remains the exposure-integrated physical transit model with heteroscedastic measurement error plus independent white jitter.

Create a distinct M6 family/version with explicit covariance/process semantics.

Conceptually:

`y ~ MVN(mu_transit(theta), K_phi + Sigma_measurement + Sigma_white_jitter)`

where `K_phi` is a declared temporal covariance/process.

## Kernel/process selection

Evaluate an appropriate GP/celerite-style implementation. Choose the process based on scientific assumptions, identifiability and computational characteristics, not because one kernel gives the desired final posterior.

Document:

- covariance/process equation;
- hyperparameters and units;
- priors;
- stationarity assumptions;
- segment-boundary treatment;
- computational approximation if any;
- interaction with transit signal timescale.

## Validation sequence

Do not apply M6 to real data first.

1. deterministic/unit validation of covariance construction;
2. synthetic white-noise control;
3. synthetic correlated-noise injection with known truth;
4. repeated injection-recovery comparison M5 vs M6;
5. residual/PPC/autocorrelation assessment;
6. observational application only after synthetic evidence is acceptable.

## Signal absorption risk

Explicitly test whether M6 absorbs transit structure or inflates uncertainty unnecessarily. Include controls where no temporal correlation is present.

## Comparison rules

Primary evidence should come from known-truth recovery/calibration. LOO/WAIC may be secondary only when models are legitimately comparable and PSIS/other diagnostics are reliable.

Never rank models from unreliable LOO diagnostics.

## Required outputs

- process/kernel specification;
- synthetic calibration comparison M5 vs M6;
- residual ACF or other temporal diagnostics;
- posterior parameter shifts;
- interval calibration/sharpness;
- computational-cost comparison;
- cases where simpler M5 is preferred/sufficient;
- cases where M6 is necessary or still inadequate.

## Done

P6 is complete only when M6's correlated likelihood is explicit, validated on known-truth synthetic data, compared against white-noise controls, and observational claims remain restricted to the behavior demonstrated by those tests.