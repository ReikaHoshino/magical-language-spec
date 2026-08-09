# SUCCESS-ARCANA-008 — Detect Poison

## Status

Design instance for Issue #77. Not yet an executable fixture.

## Intent

Observe a bounded sample, compare the acquired evidence with an admitted poison-classification model, and return a provenance-bearing observation artifact without mutating the sample.

## Reusable semantic pattern

```text
world observation + pure evidence classification
```

## Authoritative inputs

- sample `Ref<Matter>` and current state revision;
- observation Capability and permitted property scope;
- admitted composition/spectral ObserverModel;
- poison-classification model identity, revision, valid domain, and decision thresholds;
- required measurement resolution, uncertainty policy, query/observation budget, and privacy policy.

## High-level lowering

```text
RESOLVE the bounded sample
OBSERVE composition / spectrum / relevant properties
purely convert and classify acquired Measurements
produce ObservationArtifact<Result<PoisonAssessment>>
```

The classification step is pure computation over acquired Measurement evidence. It is not a new `DETECT`, `INFER`, or `TRUTH` MKI primitive.

## Required invariants

- WorldIndex metadata is not a Measurement;
- classification confidence is not proof of exact composition or universal safety;
- `Positive`, `Negative`, and `Indeterminate` remain distinct;
- model identity/revision, evidence IDs, uncertainty, observed-at time, and source revision are preserved;
- no Capability, identity, or Truth is fabricated from a model score;
- artifact generation alone does not mutate WorldState;
- observation back-action, if the selected model has any, is explicit and accounted.

## Expected successful result

A deterministic `ObservationArtifact` reports the poison assessment and supporting evidence. The sample remains unchanged for a non-destructive observer model, while History/diagnostics preserve any explicitly modeled observation event or back-action.

## Mandatory negative neighbors

- sample cannot be resolved uniquely;
- observation Capability is missing;
- measurement resolution is insufficient;
- classifier model revision is incompatible;
- evidence falls outside the model's valid domain;
- score lies in the indeterminate interval;
- attempt to convert a `Negative` result into proof that the sample is safe for every organism and dose.

## Generality check

The same observation-and-classification contract should support allergen screening, mineral identification, spoilage detection, or magical-residue analysis without adding a `Detect Poison` branch to core code.
