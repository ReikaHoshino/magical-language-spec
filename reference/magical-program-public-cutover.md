# MagicalProgram public cutover

## Status

This document defines the current experimental public execution ownership for
`SpellInstanceBundle` after pre-public archive Issue #91.

## Public path

```text
SpellInstanceBundle bytes
  -> strict artifact decoding and schema validation
  -> compatibility, host-ceiling, contract-pair, and parameter admission
  -> exact semantic/runtime contract-pair translation
  -> declarative MagicalProgram-0
  -> MagicalProgram evaluator
  -> generic PREPARE / COMMIT runtime
  -> deterministic replay
  -> compatibility-preserving public result envelope
```

`src.artifacts.spell_instance_program` owns the public library and
`magical-language-artifact check|eval|run` path.  Its semantic and runtime
registries validate admitted contract identities and parameter schemas only;
their handlers and executors are deliberately unreachable.  Executable
ownership begins only after translation to `MagicalProgram-0`.

## Canonical production registry

`src.migration.magical_program` is the single production assembly for the
complete current 12-contract inventory.  Selection uses only the exact
`(semantic_contract, runtime_contract)` pair.  Filename, suite, instance ID,
scenario name, and display name cannot select executable behavior.

The production assembly imports individual declarative translators and generic
runtime contracts directly.  It does not import the frozen legacy
`SpellInstanceService`, dedicated Success-Arcana or DEBUG-HELL handlers and
executors, or `magical_program_shadow_current` monkey-patch composition.

## Legacy boundary

`src.artifacts.spell_instance` remains frozen solely as an external historical
oracle for differential tests.  It is not exported by `src.artifacts`, is not
used by the artifact CLI, and is not imported by the production translator or
public service.

## Preserved guarantees

- artifact bytes are decoded once into an immutable admitted snapshot;
- admission diagnostics and public result envelopes remain compatible;
- syntax does not grant Identity, Capability, Lease, evidence truth, Energy,
  Matter, accounting capacity, or compatibility;
- PREPARE freezes authoritative bindings without committing state;
- COMMIT remains atomic and fail-closed;
- replay covers committed and deterministic-abort paths;
- recognized-unsupported contracts remain `Indeterminate` and have no runtime;
- stable v1.0 candidate conformance remains four classes and 65 required cases;
- package version transition does not promote this experimental cutover; the current package is `1.0.0rc1`.

## Verification requirement

Every change to this boundary must prove:

1. all 12 current bundles pass the public API and CLI path;
2. renamed copies use identical dispatch and behavior;
3. no dedicated legacy handler or executor enters the production import graph;
4. external golden, rollback, replay, identity, authority, and accounting tests
   remain green;
5. repository, editable, wheel, and sdist execution agree.
