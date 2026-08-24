---
name: bayesian-scientific-validation
description: Review or fix Bayesian models, priors, likelihoods, NUTS/MCMC diagnostics, posterior predictive checks, physical-transit consistency, prior sensitivity, noise experiments, Gaussian-process/correlated noise, derived parameters, and model comparison in this repository.
---

# Bayesian Scientific Validation

The goal is scientifically defensible inference, not merely successful sampling.

## Three separate questions

For every fitted run answer separately:

1. **Did the sampler behave well?** R-hat, ESS, divergences, BFMI, geometry.
2. **Does the fitted model reproduce relevant observed behavior?** Posterior predictive checks, residual structure, coverage/calibration where meaningful.
3. **Is the run scientifically interpretable?** Data preparation, units, target identity, priors, likelihood, physical assumptions, cadence integration, and provenance all need to be valid.

Never collapse these into one boolean without preserving the three components.

## M5 consistency

- The actual forward model, target config, generated `model_config.json`, report text, tables, and derived parameters must agree.
- Remove cross-target literals and copy/paste assumptions.
- Derived durations and other physical quantities must use the same target period and geometry used by the model.
- Record limb-darkening parameterization and constraints explicitly.
- If long-cadence data are modeled, use exposure integration/supersampling when material.

## Priors

For each scientifically important prior:

- document parameterization and units;
- justify the scale/domain;
- inspect prior predictive behavior when meaningful;
- distinguish weakly informative, informative, and deliberately pathological negative-control priors;
- do not infer robustness from an extreme prior that simply dominates the posterior.

## Sensitivity analysis

A real sensitivity study should compare multiple plausible prior choices and report:

- prior predictive implications;
- posterior shifts in scientific parameters;
- changes in uncertainty;
- sampler diagnostics;
- posterior predictive performance;
- conclusions about which parameters are data-informed vs prior-sensitive.

Keep deliberately absurd priors only as clearly labeled failure/negative-control experiments.

## Noise modeling

Distinguish:

- measurement uncertainty supplied by the data;
- independent additional jitter;
- deterministic systematics/trends;
- stochastic time-correlated noise.

Do not call independent `extra_sigma` a correlated-noise model.

If correlated noise is modeled, define a covariance/kernel/process explicitly, justify it, document priors, and validate on synthetic/injection-recovery cases. A GP/celerite2-style model is appropriate only when its assumptions and computational benefits fit the data.

## Scale sanity checks

Create explicit diagnostics such as:

- `extra_sigma / median(measurement_sigma)`;
- posterior depth vs observed transit-scale contrast;
- posterior duration vs phase-window support;
- impact parameter/radius-ratio geometry validity;
- physically constrained parameter domains;
- posterior mass near boundaries.

Large mismatches should trigger review, not automatic acceptance.

## Posterior predictive checks

Do more than global interval coverage. Where useful inspect:

- transit shape around ingress/egress;
- out-of-transit residuals;
- residual autocorrelation;
- segment/quarter residual structure;
- residual distribution and standardized scale;
- model behavior under held-out or synthetic data.

## Model comparison

- Store pointwise log likelihood when appropriate.
- Use LOO/WAIC/ELPD only when the observation target/likelihood and comparison assumptions make sense.
- Diagnose Pareto-k or other reliability indicators when using PSIS-LOO.
- Keep RMSE and other predictive summaries separate from formal Bayesian information criteria.
- Keep manually defined domain/physical scores explicitly labeled heuristic.
- Do not rank M5 as a valid scientific model until preprocessing/provenance gates pass.

## Interpretation gate

A recommended physical result should require, at minimum:

- correct target/provenance;
- valid preprocessing and units;
- acceptable sampler diagnostics;
- no unresolved pathological parameter scales;
- posterior predictive behavior adequate for the stated purpose;
- assumptions documented;
- no known implementation/config/report mismatch.

Failed runs should remain traceable and explicitly labeled as failed, exploratory, or negative controls.
