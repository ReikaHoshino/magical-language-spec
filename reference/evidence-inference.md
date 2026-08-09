# Evidence Inference

**Status:** experimental normative owner for evidence fusion used by `SUCCESS-ARCANA-003`.

Its canonical self-contained input is a `SpellInstanceBundle`; artifact loading and registry dispatch are owned by `spell-instance-bundles.md`, not by confidence or evidence semantics.

## Owner and non-goals

This document owns multi-Measurement evidence fusion, frozen evidence context, confidence semantics, and non-physical ObservationArtifact output. It does not own planning defaults (`planning-inference.md`), Identity resolution, authority grants, History rewind, future prediction, or a new MKI primitive.

## FrozenEvidenceContext

A `FrozenEvidenceContext` records:

```text
WorldRevision
HistoryRevision
EvidenceRevision
observation interval
permitted evidence sources
freshness / retention / redaction policy
privacy / discovery / observation Capability
query budget
deterministic ordering policy
```

Every EvidenceBundle input must be admissible under that same context. Mixing revisions silently is forbidden. A stale revision causes fail-closed re-acquisition/replanning; it is not coerced to current state.

## Historical evidence ownership

Committed History owns Events. An evidence store owns retained Measurement artifacts plus retention, freshness, privacy, and redaction policy. WorldIndex may enumerate candidate records/relations but is neither History nor authoritative WorldState.

```text
WorldIndex record != past WorldState
Relation != Truth
stored Measurement != current state
History query != MKI primitive
```

Reading an existing committed HistoricalMeasurement uses QUERY. Measuring a current physical trace requires OBSERVE and SAMPLE. Computation over acquired Measurement values is pure.

## EvidenceFusionModel

An EvidenceFusionModel records model ID/revision, accepted Measurement types, hypothesis schema, source-independence treatment, conflict policy, scoring/calibration, uncertainty output, minimum evidence policy, valid domain, deterministic tie-break, and provenance.

It is serialized as a distinct contract in the existing `observer_models` namespace. It is not an ordinary observer response conversion and is not `PlanningAssumption`.

## Confidence and authority

Confidence selects/ranks candidates inside the model's declared calibration domain. It is not a proof of world truth and cannot create a `Ref`, Entity identity, Capability, or Lease. The selected winner must be resolved/revalidated against current authoritative state and authority immediately before COMMIT.

## Artifact and physical rendering

`ObservationArtifact` is a non-physical provenance-bearing record containing the frozen context, EvidenceBundle, model revision, ranking/uncertainty, and selected hypothesis. Creating it does not by itself change WorldState.

Physical output is a separate world effect. A display requires a DisplayModel, radiative/surface actuation model, Energy source, Capability/Lease, accounting, and normal PREPARE/COMMIT guards. No generic `RENDER` primitive or `TRANSFER<Information>` is implied.

## Replay

Replay compares the same EvidenceBundle ordering, frozen revisions, model revision, profile, ranking, artifact content, and result hash in an isolated runtime. Replay is not rewind and does not reuse recorded authority in the current world.
