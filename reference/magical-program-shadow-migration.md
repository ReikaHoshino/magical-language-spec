# MagicalProgram Shadow Migration

**Status:** experimental normative migration owner for Issue #90.

**Prerequisites:** corrected `MagicalProgram-0` artifact/evaluator/runtime contracts from Issues #110, #114, and #118.

**Stable v1.0 impact:** none. Migration evidence does not alter the released four-class / 65-case conformance surface or version `0.12.0`.

## 1. Purpose

The shadow path proves that current repository spells can be represented and executed through the same declarative MagicalProgram pipeline used by an independent authored program.

```text
frozen SpellInstanceBundle bytes
  ├─ legacy path -> frozen external oracle
  └─ contract-pair translator
       -> explicit MagicalProgram values/nodes/edges/outputs
       -> generic evaluator
       -> generic PREPARE/COMMIT runtime
       -> replay
       -> contract-owned normalized projection comparison
```

Migration is not cutover. The legacy path remains available only as an external differential oracle until Issue #91.

## 2. Selection boundary

A translator is selected only by the exact pair:

```text
(semantic_contract ID/revision, runtime_contract ID/revision-or-null)
```

Path, filename, suite ID, instance ID, display name, scenario name, and expected outcome never select translator or executor code.

The inventory in `conformance/magical-program-shadow-migration.json` is complete for every current `examples/spell-instances/**/*.json` file. Inventory metadata describes coverage; it is not executable dispatch data.

## 3. Prohibited migration shortcuts

The generic path must not:

- embed a complete legacy bundle or parameter object as base64/JSON text;
- call a legacy semantic handler or executor;
- import executable code named by the artifact;
- dispatch by fixture/suite/spell names;
- copy concrete host Capability, Lease, identity, evidence, or accounting IDs into portable obligations;
- copy current entity state revisions into portable selectors;
- let portable syntax assign a WorldRevision directly;
- treat expected outcomes as program semantics;
- compare only a self-authored expected field while ignoring the external oracle.

Complex parameters use bounded typed records and sequences from Issue #114.

## 4. Differential evidence

Both paths consume the same frozen source bytes. The translator creates its own declarative program and a cloned initial runtime world. Comparisons record raw and normalized status separately.

The only general status normalization currently admitted is:

```text
legacy Feasible + generic ConditionallyFeasible
  -> ExecutablePendingOrCompletedAuthorityBinding
```

This reflects the corrected rule that portable syntax cannot imply current authority.

Diagnostic aliases are explicit and narrow. Generic PREPARE diagnostics may be more local than the frozen legacy contract—for example, `ProgramAuthorityError`, `ProgramAccountingMissing`, or `ProgramEnergyInsufficient`—but the differential boundary maps only the registered aliases to the legacy-owned public category. Unknown or fatal diagnostics are never suppressed.

Expected truth and adversarial mutations are owned by `conformance/magical-program-golden-parity.json`. Embedded `expected_outcome` data is never an oracle for either path.

Committed cases compare:

- legacy oracle success;
- generic runtime and replay status;
- declared final invariants;
- expected History event identities;
- contract-owned normalized final projection;
- contract-specific accounting where configuration projection omits ledgers.

Aborted cases compare:

- exact normalized diagnostic identity;
- deterministic abort replay;
- unchanged world revision, History, and complete authoritative configuration;
- absence of committed artifacts/effects.

## 5. Completed foundation cases

### 5.1 Independent generic transition

`example.generic-transition@1` + `runtime.generic-transition@1` is the control case. It proves:

- explicit reference resolution;
- portable authority/accounting requirements;
- registration-owned execution;
- host-owned WorldRevision transition;
- event identity and deterministic replay;
- filename/instance/suite rename independence.

### 5.2 Recognized unsupported contracts

The following remain recognized but non-executable and preserve `Indeterminate` / `UnsupportedSemanticSubset`:

- `light.guidance@1`;
- `dynamics.levitation@1`;
- `matter.purification@1`;
- `observer.poison-detection@1`.

They have no generic runtime executor.

## 6. SA-001 boundary reflection

Contract pair:

```text
controller.boundary-reflection@1
runtime.boundary-controller@1
```

The portable program contains:

- PREPARE-resolved target and reaction-anchor selectors;
- `record:BoundaryReflectionModel` for registered model identity and safety policy;
- `record:BoundaryReflectionPolicy` for restitution, admitted domain, saturation, and timing bounds;
- `record:BoundaryReflectionPublication` for controller/region/event identities;
- one `effect.invoke` contract node whose lowering is `OBSERVE` + `CONSTRAIN`;
- portable Constrain Capability, Actuate Lease, target/anchor identity, and Momentum/Energy accounting requirements;
- effect-result and event outputs.

The portable artifact does **not** contain current state revisions, host record IDs, the input bundle, or `result_world_revision`. PREPARE resolves both entities and freezes their current state revisions. The runtime generates the successor WorldRevision through the common host-owned revision function.

The bundle's `registry_extensions.controller_models` entry is compatibility evidence, not a source of runtime safety policy. It must exactly match the host-owned `controller.boundary-reflection@1` registration. An artifact cannot widen the registered mass domain, disable per-actuation revalidation, or permit authority amplification; declaration drift fails closed before translation, and tampering with the typed program model fails atomically at COMMIT.

COMMIT validates:

- model identity/revision, per-actuation revalidation, and no-authority-amplification policy;
- target mass and incident Momentum domain;
- event latency and jitter bounds;
- impulse and dissipated-Energy saturation limits;
- exact bound Capability, Lease, identities, and accounting ledger after revalidation.

For an unauthorized crossing it atomically:

- reflects target normal Momentum using the declared restitution coefficient;
- applies equal and opposite Momentum to the reaction anchor;
- records dissipated Energy in the bound ledger;
- registers the persistent Controller semantic projection;
- advances WorldRevision once;
- appends one reflection History event whose accounting names target Momentum, anchor reaction, and dissipated Energy.

The positive projection compares WorldRevision, target/anchor Momentum, Controller state, and History event; contract accounting separately checks the ledger because ledgers are outside `C=<Σ,H,Ω,P>`. Four external-golden variants prove deterministic fail-closed parity for revoked authority, absent accounting proof, target-domain overflow, and timing violation.

## 7. SA-002 staged treatment

Contract pair:

```text
treatment.staged-repair@1
runtime.staged-treatment@1
```

The generated program contains five explicit PREPARE-resolved references:

- patient;
- treatment proxy;
- sink;
- donor;
- Energy reservoir.

It then executes an explicit acyclic stage graph:

```text
stabilize -> repair -> manifest
```

Each stage is a separate `effect.invoke` node with:

- the same five resolved references;
- `record:StagedTreatmentModel`;
- `record:StagedTreatmentPolicy`;
- one stage-specific `record:TreatmentStage`;
- portable Reconfigure and Channel Capability requirements;
- patient Write and reservoir Consume Lease requirements;
- identity requirements for every participating entity;
- one `UniqueCorrespondence` evidence requirement bound to the proxy;
- one staged-treatment accounting requirement;
- explicit stage-specific Energy, Matter, and event reservations.

The complete reservation is:

```text
stabilize   120 J   0.020 kg   1 event
repair      450 J   0.005 kg   1 event
manifest     50 J   0.000 kg   1 event
aggregate   620 J   0.025 kg   3 events
```

The fixed MKI lowering is limited to `OBSERVE`, `CHANNEL`, `TRANSFER`, and `RECONFIGURE`. The lower World Kernel classification uses only the admitted fixed classes `SAMPLE` and `TRANSITION`; an MKI operation name is never invented as a sixth World Kernel class.

### 7.1 Host ownership and evidence

The bundle's StructureSchema, reaction-rule, and conservation-ledger declarations are compatibility evidence only. They must exactly match host registrations. They cannot select code or redefine the treatment model.

`correspondence_unique` is not copied into the portable program as authority or truth. PREPARE binds a host-owned `UniqueCorrespondence` evidence record containing the proxy identity, exact state revision, token identity, and uniqueness result. Missing, stale, mismatched, or non-unique evidence fails closed.

The portable artifact does not contain current state revisions, host record IDs, the legacy bundle, or `result_world_revision`. Each stage receives immutable PREPARE-frozen values and bound records. The runtime derives each successor WorldRevision through the common host-owned revision transition.

### 7.2 Atomic staged execution

All three effects belong to one PreparedProgramPlan and one atomic COMMIT boundary. The runtime revalidates every entity and bound record before the first stage. If any stage fails, the runtime restores all prior stage mutations, History events, ledger allocations, runtime state, process state, and WorldRevision.

The stages have distinct responsibilities:

1. `stabilize` transfers excess thermal Energy and removable fluid to the bounded sink;
2. `repair` consumes bounded donor Matter and external Energy to repair structural deviation;
3. `manifest` consumes the remaining external Energy, finalizes the repaired chemical state, and publishes the non-reversing proxy descriptor.

The committed authoritative projection preserves the patient's existing identity, produces the same patient/proxy/sink/donor/reservoir records as the frozen legacy oracle, advances WorldRevision three times, and emits exactly:

```text
TreatmentStabilize
TreatmentRepair
TreatmentManifest
```

Treatment-specific accounting records the sink transfer and external treatment Energy. Generic runtime accounting independently records all three per-node allocations and the remaining Energy, Matter, and event capacity. These layers are compared separately rather than conflated.

Six external-golden variants prove deterministic atomic abort parity for:

- ambiguous correspondence;
- missing medical authority;
- insufficient sink capacity;
- insufficient donor Matter;
- identity-critical information loss;
- attempted reverse proxy effect.

Additional tests prove host-registration drift, stage-order tampering, missing Capability/Lease/accounting records, filename/suite/instance renaming, and replay behavior.

## 8. SA-003 evidence fusion

Contract pair:

```text
evidence.snapshot-fusion@1
runtime.evidence-artifact@1
```

The generated program contains:

- PREPARE-resolved subject reference;
- `record:EvidenceFusionModel`;
- `sequence:record:HypothesisScore`;
- `record:EvidenceFusionPolicy`;
- `record:CurrentMeasurement`;
- `record:ArtifactPublication`;
- one `evidence.observe` contract node;
- portable Discover, Observe, PrivacyAccess, ReadSnapshot, identity, snapshot-evidence, and accounting requirements;
- evidence, artifact, and event outputs.

PREPARE binds exact host records for:

- three capabilities associated with the subject;
- one snapshot lease;
- subject identity and state revision;
- History and Evidence snapshot records;
- observation accounting ledger.

COMMIT validates:

- identity conflict policy;
- frozen History/Evidence revisions;
- fusion model ID/revision and non-truth confidence policy;
- winner confidence threshold;
- optional physical-display Energy availability;
- minimum evidence count;
- deterministic evidence and ranking order.

It publishes a nonphysical observation artifact, records observation Energy consumption, appends one History event, and leaves WorldRevision and physical world state unchanged.

The positive differential projection compares WorldRevision, artifact, ranking, evidence bundle, winner, confidence/physical flags, and publication event. Six repository variants prove deterministic abort parity for stale evidence, identity conflict, privacy authority failure, threshold failure, model mismatch, and display-Energy insufficiency.

## 9. SA-004 bounded explosion

Contract pair:

```text
dynamics.explosion@1
runtime.explosion@1
```

The portable program resolves only:

- explosion origin;
- reaction anchor.

It carries typed host-validated model, policy, and publication records, plus portable Capability, Lease, origin/anchor identity, affected-set evidence, and accounting requirements. It reserves the complete 5000 J release and two History events in one effect node. Its admitted lowering uses the existing six MKI operations and only the fixed World Kernel classes `SAMPLE`, `TRANSITION`, and `ACTIVATE`.

### 9.1 Prepare-bound affected set

Affected entity IDs are not copied into portable syntax. The host constructs an `ExplosionAffectedSet` evidence record associated with the resolved origin. That record freezes:

- source WorldRevision;
- medium revision;
- deterministic radial ordering;
- every affected entity ID;
- every exact entity state revision;
- observed distance from the origin.

The generic contract therefore cannot widen its own target set after PREPARE. COMMIT rejects a stale WorldRevision, changed medium, absent or revised target, target that left the region, non-blast subject, target outside the radius, changed ordering, or increasing radial pressure.

The bundle's `explosion_models` declaration is compatibility evidence only and must exactly match the host-owned synthetic-air model. Artifact data cannot widen valid radius, substitute attenuation/occlusion policy, or select code.

### 9.2 Bounded atomic effect

COMMIT validates:

- model identity/revision and authoritative medium revision;
- positive radius within both policy and host model domains;
- peak-pressure bound;
- nonnegative duration, impulse, and Energy limits;
- pressure/thermal fractions that exactly partition released Energy;
- maximum thermal allocation;
- prepare-bound target-count ceiling;
- monotonic linear radial attenuation.

The executor then atomically:

- records pressure, radial impulse, thermal allocation, and duration on each prepare-bound target;
- applies equal and opposite aggregate reaction impulse to the anchor;
- records released, pressure, thermal, and reaction accounting;
- consumes the reserved Energy through generic runtime accounting;
- advances WorldRevision once;
- appends exactly `BoundedExplosionActivated` and `BoundedExplosionTerminated` events.

The positive differential projection compares origin, anchor, both affected targets, both History events, and WorldRevision. Contract accounting separately verifies the remaining Energy, release partition, reaction impulse, two-event reservation, and generic allocation.

Nine external-golden variants prove deterministic atomic abort parity for insufficient Energy, radius overflow, target-count overflow, stale WorldRevision, revoked Capability, expired Lease, absent accounting sink, pressure overflow, and thermal overflow. Additional tests prove host-model drift, affected-set revision tampering, missing host records, rename independence, and replay behavior.

## 10. Implementation ownership

- `src/migration/magical_program_shadow.py`: stable contract-pair registry and external differential core;
- `src/migration/magical_program_shadow_suite.py`: compositional current migration suite and contract-owned projections;
- `src/migration/magical_program_shadow_support.py`: shared data/world construction;
- `src/migration/magical_program_shadow_generic.py`: independent control contract;
- `src/migration/magical_program_shadow_boundary.py`: reusable SA-001 boundary Controller contract;
- `src/migration/magical_program_shadow_treatment.py`: explicit SA-002 staged-treatment contract;
- `src/migration/magical_program_shadow_success_arcana.py`: typed SA-003 evidence-fusion contract;
- `src/migration/magical_program_shadow_explosion.py`: prepare-bound SA-004 explosion contract;
- `src/migration/magical_program_shadow_unsupported.py`: recognized-unsupported classification.

Legacy execution is imported only by the differential orchestrator. Contract modules must not import `src.extensions` or `default_service`.

## 11. Remaining Issue #90 work

```text
DEBUG-HELL-001..003 adversarial semantics
full 12-case differential matrix and package smoke
```

Issue #91 may retire dedicated executors only after every implemented and adversarial case has exact accepted parity evidence.

## 12. Traceability

- inventory and foundation: `tests/test_magical_program_shadow_foundation.py`;
- SA-001 positive and four variants: `tests/test_magical_program_shadow_sa001.py`;
- SA-001 host-model ownership: `tests/test_magical_program_shadow_sa001_model_ownership.py`;
- SA-002 positive and six variants: `tests/test_magical_program_shadow_sa002.py`;
- SA-003 positive and six variants: `tests/test_magical_program_shadow_sa003.py`;
- SA-004 positive and nine variants: `tests/test_magical_program_shadow_sa004.py`;
- diagnostic phase normalization: `tests/test_magical_program_shadow_diagnostic_phases.py`;
- migration inventory schema: `schemas/magical-program-shadow-migration.schema.json`;
- machine inventory: `conformance/magical-program-shadow-migration.json`.
