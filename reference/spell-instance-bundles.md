# Experimental Spell Instance Bundles

**Status:** experimental normative owner for SpellInstanceBundle artifact ingress. It is optional, does not change the four v1.0 required classes or 65 stable cases, and does not publish a stable ECIR.

## Ownership and DefinitionSource

This document owns the single-file envelope, loading phases, registry boundaries, and fail-closed diagnostics. Portable spell semantics remain owned by their domain references, including success-arcana.md and evidence-inference.md. Runtime PREPARE/COMMIT semantics remain owned by kernel-execution.md and security-sandbox.md.

schemas/artifact-envelope.schema.json and schemas/spell-instance-bundle.schema.json are the machine-readable owners. Canonical artifacts live under examples/spell-instances/; conformance/spell-instance-experimental.json is their non-stable inventory.

## Artifact contract

A bundle is a bounded UTF-8 JSON object with in-document artifact_kind = SpellInstanceBundle and artifact_version = 0. Its identity, suite label, scenario label, ingress, semantic/runtime contract identities, Registry extensions, profiles, WorldIndex evidence, initial WorldState/History, execution evidence, expectations, variants, provenance, and compatibility decisions are self-contained.

The filename, directory, suite ID, display name, and instance_id do not select executable behavior. Dispatch uses only explicitly registered (contract_id, revision) pairs. Renaming a file or instance therefore cannot change the selected handler/executor.

The only admitted frontend stage in version 0 is schema-valid NSR. Direct public SemanticAST, TypedMIR, KernelPlan, PreparedPlan, or multi-stage ingestion remains deferred to pre-public archive Issue #48.

## Phases

check strictly decodes the input path once, freezes an immutable admitted snapshot, performs schema validation, compatibility aggregation, embedded NSR validation, support-level verification, versioned semantic/runtime pair admission, executor-owned parameter validation, reference validation, and host-ceiling admission. It never mutates WorldState.

eval invokes the registered semantic handler after check. Internal SemanticAST/TypedMIR/KernelPlan records are implementation-owned report evidence; their presence does not establish a public serialized ECIR.

run admits only a Feasible/ConditionallyFeasible report, constructs the declared sandbox, performs PREPARE, revalidates current identity/Capability/Lease/accounting evidence, COMMITs atomically, and verifies expected outcome plus replay. Expected adversarial failures are successful conformance results only when their stable diagnostic, unchanged WorldRevision/History, and deterministic repeat match.

## Versioned registries

Artifact loaders, semantic handlers, runtime executors, and admitted semantic/runtime execution pairs are separate registries. Resolving each identity independently is insufficient: only an explicitly registered pair may proceed. Each executor owns a closed parameter schema. Duplicate registration, unknown kind/version/contract, invalid pair, missing/wrong/unknown parameter, and invalid record reference fail closed before PREPARE. A registered handler does not grant Identity, Capability, Lease, ownership, Truth, resources, or compatibility.

`registry_extensions` contains only bounded schema-validated declarative records in admitted namespaces. It cannot name/import executable code or mutate host registrations; host-owned registration code alone selects handlers and executors.

Shared envelope metadata does not imply a shared compatibility algorithm. Bundles carry decisions already produced by domain owners; the generic consumer only aggregates the required domains. A hash mismatch alone is never treated as a universal compatibility decision.

## Support level

implemented means the registered contract has the requested local evaluation/runtime evidence. recognized-unsupported means the semantic identity is known but evaluation deterministically returns Indeterminate / UnsupportedSemanticSubset. Unsupported contracts are not ignored, coerced, or treated as a successful no-op.

SA-001 through SA-004 are implemented experimental cases. SA-005 through SA-008 are canonical recognized-unsupported neighbors until their domain contracts are explicitly admitted. DEBUG-HELL-001 through 003 are adversarial evaluation/runtime fixtures. GENERIC-001 proves that the ingress and registry mechanism is not suite-specific.

## File and resource security

Ingress is strict UTF-8 without BOM and strict JSON:

- duplicate object keys, malformed/non-finite or host-magnitude-exceeding values, non-object roots, excessive bytes, parameter bytes, nesting, or node counts are rejected;
- symbolic-link input and absolute, URI-scheme, or parent-traversal external resource references are rejected;
- external network/resource loading is absent;
- an explicit caller-provided artifact kind must match the in-document kind;
- unknown future versions require an explicit loader and cannot silently fall back.

Host ceilings independently bound Energy, events, microsteps, concurrency, entities, History records, JSON size/depth/nodes, and parameter bytes. Artifact profiles may narrow but never raise those ceilings. `expected_outcome` is fixture/spec-owned truth: abort and non-executable expectations require diagnostics, committed expectations require non-empty invariants plus EventID or result-hash evidence, and empty objects/lists are never treated as wildcards.

The bundle is self-contained. Repository-owned reference files may define semantics, but an untrusted artifact cannot request arbitrary filesystem or network inclusion.

## Immutable execution boundary

The MKI data plane remains exactly:

    RESOLVE / OBSERVE / CHANNEL / TRANSFER / RECONFIGURE / CONSTRAIN

The lower World Kernel interaction classes remain exactly:

    QUERY / SAMPLE / TRANSITION / ACTIVATE / DEACTIVATE

No seventh MKI, generic SET, CREATE, HEAL, INFER, or RENDER is introduced. Scheduler, integrator, resolver query, inference, and renderer remain outside the MKI primitive set.

## CLI

The installed magical-language-artifact command accepts check, eval, and run, emits deterministic JSON, and can execute an arbitrary admitted file outside the repository checkout. magical-language-spell-instances runs the repository-owned experimental inventory.

## Non-goals

- promotion into the stable v1.0 required guarantee;
- changing WB-CANON-001 or the four stable classes;
- defining artifact content hashing;
- public stable ECIR or direct intermediate-stage ingress;
- inferring authority/identity/truth from metadata, confidence, relation, or CorrespondenceToken;
- changing historical spec/ snapshots.
