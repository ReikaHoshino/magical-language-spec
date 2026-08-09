# MagicalProgram-0 Artifact Contract

**Status:** experimental normative owner after the Issue #110 architecture correction and Issue #114 structured-value extension.

**Stable v1.0 impact:** none. The released package and required four-class / 65-case conformance surface remain `0.12.0`.

## 1. Boundary

`MagicalProgram-0` is a portable, declarative, untrusted artifact. It is accepted before implementation-owned SemanticAST, TypedMIR, KernelPlan, and the runtime-local PreparedPlan.

```text
program text != authoritative identity
portable requirement != Capability or Lease
reference hint != resolved Ref
structured data != executable payload
schema acceptance != compatibility
compatibility != authority
output declaration != committed result
```

The artifact may describe data, computation, resolution, and authorization requirements. It cannot contain a host-owned Capability, Lease, identity-evidence, accounting-ledger, reservation, PreparedPlan, executable code, or opaque serialized legacy artifact.

## 2. Closed envelope

The root is a closed JSON object containing:

- `artifact_kind = MagicalProgram`;
- `artifact_version = 0`;
- `contract = magical-program@0`;
- `stability = experimental`;
- `program_id`;
- direct or lowered provenance;
- exact registry/profile compatibility binding;
- bounded execution budget;
- values, nodes, explicit edges, and outputs.

Unknown fields and unknown instruction names fail closed.

## 3. Values and resolution

Revision 0 admits top-level bindings of these kinds:

- scalar `literal`;
- dimensioned `quantity`;
- typed `record`;
- typed ordered `sequence`;
- `selector`;
- untrusted `reference_hint` / `evidence_hint`.

A selector or hint becomes authoritative only through `ref.resolve` at PREPARE. The node produces a typed reference request during evaluation and an exact entity/revision binding during PREPARE. A missing, ambiguous, or stale request aborts before COMMIT.

Downstream effect nodes consume the resolved-reference binding. They do not silently rerun the selector or retarget a later eligible entity.

### 3.1 Typed record

A record contains:

```text
kind = record
type_id = exact semantic record identity
fields = closed-name map of anonymous structured values
```

Its registry signature is `record:<type_id>`. Field order in JSON is not semantic; canonical serialization sorts object keys. A nested field has no `value_id` and therefore cannot create another graph binding.

### 3.2 Typed sequence

A sequence contains:

```text
kind = sequence
element_type = exact element signature
items = ordered anonymous structured values
```

Its registry signature is `sequence:<element_type>`. Every item must have exactly the declared signature. Sequence order is semantic and is preserved by canonical serialization, evaluation, PREPARE, COMMIT, and replay.

Anonymous structured values may be literals, quantities, records, or sequences. Selectors, reference/evidence hints, graph bindings, requirements, and executable contract references are not admitted inside structured values.

### 3.3 Exact signatures

Examples:

```text
record:EvidenceFusionModel
record:HypothesisScore
sequence:record:HypothesisScore
sequence:literal:string
```

A contract registration must name exact signatures. Untyped wildcards such as `object`, `array`, `any`, and `*` are prohibited.

### 3.4 Structured host ceilings

Admission enforces immutable host ceilings for:

- encoded program bytes;
- structured nesting depth;
- fields per record;
- items per sequence;
- aggregate nested fields/items across the program.

All numbers must be finite. `NaN`, positive/negative infinity, duplicate JSON properties, heterogeneous sequences, and excessive structures fail before PREPARE.

## 4. Portable requirements

Every effect or observation node carries a closed `obligations` object. Its entries are **portable requirement objects**, not concrete host record IDs.

- Capability requirement: local requirement ID, target binding, required effect, optional scope.
- Lease requirement: local requirement ID, target binding, required mode, optional scope.
- Identity requirement: local requirement ID and target binding.
- Evidence requirement: local requirement ID, target binding, and evidence kind.
- Accounting requirement: local requirement ID, accounting kind, and optional target binding.
- Resource requirement: Energy, Matter, and event upper bounds.

Every target binding must be an input of the owning node and must evaluate to a resolved reference. Requirement IDs are local program names and must be unique within the node.

Exact Capability, Lease, identity, evidence, and accounting IDs appear only in the runtime-local PreparedPlan after authoritative PREPARE binding.

## 5. Instructions and graph

Revision 0 admits:

- `ref.resolve`;
- `evidence.observe`;
- `pure.calculate`;
- `pure.compare`;
- `pure.rank`;
- `assert.require`;
- `effect.invoke`.

Nodes have unique IDs and deterministic integer order. Bindings have one producer. Data dependencies require explicit forward edges. The graph is acyclic and bounded by immutable host ceilings.

Structured values are immutable declarative inputs. Revision 0 admits equality/inequality comparison for exact matching structured signatures, but no arithmetic or ordering over records/sequences.

No raw state path, arbitrary `SET`, dynamic import, recursion, unbounded loop, network/filesystem primitive, or artifact-authored executable code exists.

## 6. Outputs

An output names an existing binding and declares one of:

- `value`;
- `reference`;
- `evidence`;
- `effect_result`;
- `event`;
- `artifact`.

`value` includes scalar, quantity, record, sequence, and pure ranked-sequence bindings. Evaluation checks type compatibility. COMMIT checks that declared event and artifact outputs correspond to identities actually appended or created by the registered runtime contract. An artifact cannot forge a committed result by declaring its name.

## 7. Admission sequence

```text
strict UTF-8, finite-number, and duplicate-key rejection
  -> canonical byte ceiling
  -> JSON Schema validation
  -> graph and execution host ceilings
  -> structured depth/field/item/homogeneity ceilings
  -> registered contract-pair admission
  -> node/order/edge/DAG validation
  -> binding producer and data-edge validation
  -> portable requirement target validation
  -> output binding validation
```

Admission performs no semantic evaluation, resolution, authority lookup, reservation, or mutation.

## 8. Security invariant

Opaque legacy tunnelling is prohibited. A MagicalProgram must not contain a complete legacy SpellInstanceBundle, contract parameter record, or arbitrary object encoded as JSON/base64 text merely to bypass typing. Complex data must use the closed record/sequence contract.

The generic path must not call a legacy executor as its implementation. Legacy executors may participate only as frozen external differential oracles during migration.

## 9. Traceability

The contract is exercised by:

- `tests/test_magical_program_contract.py`;
- `tests/test_magical_program_evaluator.py`;
- `tests/test_magical_program_runtime.py`;
- `tests/test_magical_program_runtime_extensions.py`;
- `tests/test_magical_program_structured_values.py`;
- `examples/magical-program/MP-001.json`;
- `examples/magical-program/MP-OBSERVE-001.json`;
- `examples/magical-program/MP-PURE-001.json`;
- `examples/magical-program/MP-STRUCTURED-001.json`.

The historical `spec/` snapshots remain immutable. This file owns the current experimental contract.
