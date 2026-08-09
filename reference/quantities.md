# Quantity and Dimension Reference — v0.6.1

**Status:** normative quantity/dimension contract; display conventions and concrete model coefficients are informative or profile-owned.

## Purpose

semantic quantity kind、SI dimension、measurement、uncertainty、unit presentationの境界を定義する。

## Non-goals

- dimension equalityだけでsemantic type equalityを決めない。
- display unitをinternal canonical quantity representationと同一視しない。
- world/model coefficientを暗黙の実装defaultとして固定しない。

## Depends on

- `scope-and-ownership.md`
- `conventions.md`
- `types.md`
- `machine-values.md`

## Key invariants

```text
Dimension equality != Semantic type equality
measurement != authoritative world state
display unit != internal canonical unit
Unknown != zero
```

## 1. 意味型と次元

物理量は意味型 `Q` とSI次元 `D` を分離する。

```text
Quantity<Q,D>
```

SI次元基底順序:

```text
(kg, m, s, A, K, mol, cd)
```

同じ `D` を持つ意味型でも自動的には互換にしない。

## 2. Traits

```text
Observable
Transferable
Conserved
ScalarPayload
CompositePayload
VectorQuantity
```

### Transferable

```text
K : Transferable
```

MKIが `Channel<K>` と `PayloadOf<K>` による輸送を実装できる処理系能力trait。

### Conserved

```text
Q : Conserved
```

閉じた系で保存ledger対象となる物理的性質。

`Transferable` と `Conserved` は直交する。

## 3. Scalar conserved transfer

```text
K : Transferable & Conserved & ScalarPayload
PayloadOf<K> = Quantity<K>
```

典型例:

| 意味型/Kind | 次元 | Transferable | Conserved | Payload |
|---|---|---:|---:|---|
| `Energy` | `kg m^2 s^-2` | yes | yes | `Quantity<Energy>` |
| `Momentum` | `kg m s^-1` | yes | yes | `Quantity<Momentum>` |
| `Charge` | `A s` | yes | yes | `Quantity<Charge>` |
| `Temperature` | `K` | no | no | — |
| `LuminousIntensity` | `cd` | no | no | — |
| `Matter` | — | yes | scalar traitなし | `MatterPayload` |

## 4. AmountOfSubstance and SpeciesAmount

```text
AmountOfSubstance : mol
SpeciesAmount = Quantity<AmountOfSubstance>
```

v0.6.1ではMatterPayload全体へ単一 `amount` を置かず、Compositionの各Species entryへSpeciesAmountを持たせる。

```text
Composition {
    entries : Map<SpeciesID, SpeciesAmount>
}
```

従って:

```text
AmountOfSubstance != Matter itself
```

である。

混合物の総mol数を計算することはできるが、それはCompositionから導出される集約値であり、MatterPayloadの普遍的な主キーではない。

## 5. Species accounting

SpeciesIDは意味上の化学種識別子であり、普遍的保存量ではない。

化学反応では:

```text
Δn_i = ν_i ξ
```

に従ってSpeciesAmountが変化しうる。

Chemical domainでは必要に応じて:

```text
Element inventory
Nuclide inventory
Charge
Energy
Momentum
```

等のledgerを検査する。

```text
Species identity != conserved quantity
```

## 6. ConservationProfile

transfer kindごとに、輸送で追跡すべき保存ledgerをregistryが定義する。

```text
ConservationProfile<K>
```

例:

```text
Energy   -> [Energy]
Momentum -> [Momentum, Energy]
Charge   -> [Charge, Energy]
Matter   -> [Energy, Momentum, Charge]
```

payload型と保存profileは別概念。

```text
Payload type != ConservationProfile
```

ReactionではReactionDomain固有のprofileを追加する。

## 7. Mass

```text
Mass : kg
```

Massは有用な観測量・工学量だが、v0.6.1でも世界全体の普遍的な独立保存ledgerとは断定しない。

反応会計ではEnergyとの関係を含むworld/kernel physics contractに従う。

## 8. Dimensionless quantities

無次元は `1`。

```text
Angle      : 1
SolidAngle : 1
```

同じ次元 `1` でも意味型は保持する。

## 9. Radiometric quantities

| 意味型 | SI基本単位積 | 注記 |
|---|---|---|
| `RadiantEnergy` | `kg m^2 s^-2` | Energyの放射文脈 |
| `RadiantFlux` | `kg m^2 s^-3` | 単位時間あたりRadiantEnergy |
| `RadiantIntensity` | `kg m^2 s^-3` | solid angleあたり |
| `Irradiance` | `kg s^-3` | 面積あたりRadiantFlux |
| `Radiance` | `kg s^-3` | 面積・solid angleあたり |

同次元でも意味型は別。

## 10. Photometric quantities

| 意味型 | SI基本単位積 | 慣用単位 |
|---|---|---|
| `LuminousIntensity` | `cd` | cd |
| `LuminousFlux` | `cd` | lm = cd sr |
| `Illuminance` | `cd m^-2` | lx |
| `Luminance` | `cd m^-2` | cd m^-2 |

observer modelを含むためradiometric quantityから暗黙castしない。

## 11. Heat

`Heat` を保存量型として登録しない。

```text
Transfer<Energy, mode=Thermal>
```

へ精緻化する。

## 12. Matter

```text
PayloadOf<Matter> = MatterPayload
```

Matterは単一scalar Quantityとして扱わない。

Composition、Momentum、InternalEnergy、Charge、ThermodynamicState、Structureを組み合わせて記述する。

詳細は [`matter.md`](matter.md) と [`payloads.md`](payloads.md)。

## 13. Registry

dimension、traits、payload、ConservationProfile、Species/Reaction contract等は `SemanticRegistry` で管理する。

```text
Registry metadata != Capability
```

## 14. Machine-readable scalar quantity

portable JSON表現は [`machine-values.md`](machine-values.md) と
`schemas/common-values.schema.json` を正本とする。

```text
semantic quantity type != SI dimension
quantity encoding != physical law
```

semantic type、7つのSI base exponent、value、unitを別fieldで保持する。同じdimensionを
持つ別semantic typeを暗黙castしない。Measurement uncertainty、Estimate、exact rational、
composite payloadはこのscalar shapeへ黙って縮約せず、owning domain contractを使う。
