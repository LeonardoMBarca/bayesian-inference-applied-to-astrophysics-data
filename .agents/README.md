# Repository-local agent setup

This directory contains durable instructions, research protocols and reusable skills for turning the scientifically hardened TCC repository into a publication-grade research artifact.

## Branch mission

On `publication-grade-validation`, the validated `main` state is the protected baseline. The active goal is to build pre-specified, reproducible evidence for a top-quality TCC and a peer-reviewable scientific manuscript.

## Structure

```text
AGENTS.md
.agents/
  README.md
  REMEDIATION_PLAN.md          # historical hardening/baseline context
  PUBLICATION_PLAN.md          # P0-P8 master research roadmap
  EXPERIMENT_REGISTRY.md       # status/evidence ledger
  PAPER_BLUEPRINT.md           # manuscript claims/structure/reviewer questions
  CODEX_TASK.md                # ready-to-paste master execution task
  protocols/
    PROTOCOL_TEMPLATE.md
  skills/
    publication-grade-research/
      SKILL.md
    literature-novelty-positioning/
      SKILL.md
    simulation-calibration-injection-recovery/
      SKILL.md
    independent-benchmark-validation/
      SKILL.md
    ablation-failure-validation/
      SKILL.md
    multi-target-generalization/
      SKILL.md
    correlated-noise-modeling/
      SKILL.md
    paper-reproducibility-release/
      SKILL.md
    repository-hardening/
      SKILL.md
    data-pipeline-integrity/
      SKILL.md
    bayesian-scientific-validation/
      SKILL.md
    reproducibility-testing-ci/
      SKILL.md
    documentation-artifact-consistency/
      SKILL.md
```

Codex reads repository-local skills from `.agents/skills/<name>/SKILL.md`. Root `AGENTS.md` contains global scientific and engineering rules.

## Recommended use

Start Codex from the repository root and use the coordinating publication skill:

```text
$publication-grade-research
```

A complete master task is available in:

```text
.agents/CODEX_TASK.md
```

The coordinator should load focused skills as work moves through literature/novelty, simulation calibration, independent benchmarking, ablations, multi-target validation, correlated noise and final research release.

## Mandatory behavior

- Read `AGENTS.md` and `.agents/PUBLICATION_PLAN.md` before substantial changes.
- Commit/freeze a protocol before each final scientific experiment batch.
- Keep pilots separate from final evidence.
- Never cherry-pick successful targets, seeds, benchmark tools or simulation replicates.
- Preserve failed/rejected/non-interpretable runs.
- Require evidence before marking phases complete.
- Prefer known-truth calibration and independent validation over adding architectural/model complexity.
- Do not start M6/GP work merely because it is technically attractive while P2-P4 are unfinished.
- Generate aggregate reports from the complete declared registry, not manually selected successful outputs.
- Keep manuscript/TCC claims synchronized with machine-readable evidence.

## Current roadmap

The default order is:

```text
P0 baseline freeze/experiment contract
 -> P1 literature + frozen protocols
 -> P2 injection-recovery/calibration
 -> P3 independent benchmark
 -> P4 ablation/failure gates
 -> P5 multi-target validation
 -> P6 M6 correlated noise
 -> P7 paper release/DOI readiness
 -> P8 TCC + manuscript synthesis
```

The purpose is not to make the repository look more sophisticated. The purpose is to make every scientific conclusion progressively harder to falsify for the wrong reasons and easier for a reviewer to audit.