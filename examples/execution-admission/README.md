# Explicit group representation fixture

This example compiles and passes structural admission. It intentionally does
**not** execute: the current evaluator/PREPARE returns
`UnsupportedExecutionAdmission` with no authoritative effects.

It uses an existing registered transition and a later pure calculation to
expose explicit partitioning, not to claim partial-commit or preflight support.
The numeric literals are TestFixtureOnly values. No water, gravity, fixture ID
or program name selects admission behavior.

```text
magical-language compile explicit-groups.mgls
magical-language check explicit-groups.mgls
magical-language run explicit-groups.mgls
```

Compilation/check must succeed; run must reject. Replacing the policy with
`WholePlanPreflight` is structurally valid and must still reject execution.
Do not delete the policy/group record to make a run pass: that requests
different atomicity, not an equivalent conversion.

Owner: [execution admission](../../reference/execution-admission.md).
The full matter/controller and non-water paired execution fixtures remain
mandatory follow-up under public Issue #23/public Issue #26.
