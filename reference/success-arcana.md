# Experimental Success Arcana

**Status:** experimental normative owner for `Experimental-Arcana-0`; not part of the v1.0 required conformance guarantee.

## Purpose and ownership

This document owns the portable semantic boundaries exercised by `SUCCESS-ARCANA-001` through `008`. The original split design evidence remains in `examples/success-arcana/`; canonical self-contained execution input is `examples/spell-instances/success-arcana/`, governed by `spell-instance-bundles.md` and the separate `conformance/experimental-arcana.json` manifest.

The suite does not change the four required class counts. Stable promotion requires a later release decision, migration/compatibility impact analysis, and the normal release gate.

## Immutable ABI boundary

The public MKI data plane remains exactly:

```text
RESOLVE / OBSERVE / CHANNEL / TRANSFER / RECONFIGURE / CONSTRAIN
```

The lower World Kernel interaction classes remain exactly:

```text
QUERY / SAMPLE / TRANSITION / ACTIVATE / DEACTIVATE
```

No scheduler, integrator, resolver query, inference, renderer, `SET`, `CREATE`, `HEAL`, `INFER`, or `RENDER` operation is an MKI primitive. The lower interaction records in these fixtures are implementation/conformance evidence and do not freeze a public serialized ECIR.

## Dynamic Capability target scope

A bounded dynamic `Capability<Target,Domain,Operation>` scope may select future targets through a Region and predicate only when its admitted contract records:

- anchor and Region identity;
- target predicate;
- maximum target and event scope;
- effect class;
- validity interval;
- per-actuation Capability and Lease revalidation;
- `no_authority_amplification = true`.

Region membership, relation, crossing predicate, visibility, or index metadata are selection evidence only. They do not grant mutation authority. Every actuation resolves a current target and revalidates current authority within the maximum scope.

## SUCCESS-ARCANA-001

`BoundaryReflectionController` is a revisioned `controller_models` Registry contract. It owns observation input, contact/error model, permitted effects, valid mass/momentum domain, Momentum/Energy accounting, sample/latency/jitter bounds, saturation/overload, termination, provenance, and per-actuation authority requirements.

An unauthorized admitted crossing applies a bounded impulse along the boundary normal. It does not teleport the entity. One atomic actuation accounts:

- target Momentum transition;
- equal/opposite Anchor/world reaction;
- dissipated Energy;
- committed reflection Event.

An authorized target is unaffected. A target outside the model domain, insufficient reaction/accounting capacity, stale/revoked authority, or timing violation produces explicit overload/failure; it never requests unbounded force. The active Controller remains owned by authoritative World Kernel state with a portable semantic projection sufficient for replay.

## SUCCESS-ARCANA-002

`TreatmentDecomposition` separates:

- excess thermal Energy;
- removable fluid / MatterPayload;
- chemical state deviation;
- reversible structural deviation;
- irreversible information loss;
- uncertainty and measurement evidence.

The admitted stages are:

1. Stabilize — TRANSFER actual Energy/Matter to an admitted sink/proxy.
2. Repair — use donor matter and an admitted tissue/structural rule under `IdentityPolicy<Organism>`.
3. Manifest — RECONFIGURE the proxy from a provenance-bearing `DamageDescriptor`.

Damage is not a conserved TransferKind. Structure/shape descriptors are not transferred as Matter. Hair/red thread is a `CorrespondenceToken` or resolver evidence, never organism identity. Correspondence is one-way planning/selection evidence; proxy destruction has no reverse patient effect.

Each stage has its own conceptual checkpoint/commit boundary. A later failure does not reclassify already committed history as rollback. The initial reference fixture prevalidates all three stages before its first mutation and preserves pre-existing committed treatment Events on failure. Fixture Energy/resources come from its synthetic profile and are not universal constants.

## SUCCESS-ARCANA-003

`FrozenEvidenceContext` binds WorldRevision, History/evidence revisions, observation interval, permitted sources, freshness, privacy/discovery/observation authority, query budget, and deterministic ordering. Parallel execution is optional; semantics are one deterministic EvidenceBundle over one snapshot context.

Historical committed Measurement read lowers to QUERY. New physical trace acquisition uses OBSERVE then SAMPLE. Hypothesis construction/ranking is pure computation and not an MKI primitive. `EvidenceFusionModel` is registry-owned inside `observer_models` but distinct from an ordinary sensor conversion model and from `PlanningAssumption`.

Confidence is a candidate-selection score. It cannot prove Identity, Capability, Lease, or Truth. The winner is revalidated against current authoritative identity/state/observation authority before COMMIT.

The default output is a provenance-bearing non-physical `ObservationArtifact`. Artifact publication may update artifact/history bookkeeping but must not report a WorldState mutation. A physical mirror display is a separate optional effect requiring DisplayModel, radiative Energy, surface/light actuation, Capability, and accounting. This suite introduces no `TRANSFER<Information>`, future prediction, or rewind.

## SUCCESS-ARCANA-004

`SUCCESS-ARCANA-004` admits `dynamics.explosion@1` only with `runtime.explosion@1`. `ExplosionContract@1` owns the origin and bounded Region, medium model/revision, finite radius and duration, released Energy, pressure/impulse and thermal envelopes, maximum affected-entity count, attenuation and explicit no-occlusion fixture policy, reaction anchor/accounting sink, Capability/Lease scope, observation revision, result Events, and termination.

The evaluator freezes the affected set by `(distance_from_origin_m, EntityID)` under `PrepareBound` semantics. This selection grants no authority. COMMIT revalidates the current world revision, medium revision, Capability, Lease, and ledger, then applies non-increasing radial attenuation. It atomically debits finite Energy, separates pressure and thermal allocation, records equal-and-opposite reaction impulse, changes only admitted in-Region targets, and publishes activation and termination Events. A later entity is not silently retargeted into the prepared set. Any domain, count, pressure, thermal, authority, Lease, revision, or accounting failure aborts without partial WorldState/History mutation.

This is an experimental optional contract selected by versioned semantic/runtime identity. It is not a generic transition alias, a spell-name branch, a seventh MKI primitive, or a change to stable conformance counts.

## Experimental extension library

`SUCCESS-ARCANA-005` through `008` preserve guidance-light, levitation, purification, and poison-observation designs as `recognized-unsupported` bundles. Their NSR and contract identities are inspectable, but the reference evaluator returns `Indeterminate / UnsupportedSemanticSubset` until each model has an admitted semantic/runtime contract. Recognition is not execution and is not a no-op success.

## Fail-closed implementation dispatch

The reference implementation maps versioned semantic/runtime contract identities through the generic registries defined by `spell-instance-bundles.md`. Suite names, spell names, filenames, fixture paths, and instance IDs do not dispatch behavior. Unknown versions/contracts fail as explicit unknown-contract diagnostics; recognized but unsupported semantics return `UnsupportedSemanticSubset`. Extensions are not ignored or coerced.

The handler/executor interface and `implementation_lowering_evidence` are internal. Direct public entry into SemanticAST/TypedMIR/KernelPlan/PreparedPlan remains deferred to pre-public archive Issue #48. WB-CANON-001 continues through its existing handler with exact behavior.

## Conformance scope

`Experimental-Arcana-0` requires, per case:

- schema-valid input/contracts;
- deterministic elaboration and plan choice;
- independent type, identity, authority, Lease, accounting, timing checks;
- reversible PREPARE and current COMMIT revalidation;
- guarded World Kernel lowering evidence;
- deterministic final WorldState/History invariants and replay;
- all mandatory negative neighbors aborting without a partial initial commit.

It is deliberately separate from `conformance/manifest.json`, `conformance/rule-coverage.json`, and `conformance/v1-required-surface.json`.

## Non-goals

- production medical/controller/evidence-store implementation;
- stable public ECIR;
- stable general information TransferKind;
- stable promotion of these models;
- renderer breadth or distributed runtime;
- changing historical `spec/` snapshots.
