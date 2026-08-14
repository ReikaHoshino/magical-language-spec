# Planning Inference Reference — pre-v0.8

**Status:** normative planning-semantics contract.

## Purpose

source semanticsが明示的にUnknownまたはunderspecifiedな場合に、plannerが
`Estimate<T>`を作り、必要ならprovenance付き`PlanningAssumption<T>`として採用する境界を
定義する。normalization時の解釈候補選択、authority proof、runtime safety guarantee、
具体的なestimator coefficientは定義しない。

## Depends on

- `language-adapters.md`
- `machine-values.md`
- `feasibility.md`
- `world-index.md`
- `mki.md`
- `semantics.md`
- `security-sandbox.md`

## Key invariants

```text
Unknown != Estimate
Estimate != PlanningAssumption
PlanningAssumption != Observed
PlanningAssumption != Truth
NormalizationAmbiguity != PlanningInference
PlannerPrediction != RuntimeSafetyGuarantee
WorldIndexRevision != WorldRevision
```

inferenceまたはoptimizationは、明示されたsource value、constraint、または明示的Unknownを
書き換えてはならない。安価・安全・実装容易なplanを得るための変更も禁止する。

## 1. Layer boundary

```text
source / NSR semantic value
→ source-fidelity check
→ mandatory obligations
→ Estimate<T>
→ optional PlanningAssumption<T>
→ feasibility
→ optimization objective
→ PreparedPlan
```

`AmbiguityPolicy`は、sourceから得られた競合するsemantic interpretationを選択または拒否する。
planning inferenceは、選択済みsource semanticsがUnknown/underspecifiedのまま残った後にだけ
planning valueを推定する。planning resultをNSRへ書き戻してはならない。

採用順序は次の通りであり、後段が前段を弱めてはならない。

```text
1. source semantic fidelity
2. mandatory type / identity / conservation / authority / lease obligations
3. feasibility
4. optimization objective
```

初期default objectiveは、feasible candidate間のminimum estimated total Energyとする。
unknown Energyを0として比較してはならない。profileは別objective/tie-breakを定義できるが、
1〜3を満たさないcandidateを選択可能にしてはならない。

## 2. Unknown classification

semantic valueの正本は引き続きNSR上の`Unknown(reason)`である。次のclassificationは
diagnostic/planning metadataであり、Unknownを別valueへ変換しない。

```text
MissingArgument
ContextDependent
WorldDependent
ModelDependent
FutureDependent
Underdetermined
Unavailable
```

profileは追加classificationを名前空間付きidentifierとして拡張できる。追加classから
authority、identity、truth、observed stateを推論してはならない。

## 3. Inference criticality

```text
MustResolve
EstimateAllowed
Optional
```

- `MustResolve`: authoritative resolution/proof/reservation/revalidationが必要。推定値を採用して
  obligationを満たしてはならない。
- `EstimateAllowed`: source Unknownを保持したまま、bounded estimateをplanningに採用できる。
- `Optional`: 未解決でもoperationのmandatory correctnessを妨げない補助情報。

少なくとも次は`MustResolve`である。

```text
mandatory type
authoritative Ref / EntityID
conservation/accounting obligation
Capability
Lease
mandatory sandbox/runtime guard
```

AI/statistical outputはproposal/evidenceであり、`MustResolve`のproof、authority、observed truthに
昇格しない。

## 4. Estimator classes and InferenceRecord

estimator classは少なくとも次を区別する。

```text
DeterministicDerivation
ContextInference
WorldProjection
OptimizationInference
StatisticalPrediction
ProfileDefault
AIProposal
```

`InferenceRecord<T>`は少なくとも次を記録する。

```text
InferenceRecord<T> {
    record_id
    target { field_path, value_role }
    unknown { reason, classification }
    criticality
    estimate : Estimate<T>
    estimator { class, id?, revision?, trust }
    evidence_ids
    assumption_ids
    world_context? {
        world_index_revision : WorldIndexRevision
        source_world_revision : WorldRevision
    }
    selected_planning_value?
    selection?
    binding?
    validity?
    diagnostics
}
```

`WorldProjection`は両revisionを記録する。両者は対応関係を持ちうるが、同じrevision domainとして
比較・代用しない。model依存estimatorはidentity/revisionを記録する。

`selected_planning_value`はsource value、Observed、Truthではなく、対応する
`PlanningAssumption`の候補値である。selection rule/objective、evidence、boundsなしに採用しては
ならない。`MustResolve` recordからPlanningAssumptionを作ってはならない。

## 5. PlanningAssumption binding

```text
PrepareBound
CommitBound
Dynamic
```

- `PrepareBound`: PREPAREでplanを作成した時点に固定する。
- `CommitBound`: COMMIT直前のrevalidation時に再推定可能で、そのcommitted operationでは固定する。
- `Dynamic`: runtime中に意図的に再評価する。明示的なreactive/control semanticsと
  `CONSTRAIN`等へのloweringを必要とする。

bound assumptionはbinding point後に安定するMUST。環境変化を理由に暗黙にretarget、回避、
再推定してはならない。再推定が必要なら新しいPREPARE/COMMIT cycleまたは明示的Dynamic semantics
を用いる。

## 6. Terminal inference

omitted motion terminalのprecedenceは次の通り。

```text
ExplicitTerminal
→ SemanticTarget
→ WorldProjection
→ ProfileHorizon
```

`ExplicitTerminal`は推定ではなくsource constraintである。後段の候補は前段を上書きしない。
WorldProjectionがterminalを提案しても、source/NSR terminalは`Unknown`のまま保持する。

採用するterminal inferenceは、少なくとも次のいずれかによって有限にboundする。

```text
maximum inferred distance
maximum inferred duration
maximum Energy/resource budget
equivalent profile limit
```

target/obstacleが見つからないことをunbounded executionへ変換してはならない。debug fixtureの
`50 m`は明示的なsynthetic PlanningAssumptionであり、universal defaultではない。

## 7. Generation goal lowering

`generate X`はdesired-world-state goalであり、MKI data-plane primitiveではない。

```text
generate-goal
→ candidate realization plans
→ RESOLVE / OBSERVE / CHANNEL / TRANSFER / RECONFIGURE / CONSTRAIN
```

候補は、既存matterのtransfer/reconfiguration、compatible source materialからのassembly、
permitted transformation path等を使用できる。候補ごとにtype、identity、
conservation/accounting、authority、Leaseを独立に検証する。

`CREATE`、`GENERATE`その他の第7 primitiveを導入してはならない。realization不能またはmandatory
obligationが未解決なら、plannerは`Infeasible`または`Indeterminate`としてfail closedする。

## 8. Planner prediction and runtime safety

WorldIndex/world/profileから得たtrajectory/terminal predictionはplanning evidenceである。
PREPARE/COMMITでboundされたpredictionは、後から別entityがtrajectoryへ入っただけでは変化しない。

late world changeに反応するのは次の場合に限る。

- mandatory system safety invariantのruntime guardが作動する。
- source/planがcollision avoidance、tracking、dynamic retargeting等を明示的に要求し、
  Dynamic assumptionとreactive `CONSTRAIN` semanticsを持つ。

default executionは善意のcollision avoidanceを暗黙に追加しない。この規則はtype、identity、
authority、Lease、conservation/accounting、sandbox/emergency-stop等のmandatory guardを弱めない。

planning predictionはexecution-admission policyではない。`Incremental`と明示的
`WholePlanPreflight`のowner/precedence/diagnosticsは`execution-admission.md`が所有する。
preflightはsource/NSRのUnknown、Estimate、PlanningAssumption、PrepareBound/runtime-resolved
valueを相互変換せず、predictionをreservationやruntime safety guaranteeへ昇格しない。

## 9. Continuous control and cost

`horizontal`等のtrajectory constraintは、gravityをworld modelから削除する指定ではない。
必要なら`CONSTRAIN`/controllerへloweringし、continuous observation/actuationとして表す。

Energy accountingは少なくとも次を区別する。

```text
physical mechanical work
channel open / maintenance
control
observation / information
losses
```

idealized mechanical workが0でも、control/observation/channel/maintenance costが0とは限らない。
具体的model/profile coefficient、availability、Energy/resource/timing output contractは
`estimator-models.md`が所有する。

## 10. Machine-readable contract

`schemas/planning-inference.schema.json`は`InferenceRecord`、`PlanningAssumption`、
terminal policy、generation candidate/selection、prediction/reactive boundaryを定義する。
portable identifier/revision/quantityは`common-values.schema.json`、`Estimate<T>`は
`feasibility-report.schema.json`を再利用する。

fixtureとtestは次を証明する。

- 50 kg / 0.01 m / 50 m/s²等のexplicit source constraintをoptimizationが変更しない。
- source terminalはUnknownのまま、50 mは別のPrepareBound PlanningAssumptionになる。
- selected generation planは既存6 MKI primitiveのみを使用する。
- inferred evidenceだけでmandatory obligationを満たせない。
- bound predictionと明示的Dynamic/CONSTRAIN behaviorが区別される。

`canonical-water-ball.md`と`examples/canonical-water-ball/`は、これらのplanning ruleを
NaturalLanguageSourceからCOMMIT/World Historyまで同じsemantic pathでexerciseする。

`PlanningAssumption`は未指定値をplanningへ採用する契約である。複数Measurementから事実仮説を
評価する`EvidenceFusionModel`ではない。evidence fusionのconfidence/rankingはplanning default、
Identity、Capability、Lease、observed Truthを生成しない。ownerは`evidence-inference.md`とする。
