# Magical Latin Adapter — v0.7.2

**Status:** normative adapter-specific safety/semantic mapping; historical register discussion is informative unless marked otherwise.

## Purpose

Magical Latinを魔法そのものではなく、共通 `LanguageAdapter` framework上の最初の実装 `LanguageAdapter<lat>` として定義する。

Latin入力は:

```text
Latin source
→ LanguageAdapter<lat>
→ NormalizationCandidateSet
→ NSR
→ SemanticAST
→ TypedMIR
→ KernelPlan / FeasibilityReport
```

を通る。

## Non-goals

- Latin文字列を直接MKIへ実行しない。
- Latinだけを特権的source languageとしてcompiler coreへ埋め込まない。
- 曖昧な形態/項役割をAI confidenceだけで一意化しない。
- historical/Neo-Latinの唯一の語彙体系を固定しない。

## Depends on

- `conventions.md`
- `language-adapters.md`
- `selectors.md`
- `types.md`
- `feasibility.md`
- `mki.md`

例文の正本データ:

- [`data/latin-examples.csv`](../data/latin-examples.csv)
- schema/status/editorial policy: [`latin-examples.md`](latin-examples.md)

## Key invariants

```text
Latin source != magic effect
Latin parse != NSR
Morphology != semantic role by itself
Lexical meaning != Entity resolution
AI proposal != semantic truth
```

## 1. Adapter identity

project adapter ID:

```text
lat
```

外部language tag/ISO code mappingはadapter metadataで扱う。

Latinは初期実装優先度1位だが、semantic core上で他言語より高い権限を持たない。

## 2. Lexicon strategy

Latin辞書は少なくとも:

```text
GeneralLatinLexicon
MagicalLatinDomainLexicon
SemanticRegistry mapping
Profile aliases / register metadata
```

へ分離できる。

例:

```text
calor, caloris
  -> semantic candidates: ThermalEnergyExpression

transfero, transferre
  -> argument frame:
       Patient : ACC
       Source  : A/AB + ABL
       Goal    : AD + ACC
       Path    : PER + ACC
```

辞書entryは `EntityID` や最終TypedMIR型そのものではない。

Machine-readable reference:

- schema: [`schemas/latin-lexicon.schema.json`](../schemas/latin-lexicon.schema.json)
- shared role vocabulary:
  [`schemas/semantic-roles.schema.json`](../schemas/semantic-roles.schema.json)
- minimal lexicon: [`examples/latin-adapter/minimal-lexicon.json`](../examples/latin-adapter/minimal-lexicon.json)
- canonical normalization evidence:
  [`examples/latin-adapter/thermal-transfer-normalization.json`](../examples/latin-adapter/thermal-transfer-normalization.json)
- reference implementation:
  [`tools/latin_adapter.py`](../tools/latin_adapter.py)
- unresolved morphology / `StrictReject` fixture:
  [`examples/latin-adapter/aquae-strict-reject.json`](../examples/latin-adapter/aquae-strict-reject.json)

canonical fixtureはtoken/source span、lexeme/morphology evidence、verb-frame evidence、
role proposal、`NormalizationCandidateSet`、NSRを分離して記録する。`aquae` のように
複数の形態分析を持つsurface formは候補を保持し、辞書だけで一意化しない。

### 2.1 Reference implementation boundary

pre-v0.8 reference implementationは次の範囲だけを実行する。

```text
SourceTextNormalizerV1
→ Latin tokenization
→ minimal lexicon lookup
→ morphology candidate preservation
→ preposition + transfero frame matching
→ role proposals
→ NormalizationCandidateSet
→ schema-valid NSR + SemanticFingerprintV1
```

明示的adapter dispatchだけを提供し、language detectionは行わない。Latin lexical lookupは
source spellingとspanを保持したままadapter-owned case-insensitive lookup keyを使用する。
これはcommon source normalization、NSR identifier normalization、またはsemantic
equivalence ruleではない。

canonical `LAT-001` では `aqua` のnominative/ablative形態候補をtoken evidenceとして保持し、
`ab` + `transfero` frameのSource/ablative requirementとの一致によってablative候補を選ぶ。
形態だけからSourceを確定しない。

frame/contextが候補を一意化できない場合、candidateを入力順やconfidenceで選んではならない。
`StrictReject`は`SemanticRoleAmbiguous` / `AmbiguousNormalization`で停止し、
`InteractiveResolve`は明示選択待ちとする。versioned selection profileを渡していない
deterministic/permissive policyは`AmbiguityDecisionUnreproducible`となる。

## 3. 格の典型的役割

| 格 | 典型的意味 |
|---|---|
| 主格 | Actor / constraint subject |
| 対格 | Patient / direct target |
| 与格 | Recipient / beneficiary |
| 属格 | Type / property / ownership |
| 奪格 | Source / instrument / condition |
| 呼格 | Agent selection |

意味は格だけではなく、前置詞・verb frame・contextを合わせて決定するMUST。

厳格Magical Latinでは自然ラテン語の自由語順を完全には利用せず、曖昧性を減らす明示的項表現をSHOULD使用する。

## 4. 命令法 / 接続法

- 命令法: 一回操作の標準表現。
- 独立した規範的接続法: 継続制約、禁止、規則の標準表現。
- 条件節・時間節・event節: 各従属節規則とverb frameに従う。

```text
Si lapis intra circulum est, nexum aperi.
```

`est` は直説法で条件分岐へ精緻化される。

```text
Globus intra circulum maneat.
```

`maneat` はpersistent `CONSTRAIN` 候補へ正規化される。

## 5. Selectorとの関係

```text
Hunc lapidem designa.
```

は直接EntityIDを含まず:

```text
SelectorProposal<Object>
→ later RESOLVE / WorldIndex
→ Ref<Object>
```

とする。

```text
Lexical deixis != Entity resolution
```

## 6. Thermal transfer example

```text
Calorem ab aqua ad aerem transfer.
```

Surface:

```text
Patient : calorem
Source  : ab aqua
Goal    : ad aerem
Action  : transfer
```

NSR候補:

```text
TransferCommand {
    Patient = SemanticKind(Energy, mode=Thermal)
    Source = SelectorProposal(Symbolic("water"))
    Goal = SelectorProposal(Symbolic("air"))
    Quantity = Unknown(MissingSurfaceArgument)
}
```

`Heat` 独立transfer kindを作らず、後段で:

```text
TRANSFER<Energy>(mode=Thermal)
```

へ精緻化できる。

Quantityは表層にないため捏造しないMUST。

## 7. Other examples

Momentum:

```text
Quantitatem motus a terra ad lapidem transfer.
```

Channel:

```text
Canalem energiae a fonte ad globum aperi.
```

Constraint:

```text
Globus intra circulum maneat.
```

Event:

```text
Cum hostis limen transeat, globum emitte.
```

法だけを直接MIR命令へ写像せず、節全体を解析する。

## 8. Ambiguity

Latin固有の曖昧性例:

```text
aquae
```

は複数格解釈を持ちうる。

Adapterは複数candidateを `NormalizationCandidateSet` として保持できる。

安全profileでは:

```text
AmbiguousCaseError
AmbiguousNormalization
```

等をreportして停止可能。

`LegacyPermissive` profileでは、複数のsemantically valid candidateからprofile-defined orderingで一つを選ぶことができるが、選択根拠を記録する。

reference implementationが報告するfocused diagnostics:

```text
LexiconEntryMissing
MorphologicalAnalysisIncomplete
SemanticRoleAmbiguous
NormalizationFailed
AmbiguousNormalization
AmbiguityInteractionRequired
AmbiguityDecisionUnreproducible
```

source ingress rejectionは`SourceTextNormalizerV1`のstable diagnosticを保持し、NSR candidateを
生成しない。

## 9. AI-assisted Latin analysis

AIは:

- lemma候補。
- morphology候補。
- syntactic relation候補。
- semantic role候補。
- ellipsis/paraphrase候補。

を提案MAY。

ただし:

```text
AI Latin analysis = untrusted proposal
```

であり、confidence値だけでsemantic-critical ambiguityを解消してはならない。

## 10. Cross-language conversion

Latinを別言語へ変換する場合:

```text
lat source
→ NSR
→ SurfaceRenderer<target>
```

を使う。

直接翻訳器の出力をsemantic authorityとして扱わない。

round-trip時は `SemanticFingerprint` を比較できる。

## 11. Dry-run evidence

Evaluatorは可能な範囲で:

```text
source text
morphological analysis
verb frame
semantic roles
normalization candidates
selected NSR
ambiguity policy
SemanticAST
TypedMIR
KernelPlan
FeasibilityReport
```

を表示できるSHOULD。

source span / token / lexicon entry / grammar rule / AI providerへ追跡可能なprovenanceを保持するSHOULD。

## 12. Context and omitted arguments

自然/歴史的Latinはquantity等を省略しうる。

- profile/registry/world contextで一意に証拠化できるなら補完MAY。
- 補完値とDefinitionSource/assumptionを記録MUST。
- 一意化できなければUnknownを保持MUST。

## 13. 校訂方針

評価軸:

1. semantic correctness。
2. frontend safety。
3. morphological correctness。
4. historical/register fit。

これらは別軸。

## 14. Definition ownership

- common adapter/NSR contract: specified。
- Latin morphology/verb-frame safety rules: adapter specification。
- individual lexicon/register choice: registry/profile/editorial-defined。
- AI provider/model behavior: implementation/profile-defined + untrusted evidence。
- historical naturalness judgement: informative/editorial unless profile requires it。
