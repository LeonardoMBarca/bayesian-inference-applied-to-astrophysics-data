---
name: simulation-calibration-injection-recovery
description: Design, implement, validate, and summarize synthetic transit injection-recovery and posterior calibration experiments with known ground truth.
---

# Simulation Calibration and Injection-Recovery

Use this skill for P2 and any known-truth validation.

## Scientific objective

Measure whether the workflow recovers known parameters with calibrated posterior uncertainty across predeclared observational regimes.

## Anti-circularity

The simulator and inference may share validated physical primitives when scientifically necessary, but avoid making the test tautological.

- Keep generative configuration separate from inference configuration.
- Inference code must not read ground-truth artifacts.
- Where practical, validate the simulator against an independent light-curve implementation or analytic sanity checks.
- Include model-misspecification scenarios so success is not guaranteed by construction.

## Scenario protocol

Before final runs define:

- true transit parameters;
- cadence/exposure;
- segment structure;
- measurement-error distribution;
- white jitter;
- correlated/systematic perturbations if any;
- number of replicates;
- random-seed derivation;
- inference priors/model;
- success metrics and uncertainty.

Do not change the scenario grid after inspecting final aggregate results without a logged amendment.

## Required metrics

For designated scientific parameters report across all declared replicates:

- posterior-center bias;
- RMSE/MAE where useful;
- credible-interval empirical coverage at multiple nominal levels (at least 50%, 80%, 94%);
- confidence/credible uncertainty on empirical coverage itself;
- interval width/sharpness;
- standardized/rank calibration diagnostics where valid;
- sampler/PPC/scientific gate pass rates;
- failure counts and reasons.

Do not exclude failed runs from denominators unless the protocol declared that rule in advance; always report both attempted and successfully interpretable counts.

## Calibration interpretation

`94% observed coverage = 94%` is not by itself proof of perfect calibration. Account for finite-simulation uncertainty and evaluate patterns across parameters/scenarios.

Flag cases such as:

- good R-hat but poor coverage;
- narrow intervals with systematic bias;
- apparent calibration caused by excessively broad uncertainty;
- coverage degradation as SNR decreases;
- correlation-induced undercoverage under a white-noise likelihood.

These are scientifically valuable findings.

## Reproducibility

Each replicate must be derivable from stable identifiers and record:

- `scenario_id`;
- `replicate_id`;
- generative seed;
- inference seed;
- ground-truth checksum;
- simulated-data checksum;
- model/input checksum;
- run status/gates.

Aggregate reports must be generated from the registry, not manually selected paths.

## Testing

Add deterministic tests for:

- exact seed derivation;
- injected signal amplitude/depth;
- exposure integration semantics;
- segment offsets/noise semantics;
- separation between truth and inference config;
- aggregate denominators including failures;
- coverage calculations.

## Done

P2 is complete only when final repeated simulations exist under a frozen protocol, all declared replicates are accounted for, calibration uncertainty is quantified, and negative/misspecified scenarios are reported rather than discarded.