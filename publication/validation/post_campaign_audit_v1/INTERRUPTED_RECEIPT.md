# Incomplete first post-campaign validation attempt

The practical suite passed 258 tests with zero skips. Lint, static validation
and historical baseline validation also returned zero. The synthesis check
started before the concurrent report build had finished and returned one
because its artifact manifest was absent. The paper-release gate returned
the expected nonzero result (release not approved).

The harness then failed while trying to hash that missing synthesis manifest,
so it did not write `validation.json`. Existing stdout/stderr are preserved.
This attempt is **incomplete**, not final validation approval. The harness now
records missing source paths explicitly rather than losing its failure receipt.
A later validation must run after synthesis generation and use a new output ID.

No scientific inference, gate, prior, seed or result was changed by this
validation-ordering failure. See the successor `post_campaign_audit_v2` bundle
for final checks when available.
