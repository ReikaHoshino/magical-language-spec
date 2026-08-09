# Minimal Local Evaluator Implementation Reference — v0.8.0

**Status:** informative reference implementation profile; normative semantics remain in the linked current reference documents.

## Purpose

v0.8.0 ships the first usable local reference evaluator for the frozen pre-v0.8 contracts.
It evaluates supported source/NSR inputs deterministically through internal semantic/compiler stages and returns a validated `FeasibilityReport` without authoritative world mutation.

## Normative dependencies

- `language-adapters.md`
- `feasibility.md`
- `planning-inference.md`
- `estimator-models.md`
- `registry.md`
- `world-index.md`
- `canonical-water-ball.md`
- `machine-values.md`
- `security-sandbox.md`

This implementation document does not override those contracts.

## Public v0.8 ingress

Exactly two public ingress families are implemented:

1. natural-language source with explicit project adapter selection `--lang lat`;
2. schema-valid NSR JSON/object input.

```text
source --lang lat
→ LanguageAdapter<lat>
→ NormalizationCandidateSet / AmbiguityPolicy
→ NSR

NSR JSON/object
→ NSR validation
```

Both paths converge on:

```text
NSR validation
→ SemanticAST
→ TypedMIR
→ type/dimension checks
→ read-only resolver / SemanticRegistry evidence
→ KernelPlan
→ planning / estimator / obligation assessments
→ validated FeasibilityReport
→ STOP
```

The following are intentionally **not** public v0.8 ingress contracts:

- `SemanticAST`;
- `TypedMIR`;
- `NormalizedIR`;
- `KernelPlan`;
- automatic language detection;
- automatic input-kind detection.

General multi-stage direct ingestion remains owned by Issue #48.

## CLI

The reference entry point is:

```text
python -m src.evaluator
```

Latin source:

```text
python -m src.evaluator \
  --source "Calorem ab aqua ad aerem transfer." \
  --lang lat \
  --format human \
  --level report
```

NSR JSON:

```text
python -m src.evaluator \
  --nsr path/to/nsr.json \
  --format json \
  --level report
```

`--nsr -` reads JSON from stdin.

Supported output levels:

```text
surface
nsr
semantic-ast
typed-mir
kernel-plan
report
all
```

`surface` is meaningful for natural-language ingress; structured NSR ingress has no invented surface stage.

## Implementation layout

```text
src/
└─ evaluator/
   ├─ __main__.py       CLI module entry point
   ├─ cli.py            explicit public ingress and formatting selection
   ├─ evaluator.py      public release/report facade
   ├─ core.py           semantic pipeline orchestration
   ├─ fixtures.py       read-only reference registry/index/profile boundaries
   ├─ formatting.py     deterministic human/JSON output
   └─ schema.py         local JSON Schema validation helpers
```

The package public API exposes `LocalEvaluator`, Latin source evaluation, NSR object/JSON evaluation, and deterministic formatters. It does not expose direct later-stage ingestion methods.

## Read-only evidence boundaries

The v0.8 implementation consumes fixture-backed `SemanticRegistry`, `WorldIndex`, estimator profiles, and canonical conformance artifacts as read-only evidence.

```text
WorldIndex candidate != Ref
Visibility != Authority
Registry metadata != Capability
Estimate != Reservation
```

The evaluator never upgrades lexical proposals/index candidates into authoritative identity or permission by inference.

## Planning inference

For WB-CANON-001 the source terminal remains semantic `Unknown(MissingArgument)`.
When the frozen profile permits `EstimateAllowed` + `PrepareBound`, the evaluator records a distinct provenance-bearing `PlanningAssumption` for the 50 m fixture horizon.

```text
source Unknown remains Unknown
PlanningAssumption = separate planning artifact
```

A `MustResolve` terminal cannot be weakened into a planning assumption.

## Estimation and obligations

The synthetic reference estimator evaluates profile-owned Energy/resource/timing coefficients. The canonical synthetic Energy total is 200 J and remains fixture/profile data, not a world constant.

Estimator output is independent from mandatory:

- type proof;
- identity/revalidation evidence;
- Capability;
- Lease;
- conservation proof;
- sandbox safety.

A missing required estimator model produces `EstimatorModelUnavailable` / `Indeterminate`; it is never interpreted as zero.

## Gravity / trajectory control

The canonical horizontal trajectory lowers to `CONSTRAIN`. Gravity is not removed from the world model.
Control Energy is accounted separately from physical mechanical work through the estimator profile.
If control-estimator evidence is unavailable, trajectory control remains `Unknown`, not a proven control violation.

## Kernel boundary

The data plane remains exactly:

```text
RESOLVE
OBSERVE
CHANNEL
TRANSFER
RECONFIGURE
CONSTRAIN
```

`COMMIT` is not a KernelPlan data-plane primitive and is not executed by v0.8.

## Canonical conformance

WB-CANON-001 enters the evaluator from its authoritative structured NSR stage. Its English surface is retained as source-fidelity/provenance evidence only.

v0.8.0 does **not** claim an `eng` source→NSR adapter.

The evaluator preserves:

- mass = 50 kg;
- radius = 0.01 m;
- relative distance = 3 m;
- initial velocity = 0 m/s;
- acceleration = 50 m/s²;
- horizontal-forward trajectory;
- source terminal = semantic Unknown;
- minimum eligible canonical plan = `wb:plan:transfer-reconfigure`;
- canonical synthetic estimated Energy = 200 J;
- report-only result with no world mutation.

## Failure behavior exercised in v0.8

The reference tests exercise, at minimum:

- invalid UTF-8 / normalization failure;
- unresolved interactive ambiguity;
- NSR schema failure;
- SemanticFingerprint mismatch;
- semantic type failure;
- SI dimension failure;
- read-only resolution failure;
- authority failure;
- conservation failure;
- estimator unavailable;
- forbidden MustResolve inference;
- non-MKI plan operation;
- unsupported semantic subset without invented semantics.

Runtime-only revalidation/binding failures remain v0.9 concerns because v0.8 stops before COMMIT.

## Determinism / validation

Repository release validation uses:

```text
python tests/validate_schemas.py
python -m unittest discover -s tests -v
git diff --check
```

Machine-readable CLI output uses deterministic JSON key ordering. Every public evaluator return is validated against `schemas/feasibility-report.schema.json` before it leaves the public facade.

## Non-goals retained after v0.8.0

- authoritative mutable WorldState;
- COMMIT execution;
- production WorldIndex/storage/spatial engine;
- scheduler/integrator runtime;
- general later-stage direct ingestion;
- automatic language/input-kind detection;
- non-reference language adapter breadth;
- renderer breadth;

## Experimental handler dispatch

Issue #77 adds an implementation-owned `(NSR kind, action) -> evaluator handler` dispatch for
`Experimental-Arcana-0`. The existing WB-CANON-001 Generation handler is preserved. Unknown action or
unadmitted extension fails as `UnsupportedSemanticSubset`; it is not ignored or coerced. Handler-produced
SemanticAST/TypedMIR/KernelPlan remain internal evidence, not new public direct-ingress or serialized ECIR
contracts. The portable semantic owner is `success-arcana.md`.
- performance optimization.

Sandboxed execution/runtime is owned by Issue #37 (v0.9).
