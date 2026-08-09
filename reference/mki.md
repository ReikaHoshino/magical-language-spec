# MKI Reference — v0.7

**Status:** normative data-plane/control-plane boundary.

## Purpose

MKIが直接提供するworld-effect semantic operationと、resolver/planner/scheduler/integrator/replay service、
およびauthoritative world evolutionを仲介するWorld Kernel semantic boundaryの関係を定義する。

MKI primitiveはportable semantic operation boundaryであり、物理的にこれ以上分解不能な現象、
runtimeの最小micro-operation、またはworld lawそのものを意味しない。

lower semantic execution boundary、active-effect ownership、atomic group、temporally extended COMMIT、
bounded controller actuationのnormative ownerは[`kernel-execution.md`](kernel-execution.md)とする。

## Key invariants

```text
MKI data-plane primitives = 6
WorldIndex query != MKI primitive
Scheduler tick != MKI primitive
Integrator != MKI primitive
Replay != MKI primitive
Registry metadata != Capability
generate goal != MKI primitive
MKI primitive != physical primitive
magic effect request != physical-law definition
ordinary MKI effect != physical-law mutation
World Kernel != DefinitionSource
```

## Data plane

```text
RESOLVE
OBSERVE
CHANNEL
TRANSFER
RECONFIGURE
CONSTRAIN
```

上記6 primitiveを維持するMUST。

ここでいう`primitive`は、compiler/planner/runtime間でportable semanticsを保証する公開semantic operation
setを指す。1つのMKI operationが下位runtimeで複数のguarded transition、active process、measurement、
service interactionへloweringされること、またはobservable semanticsを維持したまま複数MKI operationが
一つのatomic realizationへ統合されることを禁止しない。

```text
MKI primitive != implementation micro-operation
MKI primitive != numerical integration step
MKI primitive != physical elementary process
```

lower semantic execution layerはWorld Kernel interaction classとして定義するが、public MKI primitiveや
stable serialized IRを追加しない。詳細は`kernel-execution.md`を参照する。

`generate X`はhigh-level desired-world-state planning goalであり、第7の
`GENERATE`/`CREATE` primitiveではない。plannerはsource fidelityとmandatory obligationsを
維持したcandidateを、既存のRESOLVE / OBSERVE / CHANNEL / TRANSFER / RECONFIGURE /
CONSTRAINへloweringする。詳細は`planning-inference.md`を参照する。

## Magic / World Kernel boundary

通常のMKI operationは、admitted world/model contractの下でsemantic effectを要求する。
術式またはMKI operationそのものがgoverning physical/model law、conservation rule、identity semantics、
causal/history semantics、authority modelを定義・置換・停止・暗黙上書きしてはならない。

```text
request effect under admitted model != define governing law
counteract world dynamics != delete world dynamics
```

術式はRegistry / World / Profile等が所有するadmitted modelを参照、選択、parameterizeできるが、
通常MKIから任意の新しいdynamics equation / physical lawを注入してはならない。

例えばgravity下の水平trajectory維持は、gravity modelを変更する指定ではない。`CONSTRAIN`は必要な
observation / controller / permitted actuationを通じてworldへ追加作用を与え、そのauthority、Energy /
resource、accounting、timingを通常のguardで処理する。

```text
CONSTRAIN(horizontal trajectory under gravity)
!= rewrite(gravity = disabled)
```

`World Kernel` はvalidated / revalidatedなMKI semantic requestまたはそのlowered realizationと、
authoritative world evolutionの間を仲介する特権的semantic boundaryである。

```text
MKI semantic request
→ lower semantic execution boundary
→ World Kernel
→ authoritative world evolution
```

World Kernelは新しいCapability、Lease、DefinitionSource、registry truthを生成しない。下位化後も、
元のoperationに適用されるauthority、identity、conservation/accounting、model compatibility、sandbox、
current-state guardを維持するMUST。

World Kernelという抽象は、worldがbinary computerまたはsoftwareであることを規定しない。
scheduler / integrator / replay / storage implementationはWorld Kernel boundaryを実装しうるserviceだが、
そのalgorithm自体をphysical lawとして扱わない。

physical/model lawそのものを変更するoperationを将来定義する場合、それはordinary MKI effectの暗黙能力
ではない。current six-primitive semanticsとは別の明示的高権限contractとして設計するMUST。

## RESOLVE

```text
RESOLVE<T>(Selector<T>,QueryContext) -> Ref<T>
```

内部ではWorld Indexを利用できる。

```text
Selector
→ ResolverQuery
→ WorldIndexSnapshot
→ CandidateSet
→ visibility/type/uniqueness
→ authoritative revalidation
→ Ref<T>
```

World Index recordだけから未検証Refを作ってはならない。

`RESOLVE`はworld lawを問い合わせるroot introspectionではなく、定義済みresolver / identity boundaryを
通じて検証済み`Ref<T>`を取得するsemantic operationである。

## OBSERVE

```text
OBSERVE(ref,property,resolution) -> Measurement<Q>
```

specialized snapshots:

```text
Measurement<CompositionEstimate>
SpectralMeasurement<Q,Axis>
```

```text
Index metadata != Measurement<Q>
```

Observation modelが物理的back-actionを持つ場合、そのmutation / resource / accounting effectを単なるreadの
内部実装として隠してはならない。通常world-effect boundaryで明示的にaccountするMUST。

## CHANNEL

```text
Channel<K : Transferable>
```

```text
E_open  = α_K σ d^2
P_maint = β_K σ d^2
```

Matter structure保持には別契約:

```text
PreserveStructure<S>
```

Channelはadmitted transport model / resource contractを使用する。`CHANNEL`から任意の伝播法則を術式が
新設できることを意味しない。

## TRANSFER

```text
TRANSFER<K>(Channel<K>,PayloadOf<K>)
    -> TransferHandle<K>
```

```text
PayloadOf<Energy>   = Quantity<Energy>
PayloadOf<Momentum> = Quantity<Momentum>
PayloadOf<Charge>   = Quantity<Charge>
PayloadOf<Matter>   = MatterPayload
```

transport中は `Transit<K,PayloadOf<K>>` としてaccountingする。

physical/effective arrival timeはChannel propagation modelから決まり、scheduler tick幅が変更してはならない。

非zero propagationでは送出、transit、deliveryが時間的に分離しうる。`TRANSFER`のsemantic commitmentを
一回の瞬時destination writeとみなしてはならない。source debit + Transit activation、arrival credit + Transit
settlementのatomic groupとactive-effect lifecycleは`kernel-execution.md`が所有する。

## RECONFIGURE

既存matter/state/composition/structureを変更する。

要求:

- Write Lease。
- authority。
- conservation/accounting obligations。
- invariants。
- identity preservation時のIdentityPolicy。

Reaction/Kinetics metadataは高級planning syntaxであり、新primitiveではない。

```text
ReactionRule != ReactionPathway
Stoichiometry != RateLaw
Kinetics != Thermodynamics
```

`RECONFIGURE`は既存world/model contractに基づくstate transformationであり、arbitrary property writeまたは
physical-law mutationではない。continuous transformationはadmitted kinetic/dynamics modelを使用し、
integrator step列をworld ontologyそのものとして定義しない。

## CONSTRAIN

feedback Controllerを登録する。

```text
OBSERVE -> error -> controller -> actuator plan
```

v0.7ではController timing requirementをscheduler contractへ渡せる。

```text
sample_period
max_jitter
actuation_latency_bound
```

`CONSTRAIN`はrequested invariantをworld lawへ追加するoperationではない。Controllerは許可された観測と
actuationによってconstraint維持を試み、timing / authority / resource / safety guardを満たせなければ失敗しうる。

Controller登録はunlimited future authorityを付与してはならない。継続actuationのeffect class、target、
resource、timing、authority scopeをboundするcontractをlower semantic execution boundaryで保持するMUST。
そのbounded actuation / revalidation / deactivation contractは`kernel-execution.md`が所有する。

## Control plane

```text
ACQUIRE
RELEASE
COMMIT
ABORT
REVOKE
DELEGATE
```

## PREPARE / scheduler admission

PREPAREでは必要に応じて:

```text
WorldIndexRevision
EntityID/state revision guard
registry contract
Capability / Lease
resource reservation
TemporalTolerance
ControllerTiming
Integrator availability
scheduler policy compatibility
```

を検査する。

安全条件を証明できなければfail closed。

PREPARE / COMMITはadmitted modelの存在・compatibility・authorityを検証するが、術式が新しいworld lawを
宣言したという理由だけでそのmodelをadmitしてはならない。

## Runtime scheduler boundary

SchedulerはMKI primitiveの意味を変更せず、physical time上のEvent/continuous processを実行する。

logical phases:

```text
Ingress
ContinuousAdvance
Revalidate
Commit
PublishSnapshot
Control
IndexUpdate
Dispatch
```

MKI `COMMIT` とscheduler `Commit` phaseは関連するが同一概念ではない。

- control-plane COMMIT: operation / admitted active effectを不可逆実行可能状態へ移す。
- scheduler Commit phase: due discrete transitionをauthoritative World State/Historyへ確定する。

一つのcontrol-plane COMMIT後に非zero transfer、continuous reconfiguration、persistent control等の
world evolutionが継続しうる。初回COMMITを「全future consequenceが既に発生した」と解釈しない。
active effectのsemantic ownership、initial atomic group、later scheduler commitの関係は
`kernel-execution.md`を参照する。

## Continuous integration boundary

Kinetics等の規範的意味:

```text
dξ/dt = rate(context(t))
```

runtime integratorはこの連続モデルを近似する。

```text
Integrator approximation != physical law
```

IntegratorContract/toleranceを満たせなければunsafe effectを無理に継続してはならない。

World Kernel boundaryはcontinuous semantic modelとnumerical approximationを分離し、scheduler tick幅、
solver substep、floating-point representation等を術式からgoverning physical lawとして定義させない。

## Event / await boundary

v0.7では:

```text
EventTimeRecord {
    effective_at
    committed_at
}
```

を区別する。

- `effective_at`: model上effectが有効な時刻。
- `committed_at`: scheduler Commit phaseでauthoritative state/historyへ確定した時刻。

runtimeは `committed_at` を過去へbackdateしてはならない。

continuation:

```text
Delivered(tx) ≺ continuation
```

latency:

```text
CommitLatency   = committed_at - effective_at
DispatchLatency = resumed_at - committed_at
ResponseLatency = resumed_at - effective_at
```

## World Index synchronization

Commit後のWorldRevisionはIndexUpdate phaseでWorld Index updaterへ渡せる。

World Indexが非同期更新でもよいが、revision mappingを保持する。

## Replay boundary

```text
ReplayManifest
TickRecord
```

はruntime/debug metadataでありMKI world-effect primitiveではない。

```text
DeterministicReplay != Rewind
```

Replayは別runtime/simulationでexecutionを再現し、元world historyを変更しない。

## Source-language boundary

`RuntimeTickID`, `SchedulerPhase`, `MicrostepOrdinal` は通常MIRへ直接公開しない。

portable time APIは `Instant` ベース。

```text
now_monotonic() -> Instant
```
