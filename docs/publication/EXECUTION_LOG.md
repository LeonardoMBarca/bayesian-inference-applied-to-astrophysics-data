# Publication execution log

## Scope and protected evidence

Work is confined to `publication-grade-validation`. The protected `main` and
backup baseline is `7489a90689a753bea5243f86c1489329916c98e2`.
`scientific_003` is historical validated evidence, not a destination for any new
inference or artifact regeneration. Publication outputs live under `publication/`.

## Dependency-aware implementation and acceptance plan

1. PUB-00: freeze and verify baseline bytes; reject collisions and identity
   changes; machine-readable declared attempts, immutable status history and
   protocol amendments. Acceptance: deterministic regression tests and hash
   verification of historical evidence, including the local trace.
2. PUB-01: primary-source literature matrix and pre-outcome external-tool choice.
   Acceptance: capability claims cited; unknown distinguished from absent;
   no unsupported priority/novelty claim.
3. PUB-02: physical synthetic generator, truth-blind subprocess inference,
   pilot cost measurements, then commit final scenario/replicate/metric protocol
   and complete registry before execution. Acceptance: all attempts accounted
   for, coverage uncertainty and both numerical and operational denominators,
   bias/width/failures, figures/tables and machine-readable evidence.
4. PUB-03: isolated independently implemented transit benchmark, with frozen
   observation/prior/likelihood contract before final comparison. Acceptance:
   comparable distributions and explicit mismatches; no agreement-driven tuning.
5. PUB-04: frozen paired ablations and negative controls. Acceptance: quantified
   effects and distinct provenance, sampler, PPC and interpretation decisions.
6. PUB-05: preselected diverse real targets, shared preparation and model.
   Acceptance: every declared target attempted and retained, including failures.
7. PUB-06: only after PUB-02–04 are scientifically complete, explicit separately
   versioned temporal covariance with synthetic controls before observations.
8. PUB-07–08: complete evidence-linked artifacts, strict release validation,
   hostile-review audit, consolidated report and manuscript/TCC source inventory.
   Release readiness must fail closed when required scientific evidence is absent.

## Initial findings

- The inherited M5 likelihood is independent Normal with measurement variance
  plus inferred white-jitter variance. It is not a correlated-noise model.
- The historical sampler helper can retry automatically on divergences. New
  publication inference uses one declared attempt without automatic retries.
- Default M5 radius priors use a catalog-derived center. Synthetic publication
  priors are instead declared independently of injected values; fixed-truth
  coverage is not mislabeled as prior-predictive simulation-based calibration.
- A temporal residual check is an additional publication diagnostic, not a
  retroactive alteration of historical M5 gates.
- Available Linux compute: 4 logical CPUs and approximately 4.8 GiB RAM. Pilot
  timing will inform the final precommitted simulation count and precision.

## Evidence recorded during execution

- Baseline manifest: `publication/baseline/manifest.json`; 26 protected artifacts
  verified, including the 239 MB local trace. Historical environment locks are
  copied byte-for-byte, not overwritten.
- `python -m unittest tests.test_publication_inference -v`: 6 tests passed;
  collision, input identity, explicit prior validation, equal-tailed interval
  semantics, temporal-pair boundaries and truth-blind import surface.
- No final scientific publication experiment has yet been promoted.
- Practical suite at initial implementation checkpoint: 95 tests passed, zero
  skips, including existing scientific artifact contracts and the new simulator.
- First deep-transit pilot sampled four chains (500 tuning + 500 retained draws
  each) in 135 seconds but failed during summary generation because ArviZ 1.x
  requires `ci_prob` rather than `hdi_prob`. The failed run and trace are retained;
  the adapter was corrected and a regression smoke test added. This is debugging
  evidence, not a final scientific result or a seed eligible for selection.
- Literature review is explicitly scoped and credits prior calibration,
  transit-injection, provenance and reproducibility work. The separate benchmark
  choice was made from likelihood compatibility, before posterior outcomes.

This is a living execution record, not the final scientific report. Terminal
run artifacts and protocol amendments are never rewritten to improve outcomes.
