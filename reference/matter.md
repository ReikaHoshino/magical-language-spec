# Matter / Chemistry Reference — v0.6.1

**Status:** normative matter/composition/accounting contract; examples and model guidance are informative.

## Purpose

`MatterPayload`、Composition、Species、Structure、ThermodynamicState、ReactionRuleの
language/runtime contractを定義する。

## Non-goals

- 具体Species inventory、material database、reaction datasetを本書へ埋め込まない。
- `MaterialClassID`を普遍的保存ledgerとして扱わない。
- 物質変換のために新しいMKI primitiveを追加しない。

## Depends on

- `scope-and-ownership.md`
- `payloads.md`
- `quantities.md`
- `registry.md`
- `mki.md`

## Key invariants

```text
MatterPayload != Ref<Entity>
Composition != CompositionEstimate
MaterialClassID != conservation ledger
Matter transport = TRANSFER
Matter transformation = RECONFIGURE
```

## 1. Scope

本資料は `MatterPayload`、Composition、Species、Structure、ThermodynamicState、ReactionRuleの現行定義をまとめる。

MKI primitiveを増やさず、物質輸送はTRANSFER、物質変換はRECONFIGUREとして扱う。

## 2. MatterPayload

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

v0.6の単一 `amount` は廃止する。混合物全体へ単一mol値を置くより、Composition各成分へ量を持たせる。

```text
MatterPayload != Ref<Entity>
MatterPayload != Entity identity
```

## 3. Species identifiers

```text
ElementID
NuclideID
SpeciesID
MaterialClassID
```

### ElementID

原子番号レベルの分類。化学反応の粗い核inventory検査に使える。

### NuclideID

同位体/核種を区別する。isotope-sensitiveな化学・核反応ではElementIDより精密なledgerに使う。

### SpeciesID

原子・分子・イオン等の化学種。charge、nuclear composition、必要ならbond/connectivity等のspecies contractをregistryから参照する。

### MaterialClassID

steel、blood、tissue等の高級材料分類。検索・モデル選択には使えるが、基本保存ledgerではない。

## 4. Composition

```text
Composition {
    entries : Map<SpeciesID, SpeciesAmount>
}

SpeciesAmount = Quantity<AmountOfSubstance>
```

例:

```text
{
    H2O  : 55.5 mol,
    Na+  : 0.10 mol,
    Cl-  : 0.10 mol
}
```

species inventoryは反応により変化するため、Composition全体を普遍的保存量とはしない。

## 5. CompositionEstimate

術式がOBSERVEで得る組成情報は実状態そのものではない。

```text
Measurement<CompositionEstimate>
```

`CompositionEstimate` は分解能・不確かさ・未同定成分を持ちうる。

概念的に:

```text
CompositionEstimate {
    entries
    unidentified_fraction?
    model
    resolution
}
```

完全性証明なしに:

```text
CompositionEstimate -> Composition
```

という暗黙変換は禁止する。

## 6. StructureDescriptor

Compositionが「何でできているか」なら、Structureは「どう配置・組織化されているか」を記述する。

```text
StructureDescriptor<S : StructureSchema> {
    schema_id
    schema_revision
    data : S
}
```

代表schema:

```text
MolecularTopology
CrystalLattice
Microstructure
TissueArchitecture
```

同一CompositionでもStructureが違えば性質や機能は大きく変わりうる。

## 7. Structure preservation

Matter channelが構造を保持できるとは限らない。

registry contract例:

```text
PreserveStructure<CrystalLattice>
PreserveStructure<TissueArchitecture>
```

構造保存能力を持たないChannelへstructure付きpayloadを渡す場合:

- structureを落として輸送することを明示する
- 別途RECONFIGUREで再構成する
- または `StructureSchemaMismatch` / capability errorとして拒否する

のいずれかをpolicyとして選ぶ。

暗黙の構造破棄は禁止を推奨する。

## 8. ThermodynamicState

```text
ThermodynamicState<M> {
    model_id
    variables
}
```

Temperature一値だけでMatterの熱力学状態を完全表現しない。

モデルに応じて:

```text
Temperature
Pressure
Phase
Density
chemical_potential...
```

等を持ちうる。

```text
Temperature != InternalEnergy
Phase != Composition
```

## 9. ReactionRule

```text
ReactionRule<R : ReactionDomain> {
    id
    stoichiometry
    domain
    required_state
    products
    accounting_profile
    authority_requirements
}
```

ReactionRuleは実行権限ではなく、反応モデル/契約である。

```text
ReactionRule != Capability
```

## 10. Stoichiometry

```text
Stoichiometry = Map<SpeciesID, RationalCoefficient>
ReactionExtent : Quantity<AmountOfSubstance>
```

符号:

- reactant: negative
- product: positive

反応extent `ξ` について:

```text
Δn_i = ν_i ξ
```

これはspecies量変化のモデルであり、speciesそのものが保存されることを意味しない。

## 11. Reaction domains

```text
Chemical
Nuclear
Biochemical
Structural
```

### Chemical

通常の化学結合/電子状態変更。原則としてNuclide inventoryを変えない。

### Nuclear

核種変換を含みうる。ChemicalReactionProfileでは検証できない。

### Biochemical

基礎物理としては主にChemicalだが、TissueArchitecture、局所環境、触媒、反応系列等の追加制約を持つ高級domain。

### Structural

species inventoryを主に変更せず、相・結晶・微細構造・組織構造等を変更する高級分類。

## 12. ChemicalReactionProfile

```text
ChemicalReactionProfile {
    conserve_nuclide_inventory
    conserve_charge
    account_energy
    account_momentum
}
```

反応ruleのstoichiometryから、Nuclide/Element balanceを静的に検査できる場合はPREPARE前に証明する。

## 13. NuclearReactionProfile

v0.6.1では素粒子物理の完全なledger集合を固定しない。

最低限:

```text
Energy
Momentum
Charge
```

を要求し、追加ledgerはruntime registry contractへ委ねる。

Chemical ruleをNuclear reactionへ自動変換してはならない。

## 14. RECONFIGUREとの関係

Reactionは新しいMKI命令ではない。

高級reaction指定:

```text
reconfigure target {
    reaction = @rule;
    extent = 2 mol;
    identity = preserve;
}
```

compiler/runtimeは概念的に:

1. ReactionRuleをregistryから取得
2. reactant materialが十分か検査
3. required state / Lease / authorityを検査
4. stoichiometric balanceとConservationProfileを検証
5. 必要Energy/Momentum等をTRANSFERで準備
6. RECONFIGUREを実行
7. Eventへrule/revision/accounting結果を記録

する。

## 15. Healing implications

高級heal operationは最低でも:

```text
Composition
StructureDescriptor<TissueArchitecture>
ThermodynamicState
physiological constraints
```

を扱う必要がある。

単なるComposition一致は生体機能の復元を保証しない。

```text
same Composition != same Structure
same Structure != same Agent identity
```

## 16. Errors

```text
UnknownSpeciesError
StructureSchemaMismatch
ReactionTypeError
InsufficientMaterial
ConservationProofFailure
ReactionUnavailable
ReconfigurationFailure
```
