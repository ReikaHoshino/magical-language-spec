# Observer Model Reference — v0.6

**Status:** normative observer-conversion contract; individual response curves and datasets are registry/profile-defined.

## Purpose

radiometric measurementとphotometric quantityの変換を、observer identity・revision・
domainを持つ明示的modelとして定義する。

## Non-goals

- radiometric quantityをphotometric quantityへ単純castしない。
- ObserverModelをAgent identityまたはauthorityとして扱わない。
- human-specific response curveを唯一の組込みworld truthとして固定しない。

## Depends on

- `scope-and-ownership.md`
- `quantities.md`
- `registry.md`
- `semantics.md`

## Key invariants

```text
radiometric quantity != photometric quantity
ObserverModel != Ref<Agent>
observation != pure observer-model conversion
registry model metadata != authority
```

## 1. Purpose

radiometric quantityとphotometric quantityを単純castせず、観測者依存変換として扱う。

```text
radiometric measurement
+ spectral information
+ observer model
-> photometric measurement
```

## 2. Spectral types

```text
Spectrum<Q, Axis>
SpectralMeasurement<Q, Axis>
```

代表Axis:

```text
Wavelength
Frequency
```

`SpectralMeasurement` は通常のMeasurement同様、観測時刻・不確かさ・revision等を持ちうる。

## 3. ObserverModel

```text
ObserverModel<In, Out> {
    id
    domain
    response
    normalization
    revision
}
```

- `In`: 入力radiometric quantity family
- `Out`: 出力photometric quantity family
- `domain`: responseが定義される波長/周波数域
- `response`: spectral weighting function
- `normalization`: 出力スケールの定義

## 4. Conversion

高級純粋関数:

```text
photometric(
    spectral : SpectralMeasurement<RadiantFlux, Wavelength>,
    observer : ObserverModel<RadiantFlux, LuminousFlux>
) -> Measurement<LuminousFlux>
```

一般形:

```text
convert_observer<In, Out>(
    spectral : SpectralMeasurement<In, Axis>,
    observer : ObserverModel<In, Out>
) -> Measurement<Out>
```

既取得データに対する変換はpure。

## 5. Observation vs computation

```text
let S = observe lamp.spectral_radiance @ resolution;
let L = photometric(S, human_photopic_model);
```

最初のOBSERVEはworld effectを持つ。

二番目は純粋計算。

これにより「光を測る」ことと「人間にはどの程度明るく見えるかを評価する」ことを分離する。

## 6. Observer identity

ObserverModelはAgentそのものではない。

```text
ObserverModel != Ref<Agent>
```

あるAgentの視覚特性をOBSERVEしてmodelを構築することは可能だが、そのmodelは測定/計算用情報であり人格同一性を持たない。

## 7. Species and individual models

世界設定上、異種族や個人差のある視覚系を扱える。

```text
human_photopic
human_scotopic
species_X_visual
individual_observer_17
```

同じradiometric fieldでもObserverModelが違えばphotometric/subjective proxy値は異なりうる。

## 8. Type safety

ObserverModelの入出力型が合わなければ:

```text
ObserverModelTypeError
```

スペクトルresolution/domainが不十分なら:

```text
SpectralObservationFailure
```

または明示的な不確かさ拡大を伴うResultとして扱う。

## 9. No implicit cast

次は禁止。

```text
let x : LuminousFlux = radiant_flux;
```

必要なのはobserver modelを明示した変換である。

## 10. Scope

v0.6ではobserver model APIの型構造だけを定義する。

具体的な標準視感度曲線、歴史的/種族別モデル値、数値積分アルゴリズムはライブラリまたは将来仕様に委ねる。

`EvidenceFusionModel`は複数の既取得Measurementから仮説を評価する別contractであり、単一観測の
response/normalizationを所有する通常のObserverModelと相互代用しない。experimental ownerは
`evidence-inference.md`、machine-readable contractは
`semantic-registry-contracts.schema.json#/$defs/EvidenceFusionModelEntryContract`とする。
