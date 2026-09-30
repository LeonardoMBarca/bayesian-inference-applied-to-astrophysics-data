# Derived-report JSON round-trip issue — not scientific invalidation

This attempt passed 263 unit/integration/smoke tests, lint, static validation
and historical-baseline artifact validation. The paper-release gate rejected
the incomplete release as expected.

During visual review, the preview and final figures differed in scenario order.
A direct read-only check of the sealed summary established:

```text
report_roundtrip_equal: False
manuscript_roundtrip_equal: True
serialized_campaign_order: ['tcc_calibration_confirmatory_v1', 'tcc_campaign_v1']
```

The summary writer sorts JSON keys, while the report and figures depended on
dictionary insertion order. Scientific values, denominators and gate decisions
were unchanged, but exact regeneration from the saved summary was inconsistent.
The expensive recursive integrity subprocess was deliberately stopped with
SIGTERM after this issue was confirmed. The harness continued and recorded
return code -15 and overall `failed`; this is not a completed integrity check.

The original derived bundle is preserved in commit
`b667748f0666f9b09a886493cb529759df453525`. Source hashes and completed test logs
remain in this directory. The fix specifies presentation order and tests text
and PNG equality across a sorted-key JSON round trip. Final validation must
use the successor `post_campaign_audit_v3`; v2 is not approval.

No final scientific run, trace, prior, gate, seed or input was changed or rerun.
