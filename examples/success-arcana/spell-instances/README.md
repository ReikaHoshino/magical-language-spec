# SUCCESS-ARCANA spell-instance library

Status: design inputs for Issue #77 (`Experimental-Arcana-0`). These files are not current normative reference text and are not executable conformance fixtures by themselves.

Each spell instance lives in one standalone file. Instance IDs and names are fixture identities only; evaluator/runtime dispatch MUST depend on versioned semantic/runtime contract identities rather than `SA-*` names.

## Instances

- `SA-001` — `Sevenfold Boundary Reflection Ward`
- `SA-002` — `Crimson Thread Substitution`
- `SA-003` — `Mirror Palace of Mnemosyne`
- `SA-004` — `Explosion`
- `SA-005` — `Guiding Light`
- `SA-006` — `Levitation`
- `SA-007` — `Purify Water`
- `SA-008` — `Detect Poison`

These instances deliberately exercise different reusable semantic patterns:

```text
persistent bounded boundary controller
staged observation-guided reconfiguration
snapshot-consistent evidence acquisition + pure fusion
bounded one-shot dynamics
persistent radiative controller
bounded force controller
selective Matter transfer
observation + pure evidence classification
```

A future implementation SHOULD be able to add another spell using one of these contract families without modifying evaluator/runtime core dispatch. Unsupported contracts MUST continue to fail closed.

## File boundary

One spell instance equals one file. Shared schemas, registry contracts, profiles, implementation handlers, and tests may live elsewhere, but an instance definition MUST NOT be hidden inside a combined prose document or hard-coded only in evaluator/runtime source.
