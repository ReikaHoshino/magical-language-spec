# Source and Artifact File Naming

**Status:** experimental normative naming owner for pre-public archive Issues #47 and pre-public archive Issue #92. This
document defines filename and media-type hints. Concrete source revision 0 is
owned by [`mgls-source-language.md`](mgls-source-language.md).

## Purpose

Define durable project naming for human-authored source, machine-readable
artifacts, stage descriptors, extension/header disagreement, and media-type
hints without making a filename semantically authoritative.

## Non-goals

- selecting executable behavior from a filename;
- replacing source/artifact contract validation;
- making implementation-internal stages public;
- registering an IANA media type;
- changing the stable v1.0 candidate surface or historical snapshots.

## Depends on

- `conventions.md`
- `compatibility.md`
- `multi-stage-ingress.md`
- `spell-instance-bundles.md`
- `magical-program.md`
- `mgls-source-language.md`

## Key invariants

```text
filename != artifact identity
extension != artifact kind
extension != schema/source version
extension != semantic contract
extension != compatibility decision
extension != authority
extension != executable dispatch
encoding suffix != semantic stage
```

## 1. Human-authored source

The canonical source suffix is:

```text
.mgls
```

A `.mgls` file is strict UTF-8 text under source contract `mgls-source`
revision `0`. Its authoritative first declaration is:

```mgls
mgls "0";
```

The suffix selects source decoding/tooling only. A tool MUST still apply
`SourceTextNormalizerV1`, parse the header, enforce the closed grammar, resolve
exact registry/profile contracts, and compile through the ordinary
`MagicalProgram-0` admission path.

Merely renaming text to `.mgls` does not make it source. A suffix/header/media
version disagreement fails before source semantic checking.

MGLS is a formal source frontend. It is not an implicit natural-language
adapter and the suffix does not select Latin, German, Japanese, Chinese, or any
other LanguageAdapter.

## 2. Machine-readable artifacts

The canonical JSON filename form is:

```text
<name>.mga.json
```

`mga` means **Magical Artifact**. The final `.json` remains visible to editors,
formatters, scanners, and transport tooling. The authoritative in-document
envelope identifies artifact kind/version, contract/profile references,
provenance, and compatibility evidence.

A plain `.json` name remains usable where an explicit loader admits it.
`.mga.json` is the canonical project-facing form, not an exclusivity rule.

## 3. Advisory stage tokens

A public artifact contract MAY register:

```text
<name>.<stage>.mga.json
```

A stage token is lowercase ASCII, descriptive only, and MUST agree with the
authoritative envelope when filename validation is enabled. It MUST NOT be the
sole dispatch key or imply stable/public status.

The current inventory is:

| Representation | Canonical form | Status / owner |
|---|---|---|
| MGLS source | `*.mgls` | public experimental source; `mgls-source` revision `0` |
| generic JSON artifact | `*.mga.json` | canonical naming family |
| NSR artifact | `*.nsr.mga.json` | reserved public token; raw NSR JSON remains admitted where owned |
| SpellInstanceBundle | `*.bundle.mga.json` | experimental token |
| MagicalProgram | `*.program.mga.json` | public experimental artifact revision `0` |

The following are deliberately not registered:

```text
ast
mir
plan
prepared
```

SemanticAST and TypedMIR are implementation-owned; KernelPlan is profile-bound;
PreparedPlan is a runtime-local opaque handle with no portable file form.

## 4. Encoding suffixes

The encoding suffix remains last:

```text
<name>.mga.json
<name>.mga.cbor
<name>.mga.yaml
<name>.mga.txt
```

Only encodings explicitly admitted by an owning contract are supported. These
forms reserve a pattern and do not authorize fallback decoding or transcoding.
A loader validates the decoded envelope; changing the suffix does not alter
semantics.

## 5. Filename-hint validation

Tools may use:

1. **explicit-kind mode**, where the caller states an expected source/artifact
   kind; or
2. **auto-inspection mode**, where the tool selects one decoder and reads the
   authoritative source header or artifact envelope.

The expected kind MUST agree with decoded content. Deterministic automatic
precedence is:

1. `.mgls` -> strict source path;
2. recognized structured encoding -> decode once and read envelope;
3. raw legacy forms only through their explicit owned command/rule;
4. never try unrelated loaders until one succeeds.

A tool MUST NOT select a semantic handler, translator, runtime executor, or
contract from basename, directory, suite ID, scenario label, instance ID, spell
proper name, or display name.

An unknown suffix is not proof of invalid content. An explicit loader MAY admit
correct content under policy; automatic discovery SHOULD fail when decoding is
ambiguous.

## 6. Source metadata

MGLS-0 uses an in-source header rather than filename metadata:

```mgls
mgls "0";
source "source:example:001";
program "program:example:001";
registry "registry:reference-experimental" revision "1";
profile "profile:reference-experimental" revision "1";
```

The header owns source revision, source provenance identity, target program
identity, and exact registry/profile compatibility declarations. The filename
MUST NOT fabricate:

- adapter identity or language tag;
- source provenance/fidelity;
- target program identity;
- World or RuntimeProfile selection beyond explicit header declarations;
- authority, Capability, Lease, evidence truth, resources, or compatibility.

MGLS-0 has no imports or companion manifest. Future source revisions require an
explicit compatibility/migration decision before adding either.

## 7. Media types

The project-facing source media type is reserved as:

```text
text/vnd.magical-language.source; version=0; charset=utf-8
```

The artifact candidate remains:

```text
application/vnd.magical-language.artifact+json
```

Neither is claimed as IANA-registered. Media parameters are hints and MUST agree
with decoded content. The decoded contract remains authoritative.

## 8. Editor, LSP, and repository tooling

Tooling SHOULD:

- associate `.mgls` with `grammar/mgls.ebnf` and source revision `0`;
- treat `*.mga.json` and `*.<stage>.mga.json` as JSON first;
- use the source header/artifact envelope for version and schema selection;
- expose filename/header/envelope disagreement as a diagnostic;
- preserve original filenames and source maps as provenance, not identity;
- avoid classifying generated artifacts as source code where possible.

## 9. Compatibility and migration

```text
same filename != compatible artifact
same extension != same contract
renamed file != migrated source/artifact
new suffix != semantic version change
```

Changing a canonical suffix, stage token, media parameter, or header relation
requires an explicit compatibility/deprecation decision and a documented rename
or migration path. Renaming alone MUST NOT change decoded semantics.

Unknown source/artifact versions fail closed; a tool MUST NOT reinterpret them
as its newest supported version.

## 10. Traceability

- source grammar/semantics: `mgls-source-language.md`, `grammar/mgls.ebnf`;
- source revision: `mgls-source` revision `0`;
- source map: `schemas/mgls-source-map.schema.json`;
- ingress ownership: `multi-stage-ingress.md`;
- artifact contract: `magical-program-artifact.md`.

---

## pre-public archive Issue #94 unified workflow integration

The experimental `magical-language` command implements the rules above as follows:

- `*.mgls` selects the strict MGLS decoder;
- `*.program.mga.json` and `*.bundle.mga.json` are validated stage hints;
- generic `.json` / `.mga.json` selects one structured decoder, after which decoded `artifact_kind` / `artifact_version` is authoritative;
- an unknown suffix requires explicit `--input-kind` and remains semantically inert;
- suffix/header/explicit-kind disagreement is `InputKindHintMismatch` or `ExpectedInputKindMismatch` and never falls back to another decoder;
- filenames, source/program/instance IDs, suites, fixtures, and spell names never select contracts or executors.

The complete command, envelope, exit-code, security, and packaging owner is
[`user-workflow.md`](user-workflow.md). This integration is experimental and does not alter stable v0.8 direct-entry contracts.
