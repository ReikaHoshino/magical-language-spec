# 魔術ラテン語例文データ — v0.5.2

**Status:** informative adapter examples; canonical labels identify project test inputs, not a privileged core language.

## Purpose

`LanguageAdapter<lat>`のsurface/morphology/frame/normalization例を索引化する。

## Non-goals

- Latin surfaceをlanguage-independent semanticsまたはMIR syntaxとして扱わない。
- provisional fragmentを完全な術式contractとして扱わない。

## Depends on

- `scope-and-ownership.md`
- `latin-frontend.md`
- `language-adapters.md`

## Key invariants

```text
Magical Latin = LanguageAdapter<lat>
Latin surface != NSR
example fragment != complete spell contract
```

例文の正本データは [`data/latin-examples.csv`](../data/latin-examples.csv) に置く。

Markdown本文に例文を増殖させず、CSVを2次元データとして管理し、ラテン語校訂・AST対応・検索・自動生成に備える。

## 1. スキーマ

| 列 | 内容 |
|---|---|
| `id` | 永続的な例文ID。表層形を校訂しても意味構造が同じなら原則維持。 |
| `latin` | ラテン語表層形。 |
| `japanese` | 日本語訳。 |
| `feature` | 説明対象となる言語/魔術機能。 |
| `primary_mapping` | 主たるAST/MIR/MKI対応。 |
| `register` | 時代・語体・技術語としての位置づけ。 |
| `status` | `canonical`, `provisional`, `deprecated`, `fragment`。 |
| `key_morphology` | 主要語形・格・法など。セミコロン区切り。 |
| `notes` | 技術的・文献的・仕様上の注記。 |

## 2. status

### canonical

現行の魔術言語資料で標準例として使える形。

昇格条件:

- 意味構造/MIR mappingが現行仕様と一致する。
- 格・前置詞・動詞frameが厳格frontendとして十分明示的。
- register上の位置づけを説明できる。
- 既知の重大な語形上の問題がない。

### provisional

意味構造は有効だが、語彙・語順・時代適合性を今後校訂する可能性がある形。

### deprecated

過去の議論に登場したため記録は残すが、新規資料では使用しない形。`notes` に代替例または理由を示す。

### fragment

`Semel, cum ...` のように完全な術式ではなく、構文機能だけを示した断片。

## 3. register controlled vocabulary

`register` は自由記述を許すが、以下の語を優先する。

```text
Classical Latin
post-classical Latin
scholastic Latin
17th-century technical Latin
Neo-Latin technical
Neo-Latin scientific
Magical Latin technical
fragment
```

複合指定は `17th-century-flavoured technical Latin` のように注記してよいが、古典語彙でない語を無理に `Classical Latin` と分類しない。

## 4. 校訂規則

1. 新しい意味例には新しい `LAT-xxx` IDを付ける。
2. 誤字・活用・語順など表層校訂のみで意味構造/MIR mappingが同じならIDを維持できる。
3. 意味構造やprimary mappingが変わる場合は新IDを発行し、旧行を `deprecated` にする。
4. 自然ラテン語として可能でも厳格魔術ラテン語で曖昧性が高い語順は `provisional` とする。
5. Neo-Latin/科学ラテン語を許容し、時代的位置づけを `register`/`notes` へ記録する。
6. 古典的真正性、17世紀らしさ、魔術frontendとしての安全性は別評価軸とする。
7. 現行仕様の意味解析では「格だけ」でroleを決めず、前置詞・verb frame・contextを併用する。

## 5. 意味と表層の分離

例えば:

```text
Calorem ab aqua ad aerem transfer.
```

は表層に `calor` を用いるが、MIR上の保存量型 `Heat` を意味しない。

```text
Transfer<Energy, mode=Thermal>
```

へ精緻化する。

したがってラテン語語彙の校訂は、意味mappingを自動的に変更しない。

## 6. 現在の代表例

- `LAT-001`: `Calorem ab aqua ad aerem transfer.` — Thermal Energy transfer
- `LAT-003`: `Quantitatem motus a terra ad lapidem transfer.` — Momentum transfer
- `LAT-006`: `Globus intra circulum maneat.` — persistent CONSTRAIN
- `LAT-026`: `Hunc lapidem designa. Eundem postea feri.` — early-bound Ref reuse
- `LAT-031`: `Cum hostis limen transeat, globum emitte.` — event trigger

## 7. 役割分担

- frontend意味規則: [`latin-frontend.md`](latin-frontend.md)
- 例文データ正本: [`../data/latin-examples.csv`](../data/latin-examples.csv)
- 本ファイル: データschema/status/editorial policy

今後、文献的な出典を本格管理する場合は、CSVへ `source`, `attestation`, `supersedes` 等の列を追加できる。既存IDは維持する。
