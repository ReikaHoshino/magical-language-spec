# Error Reference — v0.7.3

**Status:** normative names/stage boundaries; diagnostic payload details may be implementation-defined.

Security/sandbox/cancellation diagnostics are specified with their threat and fail policy in
[`security-sandbox.md`](security-sandbox.md).

## 0. Ingress / security

```text
InputLimitExceeded
StructuredInputInvalid
ExecutableDataInjection
ArtifactTrustFailure
SandboxProfileUnavailable
SandboxProfileMismatch
SandboxPolicyDenied
SandboxLimitExceeded
```

- `InputLimitExceeded`: byte/depth/item/work limitをingressで超過。
- `StructuredInputInvalid`: external structured inputがschema/representation contractを満たさない。
- `ExecutableDataInjection`: data/evidence fieldがexecutable/control/authority positionへ昇格しようとした。
- `ArtifactTrustFailure`: configured trust source/admission、identity/revision、dependency trustを確立できない。
- `SandboxProfileUnavailable`: required SandboxProfileを取得できない。
- `SandboxProfileMismatch`: profile schema/revision/required enforcementまたはruntime compatibilityが不成立。
- `SandboxPolicyDenied`: semantically validかつauthorizedでもsandbox restrictionがoperationを拒否。
- `SandboxLimitExceeded`: stage-specific codeがないsandbox resource/effect ceiling超過。

### 0.1 Compatibility / admission

```text
CompatibilityUndetermined
CompatibilityProfileUnsupported
CompatibilityEvidenceMissing
SpecVersionIncompatible
SchemaVersionIncompatible
RuntimeProfileIncompatible
AdapterIncompatible
AdapterCompatibilityUndetermined
SemanticFingerprintProfileMismatch
```

- `CompatibilityUndetermined`: owning profile/evidence/negotiation不足によりcompatibleとも
  incompatibleとも証明できない。
- `CompatibilityProfileUnsupported`: required compatibility profile/revisionをconsumerが
  実装していない。
- `CompatibilityEvidenceMissing`: owning profileが必須とするevidenceがない。
- `SpecVersionIncompatible`: explicit accepted/migration profileがproducer spec versionを拒否。
- `SchemaVersionIncompatible`: schema identity/versionがconsumer profileのsupport外。
- `RuntimeProfileIncompatible`: 必須runtime component contractが不成立。
- `AdapterIncompatible`: adapter profileが明示的な不一致を証明。
- `AdapterCompatibilityUndetermined`: adapter/lexicon/grammar/normalizer revision relationを
  profileから決定できない。
- `SemanticFingerprintProfileMismatch`: fingerprint comparison profileが異なるまたは
  unsupported。semantic inequalityの証明ではない。

共通result envelopeは [`compatibility.md`](compatibility.md) を参照する。
domain-specificな`RegistryMismatch`、`IndexSchemaMismatch`、`ReplayIncompatible`等は
引き続き具体原因を表す。

v1.x evolution / migrationのstable diagnostics:

- `ReleaseVersionInvalid`: release versionがstrict `MAJOR.MINOR.PATCH`でない。
- `StableContractChangeWithinMajor`: required-core/stable-public contractを同一major内で
  再解釈または削除しようとした。
- `StableContractRemovalWithinMajor`: deprecation removal boundaryがstable majorを越えない。
- `MigrationPathMissing`: exact source/target/domain migrationが宣言されていない。
- `MigrationPathAmbiguous`: exact relationに複数pathがあり一意選択できない。
- `MigrationImplementationMissing`: named transformation implementationが利用できない。
- `MigratedArtifactInvalid`: migrated outputがtarget schema validationに失敗。
- `PostMigrationIncompatible`: migration後のdomain-owned compatibility resultが`Incompatible`。
- `PostMigrationCompatibilityUndetermined`: migration後のcompatibilityを証明できない。
- `PostMigrationCompatibilityProfileMismatch`: migration後のdecisionがtargetに指定された
  domain/profile identity/revisionで評価されていない。

これらは[`versioning-and-migration.md`](versioning-and-migration.md)が所有する。

## 1. Frontend / normalization — v0.7.3

```text
LanguageAdapterUnavailable
InvalidUTF8
InvalidUnicodeScalar
UnsupportedSourceCharacter
InvalidAdapterID
InvalidExternalLanguageTag
InvalidScriptTag
LexiconEntryMissing
MorphologicalAnalysisIncomplete
SemanticRoleAmbiguous
NormalizationFailed
AmbiguousNormalization
UnsafePermissiveNormalization
NormalizationBudgetExceeded
RendererUnavailable
CrossLanguageDrift
UnsupportedSemanticExtension
SemanticFingerprintRepresentationError
UnknownSummaryContradiction
```

- `LanguageAdapterUnavailable`: requested project adapter ID/revisionを提供できない。
- `InvalidUTF8`: byte-boundary sourceがwell-formed UTF-8ではない。
- `InvalidUnicodeScalar`: in-memory sourceにsurrogate等のUnicode scalarではない値がある。
- `UnsupportedSourceCharacter`: well-formed scalarだがV1 source transportで受理しない文字がある。
- `InvalidAdapterID`: 明示されたproject adapter IDがproject syntaxを満たさない。
- `InvalidExternalLanguageTag`: external language-tag metadataがsupported syntaxを満たさない。
- `InvalidScriptTag`: script hint metadataがfour-letter ISO 15924 style syntaxを満たさない。
- `LexiconEntryMissing`: required lexical/domain entryが得られない。
- `MorphologicalAnalysisIncomplete`: morphologyが必要なprofileで解析が不足。
- `SemanticRoleAmbiguous`: semantic-critical roleが一意化できない。
- `NormalizationFailed`: usable NSR candidateを生成できない。
- `AmbiguousNormalization`: 複数のsemantic-critical candidateが残る。
- `UnsafePermissiveNormalization`: permissive policyで選択してもmandatory safety boundaryを満たせない。
- `NormalizationBudgetExceeded`: candidate expansion/provider/tool/work budget内でnormalizationを完了できない。
- `AmbiguityInteractionRequired`: `InteractiveResolve`が外部の明示的選択を待っている。
- `AmbiguityDecisionUnreproducible`: required profile/context/evidence/revisionを再現できず決定不能。
- `AmbiguityContextDrift`: recorded decisionと現在のcontext snapshot/revisionが異なる。
- `AmbiguityReplayDivergence`: compatibleと判断したambiguity trace入力から異なるselectionを再計算した。
- `RendererUnavailable`: target language renderer/profileを利用できない。
- `CrossLanguageDrift`: render→renormalize後のsemantic fingerprintが一致しない。
- `UnsupportedSemanticExtension`: Projection V1がsemantic/provenance classificationを決められないNSR extension。
- `SemanticFingerprintRepresentationError`: JCS/I-JSONで意味を保って表現できないprojection value。
- `UnknownSummaryContradiction`: top-level diagnostic unknown summaryがsemantic Unknown occurrenceと矛盾。

`AmbiguousNormalization` はpolicyによりfatalとは限らない。

```text
StrictReject              -> fatal/Indeterminate or Infeasible
InteractiveResolve        -> pending/Conditional
ContextualDeterministic   -> resolved if evidence/tie-break valid
LegacyPermissive          -> may select valid candidate with warning
```

ただしconfidenceだけでmandatory semantic ambiguityを証明済みとしてはならない。

## 2. Compile / elaboration

```text
ParseError
DuplicateBinding
UnresolvedName
AmbiguousCaseError
AmbiguousFrameError
TypeError
DimensionError
PayloadTypeError
ObserverModelTypeError
UnknownSpeciesError
StructureSchemaMismatch
ReactionTypeError
RateLawTypeError
StaticAuthorityError
EffectError
EffectMismatch
ReturnTypeError
TerminationProofFailure
LifetimeError
UseAfterMove
TemporalTypeError
SuspendWithExclusiveLeaseError
UnboundedAsyncEffect
UnboundedSelectionError
```

- `DuplicateBinding`: 同じscope・name classへ同名bindingを複数導入した。
- `UnresolvedName`: syntax positionが要求するlexical、callable、またはtype namespaceで
  identifierを解決できない。

`DuplicateBinding` と `UnresolvedName` はparse成功後のstatic semantic validationで
報告する。registry entryやWorld Index上の対象が存在しないことを、これらのdiagnosticへ
置き換えてはならない。scope、namespace、lookup順序の正本は
`reference/mir-name-resolution.md` とする。

## 3. Evaluation / report construction

```text
EvaluationInputUnsupported
EvaluationStageUnavailable
EstimatorModelUnavailable
EnergyModelUnavailable
ResourceEstimateIncomplete
MissingEvaluationEvidence
ReportSchemaMismatch
```

- `EstimatorModelUnavailable`: required Energy/resource/timing model identity/revisionまたは
  compatible modelを利用できない。`Unknown`/`Indeterminate`として扱い、0を捏造しない。
- `EnergyModelUnavailable`: Energy component model不足。`EstimatorModelUnavailable`の
  Energy-specific diagnostic。0として扱わない。
- `MissingEvaluationEvidence`: 判定証拠不足。
- `ReportSchemaMismatch`: report schema非互換。

Frontend/normalization diagnosticsは `PredictedDiagnostic` としてFeasibilityReportへ保持できる。

## 4. Load / PREPARE / resolver / planning

```text
RegistryMismatch
IndexSchemaMismatch
IndexUnavailable
IndexStale
IndexConsistencyFailure
QueryBudgetExceeded
UnsupportedTransferKind
AccountingProfileError
ConservationProofFailure
ReactionUnavailable
KineticModelUnavailable
KineticModelDomainError
PathwayUnavailable
CatalystRequirementUnsatisfied
DeadlineInfeasible
ResolutionFailure
LeaseConflict
InsufficientMaterial
InsufficientBudget
ChannelUnavailable
AuthorityError
ScheduledAuthorityFailure
InvalidEventSubscription
InsufficientTemporalPrecision
SchedulerPolicyUnavailable
TemporalToleranceUnsatisfied
ControllerTimingUnsatisfied
InferenceForbidden
SourceSemanticDrift
InvalidPlanSelection
PlanningBindingViolation
```

- `InferenceForbidden`: `MustResolve` obligationをEstimate/PlanningAssumptionだけで満たそうとした。
- `SourceSemanticDrift`: inference、optimization、loweringがexplicit source semanticsを変更した。
- `InvalidPlanSelection`: source fidelity、mandatory obligation、feasibility、profile objectiveの
  orderingに反するcandidateを選択した。
- `PlanningBindingViolation`: PrepareBound/CommitBound valueをbinding後に暗黙再推定・retargetした、
  またはDynamic behaviorを明示的reactive semanticsなしに適用した。

## 5. Runtime

```text
EmergencyStopRequested
EmergencyStopIncomplete
CommitOutcomeIndeterminate
ConstraintSaturation
ResourceExhaustion
ObservationFailure
SpectralObservationFailure
ChannelFailure
Timeout
TransferFailed
ReconfigurationFailure
KineticIntegrationFailure
CatalystDeactivated
SelectionTruncated
MicrostepBudgetExceeded
EventOverflow
ConcurrencyLimitExceeded
StaleEvent
StaleObservation
StaleReference
```

- `EmergencyStopRequested`: stop requestを受理したaudit/control diagnostic。停止完了を意味しない。
- `EmergencyStopIncomplete`: fencing/quiescence/remote statusを確認できず`Stopped`を証明できない。
- `CommitOutcomeIndeterminate`: stop/worker failureとCOMMITがraceし、authoritative outcomeをまだ確定できない。

## 6. Replay / diagnostics

```text
ReplayIncompatible
ReplayDivergence
ReplayInputRejected
```

- `ReplayInputRejected`: replay/log inputがingress limit、schema、trust isolation requirementを満たさない。

```text
ReplayIncompatible != ReplayDivergence
Replay != Rewind
```

## 7. Feasibility / assessment status

通常errorではない:

```text
Feasible
ConditionallyFeasible
Infeasible
Indeterminate
EquilibriumReached
EquilibriumLimited
```

assessment内部:

```text
Pass
Conditional
Fail
Unknown
NotApplicable
```

Overall rule:

- mandatory fatal contradiction/prohibition proven → `Infeasible`。
- explicit conditions required → `ConditionallyFeasible`。
- mandatory judgement evidence不足 → `Indeterminate`。
- mandatory assessments pass → `Feasible`。

## 8. PredictedDiagnostic

```text
PredictedDiagnostic {
    stage
    code
    severity
    cause
    evidence
}
```

severity:

```text
info
warning
conditional
fatal
unknown
```

例:

```text
NORMALIZE / AmbiguousNormalization / conditional
NORMALIZE / CrossLanguageDrift / fatal
RESOLVE   / IndexStale / conditional
PREPARE   / AuthorityError / fatal
PLANNING  / EnergyModelUnavailable / unknown
```

## 9. Causality / identity

```text
IdentityViolation
IdentityContinuityFailure
HistoryMutationDenied
TemporalAuthorityError
CausalityCycleError
```

## 10. Important boundaries

```text
AmbiguousCaseError != AmbiguousNormalization
AmbiguousNormalization != undefined behavior
Unexpected result != undefined behavior
CrossLanguageDrift != stylistic translation difference
AI confidence != semantic proof
IndexStale != StaleReference
EnergyModelUnavailable != InsufficientBudget
ResourceEstimateIncomplete != ResourceExhaustion
Predicted AuthorityError != thrown AuthorityError
EmergencyStopRequested != Stopped
Stopped != rolled back
Replay/log input != authoritative world state
```

### AmbiguousCaseError vs AmbiguousNormalization

- `AmbiguousCaseError`: Latin等のadapter-local morphology/case ambiguity diagnostic。
- `AmbiguousNormalization`: language-independent NSR candidate ambiguity。

### CrossLanguageDrift

自然な翻訳であってもexecution-relevant semantic contentが変化すれば発生する。

register/styleだけの変化でSemanticFingerprint対象外ならdriftにしない。

## 11. Fail policy

原則fail closed:

- type/dimension/payload不整合。
- registry/index schema compatibility不成立。
- authority/Lease不足。
- mandatory conservation/identity obligation不成立。
- required timing/integration safety contract不成立。
- permissive normalizationでもmandatory safety evidence不成立。
- required SandboxProfileがmissing/incompatible/enforce不能。
- mandatory stage budget超過により安全判断が未完了。
- emergency stop fenceまたはprior COMMIT outcomeを確認できない。
- replay/log dataだけを根拠にoriginal worldへmutationしようとする。

`LegacyPermissive` は曖昧なcandidate選択を許しうるが、安全検査自体を無効化しない。

### Ambiguity replay diagnostics

```text
AmbiguityDecisionUnreproducible != AmbiguityReplayDivergence
AmbiguityContextDrift != UnexpectedResult
```

- `AmbiguityDecisionUnreproducible`はrequired input/revision/evidenceが欠け、同じ決定を
  再計算できない状態。
- `AmbiguityReplayDivergence`は入力をcompatibleとして受理したにもかかわらず再計算結果が
  recorded selectionと異なる状態。
- `AmbiguityContextDrift`はcontextの変更を明示する診断であり、旧decisionが当時の
  contextで非決定的だったことを意味しない。
- `UnexpectedResult`は選択されたvalid semanticsと術者意図の不一致というoutcomeであり、
  replay engine failureではない。
