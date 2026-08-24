---
name: reproducibility-testing-ci
description: Build or review environment locking, tests, CI, clean-run reproducibility, dataset/run isolation, cross-platform paths, packaging/dependencies, and regression protection for this scientific repository.
---

# Reproducibility, Testing, and CI

Reproducibility means a clean checkout can reconstruct the claimed current state from documented inputs/configuration. It does not mean keeping every generated file in ordinary Git.

## Environment

- Define supported Python version(s).
- Include every dependency required by validated workflows, including M5/exoplanet/PyTensor-related packages.
- Choose and commit a reproducible lock/environment specification.
- Document OS/compiler requirements where native compilation matters.
- Avoid relying on an undocumented personal virtual environment path.

## Test pyramid

### Fast unit tests
Cover deterministic logic:

- target configuration;
- output path generation;
- period propagation;
- unit conversion;
- phase folding;
- cadence ranking;
- segment-preserving transformations;
- POSIX manifest paths;
- model/report metadata construction;
- interpretation gates.

### Integration tests
Use small checked-in fixtures or generated synthetic fixtures for:

- RAW→Silver transformations;
- Silver→Gold preparation;
- clean-workspace target availability;
- manifest/checksum behavior;
- model-input creation.

Avoid network dependency in normal tests when fixtures can represent the contract.

### Bayesian smoke tests
Use tiny deterministic synthetic datasets and small draw counts only to detect API/model wiring failures. Do not use tiny CI chains as scientific evidence.

### Full scientific validation
Keep expensive MCMC/injection-recovery as a separately documented/manual or scheduled workflow.

## Regression discipline

For every important bug fix:

1. write a test that captures the violated invariant;
2. demonstrate that the old behavior would fail the invariant when practical;
3. implement the fix;
4. keep the test permanently.

High-value regressions include:

- Kepler-10 b using HAT-P-7 b period;
- Kepler-10 outputs written under HAT paths;
- M5 config describing M3;
- quarter/source identity dropped before preprocessing;
- long-cadence ranking winning accidentally;
- percent/fraction ambiguity;
- Windows manifest paths failing on Linux;
- failed diagnostics being marked interpretable.

## CI

PR CI should normally include:

- dependency/environment setup;
- lint/format check chosen by the repository;
- unit tests;
- small integration tests;
- lightweight model smoke tests if stable enough.

Do not run multi-thousand-draw production MCMC on every PR.

Optionally add:

- manual workflow for complete supported-target rebuild;
- scheduled scientific validation;
- artifact upload for diagnostic summaries.

## Clean-run verification

Create a documented command/workflow that:

1. starts without generated Silver/Gold/model results from earlier runs;
2. builds only from declared current inputs/config;
3. assigns a dataset/run identity;
4. verifies manifests/checksums;
5. confirms supported targets are exactly those reproducible from current inputs;
6. produces deterministic preprocessing outputs where expected.

Historical artifacts must not silently satisfy missing current dependencies.

## Cross-platform paths

Persist repository-relative paths with `/` separators (e.g. `Path(...).as_posix()`). Normalize legacy paths when reading. Add tests using representative Windows-style legacy strings and POSIX current strings.

## Storage strategy

If large FITS, NetCDF traces, or generated figures/tables make Git history impractical, evaluate Git LFS, DVC, release artifacts, or object storage. Whatever mechanism is chosen must preserve version identity, checksums, and instructions sufficient to recover the scientific inputs/results.

## Completion evidence

A reproducibility/testing item is complete only with command output or CI evidence showing the clean environment/test path actually works.
