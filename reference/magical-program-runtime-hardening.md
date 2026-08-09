# MagicalProgram Runtime Hardening Record

**Status:** historical correction record. Normative runtime behavior is owned by `magical-program-runtime.md`.

Issue #89 initially accumulated safety fixes through several subclass and entrypoint layers. The Issue #110 architecture audit retained the safety invariants but removed the layered implementation as a normative design.

## Retained invariants

- unique runtime-local PreparedPlan identity;
- single-use COMMIT;
- exact WorldRevision, entity revision, History, Capability, Lease, identity, evidence, and accounting freeze/revalidation;
- complete authoritative-state hashing;
- total rollback on executor, output, accounting, or trace failure;
- deterministic commit and abort replay;
- distinct repeated occurrence identities;
- no runtime-local plan handle in committed process state;
- no fixture/name dispatch.

## Corrected implementation boundary

There is now one public runtime class:

```python
from src.runtime.magical_program import MagicalProgramRuntime
```

The former `magical_program_verified`, `magical_program_public`, `magical_program_safe`, `magical_program_final`, `magical_program_release`, and entrypoint modules are compatibility re-exports only. Duplicate module/package name collisions were removed.

Executable contract behavior is registered in host-owned `RuntimeContractRegistration.executor`; the generic runtime core does not select behavior with contract-ID `if/elif` branches.

Portable requirements remain in the artifact. Exact host evidence exists only in the opaque PreparedPlan.

## Migration consequence

Issue #90 must not preserve the old executor by embedding a base64 SpellInstanceBundle in a generic program. A migrated spell must be explicit values, nodes, edges, outputs, and reusable host contract registrations. The old executor is an external frozen oracle only.
