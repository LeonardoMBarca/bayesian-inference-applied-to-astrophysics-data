---
name: documentation-artifact-consistency
description: Synchronize README files, generated reports, notebooks, model configs, tables/figures metadata, context exports, target/model descriptions, scientific claims, and historical documentation with the current validated implementation.
---

# Documentation and Artifact Consistency

Documentation is part of scientific provenance. A correct model with an incorrect report is still an untrustworthy research artifact.

## Consistency contract

For every current model/run, the following must agree:

- target/planet/host/mission;
- dataset/run identity;
- input path and preprocessing;
- model family;
- parameter names and units;
- priors;
- likelihood/noise model;
- sampler settings;
- derived quantities;
- diagnostic/interpretation status;
- output filenames and paths.

Check this contract across:

- executable code/config;
- `model_config.json` and inference summaries;
- tables;
- report Markdown;
- figure captions/metadata;
- notebooks;
- model-specific docs;
- root README.

## Generated docs

Where feasible, generate repeated model facts from one structured model/run metadata object rather than hand-copying them into multiple report builders.

Do not generate documentation that describes a legacy model template while executing a different model.

## Historical snapshots

Context exports generated on older dates may be preserved, but label them clearly as historical snapshots and state which code/data configuration they describe. Do not present a June snapshot as current documentation after August model/target changes.

## Target support claims

Reconcile the declared supported targets with the executable configs and clean-run pipeline. If historical docs mention eight targets while current config intentionally supports two, explain the history and make the current scope unambiguous.

## Scientific claims

Replace unsupported absolutes with measurable statements.

Avoid claims such as:

- “100% reproducible” without clean-room automated evidence;
- “robust to priors” when the sensitivity run is prior-dominated/non-convergent;
- “red-noise model” when only independent jitter is modeled;
- “physical characterization” when preprocessing/model assumptions are known invalid.

Prefer statements tied to evidence and limitations.

## Notebooks

Keep notebooks thin:

- call/import canonical implementation;
- display structured outputs;
- avoid maintaining a second copy of model logic;
- parameterize target choice when the underlying implementation is generic;
- do not add a polished notebook for an unvalidated scientific workflow.

## Regeneration discipline

After scientific behavior changes:

1. regenerate affected configs/tables/reports/figures/notebooks as applicable;
2. inspect target names and paths;
3. inspect numeric fields/units;
4. inspect diagnostic status;
5. update living docs;
6. mark historical outputs explicitly if retained.

## Duplicate/irrelevant TCC files

Exact duplicate institutional files may be deduplicated when safe. Keep one canonical copy and preserve a note if provenance/history matters. Do not accidentally delete authoritative templates or institutional guidance solely because filenames are messy.

## Completion evidence

Before marking documentation work complete, run or implement consistency checks where practical. At minimum, search for stale target/model literals in generated current artifacts and verify that the README/docs match the validated pipeline state.
