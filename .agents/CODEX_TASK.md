# Master Codex Task — Publication-Grade Scientific Validation

Use the repository skill `$publication-grade-research` and treat `AGENTS.md`, `.agents/PUBLICATION_PLAN.md`, `.agents/EXPERIMENT_REGISTRY.md`, and `.agents/PAPER_BLUEPRINT.md` as mandatory instructions.

## Starting point

This branch starts from validated `main` commit:

`7489a90689a753bea5243f86c1489329916c98e2`

The current canonical observational baseline is Kepler-10 b run `scientific_003`. Preserve it. Do not rewrite existing validated or failed historical runs in place.

## Objective

Upgrade the repository from a scientifically hardened TCC artifact into a publication-grade research workflow capable of supporting both:

1. a 10/10-level MBA TCC; and
2. a peer-reviewable scientific paper.

The target contribution is not merely another Bayesian transit fitter. The repository should empirically demonstrate a **validation-gated, content-addressed, reproducible Bayesian workflow for exoplanet transit inference**, with known-truth calibration, independent external benchmarking, controlled failure/ablation evidence, multi-regime real-target validation, and — after those are complete — a validated correlated-noise extension.

## Non-negotiable behavior

- Read all mandatory context before substantial work.
- Follow phase dependencies in `.agents/PUBLICATION_PLAN.md`.
- Protocols must be committed before final experiment batches.
- Pilot/debug runs must be labeled and excluded from final claims unless explicitly allowed by protocol.
- Never cherry-pick successful targets, seeds, replicates or benchmark tools.
- Never tune priors/results to match catalog/literature values.
- Never weaken gates because a final result is inconvenient.
- Preserve failed, rejected and non-interpretable runs as evidence.
- Generate aggregate reports from all declared experiment entries, including failures according to protocol.
- Keep machine-readable artifacts, reports and manuscript claims synchronized.

# Execution program

## Phase P0 — Publication baseline and experiment infrastructure

Read `$publication-grade-research`, `$reproducibility-testing-ci`, and `$documentation-artifact-consistency`.

Implement:

- machine-readable publication baseline manifest containing base commit, canonical Gold dataset identity, M5 input hash, model version, environment identity and canonical `scientific_003` artifact references;
- publication experiment schema/status model;
- stable experiment/scenario/replicate/run IDs;
- protocol amendment log;
- publication experiment inventory generator;
- collision protection so new publication runs cannot overwrite historical/current baseline artifacts;
- tests for baseline identity, immutability assumptions and registry completeness.

Update `.agents/EXPERIMENT_REGISTRY.md` only after acceptance criteria are demonstrated.

## Phase P1 — Literature/novelty map and frozen protocols

Read `$literature-novelty-positioning`.

Before final scientific experiments:

- build a current cited novelty matrix covering `exoplanet`, `juliet`, `allesfitter`, related transit inference, injection-recovery/SBC, correlated-noise methods and reproducible astronomical workflows;
- identify exactly which contribution is new vs integrated/reimplemented;
- create protocol files for PUB-02, PUB-03 and PUB-04 before their final runs;
- define final metrics, scenario grids, inclusion/failure rules, sampling configuration and planned outputs;
- create a machine-readable protocol format where practical.

Do not use `first/novel/unprecedented` wording without evidence.

## Phase P2 — Synthetic injection–recovery and calibration

Read `$simulation-calibration-injection-recovery` plus `$bayesian-scientific-validation`.

Implement a publication-grade synthetic simulator with separated truth and inference configs. Support physical limb-darkened exposure-integrated transit, multiple segments, heteroscedastic errors, white jitter, optional correlated stochastic perturbation and deterministic systematic perturbation.

Build a predeclared scenario grid spanning at least:

- deep/high-SNR transit;
- intermediate transit;
- Kepler-10-like shallow transit;
- near-detection-limit transit;
- shallow transit with mild temporal correlation;
- shallow transit with stronger temporal correlation.

Use pilot runs only to validate implementation/compute feasibility. Freeze the final grid and replication count before the final batch. Target at least 100 final realizations per core scenario when computationally feasible; if using fewer, justify calibration precision before running the batch.

For final replicates report:

- posterior bias;
- RMSE/error;
- empirical 50%, 80% and 94% interval coverage with finite-sample uncertainty;
- interval width/sharpness;
- valid rank/SBC-style diagnostics where appropriate;
- sampler/PPC/scientific gate pass rates;
- all failed/missing runs and reasons.

The inference process must not read ground-truth artifacts. Add tests for that separation and for aggregate denominators.

## Phase P3 — Independent published implementation benchmark

Read `$independent-benchmark-validation`.

Evaluate current `juliet` and `allesfitter` compatibility and choose at least one benchmark based on scientific/engineering fit **before** comparing final posterior outcomes.

Use an isolated locked benchmark environment.

Create and freeze a comparability contract covering:

- same observational input/hash;
- time convention;
- period/eccentricity;
- limb-darkening law/priors;
- exposure integration;
- `Rp/Rs`, `b`, `a/Rs` definitions;
- jitter/noise model;
- likelihood;
- prior support/scale.

Run the final benchmark without agreement-driven tuning. Compare full posterior behavior where possible, not only point estimates. Investigate and preserve disagreement.

## Phase P4 — Ablations and failure-gate evidence

Read `$ablation-failure-validation`.

Implement controlled final experiments for at least:

1. exposure integration on/off;
2. segment normalization vs inappropriate/global alternative;
3. inferred jitter vs no jitter;
4. baseline vs pathological/over-informative priors;
5. invalid provenance/dataset identity rejection;
6. deliberately inadequate MCMC rejection;
7. a case where sampler diagnostics pass but PPC/scientific adequacy fails.

Generate a quantitative failure matrix with separate data/provenance, sampler, PPC, scientific and final-interpretability columns.

The paper must be able to show, empirically, that `sampler_converged != scientifically_interpretable`.

## Phase P5 — Multi-target/multi-regime validation

Read `$multi-target-generalization` and `$data-pipeline-integrity`.

Keep HAT-P-7 b and Kepler-10 b as fixed anchor targets. Define pre-result criteria for additional systems representing distinct regimes (depth/SNR, cadence sensitivity, geometry, stellar noise, etc.). Normally attempt at least five real targets total.

Do not replace failed systems silently. Every preselected target must appear in the final outcome table with its status/failure reason.

Keep one shared target-safe pipeline/model implementation.

## Phase P6 — M6 correlated-noise model

Read `$correlated-noise-modeling` and `$bayesian-scientific-validation`.

Only start this phase after P2–P4 are scientifically complete.

Create a separate M6 model family/version with explicit temporal covariance/GP semantics. Do not change M5's white-jitter meaning.

Validate in this order:

1. covariance/kernel unit semantics;
2. white-noise synthetic controls;
3. correlated-noise synthetic injections;
4. repeated M5 vs M6 known-truth calibration;
5. residual/autocorrelation/PPC comparison;
6. observational application.

Explicitly test signal absorption and unnecessary uncertainty under white-noise controls. Formal LOO/WAIC ranking is secondary and allowed only when diagnostics support it.

## Phase P7 — Publication release and paper artifacts

Read `$paper-reproducibility-release`.

Implement:

- `REPRODUCIBILITY_MANIFEST.json` generation;
- one entry point for all paper-critical figures/tables;
- stale-source/hash rejection for paper artifacts;
- complete experiment-to-paper traceability;
- `CITATION.cff` when author metadata is known;
- public-release safety/licensing/secret scan;
- release notes and archival/Zenodo DOI workflow documentation;
- clean reproduction/reporting for the final tagged paper release.

Do not create the final paper tag until all release gates pass.

## Phase P8 — TCC and manuscript synthesis

Use `.agents/PAPER_BLUEPRINT.md` and `$documentation-artifact-consistency`.

Update the TCC with the strongest completed evidence, prioritizing P2–P4. Prepare a journal-agnostic manuscript source whose numerical claims are generated or cross-validated from final experiment artifacts.

The paper should lead with methodology/evidence reliability, not with “we re-estimated Kepler-10 b”.

# Required status discipline

For every phase:

1. inspect current state;
2. write/freeze protocol before final runs;
3. implement with focused tests;
4. run pilots if needed;
5. freeze final configuration;
6. run final batch;
7. inspect machine-readable results and failures;
8. generate aggregate reports from the full declared registry;
9. update `.agents/EXPERIMENT_REGISTRY.md` with evidence;
10. update documentation/manuscript only after evidence is valid.

Do not mark a phase `COMPLETED` because code exists. Completion requires verified final evidence.

# Completion standard

Stop only when the repository can answer a skeptical reviewer with reproducible evidence:

- Are intervals calibrated under known truth?
- Does an independent implementation broadly corroborate the inference, or can differences be explained?
- Which preprocessing/model choices matter quantitatively?
- Can the validation gates catch real failure modes?
- Where does the method fail across preselected targets/regimes?
- Does correlated-noise modeling help when correlation exists without harming simple cases?
- Can every paper table/figure be regenerated from frozen, content-identified evidence?
- Were failed runs and unfavorable cases preserved?
- Are novelty claims actually supported by current literature?

Do not stop at “the code runs”. Stop when the **evidence chain is strong enough for peer review**.