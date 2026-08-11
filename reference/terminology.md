# 術語索引 — v0.12.0

**Status:** informative index; formal definitions live in linked normative reference documents.

MIR/API識別子がある場合は英語表記を正とする。仕様の保証範囲とdefinition ownershipは[`scope-and-ownership.md`](scope-and-ownership.md)を参照する。

## A. 仕様・文書規約

| 術語 | 表記 | 定義 | 初出/改訂 |
|---|---|---|---|
| 規範語 | `MUST / MUST NOT / SHOULD / SHOULD NOT / MAY` | 適合性に影響する要求レベル。 | v0.6.3 |
| implementation-defined | `implementation-defined` | 実装が選択し文書化する挙動。 | v0.6.3 |
| registry-defined | `registry-defined` | trusted SemanticRegistryが定義する意味。 | v0.6.3 |
| world-defined | `world-defined` | authoritative world modelが定義する意味。 | v0.6.3 |
| profile-defined | `profile-defined` | explicit profileが所有するchoice。 | v0.6.3 |
| unspecified | `unspecified` | 仕様が複数の適合挙動を許す状態。 | v0.6.3 |
| undefined | `undefined` | 仕様が意味を与えない状態。危険world effectではfail closed。 | v0.6.3 |
| DefinitionSource | enum | 値/policyの定義責任をSpecification / Implementation / Registry / World / Profileへ分離する。 | v0.6.3 |
| normative rule owner | document/heading | conformance caseが参照するcurrent normative definition location。manifest自身は第二仕様源にならない。 | v0.10.0 |

## A.1 日本語project用語と仕様ownership

この表は索引でありworldbuilding上の完全な定義ではない。formal ownership contractは[`scope-and-ownership.md`](scope-and-ownership.md#2-project-terms-and-ownership)に置く。

| 術語 | 仕様上の索引 | DefinitionSource / owner |
|---|---|---|
| 魔法 | typed/authorized world-effect computationのinformative総称。組込みtype/primitive/resourceではない。 | 個別language/runtime reference。世界観上の定義は本仕様外。 |
| 術式 | parse/normalize/compile/evaluate対象のprogram unit。MIR `spell` declaration、source、CompiledSpell、SpellInstanceは相互に非同値。 | Grammar / MIR / runtime specification。 |
| 詠唱 | spoken/natural-language surface inputのinformativeな入力形態。semantic authorityではない。 | adapter/profile-defined surface behavior。 |
| 魔法陣 | graphical/external representationを指しうるが、current coreには組込み構文・型・primitiveなし。 | representation adapter/toolingまたはWorld。 |
| 魔力 | current coreでは`Energy`、Capability、authority、reservationの同義語でも組込みquantityでもない。 | 採用するWorld / Registry / Profile。 |
| 魔子 | current coreは存在・物理性質・保存則・SpeciesIDを仮定しない。 | 採用するWorld / Registry / Profile。 |

```text
魔力 != Energy != Capability
魔子 != built-in SpeciesID
詠唱 != semantic authority
魔法陣 != executable permission
```

## B. Representation / compiler / evaluator

| 術語 | 表記 / 型 | 定義 | 初出/改訂 |
|---|---|---|---|
| NaturalLanguageSource | source | adapter前のUTF-8 natural-language input。 | v0.7.2/v0.8.0 |
| SurfaceAnalysis | `SurfaceAnalysis<L>` | token/morphology/syntax等のlanguage-specific analysis。 | v0.7.2 |
| NSR | `NormalizedSemanticRepresentation` | natural languageより抽象的でSemanticASTより人間可読なlanguage-independent semantic representation。 | v0.7.2 |
| SemanticAST | `SemanticAST` | language-independent semantic structure AST。 | v0.7.1/v0.7.2 |
| MIR | Magical Intermediate Representation | 型・次元・effect等を持つ中間表現。 | v0.1 |
| TypedMIR | `TypedMIR` | type/dimension/effect/registry contractが付いたMIR。 | v0.2/v0.7.1 |
| NormalizedIR | `NormalizedIR` | compiler/evaluator内部の正規化IR。 | v0.7.1 |
| KernelPlan | `KernelPlan` | admitted plan candidateのMKI-level operation plan。 | v0.7.1 |
| FeasibilityReport | report | world mutationなしでfeasibility/evidence/estimate/diagnosticを返すmachine-readable report。 | v0.7.1/v0.8.0 |
| PreparedPlan | `PreparedPlan` | PREPAREでcurrent world/profile/evidenceへ束縛されたreversible execution candidate。COMMIT許可そのものではない。 | v0.9.0 |
| PlanningAssumption | planning artifact | source Unknownと別に、明示policy/evidence/model/bindingを持ってplanningで採用する値。 | v0.8.0 |
| Estimate | estimate | Exact / Range / Bound / Distribution / Unknownを持つmodel output。authorityやreservationではない。 | v0.7.1/v0.8.0 |

```text
Language-specific parse != NSR
NSR != SemanticAST
SemanticAST != TypedMIR
TypedMIR != KernelPlan
Evaluation != Execution
Estimate != Reservation
```

## C. v0.10+ Conformance

formal contractは[`conformance.md`](conformance.md)、machine-readable class/case mappingは`conformance/manifest.json`、逆向きrule coverage inventoryは`conformance/rule-coverage.json`に置く。

| 術語 | 表記 / 型 | 定義 | 初出 |
|---|---|---|---|
| ConformanceManifest | `ConformanceManifest` | suite/class/stable case ID/rule owner/test-fixture locatorをversionedに結ぶmanifest。 | v0.10.0 |
| conformance class | class ID | 実装がclaimできるstable surface単位。初期classはCore/Evaluator/Adapter-lat/Runtime。 | v0.10.0 |
| Core-1.0 | class | core representation/ownership/MKI/planning/fingerprint/compatibility/resolution-domain candidate surface。 | v0.10.0 |
| Evaluator-1.0 | class | v0.8 evaluator ingress/type/dimension/resolution/obligation/reporting candidate surface。 | v0.10.0 |
| Adapter-lat-1.0 | class | supported Latin source normalization/ambiguity/NSR path candidate surface。 | v0.10.0 |
| Runtime-1.0 | class | PREPARE/COMMIT/MKI/scheduler/replay plus World Kernel active-effect boundary candidate surface。 | v0.10.0 |
| stable case ID | case ID | test method名とは独立したsemantic obligation identity。既存`WB-TEST-*`も意味が同じなら再利用する。 | v0.10.0 |
| candidate class | status | required case setをrelease candidate surfaceとして定義できるclass。 | v0.10.0 |
| blocked class | status | semantic/release dependency未解決のためconformance claim不可なclass。 | v0.10.0 |
| provisional measurement | execution mode | blocked/provisional baselineを測るだけでclass statusを昇格しない実行。 | v0.10.0 |
| rule coverage inventory | artifact | required caseのreverse mappingとexplicit deferred/non-executable ruleを列挙するconformance-owned crosswalk。 | v0.10.0 |
| V1RequiredSurfaceMatrix | conformance artifact | pre-public archive Issue #38の14 required conformance claimをowning classとstable required case IDへ完全mappingする。repository testの存在だけをcoverage claimにしない。 | v0.12.0 |
| CompatibilityAdmission | aggregate gate | domain-owned CompatibilityDecisionを集約しAllowed/Denied/Indeterminateを返す。compatibility自体を再計算せずauthorityも付与しない。 | v0.10.0 |
| Experimental-Arcana-0 | experimental class | SUCCESS-ARCANA-001〜008のoptional success/guard/replay/recognized-unsupported surface。4 required classと65 stable caseには含まれない。formal ownerは`success-arcana.md`。 | Unreleased experimental |
| SpellInstanceBundle | experimental artifact | self-contained NSR、versioned semantic/runtime contracts、profiles、WorldIndex/WorldState evidence、expectationを持つsingle-file ingress。filename/suite/instance IDはdispatch authorityではない。formal ownerは`spell-instance-bundles.md`。 | Unreleased experimental |

```text
repository test != conformance case merely by existing
stable case ID != test method name
implementation output != conformance truth
blocked baseline all green != class conformance
CompatibilityAdmission != Capability
CompatibilityAdmission != Lease
```

## D. World model / World Kernel / runtime

| 術語 | 表記 / 型 | 定義 | 初出/改訂 |
|---|---|---|---|
| 世界状態 | `Σ` | authoritative current WorldState。 | v0.1 |
| 世界履歴 | `H=(E,≺)` | committed Event集合と因果関係。 | v0.5 |
| runtime state | `Ω` | scheduler/runtime realization、queues、handles、cache等。causal active-effect semanticsのsole ownerではない。 | v0.5.2/v0.10.0 |
| process state | `P` | admitted/active processとreservation等のprocess-local state。 | v0.5.2/v0.9.0 |
| 実行構成 | `C=<Σ,H,Ω,P>` | runtime evaluation configuration。 | v0.5.2/v0.9.0 |
| MKI | Magical Kernel Interface | portable public semantic ABI。data planeはexactly six operations。 | v0.1/v0.10.0 |
| World Kernel | semantic boundary | validated/revalidated semantic effect requestとauthoritative world evolutionの間のprivileged execution boundary。 | v0.10.0 |
| Kernel interaction class | `QUERY/SAMPLE/TRANSITION/ACTIVATE/DEACTIVATE` | lower World Kernel semantic category。MKI primitive、source syntax、solver stepではない。 | v0.10.0 |
| QUERY | interaction class | authoritative semantic lookup/identity-resolution style interaction。 | v0.10.0 |
| SAMPLE | interaction class | admitted observation/sample interaction。 | v0.10.0 |
| TRANSITION | interaction class | bounded discrete authoritative state transition。 | v0.10.0 |
| ACTIVATE | interaction class | persistent/extended effect contractをauthoritative semanticsへactivateするinteraction。 | v0.10.0 |
| DEACTIVATE | interaction class | admitted persistent effectをsettle/terminateするinteraction。rollbackではない。 | v0.10.0 |
| active-effect semantic projection | world semantics | future authoritative evolutionをcausally決めるTransit/Channel/Controller/Dynamics等のportable semantic state。 | v0.10.0 |
| KernelAtomicGroup | semantic commit group | invariant-sensitive loweringsをall-or-noneでcommitするsemantic group。 | v0.10.0 |
| Transit | active effect | non-zero TRANSFERのin-flight matter/resource/accounting semanticsを保持するauthoritative projection。 | v0.10.0 |
| DynamicsProcess | active effect | continuous RECONFIGURE等のadmitted model semantics。integrator substepそのものではない。 | v0.10.0 |
| Controller | active effect | bounded CONSTRAIN contract。future actuationはscope/Capability/Lease/resource/timing/current-stateを再検証する。 | v0.9.0/v0.10.0 |
| BoundaryReflectionController | controller model | Region crossingへbounded impulseを適用し、target/anchor reaction・dissipation・Eventをatomicにaccountするexperimental controller contract。formal ownerは`success-arcana.md`。 | Unreleased experimental |
| PREPARE | control boundary | reversible binding/reservation phase。authoritative world mutationではない。 | v0.5/v0.9.0 |
| control-plane COMMIT | control boundary | admitted initial KernelAtomicGroupをcurrent evidence下でcommitする。future persistent consequencesを全て完了させる意味ではない。 | v0.5/v0.10.0 |
| scheduler Commit | runtime phase | due effect/consequenceをcurrent-state revalidation後にcommitするlogical scheduler phase。 | v0.7/v0.10.0 |
| emergency stop | safety state | new work/actuationをfence/settle/terminateする安全境界。過去のcommitted effectをrollbackしない。 | v0.8.0/v0.10.0 |
| SandboxProfile | profile | Energy/event/microstep/concurrency/external-interaction等を制限するprofile。Capabilityを生成しない。 | v0.9.0 |
| deterministic replay | replay | compatible profile下でexecution evidenceを再構成・比較する。Rewindではない。 | v0.7/v0.9.0 |

```text
MKI data-plane primitives = 6
Kernel interaction class != MKI primitive
runtime bookkeeping != semantic active-effect ownership
control-plane COMMIT != all future consequences already occurred
DEACTIVATE != rollback
Physical time != runtime tick
Integrator approximation != physical law
DeterministicReplay != Rewind
```

## E. Language Adapter / NSR

| 術語 | 表記 / 型 | 定義 | 初出/改訂 |
|---|---|---|---|
| LanguageAdapter | `LanguageAdapter<L>` | particular natural language surfaceをcommon normalization layerへ接続するadapter。 | v0.7.2 |
| project adapter ID | `lat/lzh/ger/jpn/eng/zho` | project stable adapter identity。external language tagとは別。 | v0.7.2 |
| SourceTextNormalizerV1 | operation | strict UTF-8/scalar validation、line endings、NFC、recoverable mappingを行うcommon ingress。 | v0.8.0 |
| SourceMap | mapping | normalized source spanとoriginal decoded source spanの対応。 | v0.8.0 |
| LexemeEntry | lexical entry | morphology/frame/semantic proposal等を持つadapter辞書entry。 | v0.7.2 |
| DomainLexicon | lexicon | domain-specific technical/magical lexicon。 | v0.7.2 |
| NormalizationCandidateSet | candidate set | 複数semantic normalization candidate集合。 | v0.7.2 |
| AmbiguityPolicy | policy | StrictReject / InteractiveResolve / ContextualDeterministic / LegacyPermissive。 | v0.7.2 |
| AmbiguityDecisionTraceV1 | trace | policy/context/ranking/replay evidenceを保持するversioned decision trace。 | v0.8.0 |
| CanonicalSemanticProjectionV1 | operation | NSR execution-relevant semanticsのV1 canonical projection。full NSR serializationではない。 | v0.7.3 |
| SemanticFingerprintV1 | fingerprint | `sf:v1:sha256:<digest>` representationを持つJCS+SHA-256 semantic digest。 | v0.7.3 |
| SurfaceRenderer | `SurfaceRenderer<L>` | NSRからtarget surfaceを生成するrenderer contract。 | v0.7.2 |
| AI proposal | proposal | untrusted normalization candidate。semantic truthではない。 | v0.7.2 |

adapter priority:

```text
lat → lzh → ger → jpn → eng → zho
```

v0.12.0でもsource→NSR conformanceを持つreference implementationは`lat`だけであり、canonical water-ball English surfaceは`eng` adapter conformance claimではない。

## F. Resolution / identity / authority

| 術語 | 表記 / 型 | 定義 | 初出/改訂 |
|---|---|---|---|
| WorldIndex | search view | RESOLVE/Selection用versioned search/read model。WorldStateではない。 | v0.6.4 |
| WorldIndexRevision | revision | index snapshot/revision identity。WorldRevisionとは別domain。 | v0.6.4 |
| EntityIndexRecord | record | search metadata。Entity本体ではない。 | v0.6.4 |
| ResolverQuery | `ResolverQuery<T>` | Selector由来query contract。 | v0.6.4 |
| CandidateSet | `CandidateSet<T>` | authoritative revalidation前のcandidate集合。 | v0.6.4 |
| Entity | `Entity` | persistent managed identityを持つ対象。 | v0.1 |
| EntityID | `EntityID<T>` | authoritative identity token。 | v0.4 |
| Ref | `Ref<T>` | Entityへのreference。authorityではない。 | v0.1/v0.4 |
| Selector | `Selector<T>` | RESOLVE前のsearch description。 | v0.5.2 |
| Selection | `Selection<T>` | bounded immutable Ref snapshot。 | v0.6 |
| Capability | authority evidence | operation eligibility/authority。 | v0.4 |
| bounded dynamic Capability target scope | authority scope | anchor/Region、predicate、maximum scope、effect class、validityを固定し、各actuationで再検証するscope。predicateやRelationからauthorityを増幅しない。formal ownerは`success-arcana.md`。 | Unreleased experimental |
| Lease | authority/reservation contract | scoped time-bound operation occupancy/permission contract。 | v0.4 |
| Borrow | access contract | limited scoped access。 | v0.4 |
| CompatibilityDecision | decision envelope | domain-owned profile/evidence/result `Compatible/Incompatible/Undetermined`。 | v0.8.0 |
| CompatibilityEvolutionPolicy | release-policy artifact | v1.x stable scope、deprecation、exact migration evidenceを列挙するcandidate policy。domain compatibility algorithmではない。 | v0.11.0 |
| MigrationEntry | migration evidence | owner、exact source/target contract/profile、named transformation、mandatory postconditionsを持つrelation。 | v0.11.0 |
| deprecation record | lifecycle evidence | affected stable contract、owner、deprecated release、earliest removal major、replacement/rationaleを持つ。 | v0.11.0 |
| CompatibilityCoverageInventory | conformance artifact | required reference-path artifactをdomain-owned compatibility profileへversioned mappingする。algorithmやresultを再計算しない。 | v0.11.0 |

```text
WorldIndex != WorldState
IndexRecord != Entity
Selector != Ref
Visibility != Authority
Registry metadata != Capability
Compatibility != authorized
```

## G. Quantity / matter / reaction / estimator

| 術語 | 表記 / 型 | 定義 | 初出/改訂 |
|---|---|---|---|
| 意味型 | `Q` | SI dimensionとは別のsemantic classification。 | v0.1 |
| Quantity | `Quantity<Q,D>` | semantic type + SI dimension。 | v0.1 |
| Energy | `kg m^2 s^-2` | Energy semantic quantity。world/profile modelが具体costを定義する。 | v0.1 |
| Momentum | `kg m s^-1` | momentum quantity。 | v0.1 |
| transfer kind | `K` | CHANNEL/TRANSFER transport category。 | v0.6 |
| PayloadOf | `PayloadOf<K>` | transfer kindに対応するpayload type。 | v0.6 |
| Composition | composition | Species amount mapping。 | v0.6.1 |
| ConservationLedger | ledger | admitted conservation/accounting contract。 | v0.5.2/v0.6.1 |
| ReactionRule | rule | stoichiometric/reaction transformation rule。rate/pathwayとは別。 | v0.6.1 |
| ReactionPathway | pathway | multiple reaction steps/path alternatives。ReactionRuleとは別。 | v0.6.2 |
| KineticModel | model | rate/dynamics model。thermodynamic admissibilityとは別。 | v0.6.2 |
| EstimatorProfile | profile | Energy/resource/timing estimate model availability/coefficient/ownershipを定義する。 | v0.8.0 |
| TreatmentDecomposition | treatment artifact | measurable injury stateをtransferable Energy/Matter、reversible structure、irreversible information loss、uncertaintyへ分離するexperimental contract。formal ownerは`success-arcana.md`。 | Unreleased experimental |

```text
Dimension equality != Semantic type equality
PayloadOf<K> != Quantity<K> in general
ReactionRule != ReactionPathway
Stoichiometry != RateLaw
Kinetics != Thermodynamics
Unknown != zero
```

## H. Machine-readable artifacts / packaging

| 術語 | 表記 / 型 | 定義 | 初出/改訂 |
|---|---|---|---|
| CommonMachineValue | serialization contract | identifier/revision/SI quantity/duration/scoped hashのportable JSON boundary。 | v0.8.0 |
| scoped hash record | record | hash scopeと`unresolved`/`digest`を分離し、digest時にprofile/algorithm/valueを要求する。 | v0.8.0 |
| runtime execution trace | `SandboxExecutionTrace` | committed/aborted runtime execution evidenceのmachine-readable artifact。 | v0.9.0 |
| FrozenEvidenceContext | evidence context | World/History/evidence revision、interval、source、freshness、authority、budget、orderingを固定するsnapshot-consistent experimental context。formal ownerは`evidence-inference.md`。 | Unreleased experimental |
| EvidenceFusionModel | registry model | acquired Measurementからhypothesisを決定的に評価するpure evidence model。PlanningAssumption、Identity proof、authority grantではない。formal ownerは`evidence-inference.md`。 | Unreleased experimental |
| ObservationArtifact | non-physical artifact | evidence context、bundle、model revision、ranking/uncertaintyを持つprovenance-bearing result。生成だけではWorldState mutationではない。formal ownerは`evidence-inference.md`。 | Unreleased experimental |
| editable-install reference path | packaging contract | clean checkout上のcanonical resourcesを使い、installed entry pointをrepository外cwdから実行するv0.10 tested path。 | v0.10.0 |
| standalone resource portability | packaging contract | wheel/sdist単体でcanonical resourcesを解決する能力。pre-public archive Issue #60 / pre-public archive PR #62でsingle-authoring-source projectionとisolated smokeを追加。 | v0.11.0 |

```text
SemanticFingerprint != artifact content_hash
hash equality != compatibility
schema-valid != Compatible
clean editable install != standalone wheel portability proof
```
