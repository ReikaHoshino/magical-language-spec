# 整合性チェック報告 — v1.0.0-rc.1 preflight complete

**Status:** PASS / GO TO SEPARATELY CONFIRMED RC VERSION TASK.

**Preflight baseline:** `b1bfd46899ce063d1c9985c213a01163618958ef`

**Preflight merge:** `e9c83c48afc374772af45310a1d141f218b4f262`

**Released identity:** `v0.12.0` — unchanged.

**RC identity/timestamp:** not assigned.

## 1. Scope and source of truth

Audited sources:

- current `reference/`;
- immutable historical `spec/` snapshots through `spec/v0.12.0.md`;
- schemas, examples, grammar, data, conformance artifacts, tests, and reference implementation;
- README, CHANGELOG, root TODO, planning documents, package metadata, and GitHub workflows;
- Issue #38 release-candidate gate;
- Issue #82 acceptance criteria;
- open issue and PR inventory;
- three independent CI states.

Priority:

```text
current user instruction
  > current normative reference
  > reconciled TODO / owning Issue
  > exact main / PR / CI evidence
  > conversational memory
```

Required preserved boundaries:

```text
SemanticFingerprint != artifact content_hash
release version != compatibility oracle
migration success != admission
Evaluation != Execution
PREPARE success != COMMIT permission
```

## 2. Version and release identity

Current released identity remains synchronized at:

```text
package version        0.12.0
conformance suite      0.12.0
release target         v0.12.0
latest immutable spec  spec/v0.12.0.md
RC version             not assigned
RC timestamp           not recorded
```

Issue #82 did not assign `v1.0.0-rc.1`, create its snapshot, create a tag/release, or invent a finalization timestamp. Those writes belong to a separately confirmed atomic version task.

No historical snapshot was modified by Issues #47, #48, or #82.

## 3. Stable candidate surface

The stable candidate surface remains exactly:

```text
Core-1.0         29 required cases
Evaluator-1.0    10 required cases
Adapter-lat-1.0   6 required cases
Runtime-1.0      20 required cases
---------------------------------
total            65 required cases
```

`conformance/v1-required-surface.json` maps Issue #38’s 14 required claims to these class/case IDs.

Execution boundaries remain:

```text
MKI data plane =
  RESOLVE / OBSERVE / CHANNEL / TRANSFER / RECONFIGURE / CONSTRAIN

World Kernel interaction classes =
  QUERY / SAMPLE / TRANSITION / ACTIVATE / DEACTIVATE
```

No post-v0.12 work added a required class/case, MKI operation, or lower interaction class.

## 4. Normative ownership audit

Current owners exist for all required release domains:

| Domain | Current owner/evidence |
|---|---|
| scope and DefinitionSource | `scope-and-ownership.md` |
| conventions | `conventions.md` |
| architecture/layer separation | `architecture.md` |
| source/adapter/NSR | `language-adapters.md`, `source-text-normalization.md` |
| MIR/name resolution/type/effects | MIR/semantics/grammar/schema owners |
| registry and compatibility | `registry.md`, `compatibility.md` |
| v1.x deprecation/migration | `versioning-and-migration.md` |
| identity/resolution/WorldIndex | `world-index.md` and semantic owners |
| Unknown/Estimate/PlanningAssumption | `planning-inference.md` |
| estimator ownership | `estimator-models.md` |
| feasibility/evaluator | `feasibility.md`, `evaluator-implementation.md` |
| PREPARE/COMMIT/runtime | `runtime-implementation.md`, `kernel-execution.md` |
| scheduler/time/replay | `runtime-time.md`, runtime owners |
| sandbox/emergency stop | `security-sandbox.md` |
| conformance lifecycle/traceability | `conformance.md` and machine-readable artifacts |
| canonical end-to-end behavior | `canonical-water-ball.md` |

No required behavior is owned only by chat or untracked prose.

## 5. Experimental/deferred boundary

The following remain outside the v1.0 stable promise:

- Experimental-Arcana-0 and broader `success-arcana.md` work;
- DEBUG-HELL future variants/promotion;
- `SpellInstanceBundle` experimental ingress;
- `MagicalProgram` implementation/source compiler roadmap;
- `.mgls` / `.mga.json` naming implementation breadth;
- future typed multi-stage entry implementation;
- non-reference language adapters/renderers;
- production WorldIndex/distributed runtime;
- exhaustive chemistry/biology/nuclear/healing models;
- public ECIR;
- public direct SemanticAST/TypedMIR/KernelPlan/PreparedPlan files.

Their boundaries remain explicit:

- no stable conformance promotion;
- no stable CLI replacement;
- no historical snapshot rewrite;
- no authority/resource/truth creation from metadata or filename;
- no impact on the 65 required cases.

## 6. Issue #47 / #48 reconciliation

Issue #47 / PR #98 established:

```text
source hint          *.mgls
JSON artifact hint   *.mga.json
optional stage hint  *.<stage>.mga.json
authority            in-document versioned envelope
```

Issue #48 / PR #99 established:

- direct entry skips only preceding transformations;
- downstream type/identity/authority/accounting/PREPARE/COMMIT/sandbox/replay obligations remain mandatory;
- SemanticAST and TypedMIR remain implementation-owned;
- KernelPlan remains non-portable/profile-bound;
- PreparedPlan remains runtime-local and has no file form;
- multi-stage containers identify exactly one authoritative ingress;
- `nsr`, `bundle`, and `program` are advisory public-ingress tokens;
- `ast`, `mir`, `plan`, and `prepared` are unregistered.

These decisions do not change the stable candidate surface.

## 7. Compatibility and migration

`versioning-and-migration.md` defines:

- `RequiredCore`, `StablePublic`, `OptIn`, `Experimental`, and `ImplementationInternal` scopes;
- patch/minor/major change classes;
- deprecation lifecycle;
- exact source/target migration selection;
- target schema validation;
- post-migration compatibility re-evaluation;
- no compatibility/authority/trust inference from version, hash, or migration success.

Required Core cases exercise evolution, deprecation, migration success/failure/ambiguity, invalid output, authority non-generation, profile mismatch, and post-migration incompatibility.

## 8. Package and fresh-checkout boundary

The documented fresh-environment path remains:

```text
python -m pip install -r requirements-dev.txt
python -m pip install --editable .
magical-language-conformance
magical-language-conformance --class Core-1.0
magical-language-conformance --class Runtime-1.0
```

Package smoke validates:

- editable installation;
- isolated wheel and sdist installation;
- execution outside repository cwd;
- package-owned resource resolution;
- evaluator/runtime/conformance entry points;
- experimental artifact ingress without stable promotion;
- missing-resource fail-closed behavior;
- generated resource-copy cleanup.

## 9. Open blocker inventory

Final P0/P1 searches returned only:

- Issue #38 — release owner;
- Issue #82 — preflight owner, now completed.

Other open work is final-release, retained experimental ownership, or planned post-v1.0 work. No separate P0/P1 blocker is waived.

```text
P0 findings = 0
P1 findings = 0
```

## 10. Issue #38 gate result

| Gate | Result | Notes |
|---|---|---|
| 1. pre-RC v0.x gates remain green | PASS | Three independent validation passes. |
| 2. authoritative owners | PASS | Section 4. |
| 3. no chat/TODO-only P0/P1 blocker | PASS | P0/P1 = 0. |
| 4. conformance covers stable surface | PASS | 4 classes / 65 cases / 14 claims. |
| 5. fresh-checkout quickstart | PASS | Editable/wheel/sdist repeated. |
| 6. compatibility/deprecation policy | PASS | Normative contract plus required Core cases. |
| 7. repository artifacts synchronized | READY FOR VERSION TASK | Current v0.12 identity is internally synchronized; RC identity writes must be atomic after confirmation. |
| 8. unsupported domains explicit | PASS | Section 5. |
| 9. RC version/timestamp recorded | NOT STARTED BY DESIGN | Requires explicit confirmation and completion of the separate version task. |

Conclusion: **GO TO SEPARATELY CONFIRMED `v1.0.0-rc.1` VERSION TASK.** This does not claim that an RC has already been cut.

## 11. Verification evidence

### Pass 1

```text
head                              0b9c7d12390ce8c1bfdcc638b38e348b5bc8caf6
Repository regression #190        SUCCESS
schemas / tests / diff             27 / 268 PASS / PASS
Conformance package smoke #111    SUCCESS — editable / wheel / sdist
review threads / reviews           0 / 0
```

### Pass 2

```text
head                              508e2ba5612961ca67758c0a0f37db216c7a1e0b
Repository regression #191        SUCCESS
Conformance package smoke #112    SUCCESS — editable / wheel / sdist
review threads / reviews           0 / 0
version                             0.12.0
```

### Pass 3

```text
exact post-merge main              e9c83c48afc374772af45310a1d141f218b4f262
identical-tree certification head  cca08610525043b030bbb47c5b1f9cf31760cbfb
compare files                      []
PR #101 changed files              0
Repository regression #192        SUCCESS
Conformance package smoke #114    SUCCESS — editable / wheel / sdist
review threads / reviews           0 / 0
version                             0.12.0
```

PR #101 was closed without merge and made no persistent repository change.

Initial correction runs are not counted as passes. They found documentary/historical marker omissions and whitespace; all were corrected before Pass 1. No semantic/runtime blocker was found.

## 12. Historical integration checkpoints retained

These exact phrases remain part of repository compatibility evidence:

```text
Final pre-v0.8 integration audit — Issue #19
pre-v0.8 specification/readiness gate = PASS
next RESUME POINT = Issue #36
```

v0.8 input / canonical conformance clarification:

- selected structured NSR is canonical evaluator ingress;
- authoritative English provenance does not claim an implemented `eng` adapter;
- source→NSR reference conformance remains owned by the `lat` corpus;
- Issue #48はfuture architecture issueとして当時扱われ、current designはlanding済みだがhistorical v0.8 public contractを遡及変更しない。

## 13. Stop condition

**STOP before versioning.** The next action is to request explicit user confirmation for a dedicated `v1.0.0-rc.1` version-update task. Only that task may synchronize RC version identities, README, CHANGELOG, release notes, immutable snapshot, TODO, consistency report, and finalization timestamp.

---

## Issue #94 experimental unified user workflow consistency checkpoint

Status: implementation/reference/package integration checkpoint; **not a release or RC authorization**.

```text
source contract                    MGLS-0 / experimental
compiled target                    MagicalProgram-0 / experimental
bundle ingress                     SpellInstanceBundle-0 / experimental
public command                     magical-language check/eval/run/compile
input ownership                    immutable single-read byte snapshot
routing                            one decoder; decoded kind/version authoritative
filename                           advisory decoder/stage hint only
common envelope                    magical-language-workflow revision 0
exit codes                         0 success / 2 rejected / 3 aborted-or-FAIL / 4 internal
emission                           program + source map with guarded temporary replace
stable commands                    preserved
experimental E2E inventory         UX-E2E-001..011
stable conformance                 4 classes / 65 cases unchanged
MKI data-plane operations          6 unchanged
World Kernel interaction classes  5 unchanged
package version                    0.12.0 unchanged
historical spec snapshots          immutable
release judgment                   SUSPENDED per root TODO.md
```

Consistency assertions:

- MGLS source and its emitted program reach the same post-lowering evaluator/runtime and replay result;
- repository bundle input uses the canonical generic MagicalProgram translation/runtime path;
- explicit kind, registered suffix, decoded envelope, and revision disagreement fails closed without fallback;
- identity renaming cannot select semantics, while occurrence-derived event/process identities may legitimately change;
- diagnostics preserve pipeline stage order and retain the terminal runtime abort separately;
- editable, wheel, and sdist smoke invoke the actual installed `magical-language` console script outside checkout cwd;
- experimental evidence remains outside `conformance/manifest.json` and does not satisfy stable Issue #38 claims by itself.

The next release/version action remains gated by root `TODO.md`: complete #94/#84, run a renewed exact-main no-waiver audit, then obtain explicit user confirmation for the specific version task.
