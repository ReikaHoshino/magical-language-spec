# Sandboxed Runtime Implementation Reference — v0.9.0

**Status:** informative reference implementation profile; normative semantics remain in the linked current reference documents.

## Purpose

v0.9.0 extends the released v0.8 evaluator with the first deterministic sandbox execution path. It consumes v0.8-produced `TypedMIR` / `KernelPlan` / `FeasibilityReport` artifacts and executes the supported subset against an in-memory test world.

This document describes the reference implementation. It does not redefine MKI, PREPARE/COMMIT, scheduler/time, security, authority, conservation, active-effect ownership, World Kernel interaction semantics, or replay semantics.

## Normative dependencies

- `mki.md`
- `kernel-execution.md`
- `semantics.md`
- `runtime-time.md`
- `security-sandbox.md`
- `planning-inference.md`
- `feasibility.md`
- `evaluator-implementation.md`
- `world-index.md`
- `registry.md`
- `canonical-water-ball.md`

## Single frontend/planning path

v0.9 MUST reuse v0.8 output. It does not introduce a second parser, elaborator, resolver, or planner.

```text
supported v0.8 input
→ LocalEvaluator
→ FeasibilityReport
→ TypedMIR / KernelPlan / PlanningAssumption evidence
→ PREPARE
→ Revalidate
→ COMMIT
→ sandbox MKI runtime
→ Σ' + H' + Ω' + P'
```

The runtime has no public source/NSR compiler path of its own.

## Sandbox configuration

The reference implementation models the specification configuration explicitly:

```text
C = <Σ,H,Ω,P>
```

- `Σ`: authoritative in-memory sandbox world state, entity state revisions, controllers, and any semantic projection required by the supported world evolution.
- `H`: committed event history.
- `Ω`: scheduler/runtime realization state, channel/reservation handles, profile identity, queues, and active-work bookkeeping.
- `P`: current process state and PreparedPlan/commit lifecycle.

`WorldIndex` remains a search/read model and is not substituted for `Σ`.

The v0.9 implementation's placement of some channel/active-work handles in `Ω` is a storage/realization choice, not semantic ownership. Under `kernel-execution.md`, any persistent state that causally determines portable future authoritative evolution must have an authoritative semantic projection under WorldState/effect-contract semantics. The canonical v0.9 fixture does not claim to implement the full non-zero Transit / general continuous Dynamics lifecycle standardized later by the current reference.

## PREPARE

`SandboxRuntime.prepare()` accepts only evaluator reports whose overall status is `Feasible` or `ConditionallyFeasible` and that contain v0.8-produced TypedMIR/KernelPlan evidence.

PREPARE:

- preserves the six MKI data-plane primitive boundary;
- requires `revalidation_required=true`;
- binds source world/index/profile/evidence revisions;
- carries Capability, Lease, accounting, resolution evidence;
- preserves v0.8 PlanningAssumptions rather than rewriting source Unknowns;
- records reversible resource reservation intent in `PreparedPlan`;
- does not mutate authoritative `Σ` or `H`.

## Revalidate / COMMIT

Immediately before COMMIT the runtime rechecks:

- current world revision;
- referenced entity state revision evidence;
- runtime profile identity/revision;
- Capability activity;
- Lease activity;
- conservation/accounting evidence;
- emergency-stop fence.

Any failed mandatory check aborts without committing state/history changes.

For the supported subset COMMIT is atomic: an exception during mutation restores the pre-COMMIT sandbox configuration.

This atomic supported subset is compatible with the current `KernelAtomicGroup` rule. It does not imply that a general ACTIVATEd Transit, Controller, Channel, or DynamicsProcess has all future consequences committed at activation time.

```text
PREPARE success != permission to skip COMMIT revalidation
Visibility != Authority
Registry metadata != Capability
Estimate != Reservation
control-plane COMMIT != all future consequences already occurred
```

## MKI data plane

The runtime accepts exactly the existing six operations:

```text
RESOLVE
OBSERVE
CHANNEL
TRANSFER
RECONFIGURE
CONSTRAIN
```

`generate`, World Kernel interaction classes, scheduler phases, replay, and COMMIT are not new data-plane primitives.

For WB-CANON-001 the selected v0.8 plan remains `wb:plan:transfer-reconfigure` and all six operations are recorded in deterministic order.

## Control plane

The v0.9 reference trace implements the minimum release subset:

```text
ACQUIRE
COMMIT
RELEASE
ABORT
```

Capability/Lease evidence is not created by ACQUIRE; ACQUIRE records use of already-authoritative evidence admitted by PREPARE/revalidation.

`REVOKE` and `DELEGATE` remain normative control-plane operations but are not implemented by the v0.9 reference subset. Their omission is an explicit implementation deferral, not removal from the specification.

## SandboxProfile

`SandboxProfile` adds restrictions but grants no authority. The reference profile enforces bounded:

- Energy admission;
- event count;
- microsteps per tick;
- concurrency;
- external interaction policy.

A missing/non-Exact Energy bound cannot silently become zero. A plan that exceeds a configured ceiling aborts before world mutation.

```text
Sandbox allowance != Capability
```

## Scheduler and time

The reference engine emits the canonical logical phase order:

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

`TickStamp` is scheduler ordering metadata. It is not physical time.

WB-CANON-001 uses the deterministic fixture values already owned by the canonical conformance case:

```text
effective_at = 2026-01-01T00:00:00Z
committed_at = 2026-01-01T00:00:00.005Z
epoch = epoch:fixture:1
tick = tick:fixture:25
```

The fixed fixture timestamps/profile are conformance data, not universal runtime constants.

## Conservation / identity

The canonical sandbox begins with 100 kg accounted source water. COMMIT moves 50 kg into the new water-ball entity while retaining a 100 kg ledger total.

```text
source allocation: 50 kg
water-ball allocation: 50 kg
accounted total: 100 kg
```

The generated ball uses `NewEntityFromAccountedMatter`; the runtime does not fabricate identity from a WorldIndex candidate.

The one-COMMIT canonical fixture is an instantaneous/synthetic supported case. General non-zero transfer accounting must include the authoritative Transit projection described by `kernel-execution.md` rather than extrapolating this fixture into a destination-write model.

## Planning binding and reactive behavior

The omitted motion terminal remains the v0.8 semantic Unknown. The 50 m horizon remains a distinct PrepareBound PlanningAssumption.

A late unrelated entity does not retarget that PrepareBound terminal. Reactive retargeting would require explicit Dynamic/CONSTRAIN semantics.

Horizontal trajectory control remains an explicit `CONSTRAIN`; gravity is not removed from the world model.

The canonical trace demonstrates that `CONSTRAIN` is explicit; it does not claim that v0.9 implements the full persistent bounded-controller lifecycle now defined normatively by `kernel-execution.md`.

## Emergency stop

The supported emergency-stop entry point fences new PREPARE and COMMIT work. A fence is not represented as rollback of already committed effects.

```text
Emergency-stop requested != stopped
Stopped != rolled back
DEACTIVATE != rollback
```

The current single-process reference subset records the fence/quiescing state. General active-effect termination/settlement must follow the admitted lifecycle/accounting contract; more elaborate distributed quiescence remains out of scope.

## Replay

Replay executes in a cloned sandbox rather than the original world and compares a deterministic state hash over `C=<Σ,H,Ω,P>`.

```text
DeterministicReplay != Rewind
```

The replay manifest records runtime profile, sandbox profile, and the distinction between physical time and runtime tick. A hash mismatch is reported as divergence rather than silently accepted.

For future persistent active-effect implementations, deterministic replay must reconstruct/compare authoritative active-effect semantic evidence rather than relying only on opaque runtime handles.

## Machine-readable trace

Committed and aborted public execution results use:

- `schemas/runtime-execution.schema.json`;
- `document_kind = SandboxExecutionTrace`;
- `schema_version = 1`.

Committed traces contain admission evidence, control-plane records, scheduler records, low-level runtime trace, history event IDs, and a deterministic result-state hash.

Aborted traces contain the fatal cause plus assertions that world revision/history remained unchanged where the failure happened before COMMIT.

## Canonical execution target

WB-CANON-001 executes:

```text
selected NSR
→ v0.8 LocalEvaluator
→ PreparedPlan
→ Revalidate
→ COMMIT
→ RESOLVE / OBSERVE / CHANNEL / TRANSFER / RECONFIGURE / CONSTRAIN
→ world:992 + event:wb-canon-001
```

Explicit source constraints remain unchanged:

- mass 50 kg;
- radius 0.01 m;
- relative distance 3 m;
- initial velocity 0 m/s;
- acceleration 50 m/s²;
- horizontal-forward trajectory.

No hidden automatic collision avoidance or terminal retargeting is added by the runtime.

## Implemented failure coverage

The runtime regression suite exercises at least:

- stale world/state revision;
- revoked/inactive Capability;
- expired/inactive Lease;
- unavailable conservation evidence;
- runtime profile drift after PREPARE;
- emergency-stop fence;
- Energy ceiling exceeded;
- indeterminate Energy admission;
- event/microstep budget exhaustion;
- deterministic replay divergence;
- invalid/non-MKI plan boundary inherited from v0.8;
- no mutation on pre-COMMIT failure.

These are v0.9 implementation tests, not a substitute for the broader Runtime-1.0 obligations in `kernel-execution.md`.

## Explicit v0.9 deferrals

## Experimental executor dispatch

Issue #77 adds an implementation-owned `plan_id -> runtime executor` dispatch. WB-CANON-001 retains its
existing executor and exact result. Only the three admitted `Experimental-Arcana-0` plan IDs are added;
unknown plans fail as `UnsupportedRuntimeSubset`. Every executor still passes PREPARE, current
Capability/Lease/accounting/state revision revalidation, COMMIT, the six MKI operation check, sandbox limits,
History publication, result hashing, and isolated replay. Lower interaction evidence does not become public
serialized ECIR.
- real hardware/world control;
- distributed networking;
- production persistence/spatial index;
- high-performance parallel scheduling;
- exhaustive physical models;
- OS/container-specific isolation contract;
- REVOKE/DELEGATE reference implementation;
- general non-reference language adapters;
- full persistent non-zero Transit lifecycle;
- general continuous DynamicsProcess lifecycle;
- general persistent Controller actuation lifecycle.

Post-v0.9 conformance/stabilization is owned by Issue #40.
