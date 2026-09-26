# Independent benchmark preselection

Decision date: 2026-09-26. Experiment family: PUB-03. Status: **preselected; final comparability contract and environment still require executable verification and freeze**.

Primary implementation: **juliet 2.2.10**, using its published batman transit calculation and a nested sampler. This choice was made from model/likelihood compatibility and documented interfaces, before observing any final posterior agreement. **allesfitter 1.2.10 was evaluated**, not discarded because of an unfavorable result. Do not replace the primary tool based on agreement; an installation blocker or scientific incompatibility requires a dated protocol amendment.

## Criteria fixed before comparison

Priority order: (1) same statistical prediction task and observations, (2) controllable priors/parameter meanings, (3) equivalent heteroscedastic likelihood, (4) exposure/limb-darkening control, (5) documented independent implementation and sampler, (6) feasible isolated environment and auditable outputs. No posterior number enters this selection.

| Criterion | juliet | allesfitter |
|---|---|---|
| Physical transit engine | batman, independently implemented from exoplanet | ellc, also independently implemented |
| Bayesian inference | Nested sampling; multiple sampler backends | emcee MCMC or nested sampling |
| Geometry control | Direct radius ratio, impact parameter and scaled semimajor axis documented | Rich binary/transit geometry; extra mapping required |
| Quadratic limb darkening | q1/q2 supported | q-parameterizations supported |
| Exposure treatment | Documented supersampling arguments | ellc-based forward model; exact exposure adapter behavior not verified here |
| Photometric uncertainty | Measured errors plus white jitter in quadrature | Published standard treatment rescales relative error weights |
| Results | Posterior samples and model evaluations accessible | Posterior samples, tables and figures accessible |
| Decision | Best match for this specific M5 likelihood | Scientifically capable; not selected because of likelihood-matching burden |

Sources: [juliet paper](https://academic.oup.com/mnras/article/490/2/2262/5583056), [juliet parameter documentation](https://juliet.readthedocs.io/en/latest/user/priorsnparameters.html), [juliet exposure API](https://juliet.readthedocs.io/en/latest/user/api.html), [allesfitter paper, §§III–IV](https://arxiv.org/html/2003.14371v2).

The distinction for heteroscedastic photometry is decisive: multiplying every input uncertainty by a common fitted factor cannot generally reproduce adding a common variance to every measurement. This is a statement about the documented model, not that allesfitter is inferior or cannot be extended. Current alternate allesfitter error options have not been exhaustively audited. [Allesfitter §IV.5](https://arxiv.org/html/2003.14371v2).

## Release metadata and environment plan

The official PyPI JSON APIs were queried on the decision date:

| Package | Latest PyPI release observed | Upload timestamp (UTC) | Verification level |
|---|---|---|---|
| juliet | 2.2.10 | 2026-02-16T06:01:19.725586Z | Release metadata, not installation |
| allesfitter | 1.2.10 | 2022-07-25T09:56:52.294262Z | First distribution upload; wheel uploaded two seconds later |

Sources: [juliet release metadata](https://pypi.org/pypi/juliet/json), [allesfitter release metadata](https://pypi.org/pypi/allesfitter/json). Release age alone does not establish maintenance quality or abandonment. Both have public source/documentation. A mutable `master` source inspection below is useful for adapter design but is **not** the final environment identity.

Install only in a separate benchmark environment. Do not add benchmark dependencies to or upgrade the validated M5 environment. juliet declares batman-package, radvel, dynesty, george, celerite, astropy, numpy, scipy, emcee, ultranest and h5py; compiled scientific dependencies make an actual import/likelihood smoke test necessary. Its permissive Python metadata is not proof of compatibility with this repository's Python 3.14 environment. Prefer a separately validated Python version supported by the resolved dependencies.

Before final execution, save Python/platform identity, exact full dependency lock, package-distribution hashes or immutable source commits, `pip check`, import results, sampler version, forward/log-likelihood tests, and the environment manifest SHA-256. Installation failure must remain recorded. No successful installation is claimed by this document.

## Proposed mapping to verify before freezing

The existing `scientific_003` remains untouched. A new publication companion fit may share the M5 physical primitive with a **declared changed prior profile** to permit exact comparison. This is not a retroactive validation or rewrite of its original LogNormal-radius posterior.

| Local meaning | juliet representation | Required verification |
|---|---|---|
| Radius ratio r | `p_p1` | Same support/density, not r1/r2 unless induced joint prior is proved equivalent |
| Impact b | `b_p1` | Same 0–1 support; circular relation cos(i)=b/a |
| Scaled semimajor a | `a_p1` | Same definition/support; do not add redundant stellar-density prior |
| Transit center t0 | `t0_p1` | Identical days/epoch convention and frozen transformation |
| Period/eccentricity | `P_p1`, `ecc_p1` | Fixed same values; omega convention fixed for circular case |
| Quadratic LD | `q1_INST`, `q2_INST` | Same priors and q-to-u transformation |
| Baseline B | `1 + theta0_INST` | Additive constant regressor, not free mflux |
| White jitter j in relative flux | `sigma_w_INST = 10^6 j` | ppm conversion and exact quadrature variance |
| Geometric depth | `p_p1**2` | Do not confuse with limb-darkened observed depth |
| Full duration T14 | Recompute from posterior geometry | Same contact definition and time unit |

The parameter documentation supplies the direct geometry and ppm jitter convention. [Official parameter definitions](https://juliet.readthedocs.io/en/latest/user/priorsnparameters.html).

For an exact **additive** baseline, fix `mdilution_INST=1` and `mflux_INST=0`; provide an all-ones regressor of shape (N,1), with `theta0_INST ~ Normal(0,0.02)`. Then the mean is T + theta0, equal to B + (T−1) for B=1+theta0. This avoids using juliet's ordinarily multiplicative mflux as if it were an additive offset. Test this identity over a physical parameter grid. [Linear-model tutorial](https://juliet.readthedocs.io/en/latest/tutorials/linearmodels.html), [flux convention](https://juliet.readthedocs.io/en/latest/tutorials/transitfits.html).

The reviewed standard prior table does not list LogNormal. A common frozen Uniform radius prior is an acceptable companion experiment, but changing one side only is not. A HalfNormal jitter can be represented by a zero-mean TruncatedNormal with lower 0 and upper +infinity, with its scale converted to ppm; the reviewed transform uses SciPy's truncated-normal inverse CDF. Verify this in **installed 2.2.10**, including near-boundary quantiles, before calling it matched. JSON cannot contain nonstandard Infinity: encode the unbounded support explicitly and resolve it at the adapter boundary. [Official source transform](https://raw.githubusercontent.com/nespinoza/juliet/master/juliet/utils.py).

Exposure handling must be frozen numerically, not just labeled “integrated.” juliet passes supersampling factor and scalar exposure duration to batman; compare quadrature rules and time units against the local primitive. If exposure varies within rows, an instrument/segment grouping or an explicitly common approximation is needed, preserving shared priors/noise parameters where intended. Record a numerical bound on any approximation. A median-exposure shortcut is not automatically an exact match. [API](https://juliet.readthedocs.io/en/latest/user/api.html), [forward initialization source](https://raw.githubusercontent.com/nespinoza/juliet/master/juliet/utils.py).

## Final contract still required

Before any final posterior run, commit PUB-03 protocol/contract with:

- Dataset ID, exact input file hash, row count, original-row index digest, time/flux/error/exposure units and array identity after any deterministic adapter transform.
- Every prior distribution, support and scale; parameter mapping; fixed physical assumptions; shared versus per-segment nuisance parameters.
- Label each item `matched`, `approximately_matched` or `not_matchable`, with numerical tolerances justified before outcomes.
- Both samplers' settings and seeds. For nested sampling, save stopping diagnostics, weights/effective posterior sample size, termination and repeated-run policy; MCMC R-hat/BFMI must not be mechanically applied to unordered nested draws.
- Prior/forward/log-likelihood equivalence tests. Forward agreement is necessary but not sufficient for matching priors.
- Primary posterior comparisons: standardized mean difference, 50/80/94 interval overlaps and width ratios, distribution distance with Monte Carlo uncertainty, geometry correlations and predictive discrepancy.
- Every required parameter including r, r², b, a, t0, T14 and jitter, with identical derived definitions.
- Missing/failed-run rules; no rescue seed selected for closer agreement; all attempts retained.
- Allowed conclusions and discrepancy-investigation order.

For nested-sampler seed reproducibility, verify the concrete backend's RNG interface in the installed version rather than assuming that a global NumPy seed controls it.

## Interpretation boundaries

Agreement would support implementation consistency under the contract, not validate omitted astrophysics or prove calibrated uncertainty. Differences must be investigated in input → definitions → priors → exposure/limb darkening → likelihood → sampler → implementation order. Unmatched priors or failed diagnostics block a pure implementation-error interpretation.

Do not rank external and local tools via their evidence estimates unless model priors, normalizations and data contracts genuinely match. The primary task is posterior/predictive compatibility, not evidence ranking. No comparison metric result, installation success or P3 completion is asserted here.
