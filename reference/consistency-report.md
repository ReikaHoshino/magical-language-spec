# 整合性チェック報告 — v1.0.0-rc.1 historical release + current pre-final work

**Status:** **v1.0.0-rc.1 FINALIZED / NO WAIVERS as historical release evidence**; public Issue #23 current execution-admission work is unreleased; final `v1.0.0` remains unauthorized pending landing plus renewed exact-main release gate/new RC decision.

**Current unreleased implementation baseline:** post-public PR #24 `main` `018c678b3c611681e208a843cd44ebec271ab15d`.

**Renewed public audit baseline:** `0df7c42dfd741086cb0dcace040f69419f99acbb`

**Historical pre-public preflight baseline:** `b1bfd46899ce063d1c9985c213a01163618958ef`

**Historical pre-public preflight merge:** `e9c83c48afc374772af45310a1d141f218b4f262`

**Historical release target:** `v1.0.0-rc.1` / Python package `1.0.0rc1`.

**RC finalization timestamp:** `2026-08-12 00:16:14 +09:00` Asia/Tokyo.

> Sections 1–13 preserve the detailed pre-public preflight and integration evidence. They do not override the renewed public verdict recorded at the top of this document and in the final public-audit checkpoint below.

## 1. Scope and source of truth

Audited sources:

- current `reference/`;
- immutable historical `spec/` snapshots through `spec/v0.12.0.md` plus the new RC snapshot `spec/v1.0.0-rc.1.md`;
- schemas, examples, grammar, data, conformance artifacts, tests, and reference implementation;
- README, CHANGELOG, root TODO, planning documents, package metadata, and GitHub workflows;
- pre-public archive Issue #38 release-candidate gate;
- pre-public archive Issue #82 acceptance criteria;
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

The release branch synchronizes:

```text
package version        1.0.0rc1 (PEP 440)
conformance suite      1.0.0-rc.1
release target         v1.0.0-rc.1
latest immutable spec  spec/v1.0.0-rc.1.md
RC owner               public Issue #2
RC timestamp           2026-08-12 00:16:14 +09:00 Asia/Tokyo
```

pre-public archive Issue #82 did not assign `v1.0.0-rc.1`. The renewed public Issue #1 audit reached GO and the user explicitly confirmed public Issue #2 on 2026-08-11; the separately scoped task then completed the atomic identity, snapshot, exact-head gate, landing, prerelease publication, and post-merge certification.

No historical snapshot was modified by pre-public archive Issues #47, pre-public archive Issue #48, or pre-public archive Issue #82.

## 3. Frozen RC surface

The released RC surface is frozen exactly at:

```text
Core-1.0         29 required cases
Evaluator-1.0    10 required cases
Adapter-lat-1.0   6 required cases
Runtime-1.0      20 required cases
---------------------------------
total            65 required cases
```

`conformance/v1-required-surface.json` maps the 14 claims inherited from pre-public archive Issue #38 and released by public Issue #2 to these class/case IDs.

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

## 6. pre-public archive Issue #47 / pre-public archive Issue #48 reconciliation

pre-public archive Issue #47 / pre-public archive PR #98 established:

```text
source hint          *.mgls
JSON artifact hint   *.mga.json
optional stage hint  *.<stage>.mga.json
authority            in-document versioned envelope
```

pre-public archive Issue #48 / pre-public archive PR #99 established:

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

- pre-public archive Issue #38 — release owner;
- pre-public archive Issue #82 — preflight owner, now completed.

Other open work is final-release, retained experimental ownership, or planned post-v1.0 work. No separate P0/P1 blocker is waived.

```text
P0 findings = 0
P1 findings = 0
```

## 10. Historical pre-public archive Issue #38 gate result

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

Historical conclusion at that checkpoint: **GO TO SEPARATELY CONFIRMED `v1.0.0-rc.1` VERSION TASK.** This archived conclusion did not cut an RC and does not replace the renewed public verdict at the top of this report.

## 11. Verification evidence

### Pass 1

```text
head                              0b9c7d12390ce8c1bfdcc638b38e348b5bc8caf6
pre-public CI Repository regression run #190        SUCCESS
schemas / tests / diff             27 / 268 PASS / PASS
pre-public CI Conformance package smoke run #111    SUCCESS — editable / wheel / sdist
review threads / reviews           0 / 0
```

### Pass 2

```text
head                              508e2ba5612961ca67758c0a0f37db216c7a1e0b
pre-public CI Repository regression run #191        SUCCESS
pre-public CI Conformance package smoke run #112    SUCCESS — editable / wheel / sdist
review threads / reviews           0 / 0
version                             0.12.0
```

### Pass 3

```text
exact post-merge main              e9c83c48afc374772af45310a1d141f218b4f262
identical-tree certification head  cca08610525043b030bbb47c5b1f9cf31760cbfb
compare files                      []
pre-public archive PR #101 changed files              0
pre-public CI Repository regression run #192        SUCCESS
pre-public CI Conformance package smoke run #114    SUCCESS — editable / wheel / sdist
review threads / reviews           0 / 0
version                             0.12.0
```

pre-public archive PR #101 was closed without merge and made no persistent repository change.

Initial correction runs are not counted as passes. They found documentary/historical marker omissions and whitespace; all were corrected before Pass 1. No semantic/runtime blocker was found.

## 12. Historical integration checkpoints retained

These exact phrases remain part of repository compatibility evidence:

```text
Final pre-v0.8 integration audit — pre-public archive Issue #19
pre-v0.8 specification/readiness gate = PASS
next RESUME POINT = pre-public archive Issue #36
```

v0.8 input / canonical conformance clarification:

- selected structured NSR is canonical evaluator ingress;
- authoritative English provenance does not claim an implemented `eng` adapter;
- source→NSR reference conformance remains owned by the `lat` corpus;
- pre-public archive Issue #48はfuture architecture issueとして当時扱われ、current designはlanding済みだがhistorical v0.8 public contractを遡及変更しない。

## 13. Historical stop condition — satisfied

The historical stop required explicit user confirmation before versioning. That confirmation was received on
2026-08-11 for public Issue #2. It does not authorize final `v1.0.0`, experimental promotion, or bypass of exact-head and
post-merge gates.

---

## pre-public archive Issue #94 experimental unified user workflow consistency checkpoint

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
- experimental evidence remains outside `conformance/manifest.json` and does not satisfy stable pre-public archive Issue #38 claims by itself.

The prerequisites retained in this historical section are complete. Current release/version action is governed by public Issue #2 and root `TODO.md`; explicit confirmation has been received for this RC task only.

---

## Renewed public exact-main no-waiver audit — 2026-08-11

Status: **GO** for public Issue #1. It was not itself a version change; the subsequent explicit confirmation authorizes public Issue #2 only.

```text
public repository                  ReikaHoshino/magical-language-spec
exact audit baseline              0df7c42dfd741086cb0dcace040f69419f99acbb
audit evidence merge             public PR #19 / 105946c1315799cbfbf6c2a8b59df0bd7e67a4c3
public Issue #15                  DONE / public PR #17 merge 82c3a42d169fe8e88cdc141eab23af24a44fe11c
public Issue #16                  DONE / public PR #18 merge 0df7c42dfd741086cb0dcace040f69419f99acbb
open Issues at audit start        public Issue #1, public Issue #2, public Issue #3, public Issue #4
released identity                 v0.12.0 unchanged
stable conformance                4 classes / 65 cases unchanged
v1 required claims               14 / all mapped and tested
MKI data-plane operations         6 unchanged
World Kernel interaction classes  5 unchanged
historical spec snapshots         immutable
audit result                      GO / no waivers
RC tracker                        public Issue #2 / explicit user confirmation required
final tracker                     public Issue #3 / blocked by public Issue #2
umbrella tracker                  public Issue #4
release/version state             unchanged / no RC identity or timestamp
```

Public-suitability assertions:

- public history uses only GitHub noreply identity metadata and contains no high-confidence secret match found by the renewed full-history scan;
- no tracked symlink, file over 5 MiB, or current host-specific user path is present;
- public `main` is protected by exact required regression, editable-install, wheel, sdist, and runtime smoke checks;
- workflow tokens are read-only and third-party Actions are pinned to full commit SHAs;
- secret scanning, push protection, Dependabot security updates, and private vulnerability reporting are enabled;
- open Dependabot and secret-scanning alert counts were zero at audit time;
- `SECURITY.md` routes sensitive reports away from public Issues;
- the repository makes no open-source license grant; source visibility must not be confused with permission to reuse;
- current live documents explicitly qualify tracker namespaces as `public Issue/PR #N` or `pre-public archive Issue/PR #N`;
- public Issue #15 and public Issue #16 completed with exact-head CI and no remaining semantic prerequisite;
- the current temporal/causal owner preserves `HistoricalRef<T>` read-only semantics, `Restore != Rewind`, `Replay != Rewind`, and `Capability<History,Causality,Rewrite>`;
- unsupported Rewind execution remains outside the stable v1 four-class / 65-case surface and fails closed without inventing a runtime path;
- public Issue #1 through public Issue #4 own the release train; only public Issue #1 through public Issue #4 were open at audit start;
- the 14 machine-readable v1 claims are present exactly once and point only to required cases in the four stable classes;
- experimental Arcana, SpellInstance, and UX evidence remains outside the stable manifest and cannot satisfy stable claims by itself;
- local exact-baseline gates passed: 32 schemas, 421 tests with 3 environment skips, stable 65/65, Experimental-Arcana PASS, and 12 SpellInstanceBundle cases PASS;
- fresh editable, wheel, and sdist installs ran outside checkout; wheel/sdist resolved package-owned resources and passed security, runtime commit/abort, replay, and 12-bundle cutover smoke;
- exact-baseline post-merge Conformance package smoke and MagicalProgram runtime smoke succeeded; the audit evidence PR must also pass all seven protected checks at its exact head;
- `TODO.md` remains the authoritative RESUME POINT;
- no package version, stable conformance inventory, MKI/World Kernel count, RC identity, tag, release, or historical `spec/` snapshot changed in this audit.

Next RESUME POINT:

1. public PR #19, public Issue #1, and public PR #20 reconciliation are complete;
2. public Issue #2 is explicitly confirmed and owns `v1.0.0-rc.1`;
3. run the normal release gate on the exact RC PR head;
4. after landing, run post-merge certification, record the Asia/Tokyo finalization timestamp, and only then close public Issue #2/unblock public Issue #3.

---

## public Issue #2 RC synchronization checkpoint — 2026-08-11

```text
baseline                          public main 01902409b7a844ac6b4d321411823a8525a96f0a
spec identity                     v1.0.0-rc.1
Python package identity           1.0.0rc1
stable classes                    4 / released
stable required cases             65
v1 required claims                14 / source public Issue #2
MKI data-plane operations         6
World Kernel interaction classes  5
immutable RC snapshot             spec/v1.0.0-rc.1.md
historical snapshots              unchanged
experimental promotion            none
final v1.0.0                       not authorized / public Issue #3
finalization timestamp            2026-08-12 00:16:14 +09:00 Asia/Tokyo
```

The release branch recorded focused/full local gate results, exact PR head, all required workflow results, independent
audit, merge SHA, and post-merge package/consistency certification. No waiver converted a failed or missing gate into RC
readiness.

### Local release-branch gate

The pre-publication gate on the dedicated branch passed without a waiver:

```text
schema validation                  PASS / 32 schemas and all enumerated fixtures
stable conformance                 PASS / 4 released classes / 65 of 65 required cases
repository regression              PASS / 421 tests / 3 environment-dependent skips
wheel build and isolated install   PASS / 1.0.0rc1
sdist build and isolated install   PASS / 1.0.0rc1
installed public entry points      PASS / evaluator, artifact, workflow, conformance, experimental inventory
installed runtime and replay       PASS / canonical commit plus deterministic replay
installed resource boundary        PASS / package-owned resources and missing-resource fail-closed diagnostic
generated source-tree projection   absent after build
historical snapshots               unchanged; only the new RC snapshot was added
```

The installed-entry-point pass found and corrected one synchronization defect before publication: the stable Latin
evaluator still emitted the historical `0.8.0` report identity even though the distribution and conformance artifacts
were at RC. `src/evaluator/evaluator.py` now emits `1.0.0-rc.1`, and the repository regression asserts that identity.
This changes release metadata only; evaluator semantics, schemas, fixtures, and the frozen 4/65/14 surface are unchanged.

The exact published PR-head CI, clean exact-head audit, merge-SHA verification, post-merge certification, and prerelease
publication are complete. public Issue #2 closes with the reconciliation PR. public Issue #3 is the next release task but
requires separate explicit authorization; this RC evidence does not authorize final `v1.0.0`.

### Exact-head landing and post-merge certification

```text
public release PR                  public PR #21
reviewed/published head            7d4aaead644f558548320b26c44f7a40f761f9bf
exact-head protected checks        PASS / 7 of 7
independent clean-head audit       PASS / 32 schemas / 65 cases / 421 tests / 4 classes / 14 claims
squash merge                       776395dbcde6a820b96a358d1085552331cd497c
post-merge local gate              PASS / schemas / conformance / 421 tests / wheel / sdist
post-merge package workflow        run 31505529263 / SUCCESS
post-merge runtime workflow        run 31505529287 / SUCCESS
prerelease                         https://github.com/ReikaHoshino/magical-language-spec/releases/tag/v1.0.0-rc.1
tag target                         776395dbcde6a820b96a358d1085552331cd497c
historical snapshots               unchanged; spec/v1.0.0-rc.1.md added only
stable surface                     4 released classes / 65 required cases / 14 required claims
MKI / World Kernel                 6 / 5 unchanged
experimental promotion            none
RC finalization                    2026-08-12 00:16:14 +09:00 Asia/Tokyo
```

Next RESUME POINT: close public Issue #2 through this reconciliation, then stop before public Issue #3 until the user
explicitly authorizes final `v1.0.0`. public Issue #4 remains the final umbrella after the final release and handoff.

---

## public Issue #23 execution-admission implementation checkpoint — Unreleased

This current-reference checkpoint supersedes the old next-step wording above; it does not rewrite the historical
`v1.0.0-rc.1` verdict or any `spec/` snapshot.

```text
implementation baseline              post-public PR #24 main 018c678b3c611681e208a843cd44ebec271ab15d
policy modes                         Incremental / WholePlanPreflight
mandatory boundary                   LocalAdmission for every KernelAtomicGroup / later actuation
whole-plan preflight                  explicit, snapshot/model/profile-scoped assessment
preflight non-guarantees              no reservation / no authority grant / no runtime completion guarantee
incremental later failure             preserves prior WorldState/History commits
CONSTRAIN termination                 new lifecycle Event; not rollback; ordinary gravity applies
stable diagnostics                    WholePlanPreflightRejected / LocalAdmissionRejected / ContinuationInfeasibleAfterPartialCommit
MKI / World Kernel classes            6 / 5 unchanged
public serialized ECIR                none added
WB-CANON-001                           existing one-group behavior unchanged
stable RC surface                     4 classes / 65 cases / 14 claims unchanged pending renewed audit
historical snapshots                  unchanged
```

Normative ownership is centralized in `reference/execution-admission.md`. Architecture, feasibility,
planning-inference, kernel-execution, runtime-implementation, canonical-water-ball, and terminology link to that owner
without duplicating a conflicting policy. Machine-readable evidence consists of two paired semantic cases, a strict
execution-admission schema, rule traceability, additive fail-closed reference behavior, and focused positive/negative/replay tests.

This checkpoint is not a release authorization. After public Issue #23 lands, exact current `main` must rerun the full
no-waiver release gate and explicitly decide whether a new RC is required before public Issue #3.

Pre-publication local evidence on the dedicated branch:

```text
execution-admission focused tests     PASS / 10 of 10
schema validation                     PASS / 34 schemas / paired cases + traceability
repository regression                 PASS / 431 tests / 3 environment-dependent skips
stable conformance                    PASS / 4 released classes / 65 of 65 required cases
Experimental-Arcana                   PASS / 8 cases
SpellInstanceBundle                   PASS / 12 cases
checkout-external editable evaluator  PASS
checkout-external editable runtime    PASS / commit, abort, replay
checkout-external 12-bundle cutover   PASS
git diff --check                      PASS
```

Wheel/sdist installed-entry-point evidence remains an exact-head protected-PR gate and must be green before landing.
