# Post-campaign scientific review: PUB-03, PUB-04 and PUB-05

Review date: 2026-09-30. Branch: `publication-grade-validation`.
Evidence cohort: `tcc_campaign_v1`; the separate 400-realization confirmatory
PUB-02 cohort must not be pooled into this cohort or used to overwrite its
outcomes. This is a post-result methodological review, not a new frozen protocol.
No inference, data preparation, gate modification or scientific rerun was
performed for this review. Existing traces and machine-readable results were
read. All negative outcomes remain evidence.

The declared campaign finished, but positive independent validation and useful
multi-target scientific applicability were **not established**. The strongest
completed evidence from these families is the empirical separation between
sampler diagnostics, predictive adequacy and provenance validity. This review
does not revoke or rewrite the historical `scientific_003` gate; the publication
protocol adds temporal residual checks and defines a different promotion rule.

## Sources and audit scope

- Frozen contracts: `publication/protocols/PUB-03.json`, `PUB-04.json`,
  `PUB-05.json`; pre-acquisition selection snapshot `PUB-05-draft.json`.
- Benchmark preselection: `docs/publication/BENCHMARK_SELECTION.md`;
  isolated environment: `publication/environments/benchmark-environment.json`.
- Authoritative attempt paths are enumerated in
  `reports/publication_campaign/tcc_campaign_v1/PUB-03/jobs.csv`,
  `PUB-04/jobs.csv`, and `PUB-05/jobs.csv`.
- Benchmark comparison: `PUB-03/benchmark.json` and
  `PUB-03/posterior_comparison.csv`, relative to that report directory.
- Ablations: `PUB-04/ablation.json`, `gate_matrix.csv`, `paired_effects.csv`.
- Multi-target: `PUB-05/targets.csv`, `posterior_intervals.csv`, `aggregate.json`.
- Per-run diagnostics and gates: each declared attempt's `result.json` under
  `artifacts/publication_campaign/tcc_campaign_v1/runs/`.
- Executable review: `src/publication/inference.py`, `ablations.py`,
  `campaign_reporting.py`, and the shared
  `src/bayesian_modeling/physical_transit.py` model.

This review checked the relation between protocols, reported numbers and
individual results, and inspected the local benchmark posterior trace by chain.
It is not a replacement for the separate complete artifact-hash, environment,
protocol-timing and clean-release validations.

## PUB-03: independent implementation ran; positive compatibility is unsupported

The protocol selected juliet before final comparison and evaluated allesfitter
on likelihood/adapter suitability. The comparison uses exactly 3,000 historical
Kepler-10 b rows with input SHA-256
`6653fced1df0b3a29be96d181daa695f86ef709a7aa459bc1b3f837d48ad8791`.
Both engines use the companion Uniform radius prior, not the historical
`scientific_003` LogNormal prior. Thus this is not a retroactive validation of
that posterior. It shares observations and physical assumptions, and cannot
provide independent astrophysical truth even if numerical agreement is good.

Both declared attempts are `COMPLETED_REJECTED`:

| Engine | Numerical diagnostics | Predictive adequacy | Permitted interpretation |
|---|---|---|---|
| Local exoplanet/PyMC | R-hat 1.52873458; minimum ESS 7.14531027; zero divergences | Temporal residual check fails | Nonconverged posterior; retain comparison descriptively |
| juliet/batman/dynesty | Weighted ESS 3483.5854; log-evidence error 0.257748; natural `dlogz` stop; 390,237 likelihood calls | Temporal residual check fails | Numerically eligible external fit with inadequate white-noise prediction |

The external numerical gate passed and the budget was not exhausted. Its
scientific rejection must not be mislabeled as failed nested sampling.
Pointwise 94% predictive coverage is approximately 0.9343 locally and 0.9323
externally, while lag-one residual correlations are 0.48823 and 0.48800 against
the same approximate reference bound 0.06839. Similar pointwise predictive
coverage therefore did not establish temporal adequacy.

The observed radius-ratio standardized mean difference is 0.07006, its 94%
equal-tailed interval width ratio external/local is 1.11772, and predictive
latent-mean RMS difference is 4.43618 ppm (maximum 23.37269 ppm). These are
descriptive comparisons of retained outputs, not an equivalence test or a
positive validation claim, because the local posterior did not converge.
The predeclared material-discrepancy flag is triggered for `t0`.

### Verified chain separation and initialization hypothesis

The local trace at
`artifacts/publication_campaign/tcc_campaign_v1/runs/PUB-03/kepler_10_b_local/rep_0000/attempt_000/trace.nc`
contains four chains, each with 2,000 retained draws:

| Chain | Mean t0 (day) | 94% equal-tailed t0 interval (day) |
|---|---:|---|
| 0 | -0.8316449975 | [-0.8358327084, -0.8262741354] |
| 1 | 0.0004116573 | [-0.0030506165, 0.0037746714] |
| 2 | 0.0004566725 | [-0.0030250713, 0.0040049930] |
| 3 | 0.0004562305 | [-0.0030374322, 0.0039149082] |

Every retained chain-0 draw remains between -0.8395307864 and -0.8209447234
day. The fixed period is 0.8374907 day. This verifies confinement near an
adjacent orbital alias, with no observed mixing to the central-time region;
it is not merely a plotting or parameter-renaming discrepancy. The combined
t0 94% interval spans [-0.834390746, 0.003648108] day, explaining the extreme
interval-width discrepancy with the external fit.

`publication.inference.fit` uses `init="jitter+adapt_diag"`; the shared graph
defines t0 directly as `Normal(0, 0.025 day)` without a scale-standardized latent
parameter. Initialization on a timescale much larger than that prior scale is
a plausible contributor to landing in an adjacent likelihood mode. This is a
**mechanism hypothesis**, not proof of the actual initial state: retained draws
do not record initialization/warmup trajectories. No prior or input-contract
mismatch was identified in the inspected settings. Do not delete chain 0,
unwrap its t0 values, or report the other three chains as a rescued final fit.
The fixed Normal time prior is not invariant under a one-period shift.

## PUB-04: successful failure demonstrations with limited paired effect inference

All 30 declared attempts are retained: 24 numerical fits and six deliberate
pre-sampling identity controls. One fit passed the joint gate; 29 attempts were
rejected. A rejection is not an unsuccessful negative-control experiment.

| Predeclared condition | Attempts | Sampler passes | PPC passes | Joint passes |
|---|---:|---:|---:|---:|
| Long-exposure baseline | 3 | 0 | 3 | 0 |
| Exposure integration off | 3 | 0 | 3 | 0 |
| Global normalization | 3 | 3 | 0 | 0 |
| No jitter | 3 | 0 | 0 | 0 |
| Strong wrong radius prior | 3 | 3 | 0 | 0 |
| Input-hash corruption | 3 | unavailable | unavailable | unavailable |
| Dataset-identity mismatch | 3 | unavailable | unavailable | unavailable |
| Insufficient sampling | 3 | 0 | 0 | 0 |
| Short-exposure baseline | 3 | 1 | 3 | 1 |
| Deterministic sinusoid | 3 | 3 | 0 | 0 |

All six identity controls failed at `input_validation`; no `trace.nc` exists
for them. This is direct evidence that the tested mismatches were blocked
before sampling. Downstream scientific checks are unavailable, not measured
failures. The correct-identity fits did not exhibit a provenance rejection.

Nine numerical fits pass the sampler gate and fail PPC: all three global
normalization controls, all three wrong-prior controls and all three sinusoidal
controls. The sinusoidal group is the cleanest demonstration of convergence
being insufficient without invoking prior domination. Its lag-one residual
correlations are 0.58068, 0.63102 and 0.58822, despite R-hat <=1.00452, ESS
>=920.66 and zero divergences in all three.

For the predeclared `short_temporal_systematic/rep_0002` pair, the baseline
passes every gate and the sinusoidal variant passes sampling but fails PPC.
The radius means are 0.06950950 and 0.07001453, respectively, against truth
0.07; the sinusoidal variant's 94% radius interval is 1.44026 times wider.
This case illustrates that an apparently good radius estimate alone does not
establish an adequate stochastic model. The other two pairs remain present;
this pair is identified because it uniquely has an approved baseline, not
selected as the sole evidence or used to discard unfavorable realizations.

### Limitations that materially restrict claims

- Each of the three long-exposure baseline fits has exactly one divergence.
  Their R-hat/ESS checks otherwise pass, but the predeclared zero-divergence
  rule rejects them. Two short-exposure baselines also fail sampling: one has
  one divergence and one has R-hat 1.52781/ESS 7.20044 with mean t0 -0.249235
  day, suggestive of a chain-alias issue. The latter mechanism was not traced
  individually in this review.
- Consequently, all nontrivial ablation pairs lack two jointly interpretable
  fits. Exposure-off radius mean shifts span -0.002320 to +0.037987 and
  94% width ratios span 1.4993 to 4.3944, but nonconvergence prevents treating
  these as clean estimates of exposure-integration effects. They remain
  numerical descriptive outcomes with sampler qualifications.
- Global normalization produces lag-one correlation 0.99476--0.99585 and
  jitter/measurement-error ratios 60.37--60.56. Its declared normalization
  policy itself also fails the inherited scientific gate. This changes flux,
  error scaling, input identity and preprocessing status together; attribution
  is to the preprocessing intervention, not to just one scalar parameter.
- No-jitter fits have observed pointwise predictive coverage only
  0.54545--0.59091; they additionally fail sampling. The wrong-prior fits have
  radius means 0.025196--0.025227, roughly 64% below truth; none of their 94%
  radius intervals covers truth, although their sampler gates pass.
- The protocol's truth-based warning (>10% radius mean error AND truth outside
  the 94% interval) is met by six numerical fits: exposure-off rep_0002,
  no-jitter rep_0000, all three wrong-prior fits, and insufficient-sampling
  rep_0002. All six are rejected. This finite sample does not establish a
  universal false-negative rate or calibration of the gates.
- All six nominal baseline fits pass PPC; five fail sampling. Calling their
  five joint rejections a PPC false-positive rate would be incorrect.
  Three independent realizations per design support failure illustrations
  and descriptive paired effects, not precise detection/error frequencies.
- The current aggregate gate matrix labels `gate_scientific` as the joint
  result, not a separate physical-scale component. Physical/preprocessing
  reasons remain available in `result.json` under
  `inherited_m5_gate.component_reasons.scientific`. A consolidated publication
  table must make this distinction explicit rather than infer a standalone
  scientific-scale measurement from the joint Boolean.

`publication.ablations` estimates per-segment/global OOT medians from supplied
raw flux and a fixed phase cutoff, and scales measured errors consistently.
It does not read injected offsets for normalization. Uncertainty of these
estimated medians is not propagated; this is a declared modeling limitation,
not evidence of perfect preprocessing or truth-free observational calibration.

## PUB-05: five attempted regimes, zero approved observational fits

All five preselected systems and all three segments per system remain in the
target table. All pass provenance; four pass the declared numerical sampler
screen; all fail the temporal PPC component. The inherited pointwise PPC and
physical-scale checks alone would approve the four sampler-passing targets.

| Target | Rows | Exposure (s) | R-hat | Minimum ESS | Lag-one residual correlation | Approximate bound |
|---|---:|---:|---:|---:|---:|---:|
| HAT-P-7 b | 1,027 | 1765.463 | 1.009733 | 594.707 | 0.841838 | 0.113370 |
| Kepler-10 b | 3,000 | 58.849 | 1.008814 | 867.992 | 0.488021 | 0.068385 |
| TrES-2 b | 612 | 1765.463 | 1.005813 | 883.060 | 0.774981 | 0.140465 |
| HD 189733 b | 3,000 | 120 | 1.007155 | 786.201 | 0.983407 | 0.059917 |
| Kepler-4 b | 1,052 | 1765.463 | 1.027075 | 223.743 | 0.220528 | 0.101278 |

All have zero recorded divergences. Kepler-4 b also fails R-hat/ESS. HAT-P-7 b
and TrES-2 b have tree depth >=10 in 22.75% and 30.875% of retained iterations,
respectively. Although tree depth is diagnostic rather than a frozen gate,
this substantial rate is an additional efficiency/exploration caution.
Pointwise predictive coverage across the five is 0.93184--0.96078 and
standardized residual SD is near one; both can look reassuring while the
temporal residual test fails strongly.

These results support a negative applicability conclusion for the exact
declared preprocessing, fixed ephemerides and white-jitter likelihood. They
do not support a claim that the current publication workflow yields approved
physical estimates across these five regimes. Nor do they imply that transit
inference is impossible for these systems. The observations, folding,
normalization, parameterization, sampler and likelihood jointly define the
tested workflow.

Correlation alone does not identify its physical cause. Stellar variability,
unmodeled deterministic structure, ephemeris drift, residual segment offsets
and stochastic correlated noise are possible contributors. The model does
not contain temporal covariance, and this study did not separate those causes.
The diagnostic pools within-segment chronological pairs after phase thinning;
its normal-reference threshold is approximate and its lag denotes selected
observation spacing, not necessarily native instrumental cadence. Catalog
ephemerides/durations influence folding and preprocessing, so catalog
agreement cannot supply independent validation. Five purposely selected
systems cannot support a population rate.

## Follow-up questions: NOT EXECUTED

1. Does scale-aware initialization or a standardized t0 parameterization
   prevent adjacent-orbit trapping while preserving the exact prior and
   likelihood? First use explicitly labeled engineering/pilot checks and
   retain chain-level initialization/warmup evidence. Any new final comparison
   requires a new protocol/run identity; never select the successful seed.
2. Can a predeclared higher-accuracy sampling configuration produce adequate
   long-exposure nominal baselines for a separately identified paired ablation
   cohort? Keep all existing divergences and negative results; do not change
   the gate to rehabilitate these fits.
3. Which observed temporal structure persists after independently justified
   ephemeris/segment/systematics checks? Define input and model alternatives
   before new final fits. M6/GP remains deferred; no automatic superiority or
   GP benefit is demonstrated by the present rejection counts.
4. What are the nominal-control PPC rejection rate and control-detection
   sensitivity across more independent realizations, including normalization
   uncertainty and selected-time sampling? Three pairs do not answer this
   precisely. Use all declared attempts and report binomial uncertainty.
5. Can the independent benchmark establish computational compatibility after
   a separately registered remedy for the local numerical failure? The same
   observed temporal misspecification would still limit scientific promotion
   even if both numerical samplers pass.

These are research recommendations, not completed improvements, amended final
claims, or authorization to overwrite existing evidence. No final outcome
justifies tuning priors, deleting chains, widening intervals, changing seeds,
relaxing thresholds or silently replacing targets.
