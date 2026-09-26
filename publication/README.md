# Publication evidence and release gates

This namespace is separate from the protected historical TCC evidence.
`baseline/manifest.json` binds the unchanged `scientific_003` result. Pilots are
debugging/sizing evidence, not final calibration results. A release validator
implementation is **not** completion of P7 or approval to publish.

The current user-launched TCC campaign is documented in
`docs/publication/CAMPAIGN_RUNBOOK.md`. Its authoritative declaration is
`configs/publication/tcc_campaign_v1_plan.json`; execution history lives under
`artifacts/publication_campaign/tcc_campaign_v1/`. The legacy registry links
this ledger but its older `expected_runs` fields are not the campaign denominator.
`python scripts/verify_publication_campaign.py` verifies campaign/report
integrity and freshness, not paper readiness. The separate full-paper release
contract below still requires evidence/claim assembly after final batches;
no automatic promotion from a completed controller state is allowed.

## Commands

```sh
# Read-only scientific verification; writes derived inventory/audit reports only.
python scripts/publication_inventory.py
python scripts/validate_publication_release.py

# Record incompleteness while other experiments are still being executed.
python scripts/validate_publication_release.py --audit --write-manifest

# Lightweight contract tests; no full scientific MCMC.
python -m unittest tests.test_publication_contracts tests.test_publication_release -v
```

Strict validation returns nonzero while required final evidence is missing or
stale. `--audit` returns successfully after recording an audit but does **not**
change `release_passed: false`. `REPRODUCIBILITY_MANIFEST.json` may therefore be
an explicitly incomplete snapshot. Its evidence excludes itself to avoid a
circular hash. It is not a release DOI or trusted timestamp.
The strict gate verifies this manifest's bound evidence, not its earlier cached
approval flag. After assembling final artifacts, generate the manifest, commit
the evidence, and rerun strict validation; an earlier incomplete snapshot never
substitutes for the current checks. The embedded validation snapshot makes its
audit hash recoverable even after a newer derived audit report is generated.

## Paper artifact contract

`paper_artifact_manifest.json` must use schema
`publication-paper-artifacts-v1`. It contains:

- `environment_locks`: `{path, sha256}` records for the scientific lock files;
- `benchmark_environment`: a JSON record reference identifying Python,
  package versions, `isolated: true`, and preserved `lock_files` references;
- `artifacts`: `{artifact_id, kind, path, sha256, sources, experiment_ids,
  regenerate_command}` records generated with `publication.release.bind_artifact`;
- `claims`: `{claim_id, kind, text, support_runs, source_artifacts}` records;
- `reviews`: references named `tests`, `clean_room`, `public_safety`, `citation`;
- `citation`: a checksummed reference to `CITATION.cff`;
- `m6_disposition`: `executed`, or a protocol-backed methodological limitation.

Artifact kinds include `aggregate`, `report`, `figure`, `table`, `limitation`,
`protocol`, and `methodology`. Every PUB-02 through PUB-05 family must have final
attempts plus aggregate/report/figure/table evidence. PUB-06 has the same
requirements if attempted. Unexecuted M6 requires a frozen committed protocol
with `execution_disposition: methodologically_blocked`, `blocking_evidence`,
and `m6_scientific_claims_allowed: false`, plus a linked limitation artifact;
it cannot be silently marked unnecessary to pass validation.

Each aggregate JSON lists its `experiment_id`, every `declared_run_paths`
entry exactly once, and `result_source_sha256` for every declared result,
including failures. The artifact's `sources` also bind these result hashes.
Tables/figures and reports are regenerated from these records; copying numbers
into a caption does not establish source identity.

Positive claims require completed final attempts with a passed scientific gate.
Negative claims may cite failed/rejected final attempts, without changing their
historical statuses. Limitation claims may cite protocol-backed limitations.
All claims must identify paper artifacts. Review JSON files require
`status: passed` and nonempty `source_checksums` mapping the actually reviewed
files to their SHA-256 values. A code-generated "passed" label does not replace
a substantive privacy, licensing, authorship or scientific review.

## Large files and reconstruction

Preserve compact configs, protocols, summaries, statuses, failure classifications,
checksums, tables and figures in version control. Large NetCDF traces may be
stored in a separately archived release bundle only if the released manifest
records each exact hash, archive location, storage/license terms and restoration
command. Until such an archive is created, do not claim that every trace is
downloadable. Strict local validation currently requires every declared artifact;
missing ignored traces are a real blocker, not an automatic pass.

For regenerated scientific results, use the exact committed protocol/environment
and a **new** attempt directory; never overwrite old outputs. Deterministic input
generation and parameter summaries are tested, but bit-identical stochastic
posterior draws across different CPUs/compilers are not promised. Restoring
archived bytes and rerunning a scientific experiment are different operations.

Paper figure/table generation commands live in each artifact manifest record.
There is no placeholder command that pretends missing final artifacts have
already been generated. The higher-level regeneration entry point is added with
the completed aggregate evidence, not as a substitute for that evidence.

## Future archive/DOI workflow — not executed

Before tagging, complete all scientific experiments and source-linked reviews,
run strict validation in a clean environment, review metadata/authors/licenses,
and archive required large evidence. `CITATION.cff` uses only the author's name
already present in `README.md` and `LICENSE`; it invents no ORCID, affiliation,
coauthor, release date or DOI. Confirm final authorship before release.

With authorization to publish, connect the repository to Zenodo and enable
archiving before creating the intended GitHub release. Zenodo documents that
new releases of an enabled repository are automatically archived; software
metadata may come from `CITATION.cff`. No repository connection, tag, release,
upload or DOI registration is performed by this validator. See the official
[repository integration guide](https://help.zenodo.org/docs/github/enable-repository/)
and [software metadata guide](https://help.zenodo.org/docs/github/describe-software/).

After deposition, verify the uploaded manifest/checksums and record the actual
version DOI and archival location. Do not insert an anticipated DOI or claim an
archive exists before checking the deposited record.
