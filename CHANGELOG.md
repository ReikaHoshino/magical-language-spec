# Changelog

## Unreleased — current v1 execution-admission blocker

- public Issue #23 defines mandatory `LocalAdmission` separately from explicit `WholePlanPreflight`.
- `WholePlanPreflight` is snapshot/model/profile-scoped assessment, not reservation, Capability/Lease grant, or runtime completion guarantee.
- paired water-transfer fixtures distinguish first-effect preflight rejection from incremental partial commit plus later continuation failure; prior commits remain authoritative and constraint termination is not rollback.
- stable diagnostics, schema, traceability, fail-closed reference behavior, deterministic replay, and current-reference synchronization are added without a seventh MKI primitive or public serialized ECIR.
- WB-CANON-001, the stable 4 class / 65 case / 14 claim RC surface, package identity, and immutable historical snapshots remain unchanged pending renewed exact-main release audit and new RC decision.

## Unreleased experimental

- pre-public archive Issue #91 / pre-public archive PR #129: public `SpellInstanceBundle` executionをcomplete current `MagicalProgram-0` pathへcutoverし、専用executorをlegacy oracleへ隔離。
- pre-public archive Issue #92 / pre-public archive PR #131: bounded human-authored `MGLS-0` source contract、closed EBNF、lowering/source-map/diagnostic ownership、2 positive / 15 negative examplesを追加。
- pre-public archive Issue #93 / pre-public archive PR #133: strict deterministic MGLS parser/typechecker/compiler、independent target admission、semantic/source-map verification、editable/wheel/sdist compiler smokeを追加。
- pre-public archive Issue #94 / pre-public archive PR #135: compatibility-safe experimental `magical-language check/eval/run/compile`、single-read decoded-kind routing、common JSON envelope、fixed exit codes、atomic output guards、source/program/bundle/replay parityを追加。
- `conformance/experimental-user-workflow.json`へ11 experimental E2E casesを追加し、stable `conformance/manifest.json`の4 classes / 65 required casesから分離。
- pre-public archive Issue #80 / pre-public archive draft PR #78: strict self-contained `SpellInstanceBundle` ingress、versioned artifact/semantic/runtime registries、deterministic `check/eval/run` CLIを追加。
- SUCCESS-ARCANA-001..008、DEBUG-HELL-001..003、non-suite GENERIC-001を同じfail-closed pathへ統合。SA-005..008はrecognized-unsupportedのまま。
- これらはpackage `1.0.0rc1`に同梱されるが、stable 4 classes / 65 cases / WB-CANON-001へ昇格しない。

## v1.0.0-rc.1 — Release Candidate 1

- public Issue #1のrenewed exact-main no-waiver auditをGOとして完了し、public Issue #2の明示承認後に専用release gateを再実行。
- Core-1.0 / Evaluator-1.0 / Adapter-lat-1.0 / Runtime-1.0を4 classes / 65 required cases / 14 required claimsのまま`released` RC surfaceとして凍結。
- conformance manifest、rule coverage、compatibility coverage、v1 required-surface matrixを`1.0.0-rc.1` / `v1.0.0-rc.1`へ同期。
- Python distribution identityはPEP 440 `1.0.0rc1`、spec/conformance identityは`1.0.0-rc.1`として明示分離。
- public Issue #15でtracker namespaceを明示し、public Issue #16でHistoricalRef / Restore / Rewind / Replayのauthority境界をcurrent normative ownerへreconcile。
- clean public history、public security policy、Dependabot、full-SHA-pinned GitHub Actions、exact-head branch protectionをrelease evidenceへ含める。
- README、reference、schemas、examples、tests、TODO、PROJECT_HANDOFF、consistency report、immutable `spec/v1.0.0-rc.1.md`を同期。
- `SemanticFingerprint != artifact content_hash`、release version != compatibility oracle、experimental evidence != stable conformanceを維持。

このログは設計会話とrepository releaseを v0.1〜v1.0.0-rc.1 に再整理したものです。

## v0.12.0 — Conformance Guarantee

- pre-public archive Issue #70のfive-gate no-waiver auditを受け、Gate 4の不足をpre-public archive Issue #71、Gate 5のfinal rehearsalをpre-public archive Issue #72へ分離。
- `conformance/v1-required-surface.json`でpre-public archive Issue #38の14 required conformance claimを4 classとstable case IDへmachine-readable mapping。
- common source normalization、ContextualDeterministic / LegacyPermissive ambiguity trace、planning binding/generation/minimum-Energy selectionをrequired caseへ昇格。
- specification-owned `WB-TEST-001..011`をcomplete canonical water-ball conformance corpusとして昇格。
- canonical evaluator path、six-operation runtime execution、resource ceiling、PrepareBound vs Dynamic runtime behaviorをrequired caseへ昇格。
- manifest / reverse rule coverage / requirement matrixの整合をregressionで強制し、required caseをbroad repository test passingだけで代用しない。
- package、schema、current reference、README、TODO、consistency report、immutable `spec/v0.12.0.md`を同期。
- Gate 4へcomplete candidate evidenceを提供するが、pre-public archive Issue #72のfinal pre-RC Release Guarantee rehearsal前にpre-public archive Issue #38をREADYへ進めない。
- Post-release pre-public archive Issue #72でexact pre-public archive PR #74 merge mainを再検証し、22 schemas / 243 tests / 65 cases / editable-wheel-sdist / no-waiver blocker auditをPASS。Gate 1–5 certificationを完了し、v1.0 RC entryをREADYとする。

## v0.11.0 — Compatibility Guarantee

- pre-public archive Issue #64でv1.x stable scope、patch/minor/major change class、deprecation lifecycle、exact migration contractをcurrent referenceとして追加。
- release versionをdomain compatibility oracleにせず、revision/hash/SemanticFingerprintからmigration pathを推測しない境界を維持。
- `CompatibilityEvolutionPolicy` schema、candidate fixture、exact migration selection/execution helper、positive/negative regressionを追加。
- migrated outputにtarget schema validationとdomain-owned compatibility re-evaluationを要求し、migrationからCapability/Lease/authority/trust/semantic proofを生成しない。
- v0.10.0 conformance manifest/snapshotはhistoricalに凍結し、promotionは新しいv0.11 suiteとして行う。
- pre-public archive Issue #66でpre-public archive Issue #64のrelease evolution / deprecation / exact migration rulesをCore-1.0 required stable casesへ昇格。
- `conformance/compatibility-coverage.json`でrequired v1 reference-path artifactsを7 domain-owned profileへ明示mapping。
- conformance manifest / reverse rule coverage / package / current reference / immutable `spec/v0.11.0.md`を同期。
- pre-public archive Issue #40のCompatibility Guarantee gateをversioned evidence付きPASSへ進めるが、他gateの最終監査前にpre-public archive Issue #38をREADYにはしない。

## v0.10.0 — Conformance Foundation

- pre-public archive Issue #55 / pre-public archive PR #57でMKI → lower semantic execution → World Kernel境界を確定。portable public MKI ABIは6 operationのまま維持し、lower execution classを`QUERY / SAMPLE / TRANSITION / ACTIVATE / DEACTIVATE`として仕様所有する。
- v1.0でpublic serialized ECIRを固定しない。lower interaction classを新MKI primitive、source syntax、numerical microstep、physical primitiveとして扱わない。
- causally relevantなTransit / active Channel / Controller / Dynamics semanticsにauthoritative WorldState/world-evolution projectionを要求し、runtime `Ω`をsole opaque semantic ownerにしない。
- control-plane COMMITをadmitted initial semantic groupのatomic commitとして整理し、persistent effectのfuture consequencesを全てactivation時に完了させる意味から分離。
- `KernelAtomicGroup` all-or-none semantics、non-zero TRANSFERのTransit accounting/lifecycle、continuous RECONFIGUREのmodel/integrator separation、bounded CONSTRAIN future-actuation revalidation、DEACTIVATE != rollbackを追加。
- pre-public archive Issue #58で`ConformanceManifest`とdeterministic conformance runnerを追加。stable case IDをtest method名から分離し、exact normative document/heading、fixture、test locatorをversionedに管理。
- initial candidate conformance classとして`Core-1.0 / Evaluator-1.0 / Adapter-lat-1.0 / Runtime-1.0`を定義。
- 既存canonical ID `WB-TEST-006` / `WB-TEST-008`を意味変更なしで再利用し、type、dimension、resolution/identity、authority、Lease、conservation、Unknown/inference、compatibility、serialization、PREPARE/COMMIT、runtime、replay、World Kernel semanticsへstable coverageを拡張。
- `conformance/rule-coverage.json`を追加し、required caseの逆向きrule coverageとexplicit deferred/non-executable ruleをmachine-readableに管理。暗黙coverageを禁止。
- aggregate compatibility admission `src.compatibility.admit_compatibility_decisions`を追加。domain-owned `CompatibilityDecision`を再計算せず、required `Incompatible`はDenied、missing/UndeterminedはIndeterminate/fail-closedとし、Capability/Lease/trustを生成しない。
- `pyproject.toml`とinstalled console entry points `magical-language-conformance` / `magical-language-evaluator`を追加。
- dedicated `Conformance package smoke` GitHub Actions workflowを追加し、editable install後にrepository外cwdからCore conformanceとLatin evaluatorを実行。
- clean checkout + declared dependencies / editable-install pathをv0.10 tested packaging boundaryとする。standalone wheel/sdistのcanonical resource portabilityはpre-public archive Issue #60へcarry-overし、未検証のwheel portabilityをclaimしない。
- `reference/conformance.md`、`reference/kernel-execution.md`、README、terminology、schemas、conformance artifacts、tests、release snapshot、consistency reportをv0.10 release stateへ同期。
- v0.10 landingだけではpre-public archive Issue #40の5 readiness gate完了やv1.0 RC eligibilityを意味しない。

## v0.9.0 — Sandboxed Runtime

- pre-public archive Issue #37でreleased v0.8 evaluator outputを唯一のfrontend/planning pathとして再利用する`src/runtime/` reference implementationを追加。第二compiler pathは作らない。
- deterministic in-memory sandbox configurationを`C=<Σ,H,Ω,P>`として実装し、WorldState、History、runtime state、process stateを分離。
- v0.8 `FeasibilityReport` / TypedMIR / KernelPlan / PlanningAssumptionからreversible `PreparedPlan`を構成。
- PREPAREではauthoritative Σ/Hを変更せず、Energy reservation intent、source/world/index/profile/evidence bindingを保持。
- COMMIT直前にworld/state revision、RuntimeProfile、Capability、Lease、conservation/accounting、emergency-stop fenceを再検証。
- supported subsetのCOMMITをatomicに扱い、mutation中のfailureではpre-COMMIT sandbox configurationを復元。
- MKI data-plane 6 primitive `RESOLVE / OBSERVE / CHANNEL / TRANSFER / RECONFIGURE / CONSTRAIN`をcanonical runtime pathで実行し、第7 primitiveを追加しない。
- control-plane reference subsetとして`ACQUIRE / COMMIT / RELEASE / ABORT`を実装。REVOKE / DELEGATEはnormative operationのままv0.9 implementationから明示defer。
- SandboxProfileとしてEnergy / event / microstep / concurrency / external-interaction ceilingを追加。Sandbox allowanceをCapabilityとして扱わない。
- canonical scheduler phase order `Ingress → ContinuousAdvance → Revalidate → Commit → PublishSnapshot → Control → IndexUpdate → Dispatch`をdeterministic trace化。
- `SyntheticReferenceIntegrator`を追加。canonical zero-duration intervalは`NoAdvanceRequired`、unknown non-zero continuous processは`IntegratorModelUnavailable`でfail closed。
- runtime execution resultを`SandboxExecutionTrace`としてversion化し、`schemas/runtime-execution.schema.json`でCommitted/Aborted traceを検証。
- replayはclone sandboxへ再実行し、profile compatibilityとresult-state hashを検査。ReplayをRewindとして扱わない。
- canonical WB-CANON-001を`world:991 → world:992`、`event:wb-canon-001`まで実行。50 kg water-ballをaccounted 100 kg water inventoryから生成し、ledger totalを100 kgに維持。
- stale revision / Capability / Lease / conservation / profile drift / stop fence / sandbox budgets / replay divergence / integrator unavailable等のnegative regressionを追加。
- `reference/runtime-implementation.md`、`spec/v0.9.0.md`、`examples/sandbox-runtime/`、README、terminology、consistency reportを同期。
- real hardware/world control、distributed runtime、production persistence、REVOKE/DELEGATE implementation等を明示defer。後続conformance/stabilizationはpre-public archive Issue #40が所有する。

## v0.8.0 — Minimal Local Evaluator

- pre-public archive Issue #8でSemanticRegistry namespaceのdomain-level JSON Schema、fixtures、negative validationを追加。
- pre-public archive Issue #9でRuntimeProfile scheduler / integrator / replay / temporal-toleranceのdomain contractとvariant fixturesを追加。
- pre-public archive Issue #10でMIR scope / name resolutionのnormative reference、EBNF semantic crosswalk、diagnostics、examplesを追加。
- pre-public archive Issue #11でsandbox profile、malicious-input threat model、emergency-stop / forced-termination contract、security diagnosticsとexamplesを追加。
- pre-public archive Issue #12でstrict UTF-8/scalar validation、NFC、line-ending normalization、recoverable source mappingを追加。
- pre-public archive Issue #13でcommon identifier/revision/SI quantity/duration/scoped hash recordを追加し、generic artifact digest algorithmを明示defer。
- pre-public archive Issue #14でdomain-owned compatibility decision envelopeを統合し、hash equalityを互換性判定にしない境界を追加。
- pre-public archive Issue #15でreference `lat` parser/normalizer、shared semantic roles、morphology/frame evidenceとambiguity処理を追加。
- pre-public archive Issue #16でnormative scope、DefinitionSource inventory、terminology ownershipを整理。
- pre-public archive Issue #20でdeterministic ambiguity ranking、LegacyPermissive selection、context-drift/replay trace contractを追加。
- pre-public archive Issue #34でUnknown / Estimate / PlanningAssumption、criticality/binding、generation lowering、terminal inference、planner/runtime safety境界を追加。
- pre-public archive Issue #17でEnergy/resource/timing estimator model/profile ownership、deterministic synthetic profile、positive/negative testsを追加。
- pre-public archive Issue #18でcanonical water-ball end-to-end pipeline、failure catalog、stable rule↔test/fixture traceabilityを追加。
- pre-public archive Issue #19でpre-v0.8 repo-wide integration auditを実施し、v0.8 implementation gateを解放。
- pre-public archive Issue #36で`src/evaluator/` reference implementationを追加。public ingressをexplicit `LanguageAdapter<lat>` sourceとschema-valid NSR JSON/objectに限定。
- NSR validation → SemanticAST → TypedMIR → type/dimension validation → read-only resolver/registry evidence → KernelPlan → assessments → FeasibilityReportをdeterministic local pipelineとして実装。
- `SemanticFingerprintV1`をpublic evaluator boundaryで検証し、artifact hashとは分離したまま維持。
- read-only SemanticRegistry / WorldIndex fixture adaptersを実装し、index candidateをRef、visibilityをAuthority、registry metadataをCapabilityへ昇格しない。
- canonical omitted terminalをsource Unknownのまま保持し、50 m horizonを別のprovenance-bearing `PlanningAssumption`として`PrepareBound`で採用。
- source fidelity → mandatory obligations → feasibility → minimum exact Energyの順でcanonical plan selectionを実装。
- pre-public archive Issue #17 synthetic profileからEnergy/resource/timingを評価し、canonical total 200 Jを再構成。estimator unavailableは0ではなく`Indeterminate`。
- authority / Lease / conservationをestimator outputと独立に評価し、mandatory failureを`Infeasible`とする。
- horizontal trajectoryを`CONSTRAIN` + control Energyとして扱い、gravityをworld modelから削除しない。
- deterministic human/JSON formatterとCLI `python -m src.evaluator`を追加。natural-language pathは`--source ... --lang lat`でexplicit dispatchする。
- canonical WB-CANON-001は未実装`eng` adapterを捏造せず、selected structured NSRからevaluatorへ入る。
- v0.8 evaluatorはCOMMIT execution / authoritative WorldState mutationを実装しない。sandbox runtimeはpre-public archive Issue #37 / v0.9へhandoff。

## v0.7.3 — Canonical Semantic Projection・SemanticFingerprint V1

- `CanonicalSemanticProjectionV1(NSR)` をversioned logical operationとして定義。
- `SemanticFingerprintV1(NSR) = SHA-256(UTF-8(JCS(projection)))` を定義。
- machine-readable representationを `sf:v1:sha256:<64 lowercase hex>` とした。
- projection top-level semantic fieldsをkind/action/roles/modifiers/conditions/constraintsに限定。
- schema_version/provenance/ambiguity/semantic_fingerprint/top-level unknowns summaryを除外。
- semantic valueのkind/semantic_kind/mode/selector/value/unit/reasonをprojection対象とし、evidenceを除外。
- omitted / explicit null / semantic Unknownを相互に非同値として固定。
- rolesをorder-independent multisetとしてsortし、duplicatesを保持。
- modifiers/conditions/constraintsのarray orderをV1では保持。
- undocumented aliasing/case folding/whitespace trimming/Unicode normalizationを禁止。
- JCS/I-JSONで意味を保てないnumeric/extension valueはcoerceせずdiagnoseする境界を追加。
- unknown semantic extensionを黙って除外せず失敗させる参照実装を追加。
- canonical thermal-transfer NSRとadapter provenance/order差のNSR-layer equivalence fixtureを追加。
- schema pattern、FeasibilityReport、examples、testsをversioned fingerprint representationへ同期。
- renderer未実装のためreal multilingual round-tripを未完了のまま維持。
- `SemanticFingerprint != artifact content_hash` を明文化し、generic artifact `content_hash` / `registry_hash` のcanonical encoding/hash algorithmは未決定のまま維持。
- MIR grammarとMKI primitivesは変更なし。

## v0.7.2 — Multilingual Language Adapters・NSR・Cross-language Conversion

- Latin Frontendを特権的frontendではなく `LanguageAdapter<lat>` として一般化。
- 共通 `LanguageAdapter<L>` contractを導入。
- 初期project adapter priorityを `lat → lzh → ger → jpn → eng → zho` と定義。
- project adapter IDとexternal ISO/BCP47 tag identityを分離。
- `GeneralLexicon`, `DomainLexicon`, `LexemeEntry`, SemanticRegistry mappingの責任境界を定義。
- AI/LLMをoptional `NormalizerProvider` とし、outputをuntrusted `NormalizationCandidate` と定義。
- `NormalizationCandidateSet`, `NormalizationDecision`, `NormalizedSemanticRepresentation (NSR)` を追加。
- `Language-specific parse != NSR`, `AI proposal != semantic truth`, `Confidence != proof`, `Lexical meaning != Entity resolution` を明文化。
- `AmbiguityPolicy = StrictReject / InteractiveResolve / ContextualDeterministic / LegacyPermissive` を追加。
- `Unexpected result != undefined behavior` を明文化。
- cross-language conversionを`Source<L1> → NSR → SurfaceRenderer<L2>`と定義。
- `SemanticFingerprint` / `CrossLanguageDrift`、`reference/language-adapters.md`、`schemas/nsr.schema.json`、examplesを追加。
- MIR source syntaxとMKI data plane 6 primitiveは変更なし。

## v0.7.1 — Feasibility Evaluator・Dry-run Report Contract

- `EvaluationInput`, `SemanticAST`, `TypedMIR`, `NormalizedIR`, `KernelPlan`, `FeasibilityReport` を正式化。
- world effectなしのdry-run評価pipelineを定義。
- `Estimate<T>`、`EnergyEstimate` / `EnergyBreakdown`、independent assessments、diagnostics/evidence/assumptionsを追加。
- `reference/feasibility.md`, `schemas/feasibility-report.schema.json`, `examples/feasibility-report.json` を追加。

## v0.7 — Runtime Tick・Scheduler・Numerical Integration・Deterministic Replay

- `RuntimeEpochID`, `RuntimeTickID`, `TickInterval`, `TickStamp`, `MicrostepOrdinal` を追加。
- runtime tickをphysical time quantumではなくscheduler step identityとして定義。
- logical scheduler phases、SchedulingPolicy、MicrostepBudget、TemporalTolerance、IntegratorContract、ReplayManifest/Profileを追加。
- `DeterministicReplay != Rewind`。

## v0.6.4 — World Index・RESOLVE Data Contract

- `WorldIndex`, `WorldIndexSnapshot`, revision/schema contractを追加。
- World IndexをWorld Stateではなくversioned search viewとして定義。
- Identity / Symbolic / Spatial / Relation / Visibility indexを論理分離。
- `ResolverQuery<T>`, `CandidateSet<T>`, consistency/query budget/revalidationを導入。
- `WorldIndex != WorldState`, `CandidateSet != Ref set`, `Visibility != Authority` を明文化。

## v0.6.3 — Normative Conventions・許容範囲・Documentation Contract

- `MUST / MUST NOT / SHOULD / SHOULD NOT / MAY` を規範語として導入。
- specified / implementation-defined / registry-defined / world-defined / profile-defined / unspecified / undefinedを区別。
- undefinedな危険world effectは原則fail closed。
- tolerance / resolution / uncertainty / numerical errorを分離。
- `spec/` historical snapshotと `reference/` live referenceを明文化。

## v0.6.2 — Reaction kinetics・Catalyst・Pathway・Equilibrium

- KineticModel / RateLaw / ReactionPathway / ReactionNetworkを追加。
- Extent / Volumetric / Surface rate basisを分離。
- `Stoichiometry != RateLaw`。
- Catalyst / Inhibitor / Activity / Equilibrium modelを追加。

## v0.6.1 — Matter・Species・Structure・Reaction accounting

- MatterPayloadの単一amountを廃止しSpecies量をCompositionへ保持。
- Element/Nuclide/Species/MaterialClass IDを追加。
- CompositionとCompositionEstimateを分離。
- StructureSchema / ThermodynamicState / ReactionRule / ReactionExtentを追加。
- Reactionは新primitiveにせずRECONFIGURE契約とした。

## v0.6 — Selection・Payload・Registry・Observer Model

- bounded `select<T>` とSelection snapshotを追加。
- TRANSFERを `Channel<K> × PayloadOf<K>` へ一般化。
- MatterPayload / ConservationProfile / SemanticRegistry / ObserverModelを追加。

## v0.5.2 — 式・selector・量trait・意味論の正式化

- MIR演算子優先順位と `^` を正式追加。
- Selector/Refを分離。
- Transferable/Conservedを直交trait化。
- `C=<Σ,H,Ω,P>` small-step骨格を追加。

## v0.5.1 — 整合性・参照資料整備

- SI基底を `(kg,m,s,A,K,mol,cd)` へ拡張。
- 非同期TRANSFERと文法を整合。
- Latin例文CSV、術語索引、整合性報告を追加。

## v0.5 — 時間・因果・イベント・非同期実行

- `Σ` + `H=(E,≺)` world model。
- Instant/Event/TransferHandle/HistoricalRefを追加。
- async TRANSFER / event / timeout / Restore vs Rewindを導入。

## v0.4 — 参照・同一性・所有権・寿命

- Ref/EntityID/State/Authority/Ownershipを分離。
- IdentityPolicy, Capability, Lease, Borrow, revisionを追加。

## v0.3 — 制御構造・関数・抽象化

- pure/effectful計算分離、SSA let、Truth、bounded loop、fn/proc/spellを導入。

## v0.2 — MIR正式化・型付き精緻化

- MIR暫定構文、Γ/Δ/Λ/Π、双方向型検査、意味型+SI次元を導入。

## v0.1 — カーネルモデル

- Magical Latin → AST → MIR → MKI → World State。
- MKI data plane 6命令/control plane 6操作を定義。
