# RAW Git byte-transport audit

The external-audit baseline is commit
`4022d16aded5d218d0921a72817ecd05da4df6f1`. The complete current-state
manifest contains **445 payloads**. The authoritative pre-repair inventory is
`publication/validation/external_audit_closure_v1/raw_git_transport_pre_fix_checkouts.json`.

## Independently reproduced failure

Two real, separate sparse Git checkouts were materialized from the committed
objects with `core.autocrlf=false` and `core.autocrlf=true`. They do not copy
payloads from the source worktree. Their object store is shared with the source
repository, explicitly distinguishing this transport test from a remote clone
or a fully independent archival restoration.

| Surface | Exact payloads | Mismatches |
|---|---:|---:|
| Original scientific worktree | 445 | 0 |
| Baseline Git blobs | 247 | 198 |
| Fresh checkout, autocrlf=false | 247 | 198 |
| Fresh checkout, autocrlf=true | 428 | 17 |

Of the 198 mismatched blobs, 197 become the exact historical size and SHA-256
when LF is converted to CRLF. One CSV has mixed historical endings: four CRLF
and one embedded LF. Its original local 1,831-byte copy matches the frozen
hash; the Git blob has 1,827 bytes. Blind whole-file LF/CRLF conversion would
not recover it. The mismatch classification therefore uses the already
hash-verified original, not guessed normalization.

The reported HAT-P-32 notes example is confirmed: `notes.md` is 657 bytes in
Git but 668 bytes in the historical manifest and exact local original. No
manifest checksum was recomputed to accept transported bytes.

An initial native-Python probe (`raw_git_transport_before.json`) reported 23
long FITS paths as missing because that Windows build required extended-length
paths. This was an access-path bug, **not missing scientific data**. WSL found
all 445, and the corrected native audit with extended-length paths also
verified all 445. Preserve that preliminary probe as debugging history; use
the completed real-checkout inventory for conclusions.

## Repair and scientific impact

The last `.gitattributes` rule now disables text, filter, ident and encoding
conversion for `data/raw/**`. Exactly 198 Git blobs were refreshed from
existing worktree originals whose size and SHA-256 already matched the frozen
manifest. No RAW filesystem bytes, scientific input arrays, historical output,
or expected manifest fields were changed. The index verification in
`raw_index_restoration.json` checks all 445 entries, not only the reported
notes, and verifies both index bytes and original worktree bytes.

The command `git add --renormalize` was used only on these 198 explicit paths
**under the new `-text` policy** to bypass Git's unchanged-file stat cache.
Despite its name, this operation copied the original bytes into the index;
it did not normalize or rewrite any RAW payload on disk. This is a transport
repair and does not justify repeating MCMC. Preservation of the downstream
historical outputs is separately checked by the closure protection manifest.

The RAW current-state CSV itself historically has CRLF in the original
worktree and LF in Git; its parsed fields are identical and it is not a
self-checksummed current-state payload. It was not regenerated or staged as
part of this repair. Payload identity, manifest field identity and manifest
serialization identity are explicitly distinguished by the audit report.

## Reproduction and regressions

```text
python -m unittest discover -s tests -p test_raw_git_bytes.py -v
python scripts/audit_raw_git_bytes.py --real-checkouts --output NEW_AUDIT_PATH.json
```

The audit refuses to overwrite an existing evidence report. Eight focused
tests passed on native Windows (39.099 seconds in the first fully corrected
run), covering actual Git checkout behavior under both autocrlf settings,
old-policy failure, exact-byte preservation, genuine content tampering,
manifest tampering, size checks, BOM/mixed-ending classification, unsafe paths,
report collisions and paths exceeding 260 characters. A separate Linux/pinned
environment run and the complete remote CI remain separate evidence; a local
test pass is not represented as hosted-CI success.

After the repair commit, repeat the audit on its actual SHA and record the
post-repair checkout inventory. Do not claim the old baseline blobs themselves
were rewritten: history and protected branches remain unchanged.
