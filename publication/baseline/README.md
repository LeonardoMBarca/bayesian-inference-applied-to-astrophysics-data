# Protected observational baseline

`manifest.json` freezes historical Kepler-10 b `scientific_003` at base commit
`7489a90689a753bea5243f86c1489329916c98e2`. It does not rerun inference or change
historical diagnostic decisions. All referenced scientific bytes remain in their
original paths. The environment files in `environment/` are immutable copies of
the baseline lock/configuration, not a new validated environment.

Verify all locally available evidence and regenerate only publication inventory:

```sh
python scripts/publication_inventory.py
```

The command fails on changed/missing required baseline bytes or changed protected
Git refs when those refs exist locally. A clean checkout without ignored large
artifacts may use `--allow-missing-external`; this explicitly reports **partial**
verification, never complete reproducibility. In particular `trace.nc` is not
silently assumed available or recreated. Its historical SHA-256 is retained.

The initial freeze command (already executed; deliberately fails if repeated):

```sh
python scripts/publication_inventory.py --freeze-baseline --initialize-registry
```

New runs use `publication/experiments/PUB-XX/scenario/replicate/run/`. Reservation
is exclusive; there is no API argument accepting a historical output directory.
Final reservations require a byte-identical committed protocol and committed
registry declaration. Pilot attempts remain separate from final denominators.
Every declared attempt appears in the inventory, including missing, failed and
rejected cases. Config checksums distinguish canonical JSON identity from raw
file-byte checksums. Statuses and amendments are hash-linked append-only files;
terminal statuses cannot be promoted by the update API.

These mechanisms protect against accidental overwrite and stale/mismatched
artifacts. They are not a trusted timestamp service, a cryptographic signature,
or a defense against deliberate rewriting of the whole Git history.
