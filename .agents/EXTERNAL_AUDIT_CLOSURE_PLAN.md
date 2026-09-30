# External-audit closure — living evidence plan

Audit starting commit: `4022d16aded5d218d0921a72817ecd05da4df6f1`.
Scope: publication-grade-validation only; preserve scientific_003, 117/400 jobs,
118/400 attempts, all historical scientific outputs, and tcc_evidence_v1.
No historical MCMC rerun, no public archive upload, no main merge.

| ID | Evidence/finding | Class | Remediation/files | Test / done criterion | New inference / cost | Status / final evidence |
|---|---|---|---|---|---|---|
| A0 | Historical byte identity must survive remediation | integrity | freeze_audit_protection.py + protected_snapshot.json | Pre/post exact SHA/size checks | No; minutes I/O | PASS: 7,041/7,041 original files rechecked with zero errors; original `scientific_003` and both campaigns retained |
| A1 | CI RAW checksums differ after Git checkout | bug/operational | raw_byte_audit.py, .gitattributes, verified original bytes only | All manifest paths; real false/true autocrlf checkout; tamper regression; no manifest rehash | No; minutes I/O | FIXED LOCALLY: 445/445 exact in both checkout modes; commits `8bb69f5`, `4619ae9`; independent restore passed 8,201 checksums, final remote CI still unverified |
| A2 | Local green test receipt did not establish remote CI | operational | CI exact-vs-compatible environment receipts | Actual GitHub workflow for final pushed SHA green | No MCMC batch; smoke only | PENDING final pushed SHA and remote workflow receipt; earlier `8bb69f5` lint failure detected and fixed in later source |
| A3 | Earlier aggregate cross-check reused summary algorithm | evidence | independent trace_audit.py + tests | All 480 traces means/SD/ETIs and separate-cohort aggregate reconciliation | No inference; minutes I/O | PASS: `publication/validation/trace_audit_v1/`, 80 and 400 kept separate; zero metric discrepancies at declared tolerances |
| A4 | Historical joint gate conflated with parameter-recovery claims | semantic/scientific | Versioned claim authorization, parameter/regime evidence | Provenance/computation/PPC/scale/information/claim separated; null != false | No | IMPLEMENTED; v2 synthesis generation/check in progress; weak-regime undercoverage retained |
| A5 | Adjacent-period t0 trapping; causal mechanism unproven | numerical | New standardized parameterization study, equivalence tests, protocol | Same prior/likelihood incl Jacobian/gradient; controlled multi-realization study; preserve rejected traces | Two smoke fits only; 24 prospective final jobs prepared | MECHANISM AUDITED; final efficacy PENDING frozen ledger/execution; pilot has two tiny rejected fits, no final claim |
| A6 | Ablation nominal baselines fail numerical gate | numerical/scientific | Targeted higher-accuracy prospective cohort | No threshold change; all pairs retained; qualified historical effects | Nine jobs within same 24-job prospective study | PENDING prospective execution; historical divergent references remain qualified |
| A7 | Observational residual correlation lacks cause isolation | scientific limitation | Read-only time/segment/gap/in-out residual audit | Existing points, ordering and spacing verified; hypotheses not GP claims | No | REVIEWED: `residual_review_v2`, 5 targets/15 segments, input flux identity checked; cause remains a scientific limitation |
| A8 | Flat storage manifest misses transitive intermediates | integrity/operational | schema-aware evidence_archive.py + archive/restore | Explicit schemas, conflict/cycle/path protections; separate-checkout exact bytes | No; local 496,436,552-byte ZIP | RESTORE PASSED: 8,201 checksums and 1,562 restored external members in new clone; one later-edited historical document resolved via exact original Git blob; public archive still absent |
| A9 | Legacy release checker counts zero; exit1 accepted indiscriminately | bug/semantic | Campaign-aware release audit + receipt validation | 517 jobs/518 attempts; integrity vs outcome vs readiness; unexpected error fails | No | CODE/TESTS IMPLEMENTED; final structured release receipt pending v2 synthesis |
| A10 | Need source-complete TCC v2, not historical rewrites | editorial/scientific | reports/publication_synthesis/tcc_evidence_v2 + closure report | Generated quantitative claims/denominators, exact source inventory, hostile second pass | No | SOURCE/TEMPLATES READY; v2 build/hostile review in progress |

Acceptance is evidence-based, not code-based. Findings may end as corrected,
bounded scientific limitation, or an explicitly pending prospectively frozen
execution. A pending new experiment is never called a completed validation.
