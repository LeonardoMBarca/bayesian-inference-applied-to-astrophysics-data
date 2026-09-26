# Kepler-4 b engineering preparation

Status: passed; purpose: PILOT. No sampler was executed and no posterior or scientific interpretation claim is available.

| Check | Result |
|---|---:|
| Exact preselected FITS products | 3 |
| Preserved segments | 3 |
| Silver rows | 6469 |
| Quality-selected rows | 5463 |
| Quality-filter exclusions | 1006 |
| Modeling rows after window/thinning | 1052 |
| Median exposure (seconds) | 1765.462885941888 |
| Median normalized measured error | 0.00007006273881415837 |

Dataset: `kepler_4_b-0d6f5de5a962f7ed`.
Input SHA-256: `dbed4135314849f0d12826c86d67b7d1ab18c3563f245424563fb2a8bbcc1caa`.
All original row identities are unique; every modeling row matches the target and dataset ID. All generated CSV hashes and all three original FITS hashes passed readback. The frozen source inventory was also checked in WSL: all 15 products across all five selected targets match their SHA-256 values.

Authoritative values, exact manifest hash, generated-file checksums and verification command: `publication/validation/kepler_4_engineering_preparation.json`.
Preparation manifest: `publication/observational/PUB-05/kepler_4_b/engineering_prep_v1/preparation_manifest.json`.

The three new files were acquired only after selection commit `c8efd26c4df1d944628a1f1c845b459c88fcd681`. This pilot reused shared Silver extraction, segment normalization, Gold identity and deterministic M5 thinning without modifying historical RAW/Silver/Gold. Its preprocessing input is new and isolated; it does not replace a final campaign job. Existing preparation directories are never overwritten.

Windows PowerShell 5.1 could not resolve a long TESS path during an inventory check; the same existing bytes were successfully hashed through WSL. Use the campaign's configured WSL interpreter, not that legacy path-resolution route.

