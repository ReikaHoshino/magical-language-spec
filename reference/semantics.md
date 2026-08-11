# Operational Semantics — v0.7

**Status:** normative semantic skeleton. Domain-specific equations live in dedicated references.

## Purpose

MIR/MKIのsmall-step semantics、PREPARE/COMMIT、World Index resolution、async transfer、reaction kinetics、runtime tick、Event/History、replayの共通骨格を定義する。

lower World Kernel execution interaction、semantic active-effect ownership、atomic groupの詳細は
[`kernel-execution.md`](kernel-execution.md)が所有する。
Committed-history mutation authority、Restore/Rewind、historical/future observationの詳細は
[`temporal-causality.md`](temporal-causality.md)が所有する。

## Non-goals

- 完全な形式証明は行わない。
- 個別化学model/database engine/solver algorithmを固定しない。
- source-languageへTickIDを公開しない。

## Depends on

- `conventions.md`
- `architecture.md`
- `world-index.md`
- `runtime-time.md`
- `temporal-causality.md`
- `mki.md`
- `kernel-execution.md`
- `kinetics.md`

## Key invariants

```text
PREPARE != COMMIT
WorldIndex != WorldState
CandidateSet != Ref set
Physical time != runtime tick
Tick execution order != causal order
Event effective time != runtime commit time in general
Event commit time != continuation resume time
Replay != Rewind
runtime bookkeeping != semantic active-effect ownership
control-plane COMMIT != all future consequences already occurred
```

## 1. Runtime configuration

```text
C = <Σ,H,Ω,P>
```

- `Σ`: authoritative current World State。
- `H`: committed Events + causal relation `≺`。
- `Ω`: runtime state。
- `P`: evaluating MIR term/process set。

`Ω` may include implementation/runtime realization data such as:

```text
SpellInstances
Leases / Borrows
Channel / Transit runtime handles
TransferHandles
Controller runtime handles
EventQueues / ScheduledTasks
PreparedPlans
Kinetic/Dynamics solver handles
RuntimeEpoch / scheduler state
WorldIndex snapshot handles
Replay recorder
```

ただし、Transit / active Channel / Controller / Kinetic/DynamicsProcess等がfuture authoritative world evolutionを
causally determineする場合、そのportable semantic projectionは`Σ`のauthoritative semanticsとして扱うMUST。
`Ω`はそのhandle、queue、cache、solver bookkeepingを保持できるが、causally relevant semanticsの唯一の
unspecified ownerになってはならない。詳細ownershipは`kernel-execution.md`を参照する。

## 2. Small-step relation

```text
<Σ,H,Ω,P> -> <Σ',H',Ω',P'>
```

pure evaluation requires:

```text
Σ' = Σ
H' = H
```

runtime bookkeeping may change `Ω` without changing world semantics.

## 3. Pure evaluation

```text
Γ;Δ ⊢ e ⇓ v
```

Pure examples:

- arithmetic / dimensional computation。
- acquired Measurement processing。
- KineticModel/EquilibriumModel evaluation over frozen context。
- ObserverModel conversion over acquired spectral data。

World effects are not pure:

```text
RESOLVE
OBSERVE
CHANNEL
TRANSFER
RECONFIGURE
CONSTRAIN
ACQUIRE
```

## 4. Resolver semantics

```text
Selector<T>
→ ResolverQuery<T>
→ WorldIndexSnapshot
→ CandidateSet<T>
→ visibility / uniqueness / type
→ authoritative revalidation
→ Ref<T>
```

```text
WorldIndex != WorldState
CandidateSet != Ref set
```

Single:

```text
RESOLVE<T>(selector,context) -> Ref<T>
```

Collection:

```text
select<T>(selector,limit=N,order=O) -> Selection<T>
```

Selection is immutable and records `WorldIndexRevision`.

## 5. OBSERVE

```text
OBSERVE(ref,property,resolution) -> Measurement<Q>
```

Measurement is a snapshot.

Specialized outputs:

```text
Measurement<CompositionEstimate>
SpectralMeasurement<Q,Axis>
```

```text
Index metadata != Measurement
CompositionEstimate != Composition
```

Observation back-actionを持つmodelでは、そのmutationをpure readとして隠してはならず、
`kernel-execution.md`のSAMPLE + ordinary world-effect/atomic-group boundaryでaccountする。

## 6. PREPARE

PREPARE MUST NOT begin irreversible physical world change.

Allowed work includes:

- Selector/Selection resolution。
- WorldIndex schema/consistency checks。
- authoritative EntityID/type/revision revalidation。
- type/dimension/effect/authority validation。
- registry compatibility checks。
- payload/accounting validation。
- Reaction/Kinetic/Pathway/Catalyst/Equilibrium resolution。
- rate/duration/equilibrium/Energy estimates。
- Lease/resource/Channel reservation。
- proof obligations。
- scheduler/timing/integrator feasibility checks。

If a mandatory safety obligation cannot be established, PREPARE fails closed.

## 7. Prepared plan

```text
PreparedPlan {
    target_refs
    world_index_revision?
    source_world_revision?
    registry_contract
    required_capabilities
    required_leases
    required_channels
    accounting_obligations
    predicted_resources
    predicted_duration?
    temporal_requirements?
    scheduler_assumptions?
    integrator_requirements?
    uncertainty
    assumptions
    inference_records?
    planning_assumptions?
    revalidation_requirements
}
```

Reaction-specific extension may include rule/pathway/kinetic/equilibrium/catalyst metadata.

Feasibility:

```text
Feasible
ConditionallyFeasible
Infeasible
Indeterminate
```

Unknown values MUST remain ranged/bounded/unknown rather than fabricated.

planningでUnknownから採用値を選ぶ場合も、source/NSR Unknownは不変とし、
`planning-inference.md`の`InferenceRecord`とbindingされた`PlanningAssumption`を別に保持する。
`MustResolve` obligationは推定だけで満たせない。

## 8. COMMIT

```text
PREPARE -> COMMIT -> EXECUTE
```

Control-plane COMMIT permits irreversible physical execution and commits the admitted **initial semantic atomic group**.
Immediately before that commit, declared guards MUST be revalidated:

```text
EntityID validity
state / WorldRevision
Capability
Lease
registry/profile compatibility
```

The initial group may contain discrete TRANSITIONs and/or ACTIVATE/DEACTIVATE lifecycle changes. Mandatory guard failure means no member of the group becomes authoritative.

Control-plane COMMIT does not imply that every future consequence of an ACTIVATEd Transit, Controller, Channel, or DynamicsProcess has already occurred. Later due discrete effects pass current Revalidate + scheduler Commit boundaries. General rollback after already committed physical Events remains not guaranteed.

## 9. Runtime epoch / tick

```text
RuntimeEpochID
RuntimeTickID
TickInterval = [t_start,t_end]
TickStamp = (epoch,tick,phase,ordinal)
```

```text
Physical time != runtime tick
TickStamp order != happens-before
```

TickID is a scheduler step identity, not a physical time unit.

## 10. Scheduler phases

Logical order:

```text
Ingress
ContinuousAdvance
Revalidate
Commit
PublishSnapshot
Control
IndexUpdate
Dispatch
```

Implementations MAY combine phases if observable semantics are preserved.

### ContinuousAdvance

Advance admitted continuous semantic processes over `[t0,t1]`, including Channel transit and reaction kinetics. The active effect/model semantics are authoritative; solver/integrator bookkeeping remains runtime realization detail.

### Revalidate

Check commit guards after continuous advance and before discrete state transitions or admitted lifecycle changes that require current guards.

### Commit

Runtime confirms due discrete semantic transitions/settlements and appends committed Events. A transition may carry an `effective_at` earlier than `committed_at` only within the declared TemporalTolerance; `committed_at` MUST NOT be backdated.

### PublishSnapshot

Expose coherent post-commit WorldRevision.

### Control

Evaluate Controllers against published snapshot and plan subsequent bounded actuation. Controller registration does not bypass later authority/resource/timing revalidation.

### IndexUpdate

Pass WorldRevision changes to World Index updater.

### Dispatch

Notify Events, ready await continuations, schedule handlers/microsteps.

## 11. Event time semantics

Committed Events may carry:

```text
EventTimeRecord {
    effective_at : Instant
    committed_at : Instant
}
```

- `effective_at`: model/world time at which effect is semantically effective。
- `committed_at`: runtime time at which Commit phase records/applies it to authoritative state/history。

Exact boundary:

```text
effective_at == committed_at
```

Approximate/coarse scheduling:

```text
|committed_at - effective_at| <= required event-time tolerance
```

`committed_at` is monotonic with runtime commitment and MUST NOT be written as an earlier past commit.

## 12. Same-tick order / microsteps

Runtime may total-order same-tick work by:

```text
(phase,ordinal)
```

but serialization alone creates no causal edge.

Zero-time work at one Instant uses:

```text
MicrostepOrdinal
MicrostepBudget
```

MicrostepBudget MUST bound zero-time chains.

## 13. CHANNEL / TRANSFER

```text
Channel<K : Transferable>
TRANSFER<K>(Channel<K>,PayloadOf<K>) -> TransferHandle<K>
```

Accounting:

```text
source_account -= account(payload)
transit_account += account(payload)
```

arrival:

```text
transit_account -= account(payload)
destination_account += account(payload)
```

for each required ledger:

```text
ΔL_source + L_transit + ΔL_destination = 0
```

For non-zero propagation, source debit + Transit activation are one initial atomic group, and destination credit + Transit settlement are one later atomic group. No partial authoritative source debit without corresponding accounted transit is permitted.

## 14. Transfer timing

Physical/model propagation:

```text
τ = d / v_m
effective_arrival_at = sent_at + τ
```

Scheduler tick size MUST NOT redefine this modeled arrival time.

If runtime commits delivery later:

```text
CommitLatency = committed_at - effective_arrival_at
```

and required TemporalTolerance MUST be satisfied.

## 15. await semantics

For:

```text
await tx;
B();
```

successful delivery ensures:

```text
Delivered(tx) ≺ B
```

Continuation timing:

```text
DispatchLatency = resumed_at - committed_at
ResponseLatency = resumed_at - effective_at
```

Event effective time, commit time, and continuation resume time are separate.

Exclusive Write Lease across suspension remains forbidden unless a specific contract permits it.

## 16. Matter TRANSFER

```text
PayloadOf<Matter> = MatterPayload
```

Composition is not a universal conserved scalar. Structure-preserving transfer may require:

```text
PreserveStructure<S>
```

Payload/structure equality does not imply Entity/Agent identity.

## 17. RECONFIGURE / Reaction

RECONFIGURE requires Write Lease, authority, accounting obligations, requested invariants, and IdentityPolicy when preserving identity.

High-level reaction metadata expands to existing operations; no `REACT` primitive exists.

Chemical species update:

```text
Δn_i = ν_i ξ
```

Species identity itself is not a conserved ledger.

Instantaneous admitted reconfiguration may commit as a discrete TRANSITION. Temporally extended reconfiguration activates an admitted Dynamics/Kinetic semantic process; numerical integration steps are not the world ontology.

## 18. KineticContext / continuous kinetics

```text
KineticContext {
    composition
    thermodynamic_state
    volume?
    surface_area?
    structure?
    catalyst_state?
    fields?
    observed_at
    revision_set
}
```

```text
KineticContext != live world state
```

Normative kinetics:

```text
dξ/dt = rate(context(t))
```

Reaction network:

```text
dn_i/dt = Σ_j ν_i,j (dξ_j/dt)
```

## 19. Numerical integration

Runtime approximates continuous semantics using `IntegratorContract` over TickIntervals.

```text
Integrator approximation != physical law
```

An `IntegrationReport` records interval, integrator identity/revision, substeps, estimated errors, tolerance, and acceptance.

If required tolerance cannot be met, runtime MUST fail or choose a compatible alternative before applying unsafe approximation.

```text
numerical error != Measurement uncertainty
```

## 20. Pathway / Catalyst / Equilibrium

```text
ReactionRule != ReactionPathway
Stoichiometry != RateLaw
Kinetics != Thermodynamics
Catalyst != equilibrium shift
```

Reversible net rate:

```text
rate_net = rate_forward - rate_reverse
```

Reaction quotient:

```text
Qr = Π_i a_i ^ ν_i
```

Equilibrium uses one explicit thermodynamic convention and tolerance. Driving beyond equilibrium requires explicit work/reservoir/matter/state effects.

## 21. CONSTRAIN / Controller timing

CONSTRAIN registers feedback control rather than a source infinite loop or a new world law.

Controller timing requirements may include:

```text
sample_period
max_jitter
actuation_latency_bound
```

The activated Controller contract must bound target/effect/model/resource/timing/authority scope. Every later actuation remains subject to current revalidation and can fail if authority, resources, compatibility, target validity, or timing requirements are not satisfied.

If scheduler cannot satisfy mandatory timing:

```text
ControllerTimingUnsatisfied
```

## 22. Scheduled work / Event queue

Scheduled work has physical `due_at` Instant plus dependencies. Causal dependency must be satisfied before eligibility.

Same-time independent work MUST have stable ordering under deterministic replay profiles.

Priority does not imply authority.

## 23. World Index update

After Commit/PublishSnapshot, runtime may update World Index synchronously or asynchronously.

It MUST retain mapping information:

```text
WorldRevision -> WorldIndexRevision / source_world_revision
```

v0.6.4 ConsistencyPolicy governs acceptance of lagging indexes.

## 24. Event / History

Committed world effects enter:

```text
H = (E,≺)
```

Normal execution appends Events and does not delete past Events.

An Event may record both `effective_at` and `committed_at`; causal/history commitment follows committed execution, not a backdated runtime record.

Restore adds a new restoration Event and does not rewrite prior Events. Rewind mutates existing `H`, is not ordinary `RECONFIGURE`, and is owned by [`temporal-causality.md`](temporal-causality.md).

```text
Restore != Rewind
Capability<History,Causality,Rewrite>
Energy/resource magnitude != temporal/causal authority
```

The current reference implementation does not support Rewind. Unsupported committed-history mutation fails closed as `HistoryMutationDenied`; admitted temporal operations with missing or invalid causal authority fail as `TemporalAuthorityError`; a cyclic proposed history fails as `CausalityCycleError`.

## 25. Deterministic replay

Replay records compatible inputs and runtime decisions using:

```text
ReplayManifest
TickRecord
```

Compatibility includes initial world state/revision, code semantics, registry, scheduler policy, integrator contracts, deterministic ordering, and external/random inputs.

Before start mismatch:

```text
ReplayIncompatible
```

During replay mismatch:

```text
ReplayDivergence
```

## 26. Replay vs Rewind

```text
DeterministicReplay != Rewind
```

Replay reconstructs execution in another runtime/simulation instance; it does not mutate committed history of the original world.
Replay evidence, state hashes, and recorded decisions grant no `Capability<History,Causality,Rewrite>`.

## 27. Source-language boundary

`RuntimeTickID`, `SchedulerPhase`, `MicrostepOrdinal`, `TickStamp` are internal runtime metadata.

Normal portable MIR/source MUST NOT depend on tick count for semantic behavior.

```text
now_monotonic() -> Instant
```

remains the portable time read concept.

## 28. Failure stages

```text
parse / elaboration
load / registry compatibility
resolver / index
PREPARE / feasibility / scheduling
COMMIT
runtime / integration / dispatch
identity / causality
replay diagnostics
```

PREPARE-before-COMMIT failure should leave no irreversible physical world effect. Failure of the initial `KernelAtomicGroup` before successful commit leaves none of that group's members authoritative. After one or more physical Events/lifecycle transitions have committed, later runtime failure may leave already-committed state/history and active-effect settlement obligations; general rollback is not guaranteed.
