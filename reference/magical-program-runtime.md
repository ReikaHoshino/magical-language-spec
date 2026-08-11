# MagicalProgram-0 Runtime

**Status:** experimental normative owner after pre-public archive Issues #110 and pre-public archive Issue #114.

**Public import:**

```python
from src.runtime.magical_program import MagicalProgramRuntime
```

Former pre-public archive Issue #89 module names are compatibility re-exports only. Exactly one `MagicalProgramRuntime` class owns behavior.

## 1. Common path

```text
MagicalProgram-0
  -> generic evaluator
  -> PREPARE resolution and host-record binding
  -> immediate revalidation
  -> registry-owned bounded executor
  -> atomic COMMIT or total rollback
  -> committed result binding
  -> deterministic replay
```

The core runtime never branches on a contract ID. `RuntimeContractRegistration` owns the executable callable, exact instruction/input/output contract, and declared History event count.

## 2. PREPARE

PREPARE is reversible and does not mutate authoritative configuration.

It:

- checks evaluator and runtime profile identity;
- enforces immutable host ceilings;
- verifies the report describes the exact finite-canonical program digest;
- deep-copies every scalar, record, and sequence binding into runtime-local storage;
- realizes every `ref.resolve` request once;
- freezes selected entity IDs and state revisions;
- resolves each portable requirement to exactly one current host Capability, Lease, identity, evidence, or accounting record;
- verifies target/effect/mode/kind/scope association;
- freezes complete selected records, WorldRevision, and History digest;
- validates per-effect and aggregate Energy, Matter, and event capacity;
- creates an opaque, runtime-local, unique, single-use PreparedPlan.

The artifact never supplies the exact selected host record IDs. Nested record/sequence objects in a PreparedPlan do not alias the admitted artifact.

## 3. Revalidation

Immediately before COMMIT, the runtime rechecks:

- emergency-stop and commit fence;
- source WorldRevision;
- History digest;
- runtime profile;
- every resolved entity state revision;
- byte/structural equality of all frozen Capability, Lease, identity, evidence, and accounting records;
- aggregate current ledger capacity.

A later eligible entity is not silently included. Missing, ambiguous, stale, revoked, expired, or drifted evidence aborts before effects.

## 4. Registry-owned execution

Each registered contract executor receives only:

- the opaque PreparedPlan context;
- one prepared effect with frozen typed inputs and bound host records;
- the authoritative sandbox world through the host-owned execution boundary.

Runtime input signatures are exact. Structured contracts use signatures such as:

```text
record:EvidenceFusionModel
sequence:record:HypothesisScore
```

Untyped `object`, `array`, `any`, and `*` signatures are rejected by both semantic and runtime registration. A new reusable contract is added by semantic and runtime registration; the core interpreter is not edited.

The generic core validates returned output kind and exact emitted History count.

Initial contracts are:

- `generic.transition@1`: consumes a resolved reference and desired state; host code allocates the successor WorldRevision and emits one event;
- `generic.observe@1`: consumes a resolved reference; creates a non-truth, nonphysical evidence artifact and emits one event.

No artifact-authored WorldRevision is authoritative.

## 5. Atomic COMMIT

COMMIT executes effects in deterministic node order. Accounting is consumed only through bound host ledgers. Any executor exception, event mismatch, output mismatch, non-finite hash failure, or trace-validation failure restores every authoritative domain:

```text
Sigma, History, Omega, Process,
Capabilities, Leases, ledgers,
stop/fence state
```

A pure program performs no authoritative mutation.

PreparedPlans are single-use. Their opaque IDs may appear in traces but are cleared from committed process state.

## 6. Committed outputs

After all effects, the runtime verifies every declared output binding:

- `event` requires an event identity actually returned and appended;
- `artifact` requires an artifact identity actually created;
- `reference` requires a PREPARE-resolved reference;
- `evidence` and `effect_result` require the registered committed result kind;
- `value` retains the immutable scalar, quantity, record, sequence, or pure derived value.

The execution trace owns `results`; declarations alone do not create identities.

## 7. Replay and canonical hashes

Replay starts from a clone of the same initial state and re-executes the program through the same evaluator, PREPARE, registry, and COMMIT path.

Program, History, and complete-state hashes use finite canonical JSON:

- object keys sorted;
- sequence order preserved;
- `NaN` and infinities rejected.

Committed replay compares:

- complete authoritative state hash;
- History event order;
- effect results;
- committed output results.

Abort replay compares stable abort code and unchanged-state guarantees. Runtime profile mismatch or malformed trace is incompatible rather than silently repaired.

## 8. Occurrence identity

Event and artifact identities derive from program digest, frozen source revision, frozen History digest, node order, and contract identity. Therefore:

- record key permutation does not change program identity;
- sequence reordering changes program identity;
- the same initial state replays identically;
- a later execution after History changes receives distinct occurrence identities;
- wall-clock time, filesystem order, Python hash randomization, and filename are irrelevant.

## 9. Security boundary

The runtime admits no raw state path, arbitrary dynamic import, artifact-authored executable code, host-ceiling escalation, authority amplification, untyped structured wildcard, opaque legacy payload, or legacy-executor call inside the generic path.

Legacy spell executors may be invoked only by the external differential harness as frozen oracles during pre-public archive Issue #90.

## 10. Traceability

Runtime behavior is owned by:

- `src/runtime/magical_program_engine.py`;
- `src/runtime/magical_program_prepare.py`;
- `src/runtime/magical_program_commit.py`;
- `src/runtime/magical_program_binding.py`;
- `src/runtime/magical_program_contracts.py`;
- `src/runtime/magical_program_model.py`.

Tests:

- `tests/test_magical_program_runtime.py`;
- `tests/test_magical_program_runtime_extensions.py`;
- `tests/test_magical_program_runtime_dispatch.py`;
- `tests/test_magical_program_structured_values.py`;
- consolidated editable/wheel/sdist package smoke, including `MP-STRUCTURED-001.json`.
