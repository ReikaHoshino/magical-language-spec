# Canonical Water-Ball End-to-End Example — pre-v0.8

**Status:** normative conformance path + synthetic fixture data.

## Purpose

一つの意図的に異常なwater-ball入力を、natural-language sourceからWorld State/History effectまで
全層で追跡する。v0.8 Local Evaluatorとv0.9 sandbox runtimeは、別の意味論を作らず同じ
conformance pathを消費する。

Normative machine-readable artifacts:

```text
schemas/canonical-water-ball.schema.json
examples/canonical-water-ball/pipeline.json
examples/canonical-water-ball/failure-cases.json
examples/canonical-water-ball/traceability.json
```

関連する既存fixture:

```text
examples/planning-inference/pathological-water-ball-bound.json
examples/planning-inference/pathological-water-ball-dynamic.json
examples/estimator-profiles/synthetic-reference-v1.json
```

## Key invariants

```text
NaturalLanguageSource != NSR != SemanticAST != TypedMIR != KernelPlan
SourceUnknown != Estimate != PlanningAssumption != Observed != AuthoritativeTruth
generate goal != MKI primitive
EstimatorOutput != MandatoryProof
WorldIndexRevision != WorldRevision
Physical time != runtime tick
PlannerPrediction != RuntimeSafetyGuarantee
SyntheticFixtureValue != UniversalWorldConstant
```

## 1. Canonical source

Canonical surface fixture:

```text
Generate a 50 kg water ball of radius 0.01 m three metres ahead
from rest and accelerate it horizontally at 50 m/s^2.
```

このEnglish surfaceは`adapter_id = eng`のconformance inputであり、English adapterの完全実装を
本Issueで提供するものではない。portable semanticsの正本は選択済みNSR以降である。
Latin sourceをこのfixtureの権威ある代替として捏造しない。Latinを追加する場合は
`reference/latin-frontend.md`のlexicon/morphology/frame evidence contractを通すMUST。

v0.8 Local Evaluatorのcanonical conformanceでは、`WB-CANON-001`を選択済みNSR /
structured fixtureからevaluatorへ入力する。English surfaceはsource fidelityとprovenanceの
証拠として保持するが、v0.8が`eng` source→NSR adapterを実装・検証済みであるとは主張しない。
source→NSR frontend conformanceはreference `lat` corpusが担当する。SemanticAST / TypedMIR等を
stableな外部direct-entry artifactとして受理する一般契約はpre-public archive Issue #48へdeferする。

次の値はsourceが明示しているため、異常・高cost・実装困難でも変更しない。

| Field | Source value | Classification |
|---|---:|---|
| material | water | exact source semantic value |
| mass | 50 kg | exact source semantic value |
| radius | 0.01 m | exact source semantic value |
| relative distance | 3 m | exact source semantic value |
| initial velocity | 0 m/s | exact source semantic value |
| acceleration | 50 m/s² | exact source semantic value |
| trajectory | horizontal-forward | exact source semantic value |
| terminal | omitted | `Unknown(MissingArgument)` |

安価なplanを得るためにmass/radius/accelerationを補正してはならない。

## 2. Pipeline and ownership

| Stage | Representation | Owner / authority | Failure boundary |
|---|---|---|---|
| Natural-language source | exact UTF-8 text | source + LanguageAdapter | invalid encoding/scalar |
| source normalization | normalized text + mapping/profile | common normalization contract | normalization rejection |
| candidate set | StrictReject decision | adapter/profile | unresolved semantic ambiguity |
| NSR | `GenerationCommand` | language-independent specification | schema/semantic drift |
| SemanticAST | `GenerationGoal` | specification | invalid semantic structure |
| TypedMIR | typed desired-state goal/effects | deterministic elaborator | type/dimension/effect error |
| resolver/registry inputs | revisioned registry/index/evidence | Registry + World | unresolved/ambiguous identity |
| KernelPlan | selected six-primitive plan | planner | mandatory obligation/feasibility failure |
| Feasibility/PREPARE | report, estimates, proof/reservation evidence | evaluator + domain owners | Indeterminate/Infeasible |
| runtime schedule/COMMIT | revalidation, event time, TickStamp | RuntimeProfile + runtime | abort before world effect |
| World State/History | new revision + event | authoritative world/history | no effect on aborted COMMIT |

各stageは前段の表現を上書きせず、source map/evidenceまたはstable representation IDで接続する。

## 3. NSR, SemanticAST, and TypedMIR

NSRはsource valueをlanguage-independent role/valueへ写す。terminal omissionはsemantic value位置の
`Unknown(MissingArgument)`として保持する。`SemanticFingerprintV1`はNSR semantic projectionの
同一性確認に使用し、artifact `content_hash`へ代用しない。

SemanticASTは`GenerationGoal`、TypedMIRは`DesiredWorldState`として表す。
`generate`をgrammar/MKIへ第7 primitiveとして追加しない。TypedMIRのeffectsは、候補planが必要と
しうる既存operation/effect境界を宣言する。

```text
generate desired state
→ candidate realization plans
→ RESOLVE / OBSERVE / CHANNEL / TRANSFER / RECONFIGURE / CONSTRAIN
```

## 4. Resolution, authority, and conservation

PREPAREは少なくとも次を別々に確認する。

```text
SemanticRegistry contract/revision
WorldIndexRevision
source WorldRevision
authoritative source EntityID/state revision
Capability
write Lease
matter/Energy conservation ledger
RuntimeProfile compatibility
```

WorldIndex candidateはEntity、authority、observed truthではない。type、identity、conservation、
Capability、Leaseのmandatory obligationをestimateやPlanningAssumptionで満たしてはならない。

## 5. Terminal inference and binding

source terminalは引き続き`Unknown(MissingArgument)`である。canonical fixtureは別layerで:

```text
Estimate<Length> = Exact(50 m)
PlanningAssumption = assumption:terminal:50m-debug
binding = PrepareBound(PREPARE)
```

を記録する。`50 m`はsynthetic fixture horizonでありsource semantics、world truth、universal
defaultではない。

PrepareBound後のlate world changeでterminalを暗黙retargetしない。明示的reactive behaviorは
`pathological-water-ball-dynamic.json`の`Dynamic` bindingと`CONSTRAIN`へloweringする。
mandatory runtime invariantが失敗した場合はrevalidation/COMMITをabortする。

## 6. Estimation and plan selection

Energy/resource/timing estimateは`estimator-models.md`のprofile/model identity、revision、
owner、unit/dimension、availabilityを使用する。canonical valuesは
`SyntheticFixtureOnly`でありworld constantではない。

default selection order:

```text
1. SourceSemanticFidelity
2. MandatoryObligations
3. Feasibility
4. minimum estimated total Energy
```

したがって、explicit sourceを変更した安価なcandidate、mandatory proofのないcandidate、
Indeterminate/Infeasible candidateはEnergy比較対象にならない。eligible candidate間だけで
200 J planを260 J planより先に選択する。

## 7. PREPARE, runtime, and world effect

FeasibilityReportはexecutionではない。PREPARE成功後もruntimeはCOMMIT直前にEntity/state
revision、Capability、Lease、conservation guardを再検証する。

canonical success path:

```text
PreparedPlan
→ Revalidate(Pass)
→ COMMIT
→ Matter TRANSFER / RECONFIGURE effect
→ WorldRevision world:991 → world:992
→ History event event:wb-canon-001
```

`effective_at`と`committed_at`は別fieldであり、TickStampはexecution ordering metadataである。
TickIDをphysical durationへ変換しない。

failure pathではRevalidateまたはCOMMITがabortし、successful WorldRevision/History effectを
発行しない。

## 8. Failure catalog

`failure-cases.json`はstable `WB-FAIL-*` IDsで次を網羅する。

- parse/source-normalization rejection
- ambiguity rejection
- type/dimension error
- resolution failure/ambiguity
- authority/Lease failure
- conservation/source-material failure
- unavailable estimator model
- MustResolve inference rejection
- explicit-source drift rejection
- invalid Energy-based plan selection
- PrepareBound/Dynamic binding violation
- runtime revalidation failure

## 9. Traceability

`traceability.json`の`WB-RULE-*` IDsはnormative ownerを、`WB-TEST-*` / `WB-FAIL-*`は
再実行可能なregressionまたはfailure caseを指す。pre-public archive Issue #36/pre-public archive Issue #37はIDを再利用・拡張し、pre-public archive Issue #38で
conformance setをfreezeできる。既存IDの意味を別ruleへ再利用してはならない。

Regression entry points:

```text
python tests/validate_schemas.py
python -m unittest tests.test_canonical_water_ball -v
```
