# DEBUG-HELL adversarial execution contracts

**Status:** experimental normative owner for the Issue #46 adversarial fixture series and Issue #90 MagicalProgram migration. These cases do not alter the four stable conformance classes, 65 stable cases, six MKI primitives, or five lower World Kernel interaction classes.

## Ownership and non-goals

Issue #46 owns the three scenario meanings. `spell-instance-bundles.md` owns generic ingress and admission; `planning-inference.md` owns Unknown and PlanningAssumption; `kernel-execution.md` and `security-sandbox.md` own PREPARE, COMMIT, rollback, scheduler, and emergency-stop boundaries. `magical-program-shadow-migration.md` owns the common differential rules and external frozen-oracle role.

This document does not authorize direct intermediate-stage ingress (Issue #48), invent authority from WorldIndex/Relation metadata, turn a deterministic failure into a successful world effect, copy adversarial host events into portable syntax, or dispatch by DEBUG fixture names.

## Common migration boundary

The three DEBUG cases are selected only by their exact versioned semantic/runtime contract pairs:

```text
debug.pathological-planning@1  / no runtime
debug.prepare-bound-transit@1  / runtime.prepare-bound-transit@1
debug.reactive-budget@1        / runtime.reactive-hydra@1
```

All three consume the same frozen source bytes as the legacy oracle and satisfy independently owned expectations in `conformance/magical-program-golden-parity.json`. Embedded `expected_outcome` is not an oracle.

The generic contracts use the normal MagicalProgram type/lowering, PREPARE/COMMIT, atomic rollback, and replay mechanisms. Contract-specific trusted code may model the adversarial event itself, but it does not bypass the common runtime, grant authority, import artifact-named code, or select behavior from path, filename, suite ID, or instance ID.

## DEBUG-HELL-001

The input carries explicit `mass = 1e9 kg`, `radius = 0.1 m`, acceleration, duration, and sphere-preservation constraints plus an Unknown/omitted terminal. The evaluator preserves those source values exactly, computes the out-of-domain density and mechanical demand without clamping, keeps gravity/control accounting distinct from mechanical work, and records that no terminal PlanningAssumption was adopted. Missing Capability/Lease cannot be synthesized from feasibility, estimates, or a later unrelated entity. The diagnostic is derived from the retained constraint/evidence path, not selected solely by the fixture ID.

### MagicalProgram representation

The portable evaluator-only program contains:

- `record:PathologicalPlanningModel`, whose density ceiling and no-rewrite policy must exactly match the host registration;
- `record:PathologicalConstraints`, containing the explicit source Mass, radius, acceleration, duration, sphere-preservation requirement, and Unknown terminal marker;
- one `debug.pathological-planning@1` analysis node;
- no runtime, no authority requirements, no WorldState mutation, and no arbitrary entity binding.

The host-owned evaluator first runs common MagicalProgram validation and lowering, then publishes the retained analysis as typed evidence and returns `Infeasible` with `PlanningAssumptionCannotSatisfyAuthority`. It records that explicit constraints were not rewritten, a PlanningAssumption was not adopted, feasibility is not authority, and no unrelated later entity was selected.

## DEBUG-HELL-002

The evaluator resolves “nearest professor named Marcus” and “my laboratory” deterministically and records concrete source/destination EntityIDs and state revisions under `PrepareBound`. A trusted registered adversarial hook changes the symbolic world after PREPARE: it adds a nearer Marcus, changes the originally bound source and destination revisions, and expires the Lease. COMMIT revalidation aborts on the original bound evidence. It never retargets the new Marcus, never treats WorldIndex evidence as authority, and never includes attached inventory without explicit authority. A Dynamic policy is a distinct explicit contract choice and is not silently inferred.

### MagicalProgram representation

Portable selectors contain semantic conditions—not concrete resolved IDs or revisions:

```text
source:      kind=Professor, name=Marcus, deterministic nearest distance
destination: kind=Laboratory, owner=current-user
```

PREPARE resolves both selectors and binds exact Capability, Lease, identity, and accounting records. A trusted `PrepareBoundInterpositionRuntime` injects the registered TOCTOU change strictly after PREPARE. It does not alter the selected PreparedProgramPlan or silently choose the late candidate. Normal COMMIT revalidation detects the changed source/destination identity or expired Lease and returns the legacy-owned `StaleReference` category. The common runtime restores the original world, History, ledgers, runtime/process state, and revision; replay reproduces the same deterministic abort.

## DEBUG-HELL-003

The Hydra controller receives three same-tick external events in deterministic EventID order. Each executed microstep emits a causally linked event that is placed at the front of the deterministic queue, creating a real self-exciting chain. Microsteps `0`, `1`, and `2` execute provisionally; exhaustion is reported at budget `3` with causal/execution ordinals, pending events, resource accounting, and emergency-stop intent. The transaction aborts and provisional WorldState/History changes roll back. Replay reproduces the same order, failure point, trace, and final configuration.

### MagicalProgram representation

External event IDs, target entity IDs, and event payloads are not copied into portable syntax. The host constructs a PREPARE-bound `ReactiveEventBatch` evidence record. Capability, Lease, identity, evidence, and accounting obligations are all bound through a resolved synthetic `ReactiveControllerAnchor` associated with the declared Controller identity; no host record is left unbound.

The portable program contains typed host-validated Hydra model and policy records. The registered executor consumes the frozen event batch in EventID order, emits three provisional causally linked microsteps, places each generated event at the front of the deterministic queue, records the pending queue and resource use, and raises `MicrostepBudgetExceeded` at the profile-owned limit. The common COMMIT transaction then rolls back every provisional Controller, History, ledger, runtime/process, and WorldRevision mutation. The adversarial trace remains evidence about the aborted attempt; it is not committed WorldState.

## Complete migration matrix

The current Issue #90 suite contains exactly 12 contract pairs:

```text
5 implemented                 GENERIC-001 + SA-001..004
3 adversarial                 DEBUG-HELL-001..003
4 recognized-unsupported      SA-005..008
```

`tools.package_program_shadow_smoke` executes this same matrix from `src.resources.resource_path`. The existing conformance package workflow invokes it for editable, wheel, and sdist installations outside checkout working directories. The golden manifest root is derived from the selected resource bundle, so installed runs use packaged canonical examples and expectations without network or source-checkout fallback.

## Security and extension boundary

DEBUG semantics are admitted only by explicit versioned semantic/runtime pairs and closed parameter schemas. Bundle `registry_extensions` are bounded declarative compatibility records: they must exactly match host registrations, may be inspected by an already registered trusted handler, and never import modules, register host code, grant Capability/Lease, or select an executor. Unknown namespaces and unsupported pairs fail closed before PREPARE.

The complete migration source audit rejects fixture/suite/name dispatch, embedded legacy payloads, base64 tunneling, and direct legacy executor calls. The legacy handlers/executors remain available only to the external frozen oracle until Issue #91 cutover.
