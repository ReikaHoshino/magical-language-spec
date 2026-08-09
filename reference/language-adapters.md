# Language Adapter / NSR Reference — v0.7.3

**Status:** normative adapter/normalization boundaries; individual linguistic models are adapter-defined.

## Purpose

多言語自然言語を共通の正規意味表現へ落とし、Latin以外のfrontendをcompiler coreから分離する。

## Non-goals

- 自然言語を直接MKIへ実行しない。
- AI出力をsemantic truthとして扱わない。
- 一般辞書全体をcompiler coreへ埋め込まない。
- project adapter IDを外部language tag規格と同一視しない。

## Depends on

- `conventions.md`
- `source-text-normalization.md`
- `latin-frontend.md`
- `feasibility.md`
- `selectors.md`
- `registry.md`

## Key invariants

```text
Language-specific parse != NSR
NSR != SemanticAST
AI proposal != semantic truth
Confidence != proof
Lexical meaning != Entity resolution
Cross-language conversion != direct translation
Unexpected result != undefined behavior
```

## 1. Adapter priority

初期実装順:

```text
lat
lzh
ger
jpn
eng
zho
```

これはproject implementation priorityであり、言語学的優劣を意味しない。

project adapter IDは安定識別子として扱い、外部tag例 (`la`, `de`, `ja`, `en`, `zh`, ISO 639-3等) はmetadata mappingとする。

## 2. Adapter contract

```text
LanguageAdapter<L> {
    adapter_id
    adapter_revision
    external_language_tags
    source_text_profile_revision
    lexicon_revision?
    grammar_revision?
    normalizer_revision
    normalization_profile
    capabilities
}
```

capability例:

```text
Morphology
DependencySyntax
SemanticRoles
Deixis
EllipsisRecovery
RegisterAnalysis
SurfaceRendering
```

Adapterは全capabilityを実装する必要はない。未実装部分はprovenance付きUnknown/diagnosticへ落とす。

### 2.1 Compatibility ownership

adapter/lexicon/grammar/normalizer revision compatibilityの共通decision envelopeは
[`compatibility.md`](compatibility.md) とする。判定規則は
`LanguageAdapterCompatibilityProfile`が所有し、次を明示する。

```text
adapter_id
adapter_revision
source_text_profile_revision
lexicon_revision?
grammar_revision?
normalizer_revision
required capabilities
```

revisionはopaque identity tokenであり暗黙の大小・prefix compatibilityを持たない。
accepted exact revisions、explicit migration、capability-preserving relationのいずれも
profileに宣言されなければresultは`Undetermined`とする。外部language tagはmetadataであり、
project `adapter_id`の代用または互換性証拠にしてはならない。

## 3. Layering

```text
UTF-8 bytes / Unicode scalar text
→ common SourceTextNormalizerV1
→ normalized source + original-source map
→ tokenization / segmentation
→ lexical candidates
→ morphology
→ syntactic relations
→ semantic roles
→ selector / quantity / action proposals
→ NormalizationCandidateSet
→ NSR
```

言語により途中段階は異なる。

common source preprocessingのnormative contractは
[`source-text-normalization.md`](source-text-normalization.md) とする。ここでのNFC /
line-ending処理はsource representationだけを扱い、NSR identifier normalization、
SemanticFingerprint、artifact hashを変更しない。

例:

- Latin: case morphology + preposition + verb frame。
- Literary Chinese: segmentation、省略、語順、機能語、文脈依存が中心。
- German: case/article/verb frame/separable verb等。
- Japanese: 助詞、省略、係り受け、指示表現等。
- English: word order/preposition/dependency等。
- Modern Chinese: segmentation、把/被構文、語順、量詞等。

## 4. Lexicon layers

```text
GeneralLexicon<L>
DomainLexicon<L>
SemanticRegistry mappings
ProfileAliases<L>
```

DomainLexiconは魔術用語・技術語・verb frameを保持できる。

```text
LexemeEntry {
    lexeme_id
    language
    lemma
    surface_forms?
    part_of_speech?
    morphology?
    semantic_candidates
    argument_frame?
    register?
    provenance
}
```

辞書の意味候補は最終型決定ではない。

### 4.1 Machine-readable `lat` serialization

`LanguageAdapter<lat>` の最小domain lexicon serializationは
[`schemas/latin-lexicon.schema.json`](../schemas/latin-lexicon.schema.json)、
reference fixtureは
[`examples/latin-adapter/minimal-lexicon.json`](../examples/latin-adapter/minimal-lexicon.json)
とする。

共通role vocabularyは
[`schemas/semantic-roles.schema.json`](../schemas/semantic-roles.schema.json)を正本とし、
Latin argument frameとNSR roleは同じdefinitionを参照する。role identityをLatin固有schemaへ
複製しない。

- morphologyは候補集合として保存し、同じsurface formの複数分析を保持する。
- argument frameのroleはmorphology / preposition / frame / contextを組み合わせるためのproposalであり、格単独による最終semantic roleではない。
- semantic candidateはlexical proposalであり、`EntityID`、Capability、最終TypedMIR型、MKI execution dataではない。
- common role vocabularyとLatinの全case表現は既存referenceを再利用する。current referenceが閉集合を定義していないpart of speech、tense、prepositionは拡張可能な語彙として扱い、特定fixtureのsubsetへ固定しない。
- extensible qualifier内を含むlexicon artifactの全階層で、`EntityID`、Capability、lease、authority fieldを禁止する。
- artifact identity / revision / provenanceはshared artifact metadata boundaryを再利用する。
- canonical content hashはcurrent referenceで未決定であり、fixtureは明示的unresolved
  sentinelを用いる。lexicon compatibility algorithmはadapter compatibility profileが
  所有し、profile/revision relationが未提示なら`AdapterCompatibilityUndetermined`とする。

pre-v0.8 executable reference pathは
[`tools/latin_adapter.py`](../tools/latin_adapter.py)とする。これは明示的`lat` dispatch、
common source normalization、minimal tokenization/lexicon/morphology/frame analysis、
role proposal、candidate selection boundary、NSR validation対象出力までを提供する。
Entity resolution、Capability grant、TypedMIR、KernelPlan、Local Evaluatorは提供しない。

## 5. AI normalizer

AI providerはoptional。

```text
NormalizerProvider =
    RuleBased
  | LexiconDriven
  | Statistical
  | AI
  | Hybrid
```

AI/Statistical outputは必ずcandidate扱い。

```text
NormalizationCandidate {
    candidate_id
    nsr
    unresolved_fields
    evidence
    provider
    ranking_metadata?
}
```

`ranking_metadata` のconfidence/probabilityだけでCOMMIT safety conditionを満たしたことにしてはならない。

## 6. NSR goal

NSRは次を満たすSHOULD:

- 言語非依存。
- 人間可読。
- source languageの語順や活用に依存しない。
- EntityID/Capability/Leaseをまだ要求しない。
- 未指定argumentをUnknownとして保持可能。
- source provenanceへ戻れる。

例:

```text
TransferCommand {
    patient = SemanticKind(Energy, mode=Thermal)
    source = SelectorProposal(Symbolic("water"))
    goal = SelectorProposal(Symbolic("air"))
    quantity = Unknown(MissingSurfaceArgument)
}
```

## 7. Semantic roles

共通role vocabulary例:

```text
Actor
Patient
Source
Goal
Recipient
Instrument
Path
Location
Condition
Cause
Quantity
Property
ConstraintSubject
```

各言語Adapterは表層文法からこれらroleを提案する。

## 8. AmbiguityPolicy

```text
StrictReject
InteractiveResolve
ContextualDeterministic
LegacyPermissive
```

### StrictReject

semantic-criticalな候補が複数残る場合は停止。

### InteractiveResolve

candidate/evidence差を提示し、人間または上位agentの選択を待つ。

### ContextualDeterministic

profile-defined ruleで一意化。context/evidence/tie-breakはrecordするMUST。

### LegacyPermissive

古い魔術・危険profile用。複数のvalid candidateのうち一つをprofile-defined orderingで選択できる。

LegacyPermissiveはtype/authority/conservation/identity checksを無効化しない。

術者の意図と結果が異なっても、選ばれたNSRが仕様上validなら:

```text
UnexpectedResult
```

というworld/story outcomeになりうるが、これはundefined behaviorとは区別する。

### 8.1 Selection boundary

ambiguity selectionは`NORMALIZE` stageのcandidate選択であり、semantic truth、術者意図、
execution safetyの証明ではない。

```text
selected candidate != user's intent proof
normalization validity != type/authority/conservation/identity validity
confidence != proof
```

ranking前に、adapter/profile admission、NSR shape、normalization budget等の
NORMALIZE-stage eligibilityを検査するMUST。eligibleでないcandidateを高いscoreや
legacy profileで復活させてはならない。選択後もtype、authority、conservation、
identityのmandatory downstream checksを通常どおり実行するMUST。

### 8.2 Ranking inputs

適合profileはranking ruleごとにstableな`rule_id`、入力種別、comparator、
missing-value policy、evidence requirementをversioned contractとして宣言するMUST。
同一profile revision内の`rule_id`は一意であるMUST。
V1で利用できる入力種別は次に限定する。

```text
ExplicitSelection
ContextualEvidence
MorphologyCompatibility
ArgumentFrameCompatibility
LexicalCompatibility
RegisterProfilePreference
ProviderRank
ProviderConfidence
LegacyInputPosition
```

- morphology/frame/lexical signalは候補生成時のproposal/evidenceであり、semantic proofではない。
- context signalはrecordされたcontext snapshotの`fact_ids` / `evidence_ids`から参照可能であるMUST。
- provider rank/confidenceを使用してよいが、type/authority/conservation/identity checkの
  resultへ変換してはならない。
- `ExplicitSelection`は`InteractiveResolve`の外部選択を記録するために使う。
- `LegacyInputPosition`は`LegacyPermissive` profileだけが明示的に宣言できる。
  宣言がないcandidate input orderはranking inputではない。
- local clock、unordered map iteration、provider arrival timing、process-random seed、
  unrecorded world queryを暗黙のranking inputにしてはならない。

ruleの値はboolean、integer、string、missingのいずれかとする。string比較を使用する場合は、
admitted valueのUnicode scalar value列をcode-point orderで比較する。この規則はsource textの
Unicode normalization方式を決めず、ranking engineが受け取った値を暗黙変換しないためのもの
である。

`Boolean*` comparatorはboolean、`Integer*` comparatorはinteger、
`StringCodePoint*` comparatorはstringだけを受理するMUST。型不一致をcoerceせず
`AmbiguityDecisionUnreproducible`とする。

### 8.3 Deterministic total order

`ContextualDeterministic`と`LegacyPermissive`のselection profileは:

```text
profile_id
profile_revision
ordering_revision
ordered ranking_rules[]
final_tie_break = [
  SemanticFingerprintAscending,
  CandidateIdAscending
]
```

を記録するMUST。

ranking engineは宣言順にruleを比較し、最初の非同値termで順位を決める。missing valueは
ruleの`RejectCandidate / RankFirst / RankLast / Unreproducible`宣言どおりに扱う。
暗黙defaultは禁止する。

通常のcandidate input orderは比較前に捨て、最後は
`SemanticFingerprintV1`、次にstable `candidate_id`の昇順でtotal orderを得るMUST。
`candidate_id`は入力array indexから生成してはならない。同じsemantic fingerprintの
candidate間でrepresentative IDが変わっても選択semantic contentは同一である。

`LegacyInputPosition`を明示するlegacy profileだけは、recordされたinput positionを
通常ruleの一つとして使用してよい。その場合もprofile/order revision、元のinput order、
全candidateをtraceへ保存するMUSTであり、入力順依存を暗黙化してはならない。

### 8.4 Policy behavior

| Policy | semantic-critical candidateが複数 | selection source | required result |
|---|---|---|---|
| `StrictReject` | 選択しない | none | `Rejected` + `AmbiguousNormalization` |
| `InteractiveResolve` | 外部選択待ち | explicit actor/evidence | `PendingInteraction`またはrecord済み`Selected` |
| `ContextualDeterministic` | context/profile ruleでtotal order | reproducible context/evidence | `Selected`。required inputを再現できなければ`Unreproducible` |
| `LegacyPermissive` | valid candidateからprofile ruleで選択可 | versioned legacy ordering | `Selected` + warning/provenance。mandatory safety checksは維持 |

`ContextualDeterministic`はrecordされたcontext evidenceで現在のcandidate setを一意化する。
必要contextが不足・revision不一致なら、weak evidenceやinput orderへfallbackせず
`AmbiguityDecisionUnreproducible`とする。

`LegacyPermissive`はprofileが宣言したassumptionやweaker orderingを使用できる点が異なる。
ただしassumption、rejected alternatives、warningを残し、unsafe candidateを選んだり
downstream checkを省略したりしてはならない。

### 8.5 AmbiguityDecisionTraceV1

machine-readable contractは
[`schemas/ambiguity-decision-trace.schema.json`](../schemas/ambiguity-decision-trace.schema.json)
を正とする。traceは最低限:

```text
decision_id / policy / decision_status
profile_id / profile_revision / ordering_revision / ranking rules
context snapshot ID / revision / fact IDs / evidence IDs
candidate-set ID / revision / input order / canonical order
candidate IDs / SemanticFingerprintV1 / evidence / assumptions
per-candidate eligibility / rank terms / rejection reasons
selected candidate / rejected alternatives / unresolved assumptions
mandatory downstream checks
diagnostics
replay status and recorded selection
```

を保持するMUST。

`input_candidate_ids`はdebug evidence、`canonical_candidate_ids`はinput permutationと独立な
順序である。candidate/evaluation/referenceの集合が一致しないtraceはinvalidとする。
selection traceはfull NSR、authority grant、Capability、World Stateの代替ではない。

### 8.6 Replay, context drift, and unexpected result

replayは同一のprofile revision、ordering revision、context snapshot revision、
candidate-set revision、candidate evidenceから同じselected semantic fingerprintを
再計算する。

- 必要revision/evidenceが利用不能なら`AmbiguityDecisionUnreproducible`。
- context snapshotが置き換わった場合は`AmbiguityContextDrift`。
- compatibleと判断された入力から異なるselectionが出た場合は
  `AmbiguityReplayDivergence`。
- legacy selectionがvalidだが術者意図と異なることが後から判明した場合は
  `UnexpectedResult`。これはranking divergenceやundefined behaviorではない。

replay/debug traceだけをauthority、current World State、元の術者意図の証明として
使用してはならない。

machine-readable conformance examples:

- [`StrictReject`](../examples/ambiguity-policy/strict-reject.json)
- [`InteractiveResolve`](../examples/ambiguity-policy/interactive-pending.json)
- [`ContextualDeterministic` input-order permutations](../examples/ambiguity-policy/contextual-permutation-a.json)
  / [`permuted`](../examples/ambiguity-policy/contextual-permutation-b.json)
- [`LegacyPermissive` unexpected result and replay](../examples/ambiguity-policy/legacy-permissive-unexpected-result.json)
- [`context drift / unreproducible decision`](../examples/ambiguity-policy/context-drift-unreproducible.json)

## 9. Decision provenance

```text
NormalizationDecision {
    candidate_id
    ambiguity_policy
    selected_by
    evidence_ids
    rejected_candidate_ids
    unresolved_assumption_ids
}
```

この短い形は`AmbiguityDecisionTraceV1`のsummary viewである。deterministic/permissive
selectionまたはreplay/debugが必要な場合はfull traceを保存するMUST。
Evaluatorはsummaryまたはfull trace referenceをreportへ添付できるSHOULD。

## 10. Cross-language conversion

```text
Source<L1>
→ normalize
→ NSR
→ render<L2>
→ Source<L2>
```

SurfaceRenderer:

```text
SurfaceRenderer<L> {
    adapter_id
    renderer_revision
    register_profile
    fidelity_profile
}
```

rendererはNSRにない新semantic fieldを追加してはならない。

## 11. SemanticFingerprint

```text
CanonicalSemanticProjectionV1(NSR)

SemanticFingerprintV1(NSR)
  = SHA-256(
      UTF-8(
        JCS(CanonicalSemanticProjectionV1(NSR))
      )
    )
```

JCSはRFC 8785 JSON Canonicalization Schemeを指す。machine-readable textual
representationは次の形をMUSTとする。

```text
sf:v1:sha256:<64 lowercase hexadecimal digits>
```

version/profile prefixはfingerprint representationの一部である。

### 11.1 Projection V1

top-levelではexecution-relevant semantic contentのみを含める。

```text
kind
action       // presentなら明示nullも含める
roles
modifiers
conditions
constraints
```

次はnormalization/provenance/transport metadataとして除外する。

```text
schema_version
provenance
ambiguity
semantic_fingerprint
unknowns
```

`unknowns` はdiagnostic/index summaryであり、意味上のUnknown occurrenceの正本ではない。
fingerprint対象のUnknownはsemantic value位置に
`{"kind":"Unknown","reason":"..."}` として存在するMUST。

current `schemas/nsr.schema.json` のsemantic valueでは次のfieldをV1 semantic
fieldとして認識する。

```text
kind
semantic_kind
mode
selector
value
unit
reason
```

`evidence_ids` は除外する。`selector` とsemantic `value` の内部payloadはsemantic
contentとして含める。ただしsource spans、tokenization、morphology、candidate/evidence
ID、provider identity、commentary、renderer register/style等のlanguage-specific
evidenceはfingerprintへ含めてはならない。

NSR semantic位置にschema-validだがV1がsemantic/provenanceのどちらか判断できない
extension fieldが現れた場合、実装は黙って無視せず
`UnsupportedSemanticExtension` 相当のdiagnosticで失敗するMUST。

### 11.2 Omitted / null / Unknown

```text
field omitted
!=
field present with JSON null
!=
semantic Unknown(reason)
```

- omittedはその位置にsemantic field/valueをassertしない。
- explicit nullはschemaが許す場合にprojectionへ保持する。
- Unknownは明示的semantic markerでありfingerprintへ含める。
- canonicalizationはこれらを相互変換してはならない。

安価に証明できる範囲でtop-level `unknowns` summaryとsemantic Unknown occurrenceが
矛盾する場合、実装は推測せずdiagnoseするSHOULD。

### 11.3 Ordering / identifiers

object property orderはJCSが処理する。

`roles` はsource word orderではなくsemantic-role assignmentである。projected roleを
role名とprojected valueで決定論的にsortし、重複を保持するMUST。

`modifiers`, `conditions`, `constraints` のarray orderはV1では保持するMUST。
current referenceがorder-insensitiveと定義していないcollectionを暗黙に可換としない。

fingerprintingはundocumented aliasing、case folding、whitespace trimming、Unicode
normalizationを行ってはならない。alias resolutionはcanonical NSR生成前の責務である。

### 11.4 JCS / numeric boundary

projection dataはJCS/I-JSONで意味を変えず表現可能であるMUST。表現不能なnumericまたは
extension valueをcoerceしてはならず、diagnosticとして失敗するMUST。

この規則はrepository-wide quantity/duration JSON encodingを決定しない。

### 11.5 Assumptions and hash boundary

execution-relevant explicit assumptionは、conditions/constraints/semantic value等の
structured NSR semantic contentとして符号化されている場合のみfingerprintへ含める。
report内のfree text、comment、evidence、provider metadataを注入してはならない。

```text
SemanticFingerprint != artifact content_hash
Canonical semantic projection != full NSR serialization
```

`SemanticFingerprintV1` のJCS + SHA-256 decisionはgeneric artifact `content_hash`,
`registry_hash` その他domain hashのcanonical byte encoding/hash algorithmを決定しない。

### 11.6 Reference utility

repository-local reference implementationは
[`tools/semantic_fingerprint.py`](../tools/semantic_fingerprint.py)、canonical fixtureは
[`examples/semantic-fingerprint/thermal-transfer-v1.json`](../examples/semantic-fingerprint/thermal-transfer-v1.json)
とする。

維持するinvariant:

```text
Semantic equality != byte-for-byte source equality
Role order != source word order
Unknown != omitted
Unknown != null
null != omitted
Provenance difference alone != semantic drift
Evidence difference alone != semantic drift
Semantic change => fingerprint change (for represented V1 semantics)
```

## 12. Round-trip validation

```text
N0 = normalize(source_L1)
T  = render(N0, L2)
N1 = normalize(T)

SemanticFingerprint(N0) == SemanticFingerprint(N1)
```

をsemantic round-trip successの基本条件とする。

不一致:

```text
CrossLanguageDrift
```

自然な翻訳文として良好でもfingerprintが変化すれば、魔術用conversionとしてはunsafeでありうる。

v0.7.3時点ではrenderer実装が存在しないため、実在するsource→renderer→source
round-trip成功を主張しない。fixtureは異なるadapter provenance/orderを持つ2つのNSRが
同一projection/fingerprintになるNSR-layer equivalenceのみを検証する。full round-tripは
renderer実装までTODOである。

## 13. Cross-language convenience

将来CLI例:

```text
spell normalize --lang lat spell.txt
spell render --to jpn normalized.json
spell convert --from lat --to ger spell.txt
spell compare a.lat b.jpn
```

`convert` は内部で必ずnormalize/renderを通る。

## 14. Adapter-specific lexicon strategy

`lat` は既存Magical Latin lexicon/verb frameを最初のreference implementationとする。

`lzh` 以降も言語固有辞書を持てるが、共通semantic kindはSemanticRegistryへ寄せる。

```text
language lexeme
  -> semantic candidate ID
  -> SemanticRegistry entry
```

同一概念の多言語同義語を各Adapterでduplicated kernel meaningとして持たない。

## 15. Diagnostics

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
RendererUnavailable
CrossLanguageDrift
```

## 16. Feasibility integration

FeasibilityReportは必要に応じて:

```text
adapter_id / revision
source language tags
normalization provider
candidate count
selected candidate
AmbiguityPolicy
NSR
normalization diagnostics
evidence
SemanticFingerprint
render/round-trip result
```

を保持できる。
