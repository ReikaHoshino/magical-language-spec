# Type Reference — v0.7.3

**Status:** normative type index; detailed semantics live in domain references.

## Purpose

現行仕様の主要型・type family・frontend/runtime/evaluation metadata型を横断参照する。

## Depends on

- `conventions.md`
- `language-adapters.md`
- `feasibility.md`
- `world-index.md`
- `runtime-time.md`
- `temporal-causality.md`
- `matter.md`
- `kinetics.md`
- `registry.md`
- `machine-values.md`

## 1. Entity / identity

```text
Entity
PhysicalEntity
Object
Organism
Artifact
Agent
Region
Anchor
SpellInstance
EntityID<T>
Ref<T>
HistoricalRef<T>
IdentityPolicy<T>
```

`HistoricalRef<T>` is a read-only historical view. It is not directly convertible to current `Ref<T>` and
does not grant current identity, liveness, Capability, Lease, or write authority. Detailed ownership lives in
[`temporal-causality.md`](temporal-causality.md).

## 2. Language adapter / normalization — v0.7.3

```text
LanguageAdapter<L>
LanguageAdapterID
SourceTextInput
SourceTextNormalizationResult
SourceTextTransformation
SourceMap
SourceSpan
SurfaceAnalysis<L>
LexemeEntry<L>
NormalizerProvider
NormalizationCandidate
NormalizationCandidateSet
NormalizationDecision
AmbiguityPolicy
NormalizedSemanticRepresentation
SemanticRole
SemanticFingerprint
SurfaceRenderer<L>
```

```text
AmbiguityPolicy =
    StrictReject
  | InteractiveResolve
  | ContextualDeterministic
  | LegacyPermissive
```

Project adapter IDs:

```text
lat
lzh
ger
jpn
eng
zho
```

Project adapter IDはexternal language tagと別identity。

## 3. Compiler / interpretation

```text
SurfaceInterpretation
NormalizedSemanticRepresentation  // NSR
CanonicalSemanticProjectionV1
SemanticFingerprintV1
SemanticAST
TypedMIR
NormalizedIR
InterpretationBundle
KernelPlan
```

```text
SurfaceInterpretation != NSR != SemanticAST != TypedMIR != KernelPlan
```

## 4. Selector / resolver

```text
Selector<T>
SymbolicSelector<T>
SpatialSelector<T>
RelationalSelector<T>
FilteredSelector<T>
Selection<T>
OrderSpec
QueryContext
ResolverQuery<T>
Candidate<T>
CandidateSet<T>
```

## 5. World Index

```text
WorldIndex
WorldIndexSnapshot
WorldIndexRevision
IndexSchemaRevision
WorldRevision
EntityIndexRecord<T>
IdentityIndex
SymbolicIndex
SpatialIndex
RelationIndex
VisibilityIndex
ConsistencyPolicy
QueryBudget
```

## 6. Authority / ownership

```text
Capability<Target,Domain,Operation>
Capability<History,Causality,Rewrite>
Lease<Target,Domain,Mode,Lifetime>
Borrow<Target,Domain,Mode,Lifetime>
```

`Capability<History,Causality,Rewrite>` is the canonical high-authority specialization for an explicitly
admitted committed-history mutation profile. It is unsupported/deferred by the current reference
implementation; its presence in the type index does not create an executor or stable conformance promise.

## 7. Quantity / transfer

```text
Quantity<Q,D>
Measurement<Q>
Channel<K : Transferable>
PayloadOf<K>
Transit<K,PayloadOf<K>>
TransferHandle<K>
TransferResult<K>
```

```text
PayloadOf<Energy>   = Quantity<Energy>
PayloadOf<Momentum> = Quantity<Momentum>
PayloadOf<Charge>   = Quantity<Charge>
PayloadOf<Matter>   = MatterPayload
```

## 8. SI dimension system

Base order:

```text
(kg,m,s,A,K,mol,cd)
```

```text
Mass              : kg
Length            : m
Time              : s
ElectricCurrent   : A
Temperature       : K
AmountOfSubstance : mol
LuminousIntensity : cd
Velocity          : m s^-1
Momentum          : kg m s^-1
Energy            : kg m^2 s^-2
Power             : kg m^2 s^-3
Charge            : A s
```

Portable JSONの`Identifier`、`RevisionToken`、`SIDimension`、`QuantityValue`、
`DurationValue`、`ScopedHashRecord`は `machine-values.md` /
`schemas/common-values.schema.json` を正本とする。

## 9. Traits

```text
Observable
Transferable
Conserved
ScalarPayload
CompositePayload
VectorQuantity
```

## 10. Matter / chemistry

```text
ElementID
NuclideID
SpeciesID
MaterialClassID
SpeciesAmount
Composition
CompositionEstimate
MatterPayload
ThermodynamicState<M>
StructureSchema
StructureDescriptor<S>
ReactionDomain
ReactionRule<R>
Stoichiometry
ReactionExtent
ChemicalReactionProfile
NuclearReactionProfile
```

## 11. Kinetics / pathway

```text
RateBasis
ReactionExtentRate
VolumetricReactionRate
SurfaceReactionRate
KineticContext
RateLaw<C>
RateEstimate<R>
RateConstantModel
RateConstantEstimate
KineticModel<R>
ReactionPathway<R>
ElementaryStep
ReactionNetwork
```

## 12. Catalysis / equilibrium

```text
CatalystModel
CatalystState
CatalystRequirement
InhibitorModel
ThermodynamicActivity<S>
ActivityModel
ReactionQuotient
EquilibriumConstant
EquilibriumModel<R>
EquilibriumAssessment
```

## 13. Feasibility / estimation

```text
EvaluationInput
EvaluationProfile
PreparedPlan
PreparedReactionPlan
FeasibilityReport
FeasibilityStatus
AssessmentStatus
Estimate<T>
InferenceRecord<T>
PlanningAssumption<T>
InferenceCriticality
PlanningAssumptionBinding
EstimatorProfile
EstimatorModel
EnergyEstimate
EnergyBreakdown
ResourceEstimate
ResolutionAssessment
AuthorityAssessment
TimingAssessment
PredictedDiagnostic
EvidenceRef
Assumption
```

```text
FeasibilityStatus =
    Feasible
  | ConditionallyFeasible
  | Infeasible
  | Indeterminate
```

```text
Estimate<T> =
    Exact
  | Range
  | LowerBound
  | UpperBound
  | Distribution
  | Unknown
```

```text
InferenceCriticality =
    MustResolve
  | EstimateAllowed
  | Optional

PlanningAssumptionBinding =
    PrepareBound
  | CommitBound
  | Dynamic
```

## 14. Measurement / spectral

```text
Measurement<Q>
Truth = True | False | Indeterminate
Spectrum<Q,Axis>
SpectralMeasurement<Q,Axis>
ObserverModel<In,Out>
```

## 15. Portable time / async

```text
Instant
EventID
Event<K>
EventRecord<K>
EventTimeRecord
TransferHandle<K>
TransferResult<K>
HistoricalMeasurement<Q>
ScheduledTask
ResumeRecord
```

```text
EventTimeRecord {
    effective_at
    committed_at
}

ResumeRecord {
    event_effective_at
    event_committed_at
    resumed_at
}
```

## 16. Runtime scheduler

```text
RuntimeEpochID
RuntimeTickID
SchedulerPhase
MicrostepOrdinal
TickStamp
TickInterval
SchedulingPolicy
TemporalTolerance
MicrostepBudget
ScheduledWork
ControllerTiming
```

## 17. Numerical integration

```text
IntegratorContract
IntegrationReport
```

## 18. Replay

```text
ReplayManifest
TickRecord
ReplayProfile
ReplayCompatibility
ReplayDivergenceReport
```

## 19. Registry

```text
SemanticRegistry
SemanticEntry<K>
SpeciesEntry
StructureSchemaEntry
ReactionRuleEntry
KineticModelEntry
ReactionPathwayEntry
CatalystModelEntry
InhibitorModelEntry
ActivityModelEntry
EquilibriumModelEntry
ConservationLedgerEntry
ConservationProfile<K>
RegistryHash
```

## 20. Core invariants

```text
Language-specific parse != NSR
AI proposal != semantic truth
Confidence != proof
Lexical meaning != Entity resolution
Cross-language conversion != direct translation
SemanticFingerprint != artifact content_hash
Reference != Identity != Authority != Ownership != State
WorldIndex != WorldState
CandidateSet != Ref set
Selector != Ref
Selection != LiveSet
Payload != Entity identity
Composition != CompositionEstimate
Reaction != TRANSFER
ReactionRule != ReactionPathway
Stoichiometry != RateLaw
Kinetics != Thermodynamics
Evaluation != Execution
Estimate != Reservation
Feasibility != Authority grant
Unknown != zero
Physical time != runtime tick
Event effective time != runtime commit time in general
Tick execution order != causal order
Integrator approximation != physical law
DeterministicReplay != Rewind
Restore != Rewind
Energy/resource magnitude != temporal/causal authority
Dimension equality != Semantic type equality
Transferable != Conserved
```

詳細は専用referenceを参照する。
