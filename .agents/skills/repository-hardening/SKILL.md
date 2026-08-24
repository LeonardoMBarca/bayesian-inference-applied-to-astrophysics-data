---
name: repository-hardening
description: Orchestrate end-to-end remediation of this astrophysics Bayesian-inference repository. Use for broad requests to fix, harden, audit, modernize, complete, or make the repository scientifically trustworthy. Coordinate data-pipeline integrity, Bayesian validation, reproducibility/testing/CI, and documentation consistency. Do not use for a tiny isolated edit that clearly belongs to one focused skill.
---

# Repository Hardening

Use this skill as the coordinator for multi-area work.

## Inputs

- `AGENTS.md`
- `.agents/REMEDIATION_PLAN.md`
- the current repository state
- current tests, manifests, generated artifacts, diagnostics, and documentation

## Workflow

1. Read `AGENTS.md` and the full remediation plan.
2. Re-verify relevant findings against the current branch before editing.
3. Build a dependency graph of the requested remediation items.
4. Select the focused skill(s) needed for each batch:
   - `$data-pipeline-integrity`
   - `$bayesian-scientific-validation`
   - `$reproducibility-testing-ci`
   - `$documentation-artifact-consistency`
5. Work P0 items before P1/P2 unless a prerequisite requires otherwise.
6. For every bug, define the scientific/engineering invariant that was violated.
7. Add a regression check that encodes that invariant when feasible.
8. Implement the smallest coherent fix that removes the root cause rather than masking the symptom.
9. Regenerate affected outputs and inspect structured artifacts.
10. Update documentation in the same batch.
11. Update the remediation plan status with concrete evidence.

## Change-batch discipline

Prefer batches that can be independently verified, for example:

1. target configuration + cross-target regression tests;
2. Gold segment preservation + normalization/detrending tests;
3. cadence selection + exposure integration;
4. M5 config/report generation from actual model state;
5. interpretation gates;
6. sensitivity/noise experiment redesign;
7. model comparison/log likelihood;
8. clean-run isolation + paths + environment;
9. CI and docs synchronization.

Do not mix unrelated cosmetic cleanup into a scientific correctness batch.

## Evidence required before `DONE`

For each remediation item, capture at least one of:

- a regression test that failed before and passes after;
- a clean-run artifact demonstrating correct target/provenance;
- a structured diagnostic showing corrected scientific behavior;
- a before/after schema or manifest validation;
- a reproducible command plus expected output;
- a consistency check across code/config/report.

Code inspection alone is not sufficient evidence for high-risk scientific fixes.

## Final repository validation

Before declaring the overall hardening complete:

1. Start from a clean generated-artifact state or isolated clean-run directory.
2. Install the documented locked environment.
3. Run the practical unit/integration suite.
4. Rebuild the supported pipeline for supported targets.
5. Run validated scientific workflows at the documented level.
6. Verify target identity and provenance in every generated artifact.
7. Verify model configs describe actual models.
8. Verify interpretation gates correctly reject intentionally bad/failed runs.
9. Verify documentation describes the regenerated state.
10. Produce a final hardening report with remaining limitations.
