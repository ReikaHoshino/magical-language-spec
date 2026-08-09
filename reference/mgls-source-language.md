# Magical Language Source — MGLS-0

**Status:** experimental normative source-language contract for Issue #92.

**Stable v1.0 impact:** none. This contract does not change package version
`0.12.0`, the four required conformance classes / 65 required cases, the six
MKI data-plane operations, the five lower World Kernel interaction classes, or
historical `spec/` snapshots.

## Purpose

MGLS-0 defines a bounded, readable source notation whose only compilation
target is `MagicalProgram-0`.

```text
strict UTF-8 .mgls source
  -> SourceTextNormalizerV1
  -> MGLS-0 lexer / parser
  -> source name, type, effect, and obligation checks
  -> deterministic MagicalProgram-0 emission
  -> ordinary program admission
  -> evaluator / PREPARE / COMMIT / replay
```

MGLS is a frontend. It does not define a second evaluator, runtime, physical
model, authority system, or WorldState mutation interface.

## Non-goals

MGLS-0 does not provide:

- loops, recursion, branching, pattern matching, exceptions, async, or dynamic
  node creation;
- modules, imports, includes, macros, reflection, metaprogramming, plugins, or
  source-defined host code;
- arbitrary state-path access or generic `SET`;
- implicit LanguageAdapter selection or natural-language interpretation;
- implicit Identity, Capability, Lease, evidence truth, resource acquisition,
  accounting capacity, compatibility, or trust;
- a public SemanticAST, TypedMIR, KernelPlan, or PreparedPlan format;
- contract selection by filename, source ID, program ID, spell name, fixture,
  suite, or scenario.

## Depends on

- `conventions.md`
- `file-naming.md`
- `source-text-normalization.md`
- `multi-stage-ingress.md`
- `compatibility.md`
- `errors.md`
- `magical-program.md`
- `magical-program-artifact.md`
- `magical-program-evaluator.md`
- `magical-program-runtime.md`
- [`grammar/mgls.ebnf`](../grammar/mgls.ebnf)
- [`schemas/magical-program.schema.json`](../schemas/magical-program.schema.json)

## Key invariants

```text
source text != authority
source name != host identity
source type annotation != validated type
source requirement != Capability / Lease / evidence / reservation
compiler success != program admission
program admission != PREPARE success
PREPARE success != COMMIT permission
output name != committed EventID / ArtifactID
source order != hidden mutable state
filename != source contract
.mgls != natural-language adapter input
```

---

## 1. Contract identity and file boundary

The canonical filename suffix is `.mgls`. The suffix selects the source decoder
only; it is advisory and does not override the in-document source version.

MGLS-0 source begins with the following six declarations in exact order:

```mgls
mgls "0";
source "source:example:001";
program "program:example:001";
registry "registry:reference-experimental" revision "1";
profile "profile:reference-experimental" revision "1";
budget {
  energy 10;
  events 1;
  microsteps 8;
  concurrency 1;
}
```

The authoritative source contract is:

```text
contract_id = mgls-source
revision    = 0
stability   = experimental
```

The first declaration MUST contain exactly `"0"`. An unknown source revision is
not interpreted as the latest known revision and fails with
`SpecVersionIncompatible`.

`source` and `program` strings MUST satisfy the `MagicalProgram-0` identifier
syntax. The compiler emits:

```json
{
  "provenance": {
    "relation": "lowered",
    "input_stage": "program",
    "source": {
      "artifact_kind": "MagicalSource",
      "artifact_version": "0",
      "artifact_id": "<source declaration>",
      "stage": "source"
    }
  }
}
```

The source file itself is text, not a structured artifact envelope. The header
is the authoritative source-language/version declaration required by
`file-naming.md` and `multi-stage-ingress.md`.

### 1.1 Media type

The project-facing media type is reserved as:

```text
text/vnd.magical-language.source; version=0; charset=utf-8
```

This reservation is experimental and is not an IANA registration. A transport
media type and a `.mgls` suffix MUST agree with the decoded header when both are
available.

---

## 2. Encoding, normalization, whitespace, and comments

Input MUST pass `SourceTextNormalizerV1` before tokenization:

1. strict UTF-8 decoding;
2. byte-boundary BOM handling;
3. CRLF/CR to LF conversion;
4. line-body NFC normalization;
5. normalized-to-original source mapping.

MGLS does not add NFKC, case folding, width folding, punctuation substitution,
whitespace collapsing, transliteration, or language detection.

Outside strings, whitespace and comments are lexical separators. Comments are:

```mgls
// line comment
/* non-nesting block comment */
```

A block comment MUST NOT nest. An unterminated comment is `ParseError`.
Comments do not affect generated program semantics or IDs.

Strings use JSON-compatible escaping. After escape decoding, the result MUST be
a Unicode scalar sequence and MUST NOT contain U+0000 or an unpaired surrogate.
String interpolation does not exist.

Keywords are ASCII lowercase and case-sensitive. Source bindings and node names
are ASCII identifiers matching:

```text
[A-Za-z_][A-Za-z0-9_]*
```

Contract IDs, revisions, requirement IDs, source/program IDs, effects, modes,
kinds, scopes, and output names are quoted strings. Their target schema syntax
is validated after decoding.

---

## 3. Namespaces, scopes, and ordering

MGLS-0 has one source-file scope and four disjoint namespaces:

1. value/binding names;
2. node names;
3. output names;
4. header identities.

A name may not be declared twice in the same namespace. Duplicate value or node
producers are `DuplicateBinding`; duplicate output names are also reported as
`DuplicateBinding` with namespace evidence.

There are no nested lexical scopes. All value declarations precede all nodes;
all nodes precede all outputs. Forward reference rules are:

- a node may consume a top-level value declared earlier;
- a node may consume a binding produced by an earlier node only;
- an `after` clause may name earlier nodes only;
- an output may name any valid top-level value or produced binding;
- no other forward reference is accepted.

Unknown names are `UnresolvedName`. The compiler does not search the filesystem,
environment variables, package imports, fixture manifests, or spell names.

Textual node order is normative. The first node emits `order = 0`, the next
`order = 1`, and so on. Reformatting and comments do not change order.

---

## 4. Header lowering

The header lowers as follows:

| MGLS declaration | `MagicalProgram-0` field |
|---|---|
| `mgls "0"` | validates source contract; no author-controlled program field |
| `source "S"` | lowered provenance source `artifact_id = S` |
| `program "P"` | `program_id = P` |
| `registry "R" revision "r"` | `compatibility.registry_id/revision` |
| `profile "P" revision "p"` | `compatibility.profile_id/revision` |
| budget `energy` | `budget.energy_j` |
| budget `events` | `budget.events` |
| budget `microsteps` | `budget.microsteps` |
| budget `concurrency` | `budget.concurrency` |

The compiler emits fixed fields:

```json
{
  "artifact_kind": "MagicalProgram",
  "artifact_version": "0",
  "contract": {"contract_id": "magical-program", "revision": "0"},
  "stability": "experimental"
}
```

The source cannot override these values.

Registry/profile strings are declarations for compatibility admission, not a
request to download or load code. `Compatible` remains distinct from authority.

---

## 5. Values and types

### 5.1 Scalar types

MGLS scalar types are:

```text
bool
int
number
string
null
```

`int` accepts a JSON integer token. `number` accepts a finite JSON number token.
An integer is assignable to `number`; no other implicit scalar conversion
exists. `NaN`, infinity, hexadecimal numbers, digit separators, and locale
number syntax are rejected.

Top-level examples:

```mgls
let enabled: bool = true;
let count: int = 3;
let ratio: number = 0.25;
let state: string = "transitioned";
let absent: null = null;
```

Each declaration emits one `values[]` entry with `kind = literal`.

### 5.2 Quantities

A quantity type declares all target artifact metadata explicitly:

```mgls
let energy: quantity<Energy, Energy, J> = quantity(10);
```

The three type arguments are:

```text
semantic_type, dimension, unit
```

The compiler emits `kind = quantity` and copies these exact identities. It does
not infer dimensions or unit conversions from a spelling. Registry-backed
semantic/type checking must confirm that the tuple is admitted.

Arithmetic requires compatible validated quantity signatures. The compiler does
not silently convert units or treat equal dimensions as equal semantic types.

### 5.3 Records

A record type is exact:

```mgls
let policy: record<TransitionPolicy> = record<TransitionPolicy> {
  mode: string = "bounded";
  threshold: quantity<Energy, Energy, J> = quantity(10);
};
```

The declared `record<T>` and constructor `record<T>` MUST match. Field names are
closed after contract resolution, unique, and emitted as the record `fields`
map. Source field order is not semantic; canonical program serialization owns
object-key ordering.

Nested record/sequence/literal/quantity values are anonymous structured values.
They do not create graph bindings, references, requirements, or executable
payloads.

### 5.4 Sequences

A sequence declares one exact element signature:

```mgls
let scores: sequence<record<HypothesisScore>> =
  sequence<record<HypothesisScore>> [
    record<HypothesisScore> {
      hypothesis: string = "A";
      score: number = 0.9;
    },
    record<HypothesisScore> {
      hypothesis: string = "B";
      score: number = 0.1;
    },
  ];
```

Declared and constructor element signatures MUST match. Every item MUST have the
same exact signature. Sequence order is semantic.

### 5.5 Selectors and hints

Selectors contain one to sixteen scalar entries:

```mgls
selector target_selector = {
  entity_type = "test-target",
  scope = "local",
};
```

They emit `kind = selector`. Selector fields are untrusted request data and do
not become a reference until a `resolve` node succeeds during PREPARE.

Hints are explicit and untrusted:

```mgls
reference_hint old_ref = "entity:known" revision "state:7";
evidence_hint old_snapshot = "evidence:known" revision "event:4";
```

They emit `reference_hint` or `evidence_hint`. A hint cannot be consumed as an
authoritative resolved reference by an effect unless the downstream contract
explicitly admits and revalidates it. Source text never makes a hint current.

---

## 6. Node forms and deterministic graph lowering

Each node declaration has an explicit source node name:

```mgls
node resolve_target: resolve target_ref from target_selector;
```

The source name becomes `node_id`. Textual position becomes integer `order`.
The node body determines `instruction`, ordered `inputs`, ordered `produces`,
and instruction-specific fields.

### 6.1 Edges

The compiler emits an edge from node A to node B when:

1. B consumes a binding produced by A; or
2. B has `after A` explicitly.

Duplicate edges collapse to one pair. Emitted edges are sorted by target node
order, then source node order. An `after` edge is an ordering dependency only;
it cannot fabricate a data input.

All edges point forward. Cycles, self-edges, and references to later nodes fail
before program emission.

### 6.2 Resolve

```mgls
node resolve_target: resolve target_ref from target_selector;
```

Lowering:

```text
instruction = ref.resolve
inputs      = [target_selector]
produces    = [target_ref]
```

The compiler only creates the request. Exact resolution, freshness, identity,
and retargeting policy remain PREPARE-owned.

### 6.3 Pure calculation

```mgls
node total: calculate total_energy = add(base_energy, extra_energy);
```

`calculate` operators map exactly to:

```text
add subtract multiply divide minimum maximum
```

The source checker validates arity and a unique result signature using admitted
operator/type rules. Pure calculation cannot read WorldState or mutate state.

### 6.4 Comparison

```mgls
node enough: compare is_enough = greater(total_energy, threshold);
```

Operators map exactly to:

```text
equal not_equal less less_equal greater greater_equal
```

The result binding is `bool`. Structured records/sequences support only
`equal`/`not_equal` with exact matching signatures.

### 6.5 Ranking

```mgls
node order_scores: rank ranked_scores = descending(scores);
```

The sole input must be an admitted ordered sequence. The output preserves the
same sequence signature. Ranking tie-breaking is contract/profile-defined and
must be deterministic; source order is the final tie-break only when the owning
registered rule says so.

### 6.6 Assertion

```mgls
node budget_guard: require is_enough else "InsufficientBudget";
```

Lowering:

```text
instruction     = assert.require
inputs          = [is_enough]
produces        = []
diagnostic_code = InsufficientBudget
```

The input must be `bool`. The diagnostic string must be an admitted diagnostic
identity; it cannot contain code or format interpolation.

### 6.7 Observation

```mgls
node observe_subject: observe observation = invoke
  "evidence.observe" revision "1" (subject_ref, model)
  requires {
    capability "capability.observe" on subject_ref effect "Observe";
    identity "identity.subject" on subject_ref;
    evidence "evidence.subject" on subject_ref kind "IdentitySnapshot";
    accounting "accounting.observe" kind "Energy" on subject_ref;
    resources { energy 5; matter 0; events 1; }
  };
```

Lowering uses `instruction = evidence.observe`. The referenced host contract
owns semantic validation, observation behavior, evidence freshness/privacy,
MKI lowering, resource use, and runtime realization.

### 6.8 Effect invocation

```mgls
node invoke_transition after resolve_target: effect transition_result = invoke
  "generic.transition" revision "1" (target_ref, desired_state)
  requires {
    capability "capability.transition" on target_ref effect "Reconfigure";
    lease "lease.transition" on target_ref mode "Write";
    identity "identity.target" on target_ref;
    accounting "accounting.transition" kind "EnergyMatter" on target_ref;
    resources { energy 10; matter 0; events 1; }
  };
```

Lowering uses `instruction = effect.invoke`. The source may select and
parameterize an already admitted contract. It cannot define executable behavior,
physical law, raw MKI operations, or a runtime executor.

Every observation/effect node produces exactly one binding in MGLS-0, matching
the target artifact contract.

---

## 7. Obligations

Every `observe` or `effect` node has exactly one `requires` block and exactly
one `resources` declaration. Missing requirements are not inferred as granted.

Requirement forms map one-to-one:

| MGLS form | target artifact array |
|---|---|
| `capability ID on B effect E [scope S]` | `obligations.capabilities[]` |
| `lease ID on B mode M [scope S]` | `obligations.leases[]` |
| `identity ID on B` | `obligations.identities[]` |
| `evidence ID on B kind K` | `obligations.evidence[]` |
| `accounting ID kind K [on B]` | `obligations.accounting[]` |
| `resources { ... }` | `obligations.resources` |

Requirement IDs MUST be unique within the owning node across all requirement
categories. Every `on` binding MUST occur in the node input list and MUST have a
resolved-reference signature where the target program contract requires it.

The compiler verifies declared obligations against the registered contract's
required static shape. It MAY report additional inferred obligations for
diagnostics, but it MUST NOT silently add them to make source succeed. The
author must amend the source.

```text
declared requirement != satisfied requirement
compiler-verified shape != current authority
```

PREPARE binds exact host Capability, Lease, identity evidence, accounting record,
and resource reservations. COMMIT revalidates them.

Resource numbers are finite and non-negative. `matter` is kilograms and lowers
to `matter_kg`; `energy` is joules and lowers to `energy_j`. No unit conversion
syntax exists in MGLS-0 obligation blocks.

---

## 8. Outputs

Outputs are declarations after all nodes:

```mgls
output "result" effect_result from transition_result;
output "event" event from transition_result;
```

Kinds map exactly to:

```text
value reference evidence effect_result event artifact
```

The output name is copied to `outputs[].name`; the source binding is copied to
`outputs[].binding`. Output names are unique.

Static checking verifies that the binding's source category can support the
kind. Runtime checking remains mandatory for `event` and `artifact`: a declared
output name cannot forge a committed identity or History record.

---

## 9. Type, effect, and contract checking

The source checker runs after parsing and before emission:

1. header/version validation;
2. namespace and declaration-order validation;
3. exact registry/profile compatibility lookup;
4. value and structured-value type validation;
5. node arity and input signature validation;
6. contract lookup by exact `(contract_id, revision)`;
7. contract parameter/output signature validation;
8. obligation completeness and target validation;
9. effect classification validation;
10. output kind validation;
11. graph/edge/order validation;
12. target host-ceiling preflight;
13. deterministic program emission;
14. ordinary `MagicalProgram-0` admission as an independent final check.

Bounded local inference is permitted only for node-produced bindings when the
instruction and exact input/contract signatures yield one unique output
signature. Top-level values, quantities, records, sequences, contracts,
revisions, obligations, and output kinds remain explicit.

An ambiguous or absent signature fails closed. The compiler does not choose the
first registry match, newest revision, same spelling, or nearest type.

---

## 10. Diagnostics and recovery boundary

MGLS-0 reuses the existing error taxonomy; it does not create a parallel family.
The stable mapping is:

| Condition | Diagnostic |
|---|---|
| malformed/missing header | `StructuredInputInvalid` |
| unsupported source revision | `SpecVersionIncompatible` |
| strict UTF-8 / scalar / source character failure | `InvalidUTF8`, `InvalidUnicodeScalar`, `UnsupportedSourceCharacter` |
| invalid token, string, comment, or grammar | `ParseError` |
| duplicate value/node/output name or producer | `DuplicateBinding` |
| unresolved value/node/binding name | `UnresolvedName` |
| unknown/incompatible contract or registry revision | `RegistryMismatch` or `CompatibilityUndetermined` as owned |
| scalar/record/sequence/signature mismatch | `TypeError` |
| quantity semantic/dimension/unit mismatch | `DimensionError` |
| instruction/contract/effect/output mismatch | `EffectMismatch` or `ReturnTypeError` |
| missing static authority declaration | `StaticAuthorityError` |
| missing/invalid accounting or resource declaration | `ConservationProofFailure` |
| cycle or non-forward dependency | `CausalityCycleError` |
| forbidden import/loop/recursion/reflection/state path/code | `UnsupportedSemanticExtension` |
| source/token/declaration/output-target ceiling | `InputLimitExceeded` |
| emitted program differs from normative lowering | `SourceSemanticDrift` |
| emitted program fails target schema/admission | `StructuredInputInvalid` with target diagnostic evidence |
| source-map generation cannot represent a required mapping | `NormalizationFailed` |

A diagnostic MUST carry normalized-source scalar span `[start,end)`. When the
normalizer can map it to original source, the diagnostic also carries the
original span and `exact` flag.

Recovery MAY continue after a statement terminator or closing brace solely to
produce more diagnostics. Recovery MUST NOT:

- invent a declaration, token, type, contract, obligation, or delimiter;
- emit a partial `MagicalProgram`;
- reorder source nodes;
- downgrade a fatal diagnostic;
- reach PREPARE or COMMIT.

Compilation succeeds only when no fatal diagnostic remains.

---

## 11. Source map and provenance

A successful compiler emits a source map conforming to
[`schemas/mgls-source-map.schema.json`](../schemas/mgls-source-map.schema.json).
Offsets use normalized-source Unicode scalar indices and half-open spans.

Every author-controlled emitted program element MUST have at least one mapping:

- header field;
- top-level value;
- node and produced binding;
- explicit or data-derived edge;
- obligation requirement/resource field;
- output.

Compiler-fixed fields (`artifact_kind`, program contract identity, stability)
map to the source version declaration with relation `synthesized`. Data-derived
edges map to the consuming binding occurrence with relation `derived`.

The MGLS source map does not replace the normalizer's normalized-to-original
map. Tooling composes both maps when displaying original-source diagnostics.

Source map data is provenance and diagnostics evidence. It grants no authority,
identity, compatibility, or execution permission.

---

## 12. Host ceilings

A conforming MGLS-0 compiler enforces immutable ceilings no weaker than:

```text
source UTF-8 bytes             262144
lexical tokens                  65536
identifier scalars                128
quoted identity scalars           160
value declarations                512
nodes                             256
emitted edges                    1024
outputs                            128
structured nesting depth            8
aggregate structured items       1024
record fields per record           128
sequence items per sequence        512
budget events                      128
budget microsteps                 4096
budget concurrency                  16
budget Energy J             1000000000
```

The compiled program MUST also pass the current `MagicalProgramHostLimits`.
Source limits do not widen program/runtime limits. An implementation MAY use a
stricter documented profile, but compatibility must identify it.

The compiler MUST predict synthesized edge count before emission and reject a
source that would exceed the target edge ceiling.

---

## 13. Forbidden syntax and closed-world rule

The grammar is closed. Unknown keywords and constructs are not extensions.
Specifically, MGLS-0 rejects tokens or forms intended as:

```text
import include module package use
macro eval reflection plugin native python wasm
if else-branch match switch for while loop repeat recurse
async await spawn thread parallel
set mutate write path field-pointer
network http file filesystem environment shell
```

The token `else` exists only inside `require ... else "Diagnostic"` and cannot
introduce control flow.

A future source revision may add a construct only through a new explicit source
contract revision and compatibility/migration decision. Implementations MUST
NOT accept private syntax in `mgls "0"` and silently ignore it.

---

## 14. Formatting

Canonical human formatting SHOULD use:

- two spaces per brace indentation level;
- one declaration per line except compact selector/sequence forms;
- trailing semicolons on declarations/statements;
- one blank line between header, values, nodes, and outputs;
- lowercase keywords and operator names;
- descriptive source names rather than generated numeric names.

Formatting is not semantic. A formatter MUST preserve decoded string values,
node textual order, sequence order, requirement order within each category, and
all explicit `after` dependencies.

---

## 15. Relationship to natural-language adapters

`.mgls` is a formal source language, not a natural-language adapter input.
Latin, Literary Chinese, German, Japanese, English, and Chinese adapters remain
separate frontend families with their own adapter identities, grammars,
lexicons, ambiguity policies, and NSR lowering.

A natural-language adapter MAY eventually emit a `MagicalProgram`, but it does
not thereby make its source MGLS or claim MGLS source fidelity.

---

## 16. Implementation handoff to Issue #93

Issue #93 MUST implement:

- strict normalized-source decoding and token limits;
- a deterministic lexer/parser for `grammar/mgls.ebnf`;
- source AST nodes with normalized scalar spans;
- the namespace and ordering rules in this document;
- exact registry-backed type/effect/contract checking;
- obligation and output validation;
- deterministic node order, binding, edge, and output emission;
- complete source-map output;
- independent target program admission;
- repeated-run and installed-package determinism tests;
- fatal failure before PREPARE for every rejected source.

The parser/compiler MUST NOT import repository fixtures or branch on source ID,
program ID, filename, output name, or spell proper name.

## 17. Traceability

Normative grammar:

- `grammar/mgls.ebnf`

Machine-readable mapping/catalog:

- `conformance/mgls-source-contract.json`
- `schemas/mgls-source-map.schema.json`

Positive examples:

- `examples/mgls/independent-transition.mgls`
- `examples/mgls/boundary-reflection.mgls`

Negative contract examples:

- `examples/mgls/invalid/contract-cases.json`

Mechanical consistency tests:

- `tests/test_mgls_source_contract.py`

These artifacts define source revision 0 before parser implementation begins.
