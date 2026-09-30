# Storage of final campaign evidence — 2026-09-30 audit

The scientific campaigns are complete locally. Public archival restoration is
still a release requirement. A local checksum match is not evidence that a
third party can obtain the same bytes from a clean checkout.

Measured local sizes at audit time, in MiB (2^20 bytes):

| Directory | Files | Total | NetCDF traces | Other evidence |
|---|---:|---:|---:|---:|
| artifacts/publication_campaign/tcc_campaign_v1 | 1,605 | 127.70 | 91.82 | 35.88 |
| artifacts/publication_campaign/tcc_calibration_confirmatory_v1 | 5,202 | 383.13 | 342.01 | 41.12 |
| reports/publication_campaign/tcc_campaign_v1 | 82 | 17.32 | 0 | 17.32 |
| reports/publication_campaign/tcc_calibration_confirmatory_v1 | 29 | 21.00 | 0 | 21.00 |
| publication/observational/PUB-05 | 36 | 363.25 | 0 | 363.25 |

These sizes describe an audit snapshot, not an archive manifest. Use file
checksums, not rounded sizes, to validate restoration. Logs are stored in a
separate tree and are not included in this table.

Keep the complete compact evidence trail in version control: frozen protocols
and job ledgers, campaign states, all attempt metadata, inputs/truth for
simulations, result and completion manifests, sampler/predictive summaries,
aggregate tables, figures and reports. Include scientific rejections and the
parent campaign's cancelled attempt. At audit start both final report trees
and the confirmatory run tree had no Git-tracked files; a later evidence commit
must be checked explicitly before claiming clean-checkout availability.

The global `*.nc` ignore rule already excludes traces from ordinary Git. Exact
historical trace restoration requires an archive identified by file SHA-256,
not merely rerunning the same seed: native environments and scheduling may
affect bytes. Regeneration is a separate reproduction experiment and must not
overwrite final sealed runs.

Two PUB-05 files exceed 100 MiB and must not be added to ordinary Git:

- `publication/observational/PUB-05/kepler_10_b/tcc_campaign_v1_kepler_10_b_attempt_000/gold_lightcurve.csv` — 109.32 MiB.
- `publication/observational/PUB-05/kepler_10_b/tcc_campaign_v1_kepler_10_b_attempt_000/silver_lightcurve.csv` — 103.78 MiB.

The HD-189733 b `gold_lightcurve.csv` and `silver_lightcurve.csv` in its
`tcc_campaign_v1_hd_189733_b_attempt_000` directory are a further 51.57 and
50.63 MiB. These full intermediate tables are regenerable from declared RAW
files, but current report validators bind their exact bytes. Until an archive
or separately audited reconstruction restores them, full recursive report
verification from a clean checkout remains unavailable. Keep the compact
`preparation_manifest.json`, `silver_fits_metadata.csv`,
`segment_diagnostics.csv` and `model_input.csv` for every target in Git.

Before public release:

1. Preserve an external bundle containing all excluded traces and bound
   observational intermediates, including rejected runs.
2. Publish a content manifest with repository-relative path, SHA-256, byte
   length, storage location and immutable archive/release identity.
3. Restore that bundle in a separate checkout and run both campaign validators
   and the synthesis validator. Record missing dependencies as failures.
4. Document redistribution rights and a data/software availability statement.
5. Archive the reviewed release and record its actual DOI only after issuance.

No remote archive, DOI, public-release safety approval or successful clean-room
restoration is asserted by this document. Never use a broad `git add` on the
observational tree before applying an explicit large-artifact storage policy.
