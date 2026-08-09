# Typed Multi-Stage Ingress

**Status:** experimental normative architecture owner for Issues #48 and #92.
This document classifies public and internal entry stages and fixes downstream
validation obligations. MGLS source revision `0` is owned by
[`mgls-source-language.md`](mgls-source-language.md).

## Purpose

Define which pipeline representations may be supplied directly and what remains
mandatory when an upstream transformation is skipped.

> Entering at stage S may skip only transformations that precede S. It MUST NOT
> bypass obligations owned by S or any downstream stage.

## Non-goals

- making every implementation object a public file format;
- defining a portable public ECIR;
- making KernelPlan or PreparedPlan portable;
- weakening compatibility, type, identity, authority, conservation, sandbox,
  PREPARE/COMMIT, or replay checks;
- changing the stable v1.0 candidate surface or historical snapshots.

## Depends on

- `file-naming.md`
- `mgls-source-language.md`
- `source-text-normalization.md`
- `compatibility.md`
- `magical-program.md`
- `magical-program-artifact.md`
- `spell-instance-bundles.md`
- `kernel-execution.md`
- `security-sandbox.md`

## Key invariants

```text
direct entry != trusted entry
later stage != higher privilege
serialized stage != stable public stage
schema-valid != semantically valid
KernelPlan != PreparedPlan
PreparedPlan != COMMIT permission
filename token != stage authority
missing provenance != invented provenance
```

## 1. Pipeline model

```text
Natural-language source
  -> SourceTextNormalizer / LanguageAdapter
  -> NSR
  -> implementation-owned semantic stages

MGLS-0 source
  -> MGLS lexer/parser/type-effect-obligation checker
  -> MagicalProgram-0
  -> implementation-owned semantic stages

SpellInstanceBundle
  -> canonical contract-pair translation
  -> MagicalProgram-0

MagicalProgram-0
  -> program admission/evaluation
  -> planning / PREPARE
  -> COMMIT / replay
```

MGLS and natural-language adapters are distinct frontend families. `.mgls` does
not select an adapter or pass through NSR unless a future explicit contract says
so.

## 2. Direct-entry inventory

| Representation | Direct input | Stability | Canonical hint | Owner |
|---|---|---|---|---|
| natural-language source | where an admitted LanguageAdapter exists | only already promised paths stable | adapter/tool-specific | source/adapter references |
| MGLS source | yes | experimental | `*.mgls` | `mgls-source-language.md`, source contract `mgls-source` revision `0` |
| raw NSR | yes for current evaluator boundary | current supported boundary | plain JSON; `*.nsr.mga.json` reserved | NSR reference/schema |
| SpellInstanceBundle | yes | experimental | `*.bundle.mga.json` | `spell-instance-bundles.md` |
| MagicalProgram | yes | experimental | `*.program.mga.json` | `magical-program-artifact.md` |
| SemanticAST | no | implementation-owned | no token | evaluator implementation |
| TypedMIR | no | implementation-owned | no token | evaluator implementation |
| KernelPlan | no portable public input | profile/revision-bound | no token | planner/runtime |
| PreparedPlan | runtime-local opaque handle only | current-state-bound | no file form | PREPARE/runtime |
| FeasibilityReport | output only | owned report contract | tool-defined output | evaluator/report |
| RuntimeExecutionTrace | output/replay evidence only | owned trace contract | tool-defined output | runtime/replay |

A representation becomes public ingress only when it has a versioned contract,
compatibility/admission rules, provenance, deterministic diagnostics, security
ceilings, downstream obligation mapping, and conformance evidence.

## 3. MGLS source ingress

MGLS source enters before `MagicalProgram-0`. The decoder MUST:

1. apply strict UTF-8 and `SourceTextNormalizerV1`;
2. validate the authoritative `mgls "0";` declaration;
3. enforce the closed grammar and source ceilings;
4. resolve source names and exact registry/profile/contract revisions;
5. check types, dimensions, effects, obligations, outputs, and graph order;
6. emit one deterministic `MagicalProgram-0` plus source map;
7. submit the emitted program to ordinary target admission.

Source revision `0` is experimental. Compiler success does not waive target
schema/admission, compatibility, PREPARE, COMMIT, sandbox, or replay.

A source filename, source ID, program ID, output name, or spell proper name MUST
NOT select contracts or execution behavior.

## 4. NSR ingress

Direct NSR skips source parsing/adapter normalization only. It still requires:

- schema/contract and compatibility validation;
- semantic elaboration and type/dimension/effect checks;
- resolution/evidence handling;
- Identity, Capability, Lease, conservation/accounting obligations;
- estimator/planning ownership;
- PREPARE/COMMIT revalidation, sandbox, and replay.

Direct NSR does not fabricate a source sentence, adapter trace, ambiguity
decision, or source fidelity claim.

## 5. SpellInstanceBundle ingress

A bundle has one authoritative ingress and supporting profiles/evidence/expected
results. Public execution now lowers through the canonical `MagicalProgram-0`
path. Bundle filename, suite, scenario, instance ID, or expected outcome does not
select implementation.

A multi-stage bundle may carry derived caches/evidence only under the
one-authoritative-ingress rule in Section 11.

## 6. MagicalProgram ingress

Direct program input skips source parsing only. It does not skip:

- graph, binding, structured-value, and output validation;
- exact contract/registry/profile compatibility;
- type/dimension/effect checking;
- evidence/identity/authority/resource obligations;
- planning, PREPARE/COMMIT revalidation, sandbox, or replay.

A declared type, reference-like ID, Capability requirement, resource amount, or
contract name remains untrusted until its owning downstream stage validates it.

## 7. Non-public stages

### SemanticAST and TypedMIR

These may be emitted as same-implementation diagnostics/caches, but are not
public interchange. Records naming themselves SemanticAST or TypedMIR cannot
bypass semantic/type/effect validation. No `ast` or `mir` token is registered.

### KernelPlan

KernelPlan is selected against explicit registry/profile/evidence/world-index
context and is not portable execution authority. A user-supplied plan record
cannot enter COMMIT. No `plan` token is registered.

### PreparedPlan

PreparedPlan is runtime-local, opaque, current-state-bound, single-use/expiring
according to runtime policy, and revalidated before COMMIT. It cannot be
reconstructed from source/JSON, embedded in a portable bundle, or transferred
between unrelated runtime instances. No `prepared` token or file form exists.

## 8. Provenance and source maps

Direct input states only provenance it actually possesses. It MUST NOT invent:

- natural-language text/adapter identity/ambiguity trace;
- MGLS source or source fidelity for directly authored programs;
- semantic/planner history;
- evidence freshness or authority;
- PREPARE reservations or compatibility decisions.

MGLS compilation emits lowered provenance and an
`MglsSourceMap-0` conforming to `schemas/mgls-source-map.schema.json`. This map
is diagnostics/provenance evidence only and grants no privilege.

Missing upstream provenance is allowed only where no downstream rule requires
it. Otherwise the owning stage fails closed or returns Indeterminate.

## 9. Obligation monotonicity

Skipping upstream transformations never removes downstream obligations.

| Obligation | Source | NSR | MagicalProgram | KernelPlan evidence | PreparedPlan |
|---|---:|---:|---:|---:|---:|
| bounded decoding/schema/contract | required | required | required | internal boundary | handle validation |
| compatibility | required | required | required | required/rechecked | rechecked |
| type/dimension/effect | source check + target recheck | required | required | evidence required | revalidated as applicable |
| identity/resolution | downstream required | downstream required | downstream required | binding evidence | current-state revalidation |
| Capability/Lease | declarations only | downstream required | requirements only | obligation evidence | exact record revalidation |
| conservation/accounting | declarations only | downstream required | requirements only | plan obligations | reservation revalidation |
| PREPARE | before execution | before execution | before execution | still required | already produced handle |
| COMMIT/sandbox/stop fence | required | required | required | required | required |
| replay | where claimed | where claimed | where claimed | same | same |

A later-stage input that cannot supply/reconstruct mandatory evidence is
rejected; it does not receive a waiver.

## 10. Deterministic CLI dispatch

Explicit mode supplies an expected input kind, which must agree with decoded
content. Automatic precedence is:

1. `.mgls` -> source path, then authoritative source revision `0` validation;
2. recognized structured encoding -> decode once and read envelope;
3. raw NSR only through an explicitly owned command/unambiguous rule;
4. no unrelated loader trial-and-error.

Unknown versions and kind/header/envelope/suffix disagreement fail before
semantic evaluation. CLI dispatch cannot infer internal stages from basenames.

## 11. Multi-stage containers and caches

A container with multiple stage records MUST:

1. declare exactly one authoritative ingress;
2. label others derived cache, diagnostic, expectation, or replay evidence;
3. identify parent/transformation evidence where required;
4. reject/invalidate disagreement deterministically, never silently prefer the
   later stage;
5. prevent caches from adding authority, resources, compatibility, or current
   bindings;
6. remain reproducible without unverified cache trust;
7. never embed a portable PreparedPlan.

## 12. Compatibility and migration

```text
newer stage version != compatible
same token != compatible
schema-valid != semantically compatible
migration success != admitted
```

Unknown contracts/versions fail closed. Migration requires exact source/target
identities, an explicit transformation revision, target validation,
post-migration compatibility, and honest provenance/loss declarations.

MGLS revision changes use source-contract compatibility rules; they are not
inferred from filename or numeric ordering.

## 13. Security and limits

Every public ingress is bounded for bytes, nesting, tokens/nodes/edges/values,
strings/numbers, contract references, structured items, outputs, effects,
Energy, Matter, events, microsteps, and concurrency as applicable.

No stage may contain or activate:

- host-language code or executable imports;
- network/filesystem/environment access;
- raw WorldState paths or arbitrary mutation;
- artifact-authored Capability/Lease/identity/evidence/accounting records;
- fixture-specific implementation dispatch;
- opaque legacy executable payloads.

Later-stage input may increase attack surface and therefore never receives
weaker ceilings.

## 14. Failure matrix

| Failure | Required behavior |
|---|---|
| malformed/unknown source header or envelope | reject before semantic evaluation |
| expected kind vs decoded content mismatch | deterministic rejection |
| unknown source/artifact/stage version | fail closed |
| internal-only stage supplied publicly | `UnsupportedSemanticExtension` or owned equivalent |
| missing required provenance/compatibility evidence | fail closed or Indeterminate according to owner |
| source/program claims authority/resources | treat only as requirements; validate/bind downstream |
| KernelPlan supplied to runtime | reject; mandatory PREPARE path |
| serialized PreparedPlan supplied | reject as non-portable |
| multi-stage records disagree | reject or invalidate cache deterministically |
| cached stage unverifiable | recompute only if owner permits; otherwise fail closed |

## 15. Registered naming inventory

```text
*.mgls               mgls-source revision 0
*.nsr.mga.json        reserved NSR token
*.bundle.mga.json     SpellInstanceBundle
*.program.mga.json    MagicalProgram-0
```

No `ast`, `mir`, `plan`, or `prepared` token is registered.

## 16. Traceability

- MGLS contract: `mgls-source-language.md`, contract `mgls-source` revision `0`;
- source grammar: `grammar/mgls.ebnf`;
- source map: `schemas/mgls-source-map.schema.json`;
- program contract: `magical-program-artifact.md`;
- naming/media hints: `file-naming.md`.

---

## Issue #94 unified workflow implementation

The experimental `magical-language` integration provides a single-read implementation of the direct-ingress obligations in this document:

```text
immutable path bytes
  -> one selected source or structured decoder
  -> decoded source/artifact kind and revision
  -> ordinary source compiler or artifact admission
  -> ordinary evaluator
  -> ordinary PREPARE/COMMIT runtime
  -> replay
```

It does not add SemanticAST or TypedMIR public ingress, does not perform loader trial-and-error, and does not infer language or artifact semantics from a basename. `magical-language-evaluator` remains the stable v0.8 Latin/NSR command. The new workflow is an experimental additive surface owned by [`user-workflow.md`](user-workflow.md).
