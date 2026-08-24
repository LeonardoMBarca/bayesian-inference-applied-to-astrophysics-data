# Repository Hardening Remediation Plan

This plan converts the latest repository audit into an executable backlog for Codex. It is intentionally evidence-driven: items are complete only after their acceptance criteria are verified.

Status values:

- `TODO` — not yet addressed.
- `IN_PROGRESS` — implementation underway.
- `BLOCKED` — dependency or external limitation prevents completion.
- `DONE` — acceptance criteria verified with evidence.

## P0 — Scientific and provenance correctness

### P0.1 — Make M5 target-safe and remove cross-target hard-codes

**Status:** TODO

**Problem:** The current physical-transit workflow contains target-specific copy/paste state. Kepler-10 b execution can reuse HAT-P-7 b names/paths/report metadata, and at least one derived duration calculation uses the HAT-P-7 b period.

**Required work:**

- Introduce one authoritative target configuration for planet name, slug, host star, mission, orbital period, reference parameters, input paths, output paths, and report names.
- Refactor M5 so the same implementation can run HAT-P-7 b and Kepler-10 b without duplicated model code.
- Remove stale HAT-P-7 b literals from Kepler-10 b execution paths and metadata.
- Ensure every derived quantity uses the target configuration actually used by the forward model.
- Add regression tests that fail on cross-target naming/period contamination.

**Acceptance criteria:**

- No Kepler-10 b M5 artifact is written under a HAT-P-7 b path or filename.
- The period used in all Kepler-10 b derived quantities is the Kepler-10 b period from the authoritative config.
- HAT-P-7 b and Kepler-10 b can be executed from the same generic M5 entry point or a shared implementation with thin target wrappers.
- Tests explicitly verify target identity and target-specific period propagation.

### P0.2 — Fix Kepler-10 b segment-level preprocessing before physical interpretation

**Status:** TODO

**Problem:** Multiple Kepler light-curve products/quarters are combined while Gold loses segment identity before segment-level normalization/detrending. Offsets can then be absorbed as astrophysical signal or enormous extra jitter.

**Required work:**

- Preserve `quarter` and/or equivalent segment identifiers plus `source_fits_file`/product identity into the modeling-ready Gold representation.
- Normalize and, when justified, detrend each segment independently before concatenation/phase folding for physical inference.
- Record every preprocessing transformation and its parameters.
- Add diagnostics showing per-segment baselines before and after correction.
- Re-run Kepler-10 b only after these transformations are verified.

**Acceptance criteria:**

- Modeling input retains auditable source-segment provenance.
- Segment baseline offsets are not silently passed to M5 as one homogeneous light curve.
- A clean rebuild produces the same normalized/detrended modeling dataset from the same source data.
- Kepler-10 b M5 is not marked scientifically interpretable until preprocessing checks pass.

### P0.3 — Handle cadence/exposure integration correctly

**Status:** TODO

**Problem:** Product ranking can select long-cadence data for a short transit, while the physical model is effectively evaluated instantaneously.

**Required work:**

- Audit MAST product ranking and cadence selection.
- Prefer scientifically appropriate cadence for each supported target when available.
- Persist cadence/exposure metadata downstream.
- Implement exposure-time integration/supersampling in the physical model when long cadence is retained and material to the inference.
- Add tests for cadence selection/ranking policy.

**Acceptance criteria:**

- Selected cadence is explicit in generated metadata.
- Short-cadence products are preferred when scientifically appropriate and available, unless a documented reason says otherwise.
- Long-cadence M5 predictions integrate over exposure time when required.

### P0.4 — Make M5 machine-readable provenance describe the actual model

**Status:** TODO

**Problem:** M5 code uses a physical limb-darkened transit model, but generated `model_config.json`/reports can still describe an older trapezoidal model and stale priors/derived fields.

**Required work:**

- Generate model configuration from the parameters actually instantiated by M5.
- Record the actual forward-model family, limb-darkening parameterization, orbital parameterization, priors, likelihood, jitter/noise model, cadence integration, sampler settings, and derived quantities.
- Generate human-readable reports from the same structured source when practical.
- Add consistency tests between model metadata and configured implementation.

**Acceptance criteria:**

- `model_config.json` for M5 contains M5 parameters such as radius ratio/impact parameter/scaled semimajor axis/limb darkening/t0 as appropriate, not M3 trapezoid parameters.
- Human-readable reports no longer claim that M5 is a trapezoid or lacks limb darkening when the code uses a limb-darkened physical model.
- Target identity, model family, priors, likelihood, and outputs agree across code/config/report.

### P0.5 — Add scientific interpretation gates

**Status:** TODO

**Problem:** Good sampler convergence can be mistaken for scientific validity; runs with pathological extra jitter or failed diagnostics need explicit interpretation status.

**Required work:**

- Centralize diagnostic thresholds and interpretation criteria.
- Track at minimum divergences, R-hat, ESS, BFMI where applicable, posterior predictive checks, and jitter-vs-measurement-error scale.
- Distinguish `sampling_converged`, `posterior_predictive_acceptable`, and `scientifically_interpretable` rather than using one boolean.
- Preserve failed runs with reasons.

**Acceptance criteria:**

- A run cannot be recommended for physical interpretation solely because R-hat/ESS are good.
- Sensitivity runs with R-hat ~1.7 / ESS ~6 remain explicitly non-interpretable.
- Kepler-10 b runs with pathological scale mismatch are flagged pending preprocessing/model review.

## P1 — Bayesian experiment quality

### P1.1 — Redesign sensitivity analysis as an actual prior-sensitivity study

**Status:** TODO

**Problem:** The current deliberately extreme prior can dominate the posterior and produce poor geometry, but documentation may frame the experiment as evidence of robustness.

**Required work:**

- Reframe the existing failed extreme-prior run as evidence of prior misspecification/failure, not robustness.
- Add prior predictive checks.
- Create a principled grid/family of weakly informative and reasonably informative priors.
- Compare posterior stability, diagnostics, and predictive behavior across priors.
- Keep the intentionally absurd prior as a negative-control experiment if useful.

**Acceptance criteria:**

- Documentation accurately states what the extreme-prior run demonstrates.
- Sensitivity conclusions are based on multiple justified priors, not one pathological counterexample.
- Prior predictive diagnostics are generated and documented.

### P1.2 — Make noise experiments match their claims

**Status:** TODO

**Problem:** A sinusoidal injected component may be called red/correlated noise while the inference likelihood still only models independent jitter.

**Required work:**

- Clearly separate white-noise injection, deterministic/systematic injection, and stochastic correlated-noise injection.
- If claiming correlated-noise handling, implement an actual correlated likelihood/noise process, e.g. GP/celerite2 or another justified covariance model.
- Pass noisy arrays explicitly into the model instead of relying on mutable dataframe/view behavior.
- Test recovery under controlled synthetic scenarios.

**Acceptance criteria:**

- Experiment names and reports match the actual data-generating process and inference model.
- Correlated-noise robustness is not claimed unless covariance/correlation is modeled or the claim is explicitly only about robustness to unmodeled correlation.
- Synthetic recovery tests are deterministic under fixed seeds.

### P1.3 — Improve model comparison

**Status:** TODO

**Problem:** M4 currently relies heavily on simple predictive metrics/heuristics and cannot compute LOO/WAIC when log likelihood is absent.

**Required work:**

- Store pointwise log likelihood in inference data for models where valid.
- Add LOO/WAIC/ELPD comparison where models share a legitimate observation target and likelihood basis.
- Do not force information-criterion comparison across models that are not statistically comparable.
- Separate empirical predictive metrics from manually defined structural scores.
- Include M5 only after M5 provenance and preprocessing are valid.

**Acceptance criteria:**

- Model-comparison report clearly distinguishes formal Bayesian criteria, simple predictive errors, and heuristic domain scores.
- No metric is presented beyond its statistical applicability.

## P1 — Data semantics and clean reproducibility

### P1.4 — Make scientific units explicit

**Status:** TODO

**Problem:** Some catalog fields can be ambiguous, especially transit depth percent vs fraction.

**Required work:**

- Audit all NASA/MAST/ETD reference fields used downstream.
- Rename or annotate columns so units are machine-readable and human-readable.
- Add explicit conversion functions with tests.

**Acceptance criteria:**

- A reviewer can identify units without consulting implicit external conventions.
- Percent/fraction conversions have regression tests.

### P1.5 — Isolate current state from historical runs

**Status:** TODO

**Problem:** Old artifacts can remain after the supported target list changes, allowing a clean-run dependency to be masked by stale files.

**Required work:**

- Introduce dataset/run IDs or another explicit run-isolation strategy.
- Define current-state manifests separately from event/history logs where needed.
- Ensure Gold backup targets are actually reproducible from the current RAW/Silver configuration or remove them from current config.
- Add a clean-workspace integration test.

**Acceptance criteria:**

- Deleting generated outputs and rebuilding does not change target availability unexpectedly.
- TrES-2 b cannot silently act as a backup unless it is part of the reproducible current pipeline.

### P1.6 — Cross-platform path normalization

**Status:** TODO

**Problem:** Manifest paths may contain Windows separators but modeling/validation may run on Linux/WSL.

**Required work:**

- Persist repository-relative manifest paths as POSIX strings.
- Normalize legacy paths at read boundaries when necessary.
- Test path round trips on platform-neutral fixtures.

**Acceptance criteria:**

- Windows-generated manifests can be consumed under Linux/WSL without interpreting backslashes as literal filename characters.

## P1 — Testing, CI, environment

### P1.7 — Add a real test suite

**Status:** TODO

**Required minimum coverage:**

- target configuration and path generation;
- orbital period propagation into derived quantities;
- unit conversion;
- phase construction;
- segment preservation/normalization;
- MAST ranking/cadence policy;
- manifest path normalization;
- report/config target identity;
- M5 metadata/model consistency;
- sensitivity interpretation gates;
- small synthetic posterior/model smoke tests where practical.

**Acceptance criteria:**

- `pytest` or equivalent runs locally from a clean environment.
- Every P0 bug fixed has a regression test when technically feasible.

### P1.8 — Add CI

**Status:** TODO

**Required work:**

- Add lint/static checks appropriate for the project.
- Run unit tests and small integration tests.
- Avoid full expensive MCMC in normal PR CI.
- Optionally add a scheduled/manual scientific validation workflow for heavier checks.

**Acceptance criteria:**

- Pull requests cannot silently break critical pipeline invariants.

### P1.9 — Lock the scientific environment

**Status:** TODO

**Problem:** Current requirements are not sufficient to reproduce the M5 stack exactly.

**Required work:**

- Define supported Python version(s).
- Include all runtime dependencies used by validated models, including `exoplanet`-related packages.
- Add a lockfile/environment specification appropriate to the chosen packaging strategy.
- Document compiler/toolchain requirements where PyTensor/exoplanet requires them.

**Acceptance criteria:**

- A clean environment can install the validated stack and run the non-expensive smoke suite.

## P2 — Documentation and repository hygiene

### P2.1 — Synchronize README and docs with current supported targets/models

**Status:** TODO

**Required work:**

- Reconcile the old eight-planet documentation with the current supported-target configuration.
- Decide which documents are historical snapshots vs living docs.
- Document M5, sensitivity, noise experiments, and Kepler-10 b only after their implementations are correct.
- Replace absolute claims such as “100% reproducible” with evidence-backed wording.

**Acceptance criteria:**

- A new reader is not told simultaneously that the current pipeline supports incompatible target sets or model generations.

### P2.2 — Update notebooks

**Status:** TODO

**Required work:**

- Keep notebooks as thin front-ends to canonical code.
- Add/update M5 and experiment notebooks only when they reflect validated workflows.
- Remove hard-coded assumptions that make notebooks silently target HAT-P-7 b when another target is intended.

### P2.3 — Repository storage strategy

**Status:** TODO

**Required work:**

- Decide whether large FITS/traces/derived binaries belong in Git, Git LFS, DVC, release artifacts, or object storage.
- Preserve reproducibility through manifests/checksums even when binaries move out of normal Git history.

### P2.4 — Clean obvious hygiene issues

**Status:** TODO

**Required work:**

- Remove/repair corrupted trailing bytes/rules in `.gitignore`.
- Replace one-off ignore rules with a documented data-artifact policy.
- Remove exact duplicate TCC documents when safe, preserving one canonical copy and any required provenance note.

## Final validation milestone

The hardening program is complete only after Codex can demonstrate, from a clean checkout/environment, a reproducible supported-target pipeline with synchronized code, tests, diagnostics, model metadata, and documentation.

For the final validation report, include:

- commands executed;
- environment/lock identity;
- test and CI results;
- regenerated dataset/run identifiers;
- M1–M5 diagnostic summary for scientifically valid runs;
- explicit list of runs retained only as failed/negative controls;
- comparison against catalog/literature references as validation, not output tuning;
- any remaining limitations that are scientifically honest and intentionally accepted.
