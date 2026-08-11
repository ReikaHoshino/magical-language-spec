# SpellInstanceBundle Ingestion — Independent Re-audit

**Decision:** PASS for optional/experimental merge readiness, subject to final CI on the audit-evidence follow-up head.

**Repository:** `ReikaHoshino/magical-language-spec`

**PR:** pre-public archive Issue #78

**Issue:** pre-public archive Issue #80

**Main SHA / merge base:** `01c7113c85bf932396ebd81098a66ef3cd968e42`

**Audited implementation head:** `ef3edf5bff2074bc3fe4ea9d05eccc2f95f63cd5`

**Audit-evidence head before this update:** `3314d2e84894bdfcdd2c25999b0c905bd170674a`

**Audit timestamp:** `2026-08-02T15:38:00+09:00 (Asia/Tokyo)`

**Audit environment:** GitHub-hosted `ubuntu-24.04` runner, Ubuntu `24.04.4 LTS`, CPython `3.12.13`; editable, isolated wheel, and isolated sdist installations were exercised separately by the package workflow.

**Independence statement:** the original blocking review was performed against exact head `8c13f5737eca7cf81fc1772bc4e27cdbf19ad102`. This re-audit starts from that review's findings and independently rechecks current implementation, tests, schemas, package workflow, and stable-surface evidence rather than treating green CI as sufficient proof. No implementation claim is accepted solely because the implementation author reported it as fixed.

**Scope:** pre-public archive PR #78 / pre-public archive Issue #80 generic `SpellInstanceBundle` ingress and the optional Experimental-Arcana suites. This audit does not promote the work into stable v1.0 conformance, does not change the four stable classes or 65 required cases, and does not alter pre-public archive Issue #38 readiness.

## Commands and evidence sources

The exact-head workflows execute or cover the following repository commands and checks:

```text
python -m pip install --requirement requirements-dev.txt
python tests/validate_schemas.py
python -m unittest discover -s tests -v
python tools/run_conformance.py
python tools/run_spell_instances.py
git diff --check <main>...<head>
```

The package matrix separately builds and installs editable, wheel, and sdist forms, then runs installed entry points from a repository-external temporary working directory. `tools/package_spell_smoke.py` verifies package-owned resources, six positive bundles, renamed filename and instance ID, and deterministic negative contract/number/JSON cases.

`python tests/validate_security_contract.py` is listed by the remediation request as a normal validation command, but no such file exists in the PR tree. Security-contract coverage is instead provided by `tests/test_spell_instance_security.py`, `tests/test_success_arcana.py`, `reference/security-sandbox.md`, and the package smoke workflow. This audit does not claim execution of a nonexistent command.

## Result summary

```text
P0 open: 0
P1 open: 0
P2 merge-blocking: 0
P3 informational: 2
stable required classes: 4
stable required cases: 65
historical spec snapshots changed: no
```

P3 informational findings:

1. The historical commit sequence was not rewritten to exactly four commits named A/B/C/D. Equivalent implementation separation is evidenced structurally by independent extension packages and current-tree generic-core tests; the PR must not claim exact historical four-commit compliance.
2. Final TODO/Issue landing reconciliation remains a post-merge task; pre-merge TODO must state READY FOR REVIEW while preserving pre-public archive Issue #38 as the return point.

## P0 re-audit

### P0-1 — semantic/runtime contract confusion and extension exception leakage

**Resolved.**

- `ExecutionContractRegistry` admits an exact semantic-contract/runtime-contract pair before evaluation or PREPARE.
- `RuntimeExecutorRegistry` validates contract-owned parameter schema and reference fields before PREPARE.
- unknown, missing, mistyped, out-of-domain, and cross-paired parameters fail with stable diagnostics.
- registered evaluator/runtime programming errors are contained as `ExtensionEvaluationFailure` / `ExtensionExecutionFailure` without traceback or partial mutation.

Evidence:

- `src/artifacts/execution_contract_registry.py`
- `src/runtime/executor_registry.py`
- `src/artifacts/spell_instance.py`
- `tests/test_spell_instance_security.py::test_semantic_runtime_pair_is_admitted_as_one_contract`
- `tests/test_spell_instance_security.py::test_parameter_schema_and_reference_fail_before_prepare`
- `tests/test_spell_instance_security.py::test_extension_programming_errors_abort_without_traceback_or_mutation`
- `tests/test_spell_instance_security.py::test_cli_boundary_wraps_keyerror_and_valueerror_without_traceback`

### P0-2 — TOCTOU through repeated file reads

**Resolved.**

`SpellInstanceService` decodes and admits a path once into immutable canonical bytes plus a source digest. Check, evaluation, PREPARE, COMMIT, expected-result comparison, and replay consume that admitted snapshot rather than reopening the path.

Evidence:

- `src/artifacts/spell_instance.py::AdmittedSpellInstance`
- `SpellInstanceService._admit_file`
- `SpellInstanceService.evaluate_admitted`
- `SpellInstanceService.run_admitted`
- `tests/test_spell_instance_security.py::test_run_decodes_path_once_and_uses_immutable_admitted_snapshot`

The regression replaces the same path and expected outcome during the first load and proves one load call plus execution of the admitted original. Symlink input is rejected where the platform permits symlink creation.

## P1 re-audit

### P1-1 — SA-004 was not an Explosion implementation

**Resolved.**

SA-004 carries an explicit `dynamics.explosion@1` / `runtime.explosion@1` contract with bounded region, authoritative medium-model revision, radius and duration, pressure/thermal allocation, prepare-bound affected entities, Capability/Lease/accounting evidence, finite Energy release, reaction impulse, activation/termination events, deterministic replay, and negative domain/accounting neighbors.

Evidence:

- `examples/spell-instances/success-arcana/SA-004.json`
- `src/extensions/success_arcana/handlers.py`
- `src/extensions/success_arcana/executors.py::explosion`
- `tests/test_success_arcana.py::test_explosion_is_bounded_accounted_and_prepare_bound`

Negative-neighbor evidence covers insufficient Energy, radius/domain bound, target-count bound, stale revision, revoked Capability, expired Lease, missing accounting sink, pressure bound, thermal bound, and prepare-bound target-set behavior.

### P1-2 — DEBUG-HELL fixtures were canned outcomes

**Resolved for the explicitly claimed experimental scope.**

- DEBUG-HELL-001 preserves pathological explicit water-ball constraints and omitted terminal semantics and reaches a non-committable planning result without rewriting source constraints.
- DEBUG-HELL-002 resolves competing selectors, freezes source/destination identities at PREPARE, injects a deterministic post-PREPARE change plus a nearer late candidate, forbids silent retargeting, revalidates revision/Lease, and aborts without mutation.
- DEBUG-HELL-003 sorts same-tick external events, executes a bounded self-triggering microstep chain with causal records and resource accounting, exhausts the profile-owned budget, requests emergency stop, and rolls provisional History/controller state back atomically.

Evidence:

- `examples/spell-instances/debug-hell/DEBUG-HELL-001.json`
- `examples/spell-instances/debug-hell/DEBUG-HELL-002.json`
- `examples/spell-instances/debug-hell/DEBUG-HELL-003.json`
- `src/extensions/debug_hell/handlers.py`
- `src/extensions/debug_hell/executors.py`
- `reference/debug-hell.md`
- `tests/test_success_arcana.py::test_debug_hell_executes_owned_adversarial_semantics`
- `tests/test_success_arcana.py::test_adversarial_abort_has_no_partial_commit_and_replays`

The claimed scope does not promote pre-public archive Issue #46 as globally complete and does not claim production planner, teleportation, or reactive-controller breadth.

### P1-3 — generic extension proof was coupled to SUCCESS-ARCANA

**Resolved in the current tree.**

`src/extensions/test_generic/` owns an independent semantic handler, runtime executor, parameter schema, and exact execution-pair registration. `GENERIC-001` can be renamed, including its instance ID, without changing dispatch, and the generic package does not import the SUCCESS-ARCANA executor.

Evidence:

- `src/extensions/test_generic/registration.py`
- `src/extensions/test_generic/handler.py`
- `src/extensions/test_generic/executor.py`
- `examples/spell-instances/generic/GENERIC-001.json`
- `tests/test_success_arcana.py::test_independent_generic_extension_does_not_import_suite_executor`
- `tests/test_success_arcana.py::test_filename_and_instance_id_do_not_select_handlers`

The remediation request asked for a historical four-commit A/B/C/D split and exact commit SHAs. The existing branch history was not rewritten into that exact form. The stronger current-tree property is verified: the independent extension owns its implementation and generic core contains no fixture/suite dispatch. This is recorded as P3 rather than falsely claiming exact commit-history compliance.

### P1-4 — artifact-authored limits and non-finite numbers

**Resolved.**

Strict decoding rejects malformed/non-UTF-8/BOM/duplicate-key/non-finite/extreme/oversize/deep/high-node-count input. Immutable host ceilings bound bytes, parameters, entities, History, Energy, events, microsteps, and concurrency independently of artifact-authored profiles.

Evidence:

- `src/artifacts/envelope.py`
- `src/artifacts/spell_instance.py::_enforce_host_ceilings`
- `tests/test_spell_instance_security.py::test_nonfinite_extreme_numbers_and_artifact_owned_host_limits_fail_closed`
- `tests/test_spell_instance_security.py::test_every_host_ceiling_is_independent_of_artifact_claims`
- `tests/test_spell_instance_security.py::test_actual_cli_security_matrix_is_json_only_and_deterministic`

### P1-5 — expected-outcome wildcarding

**Resolved.**

The bundle schema conditionally requires non-empty diagnostics for infeasible/indeterminate/aborted outcomes, `Sigma` and `H` invariants plus deterministic-abort replay for aborts, and meaningful final invariants plus event IDs or result hash for committed execution.

Evidence:

- `schemas/spell-instance-bundle.schema.json#/properties/expected_outcome`
- `tests/test_spell_instance_security.py::test_expected_outcome_cannot_use_empty_abort_truth_as_wildcard`
- `tests/test_success_arcana.py::test_all_repository_bundles_match_expected_outcomes`

Expected truth remains fixture/specification-owned; runners compare against it and do not update it from actual output.

## P2 disposition

- repository and PR test counts are synchronized to the exact-head CI result;
- DEBUG-HELL provenance points to `reference/debug-hell.md` and pre-public archive Issue #46;
- `test_core_contains_no_fixture_or_suite_dispatch` performs the prohibited-string implementation-file audit;
- `registry_extensions` is schema-whitelisted, bounded, non-executable data; unknown namespaces and executable selector fields fail closed, while owning extension handlers validate/consume admitted records where required;
- extension registration is repository-owned Python code only; an artifact cannot name a module, function, URI, or other executable resource to load code;
- no historical `spec/` path appears in the PR changed-file list.

## Security matrix

The actual CLI regression covers deterministic non-zero exit, JSON diagnostics, and no traceback for:

```text
malformed UTF-8              -> InvalidUTF8
BOM                          -> InvalidUTF8
malformed JSON               -> MalformedJSON
duplicate key                -> DuplicateJSONKey
1e999 / -1e999               -> InvalidJSONNumber
NaN literal                  -> InvalidJSONNumber
huge integer/decimal         -> JSONNumberMagnitudeExceeded
oversized file               -> ArtifactTooLarge
excessive depth              -> ArtifactNestingLimitExceeded
excessive node count         -> ArtifactResourceLimitExceeded
unknown artifact kind        -> UnknownArtifactKind
unknown artifact version     -> UnknownArtifactVersion
unknown semantic contract    -> UnknownSemanticContract
unknown runtime contract     -> UnknownRuntimeContract
invalid semantic/runtime pair-> ExecutionContractPairNotAdmitted
missing parameter            -> ExecutionParameterMissing
wrong parameter type         -> ExecutionParameterTypeMismatch
unknown parameter            -> ExecutionParameterUnknown
invalid entity reference     -> ExecutionParameterReferenceInvalid
absolute/traversal/URI field -> ExternalResourceForbidden
symlink input                -> InputSymlinkRejected where supported
file replacement             -> first immutable admitted snapshot retained
executor KeyError/ValueError -> ExtensionExecutionFailure
```

Pre-COMMIT and extension failures assert unchanged WorldRevision/History. Repeated CLI invocation asserts deterministic result and exit code.

## Explosion evidence

The SA-004 fixture and executor prove:

- finite 5,000 J release from an active ledger;
- finite 5 m radius inside a 10 m admitted domain;
- prepare-bound affected-entity IDs;
- monotonic linear radial attenuation;
- separate pressure and thermal Energy accounting;
- reaction impulse on the anchor;
- region, Capability, Lease, source revision, medium revision, pressure, thermal, target-count, and ledger revalidation;
- activation and termination events;
- deterministic committed replay and no-partial-mutation negative neighbors.

## DEBUG-HELL evidence

- `DEBUG-HELL-001` contains `1.0e9 kg`, `0.10 m`, high acceleration, duration, sphere preservation, and an omitted/Unknown terminal; explicit constraints remain unmodified.
- `DEBUG-HELL-002` binds concrete source/destination revisions, injects post-PREPARE authoritative changes and a nearer late candidate, and aborts without silent retargeting.
- `DEBUG-HELL-003` executes microsteps 0, 1, and 2, records causal/execution ordering and resource units, then fails at budget 3 with emergency-stop evidence and atomic rollback.

## Package evidence

For the audited implementation and audit-only heads, Conformance package smoke passed for:

- editable installation;
- isolated wheel installation;
- isolated sdist installation.

Each clean install runs from a repository-external temporary cwd and verifies package-owned resources. Installed entry-point coverage includes SA-001, SA-004, DEBUG-HELL-001..003, independent GENERIC-001, renamed filename, renamed instance ID, unknown contract, invalid semantic/runtime pair, `1e999`, and malformed JSON.

## Stable-surface evidence

```text
version: 0.12.0
stable classes: 4
stable required cases: 65
MKI primitives: 6
lower World Kernel interactions: 5
WB-CANON-001 exact regression: PASS
historical spec/ changes: none
pre-public archive Issue #38: READY / non-blocked
```

## Exact-head validation evidence

For implementation head `ef3edf5bff2074bc3fe4ea9d05eccc2f95f63cd5`:

- pre-public CI Repository regression run #153 — SUCCESS;
- schema/fixture validation — SUCCESS (27 schemas; 12 SpellInstanceBundle documents);
- repository unit regression — SUCCESS (268 tests, OK);
- `git diff --check` — SUCCESS;
- pre-public CI Conformance package smoke run #66 — SUCCESS.

For prior audit-evidence head `3314d2e84894bdfcdd2c25999b0c905bd170674a`:

- pre-public CI Repository regression run #155 — SUCCESS;
- pre-public CI Conformance package smoke run #68 — SUCCESS;
- compare `97319448f5ac7fb93343b4f269beb8b2be4a5d8c..3314d2e84894bdfcdd2c25999b0c905bd170674a` reports one commit and zero changed files;
- compare `ef3edf5bff2074bc3fe4ea9d05eccc2f95f63cd5..3314d2e84894bdfcdd2c25999b0c905bd170674a` reports only `planning/spell-instance-ingestion-audit.md` as a content change.

The commit produced by this audit update is documentation-only. Its exact-head CI must pass before the PR is returned to Ready for review.

## Final decision

```text
P0 = 0
P1 = 0
required implementation/security/package/stable-surface categories = PASS
historical four-commit formatting = not proven; disclosed as P3
post-merge reconciliation = pending by design
final decision = PASS subject to exact-head CI and TODO/PR metadata synchronization
```

pre-public archive Issue #80 may close when pre-public archive PR #78 lands. pre-public archive Issue #48 continues to own full typed multi-stage ingress. pre-public archive Issue #38 remains the authoritative next release task after this optional interruption is resolved.
