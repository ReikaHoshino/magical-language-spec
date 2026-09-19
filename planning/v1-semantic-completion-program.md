# Current v1 semantic completion program — restart checkpoint

**Status:** planning and architecture-review evidence, not normative semantics,
not a completed whole-reference audit, and not release authorization.

## 1. Exact synchronization baseline

Verified from the public GitHub repository on 2026-09-19:

- repository: `ReikaHoshino/magical-language-spec`;
- public main: `018c678b3c611681e208a843cd44ebec271ab15d`;
- released RC: `v1.0.0-rc.1`; package: `1.0.0rc1`;
- public PR #27: OPEN, not draft, not merged;
- candidate branch: `agent/public-issue-23-execution-admission`;
- candidate head: `c0b87e32e16b61f80ad5aa56d220f6269a4d0e05`;
- open public Issues: public Issue #3, public Issue #4, public Issue #23,
  public Issue #25, public Issue #26;
- checkpoint branch: `agent/v1-semantic-completion-checkpoint`.

public Issue #25 comment `5277442908` requires public Issue #26 to close before
the umbrella. public Issue #23 comment `5277406714` requires integration with
the umbrella, not isolated admission semantics. These comments were fetched
alongside the current Issue bodies; old conversation SHAs were not used as
current evidence.

```text
public Issue #25 semantic completion
  + public Issue #23 execution admission / candidate public PR #27
  + public Issue #26 semantic genericity
  + remaining ownership/default/order/lifecycle/failure/diagnostic criteria
  + any focused child work created from confirmed gaps
then renewed exact-main no-waiver audit
then new-RC recommendation
STOP: separately authorized version/RC/final task
```

Root `TODO.md` owns lifecycle; this document owns the restart analysis and work
decomposition only. Numbered live trackers are always **public Issue/PR**;
pre-public archive numbers are a different namespace.

## 2. Interrupted reference-audit checkpoint

The earlier audit-only request was superseded by the explicit semantic
completion program. The initial inventory contains **54 current reference
documents / 16,391 lines**. A bounded scan of Markdown inline local links outside
fenced blocks found **107 links / zero missing file targets**. It did not validate
all bare-code paths, reference-style links, or anchor slugs and does not establish
cross-reference completeness.

Reading was divided across language, runtime, experimental, and release domains.
The independent passes stopped before their final reports; whole-reference
coverage and all preliminary findings are **not certified complete**. Do not
report the 54-document audit as finished. Re-read owners before adopting any
carry-over finding. No specification or historical snapshot was changed by that
interrupted audit.

Baseline checks on exact main:

| Check | Observed result | Boundary |
|---|---|---|
| `python tests/validate_schemas.py` | PASS, 32 schemas plus enumerated fixtures | Schema/fixture validity, not semantic completeness |
| `python tools/run_conformance.py` | PASS, 4 released classes, 65/65 cases | Released RC surface, not new umbrella criteria |
| `python -m unittest discover -s tests -v` | 421 tests, OK, 3 environment-dependent skips | Not a no-waiver release gate |
| editable/wheel/sdist outside checkout | Not rerun at this baseline checkpoint | Required for each semantic PR and final renewed audit |

## 3. Exact public PR #27 architecture review

Review target is the complete **22-file diff / 1,428 additions / 30 deletions**
from the main baseline to the candidate head above. All changed production,
schema, fixture, test, reference, and planning files were inspected. The review
does not adopt the branch as current specification.

### ADM-01 — P1: a second domain-specific runtime, not generic admission

- **Targets:** candidate `src/runtime/execution_admission.py` (AdmissionWorld,
  `_local_admission_failure`, `_apply_group`, `_terminate_constraint`),
  `schemas/execution-admission.schema.json` (`atomicGroup`, `world`),
  `src/runtime/__init__.py`, `reference/runtime-implementation.md`.
- **Problem:** the newly exported runtime requires mass-transfer, constraint,
  and gravity fields; it implements effects itself. It never delegates execution
  to current `MagicalProgramRuntime`, its registered executors, PREPARE host-record
  binding, or the existing World Kernel boundaries. A non-water Energy program
  cannot use the same contract without adopting unrelated mass/constraint fields.
- **Improvement:** retain the useful local-admission/preflight distinctions,
  replace this executable side path with group control in the existing runtime,
  and keep physical effects in existing registered domain contracts.
- **Semantic change:** required multi-group refinement, already scoped by
  public Issue #23; representation/compatibility choice remains explicit below.
- **Dependencies:** public Issue #25 atomicity/lifecycle ownership;
  public Issue #26 genericity; group-boundary decision.
- **Done when:** water/matter and structurally different non-water programs pass
  through the same evaluator/PREPARE/revalidation/registered-effect/commit/replay
  path for incremental and preflight policies, without domain fields in admission.

### ADM-02 — P1: declared MKI operations do not control admitted effects

- **Targets:** candidate `_validate_contract`, `_apply_group`, schema
  `atomicGroup.mki_operations`, `tests/test_execution_admission.py`.
- **Problem/evidence:** replacing both groups' `mki_operations` with `['OBSERVE']`
  still validates against the candidate schema and execution still transfers
  **40 kg** and activates/terminates a constraint. This was reproduced against
  the exact candidate module using an in-memory copy; production files were not
  changed. Enumerating six permitted names is not enforcement of their meaning.
- **Improvement:** bind execution to exact typed registered effect contracts;
  reject operation/effect mismatch before the group's first mutation.
- **Semantic change:** none to MKI meaning; implementation correction.
- **Dependencies:** ADM-01; public Issue #26 dispatch inventory.
- **Done when:** a mismatched operation declaration is rejected with no partial
  group effect, and unseen valid typed operations select the registered executor.

### ADM-03 — P1: successful plans and representative revalidation are unproved

- **Targets:** candidate `ExecutionAdmissionRuntime.execute`, `AdmissionWorld`,
  `_validate_contract`, schema `trace`, `tests/test_execution_admission.py`.
- **Problem/evidence:** the runtime always raises after all groups succeed;
  changing the second request from 20 kg to 5 kg reproduces the explicit
  "must exercise a failure boundary" exception. Trace status permits only
  `Rejected` and `PartialCommitTerminated`. Local guards use prefilled flags,
  not the existing PREPARE-bound authority/identity/Lease evidence. Neither a
  successful preflight followed by later drift nor generic success is tested.
- **Improvement:** use real existing runtime guards and define positive terminal
  outcomes, policy/profile evidence, stale-binding and post-preflight drift cases.
- **Semantic change:** successful/partial outcome contract refinement; no weakening
  of existing mandatory guards.
- **Dependencies:** ADM-01 and public Issue #25 failure/lifecycle matrix.
- **Done when:** success, first-group rejection, later-group rejection,
  post-preflight authority/resource drift, malformed inputs, and replay are
  independently tested using the same public path.

### ADM-04 — P1: termination mutates state outside local admission

- **Targets:** candidate `_terminate_constraint`, `_trace`,
  `reference/execution-admission.md` section 5, traceability rules 001/004.
- **Problem:** continuation failure directly switches the constraint off,
  increments WorldRevision, and appends a termination Event, without a separate
  admitted lifecycle operation or current settlement guard. The normative proposal
  itself says settlement remains subject to authority/accounting/local admission.
  `gravity_applies = true` demonstrates a flag, not subsequent world evolution.
- **Improvement:** route termination/settlement through the existing effect owner;
  distinguish removal of influence from any new accounted physical effect.
- **Semantic change:** clarify failure/settlement ownership; do not invent cleanup
  authority or gravity inside admission.
- **Dependencies:** public Issue #25 lifecycle/failure work and ADM-01.
- **Done when:** revoked authority, denied settlement, resource exhaustion,
  persistent-effect termination and post-termination world behavior have explicit
  outcomes/history; prior successful commits cannot be erased.

### ADM-05 — P2: completion/traceability overclaim

- **Targets:** candidate `TODO.md`, `reference/consistency-report.md`,
  `examples/execution-admission/traceability.json`, `tests/validate_schemas.py`.
- **Problem:** completion checkboxes and the next release-audit step omit
  public Issue #25/public Issue #26; two failure fixtures plus tests for a special-purpose
  class cannot establish the generic contract. Test locator checks establish
  method-name presence, not the semantic strength of each mapped assertion.
- **Improvement:** retain exact historical evidence, reopen unsupported claims,
  map all new rules to adversarial executable evidence, and reconcile the umbrella.
- **Semantic change:** none to runtime; planning/evidence correction.
- **Dependencies:** ADM-01..04; umbrella acceptance.
- **Done when:** every claim has sufficient exact-head evidence and no child or
  umbrella closure is inferred solely from green legacy conformance/CI.

**Disposition:** do not merge public PR #27 at the reviewed head. Prefer reworking
the existing PR, preserving its useful normative distinctions but replacing the
standalone fixture runtime. Keep it open until the replacement is reviewable;
do not close it as superseded without an actual replacement/checkpoint.

## 4. Required group-boundary decision

Current `reference/magical-program-artifact.md` sections 2/5 define a closed
revision-0 envelope with nodes/edges, but no source-authored atomic-group field.
`reference/magical-program-runtime.md` sections 1/5 and
`src/runtime/magical_program_commit.py` define **one program / one atomic COMMIT**.
An error restores the state before that program. In contrast,
`reference/kernel-execution.md:173-197` defines all-or-none *per semantic group*
without assigning a portable program-to-group partition.

The missing choice changes observable failure behavior, not just file layout.
It must not be filled by guessing groups from node order, fixture identity, or
source spelling.

| Option | Meaning | Consequence |
|---|---|---|
| A — accepted by the user on 2026-09-19 | Source/program explicitly declares group boundaries; unchanged inputs retain one atomic group. Existing runtime executes each admitted group. | Supports partial progress inside one spell; needs an explicit artifact/source compatibility contract, cross-group bindings, diagnostics, and replay. No new ECIR or second engine. |
| B | Host/profile composes multiple existing atomic programs only. | Smaller internal orchestration change; no in-source group boundary. Does not by itself satisfy arbitrary within-spell sequencing/partial progress; that remains child work. |

Neither option grants Capability/Lease, selects a physical model, implies whole-
plan reservation, or permits undoing prior committed groups. Source-explicit
requirements cannot be weakened by host policy. No new release/package version
or RC is authorized by selecting an option.

**Decision D-01:** the user explicitly selected option A. Implementation may add
explicit source/program group boundaries while preserving all existing ungrouped
inputs as one atomic group. Group partition must never be inferred from node
order, filename, or fixture identity. This selects the architectural approach;
it does not authorize release/version changes or weakening per-group guards.

## 5. Carry-over current-reference issues to reconcile

These are not closed by the candidate admission patch:

1. **P1 / atomicity owner ambiguity:** `reference/success-arcana.md:65-73` describes
   conceptual per-treatment-stage checkpoint/commit boundaries, while
   `reference/magical-program-shadow-migration.md:208-210` explicitly puts all
   three stages in one atomic COMMIT. It may be intended as a conceptual versus
   supported-subset distinction, but that mapping must be explicit. Decide
   whether separate-stage execution is a new admitted profile or a change to the
   fixture; preserve existing one-group behavior unless explicitly migrated.
   Done: late-stage failure fixtures distinguish intra-group restoration from
   preservation of earlier authoritative group history. Depends on the group
   decision and public Issue #25 lifecycle/failure work; semantic decision needed.
2. **P2 / stale work state:** main `README.md:7,64`,
   `reference/consistency-report.md:460-462`, and
   `reference/conformance.md:367-379` retain obsolete next-release instructions.
   Keep historical RC evidence intact but label it historical and link current
   work state to TODO. Done: no current entry point suggests the old RC unblocks
   final. Non-semantic, depends only on verified public tracker state.
3. **P1 candidate / source-target mismatch:** `reference/mgls-source-language.md`
   section 6.5 requires an ordered sequence input for `rank`, while
   `reference/magical-program-evaluator.md` rejects structured ranking. Re-read
   compiler/evaluator and reproduce before creating or resolving focused work;
   do not invent record/sequence ordering. Depends on the relevant owners, not
   execution admission. Done: every admitted rank example has one consistent
   source/target type contract and positive/negative regression evidence.

## 6. Phased completion plan

| Phase | Scope / files | Semantic change? | Dependencies | Completion evidence |
|---|---|---|---|---|
| 0 | TODO, this planning checkpoint, public tracker comments | No | Exact main/Issue/PR refresh | Public dependency graph includes umbrella and all children; interrupted audit saved; no false completion |
| 1 | Full public PR #27 diff + existing artifact/runtime/source owners | Review only | Phase 0 | ADM findings, reproduction, disposition, group-boundary decision recorded |
| 2 | Current kernel/runtime/artifact/source owners; existing evaluator/PREPARE/commit modules; schemas/fixtures/tests | Explicit group/admission refinement | Approved representation + phase 1 | Same engine passes matter and non-water success/incremental/preflight/drift/failure/replay; one-group compatibility retained |
| 3 | Production/shared `src/`, `tools/`, dispatch/constant inventory, metamorphic tests and bounded static guard | Corrections only where owner already specifies behavior | Phase 2; public Issue #26 | Rename/ID/reorder/numeric/unseen/context/path probes; legitimate registrations separated from prohibited dispatch; constants have owners |
| 4 | Source-to-WorldState ownership matrix; defaults/order/lifecycle/failure/atomicity/error owners | Scoped decisions, not silent defaults | Relevant phase 2/3 interfaces | All public Issue #25 criteria mapped; non-water different-type contextual binding; focused children resolved |
| 5 | Conformance/rule mapping; current docs; package/runtime validation | Explicit current-candidate scope only | Semantic PRs complete | Each reviewed exact head passes required regression/conformance/security/replay/editable/wheel/sdist gates; no old-head reuse |
| 6 | TODO, consistency evidence, public Issue #23/public Issue #26 then public Issue #25 closure | No new semantics | Landed exact evidence + all criteria | Children close only with proof; umbrella closes last |
| 7 | Fresh exact-main no-waiver readiness audit | No release action | All semantic blockers closed | GO/NO-GO and new-RC recommendation; stop before version/tag/release/public Issue #3 closure |

The normative stage matrix must cover surface source, normalization candidates,
selected NSR, SemanticAST, TypedMIR, planning/inference, KernelPlan, PreparedPlan,
Revalidate, COMMIT, active effects, and WorldState/History. For each, record
authoritative values, permitted Unknown/default/inference, binding/dynamic
behavior, owner, provenance, and failure boundary. This planning checklist is
not a substitute for that completed normative matrix.

## 7. Immediate next work and non-goals

1. Publish this planning-only reconciliation separately from semantic code.
2. Record the blocking architecture review on public PR #27/public Issue #25.
3. Implement accepted D-01 explicit group ownership, then rework public PR #27 within the existing
   runtime; do not land the candidate merely because its CI is green.
4. Build the second program family and adversarial guard/replay cases alongside
   implementation, not after declaring completion.
5. Complete the independent current-reference contradictions under focused child
   ownership; preserve broader interrupted-audit coverage as unfinished.

No seventh MKI primitive, sixth World Kernel class, public serialized ECIR,
historical snapshot rewrite, implicit rollback, inferred authority, version bump,
new RC, or final release is authorized. The old 4/65/14 RC counts are historical
facts, not a reason to exclude newly required v1 semantics from current evidence.
