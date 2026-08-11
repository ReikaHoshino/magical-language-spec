# Experimental Unified User Workflow

**Status:** experimental normative integration owner for pre-public archive Issue #94. This
contract adds a compatibility-safe command over already owned MGLS,
MagicalProgram, and SpellInstanceBundle paths. It does not change the stable
v0.8 evaluator ingress or the stable conformance manifest. Inclusion in package
`1.0.0rc1` does not promote this workflow.

## Purpose

Define one user-facing procedure for:

```text
MGLS-0 source
SpellInstanceBundle-0
MagicalProgram-0
```

while preserving the distinct source compiler, artifact admission, semantic
evaluator, PREPARE/COMMIT runtime, sandbox, and replay owners.

The installed experimental command is:

```text
magical-language
```

The existing commands remain published and are not reinterpreted:

```text
magical-language-evaluator
magical-language-conformance
magical-language-artifact
magical-language-spell-instances
magical-language-experimental-arcana
```

## Depends on

- [`file-naming.md`](file-naming.md)
- [`multi-stage-ingress.md`](multi-stage-ingress.md)
- [`mgls-source-language.md`](mgls-source-language.md)
- [`magical-program-artifact.md`](magical-program-artifact.md)
- [`spell-instance-bundles.md`](spell-instance-bundles.md)
- [`security-sandbox.md`](security-sandbox.md)
- [`compatibility.md`](compatibility.md)
- [`versioning-and-migration.md`](versioning-and-migration.md)

## Key invariants

```text
CLI routing != semantic dispatch
filename hint != artifact kind
filename hint != contract selection
source identity != program occurrence identity
compiler success != target admission
admission != evaluation
Evaluation != Execution
PREPARE success != COMMIT permission
syntax != authority
source map != authority
extension disagreement != fallback decoding
runtime abort != source rejection
replay != rewind
```

## 1. Public command surface

The command grammar is:

```text
magical-language check <file> [--input-kind KIND]
magical-language eval <file> [--input-kind KIND]
magical-language run <file> [--input-kind KIND]
magical-language compile <source> [--input-kind mgls]
    [--emit-program PATH]
    [--emit-source-map PATH]
```

`KIND` is one of:

```text
auto
mgls
magical-program
spell-instance-bundle
```

`auto` is the default. It means deterministic decoder selection, not
trial-and-error parsing.

### UX-CMD-001 — compatibility-safe addition

`magical-language` is an experimental additive command. An implementation MUST
NOT silently replace, alias with changed semantics, or remove any already
published stable evaluator or conformance entry point.

### UX-CMD-002 — command ownership

- `check` owns bounded decoding, source compilation where applicable, and
  ordinary target admission.
- `eval` additionally runs the ordinary semantic evaluator but MUST NOT COMMIT.
- `run` additionally performs PREPARE/COMMIT through the ordinary sandbox
  runtime and produces replay evidence.
- `compile` accepts MGLS source only and emits a deterministic
  `MagicalProgram-0` plus `MglsSourceMap-0`; it does not execute.

## 2. Immutable ingress snapshot

### UX-INGRESS-001 — single read

A path MUST be rejected when it is a symbolic link. An admitted regular path is
read exactly once into an immutable byte snapshot. The snapshot digest is
SHA-256 of those exact bytes and is reported as ingress evidence only.

Changes to the filesystem after the snapshot is created MUST NOT alter the
current operation.

### UX-INGRESS-002 — bounded input

The existing artifact/source byte, nesting, token, graph, structured-value,
resource, event, microstep, and concurrency ceilings remain authoritative.
The integration layer MUST NOT raise them from source or artifact declarations.

### UX-INGRESS-003 — no external inclusion

No command may activate source imports, filesystem/network/environment access,
host-language code, plugin selectors, or executable artifact resources.

## 3. Deterministic decoder and kind routing

### UX-ROUTE-001 — automatic precedence

Automatic mode selects exactly one decoder:

1. `*.mgls` selects strict MGLS source decoding;
2. recognized JSON naming selects one bounded JSON decode and reads the
   authoritative `artifact_kind` / `artifact_version` envelope;
3. an unknown suffix is ambiguous in automatic mode and fails;
4. unrelated decoders are never tried until one succeeds.

### UX-ROUTE-002 — authoritative decoded kind

For structured input, only the decoded envelope may identify
`SpellInstanceBundle` or `MagicalProgram`. The basename, directory, suite,
scenario, source ID, program ID, instance ID, display name, or spell proper name
MUST NOT select a compiler branch, translator, semantic handler, runtime
executor, or contract.

### UX-ROUTE-003 — explicit mode agreement

An explicit `--input-kind` selects one expected decoder and expected public
kind. It MUST agree with:

- the source suffix where a registered source/stage suffix is present;
- the decoded source header or artifact envelope;
- the supported source/artifact revision.

Disagreement produces one deterministic ingress/routing rejection. It MUST NOT
fall back to another decoder.

### UX-ROUTE-004 — advisory filename validation

Registered filename hints are:

```text
*.mgls
*.program.mga.json
*.bundle.mga.json
```

A generic `.json` or `.mga.json` remains a structured decoding hint. A
registered stage suffix MUST agree with the decoded envelope. An unknown suffix
may be admitted only with an explicit kind; its name still cannot select
semantics.

### UX-ROUTE-005 — identity and occurrence

Renaming a filename or changing source/program/instance identity cannot change
contract dispatch. Program identity is nevertheless part of runtime occurrence
identity, so deterministic event IDs, process IDs, provenance, and replay
records MAY change while the selected semantic contract and authoritative world
transition remain the same.

```text
same semantic dispatch
!= same occurrence identity
```

## 4. Per-kind pipelines

### UX-PIPE-001 — MGLS source

```text
immutable SourceBytes
  -> SourceTextNormalizerV1
  -> bounded MGLS lexer/parser/checker
  -> verified MagicalProgram-0 + MglsSourceMap-0
  -> independent target admission
  -> ordinary evaluator
  -> ordinary PREPARE/COMMIT runtime
  -> replay
```

The integration layer MUST use the verified `src.mgls` public frontend. It MUST
NOT duplicate source grammar or accept an unverified partial program.

### UX-PIPE-002 — direct MagicalProgram

Direct program input skips source compilation only. It still undergoes ordinary
schema, graph, binding, exact contract, compatibility, type/effect/obligation,
host-limit, evaluator, PREPARE/COMMIT, sandbox, and replay checks.

The reference `run` command uses the published reference experimental host
context. This context is host-owned; the program cannot add records or raise
limits through syntax.

### UX-PIPE-003 — SpellInstanceBundle

Bundle input passes the existing bundle admission contract and canonical
contract-pair translation into `MagicalProgram-0`. The integration layer MUST
reuse the same public generic evaluator/runtime path used by the existing
artifact service. Embedded expectations remain comparison data and never select
implementation.

### UX-PIPE-004 — admitted-contract extensibility

A user program may compose contracts already admitted by the host registry
without adding Python code for each source file. Arbitrary new physical
semantics still require a separately admitted host-owned semantic/runtime
contract and cannot be defined by source spelling, registry data, or CLI flags.

## 5. Common machine-readable envelope

Every command emits exactly one JSON object to standard output:

```json
{
  "workflow": {
    "contract_id": "magical-language-workflow",
    "revision": "0",
    "stability": "experimental"
  },
  "command": "check | eval | run | compile",
  "status": "...",
  "input": {
    "kind": "...",
    "version": "...",
    "sha256": "...",
    "filename_hint": "..."
  },
  "result": {},
  "diagnostics": []
}
```

### UX-OUTPUT-001 — deterministic JSON

JSON is UTF-8, key-sorted, compact, finite-number-only, and followed by one line
terminator. User-visible failures MUST be represented by the envelope without a
Python traceback.

### UX-OUTPUT-002 — status meaning

Successful operation statuses include:

```text
Accepted
Evaluated
Compiled
Committed
PASS
```

`Rejected` means ingress, source, artifact, compatibility, admission, or
integration routing failed before the requested successful boundary.

`Aborted` means evaluation reached an executable candidate but the ordinary
runtime failed closed before a successful COMMIT. Bundle execution retains its
existing `PASS` / `FAIL` comparison status.

### UX-OUTPUT-003 — diagnostics preserve stage order

Diagnostics are collected in pipeline traversal order. An evaluation may report
non-fatal/deferred conditions before a later terminal runtime abort. The
terminal execution result remains authoritative for the run outcome and is
also present under `result.execution.abort` where applicable.

The integration layer MUST NOT erase upstream diagnostics, invent a single
cross-stage code, or hide a terminal abort behind an earlier deferred code.

## 6. Exit codes

### UX-EXIT-001 — fixed process status

```text
0  successful Accepted/Evaluated/Compiled/Committed/PASS operation
2  deterministic Rejected input or output operation
3  runtime Aborted or bundle FAIL result
4  unexpected internal integration failure, still emitted as JSON
```

Argument-parser usage errors remain owned by the command parser.

## 7. Compiler output files

### UX-EMIT-001 — optional inspection artifacts

`compile` may emit the exact program and source map returned in the JSON
envelope. Emission does not grant authority or execution permission.

### UX-EMIT-002 — atomic output boundary

Each requested output is first written to a temporary regular file in the
existing destination directory, flushed, and atomically replaced. Output paths:

- MUST be distinct;
- MUST NOT be symbolic links;
- MUST NOT overwrite the source input;
- MUST have an existing non-symlink parent directory.

A preparation/write failure rejects the output operation and removes temporary
files. Callers that require an indivisible multi-file publication transaction
must provide a stronger external storage transaction; two filesystem replaces
are not claimed to be one cross-file atomic commit.

## 8. Security and authority

### UX-SEC-001 — no authority from routing

The command, suffix, explicit kind, successful compilation, source map, program
identity, or compatibility metadata never creates:

- Capability or Lease;
- resolved identity;
- evidence truth or freshness;
- Energy, Matter, event, or microstep resources;
- registry compatibility;
- PREPARE reservation;
- COMMIT permission.

### UX-SEC-002 — no partial commit

Malformed/unknown/forbidden source or artifacts fail before runtime. Runtime
failures use the existing transactional rollback boundary and report whether
the authoritative configuration is unchanged. The integration layer MUST NOT
catch an abort and synthesize a committed result.

### UX-SEC-003 — private failure boundary

Unexpected internal exceptions fail closed as `InternalFailure` without raw
traceback, host path, private object representation, or executable details.
Detailed internal logs remain implementation-owned.

## 9. Replay

### UX-REPLAY-001 — successful and aborted runs

A program or bundle run that reaches the runtime produces replay evidence. A
committed trace and a deterministic-abort trace are replayed against a distinct
clone of the same initial host state. `Match` means deterministic reproduction;
it does not rewind the committed world.

## 10. Packaging guarantee

### UX-PKG-001 — installed command parity

The repository, editable install, wheel install, and sdist install MUST expose
the same `magical-language` command and produce matching statuses for:

- source compile/check/eval/run;
- emitted program check/eval/run;
- canonical generic bundle run;
- deterministic invalid-source rejection;
- replay and no-traceback behavior.

The installed smoke runs outside the repository working directory and uses
package-owned resources.

## 11. Compatibility and stability

### UX-COMPAT-001 — experimental surface

The workflow contract and command are experimental revision `0`. Their presence
in package version `1.0.0rc1` does not promote MGLS, MagicalProgram, or
SpellInstanceBundle to the stable v1.0 candidate direct-entry surface.

### UX-COMPAT-002 — stable counts unchanged

This integration adds separately classified experimental conformance evidence.
It MUST NOT alter:

```text
stable conformance classes          4
stable required cases              65
MKI data-plane operations           6
World Kernel interaction classes    5
package version                     1.0.0rc1
```

Historical `spec/` snapshots remain immutable.

## 12. Experimental conformance

Machine-readable evidence is in:

```text
conformance/experimental-user-workflow.json
```

It is not part of `conformance/manifest.json`, does not satisfy a pre-public archive Issue #38
stable requirement claim by itself, and cannot change the four-class/65-case
stable count.

## 13. Traceability

- source language and lowering: `mgls-source-language.md`;
- file hints: `file-naming.md`;
- direct-stage obligations: `multi-stage-ingress.md`;
- target artifact: `magical-program-artifact.md`;
- bundle translation: `spell-instance-bundles.md`;
- security/runtime: `security-sandbox.md`;
- experimental evidence: `conformance/experimental-user-workflow.json`.
