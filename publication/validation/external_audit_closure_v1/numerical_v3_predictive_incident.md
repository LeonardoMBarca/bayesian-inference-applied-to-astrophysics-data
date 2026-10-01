# Numerical complement v3: posterior-predictive trace defect

Discovered during the live `tcc_numerical_complement_v3` campaign on
2026-10-01 UTC, after PUB-02 finished and before PUB-03 finished. A graceful
stop was requested through the campaign CLI. The active PUB-03 worker finished
and the controller checkpointed `STOPPED` at 01:57:47 UTC: 8 `COMPLETED`, 5
`COMPLETED_REJECTED`, 11 `PLANNED`, no technical failures, and aggregation
completed. Of the 13 completed attempts, six PUB-02 direct-coordinate fits
are unaffected by this specific defect; six PUB-02 standardized fits and the
one PUB-03 standardized fit have invalid predictive conditioning. No attempt
is to be overwritten, deleted, or silently reclassified.
The earlier `t0_coordinate_pilot_v1` standardized fit used the same trace
retention path and its PPC is likewise not trustworthy; it was explicitly a
pilot and never belonged to the final evidence denominator. A repository-wide
search of executed `inference_config.json` files found no other pre-repair
standardized fits. Historical direct-coordinate `scientific_003` is not
affected by this defect.

## Evidence and mechanism

The frozen standardized-coordinate model samples `t0_standardized ~ N(0, 1)`
and defines `t0 = 0.025 * t0_standardized` for the deep-short synthetic case.
At matched physical coordinates, the direct and standardized likelihoods,
priors (including the Jacobian), and gradients passed the pre-run tests in
`tests/test_t0_parameterization.py`. However, the publication inference call
explicitly requested only `PARAMETERS`, which contains deterministic `t0`
but omits its free parent `t0_standardized`. Direct inspection of the sealed
standardized `rep_0000` NetCDF posterior group found `t0` but no
`t0_standardized`. PyMC's posterior-predictive reconstruction therefore did
not condition on the sampled center coordinate. This is an inference from
the saved-variable contract and the empirical predictive signature; it will
be tested directly in the repair before any new final campaign.

All three standardized deep-short PUB-02 runs have PPC rejection and
lag-one residual correlations approximately 0.79; the matched direct runs
have lag-one correlations between approximately -0.01 and 0.03. The
standardized residual SD is approximately 2.3 versus approximately 1.0 for
direct, while physical posterior centers are close in the paired numerical
table. This is consistent with predictive reconstruction using an
unspecified center, not with a proven failure of the standardized posterior
itself. The nominal PPC point coverage can still appear acceptable because
an over-dispersed predictive distribution is not an adequacy test alone.

## Scientific disposition

The affected v3 predictive summaries, residual correlations, PPC gates,
scientific-gate classifications, and any benchmark predictive agreement are
**invalid for a direct-versus-standardized scientific comparison**. Retain
their original bytes and recorded statuses as an audit trail, but do not
count them as evidence that standardized coordinates physically fail. The
sampled posterior and sampler diagnostics may still be informative about
numerical behavior, conditional on an independent trace audit; this is not
authorization to promote the v3 campaign's results to final claims.

The repair must retain every model free random variable needed for posterior
predictive conditioning, assert that the stored trace contains them, add a
regression test that detects the missing-parent case, and demonstrate a
correctly conditioned predictive curve on a small smoke experiment. A new
campaign identity and prospectively frozen protocol/seed ledger are required
for final evidence. Do not resume v3 merely to obtain a better-looking gate
result. No gate threshold, prior, seed, or completed artifact is to change.

## Repair verification before v4 freeze

The repaired inference source saves every `model.free_RVs` coordinate in
addition to reporting variables and fails closed before PPC if any free
coordinate is absent. The regression suite has a test reproducing the v3
missing-parent shape and a fixed-draw comparison of direct and standardized
predictive curves at identical physical parameters. The exact scientific
environment passed 356 tests. A separate **PILOT** with two chains and only
40 tune/40 draws per chain saved `t0_standardized` in the HDF5 posterior;
the old v3 trace did not. This pilot had 25 divergences and a rejected gate,
so it is only a trace-path smoke check, not final scientific evidence or a
claim that the coordinate change is effective. Its config is
`configs/publication/t0_predictive_fix_smoke_v1.json`; its isolated local
output is `artifacts/publication_validation/t0_predictive_fix_smoke_v1/`.
