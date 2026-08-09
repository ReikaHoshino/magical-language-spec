# Semantic Registry Reference — v0.6.2

**Status:** normative registry namespace/entry contract; storage layout and concrete datasets are informative or implementation-defined.

## Purpose

MIR、MKI、matter/reaction、kinetics、equilibrium、observer contractが参照する
trusted revisioned semantic definitionsの境界を定義する。

## Non-goals

- registry metadataからCapabilityまたはauthorityを付与しない。
- concrete registry datasetやstorage engineを固定しない。
- natural-language aliasをEntity identityとして扱わない。

## Depends on

- `scope-and-ownership.md`
- `compatibility.md`
- `matter.md`
- `kinetics.md`
- `observer-models.md`

## Key invariants

```text
Registry metadata != Capability
ReactionRule != Capability
KineticModel != Capability
registry hash mismatch alone != incompatibility
```

## 1. Purpose

MIRの意味型名、MKI実装、Matter/Reaction、kinetics、equilibriumの契約を共有するread-only registry。

```text
SemanticRegistry
```

は世界作用の権限表ではなく、型・payload・trait・accounting・species・structure・reaction・kinetics等のtrusted schemaである。

```text
Registry metadata != Capability
ReactionRule != Capability
KineticModel != Capability
```

## 2. Logical namespaces

v0.6.2では論理的に以下を区別する。

```text
semantic_kinds
species
structure_schemas
reaction_rules
kinetic_models
reaction_pathways
catalyst_models
inhibitor_models
equilibrium_models
activity_models
observer_models
controller_models
conservation_ledgers
```

実装上は同一database/fileでもよいが、ID namespaceとrevision contractを衝突させない。

## 3. Semantic kind entry

```text
SemanticEntry<K> {
    id
    category
    dimension?
    payload_type?
    traits
    conservation_profile?
    allowed_modes
    endpoint_requirements
    observer_properties
    revision
}
```

主要category:

```text
QuantityKind
TransferKind
StateProperty
TransferMode
ObserverQuantity
```

## 4. Species registry

```text
SpeciesEntry {
    id : SpeciesID
    nuclide_composition
    net_charge
    topology?
    aliases
    revision
}
```

SpeciesIDは名前文字列ではなくregistry identityを正とする。

```text
"water" != SpeciesID<H2O>
```

自然言語名/ラテン語名はalias/frontend辞書として解決する。

関連ID:

```text
ElementID
NuclideID
SpeciesID
MaterialClassID
```

`MaterialClassID` は高級分類で、普遍的保存ledgerには使わない。

## 5. Structure schema registry

```text
StructureSchemaEntry {
    schema_id
    data_contract
    compatible_transfer_capabilities
    compatible_reconfigure_domains
    revision
}
```

代表schema:

```text
MolecularTopology
CrystalLattice
Microstructure
TissueArchitecture
```

structure preserving Matter transferには対応 `PreserveStructure<S>` contractを要求できる。

## 6. Reaction rule registry

```text
ReactionRuleEntry<R : ReactionDomain> {
    id
    stoichiometry
    domain
    required_state
    products
    accounting_profile
    authority_requirements
    default_kinetic_models?
    default_equilibrium_model?
    pathway_ids
    revision
}
```

ReactionRuleは「何が何へ変化するか」のnet transformation contract。

```text
ReactionRule != ReactionPathway
ReactionRule != RateLaw
```

主要domain:

```text
Chemical
Nuclear
Biochemical
Structural
```

## 7. Kinetic model registry

```text
KineticModelEntry<R> {
    id
    reaction_rule_id
    rate_basis
    rate_law
    rate_constant_model?
    input_contract
    valid_domain
    uncertainty_model?
    revision
}
```

`KineticModelEntry` は一般のoverall reactionに対してstoichiometryからreaction orderを自動生成しない。

rate basis:

```text
ExtentRate
VolumetricRate
SurfaceRate
```

rate constant model例:

```text
ArrheniusModel {
    A
    Ea
    valid_temperature_range
}
```

Arrheniusは利用可能な一modelであり全reactionへ強制しない。

## 8. Reaction pathway registry

```text
ReactionPathwayEntry<R> {
    id
    overall_rule_id
    steps
    kinetic_model_id
    catalyst_requirements
    valid_domain
    accounting_profile
    revision
}
```

```text
ElementaryStepEntry {
    id
    stoichiometry
    reversible
    kinetic_model_id
    intermediates
    accounting_profile
    revision
}
```

複数Pathwayが同一ReactionRuleを実現できる。

## 9. Catalyst registry

```text
CatalystModelEntry {
    id
    requirement_contract
    affected_pathways
    kinetic_modifiers
    state_model
    recovery_condition
    valid_domain
    revision
}
```

CatalystModelはkinetics/pathway contractであり、同じoverall reaction・thermodynamic conditionのEquilibriumConstantを直接変更するcontractではない。

```text
Catalyst != equilibrium shift
```

触媒の実体resource/entityは別途RESOLVE/Capability/Lease等で扱う。

### CatalystState

```text
CatalystState {
    kinetic_activity
    occupied_sites?
    surface_state?
    poison_fraction?
    structure_revision?
}
```

`kinetic_activity` とthermodynamic activityを同一識別子にしないことを推奨する。

## 10. Inhibitor registry

速度低下作用は必要に応じて:

```text
InhibitorModelEntry
```

としてCatalystModelと分離する。

## 11. Activity model registry

```text
ActivityModelEntry {
    id
    species_domain
    phase_contract
    standard_state
    evaluate_activity
    valid_domain
    revision
}
```

濃度・分圧等をthermodynamic activityへ変換する規約を明示する。

## 12. Equilibrium model registry

```text
EquilibriumModelEntry<R> {
    id
    reaction_rule_id
    activity_model_id
    standard_state
    evaluate_K
    valid_domain
    tolerance_policy
    revision
}
```

平衡比較は同一のactivity / standard-state conventionで行う。

```text
ReactionQuotient Qr = Π_i a_i ^ ν_i
```

`K` と `Qr` の比較はexplicit toleranceを用いる。

## 13. Conservation ledger registry

```text
ConservationLedgerEntry {
    id
    semantic_type
    balance_rule
    applicable_domains
    revision
}
```

既存例:

```text
Energy
Momentum
Charge
```

ChemicalReactionProfileではNuclide/Element inventory balance等を追加できる。

NuclearReactionProfileでは追加の低層ledgerをworld/kernel contractとして登録できる。

## 14. Traits

主要trait:

```text
Observable
Transferable
Conserved
ScalarPayload
CompositePayload
VectorQuantity
```

`Transferable` と `Conserved` は直交する。

structure transport能力は量traitではなくChannel/endpoint capabilityとして扱う。

```text
PreserveStructure<S>
```

## 15. Example semantic entries

```text
Energy {
    category = QuantityKind + TransferKind
    dimension = kg m^2 s^-2
    payload_type = Quantity<Energy>
    traits = [Observable, Transferable, Conserved, ScalarPayload]
    conservation_profile = [Energy]
    allowed_modes = [Thermal, Radiative, Mechanical]
}

Momentum {
    category = QuantityKind + TransferKind
    dimension = kg m s^-1
    payload_type = Quantity<Momentum>
    traits = [Observable, Transferable, Conserved, ScalarPayload, VectorQuantity]
    conservation_profile = [Momentum, Energy]
}

Temperature {
    category = QuantityKind + StateProperty
    dimension = K
    traits = [Observable]
}

Matter {
    category = TransferKind
    payload_type = MatterPayload
    traits = [Observable, Transferable, CompositePayload]
    conservation_profile = [Energy, Momentum, Charge]
}
```

## 16. RegistryHash / required contract

```text
CompiledSpell {
    code_hash
    registry_hash
    required_registry_contract
    ...
}
```

v0.6.2ではrequired contractに以下も含みうる。

```text
SpeciesID
StructureSchema
ReactionRule
KineticModel
ReactionPathway
CatalystModel
EquilibriumModel
ActivityModel
ObserverModel
ConservationLedger
```

非互換:

```text
RegistryMismatch
```

## 17. Compatibility

registry hash差だけで常に拒否する必要はない。

```text
required_registry_contract
    ⊆ compatible(runtime_registry)
```

を証明できれば実行可能としてよい。

ただし以下の変更ではfail closedを優先する。

- SpeciesID意味契約。
- Stoichiometry / ReactionDomain。
- StructureSchema data contract。
- ConservationProfile。
- payload type。
- RateLaw input/output contract。
- KineticModel valid domain。
- ReactionPathway steps。
- Catalyst requirement/recovery contract。
- Equilibrium activity/standard-state convention。

判定は [`compatibility.md`](compatibility.md) のcommon envelopeを使用できるが、
required/provided contractの比較規則とgranularityはSemanticRegistry compatibility
profileが所有する。evidence不足は`Undetermined`であり、hash差だけを
`Incompatible`へ変換してはならない。

## 18. Security

registryはkernel/trusted runtime領域。

一般術式がregistryを書き換えることはできない。

```text
Registry metadata != authority
```

特に、術式が都合よくrate constant、equilibrium constant、reaction stoichiometryを変更することを許可しない。

registry mutationを許す場合は通常Capabilityより上位の管理権限として扱う。

## 19. Extensibility

安全な追加には名前だけでなく契約を登録する。

```text
semantic identity
payload / state schema
traits
accounting
structure contract
reaction rule
kinetic model
pathway
catalyst / inhibitor model
activity / equilibrium convention
revision
```

## 20. Machine-readable serialization

JSON serializationの正本は `schemas/semantic-registry.schema.json`、共通artifact
metadataは `schemas/artifact-metadata.schema.json` とする。各logical namespaceは
`id`、`revision`、domain固有の `contract` を持つentry列として表現する。
domain contractの機械可読定義は
`schemas/semantic-registry-contracts.schema.json` に分離し、namespaceごとに次を接続する。

| namespace | domain contract | reference上のrequired fields |
|---|---|---|
| `semantic_kinds` | `SemanticEntryContract` | `category`, `traits`, `allowed_modes`, `endpoint_requirements`, `observer_properties` |
| `species` | `SpeciesEntryContract` | `nuclide_composition`, `net_charge`, `aliases` |
| `structure_schemas` | `StructureSchemaEntryContract` | `data_contract`, `compatible_transfer_capabilities`, `compatible_reconfigure_domains` |
| `reaction_rules` | `ReactionRuleEntryContract` | `stoichiometry`, `domain`, `required_state`, `products`, `accounting_profile`, `authority_requirements`, `pathway_ids` |
| `kinetic_models` | `KineticModelEntryContract` | `reaction_rule_id`, `rate_basis`, `rate_law`, `input_contract`, `valid_domain` |
| `reaction_pathways` | `ReactionPathwayEntryContract` | `overall_rule_id`, `steps`, `kinetic_model_id`, `catalyst_requirements`, `valid_domain`, `accounting_profile` |
| `catalyst_models` | `CatalystModelEntryContract` | `requirement_contract`, `affected_pathways`, `kinetic_modifiers`, `state_model`, `recovery_condition`, `valid_domain` |
| `inhibitor_models` | `InhibitorModelEntryContract` | `extension` |
| `activity_models` | `ActivityModelEntryContract` | `species_domain`, `phase_contract`, `standard_state`, `evaluate_activity`, `valid_domain` |
| `equilibrium_models` | `EquilibriumModelEntryContract` | `reaction_rule_id`, `activity_model_id`, `standard_state`, `evaluate_K`, `valid_domain`, `tolerance_policy` |
| `observer_models` | `ObserverModelEntryContract` / `EvidenceFusionModelEntryContract` | observer conversion fields, or accepted Measurements, hypothesis/conflict/scoring/uncertainty/minimum-evidence/domain/tie-break/provenance |
| `controller_models` | `ControllerModelEntryContract` | observation input, error model, permitted effects, valid domain, resource/accounting, timing, saturation/overload, termination, required Capability/Lease, provenance |
| `conservation_ledgers` | `ConservationLedgerEntryContract` | `semantic_type`, `balance_rule`, `applicable_domains` |

`id` と `revision` は全entry共通のenvelopeに残し、domain fieldは `contract` 内だけに置く。
`ReactionRule`、`ReactionPathway`、`RateLaw` は別contractとして相互代用を許可しない。
各domain referenceが内部構造をまだ定義していない値は、意味を推測せず
opaque objectとして扱う。特に `InhibitorModel` は独立modelであることだけが規定済みのため、
空objectではなく明示的な `extension` objectを要求するextension pointとして表現する。

`metadata.compatibility.declarations` は互換性判定へのdomain入力であり、共通metadata
schema自体は互換性を判定しない。特に:

```text
registry_hash mismatch != incompatible
required_registry_contract ⊆ compatible(runtime_registry)
```

を維持する。`registry_hash` とartifact全体の `content_hash` は目的の異なるscopeを持つ。
前者は`registry-contract-set`、後者は`artifact-content`である。いずれもCapabilityや
compatibility resultを表さない。scoped hash recordの正本は `machine-values.md` と
`schemas/common-values.schema.json` とする。

machine-readable compatibility decisionの正本は `compatibility.md` と
`schemas/compatibility.schema.json` とする。metadata内のdeclaration/profileは判定入力で
あり、`Compatible` / `Incompatible` / `Undetermined`のresultそのものではない。

identifier、revision、SI dimensionはcommon value contractを使用する。entryの
`contract` 内部に残るexecutable modelやdomain-specific stateは既存domain referenceが
所有し、common quantityへ暗黙変換しない。

generic artifact / registry contract-setのcanonical bytesとdigest algorithmはpre-v0.8で
明示的にdeferする。fixtureは`status: unresolved`とscope/reasonを記録し、SHA-256その他の
algorithmやdigest valueを捏造しない。

`controller_models`はIssue #77のexperimental ownerとしてfull machine-readable contractを
要求する。単なるcontroller ID/string registrationでは不十分であり、登録によってCapability、
Lease、authorityが生成されることはない。`EvidenceFusionModelEntryContract`は不要な新namespaceを
増やさず`observer_models`内で明示的に識別するが、通常のObserverModel conversionおよび
`PlanningAssumption`とは相互代用しない。詳細ownerは`success-arcana.md`と
`evidence-inference.md`とする。
