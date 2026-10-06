# AGENTS.md

## Current scope: maintain an auditable research repository

The owner authorized promotion of the consolidated `publication-grade-validation`
state to `main` on 2026-10-06. `main` is now the public entry point; it is no longer
the old baseline branch. The scientific source snapshot is
`127089538dbf2e233bce0d5e92c3977e115bb86b` and the canonical evidence index is
`publication/TCC_EVIDENCE_INDEX.json` (synthesis `tcc_evidence_v3`).

The prior baseline is commit `7489a90689a753bea5243f86c1489329916c98e2`, retained
on `backup-main-2026-08-24`. Never overwrite the `scientific_003` run or sealed
campaign evidence. Publication planning documents under `.agents/` are historical
research plans, not permission to restart completed campaigns or implement M6
without a new explicit request.

## Read before working

1. The user's current request and its scope.
2. `README.md`, `docs/REVIEWER_GUIDE.md`, `docs/REPRODUCIBILITY.md`.
3. `publication/TCC_EVIDENCE_INDEX.json` and the relevant frozen artifacts.
4. `CONTRIBUTING.md`, `SECURITY.md` and the relevant `.agents/skills/` skill.
5. The actual code, configuration and tests affected by the proposed change.

For documentation work use `documentation-artifact-consistency`. For a newly
authorized research phase, read `PUBLICATION_PLAN.md`, `EXPERIMENT_REGISTRY.md`
and `publication-grade-research` plus the focused skill. Do not claim the entire
publication program is complete merely because its existing campaigns ended.

## Scientific invariants

- Preserve RAW bytes, units, time references, exposure and segment identity.
- Preserve effective input hashes, protocols, seeds, attempts and all outcomes.
- New experiments require new IDs and a protocol frozen before final results.
- No truth leakage, seed/target cherry-picking or relaxed gates to rescue results.
- Keep sampler, predictive and joint decisions separate. Unassessed and
  invalidated diagnostics are not observed scientific failures.
- Fixed-truth coverage is not SBC; ETIs are not HDIs; paired fits are not
  independent datasets. Never pool the 541 jobs into a calibration denominator.
- M5 uses independent heteroscedastic Normal errors plus white jitter. It has
  no temporal covariance/GP and does not jointly infer stellar properties.
- Matching a catalogue-informed prior to the same catalogue is not independent
  validation. Numerical proximity to juliet does not establish model adequacy.
- Negative and inconclusive outcomes remain eligible evidence under explicit
  interpretation limits. Do not promise a grade, paper acceptance or universality.

## Engineering and public changes

Keep entry points thin and reusable code in `src/`. Add regression tests for
behavior changes; run relevant tests and state their actual scope. Full campaigns
are not routine CI. Documentation-only changes do not require new MCMC.

Never rewrite sealed outputs to agree with current prose. Generate corrected
derivatives in new destinations and link their original sources. Historical
reports may retain statements about their access status at freeze time; describe
current public access in living documentation without retroactively editing them.

Do not publish credentials, personal identifiers, residential addresses, signed
records or individually watermarked academic documents. Preserve necessary
administrative copies outside the public repository. Current-tree removal does
not clean history. No force-push, historical purge, branch deletion, DOI creation
or external upload without explicit owner authorization.

Do not weaken validation to obtain green CI. Report missing external bundles as
missing, not as available or reproduced. Existing citation metadata do not imply
a deposited paper release. Verify the final remote SHA after writes and report
CI for that exact SHA when it is available.
