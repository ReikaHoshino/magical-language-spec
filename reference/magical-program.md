# MagicalProgram Architecture — experimental planning contract

**Status:** experimental architecture owner for pre-public archive Issue #84 / pre-public archive Issue #85. This document does not change the stable v1.0 candidate surface, the four required conformance classes / 65 required cases, the six MKI data-plane primitives, the five lower World Kernel interaction classes, or historical `spec/` snapshots.

## Purpose

`MagicalProgram` provides one declarative program representation that can be used by repository-owned experimental spells and user-authored spells before they enter the common evaluator/runtime pipeline.

The user-facing objective is:

```text
repository spell ─┐
                  ├─> MagicalProgram
user spell ───────┘
                         ↓
              common semantic validation
                         ↓
              common planning / PREPARE
                         ↓
              common COMMIT / replay
```

A file name, suite name, scenario label, spell proper name, or fixture identity MUST NOT select executable behavior.

## Non-goals

- This document does not define the concrete `MagicalProgram-0` JSON Schema; pre-public archive Issue #87 owns that work.
- This document does not implement generic semantic validation, lowering, runtime interpretation, migration, source parsing, or CLI integration; pre-public archive Issues #88–pre-public archive Issue #94 own those steps.
- `MagicalProgram` is not a public stable serialized ECIR, `TypedMIR`, `KernelPlan`, or `PreparedPlan`.
- It does not add a seventh MKI primitive or a sixth lower World Kernel interaction class.
- It does not expose arbitrary `SET`, raw state-path mutation, host-language code execution, imports, plugins, network loading, or unrestricted filesystem loading.
- It does not allow syntax to create Identity, Capability, Lease, Truth, Energy, Matter, evidence freshness, ownership, or compatibility.
- It does not define new physical/model laws inside an artifact.

## Depends on

- `architecture.md`
- `scope-and-ownership.md`
- `semantics.md`
- `mki.md`
- `kernel-execution.md`
- `security-sandbox.md`
- `compatibility.md`
- `spell-instance-bundles.md`
- pre-public archive Issue #47 — source/artifact extension family
- pre-public archive Issue #48 — typed multi-stage ingress
- pre-public archive Issue #77 — Experimental-Arcana semantic ownership
- pre-public archive Issue #84 — parent roadmap

## Key invariants

```text
MagicalProgram != raw WorldState write access
MagicalProgram != SemanticAST
MagicalProgram != TypedMIR
MagicalProgram != KernelPlan
MagicalProgram != PreparedPlan
MagicalProgram instruction != MKI primitive
MagicalProgram contract reference != authority
Declared type != validated type
Declared resource != reserved resource
Declared identity != resolved identity
Confidence != truth
Evaluation != execution
Artifact code reference != executable host code
```

## 1. Architectural role

### Decision

`MagicalProgram` is a **public experimental, versioned declarative program artifact** and the canonical post-source lowering target for the future human-authored source frontend.

It is also usable directly by tools and by repository-owned experimental examples. It is not promoted into the stable v1.0 artifact promise by this decision.

```text
Human-authored source
  -> source parser / resolver / type-and-effect checker
  -> MagicalProgram

Direct structured authoring
  -> MagicalProgram

Current or future normalization path, where explicitly supported
  -> NSR
  -> program elaboration
  -> MagicalProgram

MagicalProgram
  -> deterministic semantic validation
  -> implementation-owned SemanticAST
  -> TypedMIR
  -> KernelPlan
  -> PREPARE / PreparedPlan
  -> COMMIT / replay
```

The current stable NSR evaluator path may continue to lower directly into its implementation-owned stages. Introducing `MagicalProgram` does not retroactively require every v1.0 NSR implementation to serialize or expose this artifact.

### Why this position

Placing `MagicalProgram` before `SemanticAST` preserves the existing separation:

- the program is authored or compiler-emitted input;
- its declared types, references, obligations, and contracts are untrusted until validated;
- `SemanticAST`, `TypedMIR`, `KernelPlan`, and `PreparedPlan` remain implementation-owned semantic/planning/runtime stages;
- direct program input skips only source parsing or normalization, never downstream obligations.

## 2. Stage ownership and stability

| Stage | Owner | Serialization / stability in this roadmap | May skip downstream checks? |
|---|---|---|---|
| Human source | pre-public archive Issue #92 / source frontend; coordinated with pre-public archive Issue #47 | future experimental source contract | No |
| NSR | current reference owners | current stable/defined surface where already promised | No |
| `MagicalProgram` | this document + pre-public archive Issue #87 | public experimental artifact | No |
| SemanticAST | evaluator implementation/reference | implementation-owned unless separately promoted | No |
| TypedMIR | evaluator implementation/reference | implementation-owned unless separately promoted | No |
| KernelPlan | planner/runtime implementation/reference | profile/revision-bound; no new public stable ECIR here | No |
| PreparedPlan | runtime PREPARE boundary | runtime-only, current-state-bound | No |
| WorldState / History result | World + runtime contracts | authoritative committed state/events | N/A |

Entering at `MagicalProgram` skips only prior source-language or normalization transformations that were not supplied. It MUST NOT fabricate missing source provenance.

## 3. Structural form

### Decision

`MagicalProgram-0` uses a **finite directed acyclic graph**. A straight-line program is the special case in which every node depends on the preceding node.

The concrete schema is deferred to pre-public archive Issue #87, but the following architecture is fixed:

- every node has a stable explicit identity;
- dependency edges are explicit;
- cycles are rejected before evaluation;
- evaluation order is a deterministic topological order;
- where multiple nodes are ready, their explicit order in the serialized node list is the normative tie-break unless pre-public archive Issue #87 defines an equivalently deterministic rule;
- all bindings have one declared producer;
- no implicit mutable global variable exists;
- host ceilings bound nodes, edges, values, bytes, depth, effects, events, Energy, microsteps, and concurrency.

Unbounded loops, recursion, dynamic node creation, runtime code generation, and self-modifying programs are outside `MagicalProgram-0`.

## 4. Value and binding model

The program representation has explicit values and handles, including at least these architectural categories:

```text
LiteralValue
TypedQuantity
EntitySelector / unresolved reference request
ResolvedRef handle
Evidence handle
Pure computed value
Contract invocation result handle
Declared program result
```

A declaration is not proof:

```text
declared EntityID != authoritative resolution
declared CapabilityID != current authority
declared Energy amount != available or reserved Energy
declared type/dimension != validated type/dimension
```

Bindings are immutable within one admitted program snapshot. World mutation occurs only through committed registered effect contracts, not by assigning to a binding.

## 5. Instruction taxonomy

Exact serialized instruction names belong to pre-public archive Issue #87. The architecture recognizes four semantic classes.

### 5.1 Resolution and evidence-read requests

Examples:

- resolve a selector/reference against the admitted WorldIndex/World boundary;
- query committed History or an evidence store;
- request a new observation/sample through an admitted observer contract.

These instructions do not grant authority merely by returning data. Observation privacy, freshness, identity, Capability, and Lease requirements remain mandatory.

### 5.2 Pure computation

Examples:

- arithmetic with validated units/dimensions;
- comparison and bounded selection;
- deterministic sorting/ranking;
- construction of a non-authoritative proposal or intermediate value;
- assertions over already validated inputs.

Pure computation MUST NOT mutate WorldState, History, ledgers, controllers, artifacts, or runtime process state.

### 5.3 Effect requests through registered contracts

Examples:

- bounded transfer;
- bounded reconfiguration;
- channel/controller activation;
- constraint application;
- committed observation artifact publication;
- domain-specific admitted transition/effect invocation.

Every effectful node references a versioned, host-owned semantic/transition/effect contract. The registration owns validation, obligation synthesis, MKI lowering, runtime realization, and any required physical/model semantics.

The artifact may select and parameterize an admitted contract. It may not define executable host behavior or governing physical/model law.

### 5.4 Result declarations

A program may declare which validated values, committed artifacts, or committed event identities are returned as program results.

A program cannot independently forge History by emitting an arbitrary committed event. Event and artifact identities that claim committed effects must be produced by the corresponding committed contract and verified against the declared result contract.

## 6. Relationship to MKI and the World Kernel

`MagicalProgram` instructions are not new MKI primitives.

Effect registrations map admitted program nodes to the existing MKI data plane:

```text
RESOLVE / OBSERVE / CHANNEL / TRANSFER / RECONFIGURE / CONSTRAIN
```

and, where applicable, to the existing lower interaction classes:

```text
QUERY / SAMPLE / TRANSITION / ACTIVATE / DEACTIVATE
```

Pure computation, graph scheduling, assertion evaluation, registry lookup, inference, rendering, source mapping, compiler activity, and result comparison do not become MKI primitives.

A registration MUST document its lowering and MUST preserve identity, authority, Lease, conservation/accounting, timing, provenance, and sandbox obligations. Lowering cannot convert an unvalidated program node into raw WorldState access.

## 7. Registry and implementation boundary

### Artifact-owned data

The program artifact may contain:

- contract IDs and revisions;
- typed parameters and declared bindings;
- explicit dependencies;
- required evidence/resource/authority declarations;
- compatibility and provenance metadata;
- bounded declarative registry-extension records in admitted namespaces, where separately allowed.

### Host-owned executable behavior

Only host registration may provide:

- semantic validators and elaborators;
- transition/effect model implementations;
- runtime executors or generic runtime model hooks;
- obligation synthesis rules;
- MKI/lower-interaction mappings;
- trusted schema/contract registration.

```text
artifact contract reference
  != executable import
  != Python module path
  != plugin installation
```

A user can create a new spell by composing admitted contracts without changing Python. A genuinely new physical, biological, evidential, controller, rendering, or semantic model still requires a separately reviewed host-owned contract implementation.

## 8. Pure, observable, and effectful boundaries

| Class | Reads authoritative/evidence state | Mutates authoritative state | Requires PREPARE/COMMIT |
|---|---:|---:|---:|
| Literal/binding construction | No | No | No |
| Pure computation | No, except supplied immutable values | No | No |
| Resolution/query | Yes | No | requires admission/freshness checks; not COMMIT by itself |
| New physical observation/sample | Yes | may consume resources and produce committed evidence according to contract | Yes where contract requires |
| Effect request | Yes | Yes when committed | Yes |
| Result declaration | No new read beyond handles | No independent mutation | verified after execution |

An implementation may optimize pure nodes, but optimization MUST preserve deterministic semantics and diagnostics.

## 9. Admission, compatibility, provenance, and identity

A serialized program carries an authoritative in-document artifact kind and version. File extensions are hints only and remain coordinated with pre-public archive Issue #47.

Admission must include, as applicable:

- strict bounded decoding;
- artifact schema/version validation;
- compatibility aggregation without treating a hash as universal compatibility;
- profile and registry revision admission;
- instruction/contract registration resolution;
- graph/binding validation;
- type/dimension validation;
- reference/evidence declaration validation;
- host ceiling enforcement;
- security/path/external-resource rejection.

`MagicalProgram` provenance records what was actually supplied or produced. Direct program input does not invent a source sentence, source AST, adapter, or source-language fidelity claim.

`SemanticFingerprint` remains distinct from artifact content hashing. Exact canonical-byte, content-digest, and semantic-projection algorithms for `MagicalProgram-0` are owned by pre-public archive Issue #87 / compatibility work and are not silently inferred from the current NSR fingerprint.

## 10. Error ownership and fail-closed matrix

| Failure | Owning stage | Required behavior |
|---|---|---|
| malformed/unknown artifact kind or version | ingress | reject before semantic evaluation |
| cycle, duplicate node/binding, invalid dependency | program validation | reject deterministically |
| unknown instruction or contract | registry/program validation | fail closed; no fallback by name or fixture |
| type/dimension mismatch | semantic validation | infeasible/rejected according to owned diagnostic contract |
| unresolved or stale identity/evidence | resolver/PREPARE/revalidation | fail closed; no silent retarget |
| missing/revoked Capability or Lease | PREPARE/COMMIT revalidation | deterministic abort; no partial commit |
| insufficient Energy/Matter/accounting proof | planning/PREPARE/COMMIT | fail closed; no invented resource |
| sandbox/host ceiling exceeded | admission/PREPARE/runtime | deterministic rejection/abort |
| effect implementation absent | registry/support-level boundary | recognized unsupported or deterministic unknown-contract failure; never successful no-op |
| replay mismatch | replay verifier | explicit divergence/failure |
| expected/golden mismatch | independent conformance owner (pre-public archive Issue #86) | field-level parity failure |

## 11. Common-path requirement

After admission/lowering into `MagicalProgram`, repository-owned experimental spells and external user programs use the same post-lowering components:

```text
program validator
semantic/type/effect validator
registry resolution
planner
PREPARE
COMMIT runtime
sandbox
replay verifier
independent result comparator
```

No component in this common path may branch on:

```text
SA-*
SUCCESS-ARCANA-*
fixture ID
suite ID
file path
spell display/proper name
```

Domain-specific registered contracts may exist, but they are reusable model/effect contracts, not fixture dispatch.

## 12. Migration and rollback

Migration from current dedicated experimental executors proceeds only through pre-public archive Issue #86, pre-public archive Issue #90, and pre-public archive Issue #91.

### Shadow phase

- freeze existing dedicated executors as differential oracles;
- run legacy and generic paths from the same immutable admitted input and cloned initial state;
- compare evaluation, diagnostics, selected identities/revisions, obligations, MKI/lower records, WorldRevision, final state, accounting, History EventIDs/order, artifacts/controllers/process state, abort atomicity, and replay;
- use expectations owned independently from executable input.

### Cutover phase

- cut over only after exact declared parity or an explicitly approved semantic migration;
- switch production registration to the generic program path;
- retain reusable domain effect contracts;
- remove fixture-specific orchestration from production registration;
- keep legacy code only as isolated historical/test support if still needed.

### Rollback rule

Before legacy production paths are deleted, each cutover PR must identify an exact pre-cutover commit and a registration-level rollback procedure. Dual execution may be used for comparison, but only one path may authoritatively COMMIT in a given run.

## 13. Source-language frontend relationship

pre-public archive Issue #92 defines the source language; pre-public archive Issue #93 implements its compiler.

The source frontend MUST compile into the same `MagicalProgram` contract used by direct structured authoring and migrated SA programs.

```text
source syntax
  -> source AST
  -> name/contract resolution
  -> source type/effect checks
  -> MagicalProgram
  -> normal program admission and downstream validation
```

Compiler success does not waive program admission, PREPARE/COMMIT revalidation, sandboxing, or replay. Source syntax cannot grant authority or define host executable models.

## 14. Release and compatibility placement

This architecture is post-v1.0 experimental work unless a separate release-scope decision promotes it.

If implementation is proposed before v1.0 final and materially changes the frozen stable surface, the project MUST decide whether to exit RC and return to a stabilization release. It must not force the redesign into the RC without resetting the applicable release gates.

Initial artifacts, schemas, commands, and diagnostics introduced by pre-public archive Issue #87–pre-public archive Issue #94 must be explicitly classified as experimental or stable under the normal compatibility process. Historical `spec/` snapshots remain immutable.

## 15. Child issue dependency map

```text
pre-public archive Issue #85 architecture
 ├─> pre-public archive Issue #87 program artifact
 │    ├─> pre-public archive Issue #88 semantic validation/lowering
 │    │    └─> pre-public archive Issue #89 runtime/replay
 │    └─> pre-public archive Issue #92 source-language contract
 └─> pre-public archive Issue #86 independent golden/parity

pre-public archive Issue #86 + pre-public archive Issue #87 + pre-public archive Issue #88 + pre-public archive Issue #89
 └─> pre-public archive Issue #90 shadow migration
      └─> pre-public archive Issue #91 cutover

pre-public archive Issue #87 + pre-public archive Issue #88 + pre-public archive Issue #92
 └─> pre-public archive Issue #93 compiler

pre-public archive Issue #91 + pre-public archive Issue #93
 └─> pre-public archive Issue #94 CLI/docs/package/conformance integration
```

## 16. Architecture acceptance checklist

- [x] `MagicalProgram` role and stability are explicit.
- [x] Relationship to NSR, SemanticAST, TypedMIR, KernelPlan, and PreparedPlan is explicit.
- [x] DAG structure and deterministic ordering boundary are selected.
- [x] Value/reference and immutable binding boundary is defined.
- [x] Program instructions are separated from MKI and lower interactions.
- [x] Pure, read/observation, effect, and result instruction classes are separated.
- [x] Host-owned transition/effect contract boundary is explicit.
- [x] Admission, provenance, compatibility, and fingerprint ownership are assigned or explicitly deferred.
- [x] Migration, parity, cutover, and rollback rules are defined.
- [x] pre-public archive Issue #47, pre-public archive Issue #48, and pre-public archive Issue #77 coordination points are recorded.
- [x] Stable v1.0 candidate surface and release-train boundary are preserved.
