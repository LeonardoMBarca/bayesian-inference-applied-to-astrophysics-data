# PUB-04 paired ablation study — draft, not final evidence

The machine-readable design is
[`PUB-04-draft.json`](../../publication/protocols/PUB-04-draft.json).
It is **DRAFT** and deliberately cannot authorize a final batch. The proposed
100 attempts, including 20 pre-sampling rejection controls, require a runtime
and precision review followed by a committed freeze. No final P4 inference has
been executed by the transformation implementation.

## Question and design

The experiment asks which preprocessing/model assumptions materially affect
physical recovery, and whether distinct gates catch their intended failures.
It does not assume every intervention is harmful or every control will be
detected. Ten independent raw realizations are proposed for each of two pairs:

| Pair | Common data | Paired variants |
|---|---|---|
| Long-cadence segment offsets | 1800 s spacing, 1765 s exposure, three segments, four transits per segment | baseline; no exposure integration; global normalization; no jitter; strongly wrong radius prior; wrong input hash; dataset mismatch; insufficient sampling |
| Short-cadence temporal control | 180 s spacing, 120 s exposure, three segments, two transits per segment | baseline; predeclared deterministic sinusoid |

All variants in a pair share their generative seed and true transit parameters.
The sinusoid is generated separately with the same stochastic seeds, so the
measurement/jitter realization remains identical. Its amplitude, period and
phase are declared before outcomes; it is not selected from a seed search.
Independent inference/predictive streams are derived from variant identities.

## Observed-data normalization, not hidden calibration

`publication.ablations.estimate_normalization` uses only raw observed flux,
measurement errors, segment identifiers and the fixed mask `abs(phase) > 0.10`
days. Each segment (or the deliberately wrong global alternative) is divided by
its **estimated noisy** OOT median; the same divisor scales its measurement
errors. The true offsets never enter this function. The fixed mask is not tuned
from true duration or a fitted posterior.

Median estimation uncertainty is not propagated as another latent parameter.
This limitation is common to the controlled comparison and must be considered
when discussing residual correlations or exact uncertainty calibration. The
global alternative is honestly labeled; its policy rejection is distinguished
from sampler/PPC detection and quantitative posterior distortion.

`apply_ablation(raw_frame, inference_config, intervention)` returns deep copies
of the inference frame/config. It first performs this empirical preprocessing,
then applies exactly the declared intervention. Compared with its returned
`baseline`, model-only interventions have byte-identical input CSV hashes.
Global normalization changes flux/error and their derived identities together.
Only the two explicitly corrupt-identity controls receive inconsistent hashes
or identifiers. Save `frame.attrs['normalization_metadata']` as
`preprocessing.json` before invoking the inference worker. The output CSV uses
UTF-8, `float_format='%.17g'` and LF line endings.

## Measurements and interpretation

Primary outputs are paired posterior shifts, 94% interval-width/SD ratios,
separate provenance/sampler/PPC/scientific-scale/final-interpretability outcomes,
and the rate of sampler-pass but predictive/scientific-fail cases. Bias, RMSE,
multi-level coverage, residual structure and computational cost are secondary.
Truth is read only by post-inference evaluation, never by inference priors,
initialization, preprocessing or observational gates.

Every declared attempt remains in the denominator. A posterior comparison needs
both numerical posterior summaries; unavailable pairs stay explicitly listed.
Report all available pairs separately from the subset in which both scientific
gates pass. Pre-sampling identity rejections have unavailable downstream checks,
not fabricated negative sampler/PPC measurements.

Ten pairs give imprecise frequency estimates: near a probability of 0.5 the
binomial standard error is about 0.158; even zero events among ten attempts has
a Wilson 95% upper bound near 0.278. Report these intervals, all paired effects
and the limited scope; P4 is not a replacement for the larger calibration study.

An isolated 94% credible-interval miss is expected sometimes even under a
calibrated model. The draft flags joint >10% radius mean error and 94% truth
noncoverage for post-inference performance review; this flag never changes the
inference. Correctly specified white controls estimate nominal gate rejection,
not an exact type-I error after empirical normalization and fitting. False
positives/negatives of deterministic provenance checking are assessed separately.

If the predeclared sinusoid does not produce sampler-pass/PPC-fail evidence,
that requested demonstration remains unachieved. Preserve the outcome; do not
retune the sinusoid, prior, seed or gate to manufacture a favorable case.

## Implementation checks and execution boundary

```sh
python -m unittest tests.test_publication_ablations -v
```

The tests exercise empirical normalization, raw/error preservation, deterministic
pairing, exact intervention field changes and pre-sampling rejection of the
identity controls. They are not MCMC evidence and cannot complete P4. The batch
runner must still integrate these transformations, freeze the final protocol,
register all attempts, execute them and generate all machine-readable aggregate
results, tables, figures and reports before scientific conclusions are allowed.
