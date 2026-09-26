# Literature and novelty positioning

Snapshot: **2026-09-26**. Review ID: `PUB-01-literature-snapshot-2026-09-26`.

This is a targeted scoping review, not a systematic priority search. It does **not** establish that the proposed workflow is first, unique, superior, or publication-ready. The complete machine-readable matrix, including every requested comparison field and explicit unknowns, is [NOVELTY_MATRIX.json](NOVELTY_MATRIX.json). Benchmark preselection is recorded separately in [BENCHMARK_SELECTION.md](BENCHMARK_SELECTION.md).

## Search and evidence rules

The JSON records the search queries, inclusion/exclusion rules, source URLs, publication status and limitations. Searches combined named software, foundational methods, and phrases such as `"exoplanet" "simulation-based calibration"` and `"transit" "content-addressed" validation workflow`. Sources retained were original papers, author manuscripts, official standards, project documentation and package-release metadata. Search snippets and secondary mirrors were not used as proof of capabilities. Relevant source sections were inspected where a comparability decision depends on implementation details.

`unknown/not verified` means exactly that: it must never become “absent” in a manuscript. A generic provenance tool is not deficient because it does not fit transits, and a fitting package is not deficient because it does not implement this repository's exact promotion schema. Current software documentation is not proof that the same capability existed in its original paper. Repeat this review near submission, including an ADS citation-chain search and a review of then-current release sources.

## Prior-art map

The detailed JSON columns are: work, year, problem, method, Bayesian inference, transit modeling, provenance, injection/recovery, calibration, external benchmark, gates, reproducibility, software artifacts, content addressing, correlated noise, multi-target scope, limitations and difference from this work.

| Primary work | Year | Established layer relevant here |
|---|---:|---|
| [Mandel & Agol — Analytic Light Curves for Planetary Transit Searches](https://arxiv.org/abs/astro-ph/0210099) | 2002 | Analytic limb-darkened transit prediction. |
| [Kipping — Binning is sinning](https://arxiv.org/abs/1004.3741) | 2010 | Finite-exposure bias and integration. |
| [Kipping — Efficient, uninformative sampling of limb darkening coefficients](https://arxiv.org/abs/1308.0009) | 2013 | Physical limb-darkening parameterization. |
| [Kreidberg — batman](https://arxiv.org/abs/1507.08285) | 2015 | Independent transit forward implementation. |
| [Foreman-Mackey et al. — exoplanet](https://joss.theoj.org/papers/10.21105/joss.03285) | 2021 | Differentiable Bayesian exoplanet modeling. |
| [Espinoza, Kossakowski & Brahm — juliet](https://academic.oup.com/mnras/article/490/2/2262/5583056) | 2019 | Flexible Bayesian transit/RV/GP inference. |
| [Günther & Daylan — allesfitter](https://arxiv.org/abs/2003.14371) | 2021 | Broad fitting framework; injection/recovery and paper products. |
| [Abril-Pla et al. — PyMC](https://www.pymc.io/welcome.html) | 2023 | General probabilistic inference and predictive generation. |
| [Hoffman & Gelman — The No-U-Turn Sampler](https://jmlr.org/papers/v15/hoffman14a.html) | 2014 | Adaptive HMC trajectories. |
| [Vehtari et al. — Rank-normalization, folding, and localization](https://arxiv.org/abs/1903.08008) | 2021 | MCMC convergence and efficiency diagnostics. |
| [Talts et al. — Validating Bayesian Inference Algorithms with Simulation-Based Calibration](https://arxiv.org/abs/1804.06788) | 2018 | Prior-predictive algorithm calibration. |
| [Gelman et al. — Bayesian Workflow](https://arxiv.org/abs/2011.01808) | 2020 | Model checking beyond sampling. |
| [Vehtari et al. — Pareto Smoothed Importance Sampling](https://arxiv.org/abs/1507.02646) | 2024 | Importance-sampling reliability diagnostics. |
| [Christiansen et al. — Measuring Transit Signal Recovery III](https://arxiv.org/abs/1605.05729) | 2016 | Mission-scale detection injection/recovery. |
| [Twicken et al. — Kepler Data Validation I](https://arxiv.org/abs/1803.04526) | 2018 | Candidate diagnostic gates and data products. |
| [Gibson et al. — A Gaussian process framework for modelling instrumental systematics](https://academic.oup.com/mnras/article/419/3/2683/1070795) | 2012 | GP treatment of transit systematics. |
| [Gibson — Reliable inference of exoplanet light curve parameters](https://arxiv.org/abs/1409.5668) | 2014 | Simulation-based transit uncertainty/reliability assessment. |
| [Foreman-Mackey et al. — Fast and Scalable Gaussian Process Modeling](https://arxiv.org/abs/1703.09710) | 2017 | Scalable temporal covariance. |
| [Thompson et al. — Octofitter](https://arxiv.org/abs/2402.01971) | 2023 | Exoplanet orbit software with PPC/SBC. |
| [Martin & Mortlock — An approach to robust Bayesian regression in astronomy](https://academic.oup.com/rasti/article/doi/10.1093/rasti/rzaf035/8233173) | 2025 | Fixed-value calibration distinguished from SBC. |
| [Servillat et al. — IVOA Provenance Data Model 1.0](https://www.ivoa.net/documents/ProvenanceDM/) | 2020 | Standardized astronomical provenance. |
| [IVOA — Data Origin in the VO 1.2](https://www.ivoa.net/documents/DataOrigin/20260331/EN-data-origin-1.2-20260331.html) | 2026 | Current VO source/origin metadata. |
| [Akhlaghi et al. — Toward Long-Term and Archivable Reproducibility](https://arxiv.org/abs/2006.03018) | 2021 | Verifiable, archival analysis-to-narrative workflow. |
| [Halchenko et al. — DataLad](https://joss.theoj.org/papers/10.21105/joss.03262) | 2021 | Content identifiers and executable provenance. |

## What this changes about positioning

The strongest overlap is substantive, not cosmetic. Transit recovery under alternative systematics was already studied by Gibson; Bayesian workflow literature already separates computation from adequacy; Octofitter already integrates exoplanet inference and SBC. Thus “trustworthiness was tested, not merely asserted” is an appropriate research objective, but not a defensible novelty claim by itself. See [Gibson (2014)](https://arxiv.org/abs/1409.5668), [Bayesian Workflow](https://arxiv.org/abs/2011.01808), and [Octofitter](https://arxiv.org/abs/2402.01971).

Likewise, astronomical lineage and content identity are established approaches, not inventions of this repository. An implementation using SHA-256 manifests must demonstrate its guarantees rather than claim standards compliance automatically. See [IVOA provenance](https://www.ivoa.net/documents/ProvenanceDM/), [DataLad](https://joss.theoj.org/papers/10.21105/joss.03262) and [Maneage](https://arxiv.org/abs/2006.03018).

**Candidate contribution, conditional on completed evidence:** “We integrate and empirically evaluate pre-specified recovery, independent-implementation and failure-control experiments with explicit evidence-promotion gates and content/protocol/environment-bound artifacts for a bounded Bayesian transit-inference workflow.”

This is an integration/evaluation contribution. Its publishable value must come from the experiment results: supported and unsupported regimes, measured gate detection/failure behavior, independent discrepancies, and an auditable evidence chain. Simply having the architecture does not establish that value. Do not imply existing fitters lack validation: allesfitter explicitly documents injection/recovery and generated scientific products. [Allesfitter, §§I and IV.2](https://arxiv.org/html/2003.14371v2).

## Calibration terminology and interpretation contract

At fixed truth, repeated noise realizations estimate **conditional frequentist coverage of the declared Bayesian intervals** for that scenario. Bayesian intervals need not have exact nominal coverage at every fixed parameter value, especially near boundaries or under informative priors. Such tests characterize operating behavior; they do not, alone, verify an inference algorithm.

SBC draws parameters from the inference prior, then data from its likelihood, and examines ranks relative to posterior draws, with attention to finite Monte Carlo dependence. Fixed-truth ranks do not have the same uniform-rank guarantee. A shared simulator/inference implementation can share an undetected bug even when calibration appears satisfactory. Use independent forward checks and the external comparison to reduce, not claim to eliminate, that risk. See [Talts et al.](https://arxiv.org/abs/1804.06788) and the explicit distinction in [Martin & Mortlock (2025), §3](https://academic.oup.com/rasti/article/doi/10.1093/rasti/rzaf035/8233173).

Report raw all-attempt outcomes and gate-conditioned outcomes separately: selection by gates can change the coverage estimand. Missing posterior intervals are not observed noncoverage; an all-attempt “successful recovery” denominator and conditional coverage answer different questions. Uncertainty bands on observed frequencies and missingness counts are essential. These are analysis requirements for this project, not claims that published tools fail them.

Catalog-informed priors and catalog comparison are statistically dependent. Agreement between independent codes on shared observations is computational corroboration, not a second independent observation of the planet. Detection completeness, posterior interval coverage, and astrophysical planet confirmation are different estimands; mission vetting gates are not identical to this project's interpretability gates. [Kepler injection study](https://arxiv.org/abs/1605.05729), [Kepler DV](https://arxiv.org/abs/1803.04526).

## Claims that remain forbidden

- First Bayesian transit fitter, first exoplanet calibration workflow, or first astronomical validation gates.
- Novel content addressing, NUTS, GP transit modeling, exposure integration or q1/q2 parameterization.
- General calibration from a few examples, or exact calibration from an uncertainty band containing nominal coverage.
- Superior accuracy to juliet/allesfitter without a frozen matched comparison.
- External astrophysical validation from a catalog already used in the prior.
- Population-level generalization from a small regime-selected target set.
- GP superiority before paired white/correlated controls and signal-absorption checks.
- Full reproducibility before the declared clean-room/artifact gates pass.

The JSON contains the corresponding machine-readable claim policy.

## Journal-fit notes — provisional, not acceptance predictions

**Astronomy and Computing** is a plausible methodological destination if the completed study demonstrates an astronomical-computing contribution with reproducible experiments. The publisher's scope includes astronomical software, simulations and data analysis/preservation. The full Guide for Authors page was not accessible in this review; formatting, data-policy details and charges must be rechecked before submission. [Official publisher scope](https://shop.elsevier.com/journals/astronomy-and-computing/2213-1337).

**JOSS** is a possible *separate software paper*, not a substitute for the full empirical research manuscript. Current guidance requires meaningful research software, demonstrated impact, appropriate packaging/documentation/testing and sustained public development; the public-history requirement must be audited rather than assumed. Its stated screening criteria include more than six months of active public history. This branch's new work alone cannot demonstrate that history. [Current JOSS submission guidance](https://joss.readthedocs.io/en/latest/submitting.html).

No target venue is selected irrevocably; choose after reviewing the final evidence, scope, author metadata, ethics/AI-assistance disclosure and current author guidance. Do not promise acceptance or a TCC grade.

## Review limitations and next update

This snapshot maps direct overlaps and supplies usable primary references; it is not an exhaustive novelty clearance. Entries with unknown calibration/gates/provenance need deeper source inspection before making any comparative absence claim. Octofitter's journal PDF is dated October 2023 although its later arXiv deposit has inconsistent journal-year metadata; the matrix uses the journal issue/PDF date.

No final posterior outcome, seed, target or benchmark agreement was inspected for tool selection. The branch registry, not this document, determines which experiment phases are actually completed.

