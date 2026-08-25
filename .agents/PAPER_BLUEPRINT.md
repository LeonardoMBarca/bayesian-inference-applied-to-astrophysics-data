# Scientific Paper Blueprint

## Working contribution

**A validation-gated, content-addressed and reproducible Bayesian workflow for exoplanet transit inference under observational uncertainty.**

This is a working framing, not a final novelty claim. Final wording must be reconciled with `.agents/PUBLICATION_PLAN.md`, the novelty/literature matrix and completed experimental evidence.

## Candidate title directions

- *A Validation-Gated Reproducible Bayesian Workflow for Exoplanet Transit Inference*
- *From Provenance to Posterior: Reproducible Bayesian Transit Inference with Explicit Scientific Validation Gates*
- *Calibrating Trust in Bayesian Exoplanet Transit Inference: Provenance, Injection–Recovery, Independent Benchmarking and Failure Gates*

Do not lock a title until the final evidence determines the strongest defensible contribution.

## Core claims the paper should earn

The manuscript should attempt to earn — not assume — the following claims:

1. A content-addressed RAW→Silver→Gold pipeline can preserve sufficient observational provenance to audit each publication-critical inference input.
2. A physical Bayesian transit workflow can separate sampler convergence, posterior-predictive adequacy and scientific interpretability into explicit executable gates.
3. Repeated injection–recovery experiments quantify the calibration, bias and uncertainty behavior of the workflow under known truth.
4. An independent published implementation provides external computational evidence about agreement/disagreement under comparable model assumptions.
5. Controlled ablations show which preprocessing/modeling decisions materially affect inference and demonstrate that valid-looking MCMC output can still be scientifically invalid.
6. Multi-target evaluation characterizes the supported observational regime rather than generalizing from Kepler-10 b alone.
7. If M6 succeeds, explicit correlated-noise modeling improves calibration/predictive adequacy when temporal correlation is present while its additional flexibility is not universally beneficial.
8. Every claim-producing artifact can be traced to a frozen protocol, data/model identity, code commit, environment and checksum.

Any claim not supported by final experiments must be removed or weakened rather than rationalized.

## Manuscript structure

### Abstract

Five-part structure:

- problem: reliability of scientific Bayesian inference requires more than successful sampling;
- method: content-addressed provenance + physical transit model + validation gates;
- validation: injection–recovery + independent benchmark + ablation/failure tests + multi-target study;
- key quantitative results: populate only from final registry;
- contribution/scope: precise supported regime and reproducibility release.

### 1. Introduction

- Exoplanet transit inference as a measurement problem under observational uncertainty.
- Reproducibility and provenance as part of scientific validity, not only software quality.
- Why sampler convergence alone is insufficient.
- Gap identified by literature/novelty matrix.
- Contributions listed as testable statements.

### 2. Related work

Organize by function rather than a citation dump:

- physical transit modeling and limb darkening;
- Bayesian exoplanet fitting software (`exoplanet`, `juliet`, `allesfitter`, related tools);
- HMC/NUTS and Bayesian diagnostics;
- injection–recovery/SBC/calibration;
- correlated noise/GPs in astronomical time series;
- reproducible scientific software, data provenance and archival practice.

The section must explicitly state what existing tools already solve and where this workflow differs.

### 3. Data and provenance architecture

- public observational sources;
- RAW evidence and checksums;
- Silver schema/units/provenance;
- Gold segment-normalized modeling datasets;
- content-derived dataset identity;
- clean rebuild and environment contract;
- distinction between data provenance and scientific validity.

Avoid presenting architecture as an end in itself. Every engineering mechanism should be linked to a failure mode it prevents.

### 4. Bayesian transit model

- generative model;
- Keplerian geometry;
- quadratic limb darkening and Kipping parameterization;
- exposure-time integration;
- heteroscedastic measurement errors and white jitter;
- priors and their justification;
- NUTS sampling;
- derived parameters;
- limitations of M5.

### 5. Validation-gate methodology

Define separately:

- data/provenance gate;
- sampler gate;
- posterior-predictive gate;
- scientific plausibility/scale gate;
- evidence-promotion contract.

Explain that a run may converge but still be rejected.

### 6. Experimental design

#### 6.1 Injection–recovery and calibration

- simulator;
- final scenario grid;
- replication counts;
- seed policy;
- calibration metrics and uncertainty.

#### 6.2 Independent implementation benchmark

- benchmark tool/version;
- comparability contract;
- matched and unmatched assumptions.

#### 6.3 Ablation/failure study

- exposure integration;
- normalization;
- jitter;
- priors;
- provenance mismatch;
- inadequate MCMC;
- sampler-pass/PPC-fail case.

#### 6.4 Multi-target validation

- target-selection protocol;
- regimes;
- no-cherry-picking policy.

#### 6.5 Correlated-noise study (if completed)

- M6 covariance/process;
- synthetic validation;
- observational application.

### 7. Results

Keep results in protocol order. Do not organize around only positive findings.

Required publication-quality outputs should include:

- calibration/coverage plot with uncertainty;
- posterior bias/RMSE by scenario;
- gate-pass/failure matrix;
- external benchmark posterior comparison;
- ablation effect-size table;
- multi-target regime summary;
- residual/autocorrelation comparison M5 vs M6 if applicable;
- one concise real-data Kepler-10 b posterior/fit figure as anchor rather than the entire paper.

### 8. Discussion

- what is demonstrated vs merely plausible;
- where posterior uncertainty is calibrated;
- consequences of ablations;
- interpretation of external benchmark agreement/disagreement;
- supported vs unsupported observational regimes;
- relation to existing exoplanet fitting software;
- cost of stronger validation/reproducibility;
- scientific limits and threats to validity.

### 9. Reproducibility and availability

- repository release/tag;
- DOI archive;
- exact environment;
- data-source availability;
- artifact manifest;
- commands/workflow for paper figures and tables;
- storage limitations for large traces.

### 10. Conclusion

Answer the methodological question directly. Do not claim general astrophysical superiority unless multi-target/calibration evidence supports it.

## Required figure set

Final names/IDs should be generated from the publication artifact pipeline.

1. End-to-end evidence lineage: public source → RAW → Silver → Gold → inference → gates → paper artifact.
2. Transit-regime/target map including anchor and added targets.
3. Injection–recovery calibration/coverage figure.
4. Bias and uncertainty vs signal/noise regime.
5. Independent benchmark posterior comparison.
6. Ablation/failure-gate matrix.
7. Kepler-10 b physical fit/PPC anchor figure.
8. Multi-target summary.
9. M5 vs M6 correlated-noise result if supported.

## Required tables

1. Model/prior definitions.
2. Data/target regime definitions.
3. Experimental protocols and replication counts.
4. Calibration metrics with uncertainty.
5. Independent benchmark comparability matrix.
6. Ablation effect sizes and gate outcomes.
7. Multi-target outcomes and limitations.
8. Reproducibility manifest summary.

## Reviewer questions the paper must pre-answer

- Why is this needed if `juliet`/`allesfitter` already exist?
- Is the reported novelty a software-engineering artifact or a scientific method contribution?
- Are calibration conclusions based on enough simulations?
- Were scenario/target choices fixed before seeing results?
- Does the simulator share so much code with inference that injection–recovery becomes circular?
- Is external benchmark comparability genuine?
- Are priors still effectively injecting the desired answer?
- How are failed targets/runs handled?
- Why these validation thresholds?
- Do gates reject meaningful failure cases or merely restate known diagnostics?
- What evidence supports generalization beyond Kepler-10 b?
- Does a GP/correlated model absorb astrophysical signal?
- Can an independent researcher reproduce the paper from the released artifacts?

The implementation and experiments should be designed so these questions have quantitative answers before submission.