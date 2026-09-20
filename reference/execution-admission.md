# Explicit execution admission — source/program boundary foundation

**Status:** unreleased v1 semantic-completion candidate, public Issue #23 under
public Issue #25; genericity proof owned by public Issue #26. This checkpoint
implements **representation, compilation, structural admission and fail-closed
execution denial only**. It does not complete any of those public Issues or
authorize a release. The released RC surface remains historical evidence.

## 1. DefinitionSource and scope

This file owns the explicit program policy/group representation accepted by
decision D-01. It refines, not replaces, the owners:

- [program artifact](magical-program-artifact.md): untrusted values, graph and requirements;
- [source language](mgls-source-language.md): syntax and lowering;
- [World Kernel](kernel-execution.md): semantic atomic groups and five lower classes;
- [runtime](magical-program-runtime.md): PREPARE, frozen bindings, revalidation,
  registered executors, atomic COMMIT and replay;
- [feasibility](feasibility.md): prediction is neither authority nor reservation.

No physical domain belongs to this layer. Group IDs, display names, filenames
and example identities select neither an executor nor authority. No new MKI,
World Kernel interaction class, public ECIR, parallel runtime or implicit
partition is introduced.

## 2. Closed optional representation

**EA-STRUCT-001 — Explicit opt-in.** A program MAY carry:

```json
{
  "execution_admission": {
    "contract_id": "execution-admission",
    "revision": "1",
    "policy": "Incremental",
    "atomic_groups": [
      {"group_id": "first", "node_ids": ["resolve", "effect"]},
      {"group_id": "later", "node_ids": ["calculate"]}
    ]
  }
}
```

This is an optional field of the current MagicalProgram-0 envelope, not a new
IR or release version. Every field above is required when the record is
present. Unknown fields, unknown policies/revisions and null records MUST
fail closed. An older reader rejects the unknown root field; it MUST NOT
remove it to execute a downgraded program.

The policy and partition are source/program semantics. The host cannot
reinterpret an explicit WholePlanPreflight request as Incremental. Neither
policy supplies host Capability/Lease/identity/accounting evidence.

- `Incremental` requests separately admitted groups. A later failure cannot
  erase an earlier committed group.
- `WholePlanPreflight` additionally requests completion-feasibility evidence
  before the first effect. This does not reserve resources or waive later
  revalidation, nor does it make the program globally atomic.

These are requested contracts, **not implemented execution guarantees at this
checkpoint**. Binding, prediction model support, lifecycle settlement, failure
outcomes and conformance evidence remain required follow-up under the owning
public Issues. They must be completed before execution is enabled.

## 3. Partition and ordering

**EA-STRUCT-002 — Exhaustive disjoint ownership.** Every node, including pure
computation and resolution, MUST belong to exactly one nonempty group. Group
IDs MUST be unique. Missing, overlapping, unknown or duplicate node membership
is invalid. Groups are not nested, inferred from effect kinds, or derived from
node order.

**EA-STRUCT-003 — Compatible explicit order.** The group array explicitly
specifies the requested sequence of commit boundaries. The partition MUST
agree with the existing deterministic node order: groups cannot reverse or
interleave that order. Within a group, node order retains its existing owner;
the presentation order of `node_ids` does not override it. Reordering JSON
properties or the physical `nodes` array while retaining `node.order` does
not change validity.

Cross-group data use still requires an explicit forward producer/consumer
edge. Membership does not synthesize bindings, retarget references, remove
data dependencies, or define a scheduler tick as physical/causal time.
This finite sequential representation does not implement parallel, await,
reactive loops or persistent-effect lifecycle.

**EA-STRUCT-004 — Existing limits and safety remain.** The ordinary byte,
node, edge, value, depth, budget and contract-admission ceilings still apply.
There cannot be more nonempty disjoint groups than nodes. A source-authored
group cannot raise a host ceiling or supply a host-owned record.

## 4. Source lowering and provenance

**EA-STRUCT-005 — Explicit lowering.** Immediately after the unchanged six-part
MGLS header, an optional declaration chooses the policy:

```mgls
admission Incremental;
// or: admission WholePlanPreflight;
```

Values still precede nodes. With admission present, every node declaration
MUST appear inside `atomic <group-name> { ... }`. Without admission, atomic
blocks are prohibited. Mixing grouped/ungrouped nodes, empty/nested blocks,
duplicate policies or groups, and blocks after outputs MUST be rejected.

Blocks do not introduce local value scopes. Existing global binding,
type/contract/obligation checks and forward-edge generation remain unchanged.
Group names occupy a separate namespace and confer no identity or authority.
The compiler emits source spans for the explicit policy and each whole block;
the contract identity is marked synthesized. Whitespace/comments affect
source locations, not selected policy or membership.

See [example source](../examples/execution-admission/explicit-groups.mgls).

## 5. Compatibility and the current implementation gate

**EA-STRUCT-006 — No silent flattening.** A structurally valid grouped program
can be compiled/checked, but evaluation returns an `Infeasible` report with
`UnsupportedExecutionAdmission`. PREPARE independently rejects the root
field, including a single explicit group and a caller-supplied report claiming
feasibility. No executor or COMMIT is reached and authoritative state/History
is unchanged. Replay reproduces this rejection, not a fabricated grouped run.

**EA-STRUCT-007 — Ungrouped compatibility.** Absence of the record preserves
the exact prior single-program atomic COMMIT path. The compiler MUST NOT insert
an implicit policy or split an existing program. Legacy inputs are not silently
upgraded to a whole-plan guarantee.

The next implementation must execute admitted groups through the **same**
evaluator/PREPARE/revalidation/registered executor/COMMIT machinery. It must
preserve immutable cross-group bindings, current authority and resource checks,
prior committed effects and deterministic replay. Required matter and non-water
proof, preflight drift cases, lifecycle/cleanup authority and genericity tests
are outstanding; the structural fixture is not a substitute for them.

## 6. Diagnostic and evidence ownership

| Code | Boundary |
|---|---|
| `ProgramSchemaViolation` | Closed record/field/shape violation |
| `ProgramDuplicateAtomicGroup` | Duplicate group identity |
| `ProgramAtomicGroupUnknownNode` | Membership names an absent node |
| `ProgramAtomicGroupOverlap` | More than one group owns a node |
| `ProgramAtomicGroupIncomplete` | At least one node has no owner |
| `ProgramAtomicGroupOrderViolation` | Reversed/interleaved partition |
| `UnsupportedExecutionAdmission` | Recognized contract is not executable yet |

Source parse errors use existing `ParseError` /
`UnsupportedSemanticExtension`; independently detected target violations use
`StructuredInputInvalid` with the target code/path. No partial compiled program
is returned.

Machine-readable rule/test mapping:
[execution-admission-structure.json](../conformance/execution-admission-structure.json).
This is checkpoint evidence, not an additional released conformance class.
The released 4/65/14 counts are unchanged because grouped execution is not yet
implemented, **not** because public Issue #23 may be postponed out of v1.
Required v1 execution coverage must be integrated and freshly audited before
public Issue #23/public Issue #25 can close.
