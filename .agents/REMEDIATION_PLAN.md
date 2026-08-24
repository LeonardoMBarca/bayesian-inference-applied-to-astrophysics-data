# Repository Hardening Remediation Plan

This is the persistent backlog for Codex. Do not mark an item `DONE` until its acceptance criteria are verified.

Status: `TODO`, `IN_PROGRESS`, `BLOCKED`, `DONE`.

## P0 — Scientific/provenance correctness

### P0.1 — Make M5 target-safe
**Status:** DONE

- Create one authoritative target configuration for planet, slug, host, mission, orbital period, reference values, inputs, outputs, and report names.
- Refactor M5 so HAT-P-7 b and Kepler-10 b share implementation instead of copy/paste.
- Remove stale HAT-P-7 b literals from Kepler-10 b execution.
- Ensure derived quantities use the target period actually used by the model.
- Add regression tests for cross-target contamination.

**Acceptance:** no Kepler-10 artifact uses HAT-P-7 paths/names/periods; both targets run through shared/config-driven M5 code.

**Evidence (2026-08-24):** `src/project_config.py` is the authoritative target
registry; `src/bayesian_modeling/physical_transit.py` is shared by both thin
CLIs. Target/path/period contamination tests and physical graph smoke tests pass
for HAT-P-7 b and Kepler-10 b. Current Kepler-10 config/report/table identity is
checked by `tests/test_current_m5_artifacts.py`.

### P0.2 — Fix Kepler-10 b segment preprocessing
**Status:** DONE

- Preserve quarter/segment/source-FITS identity through modeling preparation.
- Normalize and, if justified, detrend each segment before concatenation/phase folding.
- Record transformations and parameters.
- Add before/after per-segment diagnostics.

**Acceptance:** segment offsets are not silently absorbed as astrophysical signal/jitter and a clean rebuild reproduces the same modeling data.

**Evidence (2026-08-24):** Gold retains segment, quarter, source FITS, cadence
and exposure, records raw and normalized medians, and normalizes each segment on
its out-of-transit baseline. `validate_clean_rebuild.py` reproduced dataset
`kepler_10_b-06a6ce6b0b39f5b4` and M5 input hash `5bd20f…3845` from RAW in an
isolated, network-free workspace.

### P0.3 — Handle cadence/exposure integration
**Status:** DONE

- Audit MAST ranking and cadence selection.
- Prefer scientifically appropriate cadence when available.
- Persist cadence/exposure metadata downstream.
- Integrate/supersample the physical transit model for long cadence when material.

**Acceptance:** cadence is explicit and model evaluation matches the exposure-time assumptions.

**Evidence (2026-08-24):** versioned selection policy chooses Kepler short
cadence for Kepler-10 b; Gold persists a median exposure of 58.849 s. M5
integrates every observation with target-configured oversampling 15. Cadence,
selection, missing-exposure and graph integration regressions pass.

### P0.4 — Make M5 provenance describe the actual model
**Status:** DONE

- Generate `model_config.json` from the actual physical M5 configuration.
- Record real limb-darkening, orbital parameters, priors, likelihood, jitter/noise model, sampler settings, and derived quantities.
- Generate reports from the same structured source where practical.

**Acceptance:** code, model config, report, tables, target identity, and derived quantities all agree.

**Evidence (2026-08-24):** `scientific_002` config/report/tables are generated
from the implemented circular Keplerian, quadratic limb-darkened, exposure-
integrated Normal likelihood. Rebuild from trace was allowed only after exact
dataset/input-hash validation; trace SHA-256 is `7ed982…df4c`.

### P0.5 — Add scientific interpretation gates
**Status:** DONE

- Separate sampler convergence, posterior-predictive adequacy, and scientific interpretability.
- Track R-hat, ESS, divergences, BFMI where applicable, posterior predictive checks, and jitter-vs-measurement-error scale.
- Preserve failed runs with explicit rejection reasons.

**Acceptance:** a run cannot be called scientifically interpretable merely because NUTS converged.

**Evidence (2026-08-24):** the gate separates sampler, PPC and scientific
checks. `scientific_002` passed R-hat 1.0051, ESS 582.1, zero divergences, BFMI
0.7317, PPC coverage 0.9337 and scale/provenance checks. `scientific_001`,
`smoke_005` and interrupted/failed runs remain rejected or failed in the run
inventory.

## P1 — Bayesian experiment quality

### P1.1 — Redesign prior sensitivity
**Status:** DONE

- Reframe the existing extreme-prior result honestly if it demonstrates prior domination/non-convergence.
- Add prior predictive checks.
- Use a justified grid/family of priors.
- Keep absurd priors only as negative controls if useful.

**Evidence (2026-08-24):** `sensitivity_001` independently ran
`catalog_tighter`, `baseline` and `weak`, each with prior predictive and all
gates. All three passed on the same 3,000 observations; maximum relative shifts
from baseline were 0.77% (`Rp/Rs`) and 1.59% (depth), reported descriptively
without a post-selected universal robustness threshold. Historical pathological
sensitivity remains labeled non-interpretable.

### P1.2 — Make noise experiments match their claims
**Status:** DONE

- Separate white, deterministic/systematic, and stochastic correlated noise.
- If claiming correlated-noise modeling, implement an actual covariance/noise process such as a justified GP/celerite2 model.
- Pass noisy arrays explicitly rather than relying on mutability/view side effects.
- Add deterministic injection/recovery tests.

**Evidence (2026-08-24):** white Gaussian, deterministic sinusoid and
segment-local AR(1) generators are separate, seeded and non-mutating. Tests
verify exact additive recovery and expected correlation. Artifacts explicitly
state `inference_status=not_run`; the repository makes no GP/correlated-
likelihood claim, so no GP implementation is implied as completed work.

### P1.3 — Improve model comparison
**Status:** DONE

- Store pointwise log likelihood where valid.
- Add LOO/WAIC/ELPD only for statistically comparable models.
- Separate formal Bayesian criteria, predictive errors, and heuristic structural scores.
- Include M5 only after M5 is scientifically valid.

**Evidence (2026-08-24):** M5 stores pointwise log likelihood. The comparison
contract requires identical dataset, exact input hash, likelihood and passed
gates. Historical M1/M2 comparison is rejected. The comparable prior runs have
LOO/WAIC persisted separately from RMSE/MAE; Pareto-k warnings set
`ranking_status=not_ranked_due_to_diagnostic_warning`.

## P1 — Data semantics and clean reproducibility

### P1.4 — Make units explicit
**Status:** DONE

- Audit scientific units, especially transit-depth percent vs fraction and hours vs days.
- Rename/annotate fields and add tested conversion functions.

**Evidence (2026-08-24):** explicit `transit_depth_percent`,
`transit_depth_fraction`, `transit_duration_hours`, period/day and exposure/sec
fields propagate through config and data products; deterministic conversion
tests and artifact checks pass.

### P1.5 — Isolate current state from historical runs
**Status:** DONE

- Introduce dataset/run IDs or equivalent isolation.
- Separate current-state manifests from append-only event logs where appropriate.
- Ensure backup targets are reproducible from current config or remove them.
- Add a clean-workspace rebuild test.

**Evidence (2026-08-24):** event history and 445-row deduplicated current-state
RAW manifests are separate. Dataset IDs and target/run-specific output paths
isolate current state. Both configured Gold targets rebuild from current RAW;
the network-free temporary-workspace reproduction passed.

### P1.6 — Normalize persisted paths across platforms
**Status:** DONE

- Store repo-relative paths as POSIX strings.
- Normalize legacy paths at read boundaries if needed.
- Add path round-trip tests.

**Evidence (2026-08-24):** all current manifests use repository-relative POSIX
paths; normalization occurs at read/write boundaries and round-trip/regression
tests pass on Windows-hosted WSL.

## P1 — Testing, CI, environment

### P1.7 — Add a real test suite
**Status:** DONE

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

**Evidence (2026-08-24):** 45 tests pass, covering every minimum item above plus
ArviZ 1.3 BFMI/HDI/LOO/WAIC compatibility, noise injection, clean fixture and
current generated artifacts.

### P1.8 — Add CI
**Status:** DONE

- Run lint/static checks, unit tests, and small integration tests on PRs.
- Keep expensive full MCMC out of standard CI; optionally add manual/scheduled scientific validation.

**Evidence (2026-08-24):** `.github/workflows/ci.yml` runs exact dependency
installation, static validation, 44 practical tests and artifact validation on
push/PR; the full clean rebuild is a manual workflow input. Equivalent commands
passed locally; no hosted-CI execution is claimed.

### P1.9 — Lock the scientific environment
**Status:** DONE

- Define supported Python version(s).
- Include all validated runtime dependencies including the M5/exoplanet stack.
- Add an appropriate lock/environment specification.
- Document compiler/toolchain requirements.

**Evidence (2026-08-24):** `requirements.txt` contains exact validated runtime
versions including PyMC/ArviZ/exoplanet; `environment.yml` fixes Python 3.14.6;
`pyproject.toml` defines build/test metadata; README documents WSL/toolchain and
lock installation.

## P2 — Documentation and repository hygiene

### P2.1 — Synchronize README/docs
**Status:** DONE

- Reconcile old eight-planet docs with current supported targets.
- Mark historical context exports as historical snapshots.
- Document M5/Kepler-10/noise/sensitivity only according to validated behavior.
- Remove unsupported absolute claims such as “100% reproducible”.

**Evidence (2026-08-24):** main README, docs index, modeling/noise docs, generated
Gold docs, reports index and TCC addendum describe current targets/model/gates
and limitations. Context exports and old HAT-P-7 reports are dated historical
snapshots; unsupported absolute claims were removed.

### P2.2 — Update notebooks
**Status:** DONE

- Keep notebooks thin front-ends to canonical code.
- Add/update M5 and experiment notebooks only for validated workflows.
- Remove hidden HAT-P-7 hard-coding where target-generic behavior is expected.

**Evidence (2026-08-24):** notebook 07 is a thin M5 front-end and notebook 06
uses the guarded comparison path. All six notebooks parse as JSON; historical
notebooks are labeled and are not presented as current generic implementations.

### P2.3 — Define repository storage strategy
**Status:** DONE

- Decide which large FITS/traces/derived binaries belong in Git vs Git LFS/DVC/releases/object storage.
- Preserve reproducibility via manifests/checksums.

**Evidence (2026-08-24):** `docs/STORAGE_POLICY.md` keeps compact published
artifacts/manifests/checksums in Git while ignoring regenerable full Silver/Gold
tables, traces and injected curves. RAW used downstream remains represented by
the versionable current-state manifest; ignored derived files were removed from
the Git index without deleting local copies. Zero dos 445 caminhos RAW atuais
está ignorado e nenhum candidato à versão excede 100 MiB.

### P2.4 — Clean hygiene issues
**Status:** DONE

- Repair corrupted trailing bytes/rules in `.gitignore`.
- Replace one-off data ignore rules with a coherent policy.
- Remove exact duplicate TCC documents when safe while keeping one canonical copy/provenance note.

**Evidence (2026-08-24):** corrupted NUL/trailing ignore rules were replaced by
a coherent `.gitignore`; the byte-identical duplicate TCC PDF was removed while
the canonical file and `tcc-docs/PROVENANCE.md` were retained.

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

**Status:** DONE

**Final evidence (2026-08-24):**

- `reports/REPOSITORY_HARDENING_FINAL.md` records commands, environment hashes,
  dataset/run IDs, diagnostics, failed controls, catalog-scale caveat and
  limitations;
- `reports/clean_rebuild_validation.json`: isolated RAW→Silver→Gold passed with
  network disabled and both dataset IDs/hashes reproduced;
- `scripts/validate_hardened_artifacts.py`: passed across RAW checksums, Silver
  units, Gold segments/cadence, M5 artifacts/gates, noise claims, sensitivity,
  formal-comparison warnings and negative controls;
- `python -m unittest discover -s tests -v`: 45/45 passed;
- `python scripts/static_validate.py`: 83 Python files, 6 notebooks and 18
  exact scientific dependencies passed;
- `reports/model_run_inventory.json`: only explicit gated runs are current and
  interpretable; historical, rejected and failed runs remain traceable.
