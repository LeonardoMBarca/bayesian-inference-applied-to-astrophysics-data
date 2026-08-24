# Repository-local Codex setup

This directory contains durable instructions and reusable skills for hardening this scientific repository.

## Structure

```text
AGENTS.md
.agents/
  README.md
  REMEDIATION_PLAN.md
  CODEX_TASK.md
  skills/
    repository-hardening/
      SKILL.md
      agents/openai.yaml
    data-pipeline-integrity/
      SKILL.md
    bayesian-scientific-validation/
      SKILL.md
    reproducibility-testing-ci/
      SKILL.md
    documentation-artifact-consistency/
      SKILL.md
```

Codex reads repository-local skills from `.agents/skills/<name>/SKILL.md`. The root `AGENTS.md` contains global instructions that apply throughout the repository.

## Recommended use

Start Codex from the repository root and use the coordinating skill:

```text
$repository-hardening
```

A ready-to-paste master task is available in `.agents/CODEX_TASK.md`.

The coordinating skill should delegate conceptually to the focused skills as the work changes from data integrity to statistical modeling, tests/CI, and documentation.

## Important behavior

- Do not ask Codex to rewrite the whole repository in one unverified pass.
- Work through `.agents/REMEDIATION_PLAN.md` in dependency order.
- Require evidence before marking an item complete.
- Preserve failed scientific runs for traceability, but label them clearly as non-interpretable when diagnostics or model validity fail.
- Prefer a clean, reproducible, scientifically defensible pipeline over cosmetic complexity.
