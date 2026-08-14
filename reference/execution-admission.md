# Execution Admission — current v1 contract

**Status:** normative current reference. public Issue #23 owner.

## Purpose

This document separates mandatory per-effect safety admission from an optional,
explicit assessment of whether every currently known step of a plan can finish.
It prevents both of these incorrect conclusions:

```text
incremental execution == permission to bypass local guards
whole-plan preflight == reservation / authority / completion guarantee
```

## 1. Terms and ownership

`ExecutionAdmissionPolicy` selects one of two portable modes:

```text
Incremental
WholePlanPreflight
```

`LocalAdmission` is not a selectable weakening.  It is mandatory immediately
before every bounded `KernelAtomicGroup` and every later Controller/process
actuation.  It revalidates all applicable type, identity, Capability, Lease,
conservation, accounting, sandbox, timing, and runtime-safety obligations.

`WholePlanPreflight` is an explicitly requested, snapshot-scoped assessment of
all currently modeled groups.  A source contract may require it.  Otherwise a
RuntimeProfile may select it only through an explicit policy rule whose
identity, revision, DefinitionSource, and provenance are recorded before
PREPARE.  There is no language-independent implicit default.  An unresolved
required policy fails closed.

```text
source-explicit requirement
> profile-selected policy
> unresolved
```

A profile must not silently weaken a source requirement from
`WholePlanPreflight` to `Incremental`.

Specification owns the meanings and invariants in this document.  Source or
RuntimeProfile owns the selected policy.  Registry/World/Profile continue to
own their model facts.  Implementations own internal plan/handler/transaction
representations; this document does not standardize a serialized ECIR.

## 2. Local admission is mandatory

Before an atomic group becomes authoritative, the runtime revalidates all
applicable mandatory obligations against current authoritative evidence.

```text
LocalAdmission(group, current C=<Σ,H,Ω,P>)
→ Pass | Reject(stable diagnostic)
```

Failure means no member of that group becomes authoritative.  This retains the
`KernelAtomicGroup` all-or-none rule.  It does not imply rollback of earlier,
separately committed groups.

An incremental policy therefore cannot bypass:

- type/dimension validity;
- identity policy and state-revision binding;
- Capability and Lease;
- conservation/accounting;
- sandbox, emergency-stop, resource, timing, or actuation bounds;
- current compatibility/revalidation obligations.

## 3. Incremental execution

In `Incremental` mode, each bounded group may pass local admission and commit
before a later group is known to be executable.

```text
LocalAdmission(G1) → COMMIT(G1)
LocalAdmission(G2) → Reject
```

If `G2` fails, `G1` remains in authoritative WorldState/History.  The runtime
records `ContinuationInfeasibleAfterPartialCommit`, including the failed group
and count of already committed groups.  It must not report a plan-wide ABORT as
if those commits never occurred.

```text
later failure != rollback of prior commit
failure Event != deletion of successful Event
```

Compensation, if a future contract defines it, is a new authorized/accounted
effect.  It is not hidden rollback.

## 4. Whole-plan preflight

`WholePlanPreflight` evaluates every currently known group against one recorded
WorldRevision, RuntimeProfile revision, and model-evidence set before the first
authoritative effect.  If completion is not supportable under that assessment,
the plan is rejected with `WholePlanPreflightRejected` and
`phase=BeforeFirstEffect`.

The assessment must record:

- source WorldRevision;
- RuntimeProfile identity/revision;
- model/evidence identities;
- policy identity/revision and DefinitionSource;
- that no reservation or authority was created;
- that runtime completion is not guaranteed.

The assessment is not a lock on the future world.  Unless a separate explicit
contract performs an authorized reservation, later state, authority, model, or
resource changes may still cause ordinary local revalidation to reject a group.

```text
WholePlanPreflight != Reservation
WholePlanPreflight != Capability grant
WholePlanPreflight != Lease
WholePlanPreflight != RuntimeSafetyGuarantee
Feasibility dry-run != WholePlanPreflight execution guarantee
```

## 5. CONSTRAIN termination after partial progress

If an earlier group transferred matter and activated a bounded controller, a
later continuation failure terminates/deactivates that controller according to
its lifecycle contract.  Deactivation is a new committed lifecycle event.

The transferred matter remains where the committed world effect placed it.
Ordinary world dynamics, including gravity, continue or resume according to the
world/model contract.

```text
DEACTIVATE(controller) != rollback transfer
DEACTIVATE(controller) != remove gravity
```

Any required settlement remains subject to ordinary authority, conservation,
accounting, and local admission.

## 6. Feasibility and planning boundary

The Feasibility Evaluator may report evidence useful to either policy, but a
dry-run does not choose the policy, reserve resources, grant authority, or make
a runtime guarantee.  It preserves:

```text
Source Unknown
!= Estimate
!= PlanningAssumption
!= PrepareBound / runtime-resolved value
```

`WholePlanPreflight` is runtime/control-plane admission using a recorded
snapshot and current authoritative evidence.  It must not rewrite explicit
source semantics or convert prediction confidence into authority/truth.

## 7. Stable diagnostics

The following diagnostic identities are stable for this contract:

| Code | Phase | Meaning |
|---|---|---|
| `WholePlanPreflightRejected` | `BeforeFirstEffect` | explicit whole-plan assessment found a later group infeasible before any commit |
| `LocalAdmissionRejected` | `BeforeFirstEffect` | the first group failed a mandatory local guard |
| `ContinuationInfeasibleAfterPartialCommit` | `AfterPartialCommit` | a later group failed after one or more authoritative commits |

Diagnostics record the failed group, failed mandatory guard, and committed-group count.  They do not
turn a failed estimate into proof, conceal committed history, or expose an
implementation-specific ECIR.

## 8. Paired normative example

The paired water-transfer example has 50 kg of accounted source matter and two
groups requesting 40 kg then 20 kg.

`Incremental`:

1. the 40 kg transfer + bounded `CONSTRAIN` activation passes local admission;
2. the group commits;
3. the 20 kg continuation fails conservation admission;
4. the controller is deactivated without rollback;
5. 40 kg remains at the destination and gravity applies;
6. History contains both the successful group Event and termination Event.

`WholePlanPreflight`:

1. the same two groups are assessed against the recorded snapshot;
2. the second group is found infeasible;
3. rejection occurs before the first effect;
4. WorldState/History are unchanged;
5. no reservation, Capability, or completion guarantee is created.

The machine-readable evidence is:

- `schemas/execution-admission.schema.json`;
- `schemas/execution-admission-traceability.schema.json`;
- `examples/execution-admission/`;
- `src/runtime/execution_admission.py`;
- `tests/test_execution_admission.py`.

These cases do not add a seventh MKI primitive.  They use only `TRANSFER` and
`CONSTRAIN`; lower interaction classes remain `QUERY / SAMPLE / TRANSITION /
ACTIVATE / DEACTIVATE`.

## 9. Canonical water-ball compatibility

WB-CANON-001 remains one admitted `KernelAtomicGroup` in the released reference
subset.  Its all-or-none commit result is unchanged.  That fixture demonstrates
atomicity of its group; it is not a universal claim that every multi-group plan
has whole-plan completion feasibility.

## 10. Replay

Replay uses the same policy identity/revision, input case, source snapshot, and
model/profile evidence.  It compares the resulting diagnostic, committed group
IDs, History Event IDs, and final authoritative state.

```text
DeterministicReplay != Rewind
```

Replay mismatch is divergence.  Replay does not undo the original committed
world effects.

## 11. Non-goals

This contract does not:

- add an MKI primitive or World Kernel interaction class;
- standardize a public serialized ECIR;
- define a reservation protocol;
- guarantee completion under future world changes;
- weaken local authority, identity, conservation, or safety checks;
- define hidden rollback/compensation;
- change historical `spec/` snapshots.
