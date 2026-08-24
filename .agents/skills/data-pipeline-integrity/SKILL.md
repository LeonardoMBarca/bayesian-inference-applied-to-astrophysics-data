---
name: data-pipeline-integrity
description: Fix or review RAW, Silver, Gold, MAST/NASA/ETD ingestion, provenance, units, segment/quarter handling, normalization/detrending, cadence selection, manifests, target selection, and clean-run data isolation in this repository.
---

# Data Pipeline Integrity

Treat the data pipeline as part of the scientific model. A posterior cannot be more trustworthy than the transformations that produced its input.

## Core invariants

### RAW
- Preserve source content immutably.
- Keep source, retrieval context, checksum, path, and status auditable.
- Do not silently convert, clean, or normalize RAW artifacts.

### Silver
- Standardize schema/types while preserving row/file provenance.
- Make units explicit.
- Preserve mission/product/quarter/sector/campaign/cadence/source identities needed downstream.
- Test every unit conversion used scientifically.

### Gold
- Preserve segment identity until segment-level normalization/detrending is complete.
- Do not treat offsets between different products/quarters as one stationary astrophysical process.
- Record preprocessing transformations and parameters in machine-readable metadata.
- Phase folding must use the intended target ephemeris and be covered by tests.

## Kepler-10 b workflow

1. Trace modeling rows to source FITS/product and quarter/segment.
2. Inspect baseline, scatter, cadence, quality filtering, and coverage per segment.
3. Normalize/detrend per segment using a documented method that does not fit away the transit.
4. Keep before/after diagnostics.
5. Concatenate/fold only after segment treatment.
6. Propagate cadence/exposure metadata to the physical model.
7. Refuse scientific interpretation while provenance/segment handling is incomplete.

Do not choose preprocessing merely because it moves `Rp/Rs` toward a catalog value. Choose from assumptions and validate with injection/recovery or out-of-transit behavior when practical.

## MAST product selection

- Audit ranking logic explicitly.
- Make cadence preference intentional, not an accidental sort consequence.
- Prefer short cadence for short transits when available and justified.
- If long cadence remains, expose integration time to the model and integrate/supersample predictions as required.
- Add regression fixtures for ranking behavior.

## Unit audit

For every field used in modeling/validation:
1. identify source unit;
2. choose internal canonical unit;
3. convert explicitly if needed;
4. encode unit in name/metadata;
5. test representative values, especially percent vs fraction and hours vs days.

## Manifest and run isolation

- Persist repo-relative paths with POSIX separators.
- Do not let historical files make an unsupported target appear available.
- Separate current-state manifest semantics from append-only event-log semantics when useful.
- Prefer explicit dataset/run identity for regenerated Silver/Gold artifacts.

## Verification checklist

Before completion verify checksums/provenance, row counts, target identity, units, segment metadata, phase/period, deterministic preprocessing, clean-workspace reproducibility, and that modeling inputs carry every piece of metadata required by the scientific model.
