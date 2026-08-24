# Repository Hardening Remediation Plan

This is the persistent backlog for Codex. Do not mark an item `DONE` until its acceptance criteria are verified.

Status: `TODO`, `IN_PROGRESS`, `BLOCKED`, `DONE`.

## P0 — Scientific/provenance correctness

### P0.1 — Make M5 target-safe
**Status:** TODO

- Create one authoritative target configuration for planet, slug, host, mission, orbital period, reference values, inputs, outputs, and report names.
- Refactor M5 so HAT-P-7 b and Kepler-10 b share implementation instead of copy/paste.
- Remove stale HAT-P-7 b literals from Kepler-10 b execution.
- Ensure derived quantities use the target period actually used by the model.
- Add regression tests for cross-target contamination.

**Acceptance:** no Kepler-10 artifact uses HAT-P-7 paths/names/periods; both targets run through shared/config-driven M5 code.

### P0.2 — Fix Kepler-10 b segment preprocessing
**Status:** TODO

- Preserve quarter/segment/source-FITS identity through modeling preparation.
- Normalize and, if justified, detrend each segment before concatenation/phase folding.
- Record transformations and parameters.
- Add before/after per-segment diagnostics.

**Acceptance:** segment offsets are not silently absorbed as astrophysical signal/jitter and a clean rebuild reproduces the same modeling data.

### P0.3 — Handle cadence/exposure integration
**Status:** TODO

- Audit MAST ranking and cadence selection.
- Prefer scientifically appropriate cadence when available.
- Persist cadence/exposure metadata downstream.
- Integrate/supersample the physical transit model for long cadence when material.

**Acceptance:** cadence is explicit and model evaluation matches the exposure-time assumptions.

### P0.4 — Make M5 provenance describe the actual model
**Status:** TODO

- Generate `model_config.json` from the actual physical M5 configuration.
- Record real limb-darkening, orbital parameters, priors, likelihood, jitter/noise model, sampler settings, and derived quantities.
- Generate reports from the same structured source where practical.

**Acceptance:** code, model config, report, tables, target identity, and derived quantities all agree.

### P0.5 — Add scientific interpretation gates
**Status:** TODO

- Separate sampler convergence, posterior-predictive adequacy, and scientific interpretability.
- Track R-hat, ESS, divergences, BFMI where applicable, posterior predictive checks, and jitter-vs-measurement-error scale.
- Preserve failed runs with explicit rejection reasons.

**Acceptance:** a run cannot be called scientifically interpretable merely because NUTS converged.

## P1 — Bayesian experiment quality

### P1.1 — Redesign prior sensitivity
**Status:** TODO

- Reframe the existing extreme-prior result honestly if it demonstrates prior domination/non-convergence.
- Add prior predictive checks.
- Use a justified grid/family of priors.
- Keep absurd priors only as negative controls if useful.

### P1.2 — Make noise experiments match their claims
**Status:** TODO

- Separate white, deterministic/systematic, and stochastic correlated noise.
- If claiming correlated-noise modeling, implement an actual covariance/noise process such as a justified GP/celerite2 model.
- Pass noisy arrays explicitly rather than relying on mutability/view side effects.
- Add deterministic injection/recovery tests.

### P1.3 — Improve model comparison
**Status:** TODO

- Store pointwise log likelihood where valid.
- Add LOO/WAIC/ELPD only for statistically comparable models.
- Separate formal Bayesian criteria, predictive errors, and heuristic structural scores.
- Include M5 only after M5 is scientifically valid.

## P1 — Data semantics and clean reproducibility

### P1.4 — Make units explicit
**Status:** TODO

- Audit scientific units, especially transit-depth percent vs fraction and hours vs days.
- Rename/annotate fields and add tested conversion functions.

### P1.5 — Isolate current state from historical runs
**Status:** TODO

- Introduce dataset/run IDs or equivalent isolation.
- Separate current-state manifests from append-only event logs where appropriate.
- Ensure backup targets are reproducible from current config or remove them.
- Add a clean-workspace rebuild test.

### P1.6 — Normalize persisted paths across platforms
**Status:** TODO

- Store repo-relative paths as POSIX strings.
- Normalize legacy paths at read boundaries if needed.
- Add path round-trip tests.

## P1 — Testing, CI, environment

### P1.7 — Add a real test suite
**Status:** TODO

Minimum regression coverage:
- target config/path generation;
- period propagation into derived values;
- unit conversion;
- phase construction;
- segment preservation/normalization;
- MAST cadence ranking;
- manifest path normalization;
- report/config target identity;
- M5 metadata/model consistency;
- sensitivity interpretation gates;
- small synthetic model smoke tests where practical.

### P1.8 — Add CI
**Status:** TODO

- Run lint/static checks, unit tests, and small integration tests on PRs.
- Keep expensive full MCMC out of standard CI; optionally add manual/scheduled scientific validation.

### P1.9 — Lock the scientific environment
**Status:** TODO

- Define supported Python version(s).
- Include all validated runtime dependencies including the M5/exoplanet stack.
- Add an appropriate lock/environment specification.
- Document compiler/toolchain requirements.

## P2 — Documentation and repository hygiene

### P2.1 — Synchronize README/docs
**Status:** TODO

- Reconcile old eight-planet docs with current supported targets.
- Mark historical context exports as historical snapshots.
- Document M5/Kepler-10/noise/sensitivity only according to validated behavior.
- Remove unsupported absolute claims such as “100% reproducible”.

### P2.2 — Update notebooks
**Status:** TODO

- Keep notebooks thin front-ends to canonical code.
- Add/update M5 and experiment notebooks only for validated workflows.
- Remove hidden HAT-P-7 hard-coding where target-generic behavior is expected.

### P2.3 — Define repository storage strategy
**Status:** TODO

- Decide which large FITS/traces/derived binaries belong in Git vs Git LFS/DVC/releases/object storage.
- Preserve reproducibility via manifests/checksums.

### P2.4 — Clean hygiene issues
**Status:** TODO

- Repair corrupted trailing bytes/rules in `.gitignore`.
- Replace one-off data ignore rules with a coherent policy.
- Remove exact duplicate TCC documents when safe while keeping one canonical copy/provenance note.

## Final validation milestone

The program is complete only after a clean checkout/environment can reproduce the supported pipeline and the repository can show:

- commands executed;
- environment/lock identity;
- tests/CI results;
- dataset/run identifiers;
- diagnostic summary for valid M1–M5 runs;
- explicit failed/negative-control runs;
- validation against catalog/literature without tuning to those values;
- remaining scientifically honest limitations.
