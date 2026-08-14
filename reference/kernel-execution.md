# World Kernel Execution Boundary

**Status:** normative semantic execution boundary for pre-v1.0 stabilization.

## Purpose

This reference defines the semantic boundary between the six portable MKI operations and authoritative world evolution. It resolves the remaining pre-public archive Issue #55 ownership questions without exposing scheduler microsteps, numerical integration steps, storage layout, or a new public intermediate representation as part of the stable language surface.

The lower boundary exists so that persistent semantic effects, atomic state changes, measurement, and service queries can be described independently of one implementation's runtime bookkeeping.

## Key invariants

```text
MKI primitive set = 6
Kernel interaction class != MKI primitive
Kernel interaction class != public source/IR syntax
Kernel interaction class != numerical integration step
World Kernel != DefinitionSource
World Kernel != authority source
World Kernel != physical law
runtime bookkeeping != semantic active-effect ownership
control-plane COMMIT != all future consequences already occurred
scheduler Commit != control-plane COMMIT
DEACTIVATE != rollback
```

## 1. Stable public boundary vs lower execution boundary

The portable MKI semantic ABI remains:

```text
RESOLVE
OBSERVE
CHANNEL
TRANSFER
RECONFIGURE
CONSTRAIN
```

An implementation may lower one MKI operation into multiple lower interactions, or combine multiple MKI operations into one atomic realization, provided the observable MKI semantics, authority, identity, accounting, timing, provenance, and model obligations are preserved.

A lower semantic execution boundary is required for v1.0 conformance, but the project does **not** freeze a serialized `ECIR` artifact or one implementation-specific storage representation. `ECIR` may be used informatively as shorthand for an implementation encoding of this contract.

## 2. Kernel interaction classes

World Kernel realizations use five semantic interaction classes:

```text
QUERY
SAMPLE
TRANSITION
ACTIVATE
DEACTIVATE
```

These classes are specification-owned semantic categories. Their concrete object model, wire format, batching representation, storage layout, solver integration, and internal API are implementation/profile-owned unless another reference explicitly says otherwise.

### QUERY

Read authoritative service/state evidence without itself performing a physical measurement or changing world state.

Typical use: resolver evidence, identity/state revision lookup, registry/profile compatibility evidence.

```text
QUERY != OBSERVE
QUERY != Measurement
```

### SAMPLE

Acquire an observation under an admitted observation model.

If the observation model has physical back-action, that mutation cannot be hidden inside SAMPLE. The back-action must be represented in the same admitted atomic group through ordinary transition/activation semantics and normal accounting/authority rules.

### TRANSITION

Commit a guarded discrete semantic state change.

A TRANSITION may change entity state, accounting state, history-visible discrete state, or other authoritative world state, but only under admitted model, identity, conservation, authority, lease, compatibility, and current-state guards.

### ACTIVATE

Create or enable a semantically active admitted effect whose consequences may continue after the initial commit.

Examples include:

```text
Transit
active Channel
Controller
Kinetic/DynamicsProcess
```

ACTIVATE does not install arbitrary equations or create authority. It references an admitted model and a bounded effect contract.

### DEACTIVATE

Terminate, settle, or disable a previously active semantic effect according to its admitted lifecycle contract.

```text
DEACTIVATE != rollback
DEACTIVATE != erase history
DEACTIVATE != discard conserved in-flight state
```

## 3. Authoritative active-effect ownership

Any persistent object that can causally affect future authoritative world evolution has an authoritative **semantic projection** owned by WorldState/world evolution semantics.

This includes the semantically relevant state of Transit, active Channel, Controller, and Kinetic/DynamicsProcess objects.

The existing runtime configuration remains:

```text
C = <Σ,H,Ω,P>
```

but the ownership rule is:

```text
causally relevant active-effect semantics ⊆ authoritative Σ semantics
runtime handles / queues / caches / solver bookkeeping ⊆ Ω
```

An implementation may physically store an active-effect handle or realization record in `Ω`, but it MUST preserve an authoritative semantic projection associated with the current WorldRevision. `Ω` alone must not be the only unspecified owner of information that determines future world evolution.

Storage placement is therefore not normative. Semantic ownership is.

## 4. Effect contracts

Every ACTIVATEd effect carries or references an admitted contract sufficient to determine its portable semantic bounds.

At minimum, as applicable:

```text
effect identity / kind
model identity + revision
subject / target refs
validity domain
required Capability / Lease
resource / accounting obligations
timing bounds
termination / settlement conditions
revalidation requirements
provenance
```

A contract may reference Registry, World, or Profile-owned models. ACTIVATE does not transfer ownership of those definitions to World Kernel.

## 5. COMMIT semantics

Control-plane COMMIT moves an admitted initial effect realization into irreversible execution eligibility and atomically commits the initial semantic group.

It may commit:

- one or more discrete TRANSITIONs;
- ACTIVATE one or more continuing effects;
- DEACTIVATE/settle active effects;
- an atomic combination of the above.

It does **not** mean that all future consequences of an ACTIVATEd effect have already happened.

```text
PREPARE
→ current revalidation
→ control-plane COMMIT(initial atomic group)
→ active-effect lifecycle / physical evolution
→ later scheduler Revalidate + Commit for due discrete transitions
```

Later scheduler Commit phases apply due discrete semantic transitions under current guards. Continuous evolution remains governed by the admitted continuous model; the integrator approximates it and does not become the physical law.

## 6. Atomic semantic groups

Operations that require multiple state/accounting/effect changes to preserve invariants use an atomic semantic group.

```text
KernelAtomicGroup {
    guards
    accounting obligations
    transitions[]
    activations[]
    deactivations[]
    provenance
}
```

The semantic guarantee is all-or-none at the commit boundary:

```text
mandatory guard failure
→ no member of the group becomes authoritative
```

This forbids partial source debit, orphan transit activation, partial identity replacement, or other intermediate authoritative states that violate mandatory invariants.

An implementation may internally use transactions, journaling, copy-on-write, or another mechanism. That mechanism is not the specification.

Atomicity is scoped to one admitted group. It does not silently promise that every later
group in a multi-group plan can complete. `execution-admission.md` defines mandatory
`LocalAdmission`, optional explicit `WholePlanPreflight`, and the rule that a later failure
does not roll back earlier separately committed groups.

## 7. TRANSFER lowering

### Zero-propagation supported case

A transfer whose admitted model is semantically instantaneous may lower to one atomic group containing source debit and destination credit.

### Non-zero propagation

A non-zero-latency transfer is temporally extended:

```text
initial COMMIT:
  TRANSITION(source debit)
  + ACTIVATE(Transit payload/process)

propagation:
  admitted transport model determines evolution / arrival time

arrival settlement COMMIT:
  TRANSITION(destination credit)
  + DEACTIVATE(settle Transit)
```

Source debit and Transit activation are one atomic group. Arrival credit and Transit settlement are one atomic group.

Conservation/accounting includes in-flight payload:

```text
source + transit + destination = conserved total
```

Scheduler tick width must not redefine modeled arrival time.

Emergency stop during transit cannot delete the payload. The active contract determines whether the result is continue, hold, redirect, dissipate under an admitted model, or another accounted settlement.

## 8. RECONFIGURE lowering

An instantaneous admitted reconfiguration may lower to a TRANSITION.

A temporally extended reconfiguration lowers to ACTIVATE of an admitted Dynamics/Kinetic process.

For continuous models:

```text
dX/dt = F(context(t), model)
```

is semantic/model-owned, while numerical integration is an approximation service.

```text
integrator substep != TRANSITION
integrator substep != physical primitive
```

Discrete semantic events produced by the process are committed through ordinary guarded scheduler Commit boundaries.

## 9. CONSTRAIN lowering and bounded actuation

CONSTRAIN activates a Controller effect contract rather than rewriting world law.

The controller contract bounds at least, as applicable:

```text
target / subject set
observation model / properties
allowed actuation effect classes
allowed model identities
required Capability / Lease
resource / Energy ceilings
timing / jitter / latency bounds
termination conditions
revalidation policy
```

Controller registration grants no unlimited future authority.

Each future actuation intent must remain inside the registered bounds and must satisfy the required current revalidation. Revoked/expired authority, exhausted resources, incompatible models, stale targets, or unsatisfied timing can cause the constraint to fail.

A Region/predicate-scoped Controller may derive a bounded future target set, but Region ownership,
crossing predicates, Relation, visibility, or index metadata do not grant authority. The Controller contract
must bind anchor/Region identity, maximum target/event scope, effect class, validity interval, and
`no authority amplification`; every actuation revalidates Capability and Lease. `SUCCESS-ARCANA-001`
in `success-arcana.md` is the experimental conformance example.

A desired constraint is therefore not a new physical invariant:

```text
requested constraint != guaranteed world law
```

## 10. OBSERVE back-action

SAMPLE represents measurement semantics. If the admitted observation model perturbs the world, the perturbation must be included as an ordinary world effect in the relevant atomic group.

A consumer must not treat a back-action-bearing measurement as a pure QUERY.

## 11. Emergency stop and deactivation

Emergency-stop behavior is a fence/lifecycle action, not rewind.

For active effects, the runtime requests DEACTIVATE/settlement according to the admitted effect contract and safety policy. Already committed history remains committed. Conserved state remains accounted until a valid settlement transition occurs.

```text
emergency stop requested != rollback
stopped != previous world restored
```

## 12. Runtime `Ω` boundary

`Ω` may contain implementation/runtime realization data such as:

```text
scheduler queues
solver handles
cached active-effect handles
prepared work
replay recorder state
runtime epoch/tick metadata
index snapshot handles
```

If a field is necessary to determine portable future world semantics, its semantic projection must be authoritative under WorldState/effect-contract semantics rather than existing only as opaque `Ω` bookkeeping.

This preserves:

```text
Physical time != runtime tick
Integrator approximation != physical law
runtime metadata != world cause merely because it is stored near semantic handles
```

## 13. Runtime-1.0 conformance obligations

Runtime-1.0 must test the observable semantic boundary, not one implementation's micro-operations.

Required classes of checks include:

1. atomic group failure leaves no partial authoritative transition/activation;
2. non-zero TRANSFER accounts in-flight payload and preserves model-defined arrival time independent of scheduler tick width;
3. emergency stop during transit preserves accounting and follows explicit settlement semantics;
4. continuous RECONFIGURE preserves model-vs-integrator separation;
5. CONSTRAIN registration does not grant unbounded future authority;
6. later controller actuation revalidates authority/resources/timing and may fail;
7. causally relevant active-effect semantics are reproducible from authoritative world/effect evidence rather than hidden only in runtime bookkeeping;
8. observation back-action is explicit and accounted;
9. DEACTIVATE never implies rollback;
10. the six MKI operations remain the portable public semantic ABI.

Conformance artifacts may encode the lower interactions for test evidence, but no specific serialized ECIR form is required by Core-1.0 or Runtime-1.0 unless a later release explicitly standardizes one.

## 14. Ownership

Specification owns:

- the five interaction-class meanings;
- active-effect semantic ownership rule;
- atomic-group semantic guarantee;
- COMMIT vs later scheduler Commit distinction;
- MKI lowering obligations and safety invariants.

Registry / World / Profile own their existing model, revision, compatibility, tolerance, and environment-specific facts.

Implementation owns:

- internal ECIR/object representation;
- storage layout of Σ/Ω realization data so long as semantic ownership is preserved;
- transaction mechanism;
- scheduler data structures;
- solver/integrator algorithms within admitted contracts;
- optimization/fusion of lower interactions that preserves observable semantics.

## 15. Non-goals

This reference does not:

- add a seventh MKI primitive;
- standardize a public ECIR serialization;
- expose raw SET/WRITE/CREATE/DELETE operations;
- make scheduler or integrator steps physical primitives;
- permit arbitrary dynamics injection;
- define World Kernel as new authority or DefinitionSource;
- require one WorldState storage layout;
- claim that the world is literally software, binary, discrete, or simulated.
