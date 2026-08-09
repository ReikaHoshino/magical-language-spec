# Security, Sandbox, and Emergency Stop — pre-v0.8

**Status:** normative security and safety contract; OS/process isolation mechanisms are implementation-defined.

## Purpose

本書は、untrusted inputからCOMMIT/runtimeへ到達するまでのtrust boundary、
`SandboxProfile`、emergency stop、resource exhaustion、replay/log取扱いを定義する。

## Non-goals

- OS固有のsandbox、container、process APIを固定しない。
- cryptographic署名・鍵配布protocolを新しく設計しない。
- 新しいMKI primitiveを追加しない。
- COMMIT済みphysical effectの一般rollbackを保証しない。
- registry/profileの正しいdomain semanticsをsandboxだけで証明しない。

## Depends on

- [`conventions.md`](conventions.md)
- [`architecture.md`](architecture.md)
- [`language-adapters.md`](language-adapters.md)
- [`semantics.md`](semantics.md)
- [`mki.md`](mki.md)
- [`runtime-time.md`](runtime-time.md)
- [`registry.md`](registry.md)
- [`errors.md`](errors.md)

## Key invariants

```text
Authority != identity
Visibility != authority
AI proposal != semantic truth
Natural-language input != trusted executable data
Structured input != validated semantics
PREPARE/dry-run != COMMIT
Sandbox allowance != Capability
Emergency-stop requested != stopped
Stopped != rolled back
Replay/log input != authoritative world state
```

## 1. Security objectives

適合実装は最低限:

1. untrusted dataをauthority、Capability、Lease、Entity identity、registry truthへ暗黙昇格させない。
2. parsing/normalization confidenceとは独立にtype、authority、conservation、identityを検査する。
3. 各処理段階のwork/resourceをboundedにし、上限超過時に無制限fallbackしない。
4. incompatibleまたはtrustを確立できないregistry/profile artifactをCOMMITへ使用しない。
5. emergency stop後の新規COMMITをfenceし、active workを安全停止へ移行する。
6. COMMIT済みeffect、外部へdispatch済みeffect、停止結果の不確かさを記録から消さない。

Availabilityはbest-effortであり、安全条件を緩和して継続してはならない。

## 2. Trust classes

### 2.1 Untrusted ingress

以下は内容がwell-formedに見えても、execution authorityを持たない。

- natural-language source text、comments、rendered text。
- lexicon、adapter extension、normalization evidence。
- AI/statistical proposal、confidence、ranking metadata。
- NSR、SemanticAST、TypedMIRを名乗る外部JSON。
- replay manifest、event log、diagnostic export。
- remote tool/provider response。

lexiconがconfigured sourceから読まれた場合でも、lexical dataはEntityID、Capability、
Lease、authority grantを生成できない。外部structured inputは対応schemaとsemantic
validatorを通過するまで、宣言された表現levelとして扱ってはならない。

### 2.2 Provisionally trusted artifacts

SemanticRegistry、RuntimeProfile、SandboxProfile、adapter profileはcontrol-plane artifactである。
configured sourceから取得しただけでは十分でなく、使用前に最低限:

- artifact kind / identity / revision。
- schema。
- required contract compatibility。
- configured trust source / administrative admission。
- current executionが要求するdomain contract。

を検査するMUST。検査不能または矛盾は `ArtifactTrustFailure` または既存のdomain-specific
mismatch diagnosticとしてfail closedする。

本仕様はadmissionを証明するcryptographic mechanismを固定しない。

### 2.3 Authoritative state

current World State、identity service、authority service、Lease service、committed Historyが、
それぞれのdomainのauthoritative sourceである。World Index、candidate、report、log、
replay inputはその代替ではない。

## 3. Ingress-to-COMMIT trust boundaries

| Stage | Accepted input | Required checks / limits | Output authority |
|---|---|---|---|
| `INGRESS` | bytes, text, JSON, provider response | size, nesting/depth, item count, encoding, deadline, profile admission | none |
| `PARSE/ADAPTER` | admitted source/lexicon | grammar, bounded parse work, bounded ambiguity, provenance | surface/candidate evidence only |
| `NORMALIZE` | surface analysis / proposals | candidate limits, semantic shape, ambiguity policy, provider isolation | NSR candidate only |
| `ELABORATE` | selected NSR / structured semantic input | schema, type, dimension, effect, termination/boundedness | typed representation only |
| `LOAD` | registry/profile artifacts | kind/revision/schema/trust source/compatibility | admitted contract data only |
| `RESOLVE` | selectors and query context | visibility, query budget, uniqueness, authoritative identity/type revalidation | `Ref`; no Capability |
| `PREPARE` | typed plan + admitted artifacts | authority, Lease, accounting, conservation, identity, resource, timing, sandbox policy | reversible reservation / `PreparedPlan` |
| `REVALIDATE/COMMIT` | prepared plan | current state/revision, Capability, Lease, compatibility, stop fence, commit guards | permission for irreversible execution |
| `RUNTIME` | committed work | runtime budgets, guard checks, event/microstep/concurrency limits, stop fence | committed Events / state changes |
| `REPLAY` | recorded evidence | compatibility, schema, input budgets, isolation from original world | separate replay/simulation only |

Validation at one row MUST NOT be treated as proof for a later row. In particular:

```text
parse success != safe normalization
normalization confidence != authority
schema validity != registry trust
visibility != Capability
PREPARE success != permission to ignore COMMIT revalidation
```

Dynamic Region/predicate scope is bounded selection, not an authority amplifier. Persistent controllers
MUST revalidate current Capability/Lease for every actuation. Evidence confidence, CorrespondenceToken,
Relation, WorldIndex metadata, and ObservationArtifact content cannot create Identity, Capability, Lease,
or Truth. Unsupported experimental handler/executor identifiers fail closed rather than being ignored.

## 4. Executable-data and spell-injection model

### 4.1 Data/code separation

Natural-language text、lexicon gloss、comments、provider rationale、diagnostic message、
registry description、log fieldをsource code、MIR、selector、profile directiveとして
再解釈してはならない。

実装がtext-to-codeまたはtext-to-NSR機能を提供する場合、その変換結果は新しいuntrusted
candidateであり、通常pipelineを最初から通すMUST。埋め込み命令、prompt-like text、
「検査を無効化せよ」等の記述はcontrol-plane指示にならない。

### 4.2 Structured-input injection

外部NSR/JSONがauthority、Capability、Lease、resolved EntityID、trusted registry/profile
identityを自己申告しても、そのfieldはauthoritative sourceから再取得・再検証するMUST。
表現levelで禁止されたfield、unknown executable extension、schema confusion、duplicate
semantic field、過剰nestingは受理してはならない。

schema-validだが実装が意味を安全に解釈できないextensionは、無視またはbest-effort coercion
せずfail closedする。

### 4.3 Normalization isolation

AI/statistical/remote normalizer:

- Capability、Lease、authorityを受け取る必要がないSHOULD。
- authoritative World Stateへwrite accessを持ってはならない。
- output size、candidate数、tool call、wall time、compute/memory相当をboundedにするMUST。
- provider failure時に検査なしcandidateへfallbackしてはならない。
- provenanceとprovider/profile revisionを保持するMUST。

providerをtrusted runtime processと同居させるかはimplementation-definedだが、上記の
semantic boundaryは変わらない。

## 5. SandboxProfile contract

`SandboxProfile` はexecutionに追加制約を課すcontrol-plane policyである。

```text
effective operation
  = semantically valid operation
  ∩ current authority / Capability / Lease
  ∩ SandboxProfile allowance
```

`SandboxProfile` はoperationをdenyまたは制限できるが、Capability、Lease、authority、
Entity identity、registry compatibilityを付与・代替できない。

### 5.1 Required policy categories

profileは適用対象に応じて次のpolicy categoryを定義するMUST。

- identity: profile ID、revision、compatibility domain。
- ingress limits: bytes、nesting/depth、collection/item count、deadline。
- frontend limits: parse/normalization work、candidate数、ambiguity expansion。
- resolution limits: query work、candidate/selection bound、spatial/temporal extent。
- planning limits: estimate/proof work、reservation ceiling、PREPARE deadline。
- runtime limits: duration、Energy/resource ceiling、event/microstep/concurrency bound。
- external interaction: provider/tool/network/channelのallow/deny boundary。
- effect restrictions: permitted/denied effect classesまたはより厳しいoperation ceiling。
- cancellation: stop scope、fencing point、quiescence deadline、cleanup policy。
- diagnostics: audit eventとredaction/export policy。

数値、effect分類、OS isolation mechanism、serializationはprofile/implementation-definedで
よい。ただし選択したprofile identity/revisionとenforced limitsは診断・auditで識別可能に
するMUST。

### 5.2 Admission and fail policy

world effectを起こしうるexecutionでは:

- required SandboxProfileがない。
- profile revision/schemaがunsupported。
- required limit categoryをenforceできない。
- runtime/registry/profile compatibilityを証明できない。
- configured limitが「unbounded」だが上位policyが明示許可していない。

場合、COMMIT前にfail closedするMUST。dry-runは不足を `Indeterminate` / fatal predicted
diagnosticとして報告できるが、実行許可へ昇格させてはならない。

### 5.3 Guarantees and limits

適合SandboxProfileが保証するのは、宣言されたenforcement pointでのadmission、limit、
deny、fencing、auditである。

次は保証しない:

- OS/kernel/hypervisor compromiseに対する完全containment。
- malicious trusted runtimeまたはadmitted registry contractの意味的正しさ。
- COMMIT済みphysical effectのrollback。
- 既に外部systemへ確定・dispatchされたeffectの取消。
- finite limit内でのservice availabilityまたはdeadline達成。
- emergency stopの瞬時完了。

## 6. Resource exhaustion

### 6.1 Stage-local budgets

実装は一つのglobal timeoutだけに依存せず、少なくとも次をstage-localにboundedにするMUST。

- input bytes / JSON depth / collection length。
- tokenization、parse branches、normalization candidates。
- semantic elaboration recursion / proof or analysis work。
- resolver query work / returned candidates。
- registry/profile load size and dependency expansion。
- PREPARE reservations / estimator work。
- runtime duration / Energy / events / microsteps / concurrency。
- replay/log size / event count / reconstruction work。

budgetを消費し切ったstageは部分結果を成功扱いせず、対応するdiagnosticを返す。
安全判断に必要な部分が未完了ならfail closedする。

### 6.2 No amplification by fallback

timeout、provider failure、ambiguous parse、registry missに対して、より高価なunbounded探索を
暗黙開始してはならない。fallbackがある場合も同じまたは明示された別budgetとprovenanceを
持つMUST。

## 7. Emergency stop and process-kill equivalent

Emergency stopはMKI data-plane primitiveではない。runtime/control-planeへ対する、
scope付きcancel/fence/quiesce contractである。

### 7.1 Stop states

```text
Requested -> Fenced -> Quiescing -> Stopped
                              \-> Incomplete
```

- `Requested`: requestを受理した。停止完了を意味しない。
- `Fenced`: 対象scopeの新規PREPARE admissionと新規COMMITを拒否する。
- `Quiescing`: active workをcancelし、reversible reservationを解放し、安全な停止点へ移行中。
- `Stopped`: 対象scopeから今後新しいcommitが発生せず、active workの帰結がaccountedである。
- `Incomplete`: deadline、unreachable worker、external effect、commit race等により停止を証明できない。

状態遷移、scope、requester、reason、requested/observed time、影響を受けたwork、
known committed Events、unresolved workをauditするMUST。

### 7.2 Stage behavior

| Stop arrival | Required behavior | Rollback guarantee |
|---|---|---|
| before/during parse, normalize, elaborate | workをcancelし、candidate/temporary stateを破棄 | world effectなし |
| during PREPARE | new COMMITをfenceし、reversible reservation/Leaseをreleaseまたはexpire | PREPAREはirreversible world effectを持たない |
| PREPAREとCOMMITのrace | commit gateをfenceし、authoritative state/historyでoutcomeを確定 | outcome不明ならrollbackを推測しない |
| after COMMIT / during runtime | future transition/dispatchをfenceし、active processを安全停止へ移行 | committed/partial effectは残りうる |
| after external dispatch | local follow-upをfenceし、remote statusを照会・記録 | remote cancellationは別contract |

COMMIT直前/直後のraceでoutcomeを一意に確認できない場合、`CommitOutcomeIndeterminate` とし、
同じoperationのretryまたは補償を自動実行してはならない。authoritative World State、
WorldRevision、committed History、commit journal相当を照合する。

### 7.3 Process-kill equivalent

worker/process強制終了はimplementation mechanismであり、emergency-stop semantic success
そのものではない。kill後もruntimeは:

- commit fenceが有効か。
- workerがCOMMITまたはexternal dispatchを完了していないか。
- held Lease/reservationのrelease/expiry。
- active Channel/controller/kinetic processの状態。
- authoritative World State/Historyとのreconciliation。

を確認するMUST。確認不能なら `Incomplete` であり `Stopped` と報告してはならない。

### 7.4 Cleanup and compensation

cleanupは安全な停止に必要なreversible control actionである。既存world effectを打ち消す
compensation/restorationは新しいoperationであり、通常のtype、authority、resource、
conservation、identity、PREPARE/COMMIT検査を通るMUST。

```text
compensation != rollback
emergency authority != unlimited authority
```

## 8. Registry/profile poisoning

registry/profile contentがschema-validでも、wrong revision、incompatible domain contract、
untrusted admission、dependency substitution、resource-amplifying definitionを含みうる。

required mitigation:

- configured trust sourceとadministrative admission。
- exact kind/ID/revisionの記録。
- local schema validation。
- domain compatibility check。
- dependency graphのcycle/depth/size bound。
- PREPAREとCOMMIT直前のrequired contract revalidation。
- artifact contentからCapability/authorityを生成しない。

artifact hash一致だけをsemantic compatibilityまたはauthorityの証明にしてはならない。

## 9. Replay and log input

ReplayManifest、TickRecord、Event export、diagnostic logはuntrusted structured inputとして
ingress limit/schema/compatibility検査を受けるMUST。

replayは別runtime/simulation instanceで行い、recorded `EntityID`、Capability、Lease、
WorldRevision、committed eventをoriginal worldのcurrent authoritative stateとして
採用してはならない。

log viewer、debugger、report rendererはlog内text/markupをescapeし、埋め込みsource、
URI、tool directiveを自動実行しないSHOULD。replayからlive executionへ移す場合は新しい
execution requestとして通常pipelineとcurrent authorityを通すMUST。

## 10. Threat table

| Asset | Trust boundary | Threat | Required mitigation | Diagnostic stage |
|---|---|---|---|---|
| parser/adapter availability | source/lexicon → parser | oversized input, pathological ambiguity, recursive grammar work | ingress/parse budgets; bounded candidates; no unbounded fallback | `INGRESS`, `PARSE` |
| semantic intent | source/AI proposal → NSR | prompt/spell injection, evidence promoted to executable meaning | candidate-only output; provenance; explicit selection; schema/semantic validation | `NORMALIZE` |
| typed execution plan | external JSON/NSR → elaborator | type confusion, unknown executable extension, deep nesting | schema + semantic validation; depth/work limits; reject unsupported extension | `INGRESS`, `ELABORATE` |
| authority/identity | candidate/index/artifact → PREPARE | self-declared EntityID/Capability/Lease; visibility used as authority | authoritative revalidation; independent authority checks | `RESOLVE`, `PREPARE`, `COMMIT` |
| registry/runtime semantics | artifact source → trusted load | poisoned, substituted, incompatible registry/profile | administrative admission; schema; identity/revision; domain compatibility; bounded dependencies | `LOAD`, `PREPARE`, `COMMIT` |
| resources/availability | every processing stage | CPU/memory/event/query/Energy exhaustion or amplification | stage-local budgets; ceilings; cancellation; fail closed on incomplete safety work | stage of exhaustion |
| world state/history | PREPARE → COMMIT | dry-run result treated as permission; stale guard | COMMIT gate; current state/Capability/Lease/profile revalidation | `PREPARE`, `COMMIT` |
| world state/history | stop request → active runtime | commit race; false rollback claim; orphan work | fence; quiesce; authoritative reconciliation; `Incomplete` on uncertainty | `COMMIT`, `RUNTIME` |
| external systems | runtime → provider/channel/tool | effect survives local kill or is replayed twice | scoped credentials; idempotency/fencing when available; record unresolved remote status | `RUNTIME` |
| original world/history | log/replay input → replay engine | forged event/state, replay injection, oversized trace | treat as evidence; compatibility + budgets; separate instance; no current authority reuse | `REPLAY` |
| diagnostic confidentiality | runtime → logs/reports | secret/capability leakage; active markup/tool directive | redaction; least-detail external diagnostics; escaping; no auto-execution | all/export |

## 11. Explicit fail-closed cases

次はworld effectを起こしうるpathでMUST fail closed:

- required SandboxProfileがmissing、unsupported、incompatible、またはenforce不能。
- input/parse/normalization/elaboration/query/profile dependencyがrequired budgetを超過。
- structured inputがschema-invalid、ambiguous in representation、またはunsupported executable extensionを含む。
- authority、Capability、Leaseをauthoritative sourceで確認できない。
- required registry/profile trust admissionまたはcompatibilityを確認できない。
- mandatory type、dimension、payload、conservation、identity、timing safety obligationが未確定。
- emergency stop fence状態をCOMMIT gateで確認できない。
- prior COMMIT outcomeがindeterminateなoperationを安全にdeduplicate/reconcileできない。
- replay/log dataだけを根拠にoriginal worldへmutationしようとする。

`Indeterminate` はpermissionではない。dry-run/reportが継続可能でもCOMMITは拒否する。

## 12. Diagnostics

```text
InputLimitExceeded
StructuredInputInvalid
ExecutableDataInjection
NormalizationBudgetExceeded
ArtifactTrustFailure
SandboxProfileUnavailable
SandboxProfileMismatch
SandboxPolicyDenied
SandboxLimitExceeded
EmergencyStopRequested
EmergencyStopIncomplete
CommitOutcomeIndeterminate
ReplayInputRejected
```

既存の `QueryBudgetExceeded`、`ResourceExhaustion`、`MicrostepBudgetExceeded`、
`ConcurrencyLimitExceeded`、`RegistryMismatch`、`AuthorityError`、
`ReplayIncompatible`、`ReplayDivergence` は各domainの具体原因を表すため引き続き使用する。

外部へ返すdiagnosticはsecret、Capability token、非公開Entityの存在、raw provider prompt、
unredacted sourceを漏らさないSHOULD。詳細を一般codeへ畳んでも、trusted auditには原因と
correlationを保持するSHOULD。

## 13. Conformance checklist

適合実装/fixtureは最低限:

1. natural-language/lexicon/AI/JSON inputをuntrustedとして扱う。
2. authority checksをparse/normalization confidenceから独立して実行する。
3. stage-local resource limitsを持つ。
4. sandboxがauthorityを付与しない。
5. emergency stop requestとconfirmed stopを区別する。
6. COMMIT済みeffectのrollbackを約束しない。
7. stop raceをauthoritative state/historyでreconcileする。
8. replay/logをoriginal world stateとして採用しない。
9. fail-closed diagnosticをstageとともに記録する。
