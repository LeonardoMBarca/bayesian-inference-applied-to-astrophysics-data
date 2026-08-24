# AGENTS.md

## Mission

This repository is scientific software. Treat correctness, reproducibility, provenance, explicit assumptions, and honest uncertainty as first-class requirements.

The goal is not merely to make the code run. The goal is to make the repository fulfill what it claims to do: ingest traceable public astrophysical data, transform it through RAW/Silver/Gold layers without losing required provenance, fit Bayesian models that match their documentation, validate those models scientifically and computationally, and produce artifacts that can be defended in an academic TCC.

When working in this repository, prefer a smaller scientifically correct implementation over a more sophisticated but weakly validated one.

## Required starting context

Before substantial work:

1. Read `.agents/REMEDIATION_PLAN.md`.
2. Read the relevant skill(s) under `.agents/skills/`.
3. Inspect the current code and generated artifacts before assuming documentation is current.
4. Treat the current executable implementation, current configuration, manifests, and generated metrics as evidence to reconcile; do not blindly trust any single README or historical context export.
5. If an audit finding in `.agents/REMEDIATION_PLAN.md` is stale because the code has already been fixed, verify the fix with tests/evidence and update the plan rather than reimplementing it.

## Source-of-truth hierarchy

When sources disagree, reconcile them explicitly. As a default hierarchy:

1. Current executable code and configuration.
2. Current raw inputs and machine-readable manifests/checksums.
3. Current generated model configuration, summaries, diagnostics, and traces.
4. Tests and reproducible validation scripts.
5. Human-readable reports and notebooks.
6. Historical documentation/context exports.

This hierarchy is not permission to keep documentation stale. The end state must make all layers agree.

## Non-negotiable scientific invariants

### RAW

- RAW data is immutable source evidence. Do not silently normalize, clean, rewrite, or replace original downloaded content.
- Every RAW artifact used downstream must have reproducible provenance: source, retrieval context where available, path, checksum, and status.
- Distinguish an event/history log from a manifest of current state when necessary.

### Silver

- Silver may standardize schemas and types, but must preserve enough provenance to trace every derived row to its RAW origin.
- Units must be explicit in schema/column names or machine-readable metadata. Never rely on ambiguous names such as `transit_depth` when percent vs fraction matters.
- Do not silently convert scientific units without documenting the transformation and testing it.

### Gold

- Gold may prepare data for modeling, but must not discard identifiers needed for scientifically necessary preprocessing.
- Preserve segment identity (`quarter`, campaign/sector when applicable, source FITS/product identity, cadence/exposure metadata) until segment-level normalization/detrending and validation are complete.
- Do not concatenate heterogeneous light-curve segments and then treat offsets between segments as astrophysical noise.
- Any normalization/detrending must be explicit, reproducible, parameterized, and recorded in artifacts.

### Bayesian modeling

- MCMC convergence is not equivalent to physical validity.
- A model is interpretable only if the data preparation, likelihood, priors, parameterization, units, and generated documentation all describe the same model.
- Do not label a model as handling correlated/red noise if the likelihood only adds independent white jitter.
- Do not call a sensitivity experiment robust when diagnostics fail or a deliberately bad prior dominates the posterior.
- Record R-hat, ESS, divergences, BFMI where applicable, posterior predictive diagnostics, and relevant scale checks.
- Add log-likelihood to inference data when model comparison requires LOO/WAIC and the models are legitimately comparable.
- Literature/catalog values may be used for validation and prior justification, but do not tune outputs merely to match a reference value.

### Target/configuration integrity

- Planet/star/mission-specific values must come from one authoritative target configuration, not scattered hard-coded literals.
- Generic modeling code must not contain stale names, periods, paths, or report filenames for a different target.
- A derived parameter must use the same target parameters as the model that generated the posterior.
- Target-specific outputs must be target-specific and run-specific. Never overwrite HAT-P-7 b artifacts while executing Kepler-10 b.

### Cadence and exposure integration

- For short transits, assess whether exposure-time integration materially changes the transit model.
- Prefer scientifically appropriate cadence during product selection. If long cadence is used, integrate/supersample the forward model when required rather than pretending samples are instantaneous.

## Reproducibility rules

- A clean checkout must be able to reproduce the documented current pipeline without relying on stale files from earlier configurations.
- Generated state from older runs must not masquerade as current inputs.
- Use explicit run/dataset identifiers when historical and current artifacts coexist.
- Store repository-relative paths in a platform-independent form (prefer POSIX-style paths in manifests).
- Pin/lock the scientific environment sufficiently to reproduce the validated stack, including dependencies used by M5 such as the `exoplanet` ecosystem.
- Do not make claims such as “100% reproducible” unless an automated clean-room reproduction test supports them.

## Engineering rules

- Keep CLI/entry-point scripts thin. Reusable logic belongs under `src/`.
- Avoid copy/paste model implementations for individual planets. Parameterize shared logic.
- Prefer typed, explicit configuration structures over module-level magic constants.
- Add regression tests for every bug fixed during hardening.
- Add deterministic unit tests for transformations, unit conversions, phase construction, target configuration, path generation, manifests, and model-derived quantities.
- Add integration/smoke tests for RAW→Silver→Gold on small fixtures that do not require downloading the full dataset.
- Expensive MCMC should not be required for every CI run; use small synthetic/smoke models in CI and keep full scientific validation as a documented reproducible workflow.
- Fail loudly on provenance/model mismatches. Do not silently continue with a different planet, stale artifact, missing required segment metadata, or invalid diagnostic state.

## Documentation rules

- Documentation must describe the current code, not a superseded model.
- `model_config.json`, reports, tables, figure captions, notebooks, and README text must agree on target, model family, priors, likelihood, sampler, units, preprocessing, and derived parameters.
- Historical exports may remain for traceability, but label them as historical snapshots with generation dates.
- Avoid exaggerated scientific claims. State assumptions, limitations, failure modes, and diagnostic caveats explicitly.

## Working protocol for remediation

For each remediation item:

1. Reproduce or verify the problem from current `main`/current branch.
2. Write a short implementation plan with acceptance criteria.
3. Add or update a regression test that would fail before the fix when feasible.
4. Implement the smallest coherent fix.
5. Run focused tests.
6. Run broader affected pipeline checks.
7. Inspect generated machine-readable artifacts, not only console output.
8. Update reports/docs/notebooks if behavior changed.
9. Update `.agents/REMEDIATION_PLAN.md` with status and evidence.
10. Do not mark an item complete solely because code was edited; mark it complete when its acceptance criteria are verified.

## Priority order

Work in this order unless dependency analysis proves another order is safer:

1. P0 scientific/provenance correctness.
2. P0 clean-run reproducibility.
3. P1 model validation and experiment correctness.
4. P1 tests, CI, environment locking, run isolation.
5. P2 documentation synchronization and repository hygiene.
6. Optional enhancements only after the repository is scientifically trustworthy.

Do not spend time polishing dashboards, plots, abstractions, or framework migrations while P0 correctness issues remain.

## Definition of done for the hardening program

The repository is not “done” until all of the following are true:

- A clean environment can build the intended RAW/Silver/Gold products for the supported targets without relying on historical leftovers.
- Kepler-10 b preprocessing handles segment offsets/cadence appropriately before physical interpretation.
- M5 is generic or cleanly parameterized and has no cross-target hard-codes.
- M5 machine-readable config and human-readable report are generated from the actual physical model.
- Derived quantities use the correct target-specific orbital parameters.
- Sensitivity and noise experiments state and test what they actually implement.
- Diagnostics gate scientific interpretation; failed runs remain available for traceability but are clearly marked invalid for interpretation.
- Unit semantics are explicit.
- Model comparison uses valid metrics where applicable and clearly labels heuristic comparisons.
- Tests cover critical transformations and previously observed regressions.
- CI runs the practical validation suite.
- The scientific environment is reproducibly specified.
- README, docs, notebooks, reports, and machine-readable artifacts are synchronized.
- Repository claims are supported by evidence.

## Skills

Use the repository-local skills under `.agents/skills/` when relevant:

- `repository-hardening`: orchestrate the complete remediation program.
- `data-pipeline-integrity`: RAW/Silver/Gold provenance, units, segment handling, target selection, and run isolation.
- `bayesian-scientific-validation`: priors, likelihoods, diagnostics, posterior predictive checks, physical-model consistency, sensitivity/noise experiments, and model comparison.
- `reproducibility-testing-ci`: environment locking, tests, CI, clean-run verification, cross-platform paths, and regression protection.
- `documentation-artifact-consistency`: synchronize code, configs, reports, notebooks, context exports, figures/tables metadata, and README claims.

When a task spans multiple skills, use `repository-hardening` as the coordinating workflow and load the focused skills for implementation details.
