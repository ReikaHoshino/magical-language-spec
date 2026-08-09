# Specification Conventions — v0.6.3

**Status:** normative

## Purpose

本書は現行仕様全体で使う規範語彙、定義責任、fail policy、注釈規約を定める。

## Non-goals

- 物理法則そのものを定義しない。
- SemanticRegistryの具体データを定義しない。
- runtime tickやWorld Indexの具体実装を定義しない。

## Depends on

- `architecture.md`
- `terminology.md`

## Key invariants

```text
specified != implementation-defined
implementation-defined != unspecified
registry-defined != Capability
world-defined != runtime whim
undefined world effect -> fail closed
```

## 1. Normative keywords

| Keyword | 意味 |
|---|---|
| `MUST` | 必須。違反は非適合。 |
| `MUST NOT` | 禁止。 |
| `SHOULD` | 強い推奨。逸脱理由を文書化する。 |
| `SHOULD NOT` | 強い非推奨。採用理由を文書化する。 |
| `MAY` | 任意。 |

大文字でない日常語の「must」「should」等は規範語として扱わない。

## 2. Definition ownership

仕様全体の保証範囲、project用語のownership、current choice inventoryは
[`scope-and-ownership.md`](scope-and-ownership.md)を正本とする。本節は共通語彙を定義する。

| 用語 | 定義責任 |
|---|---|
| `specified` | 本仕様で固定。 |
| `implementation-defined` | 実装が選ぶ。選択内容を文書化するMUST。 |
| `registry-defined` | trusted registryが定義。 |
| `world-defined` | World State / world model contractが定義。 |
| `profile-defined` | Reaction/Conservation等のprofileが定義。 |
| `unspecified` | 複数の適合挙動が許される。文書化義務なし。 |
| `undefined` | 本仕様は意味を与えない。物理作用に到達する前に拒否するSHOULD。安全性に関わる場合MUST fail closed。 |

### 2.1 Example

`CHANNEL` の距離二乗コストという形はspecifiedだが、係数 `α_K`, `β_K` はworld-definedまたはregistry-definedとできる。

```text
E_open = α_K σ d^2
P_maint = β_K σ d^2
```

実装が係数を勝手に暗黙選択してよいという意味ではない。

## 3. Normative / informative sections

文書は必要に応じて以下を使う。

- `[NORMATIVE]`: 適合性に影響する規則。
- `[INFORMATIVE]`: 解説、例、直観。
- `[RATIONALE]`: なぜその設計にしたか。
- `[COMPATIBILITY]`: 旧版/他実装との互換性。

ラベルがない節でも、`MUST` 等の規範語があればその文はnormativeである。

## 4. Error and fail policy

### MUST fail closed

以下は原則として物理実行前に拒否する。

- 型不一致。
- SI次元不一致。
- `PayloadOf<K>` 契約不一致。
- authority不足。
- 必要Leaseを取得できない。
- registry contract互換性を証明できない。
- 必須conservation/accounting obligationを証明できない。
- IdentityPolicyを満たす必要があるのに証明できない。

### MUST preserve uncertainty

`Measurement` の不確かさや `Truth::Indeterminate` を、明示policyなしに確定値へ縮約してはならない。

### Estimation

Energy、所要時間、rate等が不確かな場合、evaluatorは一意な値を捏造してはならない。

推奨表現:

```text
Exact(value)
Range(min,max)
LowerBound(value)
UpperBound(value)
Distribution(model)
Unknown(reason)
```

## 5. Tolerance vocabulary

### tolerance

結果・制御・同期等で許容する誤差範囲。

### resolution

観測/表現が区別可能な細かさ。

### uncertainty

真値に対する知識の不確かさ。

### numerical error

離散化・丸め・近似・積分法に由来する計算誤差。

```text
tolerance != resolution != uncertainty != numerical error
```

## 6. Compatibility vocabulary

```text
SourceCompatible
SemanticCompatible
RegistryCompatible
RuntimeCompatible
ReplayCompatible
```

sourceがparseできるだけではsemantic compatibleとは限らない。

例: `ReactionRule` の同じIDが別stoichiometryを指すregistryは、名前が一致してもRegistryCompatibleではない。

共通decision envelope、三値結果、domain ownershipの正本は
[`compatibility.md`](compatibility.md) とする。上記語彙はdomain別の関係名であり、
一つの共通algorithmやhash equalityを意味しない。

## 7. Documentation header template

主要reference文書は段階的に以下を冒頭へ持つSHOULD。

```markdown
**Status:** normative | informative | mixed

## Purpose
...

## Non-goals
...

## Depends on
- ...

## Key invariants
```text
...
```
```

## 8. Snapshot policy

- `spec/`: 過去版のsnapshot。原則immutable。
- `reference/`: 現行版のlive reference。
- `CHANGELOG.md`: 版間差分。
- `reference/consistency-report.md`: その版で行った横断整合性チェック。
- `TODO.md`: 未確定/未実装事項。

旧snapshotに現在の規則を後付けしてはならない。

## 9. Definition-source annotation

値・policyが本仕様で一意に決まらない場合、可能なら出所を明示する。

```text
DefinitionSource =
    Specification
  | Implementation
  | Registry
  | World
  | Profile
```

Feasibility report等は、判断に使った値と `DefinitionSource` を同時に返すSHOULD。

## 10. Review checklist

release前の整合性チェックでは最低限:

1. 新しい型/術語が `terminology.md` にあるか。
2. 新しいsyntaxがEBNFと意味論の双方にあるか。
3. 新しいerrorが `errors.md` にあるか。
4. registry-defined/world-defined/implementation-definedの責任が曖昧でないか。
5. PREPAREとruntime failureの境界が明示されているか。
6. MKI primitiveが意図せず増えていないか。
7. historical snapshotを書き換えていないか。
