---
name: multi-target-generalization
description: Select and validate multiple exoplanet targets under a predeclared regime-based protocol without cherry-picking successful systems.
---

# Multi-Target Generalization

Use this skill for P5.

## Scientific objective

Characterize where the workflow succeeds, becomes weakly identified, or fails across deliberately different observational regimes.

## Target selection before outcomes

HAT-P-7 b and Kepler-10 b are fixed anchor targets. Additional targets must be chosen using a committed protocol based on scientific/data characteristics, not posterior quality.

Candidate selection dimensions include:

- transit depth/SNR;
- planet-size regime;
- cadence/exposure sensitivity;
- stellar photometric variability/noise;
- grazing/impact-parameter geometry;
- number of usable segments/transits;
- mission/product availability.

Use current authoritative catalog/data-source information when selecting final targets. Record the source/date used.

## Minimum scope

Normally attempt at least five distinct real systems total, including the two anchors, spanning multiple regimes. More targets are useful only when they add a scientifically distinct regime rather than volume for its own sake.

## No cherry-picking

After final target selection is committed:

- failed systems remain in the final table;
- do not replace difficult systems with easier ones silently;
- protocol amendments must record the original target and reason;
- a target failing due to data availability, preprocessing, sampler behavior or model inadequacy is still a result.

## Shared pipeline requirement

Do not create planet-specific model copies. Extend authoritative target configuration and shared pipeline/model interfaces. Target-specific special cases require explicit scientific justification and tests.

## Cross-target outputs

For every attempted target report:

- data source/product/cadence;
- dataset/input identity;
- usable point/segment count;
- transit-scale summary;
- sampler/PPC/scientific gate status;
- `Rp/Rs`, depth, duration and key geometric uncertainty when interpretable;
- residual structure;
- scale comparison with literature/catalog and independence caveats;
- failure reason when not interpretable;
- computational cost where useful.

## Generalization claims

Do not infer population-level astrophysics from a small regime-based validation set. The goal is method-scope characterization.

Prefer statements such as:

- `The workflow remained interpretable across X of Y preselected regimes`;
- `Failures concentrated in ...`;
- `Exposure integration materially affected ...`.

Avoid `works for exoplanets in general` unless a much broader validation supports it.

## Testing

Protect:

- target/config isolation;
- no cross-target paths;
- units/cadence policy;
- selection-registry completeness;
- final summary including failed targets.

## Done

P5 is complete when the precommitted target set has been attempted, every outcome is accounted for, and generalization language is restricted to the regimes actually tested.