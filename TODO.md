# TODO.md — Persistent Project Queue / Roadmap

このファイルは、魔術言語仕様の**永続的な作業キュー・再開地点・release gate**を一元管理する。

- 仕様の正本: current `reference/`。
- historical snapshot: immutable `spec/`。
- 作業計画の正本: **この `TODO.md`**。
- cross-chat / Work / Codex / agent同期点: GitHub。
- last released version: **v1.0.0-rc.1**。
- pre-public archive compatibility marker: **pre-public archive Issue #36 — v0.8 Minimal Local Evaluator**。
- pre-public archive stabilization owner: **pre-public archive Issue #40 — v0.10+ Conformance / Stabilization**。
- pre-public all-open-issue sweep baseline: **`7257601cc19d73e394be98ad3b58115073cd8908`**。
- latest completed pre-public implementation: **pre-public archive Issue #94 / pre-public archive PR #135 / merge `d5ed0fae5570c8c5ada40533689246d82e2d1d09`**。
- completed pre-public architecture roadmap: **pre-public archive Issue #84 — MagicalProgram / MGLS common user workflow**。
- public migration baseline: **public `main` `46f366ddb221a1517c6545784b4614154423e1da`**。
- public hardening checkpoints: **public PR #5 merge `de9341aa288159067b2a6cf598d28ff850164815`; public PR #8 merge `b707ed3fa865f2b4aa190bc4975c37a391eb503b`; public PR #9 merge `2865e2513f1d3ca81f57832520638994a7a24724`; public PR #10 merge `dbdd51c8947487fdb7c2a2c104cc250b8c773eb4`; public PR #17 merge `82c3a42d169fe8e88cdc141eab23af24a44fe11c`; public PR #18 merge `0df7c42dfd741086cb0dcace040f69419f99acbb`; public PR #19 merge `105946c1315799cbfbf6c2a8b59df0bd7e67a4c3`; public PR #20 merge `01902409b7a844ac6b4d321411823a8525a96f0a`; public PR #21 merge `776395dbcde6a820b96a358d1085552331cd497c`**。
- active concrete work: **NEXT — public Issue #23 v1.0 execution-admission semantics; public Issue #3 final `v1.0.0` is blocked until public Issue #23 lands and the release gate is rerun**。
- release judgment: **v1.0.0-rc.1 finalized without waiver; final `v1.0.0` remains NOT AUTHORIZED; public Issue #23 intentionally reopens the pre-final semantic surface**。
- release/version state: **RC prerelease `v1.0.0-rc.1` / package `1.0.0rc1` published at merge `776395dbcde6a820b96a358d1085552331cd497c`; finalization `2026-08-12 00:16:14 +09:00` Asia/Tokyo; RC evidence cannot authorize final after public Issue #23 semantic changes**。
- final outcome order: **public Issue #15 → public Issue #16 → public Issue #1 audit → public Issue #2 RC → public Issue #23 execution-admission semantics → renewed exact-main release audit / new RC decision as required → public Issue #3 final → public Issue #4 umbrella**。

> 会話とrepositoryが食い違う場合はcurrent `reference/`、current `main`、このTODO、relevant Issue/PR evidenceを照合してreconcileする。

---

# 0. RESUME POINT — 最初に読む

## Historical release-train order retained for integration

```text
pre-public archive Issue #36 v0.8 Minimal Local Evaluator
pre-public archive Issue #37 v0.9 Sandboxed Runtime
pre-public archive Issue #40 v0.10+ Conformance / Stabilization
pre-public archive Issue #38 v1.0.0-rc.N
pre-public archive Issue #39 v1.0.0 final
```

The issue numbers in this historical block belong to the pre-public archive. Current public tracking is public Issue #15 → public Issue #16 → public Issue #1 → public Issue #2 → public Issue #23 → renewed release gate → public Issue #3 → public Issue #4 below。

## Current checkpoint

ユーザーは2026-08-04に、本来の設計思想・過去要求・current `reference/`・current implementationを再監査し、不足Issueを新設したうえで**全Issueを依存順にautonomousに解決**するよう指示した。

2026-08-13、ユーザーは「v1.0までには殆どの仕様を詰め込みたい」と明示し、public Issue #23（whole-plan preflight vs incremental execution semantics）をpost-v1.0へ延期せず、**final v1.0.0前の仕様・実装blockerとして扱う**方針へ変更した。既存`v1.0.0-rc.1`はimmutableなrelease evidenceとして保持するが、そのRCのsurface freezeは今後の`main`を拘束するものではない。public Issue #23のmaterial semantic change後は、既存RC evidenceをfinal authorizationへ再利用せず、exact current `main`でrelease gateをやり直し、新RCが必要かを明示判断する。

pre-public archive Issue #82 / pre-public archive PR #75 / pre-public archive Issue #72の旧preflight/rehearsal evidenceはhistorical evidenceとして保持するが、MagicalProgram/MGLS実装拡張後のrelease判断には再利用しない。

### Completed correction / migration / source / integration chain

```text
pre-public archive Issue #110 architecture correction
  pre-public archive PR #111 merge d36588000413695f35c97d74e97539599496da30
pre-public archive Issue #90 phase 1 shadow foundation
  pre-public archive PR #113 merge 1a5cd48a9e696fde734f50fe87ba0da77c38f4d9
pre-public archive Issue #114 bounded typed structured values
  pre-public archive PR #115 merge f4065d646898f63b6ef8ad375bb82700bd91ae79
pre-public archive Issue #90 SA-003 evidence fusion
  pre-public archive PR #117 merge 4e65f974ffc5623e609a2a55731ac0c7ffa504cf
pre-public archive Issue #118 red-main correction / exact-head gate
  pre-public archive PR #119 merge 65f9707681958e4da30eb48a5d28c0898ab6b9c5
  TODO reconciliation pre-public archive PR #120 merge fab87bda89f5d04e4d303ebd2394516246110c7b
pre-public archive Issue #90 SA-001 boundary reflection
  pre-public archive PR #121 merge 57b8f8d68e262c0986d251e75f1ed7dea1f513c1
pre-public archive Issue #90 SA-002 staged treatment
  pre-public archive PR #123 merge a166ba13b3b2f89562e523b304f14f8e383acb62
pre-public archive Issue #90 SA-004 bounded explosion
  pre-public archive PR #125 merge c27b13be5634712b54f982be298281f464641ba0
pre-public archive Issue #90 DEBUG-HELL + complete matrix
  pre-public archive PR #127 merge a85a5aedb0ac22e080ef69b615ae3913ccc3ad66
pre-public archive Issue #91 public MagicalProgram cutover + legacy executor retirement
  pre-public archive PR #129 merge 18c53d9a347db895fad3b93e2eac344ecec5c8a8
pre-public archive Issue #92 bounded human-authored MGLS-0 source contract
  pre-public archive PR #131 merge 1a3ae3ebac8db9b12f35a65f2931c3c971f7ad46
pre-public archive Issue #93 deterministic MGLS-0 parser / checker / compiler
  pre-public archive PR #133 merge 4f61fad2da979f8510ace372f70ec93e673e0a4e
pre-public archive Issue #94 unified CLI / diagnostics / docs / packaging / E2E conformance
  pre-public archive PR #135 merge d5ed0fae5570c8c5ada40533689246d82e2d1d09
pre-public archive Issue #84 MagicalProgram / MGLS architecture roadmap complete
```

### Exact completion evidence for pre-public archive Issue #94 / roadmap pre-public archive Issue #84

```text
PR                            pre-public archive PR #135
reviewed/current head         4c49e8d09e174825a0701012a11286e946172643
merge                         d5ed0fae5570c8c5ada40533689246d82e2d1d09
pre-public CI Repository regression run #394    SUCCESS / 32 schemas / 414 tests / diff check
pre-public CI Conformance package run #346      SUCCESS / editable + wheel + sdist
pre-public CI MagicalProgram runtime run #209   SUCCESS / editable + wheel + sdist
public command                magical-language check/eval/run/compile
user workflows                MGLS source + emitted program + repository bundle
installed command             editable / wheel / sdist outside checkout cwd
experimental E2E              UX-E2E-001..011 / excluded from stable manifest
replay                        source / program / bundle = Match
review threads / reviews      0 / 0
stable conformance            4 classes / 65 cases unchanged
released version              0.12.0 unchanged
```

pre-public archive Issue #94 / roadmap pre-public archive Issue #84 retained guarantees:

```text
routing                       one immutable snapshot + one selected decoder
selection                     decoded kind/version; filename/identity never dispatches
source                        verified MGLS-0 -> MagicalProgram-0
execution                     ordinary evaluator + PREPARE/COMMIT + replay
bundle                        canonical generic MagicalProgram path
output                        deterministic JSON envelope + fixed exit codes
security                      syntax/routing/compiler/source-map grant nothing
compatibility                 existing stable commands preserved
packaging                     repository = editable = wheel = sdist
stable surface                counts/version/historical snapshots unchanged
```

### Resume now

```text
public migration baseline     46f366ddb221a1517c6545784b4614154423e1da
last released RC              public Issue #2 / public PR #21 / merge 776395dbcde6a820b96a358d1085552331cd497c / v1.0.0-rc.1
new v1 blocker                public Issue #23 — explicit whole-plan preflight vs incremental execution semantics
current next                  design and implement public Issue #23 from exact current main
final release                 public Issue #3 remains blocked / NOT AUTHORIZED
release gate                  after public Issue #23 lands, rerun exact-main readiness audit and determine whether a new RC is required
```

The renewed audit that authorized `v1.0.0-rc.1`, public PR #21, exact-head gate, post-merge certification, and prerelease remain valid historical evidence for that RC. The 2026-08-13 user direction intentionally supersedes the prior "do not broaden frozen surface" instruction for work required by public Issue #23. Do not begin public Issue #3 from the old RC evidence. Resolve public Issue #23 first, then rerun the release gate on the resulting exact current `main`.

## Audit-start / post-merge public Issue inventory

```text
public stabilization / release / umbrella
  public Issue #1   renewed exact-main no-waiver release-readiness audit — GO / historical checkpoint for rc.1
  public Issue #2   v1.0.0-rc.1 — DONE / released
  public Issue #23  v1.0 execution-admission semantics — OPEN / NEXT / blocks final
  public Issue #3   v1.0 final release — BLOCKED until public Issue #23 + renewed release gate
  public Issue #4   v0.8 → v1.0 umbrella roadmap — closes after public Issue #3
```

## Dependency-correct execution order

```text
public Issue #15 tracker-reference qualification — DONE
public Issue #16 temporal/causal authority reconciliation — DONE
public Issue #1 renewed no-waiver audit for rc.1 — GO / historical checkpoint
public Issue #2 v1.0.0-rc.1 — DONE
public Issue #23 execution-admission semantics — NEXT
renewed exact-main release-readiness audit — REQUIRED after public Issue #23
new RC decision — REQUIRED after audit if material change demands it
public Issue #3 final release — BLOCKED / NOT AUTHORIZED
public Issue #4 umbrella closure — after v1.0
```

## Stable boundaries preserved throughout the sweep

```text
SemanticFingerprint != artifact content_hash
release version != compatibility oracle
migration success != admission
Evaluation != Execution
PREPARE success != COMMIT permission
Source semantics != PlanningAssumption
PlannerPrediction != RuntimeSafetyGuarantee
Reference != Identity != Authority
WorldIndex != WorldState
portable requirement != host evidence record
output declaration != committed identity
legacy oracle != generic implementation
structured data != executable payload
source language != runtime IR
source declaration != host authority/resource/evidence
compiler success != program admission
extension hint != decoded kind/version
CLI routing != semantic or runtime dispatch
same semantic dispatch != same occurrence identity
```

```text
current released stable classes   4
current released stable cases     65
pre-public RC requirement claims  14
MKI data-plane operations          6
World Kernel interaction classes  5
```

public Issue #23 MUST preserve the six MKI data-plane primitives, mandatory authority / Lease / conservation / identity / safety boundaries, and immutable historical snapshots. Any v1.0 stable-surface count change introduced by public Issue #23 must be explicit, evidence-backed, synchronized across conformance/reference/tests, and re-audited before a new RC/final release.

---

# 1. Operating rules

## 1.1 New work

1. Read this RESUME POINT。
2. Read the relevant current `reference/` owner。
3. Read the owning Issue and exact current `main`。
4. Create a dedicated branch from that exact baseline。
5. Keep important decisions/checkpoints in GitHub, not only in chat。
6. Use `AGENTS.md` / `WORKFLOW.md` for executor-neutral procedure。
7. Run focused tests, repository regression, package smoke, and runtime smoke。
8. Verify all required workflow names on the current PR head with the exact-head merge gate。
9. Reconcile this TODO and the owning Issue after each landing。

## 1.2 Interruptions

Before switching tasks, record branch/PR/head, next action, and return point in this TODO or the owning Issue。

## 1.3 “Todoに追加して”

このprojectに関する依頼なら、原則としてroot `TODO.md`への追加・更新を意味する。会話memoryだけへ未完了課題を残さない。

## 1.4 Release/version gate

Before any version update:

- [ ] all open non-release implementation/roadmap Issues completed;
- [ ] renewed no-waiver readiness audit completed on exact current `main`;
- [ ] explicit user confirmation for the specific version task after that audit;
- [ ] all relevant semantic owners re-read;
- [ ] open blocker inventory re-audited;
- [ ] repository regression green;
- [ ] required conformance green;
- [ ] editable/wheel/sdist package and runtime smoke green;
- [ ] README / CHANGELOG / schemas / examples / grammar / reference / tests / conformance artifacts synchronized;
- [ ] immutable target `spec/` snapshot prepared;
- [ ] consistency report updated;
- [ ] `git diff --check` green;
- [ ] reviewed head SHA equals current PR head SHA;
- [ ] exact-head merge gate passes all required workflows.

After release/version landing:

- [ ] verify exact merge SHA;
- [ ] run post-merge consistency/package checks;
- [ ] record Asia/Tokyo finalization timestamp at second precision;
- [ ] update this RESUME POINT;
- [ ] preserve historical snapshots;
- [ ] close/reconcile owning Issues only after evidence is recorded.

## 1.5 Priority of evidence

```text
current user instruction
  > current normative reference
  > reconciled TODO / owning Issue
  > current main / PR / CI evidence
  > workflow/handoff guidance
  > conversational memory
```

---

# 2. Active issue sweep

```text
PRE-PUBLIC DONE: pre-public archive Issue #46 pre-public archive Issue #77 pre-public archive Issue #84 pre-public archive Issue #86 pre-public archive Issue #87 pre-public archive Issue #88 pre-public archive Issue #89 pre-public archive Issue #90 pre-public archive Issue #91 pre-public archive Issue #92 pre-public archive Issue #93 pre-public archive Issue #94 pre-public archive Issue #110 pre-public archive Issue #114 pre-public archive Issue #118
PUBLIC DONE:     public Issue #15 / public PR #17; public Issue #16 / public PR #18
RC1 DONE:        public Issue #2 / public PR #21 / v1.0.0-rc.1 prerelease
V1 BLOCKER:      public Issue #23 execution-admission semantics — NEXT
FINAL BLOCKED:   public Issue #3 requires public Issue #23 + renewed exact-main release gate + explicit authorization
FINAL UMBRELLA:  public Issue #4 closes after v1.0 and handoff
```

## 2.1 pre-public archive Issue #90 true shadow migration — DONE

- [x] complete 12-contract matrix and 33 external-golden evaluations;
- [x] GENERIC-001, SA-001..004, DEBUG-HELL-001..003, recognized-unsupported SA-005..008;
- [x] independent frozen legacy oracle, rollback, replay, authority, identity, accounting;
- [x] no fixture/suite/name dispatch or opaque executable tunnelling;
- [x] installed editable/wheel/sdist matrix and exact-head gates.

## 2.2 pre-public archive Issue #91 public cutover — DONE

- [x] complete current MagicalProgram suite is the public SpellInstance path;
- [x] dedicated success/debug executors retired from production dispatch;
- [x] legacy executor retained only behind explicit test/oracle API;
- [x] public API/CLI and installed packages use generic execution for all 12 bundles.

## 2.3 pre-public archive Issue #92 source contract — DONE

- [x] bounded `.mgls` grammar, values, bindings, contracts, obligations, outputs;
- [x] deterministic source -> MagicalProgram-0 lowering and source-map contract;
- [x] source spans, diagnostic ownership, limits, compatibility, no-import boundary;
- [x] 2 positive and 15 negative implementation-ready cases.

## 2.4 pre-public archive Issue #93 compiler — DONE

- [x] strict UTF-8 normalization, bounded lexer/parser, deterministic source AST;
- [x] exact name/type/dimension/effect/obligation/resource/output checking;
- [x] deterministic MagicalProgram-0 and MglsSourceMap-0 emission;
- [x] independent semantic/source-map verification and target admission;
- [x] MGLS-NEG-001..015 fail closed with no partial program;
- [x] repository/editable/wheel/sdist determinism evidence.

## 2.5 pre-public archive Issue #94 integration / pre-public archive Issue #84 roadmap — DONE

- [x] compatibility-safe `magical-language check/eval/run/compile`;
- [x] existing stable and experimental commands preserved;
- [x] immutable single-read input and one-decoder decoded-kind routing;
- [x] deterministic common JSON envelope, stage diagnostics, exit codes;
- [x] source/program/bundle common post-lowering evaluator/runtime;
- [x] emitted program/source-map inspection with guarded output writes;
- [x] rename, mismatch, malformed, unknown contract, authority/resource/limit failures;
- [x] committed and deterministic-abort replay evidence;
- [x] current reference, README, CHANGELOG, consistency report, packaging synchronized;
- [x] UX-E2E-001..011 experimental conformance, stable 4/65 unchanged;
- [x] actual installed command verified outside checkout for editable/wheel/sdist;
- [x] version `0.12.0`, six MKI operations, five World Kernel classes, historical snapshots unchanged.

## 2.6 public Issue #15 tracker-reference qualification — DONE

- [x] qualify current live-document tracker references as public or pre-public archive;
- [x] preserve immutable historical `spec/` snapshots;
- [x] add a durable regression check for future ambiguous tracker references;
- [x] land exact-head CI evidence at head `f52c050bdd60a78a8808e76ae48348f507988ce8` and close public Issue #15 via public PR #17 merge `82c3a42d169fe8e88cdc141eab23af24a44fe11c`.

## 2.7 public Issue #16 temporal/causal authority reconciliation — DONE

- [x] reconcile the current normative owner with the retained v0.5 Restore/Rewind contract;
- [x] preserve `Replay != Rewind` and fail-closed authority/cycle validation;
- [x] decide and record v1 stable versus deferred conformance scope;
- [x] land exact-head CI at head `aaad4a425f4df9a56bfa762cc8ac0e5774673e08` and close public Issue #16 via public PR #18 merge `0df7c42dfd741086cb0dcace040f69419f99acbb`.

## 2.8 public Issue #1 renewed no-waiver release-readiness audit — GO (historical rc.1 checkpoint)

- [x] enumerate all open Issues and verify no implementation/roadmap blocker remains at that checkpoint;
- [x] re-read all 14 pre-public RC required-surface claims, tracked by public Issue #2, against exact main `0df7c42dfd741086cb0dcace040f69419f99acbb`;
- [x] re-read every current normative owner touched since the historical pre-public archive Issue #82/pre-public archive Issue #72 rehearsal;
- [x] verify four stable classes / 65 cases and experimental inventories remain correctly separated;
- [x] run repository regression, stable conformance, package, runtime, security, replay, and diff gates;
- [x] verify fresh checkout and installed editable/wheel/sdist command behavior outside checkout cwd;
- [x] verify version, README, CHANGELOG, schemas, grammar, examples, reference, conformance, consistency report, and TODO synchronization;
- [x] verify historical `spec/` snapshots remain immutable;
- [x] publish an exact-main GO report with no waivers in the consistency report and public Issue #1;
- [x] keep version, snapshot, tag, and release state unchanged at the public Issue #1 audit checkpoint.

This GO remains evidence for `v1.0.0-rc.1`; it MUST be rerun after public Issue #23 before final release.

## 2.9 public Issue #2 v1.0.0-rc.1 — DONE

- [x] explicit user confirmation received after public Issue #1 GO;
- [x] exact current public `main` baseline `01902409b7a844ac6b4d321411823a8525a96f0a` fetched into a dedicated branch;
- [x] stable surface frozen at 4 classes / 65 required cases / 14 required claims for this RC;
- [x] spec/conformance identity `1.0.0-rc.1` and PEP 440 package identity `1.0.0rc1` selected from the accepted preflight;
- [x] immutable `spec/v1.0.0-rc.1.md` prepared without rewriting older snapshots;
- [x] local full release gate green: 32-schema validation, 4 released classes / 65 required cases, 421 repository tests (`OK`, 3 environment-dependent skips), final wheel/sdist `1.0.0rc1` installed outside checkout with public CLI, runtime commit, replay, package-resource, and fail-closed smoke PASS;
- [x] exact PR head `7d4aaead644f558548320b26c44f7a40f761f9bf` passed 7/7 required workflows and an independent clean-head audit;
- [x] public PR #21 squash merge `776395dbcde6a820b96a358d1085552331cd497c` and post-merge package/consistency evidence recorded;
- [x] `v1.0.0-rc.1` prerelease published for exact merge `776395dbcde6a820b96a358d1085552331cd497c`;
- [x] Asia/Tokyo release finalization timestamp `2026-08-12 00:16:14 +09:00` recorded at second precision;
- [x] public Issue #2 closure is bound to the post-merge reconciliation evidence.

Historical RC rule: the `v1.0.0-rc.1` artifact itself remains frozen and immutable. The 2026-08-13 user direction permits new v1.0-targeted semantic work on `main`; such work means rc.1 can no longer serve as the sole final-release candidate evidence.

## 2.10 public Issue #23 explicit whole-plan preflight vs incremental execution semantics — NEXT / V1 BLOCKER

- [ ] re-read `reference/architecture.md`, `reference/feasibility.md`, `reference/kernel-execution.md`, `reference/planning-inference.md`, `reference/canonical-water-ball.md`, relevant schemas/tests, and exact current main;
- [ ] define local admission/commit safety separately from optional whole-plan completion preflight;
- [ ] preserve mandatory type / identity / authority / Capability / Lease / conservation / accounting / runtime safety checks;
- [ ] define incremental partial-commit semantics without fake rollback of authoritative world effects;
- [ ] define active `CONSTRAIN` termination so already-transferred matter remains and ordinary world dynamics resume;
- [ ] define representation/ownership of execution-admission policy and whether `Incremental`, `Preflight`, `Atomic` names/defaults are appropriate;
- [ ] add paired water-ball regression fixtures for partial-progress failure vs explicit preflight rejection;
- [ ] synchronize reference/schema/examples/traceability/tests/diagnostics;
- [ ] run focused + repository regression + package/runtime smoke + consistency checks;
- [ ] land through dedicated branch/PR with exact-head gates;
- [ ] reconcile this TODO and public Issue #23 after landing;
- [ ] rerun release-readiness audit on exact `main` after public Issue #23 and explicitly decide whether to cut a new RC before Issue #3.

public Issue #23 is a planning/control-plane semantic refinement and MUST NOT add a seventh MKI data-plane primitive or weaken existing mandatory safety/authority boundaries.

---

# 3. Stable foundations and historical integration markers

## 3.1 Completed foundations

```text
DONE(contract + v0.8 implementation) — pre-public archive Issue #34 / pre-public archive Issue #36
estimator model/profile ownership contract + deterministic synthetic profile
水球生成をcanonical end-to-end例として仕様化
canonical pathの仕様rule ↔ stable test/fixture ID traceability matrix
```

- source / NSR / SemanticAST / TypedMIR / KernelPlan / PreparedPlan separation;
- type/dimension, identity, authority, Lease, conservation/accounting;
- Unknown / Estimate / PlanningAssumption separation;
- resolver / WorldIndex / WorldState boundary;
- six MKI data-plane primitives and five lower interaction classes;
- reference Latin source and deterministic evaluator/sandbox runtime;
- versioned conformance manifest and expected-truth ownership;
- deterministic MGLS-0 compiler and experimental unified user workflow.

## 3.2 v0.8 public input boundary

The v0.8 public input boundary consists of:

- reference `LanguageAdapter<lat>` path;
- schema-validなNSR JSON direct ingress。

SemanticAST and TypedMIR remain implementation-internal stages and are **stableな外部direct-entry contractとはしない**。Broader **multi-stage direct ingestion** belongs to **pre-public archive Issue #48** and later experimental/public contracts。MGLS / MagicalProgram / SpellInstanceBundleの`magical-language` workflowはexperimental additive surfaceであり、このstable境界を変更しない。

## 3.3 Historical snapshot checkpoint

Historical `spec/` snapshots remain immutable. The retained checkpoint timestamp is:

```text
2026-07-29T05:35:45+09:00
```

---

# 4. Deferred research backlog

## Experimental breadth

- additional DEBUG-HELL variants beyond `001..003`;
- additional Experimental-Arcana semantics and stable-promotion proposals;
- production controller/evidence-store/distributed-runtime implementations.

## Language/representation

- **DEFERRED(non-reference adapter breadth)**: `lzh`, `ger`, `jpn`, `eng`, `zho` adapters/corpora;
- **DEFERRED(renderer/CLI breadth)**: per-language renderer and presentation breadth;
- round-trip semantic-equivalence suite;
- semantic-drift diff UI/CLI.

## World/runtime and physical breadth

- production WorldIndex storage/query/spatial engine;
- performance model and parallel deterministic execution;
- distributed runtime/persistence breadth;
- additional ObserverModels;
- detailed StructureSchema, isotope/nuclear precision, transport-limited kinetics, biological models.

## Formal/documentation/historical

- registry trait mechanization and formal proofs;
- stronger replay-equivalence formalization;
- additional normative/informative/rationale annotations;
- Magical Latin and 17th-century Neo-Latin review;
- Literary Chinese technical register;
- historical legacy spell profiles.

These remain **post-v1.0またはexperimental** unless separately promoted by evidence-backed scope decision. public Issue #23 has been explicitly promoted to the v1.0 blocking surface by the 2026-08-13 user direction.

---

# 5. Release evidence ledger

```text
v0.8   pre-public archive PR #52  Minimal Local Evaluator
v0.9   pre-public archive PR #53  Sandboxed Runtime
v0.10  pre-public archive PR #59  merge 90e47b7d71766272620e5f14f6304897a857d0a1
v0.11  pre-public archive PR #67  merge e79677d1706f3d05480cb230626856a8ef0b4224
v0.12  pre-public archive PR #74  merge 6d6ee23762456da6fe9e697d9f4742af09c4b447
v1.0.0-rc.1 public PR #21 merge 776395dbcde6a820b96a358d1085552331cd497c / prerelease tag v1.0.0-rc.1
Gate rehearsal pre-public archive PR #75 merge 191b8148b3daaaa48f7696dcddb893f9d4206e8f
SpellInstanceBundle pre-public archive PR #78 merge b177d92f6036fbb6d7c214cb9784de42cfc77fdd
MagicalProgram architecture pre-public archive PR #95 merge 822894e4c62a764c10ab965baa1b7077a8bd3990
open-issue sweep pre-public archive PR #103 merge d3f49a72a04f2f5cc5ea39f0acd9650bec25918a
golden parity pre-public archive PR #105 merge 4240bc82507b222d294d32c38c7a0998c4a3563f
artifact contract pre-public archive PR #106 merge 2c2e1348ea3513d51af39ac1bdd05f5cb2e3de78
evaluator pre-public archive PR #108 merge 2a13fb1941e73cdab8e3d8fc57298ec354d9de9a
runtime pre-public archive PR #109 merge a656d09425d11c7ac16fac918560e83afc764e6b
architecture correction pre-public archive PR #111 merge d36588000413695f35c97d74e97539599496da30
shadow foundation pre-public archive PR #113 merge 1a5cd48a9e696fde734f50fe87ba0da77c38f4d9
structured values pre-public archive PR #115 merge f4065d646898f63b6ef8ad375bb82700bd91ae79
SA-003 pre-public archive PR #117 merge 4e65f974ffc5623e609a2a55731ac0c7ffa504cf
red-main correction pre-public archive PR #119 merge 65f9707681958e4da30eb48a5d28c0898ab6b9c5
SA-001 pre-public archive PR #121 merge 57b8f8d68e262c0986d251e75f1ed7dea1f513c1
SA-002 pre-public archive PR #123 merge a166ba13b3b2f89562e523b304f14f8e383acb62
SA-004 pre-public archive PR #125 merge c27b13be5634712b54f982be298281f464641ba0
pre-public archive Issue #90 completion pre-public archive PR #127 merge a85a5aedb0ac22e080ef69b615ae3913ccc3ad66
pre-public archive Issue #91 public cutover pre-public archive PR #129 merge 18c53d9a347db895fad3b93e2eac344ecec5c8a8
pre-public archive Issue #92 MGLS source contract pre-public archive PR #131 merge 1a3ae3ebac8db9b12f35a65f2931c3c971f7ad46
pre-public archive Issue #93 MGLS compiler pre-public archive PR #133 merge 4f61fad2da979f8510ace372f70ec93e673e0a4e
pre-public archive Issue #94 unified workflow pre-public archive PR #135 merge d5ed0fae5570c8c5ada40533689246d82e2d1d09
```

Historical ledger entries do not authorize a release. public Issue #2 remains authoritative evidence for the immutable `v1.0.0-rc.1` artifact only. Final `v1.0.0` remains unauthorized and owned by public Issue #3, which is now blocked by public Issue #23 and a renewed exact-main release gate.
