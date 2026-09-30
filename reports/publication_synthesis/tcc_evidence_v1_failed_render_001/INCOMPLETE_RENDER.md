# Incomplete derived report — not final evidence

The first synthesis build verified its scientific sources and recomputed the
calibration aggregates, then failed in Matplotlib while rendering coverage:

```text
ValueError: 'yerr' must not contain negative values
```

At zero/full empirical coverage, floating-point roundoff in a Wilson endpoint
created a tiny negative error-bar length. No scientific posterior, gate,
coverage estimate or stored uncertainty interval was changed. The correction
clips only rendering roundoff and rejects materially inconsistent intervals;
a regression test covers both boundary cases.

This incomplete directory was moved intact to preserve the failed generation.
It has no artifact manifest and must not supply TCC/paper claims. Its partial
derived files remain locally available; only this receipt is versioned.
The authoritative replacement is `../tcc_evidence_v1/` once sealed and verified.

Future renders use a temporary directory and publish their manifest last.
No campaign, inference or preprocessing was rerun for this correction.
