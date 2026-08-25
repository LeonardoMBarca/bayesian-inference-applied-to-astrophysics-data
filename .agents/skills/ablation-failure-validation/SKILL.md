---
name: ablation-failure-validation
description: Design controlled ablations and negative controls that quantify the value of preprocessing/modeling decisions and empirically validate interpretation gates.
---

# Ablation and Failure-Mode Validation

Use this skill for P4.

## Scientific objective

Demonstrate which decisions materially affect inference and whether validation gates reject scientifically invalid but superficially plausible runs.

## Experimental discipline

Prefer one-factor-at-a-time changes when feasible. If an ablation necessarily changes multiple assumptions, state that explicitly and do not attribute causality to one component.

Freeze the ablation list and primary metrics before final runs.

## Required controls

At minimum implement and document:

1. exposure-integrated vs instantaneous transit evaluation;
2. segment-normalized vs inappropriate global normalization/declared alternative;
3. inferred white jitter vs no extra jitter;
4. baseline priors vs deliberately pathological/over-informative prior controls;
5. invalid provenance/dataset identity that must fail before inference or interpretation;
6. deliberately inadequate sampling that must fail sampler diagnostics;
7. a case where sampler diagnostics pass but PPC/scientific adequacy fails.

## Required measurements

For scientific parameters report:

- posterior-center shifts;
- uncertainty-width changes;
- standardized shifts relative to baseline uncertainty;
- residual/PPC changes;
- sampler changes;
- gate outcomes;
- computational-cost changes where material.

## Gate-validation matrix

Generate a machine-readable and human-readable matrix with separate columns for:

- data/provenance validity;
- sampler convergence;
- posterior-predictive adequacy;
- scientific plausibility/scale;
- final interpretability.

The matrix must include at least one empirical example showing that sampler convergence alone does not imply scientific interpretability.

## Negative controls

A negative control is successful when it demonstrates the intended failure mode, not when it passes the model. Do not weaken gates to make controls look cleaner.

## Interpretation

Do not conclude that an engineering feature is scientifically necessary solely because it exists. The ablation must quantify whether removing/changing it materially alters the scientific result or validity contract.

## Testing

Add tests ensuring:

- ablation configs change only intended fields where feasible;
- baseline and ablation share the declared input when required;
- invalid provenance is rejected deterministically;
- gate matrices are derived from run artifacts, not manual labels;
- failed controls remain in aggregate reports.

## Done

P4 is complete when the repository contains predeclared ablations, quantitative effect sizes, negative controls, and an auditable demonstration that its evidence-promotion gates block meaningful invalid cases.