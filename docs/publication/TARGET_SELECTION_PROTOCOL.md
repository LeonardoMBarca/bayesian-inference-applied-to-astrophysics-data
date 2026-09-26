# PUB-05 — frozen pre-result target selection

Status: target selection FROZEN; inference protocol still DRAFT, not final evidence. The authoritative
machine-readable counterpart is
`publication/protocols/PUB-05-draft.json`. No new target inference or Kepler-4
FITS download was performed while drafting this document. Catalog/header
inspection is selection evidence, not a scientific result.

## Question and selection rule

Across which deliberately different observational regimes does the shared M5
workflow produce interpretable inference, and where do its assumptions fail?
The study does not assume that all systems pass. It is a five-system case study,
not a random sample and not a population-level estimate of performance.

Keep HAT-P-7 b and Kepler-10 b as mandatory historical anchors. Add one
high-impact geometry system, one active-star system and one intermediate-depth
Neptune-size system. Require a confirmed transiting planet and public mission
photometry with supplied errors, target identity, segment identity, exposure
and an explicit BJD/TDB convention. Selection does not inspect a posterior,
gate decision, fitted residual, or agreement with a catalog value.

| Selected system | Pre-fit role | Declared observing products | Selection evidence |
|---|---|---|---|
| HAT-P-7 b | Fixed deep giant anchor; long exposure | Existing Kepler Q0/Q1/Q2, 1765.46 s | Protected target configuration at `7489a90` |
| Kepler-10 b | Fixed shallow small-planet anchor; short exposure | Existing three Kepler short-cadence products, Q2/Q3, 58.85 s | Protected target configuration; `scientific_003` unchanged |
| TrES-2 b | High-impact, near-grazing geometry; finite-exposure challenge | Existing Kepler Q0/Q1/Q2, 1765.46 s | DR25 KOI K00001.01; published geometry study |
| HD 189733 b | Active/spotted-star challenge; short exposure | Existing TESS sectors 41/54/81, 120 s | Public activity/spot evidence; archive ephemeris |
| Kepler-4 b | Intermediate depth, Neptune-size; long exposure | Planned Kepler Q0/Q1/Q2, long cadence | DR25 KOI K00007.01; discovery paper |

TrES-2 is described as near-grazing in the literature; this is not an assertion
that it is a strictly grazing transit (`b > 1-r`).
[Schröter et al. (2012)](https://arxiv.org/abs/1205.0969).
HD 189733's activity and occulted spots motivate a challenging case, without
assuming that a particular TESS sector will fail.
[Pont et al. (2007)](https://arxiv.org/abs/0707.1940),
[Miller-Ricci et al. (2008)](https://arxiv.org/abs/0802.2722).
Kepler-4 supplies a Neptune-size transit regime between the two anchors.
[Borucki et al. (2010)](https://arxiv.org/abs/1001.0604).

These are purposively selected, accessible benchmark systems. Accessibility and
the historical two-target baseline constrain selection; this is an explicit
threat to external validity, not a representative survey.

## Parameter and time provenance

Catalogs were queried on 2026-09-26 before any final PUB-05 inference. Exact SQL
queries, values, unit conversions and references are in the JSON protocol.

The anchor numerical configurations remain those of the protected baseline.
The additional Kepler ephemerides use paired period/epoch from the same
`q1_q17_dr25_koi` rows, not a mixture of independently selected measurements:

| System | Period (day) | Epoch (BJD/TDB) | Duration used for exclusion (hour) |
|---|---:|---:|---:|
| TrES-2 b / K00001.01 | 2.470613377 | 2454955.763305 | 1.74319 |
| Kepler-4 b / K00007.01 | 3.213668926 | 2454956.611878 | 3.98235 |
| HD 189733 b | 2.2185752 | 2453955.5255511 | 1.803648 |

DR25 epochs are converted by `BJD = BKJD + 2454833`. Depths in ppm are
converted to percent by division by 10000; these contextual observed depths
are not identical to geometric `r**2`.
[NASA Kepler KOI documentation](https://exoplanetarchive.ipac.caltech.edu/docs/Kepler_KOI_docs.html).

The HD 189733 composite catalog mixes period, epoch and duration sources.
Instead, use the paired `ps` row from Baluev et al. (2015), whose timing
convention is BJD/TDB. This choice precedes final inference and avoids selecting
inconsistent ephemeris components. The long extrapolation to TESS sectors still
must be stated. Period
is fixed; a common transit-center offset is fitted, but a period error can
produce sector-dependent phase drift that M5 cannot repair. Diagnose and
report this limitation; do not tune period after posterior inspection.
[Baluev et al. (2015)](https://doi.org/10.1093/mnras/stv788),
[Bourrier et al. (2020), Table 1, explicit BJD/TDB epoch](https://academic.oup.com/view-large/199083199),
[NASA Exoplanet Archive HD 189733](https://exoplanetarchive.ipac.caltech.edu/overview/HD%20189733).

FITS headers of all 12 existing selected products were inspected: Kepler uses
`BJDREFI=2454833`, TESS uses `BJDREFI=2457000`, and all declare `TIMESYS=TDB`.
The adapter rejects inconsistent header IDs (`KEPLERID`/`TICID`), mission,
checksums, time units, time references, or cadence. Source paths and SHA-256
values are fixed in the JSON. A nominal TESS 120 s value can exceed 120 by
floating-point roundoff; cadence classification admits only a documented
`1e-6` second numerical tolerance, not a scientific relaxation.

## Acquisition and no-cherry-picking policy

Commit selection before downloading new Kepler-4 photometry. The new target
is KIC 11853905, independently confirmed by MAST's Kepler HLSP index.
[MAST Kepler HLSP](https://archive.stsci.edu/prepds/kepler_hlsp/).
Acquire long-cadence PDCSAP products for Q0/Q1/Q2, record source URI/retrieval
time/size/SHA-256, then freeze exact source entries before final inference.
Use latest archived processing version if a quarter has multiple products;
break otherwise identical ties by product ID. Never choose using transit shape
or fit quality. Standard archive retrieval routes are documented by
[MAST](https://archive.stsci.edu/kepler/download_options.html).

Missing products, access failures, corrupt FITS, unsuitable metadata,
preprocessing failure and model rejection remain visible outcomes. Do not
silently reduce the source set or replace a target. Any changed acquisition
policy, target or model must have a dated amendment preserving the original
selection and reason.

## Frozen-analysis draft

The final protocol must be committed separately after acquisition metadata are
verified. Proposed settings, agreed before final results:

- PDCSAP flux/errors; mission quality flag exactly zero; discard only
  nonfinite values and nonpositive supplied errors/exposures. No residual
  clipping, flare-removal tuning or spot masking after fitting.
- Shared source-FITS segment normalization, using the median of points beyond
  `0.75 * catalog_duration` from phase zero; at least 20 baseline points.
  No new detrending. Baseline estimation uncertainty remains unpropagated.
- Shared deterministic phase-stratified thinning, at most 1000 points per
  segment. Preserve time, phase, exposure, source hash and original row index.
- Shared circular M5, quadratic limb darkening `q1,q2 ~ Uniform(0,1)`, measured
  error plus white jitter, exposure oversampling 15. It is not a correlated
  likelihood; neither stellar activity nor spots are explicitly modeled.
- Radius-ratio prior median 0.04 with log SD 0.9 for every system; baseline
  `Normal(1,0.02)`; `t0 ~ Normal(0,0.025 day)`; remaining M5 priors in JSON.
  Catalog depth is not used to tune the radius prior.
- One final run per target: four chains, 1000 tuning plus 800 retained draws,
  target acceptance 0.95, deterministic ID-derived seeds. No best-seed selection
  or automatic retries. Any corrected attempt gets a new ID.

The full freeze must state the same sampler/PPC/scientific gate definitions as
the validated publication inference implementation, including limitations of
temporal diagnostics after thinning. Numerical thresholds are not defined by
whether the observational outputs happen to pass.

## Required outcomes and interpretation

Generate a row for all five declared systems, including `missing`, `failed`
and `rejected`. Report source/provenance status, data/segment counts, dataset
and input hashes, sampler diagnostics, PPC, temporal/segment residual
structure, physical gate reasons, posterior intervals and compute cost.
Show uncertainty relative to transit scale and the observed cadence regime.
Catalog comparisons are contextual: catalog ephemeris/duration condition the
analysis, so this is not independent catalog validation.

Machine-readable data preparation manifests live only under
`publication/observational/PUB-05/<target>/<preparation_id>/` and reference
read-only original RAW inputs. Silver extraction, phase construction, segment
normalization, dataset hashing and thinning reuse existing implementation
primitives. Neither historical outputs nor global target configurations are
changed. Tests cover target isolation, byte hashes, rejection, error scaling,
cadence roundoff, deterministic identities and full selection accounting.

Engineering verification (scientific Python environment, WSL):

```sh
python -m unittest tests.test_publication_observational -v
```

After final protocol freeze, the shared adapter can be invoked with
`PYTHONPATH=src python -m publication.observational <frozen-protocol.json>
--target <selected-slug> --run-id <new-preparation-id>`. It refuses a draft by
default and always rejects an existing output directory. The explicit
`--pilot` flag labels engineering preparation as PILOT; such outputs are not
automatically final evidence.

No PUB-05 scientific result, gate pass rate or generalization conclusion is
available from this draft. Completion requires the frozen final batch,
all-target aggregates, figures/tables and a registry-backed interpretation.

## Engineering evidence (not final scientific results)

On 2026-09-26 all six `test_publication_observational` tests passed, as did
focused Ruff validation. An additional temporary-workspace smoke copied the
12 existing selected RAW products, verified their hashes, and passed shared
preparation for all four locally available targets without inference. It
recovered 3909 / 115363 / 5358 / 50529 quality-selected rows and
1027 / 3000 / 612 / 3000 modeling rows for HAT-P-7, Kepler-10, TrES-2 and
HD 189733 respectively. Every preparation was marked PILOT; all generated
files were temporary and were removed by the fixture cleanup, with original
RAW files untouched.

The temporary process read the draft before the source-consistency revision
that paired HD 189733's period/duration with its Baluev epoch. Thus its HD
preparation is evidence of adapter mechanics only, not a dataset validated
against the final frozen ephemeris. No posterior was computed or inspected to
make that revision. The final five-target preparation and inference still
require protocol freeze, acquisition completion and versioned artifacts.
