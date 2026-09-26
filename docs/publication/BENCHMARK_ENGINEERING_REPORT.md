# P3 independent-benchmark engineering validation

Date: 2026-09-26. This report covers installation, adapter wiring and numerical checks, **not final posterior validation**. Scientific execution is deferred to the user's autonomous campaign under the committed PUB-03 protocol.

## Evidence

- Environment: `publication/environments/benchmark-environment.json`; 119 pinned distributions, Python 3.12.14, juliet 2.2.10, batman-package 2.5.3, dynesty 3.1.0. `pip check` and nine library imports passed. Canonical M5 environment unchanged.
- Source/distribution archive hashes, compiler identity and exact conda runtime are captured with the lock. Separate installation history preserves the missing-ensurepip and missing-Python.h failures.
- batman's distribution version is 2.5.3 while its module `__version__` reports 2.5.1. Both observed identities are recorded; the discrepancy was not silently rewritten.
- Optional upstream warnings for zeus and jax/kelp are expected; neither is used by this circular white-noise benchmark.
- Twelve lightweight unit tests passed, including hashes/order/segments, exclusive run reservation, ppm/parameter mapping, midpoint stencil, deliberate budget termination, RNG introspection, unavailable temporal diagnostics and width disagreement despite identical means. Lint passed.

## Independent physical primitive

Canonical exoplanet-generated fixture: `publication/engineering/benchmark_forward_fixture_v1.json`. Checked with independent batman under identical quadrature nodes. No sampler or posterior comparison enters this fixture.

| Fixture | Max absolute relative-flux difference | Predeclared tolerance | Outcome |
|---|---:|---:|---|
| deep_long | 1.09495990e-9 | 2e-8 | pass |
| shallow_short | 4.01211309e-9 | 2e-8 | pass |
| grazing_long | 5.42521583e-10 | 2e-8 | pass |

A finite fixture grid is not a global precision guarantee. The final physical comparison also requires matched priors, errors, observations and sampler adequacy.

## Installed-juliet statistical contract

Sixty heteroscedastic observations with two exact exposure durations and shared nuisance parameters give maximum flux error 2.22044605e-16 and Gaussian log-likelihood difference 2.61479727e-12. These test the actual installed `juliet.load`, `juliet.model.generate` and `get_log_likelihood` interfaces.

The baseline is truly additive through a constant linear regressor, not a misuse of mflux. Jitter is converted from fractional flux to ppm. Exposure nodes match M5 midpoint Riemann integration through a declared batman stencil-span conversion; physical exposures are unchanged.

## Preserved engineering failure and amendment

`benchmark_adapter_check_v1.json` remains **failed**. Forward/likelihood tests passed, but an initially absolute 1e-8 ppm tolerance on two inverse-CDF algorithms was too restrictive at quantile 0.999999: the measured quantile difference is 2.1847881725989282e-8 ppm, equivalent to 2.1847881725989282e-14 relative flux.

The v2 engineering amendment checks the defining CDF identity within 32 machine epsilons, and the corresponding local inverse-CDF conditioning bound `32*eps/pdf(x)`. The measured CDF error is 6.077471157280833e-17. A deliberately 1% wrong prior scale is rejected. This changes only the numerical equivalence test: no prior, data, likelihood, final scientific gate or posterior result was changed. The original failing check is retained alongside v2.

## Worker and reproducibility boundary

`scripts/run_publication_benchmark.py --input PATH --config PATH --output RESERVED_RUN_DIR` writes a new juliet_native subdirectory and exclusive benchmark_started marker. The campaign reserves the parent. Final mode verifies a committed unchanged protocol, frozen model/sampler configuration and the locked external environment. Existing attempts cannot be silently reused.

The first tiny sampler smoke exposed a real compatibility defect: juliet 2.2.10 silently drops `rstate` when dynesty 3.1.0 inherits its constructor. `benchmark_worker_smoke_v1` preserves the two nondeterministic outputs. The worker now uses a transparent subclass with explicit `rstate`, delegating all computation unchanged to installed dynesty and restoring the class after the single-process fit. No installed package file is edited.

juliet's native equal-weight posterior resampling also does not supply an RNG. The worker preserves native artifacts and uses raw nested weights with a separate seeded resampling Generator for canonical `posterior_samples.npz`. Only canonical arrays may feed distribution comparisons. Raw weighted arrays, seeded PPC, diagnostics and checksums are also retained.

`benchmark_worker_smoke_v2/smoke_report.json` passes: two 60-row, 20-live-point, maxcall-100 pilots produce the same canonical posterior hash, parse successfully and both remain scientifically rejected for budget termination. They validate wiring and determinism only; tiny posterior summaries are not final benchmark evidence.

`compare_posterior_arrays` produces center, 50/80/94 interval, width, Wasserstein and CDF metrics for seven scientific parameters. It does not emit iid KS p-values, equate a nonsignificant difference with equivalence, or promote a comparison whose inputs fail diagnostics.

## Reproduction commands

See `publication/environments/BENCHMARK_README.md` for clean installation and checks. Run lightweight tests with `python -m unittest tests.test_publication_benchmark -v`. Independent numeric checks require the isolated environment. Reproduce the deliberately inadequate sampler smoke with `python scripts/smoke_benchmark_worker.py --output NEW_DIRECTORY`. Final posterior comparisons remain deferred campaign steps; the artifacts above alone do not complete PUB-03.

## Whole-campaign environment and input preflight

`publication/engineering/campaign_execution_preflight_v1.json` records an actual
read-only readiness check, before final execution. It verified the configured
scientific interpreter `/home/leonardo_barca/mc3/bin/python3.14` (Python 3.14.6
and all 19 direct pinned distributions), the isolated external interpreter
`/home/leonardo_barca/publication-benchmark-conda/bin/python` (Python 3.12.14,
119 distributions and 13 installed juliet/batman Python-source checksums), all
26 protected baseline artifacts including the original trace, the PUB-03 input,
and all 15 preselected PUB-05 RAW FITS inputs. No scientific data were changed.

`campaign_preflight.validate_execution_environment` performs these checks before
the first final job, not after P2 consumes the budget. Missing external baseline
trace data are a restoration blocker: the guard never regenerates or overwrites
historical results. Smoke and aggregation-only modes do not require this final
execution guard. Four mocked preflight tests and three lightweight canonical
environment-guard tests passed in addition to the 12 benchmark tests.

Readiness of environments and inputs is distinct from the separate committed
protocol/plan/source checks. This engineering report does not assert that a
final batch has started, finished or scientifically passed. Exact package pins
and the recorded Python sources also do not prove bit-identical native binary
builds or a complete historical transitive dependency lock.
