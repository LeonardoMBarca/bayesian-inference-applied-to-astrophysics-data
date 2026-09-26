# P0 acceptance evidence

Validation performed on `publication-grade-validation`, 2026-09-26. No baseline
scientific computation was rerun, and no historical output was edited.

The initial freeze and complete local verification checked **26 artifacts**:
the canonical Gold metadata/input, its three source FITS, all `scientific_003`
model/table/figure/report/trace files, and three preserved environment files.
The manifest content SHA-256 is
`2c251e37c175dd9d75be97c593b0241f8871f15059196872de2352e9d5d76f2d`.
Tracked scientific artifacts were also compared byte-for-byte against Git
objects at base commit `7489a90689a753bea5243f86c1489329916c98e2`.

Executed commands (scientific environment: WSL Ubuntu-24.04 / Python 3.14.6):

```sh
python -m unittest tests.test_publication_contracts -v
python -m ruff check src/publication/contracts.py src/publication/__init__.py scripts/publication_inventory.py tests/test_publication_contracts.py
```

Result: **12 tests passed**, no skips, and Ruff passed. The earlier 11-test
revision also passed on Windows; the final 12-test revision passed on WSL.
Tests cover deterministic stream seeds, identifiers/path traversal, exclusive
reservation, immutable failed statuses, committed protocols/registry, dirty
scientific-source rejection, Windows-style checkout byte identity, missing and
failed denominators, status/config tampering, append-only amendments, duplicate
attempt rejection, terminal output checksums and baseline byte mutation.

The initially generated inventory contains zero final attempts, correctly marks
the declared-batch terminal predicate false, and makes no calibration or other
scientific success claim. Later inventory generations are derived state and must
reflect all subsequently declared attempts.

Limitations: the checks detect accidental mutation, not deliberate coordinated
rewriting of manifests and Git history. The ignored large trace must be restored
or reproducibly regenerated for complete verification on a clean machine.
