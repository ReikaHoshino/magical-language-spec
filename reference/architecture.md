# Architecture Reference — v0.7.3

**Status:** mixed — layer boundaries are normative; diagrams/examples are informative.

## Purpose

多言語自然言語入力、NSR、Feasibility Evaluator、World Index、runtime scheduler、integration、replayまでを一つの処理系として俯瞰する。

## Non-goals

- 特定自然言語をcompiler coreへ埋め込まない。
- AIをsemantic authorityとして扱わない。
- 個別solver/database/parser algorithmを固定しない。
- TickIDをsource-language APIへ公開しない。
- 世界がliteral software / binary machineであると規定しない。

## Depends on

- `conventions.md`
- `scope-and-ownership.md`
- `language-adapters.md`
- `feasibility.md`
- `world-index.md`
- `runtime-time.md`
- `semantics.md`
- `mki.md`
- `kernel-execution.md`
- `planning-inference.md`

## Key invariants

```text
MKI data-plane primitives = 6
Language-specific parse != NSR
AI proposal != semantic truth
Cross-language conversion != direct translation
SemanticFingerprint != artifact content_hash
Evaluation != Execution
WorldIndex != WorldState
Physical time != runtime tick
Replay != Rewind
Registry metadata != Capability
PlannerPrediction != RuntimeSafetyGuarantee
WholePlanPreflight != Reservation != Authority grant != RuntimeSafetyGuarantee
magic effect request != physical-law definition
ordinary magic != physical-law mutation
World Kernel != DefinitionSource
scheduler/integrator behavior != physical law
Kernel interaction class != MKI primitive
runtime bookkeeping != semantic active-effect ownership
control-plane COMMIT != all future consequences already occurred
```

## 1. End-to-end layers

```text
Natural Language Source
 lat / lzh / ger / jpn / eng / zho / ...
        ↓ LanguageAdapter<L>
SurfaceAnalysis<L>
        ↓ normalization
NormalizationCandidateSet
        ↓ AmbiguityPolicy
NSR
        ↓ deterministic semantic validation
SemanticAST
        ↓ typed elaboration
TypedMIR
        ↓ static checks / SemanticRegistry
Resolver / WorldIndex → candidate evidence
        ↓
Feasibility Evaluator / PREPARE planning
        ↓
KernelPlan / PreparedPlan
        ├─ dry-run → FeasibilityReport → STOP
        └─ execution → Revalidate → control-plane COMMIT
                         ↓
                   MKI semantic operations
                         ↓
              lower semantic execution boundary
                         ↓
                 World Kernel boundary
                         ↓
          authoritative world evolution: Σ + H
                         ↕
                 runtime/process state Ω / P
```

`lower semantic execution boundary`は[`kernel-execution.md`](kernel-execution.md)が所有する。
World Kernel interaction classは `QUERY / SAMPLE / TRANSITION / ACTIVATE / DEACTIVATE` の5 categoryを持つが、
それらは新MKI primitiveでもpublic source syntaxでもなく、v1.0でserialized ECIR artifactを固定しない。

Scheduler / Integratorはこのexecutionを支援するserviceであり、World Kernelの存在を理由に
scheduler tickやnumerical substepをphysical lawへ昇格させない。

## 2. Frontend architecture — v0.7.3

```text
LanguageAdapter<L>
├─ tokenizer / segmentation
├─ lexicon
├─ morphology? 
├─ syntax / dependency
├─ semantic-role proposal
├─ selector proposal
└─ normalization candidate generation
```

すべてのAdapterが同じ内部言語学pipelineを持つ必要はない。

共通出口:

```text
NormalizationCandidateSet
→ NSR
```

Latinは `LanguageAdapter<lat>` であり、特権的core syntaxではない。

## 3. AI normalization boundary

AI/LLMはoptional provider。

```text
Natural language
→ AI proposal
→ NormalizationCandidate
```

ただし:

```text
AI proposal != semantic truth
confidence != proof
```

TypedMIR type、Capability、EntityID、Energy値、保存則成立等は後段のdeterministic/trusted layerが検証する。

## 4. Cross-language architecture

```text
Source<L1>
→ LanguageAdapter<L1>
→ NSR
→ SurfaceRenderer<L2>
→ Source<L2>
```

直接translation resultをsemantic authorityにしない。

同値性検査:

```text
SemanticFingerprintV1(NSR_before)
==
SemanticFingerprintV1(normalize(render(NSR_before,L2)))
```

不一致は `CrossLanguageDrift`。

fingerprintはRFC 8785 JCSによる`CanonicalSemanticProjectionV1`のSHA-256であり、
full NSR serializationやgeneric artifact content hashではない。renderer未実装の
v0.7.3ではNSR-layer adapter equivalenceのみをtestする。

## 5. Ambiguity architecture

```text
AmbiguityPolicy =
    StrictReject
  | InteractiveResolve
  | ContextualDeterministic
  | LegacyPermissive
```

`LegacyPermissive` は意図外だがvalidな候補選択を許しうる。

```text
Unexpected result != undefined behavior
```

ただしtype/authority/conservation/identity等のmandatory safety checkは回避しない。

## 6. Compiler / semantic layers

```text
NSR
→ SemanticAST
→ TypedMIR
→ KernelPlan
```

分離:

```text
Surface text != NSR
NSR != SemanticAST
SemanticAST != TypedMIR
TypedMIR != KernelPlan
```

NSRは人間可読性を維持し、language-specific morphology/word orderから離れる。

## 7. Runtime configuration

```text
C = <Σ,H,Ω,P>
```

- `Σ`: authoritative World State。
- `H`: committed Events + causal relation。
- `Ω`: runtime/scheduler/leases/handles/queues/solver bookkeeping等。
- `P`: evaluating MIR/process state。

Channel / Transit / Controller / active Dynamics等がfuture world evolutionへsemanticに影響する場合、
そのcausally relevant semantic projection / lifecycleはauthoritative `Σ` semanticsとして扱うMUST。
実装は対応handle、queue、cache、solver stateを`Ω`へ置けるが、`Ω`だけをsemantic ownerにしない。

```text
semantic active effect != arbitrary runtime bookkeeping
causally relevant active-effect semantics ⊆ authoritative Σ semantics
```

storage-independent ownershipは`kernel-execution.md`を参照する。

## 8. MKI data plane

```text
RESOLVE
OBSERVE
CHANNEL
TRANSFER
RECONFIGURE
CONSTRAIN
```

6 primitiveを維持するMUST。

ここでいうprimitiveはportable semantic operation boundaryであり、
「物理的にこれ以上分解不能」「runtimeの最小micro-operation」であることを意味しない。
MKI operationは`kernel-execution.md`のlower interactionへloweringできるが、observable MKI semantics、guard、
identity、accounting、timing、provenanceを保存するMUST。

LanguageAdapter、NSR、AI normalizer、SurfaceRenderer、Evaluator、WorldIndex query、scheduler、integrator、replay、およびWorld Kernel interaction classは新MKI primitiveではない。

### 8.1 Magic / physical-law boundary

MKI operationはworldへsemantic effectを要求するが、通常のMKI operation自体はgoverning physical/model
lawを定義・置換・停止・書換えしない。

```text
MKI effect request != physical-law definition
MKI effect request != arbitrary dynamics injection
```

術式が自然発展に対抗する場合も、admitted Channel / Transfer / Reconfiguration / Controllerその他の
effectとして実現し、そのmodel、authority、Energy/resource、conservation/accounting、timingを通常境界で
処理する。例えば水平軌道維持はgravity model削除ではない。

physical/model law自体のmutationを将来導入するなら、ordinary MKIの暗黙能力としてではなく、
別の明示的高権限contractとして定義するMUST。

### 8.2 World Kernel semantic boundary

`World Kernel` はMKI/lower semantic execution requestとauthoritative world evolutionの間にある
特権的semantic boundaryである。

World Kernelは:

- current state / model / authority / accounting / safety guardを維持してeffect realizationを仲介する。
- raw unvalidated world writeを通常術式へ公開しない。
- `Specification / Implementation / Registry / World / Profile` に代わるDefinitionSourceではない。
- scheduler、integrator、replay、storage engine等の具体実装algorithmを規範的物理法則へ昇格しない。
- 世界がbinary/discrete/continuous/hybridのどれであるかを本境界だけから決定しない。

```text
World Kernel != DefinitionSource
World Kernel != unlimited authority
World Kernel != binary-machine claim
```

world自身のnatural/world-defined dynamicsは魔法programと独立に存在できる。魔法はadmitted effectを
世界発展へ参加させる情報制御mechanismであり、world evolution全体の定義者ではない。

## 9. Control plane

```text
ACQUIRE
RELEASE
COMMIT
ABORT
REVOKE
DELEGATE
```

control-plane COMMITはinitial `KernelAtomicGroup`をauthoritativeに確定し、ACTIVATEされたeffectを実行可能状態へ移す。
それはactive effectの全future consequenceが既に生じたことを意味しない。later due discrete effectsはscheduler
Revalidate + Commitを通る。

## 10. Trusted contexts/services

```text
Γ / Δ / Λ / Π
SemanticRegistry
WorldIndexSnapshot
EvaluationProfile
AmbiguityPolicy
SchedulerPolicy
IntegratorContract
```

```text
Registry metadata != Capability
WorldIndex visibility != Authority
Feasibility result != Authority grant
LanguageAdapter output != Authority grant
```

## 11. Resolver architecture

```text
Selector<T>
→ ResolverQuery<T>
→ WorldIndexSnapshot
→ CandidateSet<T>
→ visibility/type/uniqueness
→ authoritative revalidation
→ Ref<T>
```

Lexical item / selector proposal does not bypass this pipeline。

```text
Lexical meaning != Entity resolution
CandidateSet != Ref set
```

## 12. Feasibility architecture

```text
EvaluationInput
→ InterpretationBundle
→ NSR / SemanticAST / TypedMIR
→ KernelPlan
→ Assessment dimensions
→ FeasibilityReport
```

代表assessment:

```text
syntax
normalization / ambiguity
semantic_typing
resolution
registry
resource / energy
authority / lease
timing / integration
conservation / identity
```

Overall:

```text
Feasible
ConditionallyFeasible
Infeasible
Indeterminate
```

Unknown/range/lower-boundは第一級で保持する。

## 13. Planning / execution

```text
TypedMIR
→ static validation
→ resolver/index
→ PREPARE / evaluator planning
→ PreparedPlan / KernelPlan
→ Revalidate
→ control-plane COMMIT(initial atomic group)
→ MKI semantic operation realization
→ QUERY / SAMPLE / TRANSITION / ACTIVATE / DEACTIVATE
→ World Kernel boundary
→ authoritative world evolution + runtime realization
```

Dry-runはCOMMIT前に停止。

Unknown/underspecified fieldをplanning valueへ採用する場合は
`planning-inference.md`の`InferenceRecord` / `PlanningAssumption`境界を使用する。
source/NSRのUnknownを採用値で置換しない。候補選択はsource fidelity、mandatory obligations、
feasibilityを通過した後にのみoptimization objectiveを適用する。

Execution admissionは[`execution-admission.md`](execution-admission.md)が所有する。
各`KernelAtomicGroup`の`LocalAdmission`はmandatoryであり、`Incremental` modeでも
type / identity / Capability / Lease / conservation / accounting / runtime safetyを省略しない。
明示的`WholePlanPreflight`は全currently-modeled groupのcompletion assessmentだが、
reservation、authority grant、future completion guaranteeではない。later group failureは
既commit groupをrollbackせず、authoritative WorldState/Historyを保持する。

## 14. Runtime time

Portable coordinate:

```text
Instant
```

Scheduler metadata:

```text
RuntimeEpochID
RuntimeTickID
TickInterval
TickStamp = (epoch,tick,phase,ordinal)
```

```text
Physical time != runtime tick
Tick execution order != causal order
```

## 15. Scheduler phases

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

## 16. Event timing

```text
EventTimeRecord.effective_at
EventTimeRecord.committed_at
ResumeRecord.resumed_at
```

```text
CommitLatency   = committed_at - effective_at
DispatchLatency = resumed_at - committed_at
ResponseLatency = resumed_at - effective_at
```

## 17. Continuous processes

Runtimeはcontinuous physicsを `IntegratorContract` で近似する。

```text
Integrator approximation != physical law
```

continuous processのnormative modelはadmitted semantic model / contractが所有し、Integratorはその
意味を変更しない。active processのsemantic stateをruntime tick列そのものへ縮約してはならない。
ACTIVATEされたDynamicsProcessのmodel semanticsとnumerical substepsは`kernel-execution.md`の境界で分離する。

## 18. Replay

```text
ReplayManifest
TickRecord[]
```

```text
DeterministicReplay != Rewind
```

## 19. Evaluation mode

```text
source
→ adapter/normalize
→ NSR
→ typed elaboration
→ static checks
→ registry/index read
→ KernelPlan / estimates
→ FeasibilityReport
STOP
```

## 20. Execution mode

```text
source
→ adapter/normalize
→ NSR
→ typed elaboration
→ static checks
→ registry/index
→ PREPARE
→ scheduler admission
→ Revalidate
→ control-plane COMMIT
→ MKI semantic realization
→ lower World Kernel interactions
→ World Kernel boundary
→ runtime/world execution
→ COMPLETE | FAIL
```

## 21. Major boundaries

```text
Language-specific parse != NSR
AI proposal != semantic truth
Confidence != proof
Lexical meaning != Entity resolution
Cross-language conversion != direct translation
SemanticFingerprint != artifact content_hash
Unexpected result != undefined behavior
Evaluation != Execution
Estimate != Reservation
Feasibility != Authority grant
WorldIndex != WorldState
CandidateSet != Ref set
Reference != Identity != Authority != Ownership != State
Physical time != runtime tick
Event effective time != runtime commit time in general
Tick execution order != causal order
Integrator approximation != physical law
DeterministicReplay != Rewind
ReactionRule != ReactionPathway
Stoichiometry != RateLaw
Kinetics != Thermodynamics
Registry metadata != Capability
magic effect request != physical-law definition
World Kernel != DefinitionSource
semantic active effect != arbitrary runtime bookkeeping
Kernel interaction class != MKI primitive
runtime bookkeeping != semantic active-effect ownership
control-plane COMMIT != all future consequences already occurred
DEACTIVATE != rollback
```

全pipeline境界のcanonical conformance pathは`canonical-water-ball.md`を参照する。
