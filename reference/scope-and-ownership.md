# Specification Scope and Definition Ownership — pre-v0.8

**Status:** normative scope and ownership contract; examples and project-language notes are informative.

## Purpose

本書は、魔術言語仕様が保証するもの、保証しないもの、および実装・registry・world・profileへ
委譲する判断を一つの入口から確認できるようにする。

この仕様への適合は、ここで定義するcontractと境界を守ることを意味する。完全なcompiler、
evaluator、runtime、world model、または特定worldbuildingの存在を保証するものではない。

## Non-goals

- 世界観としての「魔法」の起源・社会制度・知覚体験を定義しない。
- `魔力` や `魔子` を組込み物理量・粒子・権限として新設しない。
- parser、database、solver、scheduler、OS isolationの具体algorithmを固定しない。
- `planning-inference.md`が所有するUnknown inference、PlanningAssumption、generation
  lowering、terminal bindingの意味論を本scope indexで重複定義しない。
- historical `spec/` snapshotへcurrent referenceの未release変更を遡及させない。

## Depends on

- [`conventions.md`](conventions.md)
- [`architecture.md`](architecture.md)
- [`semantics.md`](semantics.md)
- [`mki.md`](mki.md)
- [`security-sandbox.md`](security-sandbox.md)
- [`compatibility.md`](compatibility.md)

## Key invariants

```text
specification contract != complete implementation
surface representation != semantic authority
Language-specific parse != NSR != SemanticAST != TypedMIR != KernelPlan
Evaluation != Execution
Feasibility != Authority grant
Registry metadata != Capability
Visibility != Authority
Unknown != zero
SemanticFingerprint != artifact content_hash
MKI data-plane primitives = 6
magic effect request != physical-law definition
ordinary magic != physical-law mutation
World Kernel != DefinitionSource
scheduler/integrator behavior != physical law
```

## Core design principle — magic as authorized information control

本仕様は、魔法を**物理世界に対する型付き・権限付きの情報制御**として扱う。

術式はworld内部実装を直接書き換える命令列ではなく、型・identity・authority・Lease・
conservation/accounting・model/profile contractを満たしたsemantic intentを表し、MKI / control-plane
境界を通じて観測、参照取得、輸送、状態変化、継続作用を要求する。

```text
magic program
    requests typed / authorized semantic effects

magic program
    != raw write access to world internals
```

### Physical-law boundary

通常の魔法は、物理法則・保存則・identity semantics・causal/history semantics・authority modelを
術式そのものから定義、置換、停止、または暗黙上書きしてはならない。

world effectは、Specification / Registry / World / Profileが所有するadmitted model / contractの下で
実行されるMUST。術式は必要なmodelを参照・選択・parameterizeできるが、通常のMKI effectとして
任意の新しい governing law を注入してはならない。

```text
reference/select admitted model != define governing law
counteract natural evolution != delete natural law
```

例えば重力下で対象を水平軌道へ維持する術式は、重力modelを消去するのではなく、必要な観測、
controller、力・運動量・Energyその他のadmitted effectを追加し、そのcost / accounting / timing /
authorityを通常境界で処理する。

```text
maintain horizontal trajectory under gravity
!= set gravity = 0
```

将来、world法則そのものの変更を扱う場合、それはcurrent ordinary MKI / ECIR相当のeffectから
暗黙に得られる能力ではない。別個の明示的な高権限contract、authority model、causality/accounting
境界を要求するMUSTであり、`RECONFIGURE` / `CONSTRAIN` 等を法則書換えとして解釈してはならない。

### World Kernel boundary

`World Kernel` は、validated / revalidatedなsemantic effect requestとauthoritative world evolutionの
間に置く**特権的semantic execution boundaryの仕様上の抽象概念**である。

```text
magic semantics
→ MKI / lower semantic execution boundary
→ World Kernel
→ authoritative world evolution
```

World Kernelは第六の`DefinitionSource`ではなく、世界がbinary computerであること、softwareとして
実装されていること、または特定solver/scheduler algorithmを物理法則として採用することを意味しない。
既存のDefinitionSource ownershipを用いて、admitted effectが現在のworld / model / authority / safety
contractの下で実行可能かを最終的に仲介する境界として扱う。

World Kernel境界では少なくとも次を維持するMUST。

1. 術式からraw `SET` / `WRITE` / `CREATE` / `DELETE`相当のunvalidated world mutationを許可しない。
2. Capability / Lease / sandbox / conservation / identity / current-state guardを下位化によって回避しない。
3. scheduler tick、integrator substep、replay bookkeeping等のruntime mechanismをworld lawへ昇格しない。
4. world自身の自然発展は魔法の存在と独立に定義可能であり、魔法はその全法則を所有しない。
5. 魔法による継続作用はadmitted active effectとして世界発展へ参加できるが、そのeffect modelの意味は
   implementation bookkeepingだけから生成しない。

```text
World Kernel != new authority source
World Kernel != new DefinitionSource
World Kernel != proof of binary ontology
world evolution != scheduler implementation detail
```

この原理はworldbuilding上の「宇宙が実際に計算機である」「神がkernelを実装した」等を主張しない。
仕様が固定するのは、**魔法側から見たsemantic / authority / execution boundary**である。

## 1. Normative guarantees

適合実装は、実装しているfeatureについて次を満たすMUST。

1. **Layer separation**
   - surface analysis、NSR、SemanticAST、TypedMIR、KernelPlan、runtime effectを同一視しない。
   - AI、辞書、parser、WorldIndexの出力を検証なしにsemantic truthまたはauthorityへ昇格しない。
2. **Typed and dimensioned semantics**
   - 型、意味型、SI dimension、payload contractの不一致を物理作用前に拒否する。
   - dimension equalityだけをsemantic type equalityとして扱わない。
3. **Authority and identity**
   - `Ref`、Identity、Visibility、Capability、Leaseを分離する。
   - registry metadata、resolver candidate、推定値はauthorityを付与しない。
4. **Accounting and mandatory safety**
   - 適用されるconservation/accounting、security sandbox、emergency-stop contractを回避しない。
   - mandatory contractを証明できない場合はfail closedまたは明示的`Indeterminate`とする。
5. **Uncertainty and provenance**
   - `Unknown`、estimate、measurement uncertainty、provenanceを捏造した確定値へ縮約しない。
   - profile/registry/world/implementationから採用した判断は、そのownerとrevision/evidenceを
     contractが要求する範囲で記録する。
6. **Compatibility**
   - 共通decision envelopeを用いても、domain固有のcompatibility relationを単一hash比較や
     単一boolean algorithmへ統合しない。
7. **World effects**
   - world effectは既存6 MKI data-plane primitivesとcontrol-plane境界を通す。
   - dry-run evaluation、report生成、candidate選択だけではworldを変更しない。
   - ordinary magic effectをphysical/model law definitionまたはlaw mutationとして解釈しない。
   - world effectの下位化はWorld Kernel boundaryでmandatory authority/accounting/model guardを維持する。

仕様がcontractを定義していても、必要なworld data、registry entry、resource、Capability、
modelまたはimplementationが存在するとは限らない。したがって適合性は個別術式の実行可能性を
保証しない。

## 2. Project terms and ownership

次の表は、このrepositoryで日本語project用語をどう読むかを示す。worldbuilding上の完全な
存在論を定義する表ではない。

| 用語 | この仕様での扱い | 正規contract / owner |
|---|---|---|
| 魔法 | 物理世界に対するtyped/authorized information-control computationの総称。semantic effectを要求するが、通常の術式はworld lawそのものを定義・書換えしない。単一のMIR型、MKI primitive、resourceではない。 | 本書のCore design principle + 個別language/runtime reference。起源・形而上学的存在論は仕様外。 |
| 術式 | parse/normalize/compile/evaluateされるprogram unitの総称。MIRではtop-level `spell` declarationが最も近い形式だが、surface source、CompiledSpell、runtime `SpellInstance`とは同一ではない。 | `grammar/mir.ebnf`, `mir-name-resolution.md`, `semantics.md`, registry contract。 |
| 詠唱 | spokenまたはnatural-language surface inputを表すinformativeな入力形態。意味は`LanguageAdapter<L>`を通過して初めて候補化され、詠唱自体はauthorityではない。 | adapter/profile-defined surface behavior。共通出口はNSR contract。 |
| 魔法陣 | graphical/external representationまたは入力媒体を指しうるworld/tooling用語。current coreには対応する構文・型・primitiveを定義しない。実行可能dataとして扱う場合は通常のvalidationとspell-injection境界に従う。 | representation adapter/toolingまたはworld-defined。core semanticsは未定義。 |
| 魔力 | resourceを指しうるworldbuilding用語。current coreでは`Energy`、Capability、authority、resource reservationの同義語ではなく、組込みquantityでもない。 | 採用するworld/profile/registryがidentity・dimension・accounting contractを定義する。 |
| 魔子 | particle/entity/species/modelを指しうるworldbuilding用語。current coreは存在、物理性質、保存則、SpeciesIDを仮定しない。 | 採用するworld/registry/profileが定義する。本仕様には組込みtypeなし。 |
| World Kernel | validated semantic effect requestとauthoritative world evolutionを仲介する特権的semantic boundaryの抽象概念。software/binary machine/DefinitionSourceを意味しない。 | 本書 + `architecture.md` / `mki.md`。具体実装mechanismはImplementation/Profile/World-owned。 |

```text
surface term != semantic type
魔力 != Energy != Capability
魔子 != built-in SpeciesID
詠唱 != semantic authority
魔法陣 != executable permission
World Kernel != DefinitionSource
```

## 3. DefinitionSource

値またはpolicyが本仕様だけで一意に決まらない場合、適合artifact/reportは可能な範囲で
`DefinitionSource`を明示するSHOULD。

```text
DefinitionSource =
    Specification
  | Implementation
  | Registry
  | World
  | Profile
```

| Source | 所有するもの | 適合条件 |
|---|---|---|
| `Specification` | syntax、layer、type/effect boundary、MKI primitive set、mandatory invariant、World Kernel semantic boundary | 実装は変更できない。変更は仕様改訂として扱う。 |
| `Implementation` | parser/solver/database layout、query plan、OS isolation mechanism等 | 選択内容と適用範囲を文書化するMUST。semantic contractを変更しない。 |
| `Registry` | Species/Reaction/Observer/semantic kind等のtrusted revisioned entry | registry identity/revision/evidenceを保持し、metadataをCapabilityとみなさない。 |
| `World` | authoritative state、entity existence/property、current availability、physical/model context | WorldIndex candidateではなく必要に応じauthoritative revalidationを行う。 |
| `Profile` | tolerance、ordering、accepted revision relation、adapter/runtime policy等 | profile identity/revisionとdomain ownerを記録する。mandatory safetyを弱めない。 |

`World Kernel`は上記Sourceから得た定義・状態・policyを仲介するexecution boundaryであり、
DefinitionSource列挙へ追加しない。

`unspecified`は第六の`DefinitionSource`ではない。複数の適合挙動を仕様が意図的に許す分類であり、
required identity、authority、conservation、compatibilityまたはworld factを埋める既定値として
用いてはならない。現在のmandatory execution contractに、暗黙の`unspecified` choiceはない。

```text
specified != implementation-defined != unspecified
Unknown value != unspecified specification choice
profile-defined != implementation whim
registry-defined != Capability
world-defined != WorldIndex guess
```

## 4. Current ownership inventory

| Choice / artifact | Classification | Authoritative reference | Notes |
|---|---|---|---|
| MIR grammar、name scope、layer boundary | Specification | `grammar/mir.ebnf`, `mir-name-resolution.md`, `architecture.md` | parser algorithmはImplementation。 |
| MKI primitive set、PREPARE/COMMIT | Specification | `mki.md`, `semantics.md` | data-plane primitiveは6個。 |
| magic / physical-law boundary、World Kernel semantic boundary | Specification | `scope-and-ownership.md`, `architecture.md`, `mki.md` | ordinary magic effectはlaw definition/mutationではない。World KernelはDefinitionSourceではない。 |
| semantic kinds、species、reaction、observer model | Registry | `registry.md`, domain references | entry revisionとprovenanceが必要。 |
| current entity/state/property、availability | World | `world-index.md`, `semantics.md` | Index recordはauthoritative entity/stateではない。 |
| scheduler/integrator/replay/tolerance policy | Profile | `runtime-time.md`, RuntimeProfile schema | numerical algorithmの実装はImplementation。 |
| compatibility relation、accepted revision、migration | Profile (domain-owned) | `compatibility.md` | shared metadata/envelopeは共通でもrelationはdomain-owned。 |
| ambiguity ordering / permissive selection | Profile | `language-adapters.md` | decision traceとordering revisionを記録する。 |
| parser/model/provider/database/OS isolation mechanism | Implementation | owning referenceのimplementation-defined section | provenance/documentationを要求しうる。 |
| physical/model coefficients | Registry / World / Profile / Implementation | `estimator-models.md`, `feasibility.md` | model/coefficient identity、revision、availability、evidenceを記録し、synthetic値をworld constantとみなさない。 |
| Unknown inference、PlanningAssumption、generation lowering、terminal binding | Specification + Profile-owned policy | `planning-inference.md` | source semanticsを変更せず、criticality/binding/provenanceを保持する。 |
| canonical water-ball conformance path | Specification + synthetic fixture profile | `canonical-water-ball.md` | normative boundaryとsynthetic dataを区別する。 |
| generic artifact canonical bytes / digest algorithm | Deferred design | `machine-values.md`, `compatibility.md` | `SemanticFingerprintV1`とは別。暗黙選択しない。 |

## 5. Open implementation and deferred choices

| Work | Owner | Blocking status |
|---|---|---|
| minimal Local Evaluator implementation | pre-public archive Issue #36 / [`planning/v1.0-roadmap.md`](../planning/v1.0-roadmap.md) | DONE。v0.8 contractを実装し、COMMIT/world mutationを行わない。 |
| sandbox execution/runtime | pre-public archive Issue #37 | DONE。v0.9.0 reference subset。 |
| MKI → lower semantic execution layer → World Kernel detailed boundary | pre-public archive Issue #55 / pre-public archive Issue #40 | **P0 / v1.0 blocker**。本書のcore principle / law boundaryを維持したままactive-effect state、lowering、Runtime-1.0 conformance ownerを確定する。 |
| generic artifact canonical bytes / digest algorithm | owning future profile/design issue | 明示的deferred。v1.0 blockerへpromotionされない限りoptional。 |

この表の未完事項を、implementation default、world guess、AI proposalまたはinformative exampleで
黙って確定してはならない。

## 6. Document authority and navigation

- `reference/`はcurrent live specification。
- `spec/`はhistorical release snapshotであり、current workを遡及反映しない。
- `terminology.md`は索引であり、formal definitionは各owning referenceに置く。
- `TODO.md`は作業計画とdependency stateの正本であり、semantic definitionの正本ではない。
- example、rationale、consistency report、PR/Issue本文はnormative ownerを置き換えない。

主要referenceは`Status`、`Purpose`、`Non-goals`、`Depends on`、`Key invariants`を明示するSHOULD。
重複する規範文を新設する代わりに、owning referenceへlinkする。
