# Master Codex Task — Make the Repository Scientifically Production-Grade

Use the repository skill `$repository-hardening` and treat `AGENTS.md` plus `.agents/REMEDIATION_PLAN.md` as mandatory instructions.

## Objective

Bring this repository to a state where it reliably fulfills its stated scientific and engineering goals end to end with minimal manual intervention:

- traceable RAW ingestion;
- semantically correct Silver transformations;
- modeling-ready Gold preparation;
- scientifically defensible Bayesian inference;
- correct target-specific physical modeling;
- honest sensitivity/noise experiments;
- reproducible environments and clean rebuilds;
- automated regression protection;
- synchronized machine-readable and human-readable artifacts;
- documentation suitable for academic scrutiny.

Do not optimize for the smallest diff. Optimize for correctness, maintainability, reproducibility, and scientific defensibility while avoiding unnecessary architectural complexity.

## Required workflow

1. Read `AGENTS.md` completely.
2. Read `.agents/REMEDIATION_PLAN.md` completely.
3. Inspect the current repository state and verify each listed finding before changing code. If a finding has already been fixed, prove it and update its status.
4. Produce a dependency-aware execution plan. P0 scientific/provenance problems come before refactors, cosmetic cleanup, or new features.
5. Work through remediation items in coherent batches. Do not mark an item `DONE` until its acceptance criteria are demonstrated.
6. Add regression tests as bugs are fixed.
7. Prefer shared/config-driven implementations over planet-specific copy/paste.
8. Rebuild affected artifacts after behavior changes and inspect machine-readable outputs.
9. Keep documentation synchronized in the same change that alters scientific behavior.
10. Update `.agents/REMEDIATION_PLAN.md` continuously with status and concise evidence.

## Critical expectations

### M5 and targets

Create one authoritative target configuration and make the physical transit workflow target-safe. HAT-P-7 b and Kepler-10 b must not contaminate one another's periods, paths, filenames, reports, configs, figures, tables, or derived parameters.

### Kepler-10 b preprocessing

Do not interpret Kepler-10 b physically until segment/quarter offsets and cadence/exposure issues are handled correctly. Preserve segment identity through the stage where segment-level normalization/detrending is performed. Re-evaluate product cadence selection and implement exposure integration/supersampling when scientifically necessary.

### Scientific validation

Treat sampler convergence, posterior predictive adequacy, and physical interpretability as different concepts. Add explicit interpretation gates. Pathological jitter, failed R-hat/ESS/divergence diagnostics, bad preprocessing, or provenance mismatches must prevent a run from being recommended as a scientific result.

### Sensitivity and noise experiments

Reinterpret the existing extreme-prior sensitivity run honestly if it demonstrates prior domination/non-convergence. Build a real prior-sensitivity study with justified priors and prior-predictive checks. Do not claim correlated/red-noise modeling unless the inference actually represents covariance/correlation; use a justified GP/celerite2-style model if that claim is retained.

### Model comparison

Add pointwise log likelihood where appropriate and use LOO/WAIC/ELPD only when models are statistically comparable. Keep simple predictive metrics and heuristic structural scores explicitly separate from formal Bayesian model-comparison criteria.

### Reproducibility

A clean checkout must not rely on stale historical files. Introduce explicit run/dataset isolation where needed, normalize persisted paths across platforms, lock the validated environment, and add a practical test/CI suite.

## Do not do these things

- Do not tune posterior results merely to match NASA/catalog/literature values.
- Do not hide failed runs by deleting them; preserve them as failed/negative-control artifacts when useful.
- Do not call a run scientifically valid only because NUTS converged.
- Do not replace a working simple architecture with a large framework without a concrete requirement.
- Do not duplicate an entire model script just to change the target.
- Do not update docs separately from the code behavior they describe.
- Do not preserve incorrect behavior solely for backward compatibility unless historical reproducibility requires an explicitly versioned legacy path.

## Deliverables

At completion, provide:

1. All code/configuration fixes.
2. Regression tests for fixed P0/P1 defects where feasible.
3. CI configuration for the practical test suite.
4. Reproducible environment/lock specification.
5. Clean rebuild workflow with run/dataset identity.
6. Regenerated and synchronized machine-readable configs, reports, tables, and relevant figures/notebooks.
7. Updated README/docs describing the actual current pipeline.
8. Updated `.agents/REMEDIATION_PLAN.md` with all statuses and evidence.
9. A final hardening report containing:
   - files/components changed;
   - commands executed;
   - tests run and results;
   - scientific diagnostics before/after where relevant;
   - which runs are scientifically interpretable;
   - which runs are retained only as failures/negative controls;
   - remaining accepted limitations.

## Completion standard

Do not stop at “the code runs.” Stop when the repository can defend its own claims with reproducible evidence.
