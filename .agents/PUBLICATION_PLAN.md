# Publication-Grade Scientific Validation Plan

## Mission

This branch upgrades the repository from a strong, defensible MBA TCC artifact into a publication-grade scientific workflow.

The baseline is the validated `main` state at commit `7489a90689a753bea5243f86c1489329916c98e2`. The current Kepler-10 b `scientific_003` result remains the reference baseline until a later experiment legitimately supersedes it. Nothing in this program may retroactively rewrite a failed or historical result into a successful one.

The scientific objective is broader than fitting a transit. The repository must demonstrate, with controlled experiments, that its conclusions are trustworthy because:

1. known injected truths can be recovered with calibrated uncertainty;
2. an independent implementation reaches compatible inferences under comparable assumptions;
3. key preprocessing/modeling decisions survive or fail transparent ablation tests;
4. the method behaves across deliberately different observational regimes rather than one favorable target;
5. correlated-noise limitations are tested explicitly and, if implemented, modeled with a scientifically justified extension;
6. provenance, diagnostics, posterior predictive adequacy, and scientific interpretation gates prevent invalid runs from being promoted to evidence;
7. every major result can be regenerated from versioned inputs, configuration, environment and experiment definitions.

The desired paper contribution is not merely “Bayesian transit fitting”. It is a **validation-gated, content-addressed, reproducible Bayesian workflow for exoplanet transit inference**, with empirical evidence that the validation contracts detect failure and that posterior uncertainty is calibrated in controlled settings.

---

## Scientific operating rules

These rules are mandatory for every phase.

### No result-driven protocol changes

- Define hypotheses, scenario grids, primary metrics and success/failure criteria before running the final experiment batch.
- Pilot runs may be used to debug code and estimate compute cost, but pilot outputs must be labeled `pilot` and excluded from final scientific claims unless the protocol explicitly permits otherwise.
- Do not remove a target/scenario because the result is inconvenient. If a run fails, preserve and classify it.
- Do not tighten priors, alter preprocessing, change seeds or modify gates merely to improve agreement with catalog/literature values.
- Any protocol amendment after final runs begin must be recorded with reason, date, affected experiments and whether the change invalidates prior outputs.

### Separate implementation debugging from scientific evidence

- Unit/smoke tests may use tiny samples and relaxed sampling.
- Scientific runs must use their declared production sampling configuration and pass the applicable sampler/PPC/scientific gates.
- A numerically converged result is not automatically physically valid.

### Preserve full provenance

Every experiment must record at minimum:

- experiment family and `experiment_id`;
- target or synthetic scenario identifier;
- dataset ID and input SHA-256;
- source FITS SHA-256 where observational data are used;
- model version and likelihood identity;
- prior profile/version;
- sampler settings and random seeds;
- software environment identity;
- code commit SHA;
- run status and gate status;
- output checksums for publication-critical tables/figures.

### Negative results are results

Failed calibration, poor convergence, disagreement with an external implementation, Pareto-k warnings, target-specific failures, and correlated residuals must be reported rather than hidden. A publication-grade repository should be capable of saying “this configuration is not supported by the evidence”.

---

# Roadmap

## P0 — Freeze the validated baseline and publication contract

### Purpose

Protect the already validated TCC result while establishing a new experiment namespace and research protocol.

### Work

- Record the base commit and the canonical `scientific_003` identifiers in a machine-readable publication baseline manifest.
- Add experiment schemas for publication studies without altering historical artifact semantics.
- Add explicit statuses: `planned`, `pilot`, `running`, `completed`, `failed`, `rejected`, `not_interpretable`.
- Add a publication experiment registry generated from machine-readable configs.
- Ensure future publication runs never overwrite `scientific_003` or historical M1–M5 artifacts.
- Create a protocol-amendment log.

### Acceptance criteria

- Baseline manifest reproduces exact dataset/model/input identities from `main`.
- Historical artifacts remain byte-identical unless documentation-only references are added.
- New publication experiments are isolated by family/target/scenario/run ID.
- Tests fail on output-path collision, missing experiment identity or baseline mutation.

---

## P1 — Novelty map and pre-registered experiment protocols

### Purpose

Prevent the paper from making a novelty claim that already exists in the literature and prevent final experiments from being tuned after observing outcomes.

### Work

Create a structured literature/novelty matrix covering at least:

- `exoplanet`;
- `juliet`;
- `allesfitter`;
- PyMC/HMC/NUTS transit workflows;
- Kepler/TESS transit pipelines;
- injection-recovery and simulation-based calibration in exoplanet inference;
- correlated-noise/GP methods for photometric time series;
- reproducible scientific software/provenance workflows in astronomy.

For each planned study, create a protocol before final runs:

- question/hypothesis;
- datasets/scenarios;
- exclusions known in advance;
- priors;
- sampler configuration;
- primary and secondary metrics;
- diagnostic gates;
- interpretation rules;
- planned figures/tables.

### Acceptance criteria

- No “first”, “novel”, or “unprecedented” claim exists without a cited novelty matrix entry.
- Every final experiment has a committed protocol file created before the final result artifact.
- Protocol changes are traceable.

---

## P2 — Synthetic injection–recovery and calibration

### Scientific question

When the generative truth is known, does the workflow recover scientifically relevant transit parameters with calibrated uncertainty across signal-to-noise regimes?

### Required simulator

Implement a synthetic-data generator that uses an independently declared generative configuration and records the exact hidden/ground-truth parameters. The simulator should support:

- physical limb-darkened transit;
- exposure-time integration;
- multiple observational segments;
- heteroscedastic measurement error;
- independent Gaussian jitter;
- optional correlated stochastic perturbations;
- optional deterministic systematic signals;
- configurable cadence and transit depth.

The inference configuration must not silently read the ground-truth file.

### Core scenario grid

At minimum include scientifically distinct regimes such as:

1. deep/high-SNR transit;
2. intermediate transit;
3. Kepler-10-like shallow transit;
4. near-detection-limit shallow transit;
5. shallow transit with mild temporal correlation;
6. shallow transit with strong temporal correlation.

The final numerical values of the grid must be committed before the final batch.

### Final-study design

- Use an explicit pilot phase for debugging only.
- Use repeated independent datasets per scenario.
- Target at least 100 final realizations per core scenario if computationally feasible; if fewer are used, justify the statistical precision of calibration estimates before running the final batch.
- Use deterministic seed derivation from `(experiment_id, scenario_id, replicate_id)` while preserving independence between simulated datasets.
- Do not reuse posterior draws between replicates.

### Primary metrics

For `Rp/Rs`, depth, duration, `b`, `a/Rs`, and other protocol-designated quantities:

- posterior bias;
- absolute/relative error of posterior center;
- RMSE across replicates;
- empirical coverage of 50%, 80%, 94% credible intervals;
- interval width/sharpness;
- rank or SBC-style calibration diagnostics where technically valid;
- sampler gate pass rate;
- posterior-predictive gate pass rate;
- scientific interpretation pass rate.

Coverage must be reported with binomial uncertainty. Do not declare exact calibration merely because observed coverage is numerically close to nominal.

### Key failure interpretation

A case where the sampler converges but interval coverage is systematically poor is an important negative result and must be retained.

### Acceptance criteria

- Ground truth and inference inputs are structurally separated and tested.
- Simulator reproduces its declared injected signals numerically.
- Final calibration report is generated from all declared replicates, including failures.
- Missing/failed runs cannot be silently excluded from denominators.
- Coverage uncertainty and scenario-specific limitations are explicit.

---

## P3 — Independent external benchmark

### Scientific question

Does an independently developed, published exoplanet-inference implementation obtain compatible posterior conclusions from the same observational task under meaningfully comparable assumptions?

### Tool selection

Evaluate current compatibility and scientific fit of at least `juliet` and `allesfitter`. Select at least one as the primary external benchmark and document the decision. Do not select the implementation based on which agrees best with this repository.

The external benchmark should use its own isolated environment to avoid contaminating the validated repository environment.

### Benchmark contract

Match, as closely as the external implementation permits:

- observations;
- cadence/exposure handling;
- period/eccentricity assumptions;
- limb-darkening law/parameterization;
- prior support and scale;
- jitter/noise assumptions;
- likelihood family.

Where exact equivalence is impossible, record the mismatch as part of the result.

### Primary comparisons

Compare at minimum:

- `Rp/Rs`;
- depth;
- impact parameter;
- `a/Rs`;
- transit center;
- full duration;
- uncertainty widths;
- predictive residual structure.

Use distribution-aware comparison, not only mean differences. Candidate summaries include overlapping credible mass, standardized posterior-center differences, interval overlap and predictive discrepancies.

### Acceptance criteria

- External environment and exact version are locked.
- Same Gold dataset/input identity is used whenever scientifically possible.
- No benchmark-specific tuning is performed to force agreement.
- Both agreement and disagreement are reportable outcomes.
- A benchmark report clearly separates implementation differences from scientific disagreement.

---

## P4 — Ablation and failure-mode validation

### Scientific question

Which pipeline/model decisions materially protect the inference, and do validation gates block configurations that should not be interpreted scientifically?

### Required ablations

At minimum test:

1. **Exposure integration**: integrated forward model vs instantaneous-sample approximation.
2. **Normalization**: per-segment normalization vs inappropriate global normalization or a clearly specified alternative.
3. **Jitter**: measured error + inferred jitter vs measured error only.
4. **Prior information**: baseline priors vs deliberately over-informative/pathological controls.
5. **Segment/provenance integrity**: intentionally invalid/mismatched dataset identity must be rejected before interpretation.
6. **Sampler insufficiency**: deliberately inadequate sampling must fail numerical gates.
7. **Posterior predictive inadequacy**: construct at least one case where sampler diagnostics are acceptable but predictive/scientific adequacy is not.

Additional ablations may evaluate thinning strategy, phase-window definition and target-specific cadence policy if scientifically justified.

### Primary result

Produce a failure matrix demonstrating that different gates answer different questions:

| condition | data/provenance | sampler | PPC | scientific | interpretation |
|---|---|---|---|---|---|

The paper must be able to demonstrate empirically that `sampler_converged != scientifically_interpretable`.

### Acceptance criteria

- Each ablation changes one declared factor at a time where feasible.
- All negative controls are labeled before results are examined.
- Gates are not weakened merely to make a control pass.
- Quantitative parameter shifts and predictive effects are reported, not only pass/fail labels.

---

## P5 — Multi-target, multi-regime generalization

### Scientific question

Across which observational regimes does the workflow remain scientifically interpretable, and where does it fail?

### Target-selection protocol

Select targets by predeclared scientific criteria rather than by posterior quality. HAT-P-7 b and Kepler-10 b remain fixed anchor targets. Add enough systems to represent at least the following contrasts where public data quality permits:

- deep hot-Jupiter-like transit;
- shallow rocky/small-planet transit;
- intermediate-depth transit;
- long-exposure/cadence-sensitive case;
- challenging geometric or near-grazing case;
- comparatively noisy stellar/light-curve case.

A single target may satisfy more than one regime, but the final set should normally contain at least 5 distinct systems including the two anchors.

### Rules

- Commit selection criteria and selected targets before final inference.
- Preserve failed targets and explain failure.
- Do not replace failed targets with easier ones without logging the protocol amendment.
- Use the shared target-safe pipeline rather than target-specific model copies.

### Cross-target metrics

- scientific gate pass/fail and reason;
- posterior/catalog scale comparison with independence caveats;
- predictive residual diagnostics;
- uncertainty width relative to transit scale;
- computational cost;
- sensitivity to cadence/exposure policy.

### Acceptance criteria

- At least five distinct targets are attempted under the committed protocol, unless data-access/scientific constraints documented before final analysis justify a smaller final set.
- No target is omitted from the final summary because of an unfavorable result.
- Target-specific values remain centralized in authoritative configuration/provenance.

---

## P6 — M6 correlated-noise extension

### Scientific question

When residuals exhibit temporal correlation, does an explicitly correlated likelihood improve calibration or predictive adequacy relative to M5, and when is the simpler white-jitter model sufficient?

### Model requirement

Implement a separate model version/family rather than silently changing M5 semantics.

Conceptually:

`y ~ Normal(mu(theta), K_phi + Sigma_measurement)`

where `K_phi` is a declared temporal covariance/process and `Sigma_measurement` contains known heteroscedastic measurement variance plus any justified white-jitter term.

Evaluate a computationally appropriate GP/celerite-style implementation. Kernel/process choice must be justified and must not be selected solely because it improves one final target.

### Validation order

1. unit-test kernel/covariance semantics;
2. synthetic white-noise control;
3. synthetic correlated-noise injection;
4. calibration/injection-recovery comparison M5 vs M6;
5. observational application only after synthetic validation.

### Comparison

Compare M5/M6 using:

- calibration under known truth;
- residual autocorrelation;
- PPC;
- posterior shifts;
- interval calibration/sharpness;
- LOO/WAIC/ELPD only when formal-comparison assumptions and diagnostics are valid.

Do not promote a ranking when PSIS diagnostics are unreliable.

### Acceptance criteria

- M5 remains explicitly a white-jitter model.
- M6 artifacts declare the correlated likelihood and kernel/process.
- Synthetic correlated cases demonstrate whether M6 actually improves recovery/calibration.
- White-noise controls demonstrate whether M6 unnecessarily absorbs transit signal or creates unhelpful uncertainty.

---

## P7 — Paper-grade reproducibility and public scientific release

### Purpose

Turn the repository into a citable research object, not merely a GitHub project.

### Work

- Add `CITATION.cff` with publication/repository metadata when final author/title details are known.
- Add release-specific `REPRODUCIBILITY_MANIFEST.json` tying commit, datasets, environments, protocols, result hashes, tables and figures together.
- Create one command/workflow to regenerate all paper-critical derived tables and figures from already versioned/raw inputs and approved run artifacts.
- Create a paper artifact validator that rejects stale figures/tables when their source hashes/configs do not match.
- Archive a final tagged release suitable for Zenodo DOI deposition.
- Document what is and is not included due to file-size/storage policy.
- Include data/software availability statements appropriate for the target journal.
- Preserve failed/negative results needed to reproduce the paper narrative.

### Release gate

Do not tag `v1.0.0-paper` (or equivalent) until:

- all publication-critical protocols are frozen;
- final experiment registry is complete;
- clean rebuild and tests pass;
- paper tables/figures validate against source artifacts;
- citation metadata is complete;
- public-repository review finds no secrets/private material/licensing conflict;
- DOI/archive instructions are ready.

---

## P8 — TCC 10/10 integration and manuscript preparation

### TCC integration

The final TCC should add the strongest completed evidence from P2–P4 at minimum:

- injection–recovery/calibration;
- independent benchmark;
- ablation/failure-gate study.

If P5/P6 are complete before final submission, summarize them without displacing the core mathematical/statistical exposition.

### Paper manuscript

Prepare a journal-agnostic source manuscript first, then adapt to the selected journal template.

Recommended scientific narrative:

1. motivation: inference reliability is broader than sampler convergence;
2. related work and precise novelty claim;
3. content-addressed RAW/Silver/Gold provenance;
4. physical Bayesian transit model and validation gates;
5. synthetic calibration/injection–recovery;
6. independent implementation benchmark;
7. ablation/failure experiments;
8. multi-target generalization;
9. correlated-noise extension if supported;
10. limitations and supported scope;
11. reproducibility/release statement.

The headline result must not be “we estimated Kepler-10 b”. The paper should demonstrate a reusable validation methodology and state exactly where it succeeds or fails.

---

# Current execution handoff (2026-09-26)

The user's latest instruction overrides long-running agent execution: prepare,
test and commit an autonomous campaign runner, then let the user launch finals.
`configs/publication/tcc_final_campaign.json` and its frozen job/seed ledger
implement P2→P3→P4→P5 within a soft36h planning envelope. Four main P2 regimes
have20 replicates each; P4 has3 paired realizations; all5 selected targets remain.
OU exploration and P6/M6 are deferred before results for deadline/compute reasons,
not marked scientifically completed. See `docs/publication/COMPUTE_BUDGET_AMENDMENT.md`.
Runner readiness does not satisfy the scientific definition of done below;
coverage, external agreement and generalization remain open empirical questions.

Runner handoff acceptance is verified by
`publication/validation/handoff/handoff_v5/validation.json`: 204 practical tests,
zero skips, lint/static checks, historical artifact checks, final dry-run/status,
and recursive report freshness passed. `runner_smoke_v2` separately verifies
real physical smoke inference, deliberate interruption, resume, idempotence,
technical retry preservation and scientific rejection without retry. See
`reports/PUBLICATION_CAMPAIGN_HANDOFF.md` for the delivered/pending distinction.

After that validation and infrastructure commit, the user explicitly authorized
immediate launch in a visible terminal. The campaign began at
`2026-09-26T20:18:21.225846+00:00`, in WSL/tmux, without changing the frozen design.
See `docs/publication/CAMPAIGN_LAUNCH.md`; current progress comes only from the
campaign state/journal. Handoff reports retain their pre-launch snapshot status.

# Phase dependencies

Post-campaign update (2026-09-30): both user-authorized campaigns finished.
The evidence synthesis is `reports/publication_synthesis/tcc_evidence_v1/`.
Execution completion yielded mixed/negative scientific results, including
low-information undercoverage, local benchmark mode trapping and all-target
temporal PPC rejection. See the updated experiment registry and scientific
reviews. The frozen batches are preserved; P6 remains deferred and P7 is not
release-approved. The prelaunch handoff above is historical, not current status.

`P0 -> P1 -> P2 -> P3 -> P4 -> P5 -> P6 -> P7 -> P8`

Parallel work is allowed only when it does not create protocol leakage:

- literature mapping may continue while P0 infrastructure is built;
- external benchmark adapter development may start during synthetic simulator work, but final benchmark configuration must be frozen before final benchmark runs;
- paper prose may be drafted early, but Results/Discussion claims must be regenerated from the final experiment registry.

Do not start P6 merely because it is technically interesting while P2–P4 remain incomplete. Ground-truth calibration and independent validation have higher publication value than adding model complexity.

---

# Publication-grade definition of done

This program is complete only when all of the following are supported by machine-readable evidence:

- baseline `scientific_003` remains traceable and unchanged;
- final protocols predate final scientific result batches;
- repeated synthetic experiments quantify bias, uncertainty and credible-interval calibration;
- at least one independent published implementation is benchmarked under a documented comparability contract;
- ablations quantify why key pipeline/model decisions matter;
- validation gates demonstrably reject known invalid conditions;
- at least five real targets/regimes are attempted without cherry-picking, unless a pre-result protocol documents a justified alternative;
- correlated noise is either explicitly modeled and validated or retained as a clearly bounded limitation;
- every publication-critical table/figure traces to configs/data/result hashes;
- clean rebuild, CI and artifact validation pass;
- failed and negative results remain auditable;
- a public release can be archived with a persistent DOI;
- the manuscript makes only novelty and scientific claims that the experiment registry and literature matrix support.

The standard is not “more sophisticated code”. The standard is **stronger, pre-specified, reproducible evidence**.
