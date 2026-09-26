# Publication execution log

## Scope and protected evidence

Work is confined to `publication-grade-validation`. The protected `main` and
backup baseline is `7489a90689a753bea5243f86c1489329916c98e2`.
`scientific_003` is historical validated evidence, not a destination for any new
inference or artifact regeneration. New outputs are isolated under `publication/`,
`artifacts/publication_campaign/` and `reports/publication_campaign/`.

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
- Pre-final review caught a potential pilot/final realization reuse: the initial
  seed derivation omitted study mode. Before any final batch, final streams were
  separated as `final_v1_*` from pilot streams; regression tests also prohibit
  changing a final replicate's data seed merely by renaming a retry. Original
  pilot artifacts remain unchanged. No final dataset was executed under the
  earlier ambiguous namespace.

This is a living execution record, not the final scientific report. Terminal
run artifacts and protocol amendments are never rewritten to improve outcomes.

## Revised user execution contract: autonomous runner

The user instructed that Codex must not babysit hours/days of final computation.
The runner is therefore delivered for independent user execution, with a 36h
soft budget, frozen seeds and 117 declared jobs. No final scientific campaign
was launched during engineering. See `COMPUTE_BUDGET_AMENDMENT.md` for the
pre-result reduction from 100 replicates/scenario to 20 in four main regimes,
deferral of OU/M6, and three pairs per ablation design.

The actual integration smoke `runner_smoke_v2` passed: graceful stop, resume,
completed-output preservation, second-resume idempotence, classified technical
retry with original failure retained, and scientific rejection without retry.
The real 20-draw physical fit was rejected, not promoted. The earlier v1 harness
failed on a transient DrvFS state-file read; bounded retry was added and the
original attempt was preserved.

Independent juliet engineering uncovered an ignored `rstate` argument in its
dynesty3 introspection path. The failed nondeterministic smoke is preserved.
A transparent constructor-signature bridge passes the explicit Generator;
two subsequent identical tiny pilots produced identical canonical posterior
hashes. Both were correctly rejected by their deliberately insufficient
nested-sampling budget. This validates plumbing, not external posterior agreement.

Final preflight verifies the actual two interpreters, package locks, installed
benchmark source hashes, protected baseline/ref identities, and all 15 target
source FITS before spending the campaign budget. Review also added embedded
dataset-ID rejection, float64 enforcement, full imported-source binding and
explicit temporal-diagnostic unavailability after thinning.

The final reporting review added the predeclared P3 distribution and predictive
figures, with bijective row mapping to the exact shared input and explicit
unavailable placeholders for missing evidence. P2 bias-versus-SNR now uses a
post-inference known-white-noise design metric, never truth-informed fitting or
a claimed detection significance. These derived-only changes do not resample or
alter any existing scientific result. The source/seed ledger is refreshed before
any final campaign starts; completed engineering attempts retain their original
source identity. Nested Python entry points also have an explicit LF checkout
policy so Windows does not silently change content-addressed scientific sources.

Pre-handoff checkpoint: `publication/validation/handoff/handoff_v4/validation.json`
passed against source commit `7dcc8153f9eae0c2299747ed2e02c73ee4d67d7a`:
201 practical tests, zero skips, lint/static contracts, historical artifact
validation, a 117-job final dry run, uninitialized final status and regenerated
smoke report freshness. The two P3 plots were also visually inspected using a
clearly synthetic test fixture, not new benchmark evidence. PNG/NPZ artifacts
and campaign logs have binary-preserving Git attributes to protect exact bytes.
Final science remains unstarted; the full paper release audit intentionally
remains incomplete until actual final evidence and scientific review exist.

Subsequent hostile review found that a passing global freshness check did not
cover stale family-level report/manifests left by an earlier aggregation. The
v4 checkpoint is retained as evidence of its actual limited check, not promoted
as verification of every nested report. The final correction regenerates family
metadata from the same evidence snapshot and verifies declared child manifests;
regression tests explicitly alter a family report to require rejection.
