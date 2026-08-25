# Final Scientific Experiment Protocol — TEMPLATE

> Copy this file to a new protocol-specific path before any final experiment batch. Replace every placeholder. Commit the completed protocol before final runs start.

## Metadata

- `experiment_id`: `<PUB-XX>`
- `protocol_version`: `<1.0.0>`
- `protocol_status`: `DRAFT | FROZEN | AMENDED`
- `protocol_commit`: `<filled after freeze>`
- `date_frozen_utc`: `<YYYY-MM-DDTHH:MM:SSZ>`
- `owner`: `<author/agent>`
- `related_phase`: `<P0-P8>`

## Scientific question

State one primary question that can be answered by the declared experiment.

## Hypothesis / expected failure mode

State the scientific hypothesis or, for a negative control, the failure behavior expected before seeing final results.

## Primary outcomes

List the exact metrics that determine the primary interpretation.

Example categories:

- posterior bias;
- empirical credible-interval coverage;
- standardized posterior shift;
- PPC metric;
- gate pass/fail rate;
- external posterior compatibility.

## Secondary outcomes

List exploratory/supporting metrics. Do not later promote a secondary metric to the sole primary conclusion without recording an amendment.

## Dataset / target / scenario selection

Define the selection rule and final frozen set.

- targets/scenarios:
- data source:
- dataset IDs if known:
- cadence/exposure requirements:
- inclusion criteria:
- exclusions fixed in advance:

## Generative model / truth (synthetic experiments only)

- truth config path:
- transit model:
- noise/systematics:
- segment structure:
- exposure integration:
- truth parameters:
- generative seed policy:

State how truth artifacts are isolated from inference.

## Inference model

- model family/version:
- likelihood:
- period/eccentricity treatment:
- limb darkening:
- exposure integration:
- jitter/correlated-noise behavior:
- derived parameter definitions:

## Priors

For each important parameter record distribution, units, support, scale and justification.

## Sampling configuration

- sampler:
- draws:
- tune:
- chains:
- cores:
- target_accept:
- seed policy:
- other settings:

## Replication plan

For aggregate/simulation experiments:

- number of scenarios:
- final replicates per scenario:
- total attempted final runs:
- pilot runs excluded from final analysis:

If replication count is below the master-plan recommendation, justify the precision/power/calibration uncertainty **before** final execution.

## Diagnostic gates

### Data/provenance

Define required dataset/input/provenance identities.

### Sampler

Define R-hat/ESS/divergence/BFMI or other thresholds.

### Posterior predictive

Define PPC/residual adequacy metrics and acceptable ranges where pre-specification is scientifically justified.

### Scientific interpretation

Define physical/scale/boundary/identifiability rules.

## Failed/missing-run policy

State exactly how failures enter denominators and aggregate summaries.

Default: preserve every declared attempt; do not silently exclude failures.

## Statistical analysis

Specify:

- estimands;
- aggregate statistics;
- uncertainty intervals for aggregate metrics;
- multiple-comparison handling if relevant;
- formal model-comparison conditions;
- treatment of unreliable PSIS/Pareto-k diagnostics;
- definitions of practical equivalence/compatibility if used.

## Planned outputs

### Machine-readable

- configs:
- run registry:
- aggregate tables:
- diagnostics:
- checksums:

### Figures

List planned figures before final results.

### Human-readable report

State report path/structure.

## Interpretation rules

Write the allowed conclusions for each major outcome pattern, including negative outcomes.

Example:

- sampler passes + coverage calibrated -> supports inferential calibration in this scenario;
- sampler passes + systematic undercoverage -> numerical convergence does not imply calibrated uncertainty;
- benchmark discrepancy with unmatched priors -> cannot attribute difference to implementation alone;
- LOO Pareto-k warning -> retain values for audit but do not promote ranking.

## Stop / invalidation conditions

Define implementation bugs or protocol violations that invalidate the final batch and require a new protocol/run ID.

## Amendment log

| version | date | change | reason | final runs already started? | impact on previous evidence |
|---|---|---|---|---|---|

No amendment may erase the previous version/history.

## Freeze declaration

When ready for final execution, change `protocol_status` to `FROZEN`, commit this file, and record that commit in `.agents/EXPERIMENT_REGISTRY.md` before running the final batch.