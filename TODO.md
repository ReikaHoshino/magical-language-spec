# TODO.md — Persistent Project Queue / Roadmap

このファイルは、魔術言語仕様の**永続的な作業キュー・再開地点・release gate**を一元管理する。

- 仕様の正本: current `reference/`。
- historical snapshot: immutable `spec/`。
- 作業計画の正本: **この `TODO.md`**。
- cross-chat / Work / Codex / agent同期点: GitHub。
- last released version: **v0.12.0**。
- pre-public archive compatibility marker: **Issue #36 — v0.8 Minimal Local Evaluator**。
- pre-public archive stabilization owner: **Issue #40 — v0.10+ Conformance / Stabilization**。
- pre-public all-open-issue sweep baseline: **`7257601cc19d73e394be98ad3b58115073cd8908`**。
- latest completed pre-public implementation: **archive Issue #94 / PR #135 / merge `d5ed0fae5570c8c5ada40533689246d82e2d1d09`**。
- completed pre-public architecture roadmap: **archive Issue #84 — MagicalProgram / MGLS common user workflow**。
- public migration baseline: **public `main` `46f366ddb221a1517c6545784b4614154423e1da`**。
- public hardening checkpoints: **PR #5 merge `de9341aa288159067b2a6cf598d28ff850164815`; PR #8 merge/current audit baseline `b707ed3fa865f2b4aa190bc4975c37a391eb503b`**。
- active concrete work: **public Issue #1 — renewed exact-main no-waiver release-readiness audit**。
- release judgment: **SUSPENDED until the renewed no-waiver audit is complete**。
- release/version state: **unchanged at `0.12.0`; no RC snapshot/tag/publication/finalization timestamp exists**。
- final outcome order: **public #1 audit → public #2 RC → public #3 final → public #4 umbrella**。

> 会話とrepositoryが食い違う場合はcurrent `reference/`、current `main`、このTODO、relevant Issue/PR evidenceを照合してreconcileする。

---

# 0. RESUME POINT — 最初に読む

## Historical release-train order retained for integration

```text
#36 v0.8 Minimal Local Evaluator
#37 v0.9 Sandboxed Runtime
#40 v0.10+ Conformance / Stabilization
#38 v1.0.0-rc.N
#39 v1.0.0 final
```

The issue numbers in this historical block belong to the pre-public archive. Current public tracking is #1 → #2 → #3 → #4 below。

## Current checkpoint

ユーザーは2026-08-04に、本来の設計思想・過去要求・current `reference/`・current implementationを再監査し、不足Issueを新設したうえで**全Issueを依存順にautonomousに解決**するよう指示した。

Archive Issue #82 / PR #75 / Issue #72の旧preflight/rehearsal evidenceはhistorical evidenceとして保持するが、MagicalProgram/MGLS実装拡張後のrelease判断には再利用しない。

### Completed correction / migration / source / integration chain

```text
#110 architecture correction
  PR #111 merge d36588000413695f35c97d74e97539599496da30
#90 phase 1 shadow foundation
  PR #113 merge 1a5cd48a9e696fde734f50fe87ba0da77c38f4d9
#114 bounded typed structured values
  PR #115 merge f4065d646898f63b6ef8ad375bb82700bd91ae79
#90 SA-003 evidence fusion
  PR #117 merge 4e65f974ffc5623e609a2a55731ac0c7ffa504cf
#118 red-main correction / exact-head gate
  PR #119 merge 65f9707681958e4da30eb48a5d28c0898ab6b9c5
  TODO reconciliation PR #120 merge fab87bda89f5d04e4d303ebd2394516246110c7b
#90 SA-001 boundary reflection
  PR #121 merge 57b8f8d68e262c0986d251e75f1ed7dea1f513c1
#90 SA-002 staged treatment
  PR #123 merge a166ba13b3b2f89562e523b304f14f8e383acb62
#90 SA-004 bounded explosion
  PR #125 merge c27b13be5634712b54f982be298281f464641ba0
#90 DEBUG-HELL + complete matrix
  PR #127 merge a85a5aedb0ac22e080ef69b615ae3913ccc3ad66
#91 public MagicalProgram cutover + legacy executor retirement
  PR #129 merge 18c53d9a347db895fad3b93e2eac344ecec5c8a8
#92 bounded human-authored MGLS-0 source contract
  PR #131 merge 1a3ae3ebac8db9b12f35a65f2931c3c971f7ad46
#93 deterministic MGLS-0 parser / checker / compiler
  PR #133 merge 4f61fad2da979f8510ace372f70ec93e673e0a4e
#94 unified CLI / diagnostics / docs / packaging / E2E conformance
  PR #135 merge d5ed0fae5570c8c5ada40533689246d82e2d1d09
#84 MagicalProgram / MGLS architecture roadmap complete
```

### Exact completion evidence for Issue #94 / roadmap #84

```text
PR                            #135
reviewed/current head         4c49e8d09e174825a0701012a11286e946172643
merge                         d5ed0fae5570c8c5ada40533689246d82e2d1d09
Repository regression #394    SUCCESS / 32 schemas / 414 tests / diff check
Conformance package #346      SUCCESS / editable + wheel + sdist
MagicalProgram runtime #209   SUCCESS / editable + wheel + sdist
public command                magical-language check/eval/run/compile
user workflows                MGLS source + emitted program + repository bundle
installed command             editable / wheel / sdist outside checkout cwd
experimental E2E              UX-E2E-001..011 / excluded from stable manifest
replay                        source / program / bundle = Match
review threads / reviews      0 / 0
stable conformance            4 classes / 65 cases unchanged
released version              0.12.0 unchanged
```

Issue #94 / roadmap #84 retained guarantees:

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
audit baseline                b707ed3fa865f2b4aa190bc4975c37a391eb503b
active work                   public Issue #1 renewed exact-main no-waiver release-readiness audit
first                         enumerate every open Issue and release requirement on current main
then                          re-read all current normative owners and the 14 archived RC claims represented by public #2
then                          run repository / stable conformance / editable-wheel-sdist / runtime gates
then                          verify README / CHANGELOG / schemas / examples / grammar / reference / tests / conformance / TODO consistency
then                          publish an evidence-backed GO or NO-GO without changing version
release action                forbidden until audit completion and explicit user confirmation
```

Create a **fresh audit branch from exact public main `b707ed3fa865f2b4aa190bc4975c37a391eb503b`**。

## Remaining open Issue inventory

```text
public release / umbrella
  #1  renewed exact-main no-waiver release-readiness audit — ACTIVE
  #2  v1.0 RC — BLOCKED BY #1
  #3  v1.0 final release — BLOCKED BY #2
  #4  v0.8 → v1.0 umbrella roadmap — closes after #3 and post-v1.0 handoff
```

## Dependency-correct execution order

```text
public #1 renewed no-waiver release audit
public #2 RC path or evidence-backed return to stabilization
public #3 final release after a valid RC
public #4 umbrella closure after v1.0 and post-v1.0 handoff
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
required stable classes           4
required stable cases             65
pre-public RC requirement claims  14
MKI data-plane operations          6
World Kernel interaction classes  5
```

The audit/release train MUST NOT silently alter these counts, create authority from syntax, expose raw WorldState writes, tunnel legacy executable payloads, replace stable commands incompatibly, or rewrite historical snapshots。

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
PRE-PUBLIC DONE: #46 #77 #84 #86 #87 #88 #89 #90 #91 #92 #93 #94 #110 #114 #118
ACTIVE:          public #1 renewed exact-main no-waiver release-readiness audit
SUSPENDED:       public #2 RC judgment pending #1 and explicit user confirmation
BLOCKED:         public #3 final release requires valid RC
FINAL UMBRELLA:  public #4 closes after v1.0 and post-v1.0 handoff
```

## 2.1 #90 true shadow migration — DONE

- [x] complete 12-contract matrix and 33 external-golden evaluations;
- [x] GENERIC-001, SA-001..004, DEBUG-HELL-001..003, recognized-unsupported SA-005..008;
- [x] independent frozen legacy oracle, rollback, replay, authority, identity, accounting;
- [x] no fixture/suite/name dispatch or opaque executable tunnelling;
- [x] installed editable/wheel/sdist matrix and exact-head gates.

## 2.2 #91 public cutover — DONE

- [x] complete current MagicalProgram suite is the public SpellInstance path;
- [x] dedicated success/debug executors retired from production dispatch;
- [x] legacy executor retained only behind explicit test/oracle API;
- [x] public API/CLI and installed packages use generic execution for all 12 bundles.

## 2.3 #92 source contract — DONE

- [x] bounded `.mgls` grammar, values, bindings, contracts, obligations, outputs;
- [x] deterministic source -> MagicalProgram-0 lowering and source-map contract;
- [x] source spans, diagnostic ownership, limits, compatibility, no-import boundary;
- [x] 2 positive and 15 negative implementation-ready cases.

## 2.4 #93 compiler — DONE

- [x] strict UTF-8 normalization, bounded lexer/parser, deterministic source AST;
- [x] exact name/type/dimension/effect/obligation/resource/output checking;
- [x] deterministic MagicalProgram-0 and MglsSourceMap-0 emission;
- [x] independent semantic/source-map verification and target admission;
- [x] MGLS-NEG-001..015 fail closed with no partial program;
- [x] repository/editable/wheel/sdist determinism evidence.

## 2.5 #94 integration / #84 roadmap — DONE

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

## 2.6 public #1 renewed no-waiver release-readiness audit — ACTIVE

- [ ] enumerate all open Issues and verify no implementation/roadmap blocker remains;
- [ ] re-read all 14 pre-public RC required-surface claims, now tracked by public #2, against exact current main;
- [ ] re-read every current normative owner touched since the historical #82/#72 rehearsal;
- [ ] verify four stable classes / 65 cases and experimental inventories remain correctly separated;
- [ ] run repository regression, stable conformance, package, runtime, security, replay, and diff gates;
- [ ] verify fresh checkout and installed editable/wheel/sdist command behavior outside checkout cwd;
- [ ] verify version, README, CHANGELOG, schemas, grammar, examples, reference, conformance, consistency report, and TODO synchronization;
- [ ] verify historical `spec/` snapshots remain immutable;
- [ ] publish an exact-main GO or NO-GO report with no waivers;
- [ ] do not change version, snapshot, tag, or release state before explicit user confirmation after a GO.

---

# 3. Stable foundations and historical integration markers

## 3.1 Completed foundations

```text
DONE(contract + v0.8 implementation) — Issue #34 / Issue #36
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

SemanticAST and TypedMIR remain implementation-internal stages and are **stableな外部direct-entry contractとはしない**。Broader **multi-stage direct ingestion** belongs to **Issue #48** and later experimental/public contracts。MGLS / MagicalProgram / SpellInstanceBundleの`magical-language` workflowはexperimental additive surfaceであり、このstable境界を変更しない。

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

These remain **post-v1.0またはexperimental** unless separately promoted by evidence-backed scope decision。

---

# 5. Release evidence ledger

```text
v0.8   PR #52  Minimal Local Evaluator
v0.9   PR #53  Sandboxed Runtime
v0.10  PR #59  merge 90e47b7d71766272620e5f14f6304897a857d0a1
v0.11  PR #67  merge e79677d1706f3d05480cb230626856a8ef0b4224
v0.12  PR #74  merge 6d6ee23762456da6fe9e697d9f4742af09c4b447
Gate rehearsal PR #75 merge 191b8148b3daaaa48f7696dcddb893f9d4206e8f
SpellInstanceBundle PR #78 merge b177d92f6036fbb6d7c214cb9784de42cfc77fdd
MagicalProgram architecture PR #95 merge 822894e4c62a764c10ab965baa1b7077a8bd3990
open-issue sweep PR #103 merge d3f49a72a04f2f5cc5ea39f0acd9650bec25918a
golden parity PR #105 merge 4240bc82507b222d294d32c38c7a0998c4a3563f
artifact contract PR #106 merge 2c2e1348ea3513d51af39ac1bdd05f5cb2e3de78
evaluator PR #108 merge 2a13fb1941e73cdab8e3d8fc57298ec354d9de9a
runtime PR #109 merge a656d09425d11c7ac16fac918560e83afc764e6b
architecture correction PR #111 merge d36588000413695f35c97d74e97539599496da30
shadow foundation PR #113 merge 1a5cd48a9e696fde734f50fe87ba0da77c38f4d9
structured values PR #115 merge f4065d646898f63b6ef8ad375bb82700bd91ae79
SA-003 PR #117 merge 4e65f974ffc5623e609a2a55731ac0c7ffa504cf
red-main correction PR #119 merge 65f9707681958e4da30eb48a5d28c0898ab6b9c5
SA-001 PR #121 merge 57b8f8d68e262c0986d251e75f1ed7dea1f513c1
SA-002 PR #123 merge a166ba13b3b2f89562e523b304f14f8e383acb62
SA-004 PR #125 merge c27b13be5634712b54f982be298281f464641ba0
Issue #90 completion PR #127 merge a85a5aedb0ac22e080ef69b615ae3913ccc3ad66
Issue #91 public cutover PR #129 merge 18c53d9a347db895fad3b93e2eac344ecec5c8a8
Issue #92 MGLS source contract PR #131 merge 1a3ae3ebac8db9b12f35a65f2931c3c971f7ad46
Issue #93 MGLS compiler PR #133 merge 4f61fad2da979f8510ace372f70ec93e673e0a4e
Issue #94 unified workflow PR #135 merge d5ed0fae5570c8c5ada40533689246d82e2d1d09
```

No line in this ledger authorizes an RC or final release。

