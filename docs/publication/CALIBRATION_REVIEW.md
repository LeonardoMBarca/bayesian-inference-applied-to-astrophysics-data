# Scientific review of the completed P2 cohorts

Review date: 2026-09-30. This is a post-result interpretation of preserved
evidence, not a new protocol or a change to any historical gate. No inference,
seed, prior, threshold, dataset or completed run was changed for this review.

## Evidence and estimand

The primary extension is the 400-run cohort specified in
[`PUB-02-confirmatory-v1.json`](../../publication/protocols/PUB-02-confirmatory-v1.json).
Its 100 independent noise realizations per scenario must remain separate from
the 20-per-scenario parent cohort. The decision to increase replication followed
inspection of parent outcomes; this is explicitly disclosed in the protocol's
`confirmatory_extension.outcome_knowledge` and in
[`CONFIRMATORY_CALIBRATION_CAMPAIGN.md`](CONFIRMATORY_CALIBRATION_CAMPAIGN.md).
There was no outcome-dependent change to the four truths, priors or likelihood.

Numerical authorities are the two cohort-specific `PUB-02/calibration.json`
files, with `calibration.csv`, `posterior_recovery.csv`, `jobs.csv`, `attempts.csv`
and the sealed per-attempt `result.json`, `truth.json`, and `trace.nc`:

- [Confirmatory calibration](../../reports/publication_campaign/tcc_calibration_confirmatory_v1/PUB-02/calibration.json).
- [Parent calibration](../../reports/publication_campaign/tcc_campaign_v1/PUB-02/calibration.json).

The estimand is conditional repeated-sampling coverage at four fixed parameter
vectors. It is not simulation-based calibration (SBC), because truths were not
drawn from the inference prior. A Bayesian posterior can have nonnominal
frequentist coverage at a fixed truth without an implementation error. These
experiments measure the operating performance needed for the stated recovery
claims; they do not establish a universal calibration theorem.

Coverage uses equal-tailed intervals, not HDIs. All seven declared parameters
and all three levels (50%, 80%, 94%) must be considered. Wilson intervals describe
finite-replication uncertainty for individual proportions, not simultaneous
confidence across every scenario, level and parameter. Radius and geometric
depth have identical interval-inclusion events under the monotone transform
`depth = r**2`; they are not independent confirmations. The comparisons are
descriptive, with no unadjusted multiple-testing discovery claim.

The primary confirmatory cohort has numerical posteriors for all 400 declared
replicates, including all 63 rejected runs. Its stored gate decisions pass 337
replicates. The parent has 80 numerical posteriors, 65 gate passes and 15
rejections. There is no scientific justification for retaining only successes.
Numeric, sampler-conditioned and final-gate-conditioned coverage answer
different questions; their denominators must remain explicit. Conditioning on
a gate is selection and does not repair the unconditional estimator. The
covered-and-passed/all-declared rate is an operational yield, not interval
coverage.

An independent read-only reconstruction from every registered per-attempt
`result.json` and `truth.json` reproduced all 84 parameter-by-level coverage
cells and all 28 mean biases in each cohort. This includes the all-numeric
covered counts, final-gate denominators, and covered-and-passed counts. No
discrepancy was found in these checked aggregate quantities. This check did
not re-estimate posterior quantiles from every trace or independently establish
the validity of the sampler; the five alias traces below were inspected
directly.

## What the calibration supports and does not support

Radius recovery has small average bias in the two short-cadence regimes, but
the intervals are often conservative for these fixed truths. The confirmatory
radius coverage at 50/80/94% is 71/98/100% in `deep_short` and 67/96/100% in
`shallow_short`. These values cannot be described as exact nominal calibration.
The 95% Wilson interval for 100/100 is approximately [96.3%, 100%], and even a
numerically perfect empirical inclusion rate does not imply precise inference.
Sources: `scenarios.<scenario>.parameters.r.coverage` in the confirmatory JSON.

Geometry is substantially less identified than a radius-only headline suggests.
For `intermediate_long`, the 50% interval for impact parameter contains the
fixed truth in 0/100 realizations, while the 80% and 94% intervals contain it in
100/100. Its mean impact-parameter bias is about -0.318 from true `b=0.75`.
This combination is compatible with a broad, prior-sensitive posterior and
does not support accurate recovery of its center. In `shallow_short`, impact
parameter is covered in 100/100 even by the 50% interval; that is also evidence
of weak identification/conservative uncertainty at this truth, not exceptional
precision. Sources: the corresponding `parameters.b` entries.

The strongest negative finding is `near_limit_long`. Its 94% coverage is 9/100
for `a/Rs` (Wilson95 approximately [4.8%, 16.2%]) and 48/100 for duration
([38.5%, 57.7%]). Radius has approximately +139.8% relative mean bias and
geometric depth +688.8%. Its broad 94% radius intervals still cover the truth
in 98/100. Hence radius inclusion alone would conceal large bias and poor
geometric recovery. The parent independently shows the same direction, with
`a/Rs` coverage 1/20 and duration 5/20 at 94%; it is a separate cohort, not an
extra denominator chosen after inspecting the extension.

The frozen priors make a useful limiting illustration: with no information,
`a/Rs ~ Uniform(2,50)` has central 94% interval [3.44,48.56], which already
excludes the near-limit truth 3.3 despite that truth being inside the prior
support. Likewise the radius prior's median 0.04 exceeds its true 0.01. This
explains why prior influence can produce severe conditional noncoverage and
bias in a low-information regime without requiring a coding defect. It is an
analytic prior-only illustration, not a claim that the measured posterior
equals its prior or a quantitative attribution of all observed error.
Changing priors to match the known truth would destroy this test's purpose.

The failure persists among passing runs: `near_limit_long` has 85 final-gate
passes, but only 7 of those 85 cover true `a/Rs` and 39/85 cover true duration
at 94%. This is a demonstrated limitation of the gate as a guarantee of
parameter recovery. Do not interpret each missed credible interval as an
individual false positive: noncoverage is possible even for a calibrated
procedure. The severe aggregate pattern establishes that gate approval is
insufficient for the broad accuracy/calibration claim in this regime. Sources:
`parameters.{a,full_duration}.coverage["0.94"]`, including the explicitly stored
`covered_and_scientific_gate_passed_count` and selected denominator.

These runs were already labelled as near/below useful detection SNR. The gates
test input identity, computational behavior, broad predictive adequacy and
limited scale checks; they do not test posterior identifiability or establish
that the observations contain enough information about every parameter. A
truth-free identifiability/information diagnostic would need a new prospective
validation study. It must not be retrofitted to turn this batch into a positive
result. Stored `scientifically_interpretable` is therefore a historical decision
under that gate definition, not a promise that every derived physical quantity
has validated recovery.

## Rejections and the transit-center alias failure

Of the 63 confirmatory rejections, 61 fail sampler criteria. Across those runs,
28 exceed R-hat 1.01, 27 have minimum ESS below 400, and 24 have divergences;
these categories overlap. None fail BFMI 0.30. The remaining two pass the
sampler but fail PPC: `intermediate_long/rep_0060` fails the selected-observation
residual-correlation screen, and `near_limit_long/rep_0007` has observed-point
predictive coverage 0.991379 above the predeclared 0.99 upper screen.
These are completed scientific rejections, not technical execution failures.
Their occurrence under the simulated white-noise model also shows why a screen
is not a certainty about model misspecification; its calibration is approximate.

Five rejected attempts have one of four chains trapped in a transit-center
mode displaced by approximately one fixed orbital period (one day). Direct
read-only inspection of the NetCDF posterior confirmed the chain means below;
the other three chains remain close to the injected center. Paths are relative
to `artifacts/publication_campaign/tcc_calibration_confirmatory_v1/runs/PUB-02/`.

| Attempt path | Displaced chain (zero-based) | Mean t0, days |
|---|---:|---:|
| `deep_short/rep_0012/attempt_000/trace.nc` | 1 | -0.998860 |
| `deep_short/rep_0033/attempt_000/trace.nc` | 1 | -0.999187 |
| `deep_short/rep_0070/attempt_000/trace.nc` | 0 | -0.999207 |
| `deep_short/rep_0094/attempt_000/trace.nc` | 0 | 1.000757 |
| `intermediate_long/rep_0093/attempt_000/trace.nc` | 3 | 0.997928 |

The corresponding `result.json` files have maximum R-hat approximately 1.53
and minimum ESS approximately 7; every one is rejected by the sampler gate
even though PPC passes. The periodic forward model can predict similar flux
at these aliases. The frozen sampler uses `init="jitter+adapt_diag"`
(`src/publication/inference.py`), and the center prior is Normal(0, 0.025 days).
The trace evidence establishes mode trapping; it does not by itself prove
which initialization/trajectory detail caused it. This is a numerical failure,
not a physical displacement inferred by a valid converged posterior.

Retaining these outputs inflates all-numeric transit-center bias/width/RMSE.
The already generated sampler-conditioned summaries are essential alongside
the all-attempt results. For example, `deep_short` t0 RMSE is about 0.0500 days
for all numeric outputs and 0.000210 days among its sampler passes. Removing
the failed chains, wrapping t0 after sampling, or choosing a replacement seed
would change the declared experiment and must not be done retroactively.
A separately registered sampler study could investigate prior-scale-aware
initialization or an explicitly justified phase parameterization.

## Integrity, anti-circularity and remaining scope limits

`campaign_worker.prepare_synthetic` writes ground truth separately and copies
only the declared inference configuration. The subprocess receives input,
inference config and output paths; `publication.inference` does not import the
simulator or open truth artifacts. `campaign_reporting._scientific_summary`
attaches truth after the result has been sealed. `coverage_metrics` retains
rejected numerical outputs and explicitly accounts for unavailable intervals.
This source inspection found no truth leakage through the inference interface.
It is a software separation, not an OS filesystem access-control boundary.

The simulator and inference share the `exoplanet` physical primitive. The
generator uses finer exposure quadrature, but that does not make it an
independent implementation. Analytic/independent-forward checks and the
separate benchmark supply different, limited evidence. They do not eliminate
the possibility of a shared physical assumption being wrong.

Period, circular geometry, exposure, measurement uncertainties and exact segment
calibration are known in P2; limb darkening and other sampled quantities have
declared priors. Empirical normalization error is not validated by these
already normalized simulations. Scenario factors vary together, so the plot
against known-white-noise signal-to-noise ratio is descriptive, not a causal
estimate of cadence or SNR effects. This SNR uses the truth signal after
inference and is not a detection significance available to the fitting code.

No stochastic-correlated-noise calibration cohort was executed here. OU cases
were deferred before the final batches, and M5 retains independent white
jitter. Neither this review nor passing residual screens establish robustness
to arbitrary red noise, grazing geometry outside prior support, uncertain
ephemerides, unmodeled astrophysics or a population of planetary systems.

The defensible conclusion is regime- and parameter-specific: the workflow
quantifies useful recovery behavior, exposes both conservative uncertainty and
severe low-information failures, and detects some numerical/identity failures.
It has not demonstrated universal parameter calibration or that gate approval
alone is sufficient for scientific accuracy.
