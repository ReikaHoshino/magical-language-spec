# Estimator Model and Profile Ownership — pre-v0.8

**Status:** normative Energy/resource/timing estimator contract.

## Purpose

Feasibility Evaluatorとplannerが使用するEnergy、resource、timingのmodel identity、
revision、coefficient ownership、estimate provenanceを定義する。具体値やalgorithmを
universal physical lawとして固定する文書ではない。

## Depends on

- `scope-and-ownership.md`
- `machine-values.md`
- `compatibility.md`
- `planning-inference.md`
- `feasibility.md`
- `runtime-time.md`

## Key invariants

```text
SourceSemanticValue != Estimate != PlanningAssumption
Estimate != Reservation
EstimatorOutput != MandatoryProof
UnavailableModel != zero
SyntheticFixtureValue != UniversalWorldConstant
Physical time != runtime tick
Shared metadata rules != shared compatibility algorithm
```

estimatorは明示的source valueまたはsource上の`Unknown(reason)`を書き換えないMUST。
estimator resultをplanning valueとして採用する場合は、
`planning-inference.md`の`InferenceRecord<T>`、`PlanningAssumption<T>`、criticality、
bindingを再利用するMUST。

## 1. EstimatorProfile

machine-readable `EstimatorProfile` はcore artifact metadata envelopeを使用し、少なくとも
次を保持する。

```text
EstimatorProfile {
    metadata {
        artifact_id
        revision
        provenance
        compatibility
    }
    profile_kind
    scope
    runtime_profile_requirement
    models
    reference_cases?
}
```

`metadata.compatibility`はdomain-owned declarationであり、hash equalityまたは共通boolean
algorithmを互換性判定へ導入しない。generic artifact `content_hash`のcanonicalization方式も
本contractでは決定しない。

## 2. Model identity and availability

各modelは次を明示するMUST。

```text
EstimatorModel {
    model_id
    revision
    domain : Energy | Resource | Timing
    category
    owner
    availability
    input_contract
    output_contract
    evaluation_rule?
    coefficients?
}
```

model依存estimateには`model_id`と`revision`が必要である。必要modelがない、取得できない、
または要求profileと非互換の場合、evaluatorは値を捏造せず`Unknown(ModelDependent)`、
`Unknown(Unavailable)`、または全体`Indeterminate`を返す。

`Unavailable` modelはcoefficientやevaluation ruleを持たず、利用不能理由を記録する。
missing modelをzero-cost modelとして扱ってはならない。

## 3. DefinitionSource and coefficient ownership

modelおよび各coefficientは`DefinitionSource`とowner identity/revision/evidenceを保持する。
許可されるconcrete model ownerは次である。

```text
Implementation
Registry
World
Profile
```

仕様はrecord shape、境界、dimension requirementを所有するが、concrete physical/model
coefficient自体を暗黙の`Specification` constantとして所有しない。ownerごとの責任は
`scope-and-ownership.md`に従う。

- `Registry`: revisioned model/entryとして定義された値。
- `World`: authoritative world/model contextに依存する値。
- `Profile`: runtime/evaluator policyまたはbounded fixtureとして定義された値。
- `Implementation`: documented algorithm/provider固有値。semantic contractを変更しない。

coefficientはsemantic type、完全なSI dimension、unitを持つ。dimension equalityだけで
semantic type equalityを証明しない。

## 4. Energy models

Energy outputは`Quantity<Energy, kg m^2 s^-2>`である。breakdownは少なくとも次を区別する。

```text
physical_work
reaction_or_thermodynamic
channel_open
channel_maintenance
control
observation_information
synchronization
losses
reserved_margin
```

unknown componentを0としてtotalへ合算しない。totalを作れるのは、採用profileのaccounting
boundaryの下で必要componentがExact/boundedであり、unit/dimensionが整合する場合だけである。

## 5. Resource models

resource modelはEnergy以外のquantity、payload、channel、observation、information/control
budget等を対象にできる。input contractとoutput semantic type/dimensionを明示するMUST。

model入力がUnknownの場合、modelがsound boundを提供できると宣言した場合にだけ
`Range`/boundを返せる。それ以外は`Unknown`とする。estimateのuncertainty、evidence、
採用assumptionを保持する。

## 6. Timing models

timing estimateは対応する`RuntimeProfile` identity/revisionおよびcompatibility profileを
参照する。physical durationは`Quantity<Time, s>`として表現する。

`RuntimeTickID`はscheduler ordering metadataであり、durationでもphysical lawでもない。
tick countやtick identityをphysical secondsへ暗黙変換してはならない。scheduler/integrator
contractを利用したtiming estimateでも、物理時間とruntime tickの両domainを分離する。

```text
Physical time != runtime tick
Integrator approximation != physical law
```

## 7. Estimate, uncertainty, and adoption

estimator outputは`Exact`、`Range`、bounds、`Distribution`、`Unknown`のいずれかとして、
model identity/revision、uncertainty、evidenceを保持する。

planningでestimateを採用する場合:

1. source valueは変更しない。
2. `criticality = EstimateAllowed`または`Optional`である。
3. `InferenceRecord<T>`を作る。
4. 採用値は別の`PlanningAssumption<T>`として記録する。
5. `PrepareBound`、`CommitBound`、`Dynamic`のbindingを明示する。

mandatory type、identity、conservation、authority、Leaseは`MustResolve`であり、
estimator outputだけを根拠に`Verified`/`Reserved`へ昇格しない。必要evidence、proof、
reservation、runtime guardが得られない場合は`Indeterminate`または失敗とする。

## 8. Synthetic reference profile

`examples/estimator-profiles/synthetic-reference-v1.json`はdeterministic regression用である。
その値とruleは`SyntheticFixtureOnly` scopeを持ち、universal world constant、default physics、
またはdeployment recommendationではない。

synthetic profileは:

- 9つのEnergy categoryを区別する。
- resourceとphysical-duration modelを含む。
- unavailable modelを`Unknown`へ落とすcaseを含む。
- source semanticsをestimate前後で同一に保つ。
- PlanningAssumption adoptionとmandatory obligationの境界を例示する。

## 9. Machine-readable contract

Normative schema:

```text
schemas/estimator-profile.schema.json
```

Normative regression entry points:

```text
python tests/validate_schemas.py
python -m unittest tests.test_estimator_profile -v
```

JSON Schemaで表せないmodel/reference link、coefficient/result一致、source immutability、
dimension consistencyはsemantic regression testで検証する。
