# AGENTS.md

## Mission

This repository is scientific software. Treat scientific correctness, reproducibility, provenance, explicit assumptions, honest uncertainty, calibration, external validation, and failure transparency as first-class requirements.

On branch `publication-grade-validation`, the mission is no longer merely to harden a TCC repository. The validated `main` state is the protected baseline. The goal of this branch is to build enough pre-specified, reproducible evidence for:

1. a top-quality MBA TCC;
2. a defensible scientific manuscript suitable for peer-review submission;
3. a public, citable research-software/data artifact.

The intended methodological contribution is a **validation-gated, content-addressed and reproducible Bayesian workflow for exoplanet transit inference**, supported by synthetic calibration, independent implementation benchmarking, controlled ablations/failure cases, multi-target validation, and — only after those are solid — explicit correlated-noise modeling.

Do not optimize for impressive complexity. Optimize for stronger evidence.

## Required starting context

Before substantial work on this branch, read in order:

1. `AGENTS.md` completely.
2. `.agents/PUBLICATION_PLAN.md` completely.
3. `.agents/EXPERIMENT_REGISTRY.md`.
4. `.agents/PAPER_BLUEPRINT.md`.
5. `.agents/REMEDIATION_PLAN.md` as historical/baseline hardening context.
6. The relevant skill(s) under `.agents/skills/`.
7. Current executable code, configurations and generated artifacts relevant to the task.

Do not assume historical docs are current. The validated baseline and current machine-readable evidence take precedence.

## Protected baseline

The publication branch starts from validated `main` commit:

`7489a90689a753bea5243f86c1489329916c98e2`

The current primary scientific baseline is Kepler-10 b run `scientific_003`, Gold dataset `kepler_10_b-b4d1e6ec961c1f4d`, M5 input SHA-256 `6653fced1df0b3a29be96d181daa695f86ef709a7aa459bc1b3f837d48ad8791`.

Do not rewrite this historical evidence in place. New experiments require new experiment/run IDs. If a later model supersedes a result, preserve both and state the relationship explicitly.

## Source-of-truth hierarchy

When sources disagree, reconcile them explicitly. Default hierarchy:

1. Current executable code and authoritative configuration.
2. Current raw inputs and machine-readable manifests/checksums.
3. Frozen experiment protocols and experiment registry.
4. Generated model configuration, summaries, diagnostics, traces and aggregate experiment artifacts.
5. Tests and reproducible validation scripts.
6. Human-readable reports/notebooks/manuscripts.
7. Historical context exports.

This hierarchy is not permission to leave documentation stale. Final publication artifacts must agree with code/config/evidence.

# Publication-grade research rules

## Protocol before final results

Before starting a final scientific batch:

- define the scientific question/hypothesis;
- freeze scenario/target selection;
- freeze primary outcomes and secondary metrics;
- freeze priors/model/likelihood and sampler settings;
- freeze inclusion/exclusion and failed-run handling;
- freeze diagnostic/interpretation rules;
- commit the protocol;
- register the experiment as `PLANNED`.

Pilot/debug runs must be explicitly labeled `PILOT` and excluded from final claims unless the protocol says otherwise.

## No cherry-picking or outcome tuning

Never:

- drop a target/scenario because the posterior is unfavorable;
- choose an external benchmark because it agrees best;
- alter priors after seeing final disagreement merely to improve agreement;
- choose the best seed/run among repeated attempts as the scientific result;
- weaken validation thresholds to rescue a negative control;
- silently exclude failed simulation replicates from aggregate denominators;
- delete failed runs that are relevant to the evidence trail.

If a protocol must change after final runs begin, record an amendment with reason and impact.

## Negative evidence is first-class evidence

Poor calibration, non-convergence, failed PPC, external disagreement, invalid LOO diagnostics, target-specific failure, model misspecification and correlated residuals are publishable findings when generated under a defensible protocol.

The repository must be capable of saying “not supported” or “not interpretable”.

## Evidence promotion

A positive scientific result may be promoted to TCC/paper evidence only when:

1. the relevant protocol predates the final batch;
2. data/provenance identity is valid;
3. the run/batch completed under the declared configuration;
4. sampler/PPC/scientific gates pass where required;
5. aggregate reports account for all declared attempts according to protocol;
6. result artifacts are machine-readable and traceable;
7. human-readable claims match the artifacts.

Negative/failure-control claims can rely on deliberately rejected runs when classification and interpretation are correct.

# Scientific invariants inherited from hardening

## RAW

- RAW data is immutable source evidence. Never silently normalize, clean, rewrite or replace original downloaded content.
- Every RAW artifact used downstream must preserve source/path/status/checksum provenance.
- Distinguish history/event logs from current-state manifests.

## Silver

- Silver may standardize schema/types but must preserve traceability to RAW.
- Units must be explicit in names or machine-readable metadata.
- Unit conversions must be documented and tested.

## Gold

- Preserve segment/product/cadence/exposure identity through scientifically necessary preprocessing.
- Do not treat segment offsets as astrophysical noise.
- Normalization/detrending must be explicit, reproducible, parameterized and recorded.
- Dataset identity must remain content/provenance-bound.

## Bayesian inference

- MCMC convergence is not physical validity.
- Priors, likelihood, units, target assumptions, preprocessing and documentation must describe the same model.
- Do not claim correlated/red-noise handling when the likelihood only contains independent white jitter.
- Record R-hat, ESS, divergences, BFMI where applicable, PPC diagnostics and relevant scientific scale checks.
- Add/use pointwise log likelihood only when formal model comparison is scientifically valid.
- Catalog/literature values may justify priors and scale checks, but never tune outputs to match them.

## Cadence/exposure

- For short transits, evaluate exposure integration explicitly.
- Do not treat long/finite exposures as instantaneous when that approximation materially alters inference.

## Target integrity

- Target-specific values come from authoritative configuration/provenance, not scattered hard-coded literals.
- Shared models remain target-safe.
- Target/run outputs must be isolated.

# Publication phase priority

Default dependency order:

1. **P0** — freeze validated baseline and publication experiment contract.
2. **P1** — current literature/novelty matrix + frozen protocols.
3. **P2** — synthetic injection–recovery and calibration with known truth.
4. **P3** — independent published implementation benchmark.
5. **P4** — ablation and failure-gate validation.
6. **P5** — multi-target/multi-regime validation.
7. **P6** — separate M6 correlated-noise extension, only after P2–P4 are solid.
8. **P7** — paper-grade release, citation metadata, artifact regeneration and DOI readiness.
9. **P8** — integrate strongest evidence into TCC and manuscript.

Do not prioritize P6 over P2–P4 merely because a GP is technically sophisticated. Known-truth calibration and independent validation have greater evidentiary value.

# Experiment-specific requirements

## Synthetic calibration / injection–recovery

- Separate truth/generative config from inference config.
- Inference must not read ground-truth artifacts.
- Use repeated independent realizations under predeclared scenario grids.
- Report bias, RMSE/error, empirical interval coverage at multiple levels, interval width/sharpness, gate pass rates and failed-run counts.
- Report uncertainty on empirical coverage itself.
- Keep model-misspecification scenarios; success must not be guaranteed by construction.

## Independent benchmark

- Evaluate at least `juliet` and `allesfitter` for current suitability, then preselect at least one benchmark before final comparison.
- Lock a separate benchmark environment.
- Create a comparability contract for data, priors, likelihood, geometry, limb darkening, exposure integration and jitter.
- Do not force numerical agreement.
- Preserve unexplained disagreement as a result/limitation.

## Ablations / negative controls

At minimum evaluate:

- exposure integration;
- per-segment vs inappropriate/global normalization;
- jitter vs no jitter;
- baseline vs pathological/over-informative priors;
- provenance/input mismatch rejection;
- inadequate sampler configuration;
- at least one sampler-pass but PPC/scientific-fail case.

Quantify parameter/predictive effects, not only booleans.

## Multi-target validation

- HAT-P-7 b and Kepler-10 b remain anchor targets.
- Add targets by a precommitted regime-selection protocol.
- Normally attempt at least five distinct systems total.
- Failed targets remain in the final table.
- Do not make population-level claims from a small regime-based validation set.

## Correlated noise / M6

- M5 semantics remain white-jitter-only.
- Create a separate M6 model family/version for temporal covariance/GP behavior.
- Validate M6 on synthetic white and correlated controls before applying it to observational data.
- Explicitly test signal absorption/over-flexibility.
- Prefer known-truth calibration over information-criterion ranking as primary evidence.

# Reproducibility and engineering rules

- Keep CLI scripts thin; reusable logic belongs under `src/`.
- Keep experiment configs machine-readable.
- Use stable experiment/scenario/replicate/run identifiers.
- Derive simulation seeds deterministically from stable identifiers while preserving independent datasets.
- Store repository-relative POSIX paths in manifests.
- Pin scientific and benchmark environments separately when needed.
- Expensive final MCMC does not need to run on every CI job; CI should validate contracts using lightweight fixtures/smoke runs.
- Add regression tests for every discovered correctness bug.
- Aggregate reports must be generated from registries/artifacts, never manually curated lists of successful runs.
- Publication-critical figures/tables must be generated from approved machine-readable evidence and fail on stale hashes.

# Documentation/publication rules

- Final TCC/paper numerical text must match machine-readable evidence.
- Do not claim novelty until `.agents/skills/literature-novelty-positioning` work supports the claim.
- Do not call a result externally validated when the same catalog quantity informs its prior; state dependence explicitly.
- Distinguish geometric depth `r^2` from observed limb-darkened depth.
- Distinguish stochastic correlated noise from deterministic systematics.
- Distinguish method-scope validation from population-level astrophysical generalization.
- Update manuscript claims when negative results narrow supported scope.

# Working protocol

For each publication phase/item:

1. read relevant protocol/skill;
2. inspect current code/artifacts;
3. write/freeze protocol before final batch;
4. implement the smallest scientifically coherent extension;
5. add focused tests;
6. run pilot/debug experiments if needed;
7. explicitly freeze final experiment configuration;
8. execute final batch;
9. inspect machine-readable artifacts and failures;
10. generate aggregate report from full declared registry;
11. update `.agents/EXPERIMENT_REGISTRY.md` with status/evidence;
12. update docs/manuscript only from validated outputs.

Do not mark an item complete merely because code was edited or a run finished.

# Skills

Existing hardening skills remain applicable:

- `repository-hardening`
- `data-pipeline-integrity`
- `bayesian-scientific-validation`
- `reproducibility-testing-ci`
- `documentation-artifact-consistency`

Publication-focused skills:

- `publication-grade-research` — coordinating workflow for the complete publication program.
- `literature-novelty-positioning` — current literature matrix and defensible novelty claims.
- `simulation-calibration-injection-recovery` — known-truth simulation, calibration and coverage.
- `independent-benchmark-validation` — external published implementation comparison.
- `ablation-failure-validation` — ablations, negative controls and empirical gate validation.
- `multi-target-generalization` — preselected multi-regime real-target validation.
- `correlated-noise-modeling` — separate M6 GP/covariance extension.
- `paper-reproducibility-release` — paper artifacts, citation metadata, archival/DOI readiness and public-release checks.

When a task spans multiple skills, start with `publication-grade-research` and load focused skills as needed.

# Definition of done

The publication program is not done until the repository can defend, with machine-readable evidence, all final manuscript claims. At minimum:

- baseline evidence is preserved;
- final protocols predate final experiment batches;
- known-truth calibration is quantified with repeated simulations;
- an independent published implementation is benchmarked under a frozen comparability contract;
- ablations quantify important design choices;
- gates demonstrably reject meaningful failure cases;
- multiple preselected real targets/regimes are attempted without cherry-picking;
- correlated noise is either explicitly modeled/validated or retained as a clear limitation;
- every paper-critical table/figure traces to frozen evidence;
- clean rebuild/tests/CI/artifact validation pass;
- failed and negative results remain auditable;
- public release is safe, citable and archival/DOI-ready;
- TCC and paper claims match the final experiment registry.

The stopping criterion is not “the model is sophisticated”. It is **the evidence is strong enough that a reviewer can audit why the conclusions deserve to be trusted**.