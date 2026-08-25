---
name: paper-reproducibility-release
description: Prepare a publication-grade repository release with frozen evidence, paper artifact regeneration, citation metadata, archival/DOI readiness, and public-release safety checks.
---

# Paper Reproducibility and Release

Use this skill for P7 and final publication preparation.

## Objective

Make the paper's computational evidence independently auditable and citable.

## Release object

A paper release must tie together:

- Git commit/tag;
- experiment protocols;
- experiment registry;
- raw/current-state manifests;
- Gold dataset IDs and source hashes;
- model/run configs;
- environment locks;
- result summaries;
- paper tables and figures;
- checksums;
- known failed/negative results required by the manuscript.

Generate a machine-readable `REPRODUCIBILITY_MANIFEST.json` rather than relying on prose.

## Paper artifact pipeline

Create one documented entry point that regenerates paper-critical tables and figures from approved machine-readable evidence. It should fail if:

- a source artifact is missing;
- a hash differs;
- a protocol/result status is invalid;
- a table/figure was generated from a stale run;
- a publication result has no traceable experiment entry.

Do not manually edit numerical values into final publication figures/tables.

## Citation and archival metadata

Before public release prepare:

- `CITATION.cff`;
- license review;
- authors/affiliations/ORCID fields when available;
- software/data availability statement;
- release notes;
- repository DOI archival instructions (for example Zenodo-compatible release flow);
- third-party data/software citation inventory.

Do not invent missing author identifiers or affiliations.

## Public-release safety

Before making the repository public, scan for:

- credentials/tokens/secrets;
- private email/data not intended for release;
- proprietary material;
- third-party files whose redistribution is not permitted;
- large files that violate host limits;
- historical documents containing sensitive/non-public information.

A scientifically useful artifact does not justify publishing private material.

## Storage policy

Large traces may remain unversioned if the repository preserves sufficient configs, seeds, hashes and commands to regenerate them. Publication-critical summaries must remain available and traceable.

## Clean reproduction

Run the strongest practical clean-room reconstruction and paper-artifact validation before tagging the release. Record exact commands and outcomes.

## Release gate

Do not tag the paper release until:

- publication experiments are frozen and registry-complete;
- tests/CI pass;
- paper artifacts validate against sources;
- environment identity is locked;
- citation metadata is complete;
- public-release safety review passes;
- known limitations are documented;
- archival/DOI deposition path is ready.

## Done

P7 is complete when a third party can identify exactly which immutable evidence produced each paper claim/table/figure and the release is safe and ready to archive with a persistent identifier.