---
name: literature-novelty-positioning
description: Build and maintain the publication novelty matrix, compare this repository with existing exoplanet inference/reproducibility tools, and prevent unsupported novelty claims.
---

# Literature and Novelty Positioning

Use this skill for P1 and whenever manuscript language claims novelty, comparison with prior work, or journal fit.

## Goal

Identify the narrowest defensible contribution supported by current literature and the repository's completed evidence.

## Required literature map

Search current authoritative literature for at least:

- physical exoplanet transit modeling;
- `exoplanet`;
- `juliet`;
- `allesfitter`;
- PyMC/HMC/NUTS transit inference;
- injection-recovery and simulation-based calibration in exoplanet science;
- Gaussian-process/correlated-noise modeling in photometric time series;
- provenance/content-addressed scientific data workflows;
- reproducible astronomical software and archived computational artifacts.

Prefer peer-reviewed papers and official project/journal documentation. Record DOI/arXiv/version/date and the exact capability relevant to the comparison.

## Novelty matrix

For each relevant prior system/paper, record:

- data lineage/provenance support;
- transit model family;
- sampler/inference engine;
- correlated-noise support;
- injection-recovery/calibration evidence;
- external benchmark evidence;
- failure/interpretation gates;
- content-addressed dataset/run identity;
- reproducibility/release model;
- multi-target validation;
- major limitations.

Use `unknown/not verified` rather than assuming absence.

## Claim policy

Words such as `first`, `novel`, `unprecedented`, `unique`, `state of the art`, and `superior` require explicit evidence from the novelty matrix.

Prefer claims like:

- `This work integrates ...`;
- `We empirically evaluate ...`;
- `Within the literature reviewed, we did not identify ...`;

unless a systematic-enough search justifies stronger wording.

## No strawman comparisons

Do not criticize existing tools for features outside their intended scope. Distinguish:

- fitting capability;
- validation methodology;
- provenance/reproducibility infrastructure;
- scientific scope.

A tool can be excellent at transit fitting without implementing this repository's exact evidence-promotion contract.

## Deliverables

- machine-readable or tabular novelty matrix;
- cited narrative summary;
- precise candidate novelty statement;
- list of claims that must not be made;
- journal-fit notes based on current author guidelines;
- references to use in the TCC/paper.

Update the matrix near submission because software and journal scopes can change.