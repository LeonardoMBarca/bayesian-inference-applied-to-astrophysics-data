---
name: repository-hardening
description: Orchestrate end-to-end remediation of this astrophysics Bayesian-inference repository. Use for broad requests to fix, harden, audit, modernize, complete, or make the repository scientifically trustworthy. Coordinate data-pipeline integrity, Bayesian validation, reproducibility/testing/CI, and documentation consistency.
---

# Repository Hardening

Use this as the coordinating skill for multi-area remediation.

## Workflow

1. Read `AGENTS.md` and `.agents/REMEDIATION_PLAN.md` completely.
2. Re-verify relevant findings against the current branch before editing.
3. Build a dependency-aware plan and work P0 items first.
4. Load focused skills as needed:
   - `$data-pipeline-integrity`
   - `$bayesian-scientific-validation`
   - `$reproducibility-testing-ci`
   - `$documentation-artifact-consistency`
5. For every defect, identify the violated invariant and add a regression test when feasible.
6. Implement root-cause fixes rather than masking symptoms.
7. Regenerate affected structured artifacts and inspect them.
8. Update docs in the same batch as behavior changes.
9. Update remediation-plan status only after acceptance criteria are verified.

## Recommended remediation batches

1. authoritative target configuration + cross-target tests;
2. Gold segment preservation + segment normalization/detrending;
3. cadence selection + exposure integration;
4. M5 model metadata/report correctness;
5. scientific interpretation gates;
6. sensitivity/noise redesign;
7. model comparison/log likelihood;
8. clean-run isolation + paths + environment;
9. tests/CI + documentation synchronization.

Do not mix unrelated cosmetic cleanup into scientific-correctness batches.

## Evidence required before `DONE`

Use at least one strong form of evidence per item:

- regression test that would fail before the fix;
- clean-run artifact proving correct target/provenance;
- structured diagnostic showing corrected behavior;
- schema/manifest validation;
- reproducible command plus expected result;
- automated consistency check across code/config/report.

Code inspection alone is insufficient for high-risk scientific fixes.

## Final validation

Before declaring the repository hardened:

1. start from a clean generated-artifact state/run directory;
2. install the documented locked environment;
3. run unit/integration checks;
4. rebuild supported RAW→Silver→Gold flows;
5. run validated scientific workflows;
6. verify target/provenance identity everywhere;
7. verify model configs describe actual models;
8. verify interpretation gates reject bad/negative-control runs;
9. verify docs describe the regenerated state;
10. produce a final hardening report with remaining limitations.
