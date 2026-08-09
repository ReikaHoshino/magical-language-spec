# Feasibility Evaluator Reference — v0.7.3

**Status:** normative report contract + informative examples.

## Purpose

自然言語/IRを実行せず、LanguageAdapter/NSRを含む複数抽象度で解釈し、必要Energy・resource・authority・timing・uncertainty・failure候補を評価するdry-run contractを定義する。

## Non-goals

- world stateを変更しない。
- Capability/Leaseを発行しない。
- AI outputをsemantic truthとして扱わない。
- 未知値を0や恣意的代表値で埋めない。
- UI/estimate algorithmを固定しない。

## Depends on

- `conventions.md`
- `architecture.md`
- `language-adapters.md`
- `types.md`
- `world-index.md`
- `runtime-time.md`
- `registry.md`
- `mki.md`
- `planning-inference.md`
- `estimator-models.md`

## Key invariants

```text
Evaluation != Execution
Estimate != Reservation
Feasibility != Authority grant
AI proposal != semantic truth
Unknown != zero
Unknown != Estimate != PlanningAssumption
PlannerPrediction != RuntimeSafetyGuarantee
Display unit != internal SI normalization
```

## 1. Pipeline

Natural-language input:

```text
EvaluationInput
→ LanguageAdapter<L>
→ NormalizationCandidateSet
→ AmbiguityPolicy
→ NSR
→ SemanticAST
→ TypedMIR
→ KernelPlan
→ assessments
→ FeasibilityReport
```

IR inputは存在しない上位stageを生成しなくてよい。

## 2. EvaluationInput

```text
NaturalLanguageSource {
    adapter_id
    source_text
    external_language_tags?
    adapter_revision?
}

HighLevelSource
NSR
SemanticAST
TypedMIR
NormalizedIR
StructuredInput
```

`LatinSource` は互換aliasとして `NaturalLanguageSource(adapter_id=lat)` に精緻化可能。

inputはsource-evidence hash/revisionを記録するSHOULD。source-evidence hashは
`machine-values.md` の`source-evidence` scopeを使用し、generic artifact
`content_hash`やregistry hashとして扱わない。

## 3. InterpretationBundle

```text
InterpretationBundle {
    surface_analysis?
    normalization_candidates?
    normalization_decision?
    nsr?
    semantic_ast?
    typed_mir?
    kernel_plan?
}
```

各level間のsource map/provenanceを保持するSHOULD。

## 4. NormalizationAssessment — v0.7.3

```text
NormalizationAssessment {
    adapter_id
    adapter_revision
    provider
    candidate_count
    selected_candidate?
    ambiguity_policy
    unresolved_fields
    semantic_fingerprint?
    diagnostics
    evidence
}
```

`semantic_fingerprint` は指定される場合
`sf:v1:sha256:<64 lowercase hexadecimal digits>` 形式の
`SemanticFingerprintV1` とする。generic artifact `content_hash` とは別domainである。
report内のfree-text assumptions/evidence/provider metadataは、structured NSR semantic
contentに符号化されない限りfingerprintへ注入しない。

`registry_hash` はnullまたは`machine-values.md`の`registry-contract-set` scoped hash
recordとする。hash equalityはregistry compatibilityを決めない。input `hash` とNSR
`provenance.source_hash` はsource evidence traceability用であり、artifact/registry hashと
相互代用しない。

assessment dimensionに:

```text
normalization
```

を追加する。

StrictRejectでsemantic-critical candidateが複数なら`Pass`へ丸めない。

LegacyPermissiveでcandidateが選択された場合も、warning/provenanceを保持するSHOULD。

## 5. Cross-language assessment

conversion/renderer利用時:

```text
CrossLanguageAssessment {
    source_adapter
    target_adapter
    renderer_revision
    fingerprint_before
    fingerprint_after?
    round_trip_status
    diagnostics
}
```

fingerprint不一致:

```text
CrossLanguageDrift
```

## 6. KernelPlan

```text
KernelPlan {
    operations
    selectors
    observations
    channels
    transfers
    reconfigurations
    constraints
    control_plane_requirements
    capabilities
    leases
    accounting_obligations
    timing_requirements
    revalidation_requirements
}
```

KernelPlanはEvent logではない。

## 7. Estimate<T>

```text
Exact(value)
Range(min,max)
LowerBound(value)
UpperBound(value)
Distribution(summary)
Unknown(reason)
```

可能な限りuncertainty/assumptions/evidence/validityを持つ。

```text
known + unknown != known
```

Unknownからplanning valueを採用する場合、source/NSR Unknownを変更せず、
`planning-inference.md`のprovenance付き`InferenceRecord<T>`と
`PlanningAssumption<T>`を別に記録する。mandatory type / identity / conservation /
authority / Leaseは推定だけで`Pass`にしてはならない。

## 8. EnergyEstimate

内部値:

```text
Quantity<Energy>
kg m^2 s^-2
```

```text
EnergyBreakdown {
    physical_work
    reaction_or_thermodynamic
    channel_open
    channel_maintenance
    control
    observation_information
    synchronization
    losses
    reserved_margin
}
```

人間向けdefault profileではkJ表示を推奨。

未知componentを0としてtotalへ合算しない。

model identity/revision、coefficient owner、availability、synthetic profile境界は
`estimator-models.md`に従う。modelが利用不能なら値を捏造せず
`Unknown(ModelDependent|Unavailable)`または全体`Indeterminate`とする。

## 9. ResourceAssessment

Energy以外:

```text
Momentum / Charge
MatterPayload / Species
Channel requirements
observation resolution
information/control budget
scheduler/integrator profile
```

resource modelのinput/output contract、DefinitionSource、coefficient provenanceは
`estimator-models.md`に従う。synthetic fixture値をworld constantへ昇格しない。

## 10. ResolutionAssessment

World Indexをread-only evidenceとして利用可能。

```text
selector
index revision
source world revision
candidate evidence
resolved Ref?
consistency policy
revalidation requirement
```

```text
Resolved Ref != mutation permission
Lexical meaning != Entity resolution
```

## 11. AuthorityAssessment

```text
required
available_if_known
missing
lease_requirements
known_conflicts
```

runtime authority snapshotがなければ`Indeterminate`/Conditionalとしてよい。

## 12. TimingAssessment

```text
channel propagation
physical execution estimate
commit latency requirement/bound
dispatch latency requirement/bound
controller timing
integration error budget
scheduler assumptions
```

timing estimatorは対応するRuntimeProfile identity/revisionを記録する。
physical durationはTime quantityであり、RuntimeTickIDをdurationへ代用しない。

```text
effective_at
committed_at
resumed_at
```

を混同しない。

Persistent ControllerのFeasibilityはobservation resolution、sample period、event latency、jitter、
target mass/momentum、impulse/Energy ceiling、saturation/overloadをmodel/profile evidenceとともに
評価する。estimateだけでper-actuation Capability/Lease、Anchor identity、accountingを満たしてはならない。

## 13. Assessment dimensions

```text
syntax
normalization
semantic_typing
resolution
registry
resource
energy
authority
lease
timing
integration
conservation
identity
cross_language? 
```

各dimensionはstatus + diagnostics + evidenceを持てる。

## 14. Overall status

```text
Feasible
ConditionallyFeasible
Infeasible
Indeterminate
```

優先規則:

1. mandatory contradiction/prohibition proven → `Infeasible`。
2. explicit conditions required → `ConditionallyFeasible`。
3. mandatory judgement evidence不足 → `Indeterminate`。
4. mandatory項目pass → `Feasible`。

LegacyPermissiveで曖昧性を解消しただけでは、自動的に`Feasible`にはならない。

## 15. PredictedDiagnostic

```text
PredictedDiagnostic {
    stage
    code
    severity
    cause
    evidence
}
```

例:

```text
NORMALIZE / AmbiguousNormalization / conditional
NORMALIZE / CrossLanguageDrift / fatal
PREPARE  / AuthorityError / fatal
RESOLVE  / IndexStale / conditional
PLANNING / EnergyModelUnavailable / unknown
```

## 16. Provenance

reportは可能な範囲で:

```text
schema_version
spec_version
input_hash
adapter_id/revision?
normalizer_provider?
ambiguity_policy?
semantic_fingerprint?
registry_hash?
world_index_revision?
source_world_revision?
runtime_profile?
created_at?
assumptions[]
evidence[]
```

を保持する。

## 17. Human-readable abstraction levels

v1.0 local evaluator目標:

1. Surface analysis。
2. Normalization candidates / NSR。
3. Semantic AST。
4. Typed MIR。
5. Kernel plan。
6. Feasibility report。

ユーザーは抽象度を選択できるSHOULD。

## 18. Latin example

```text
Calorem ab aqua ad aerem transfer.
```

```text
Adapter : lat
Patient : calor -> Energy/Thermal
Source  : aqua -> SelectorProposal
Goal    : aer  -> SelectorProposal
Quantity: Unknown
```

Quantityがないためrequired Energy totalを自動数値化しない。

## 19. Cross-language example

同一NSRをjpn/ger等へrender可能。

conversion後にrenormalizeしSemanticFingerprintを比較できる。

v0.7.3時点ではrenderer未実装のため、real source round-tripではなく
NSR-layer adapter equivalence fixtureのみを提供する。

## 20. Machine-readable schema

- `../schemas/feasibility-report.schema.json`
- `../schemas/nsr.schema.json`
- `../schemas/canonical-water-ball.schema.json`

例:

- `../examples/feasibility-report.json`
- `../examples/cross-language-normalization.md`
- `canonical-water-ball.md`
- `../examples/canonical-water-ball/pipeline.json`

## 21. Definition ownership

- report/NSRの必須意味: specified。
- adapter/parser/estimate algorithm: implementation-defined、provenance記録MUST。
- lexicon/semantic mapping: adapter/registry/profile-defined。
- AI provider/model: implementation/profile-defined、untrusted candidate。
- display unit/style: profile-defined。
- physical constants/model: registry/world/profile-defined出所を記録MUST。
