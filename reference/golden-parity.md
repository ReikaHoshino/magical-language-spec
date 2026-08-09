# Independent Golden Expectations and Parity Harness

**Status:** Experimental normative contract for Issue #86 and current Issue #90 migration evidence.

**Owner:** `conformance/magical-program-golden-parity.json`.

**Stable v1.0 impact:** none; the required manifest remains four classes / 65 cases.

## 1. Purpose

The embedded `SpellInstanceBundle.expected_outcome` field is useful for fixture self-checking, but it is not an independent migration oracle. Executable input and an embedded expectation can drift together. Migration evidence therefore uses a separately owned golden manifest and a raw observation path that never reads the embedded expectation.

```text
executable artifact != expected-truth owner
observed output      != golden generator
self-consistency     != migration parity
```

## 2. Frozen input rule

Every comparison begins with one immutable byte snapshot. The harness records its SHA-256 digest and supplies the same bytes to each compared path. A filename, instance ID, later file rewrite, or second read cannot change the compared input.

A variant is produced by applying only the mutations written in the external golden manifest to a deep-decoded copy of that frozen snapshot. Variant expectations are not read from the bundle's `variants` or `expected_outcome` members.

## 3. Observation boundary

`src/artifacts/golden_parity.py::observe_frozen` performs:

```text
admit -> evaluate -> PREPARE -> COMMIT/abort -> replay -> final configuration
```

The observation contains admission, evaluation, execution, replay, and final `C=<Sigma,H,Omega,P>` evidence. The function deliberately does not read `expected_outcome`; changing that field alone cannot change an observation.

## 4. Comparison modes

- `exact`: identity-bearing or otherwise fully owned values must be equal.
- `subset`: the expected object is a recursively required subset; additional implementation evidence is allowed. Lists remain exact because order and multiplicity can be semantic.
- `contains`: every expected list item must occur in the observed list; additional items are allowed only where the owner selected this mode.
- `absent`: the path must not exist.

Every failure reports `GoldenSemanticMismatch` with the exact JSON Pointer, comparison mode, owner, expected value, observed existence, and observed value. Aggregate PASS/FAIL never replaces field-level evidence.

## 5. Identity and provenance policy

Event IDs, selected/winner IDs, artifact IDs, bound entity IDs, model/profile revisions, and provenance-sensitive identifiers are exact unless the golden owner explicitly records a migration rename. A rename is not inferred from similarity, ordering, hashes, or a successful execution.

Subset comparison is reserved for extensible records whose required semantic core is owned while additional non-conflicting evidence may be emitted. It cannot weaken an exact identity field.

## 6. Differential execution

`differential_compare` accepts two observation runners and one `FrozenArtifact`. It derives a temporary differential expectation from the old path only for old-vs-new comparison; this does not modify or replace the external golden owner. Release or migration acceptance requires both:

1. each path satisfies the external golden manifest; and
2. the selected differential fields agree or have an explicitly reviewed rename record.

## 7. Current required experimental cases

The manifest owns exactly:

```text
8 base expectations
25 mandatory negative variants
33 total independently evaluated cases
```

The eight base expectations are:

- `GENERIC-001`;
- SA-001 through SA-004 positive paths;
- DEBUG-HELL-001 semantic infeasibility;
- DEBUG-HELL-002 deterministic post-PREPARE stale-reference abort;
- DEBUG-HELL-003 deterministic microstep-budget abort and rollback.

The 25 variants remain the mandatory SA-001..004 negative neighbors declared at Issue #86 start. The manifest also owns committed replay, deterministic abort replay, abort atomicity, exact event IDs, SA-003 artifact/winner identity and artifact subset, and SA-004 affected/unaffected entity evidence.

Renamed filename/instance-ID behavior and synthetic event/winner/artifact drift are covered by separate mutation tests. The complete current MagicalProgram suite additionally proves 5 implemented, 3 adversarial, and 4 recognized-unsupported contract pairs across all 12 repository bundles.

## 8. Resource-bundle ownership

A selected golden manifest defines the root of its own canonical resource bundle. Input paths are resolved relative to that manifest root, not a hard-coded source checkout. Editable, wheel, and sdist installations therefore run against their packaged examples and expectations without network access or fallback to another checkout.

Changing the executable input and embedded expectation together still cannot satisfy an unchanged external manifest. Replacing the selected manifest is an explicit test-configuration act and never runtime authority.

## 9. Security and authority boundary

Golden data is test expectation, not runtime authority. It cannot grant Capability, create or renew a Lease, fabricate Identity or Truth, change host ceilings, select executable code, or mutate WorldState. The executable artifact still passes normal admission, compatibility, schema, authority, accounting, PREPARE/COMMIT, sandbox, and replay checks.

## 10. Migration and cutover use

Issue #90 registers the complete current MagicalProgram observation suite beside the legacy runner. Both consume the same frozen input snapshot and satisfy this independent manifest. Issue #91 may retire dedicated executors only after the complete 12-contract matrix, installed-package smoke, source-dispatch audit, and exact-head CI remain green. New fields require an owner and comparison mode; silently regenerating golden output from either runner is forbidden.
