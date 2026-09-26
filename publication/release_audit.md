# Publication release audit

Status: **incomplete**. Release approved: `False`.

Declared final attempts: 0. Failed checks: 17.

| Check | Status | Reason |
|---|---|---|
| protected_baseline | passed |  |
| registry_schema | passed |  |
| registry_integrity | passed |  |
| runtime_snapshot | passed |  |
| scientific_runtime | passed |  |
| paper_manifest | failed | [Errno 2] No such file or directory: '/mnt/c/Users/Leonardo Barca/Desktop/workspace/personal/bayesian-inference-applied-to-astrophysics-data/publication/paper_artifact_manifest.json' |
| paper_manifest_schema | failed | Missing/unknown publication-paper-artifacts-v1 schema |
| required_family:PUB-02 | failed | Mandatory scientific family has no declared final batch and frozen protocol |
| required_family:PUB-03 | failed | Mandatory scientific family has no declared final batch and frozen protocol |
| required_family:PUB-04 | failed | Mandatory scientific family has no declared final batch and frozen protocol |
| required_family:PUB-05 | failed | Mandatory scientific family has no declared final batch and frozen protocol |
| m6_disposition | failed | Unexecuted M6 requires an explicit protocol-backed methodological limitation |
| environment_locks | failed | Paper manifest lacks the complete scientific environment lock identity |
| benchmark_environment | failed | 'benchmark_environment' |
| claim_ledger | failed | No auditable manuscript claim ledger |
| review:tests | failed | 'reviews' |
| review:clean_room | failed | 'reviews' |
| review:public_safety | failed | 'reviews' |
| review:citation | failed | 'reviews' |
| citation_metadata | failed | 'citation' |
| reproducibility_manifest | failed | Reproducibility manifest is absent, incomplete, or has an unknown schema |
| committed_release_evidence | failed | Command '['git', '-C', '/mnt/c/Users/Leonardo Barca/Desktop/workspace/personal/bayesian-inference-applied-to-astrophysics-data', 'ls-files', '--error-unmatch', '--', 'CITATION.cff', 'environment.yml', 'publication/baseline/manifest.json', 'publication/paper_artifact_manifest.json', 'publication/registry.json', 'pyproject.toml', 'requirements.txt', 'scripts/aggregate_publication_campaign.py', 'scripts/publication_campaign_job.py', 'scripts/publication_inventory.py', 'scripts/run_publication_batch.py', 'scripts/run_publication_benchmark.py', 'scripts/run_publication_campaign.py', 'scripts/summarize_publication.py', 'scripts/validate_publication_campaign_smoke.py', 'scripts/validate_publication_handoff.py', 'scripts/validate_publication_release.py', 'scripts/verify_publication_campaign.py', 'src/publication/__init__.py', 'src/publication/ablations.py', 'src/publication/acquisition.py', 'src/publication/batch.py', 'src/publication/benchmark.py', 'src/publication/benchmark_runner.py', 'src/publication/calibration.py', 'src/publication/campaign.py', 'src/publication/campaign_plan.py', 'src/publication/campaign_preflight.py', 'src/publication/campaign_reporting.py', 'src/publication/campaign_worker.py', 'src/publication/contracts.py', 'src/publication/environment_guard.py', 'src/publication/handoff_validation.py', 'src/publication/inference.py', 'src/publication/numerical_checks.py', 'src/publication/observational.py', 'src/publication/release.py', 'src/publication/reporting.py', 'src/publication/simulation.py', 'src/publication/target_reporting.py']' returned non-zero exit status 1. |

Validation approval is limited to declared contracts; it does not prove novelty, scientific truth, authorship, or absence of all privacy/licensing risks.
