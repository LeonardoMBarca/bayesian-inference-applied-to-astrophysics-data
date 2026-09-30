# External-audit closure — living evidence plan

Audit starting commit: `4022d16aded5d218d0921a72817ecd05da4df6f1`.
Scope: publication-grade-validation only; preserve scientific_003, 117/400 jobs,
118/400 attempts, all historical scientific outputs, and tcc_evidence_v1.
No historical MCMC rerun, no public archive upload, no main merge.

| ID | Evidence/finding | Class | Remediation/files | Test / done criterion | New inference / cost | Status / final evidence |
|---|---|---|---|---|---|---|
| A0 | Historical byte identity must survive remediation | integrity | freeze_audit_protection.py + protected_snapshot.json | Pre/post exact SHA/size checks | No; minutes I/O | IN_PROGRESS |
| A1 | CI RAW checksums differ after Git checkout | bug/operational | raw_byte_audit.py, .gitattributes, verified original bytes only | All manifest paths; real false/true autocrlf checkout; tamper regression; no manifest rehash | No; minutes I/O | IN_PROGRESS |
| A2 | Local green test receipt did not establish remote CI | operational | CI exact-vs-compatible environment receipts | Actual GitHub workflow for final pushed SHA green | No MCMC batch; smoke only | PLANNED |
| A3 | Earlier aggregate cross-check reused summary algorithm | evidence | independent trace_audit.py + tests | All480 traces means/SD/ETIs and separate-cohort aggregate reconciliation | No inference; minutes I/O | IN_PROGRESS |
| A4 | Historical joint gate conflated with parameter-recovery claims | semantic/scientific | Versioned claim authorization, parameter/regime evidence | Provenance/computation/PPC/scale/information/claim separated; null != false | No | PLANNED |
| A5 | Adjacent-period t0 trapping; causal mechanism unproven | numerical | New standardized parameterization study, equivalence tests, protocol | Same prior/likelihood incl Jacobian/gradient; controlled multi-realization study; preserve rejected traces | Pilot allowed; estimate before final | PLANNED |
| A6 | Ablation nominal baselines fail numerical gate | numerical/scientific | Targeted higher-accuracy prospective cohort | No threshold change; all pairs retained; qualified historical effects | New small study only after frozen budget | PLANNED |
| A7 | Observational residual correlation lacks cause isolation | scientific limitation | Read-only time/segment/gap/in-out residual audit | Existing points, ordering and spacing verified; hypotheses not GP claims | No | PLANNED |
| A8 | Flat storage manifest misses transitive intermediates | integrity/operational | schema-aware evidence_archive.py + archive/restore | Explicit schemas, conflict/cycle/path protections; separate-checkout exact bytes | No; local disk/time cost measured | IN_PROGRESS |
| A9 | Legacy release checker counts zero; exit1 accepted indiscriminately | bug/semantic | Campaign-aware release audit + receipt validation | 517jobs/518attempts; integrity vs outcome vs readiness; unexpected error fails | No | PLANNED |
| A10 | Need source-complete TCC v2, not historical rewrites | editorial/scientific | reports/publication_synthesis/tcc_evidence_v2 + closure report | Generated quantitative claims/denominators, exact source inventory, hostile second pass | No | PLANNED |

Acceptance is evidence-based, not code-based. Findings may end as corrected,
bounded scientific limitation, or an explicitly pending prospectively frozen
execution. A pending new experiment is never called a completed validation.
