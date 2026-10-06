# Bayesian exoplanet transit inference

**From public photometry to auditable evidence.** Research software developed by
Leonardo Moraes Barca for an MBA thesis in Data Science and Analytics at USP/Esalq.

[Português](README.md) · [Reviewer guide](docs/REVIEWER_GUIDE.md) ·
[Evidence synthesis](reports/publication_synthesis/tcc_evidence_v3/REPORT.md) ·
[Reproducibility and availability](docs/REPRODUCIBILITY.md) · [Citation](CITATION.cff)

## Research question

Under which conditions does a traceable Bayesian workflow recover exoplanet
transit parameters and represent their uncertainty adequately?

The project combines RAW/Silver/Gold data preparation, an exposure-integrated
physical transit model, PyMC inference, ArviZ diagnostics, synthetic recovery,
a `juliet` benchmark, controlled ablations and five observational systems.
The scientific reference is commit `127089538dbf2e233bce0d5e92c3977e115bb86b`;
`main` presents that consolidated evidence without rewriting historical runs.

## Findings, not just features

Useful radius-ratio recovery in the tested short-exposure regimes coexists with
conservative intervals. In the weakest synthetic regime, nominal 94% intervals
covered scaled orbital separation in 9/100 realizations and duration in 48/100,
although 85/100 runs passed the joint criteria. Passing those criteria therefore
did not establish physical identification of every parameter.

Three new local benchmark fits passed sampling diagnostics and yielded nearby
marginals under a matched comparison contract, but all failed the temporal
predictive assessment. They share one observed dataset and the same historical
external posterior; they are not three independent external validations.

The initial campaign contains 117 jobs, including 80 synthetic realizations; a
separate confirmatory cohort contains 400 realizations; the numerical follow-up
contains 24 fits. These are **not a pooled calibration sample**. The interrupted
v3 campaign remains separate, with seven predictive assessments invalidated
because of a conditioning defect.

Sources: [report](reports/publication_synthesis/tcc_evidence_v3/REPORT.md),
[recovery metrics](reports/publication_synthesis/tcc_evidence_v3/calibration_metrics.csv),
[benchmark comparisons](reports/publication_synthesis/tcc_evidence_v3/benchmark_comparisons.csv).

## Scope and access

M5 assumes a fixed period, circular orbit, independent heteroscedastic Normal
errors plus white jitter, and no joint stellar-parameter inference. It is not a
correlated-noise/GP model. Fixed-truth interval coverage is not simulation-based
calibration. Negative outcomes and limitations are part of the evidence.

The canonical index is [TCC_EVIDENCE_INDEX.json](publication/TCC_EVIDENCE_INDEX.json).
Read the report and structured tables directly in GitHub before installing or
running anything. Full posterior traces and some large intermediate files still
require an external local bundle: a public repository is not a complete public
archive. No DOI, publication acceptance or universal validation is claimed.

Original software: [MIT](LICENSE). Third-party material retains its own terms.
See [availability](docs/REPRODUCIBILITY.md), [contributing](CONTRIBUTING.md) and
[security](SECURITY.md) before reproducing or redistributing material.
