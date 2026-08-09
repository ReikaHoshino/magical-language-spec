# Transfer Payload Reference — v0.6.1

**Status:** normative payload/transfer contract; concrete registry mappings and examples are informative.

## Purpose

MKI transfer kindと`PayloadOf<K>`、composite payload、measurement/state payloadの境界を定義する。

## Non-goals

- `Quantity<K>`を一般に`PayloadOf<K>`と同一視しない。
- payload dataをEntity identityまたはauthorityとして扱わない。

## Depends on

- `scope-and-ownership.md`
- `quantities.md`
- `matter.md`
- `mki.md`
- `registry.md`

## Key invariants

```text
PayloadOf<K> != Quantity<K> in general
payload != Entity identity
TRANSFER accounting includes coupled conserved quantities
```

## 1. General transfer signature

TRANSFERはscalar quantity専用ではない。

```text
Channel<K> × PayloadOf<K>
    -> TransferHandle<K>
```

`K` はtransfer kind、`PayloadOf<K>` はregistryで定義されるassociated payload type。

## 2. Scalar payloads

```text
PayloadOf<Energy>   = Quantity<Energy>
PayloadOf<Momentum> = Quantity<Momentum>
PayloadOf<Charge>   = Quantity<Charge>
```

従って従来の:

```text
transfer energy_ch, 1000 kg m^2 s^-2;
```

は引き続き合法。

## 3. Composite payloads

Matterのように単一の意味型+scalar値では十分でないtransfer kindにはcomposite payloadを使う。

```text
PayloadOf<Matter> = MatterPayload
```

v0.6.1の現行形:

```text
MatterPayload {
    composition          : Composition
    momentum             : Quantity<Momentum>
    internal_energy      : Quantity<Energy>
    net_charge           : Quantity<Charge>
    thermodynamic_state  : ThermodynamicState
    structure            : StructureDescriptor?
}
```

v0.6の `amount` フィールドは廃止する。混合物全体へ一つのmol値を置かず、各Species量をComposition側で管理する。

## 4. Composition

```text
Composition {
    entries : Map<SpeciesID, SpeciesAmount>
}

SpeciesAmount = Quantity<AmountOfSubstance>
```

例:

```text
Composition {
    H2O : 55.5 mol
    Na+ : 0.10 mol
    Cl- : 0.10 mol
}
```

species inventoryは記述情報であり、常に保存される基本量ではない。

```text
Species identity != conserved quantity
```

## 5. Actual state vs observed composition

カーネル実状態:

```text
Composition
```

術式の観測値:

```text
Measurement<CompositionEstimate>
```

`CompositionEstimate` は未同定成分、不確かさ、分解能等を持ちうるため、完全性証明なしにCompositionへ暗黙変換しない。

## 6. Momentum / internal energy / charge

### momentum

payload物質系全体の重心運動量。

### internal_energy

payload内部自由度に保持されるEnergy。Temperatureそのものではない。

### net_charge

payload全体の総電荷。

これらはMatterPayloadの一部であると同時に、ConservationProfile<Matter>のledgerと整合しなければならない。

## 7. ThermodynamicState

```text
ThermodynamicState<M> {
    model_id
    variables
}
```

温度・圧力・相等を型付き状態モデルとして保持する。

```text
Temperature != InternalEnergy
Phase != Composition
```

## 8. StructureDescriptor

```text
StructureDescriptor<S : StructureSchema> {
    schema_id
    schema_revision
    data : S
}
```

例:

```text
MolecularTopology
CrystalLattice
Microstructure
TissueArchitecture
```

CompositionとStructureは別概念。

```text
same Composition != same Structure
```

Matter channelが対応schemaを保持できる場合のみ、structureをそのまま輸送できる。

## 9. Coupled accounting

Matter TRANSFERは物質だけを魔法的に抜き出してEnergy/Momentum/Chargeを無視してはならない。

```text
ConservationProfile<Matter> = [
    Energy,
    Momentum,
    Charge
]
```

追加の局所条件は `invariant` で要求できる。

```text
transfer matter_ch, payload,
    invariant = [ChemicalSpecies];
```

これはそのTRANSFER中に化学反応を許さないという局所条件であり、ChemicalSpeciesが世界全体で普遍的に保存されるという意味ではない。

## 10. Matter and RECONFIGURE

Matter輸送と化学/構造変更は別操作。

```text
TRANSFER<Matter>
```

はpayloadを端点間で輸送する。

```text
RECONFIGURE
```

は存在するMatterの組成・構造・状態を変更する。

反応は高級ReactionRuleからRECONFIGUREへ展開する。

## 11. Reaction-aware reconfiguration

例:

```text
reconfigure target {
    reaction = @rule;
    extent = 2 mol;
    identity = preserve;
}
```

compiler/runtimeはReactionRule、Stoichiometry、required state、authority、ConservationProfileを検証し、必要なEnergy/Momentum等のTRANSFERを別途要求する。

## 12. Identity during Matter transfer

MatterPayloadはEntity identityそのものではない。

```text
Payload != Ref<Entity>
```

Entity全体の連続的輸送を表現する高級処理では、IdentityPolicyとTRANSFER中のcontinuity proofを別途要求しうる。

人体と同じComposition/Structureを輸送・再構成してもAgent identityの輸送を意味しない。

## 13. Transit

非同期輸送中は:

```text
Transit<K, PayloadOf<K>>
```

としてChannel/runtime Ωが保持する。

Matterの場合もpayloadがsourceから離れてdestinationへ届くまで、ConservationProfileのledgerから消失してはならない。

## 14. Errors

```text
PayloadTypeError
UnsupportedTransferKind
AccountingProfileError
UnknownSpeciesError
StructureSchemaMismatch
InsufficientMaterial
ConservationProofFailure
```

詳細は [`matter.md`](matter.md) と [`errors.md`](errors.md)。
