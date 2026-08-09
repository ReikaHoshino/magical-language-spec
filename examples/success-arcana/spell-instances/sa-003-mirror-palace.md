# SUCCESS-ARCANA-003 — Mirror Palace of Mnemosyne

## Status

Design instance for Issue #77. Not yet an executable fixture.

## Intent

Collect bounded current and historical evidence under one frozen context, rank candidate histories through a pure evidence-fusion model, revalidate the winning identity, and produce a provenance-bearing observation artifact.

## Reusable semantic pattern

```text
snapshot-consistent evidence acquisition + pure fusion
```

The seven mirrors are a narrative presentation. They do not require seven MKI primitives, seven threads, or a spell-specific inference engine.

## Authoritative inputs

- search subject selectors and identity constraints;
- `FrozenEvidenceContext` with WorldRevision, history/evidence revision, interval, permitted sources, freshness, and deterministic ordering;
- discovery, privacy, and observation Capability evidence;
- admitted observer models and `EvidenceFusionModel` identity/revision;
- query/observation budget;
- hypothesis schema, uncertainty policy, minimum evidence rule, and deterministic tie-break;
- optional physical display model and Energy budget.

## High-level lowering

```text
QUERY committed HistoricalMeasurement evidence
RESOLVE and OBSERVE current traces where authorized
SAMPLE under admitted observation models
purely build EvidenceBundle and rank hypotheses
RESOLVE / QUERY current authoritative winner identity and revision
produce ObservationArtifact
optionally lower physical mirror display as a separate admitted world effect
```

Stored evidence queries, new physical observations, pure inference, artifact creation, and physical rendering remain distinct stages.

## Required invariants

- WorldIndex metadata is not historical WorldState or a Measurement;
- all fusion inputs are bound to the declared frozen evidence context;
- confidence is a score, not Identity, Capability, Lease, or Truth proof;
- conflicting or insufficient evidence may remain `Indeterminate`;
- the selected candidate is authoritatively revalidated before any dependent commit;
- artifact creation alone does not mutate physical WorldState;
- optional display consumes accounted resources and grants no reverse observation/control channel;
- no future prediction, rewind, or history mutation is implied.

## Expected successful result

The system produces a deterministic ranked hypothesis set and an `ObservationArtifact` containing evidence IDs, model revision, uncertainty, and revalidation outcome. Under the same context/profile, replay reproduces the same ranking and artifact.

## Mandatory negative neighbors

- stale or mismatched evidence revisions;
- unresolved identity conflict;
- missing privacy/discovery/observation authority;
- evidence outside observer/fusion model domains;
- confidence below the acceptance threshold;
- non-deterministic tie without an admitted tie-break;
- insufficient Energy or authority for optional physical display.

## Generality check

The same evidence-fusion contract should support lost-object search, forensic reconstruction, source attribution, or multi-sensor tracking without adding a `Mirror Palace` branch to evaluator/runtime core.
