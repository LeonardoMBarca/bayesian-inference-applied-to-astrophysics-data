---
name: publication-grade-research
description: Orchestrate the publication-grade validation program: protocols, dependencies, experiment registry, anti-cherry-picking rules, evidence promotion, TCC integration, and paper readiness.
---

# Publication-Grade Research Orchestrator

Use this skill whenever work spans more than one publication experiment family.

## Mandatory context

Read in this order:

1. `AGENTS.md`
2. `.agents/PUBLICATION_PLAN.md`
3. `.agents/EXPERIMENT_REGISTRY.md`
4. `.agents/PAPER_BLUEPRINT.md`
5. relevant focused skill(s)
6. current executable code/config/artifacts

The validated `main` baseline at commit `7489a90689a753bea5243f86c1489329916c98e2` is protected scientific evidence. Do not rewrite it in place.

## Operating principle

Optimize for stronger evidence, not more code.

Prefer, in order:

1. known-truth calibration;
2. independent external validation;
3. controlled ablations/failure cases;
4. real-target generalization;
5. additional model complexity;
6. publication/release polish.

Do not jump to GP/M6 merely because it is interesting while calibration and independent benchmarking remain incomplete.

## Protocol-before-result rule

Before a final experiment batch:

- create a protocol with hypothesis/question;
- freeze scenario/target selection;
- freeze primary metrics;
- freeze inclusion/exclusion handling;
- freeze sampler/prior/model assumptions;
- freeze diagnostic/interpretation rules;
- commit the protocol;
- register the experiment as `PLANNED`.

Pilot runs must be labeled `PILOT` and may not silently become final evidence.

## Dependency discipline

Default order:

`P0 baseline -> P1 novelty/protocols -> P2 injection-recovery -> P3 external benchmark -> P4 ablations -> P5 multi-target -> P6 M6 correlated noise -> P7 release -> P8 TCC/paper`

Parallelize engineering only when it cannot leak final outcomes into protocol choices.

## Evidence promotion

A positive scientific claim requires:

- valid protocol timing;
- valid dataset/provenance identity;
- completed declared batch;
- applicable gates passed;
- aggregate reports include failures/missing runs according to protocol;
- result reproduced from machine-readable artifacts;
- documentation synchronized.

Negative controls and failed runs may support negative/failure claims without passing the same positive interpretation gate, but they must be correctly classified.

## No cherry-picking

Never:

- drop a target because it fails;
- choose the external benchmark because it agrees best;
- narrow priors after seeing disagreement;
- alter gate thresholds after seeing final outcomes without a protocol amendment;
- report only successful simulation replicates;
- select the best seed/run from repeated attempts as representative evidence.

## Completion of a phase

Mark a phase complete only after:

1. focused tests pass;
2. final experiment artifacts exist;
3. aggregate report is generated from all declared runs;
4. protocol/registry status is updated;
5. failure cases are preserved;
6. documentation states limitations;
7. publication-critical outputs have traceable source hashes.

## Final standard

The repository should be able to answer a reviewer asking:

- What did you decide before seeing results?
- What is the ground truth in controlled experiments?
- What independent implementation corroborates or challenges the inference?
- Which design choices matter quantitatively?
- Where does the method fail?
- Can I reproduce every paper table/figure from frozen evidence?

If those questions do not yet have machine-readable answers, the publication program is not done.