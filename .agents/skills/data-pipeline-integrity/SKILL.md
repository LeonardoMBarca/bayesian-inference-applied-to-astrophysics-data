---
name: data-pipeline-integrity
description: Fix or review RAW, Silver, Gold, MAST/NASA/ETD ingestion, provenance, units, segment/quarter handling, normalization/detrending, cadence selection, manifests, target selection, and clean-run data isolation in this repository. Use when data preparation can affect scientific inference. Do not use for purely statistical model changes that leave data semantics untouched.
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
- Test any unit conversion used for scientific parameters.

### Gold

- Preserve segment identity until segment-level normalization/detrending is complete.
- Do not treat offsets between different products/quarters as one stationary astrophysical process.
- Record preprocessing transformations and parameters in machine-readable metadata.
- Phase folding must be testable and use the intended target ephemeris.

## Kepler-10 b workflow

When working on Kepler-10 b:

1. Trace every modeling row back to source FITS/product and quarter/segment.
2. Inspect per-segment baseline, scatter, cadence, quality filtering, and time coverage.
3. Normalize/detrend per segment using a documented method that does not fit away the transit.
4. Keep pre- and post-correction diagnostics.
5. Concatenate/fold only after segment-level treatment.
6. Propagate cadence/exposure metadata to the physical-model input.
7. Refuse scientific interpretation if provenance/segment handling is incomplete.

Do not choose a detrending method solely because it moves `Rp/Rs` closer to a catalog value. Choose it from data/model assumptions and validate with injection/recovery or out-of-transit behavior when practical.

## MAST product selection

- Audit ranking functions before assuming selected products are scientifically preferred.
- Make cadence preference explicit rather than an accidental consequence of sorting.
- Prefer short cadence for short transits when available and justified.
- If long cadence remains, expose integration time so the forward model can integrate over it.
- Add regression fixtures for product-ranking behavior.

## Unit audit

For every field used in modeling or validation:

1. identify source unit;
2. identify internal canonical unit;
3. implement explicit conversion if needed;
4. encode unit in name/metadata;
5. test representative values, especially percent vs fraction and hours vs days.

## Manifest and run isolation

- Persist repository-relative paths using POSIX separators.
- Do not let historical outputs make a currently unsupported target appear available.
- Separate current-state manifest semantics from append-only event-log semantics when necessary.
- Prefer explicit dataset/run identifiers for regenerated Silver/Gold artifacts.

## Verification checklist

Before completing a data-pipeline change, verify:

- checksums/provenance still resolve;
- row counts are explainable;
- target identity is correct;
- units are explicit;
- segment metadata survives as long as needed;
- phase and period are target-correct;
- normalization/detrending is deterministic from recorded inputs/config;
- a clean workspace reproduces the expected target availability;
- downstream modeling inputs have the metadata required by the scientific model.
