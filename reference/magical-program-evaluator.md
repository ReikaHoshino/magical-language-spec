# MagicalProgram Generic Semantic Evaluation and Lowering

**Status:** experimental normative owner after Issues #110 and #114.

**Input:** `MagicalProgram-0`.

**Boundary:** dry-run only. Evaluation never resolves host records, reserves resources, creates authority, appends History, or mutates WorldState.

## 1. Generic path

The evaluator dispatches only through exact host-registered program contract pairs.

```text
filename != dispatch
program_id != dispatch
suite or spell name != dispatch
portable requirement != host evidence
structured value != opaque payload
lowering evidence != PreparedPlan
ConditionallyFeasible != COMMIT permission
```

No branch may inspect SUCCESS-ARCANA, DEBUG-HELL, fixture IDs, display names, or filenames.

## 2. Sequence

```text
structural admission
  -> registry/profile compatibility
  -> immutable exact typed bindings
  -> deterministic pure evaluation
  -> first-class reference requests
  -> registered contract resolution
  -> portable requirement and minimum-resource validation
  -> MKI / World Kernel lowering evidence
  -> schema-valid FeasibilityReport
```

Failures are deterministic `Infeasible` reports with stable program locations.

## 3. Typed bindings

Initial values retain literal, quantity, record, sequence, selector, or untrusted-hint type. Produced bindings are immutable and have one producer.

Structured signatures are exact:

```text
record:<type_id>
sequence:<element_type>
```

Examples include `record:EvidenceFusionModel` and `sequence:record:HypothesisScore`. A semantic contract cannot register an untyped `object`, `array`, `any`, or `*` input. Nested values are anonymous data; they do not create graph bindings or authority.

Record key order is not semantic because canonical serialization sorts object keys. Sequence order is semantic and preserved. Evaluation deep-copies structured values before exposing typed evidence.

Pure calculation, comparison, ranking, and assertion retain revision-0 behavior: quantities require exact semantic type, dimension, and unit; implicit unit conversion and quantity multiply/divide are not admitted. Structured values admit exact-signature equality/inequality only; arithmetic, ordering, and `pure.rank` fail closed.

## 4. First-class resolution

`ref.resolve` accepts a selector or untrusted reference hint and produces a typed `reference` request:

```text
resolution = Required
authority_granted = false
```

It lowers to `RESOLVE` / `QUERY` and makes the report conditional. PREPARE must realize the request into an exact entity ID and state revision. Downstream effect inputs are typed as `reference`; the effect does not receive the original selector.

## 5. Registered contracts

A semantic registration owns:

- exact ID/revision;
- instruction class;
- exact scalar, reference, record, or sequence input signatures;
- output kind;
- required portable-requirement categories;
- minimum Energy, Matter, and event declaration;
- an existing-six-MKI subset;
- an existing-five-lower-class subset;
- support level.

Initial registrations:

| Contract | Instruction | Inputs | Minimum events | MKI | Lower class |
|---|---|---|---:|---|---|
| `generic.transition@1` | `effect.invoke` | reference, string | 1 | `RECONFIGURE` | `TRANSITION` |
| `generic.observe@1` | `evidence.observe` | reference | 1 | `OBSERVE` | `SAMPLE` |

Resolution itself contributes `RESOLVE` / `QUERY` through its own node.

Unknown contracts, instruction mismatch, exact signature mismatch, untyped structured wildcard, or a seventh MKI operation fail closed.

## 6. Requirement validation

Evaluation checks requirement shape, target-binding type, mandatory categories, and contract minimum resources. It records:

```text
authority_granted = false
resources_reserved = false
host_records_bound = false
requires_runtime_revalidation = true
```

Exact host record IDs do not appear in evaluator output as if they were granted evidence. They are selected only by PREPARE.

## 7. Outputs

The evaluator checks output-kind compatibility with the referenced binding. `value` includes scalar, quantity, record, and sequence values. `event` and `artifact` declarations may point to a planned effect/evidence result, but they are not considered committed. COMMIT must bind and verify the actual identities.

## 8. Result status

- A pure program that passes all assertions is `Feasible`.
- A program containing resolution, observation, or effect requests is `ConditionallyFeasible`.

The report contains typed bindings, explicit lowering evidence, declared upper bounds, registry evidence, diagnostics, and `prepared=false` / `committed=false`. Its content digest uses finite canonical JSON: sorted object keys and preserved array order.

## 9. Non-mutation and security

Optional WorldState/History arguments exist only to verify observational non-mutation. The evaluator imports no artifact-named code and exposes no raw state path, dynamic plugin, network/filesystem operation, untyped object wildcard, or legacy payload tunnel.

## 10. Traceability

- resolution and conditional lowering: `test_effect_program_is_conditional_and_resolution_is_first_class`;
- observation event minimum: `test_observation_requires_one_declared_history_event`;
- pure typed evaluation: `test_pure_program_is_feasible_and_immutable`;
- structured exact signatures and canonical digest: `test_magical_program_structured_values.py`;
- type/unit/dimension diagnostics: `test_type_dimension_unit_and_operator_errors_have_locations`;
- registered contract failure: `test_unknown_and_mismatched_contracts_fail_closed`;
- portable monotonic obligations: `test_portable_obligations_are_monotonic_not_authorizing`;
- output compatibility: `test_output_declaration_must_match_binding_semantics`;
- rename independence and source audit: corresponding evaluator tests;
- installed execution: consolidated MagicalProgram package smoke.
