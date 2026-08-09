# Compatibility Reference

**Status:** normative common decision envelope and domain-ownership boundary.

## Purpose

spec version、schema、SemanticRegistry、RuntimeProfile、LanguageAdapter、
SemanticFingerprint、WorldIndexの互換性判定について、共通の入力・証拠・結果表現と
判定所有者を定義する。

共通化するのはdecision envelopeだけである。各domainの意味を一つのboolean、
revision比較、hash比較へ縮約しない。

## Non-goals

- 全domainを一つの互換性algorithmへ統合しない。
- opaque revision tokenへnumeric/lexicographic orderingを追加しない。
- artifact hash、registry hash、SemanticFingerprintを相互代用しない。
- compatibility判定からCapability、authority、trust admissionを生成しない。
- source text normalizationからadapter identityやidentifier equivalenceを推測しない。

## Depends on

- `conventions.md`
- `machine-values.md`
- `registry.md`
- `runtime-time.md`
- `language-adapters.md`
- `source-text-normalization.md`
- `world-index.md`
- `security-sandbox.md`
- `versioning-and-migration.md`

machine-readable envelopeは
[`schemas/compatibility.schema.json`](../schemas/compatibility.schema.json) とする。

## Key invariants

```text
shared metadata rules != shared compatibility algorithm
hash mismatch alone != incompatibility
hash equality != compatibility
WorldIndexRevision != WorldRevision
adapter ID != external language tag
SemanticFingerprint profile mismatch != semantic inequality proof
Registry metadata != Capability
Compatibility != trust admission
```

## 1. Compatibility decision

互換性判定は次を明示するMUST。

```text
CompatibilityDecision {
    decision_id
    profile {
        profile_id
        profile_revision
        domain
        owner
        rule_source
    }
    producer
    consumer_requirement
    evidence[]
    result {
        status
        reason_code
        diagnostic?
    }
}
```

`profile` は「どの規則がこの判定を所有したか」を識別する。profile revisionはopaque
identity tokenであり、大小比較を意味しない。`producer.declarations` と
`consumer_requirement.declarations` はdomain-owned dataであり、共通envelopeはその
内部を解釈しない。

各evidenceは`decisive`を持つ。hash、external language tag、provenance等を記録しても、
owning profileが判定根拠としない値は`decisive: false`とするMUST。

## 2. Result model

```text
Compatible
Incompatible
Undetermined
```

- `Compatible`: 指定profileと利用可能なevidenceの範囲でconsumer requirementを満たす。
- `Incompatible`: 指定profileが要求する条件に反することを証明できる。
- `Undetermined`: profile unsupported/missing、必要evidence不足、または交渉/選択が必要。

`Undetermined` は `Compatible` ではない。LOAD/PREPARE/COMMIT等の安全境界では、owning
policyが明示的なnegotiation/fallbackを定義しない限りfail closedとするMUST。

```text
Undetermined != Incompatible
Undetermined != Compatible
schema-valid != Compatible
Compatible != authorized
```

同時に複数domainの判定が必要な場合、各domain decisionを別々に生成する。総合admissionは
必要decisionが全て`Compatible`であることに加え、trust、authority、freshness等の別gateを
満たす必要がある。

## 3. Domain decision matrix

| domain | producer | consumer requirement | authoritative evidence | owner / result | typical diagnostic |
|---|---|---|---|---|---|
| SpecVersion | artifact `spec_version` | accepted exact versions / migration profile | producer token、explicit accepted set | consuming implementation/release profile | `SpecVersionIncompatible`, `CompatibilityUndetermined` |
| Schema | schema `$id` + schema version | supported schema/profile | schema identity/version、validation result | schema consumer | `SchemaVersionIncompatible`, existing schema-specific mismatch |
| SemanticRegistry | registry contract set | `required_registry_contract` | required/provided contract semantics and revisions | SemanticRegistry compatibility profile | `RegistryMismatch`, `CompatibilityUndetermined` |
| RuntimeProfile | scheduler/integrator/replay/tolerance components | required runtime contract | component IDs/revisions/contracts and profile-owned tolerances | each runtime component profile | `RuntimeProfileIncompatible`, existing runtime diagnostics |
| LanguageAdapter | adapter/lexicon/grammar/normalizer revisions | accepted adapter contract/capabilities | exact adapter ID、revision declarations、required capabilities | LanguageAdapter compatibility profile | `AdapterCompatibilityUndetermined`, `AdapterIncompatible` |
| SemanticFingerprint | fingerprint profile/version | supported comparison profile | representation prefix/profile and validated digest representation | fingerprint comparison profile | `SemanticFingerprintProfileMismatch` |
| WorldIndex | index schema/snapshot mapping | required index schema/freshness policy | schema revision、index revision、source world revision、mapping | WorldIndex consumer/query policy | `IndexSchemaMismatch`, `IndexStale`, `CompatibilityUndetermined` |

domain-specific diagnostics remain authoritative. Generic diagnostics only express that a common
envelope/profile/evidence boundary failed; they do not replace the owning diagnostic.

## 4. Domain rules

### 4.1 Spec version

`spec_version`はopaque version identityである。このreferenceはSemVer orderingを追加しない。
profileはaccepted exact tokenまたはexplicit migration relationを宣言できる。relationが
なければ`Undetermined`であり、「latest wins」と推測しない。

### 4.2 Schema

schema compatibilityはexpected schema identity/versionと、consumerがsupportするprofileでの
validation成功を要求する。`schema_version`一致だけではsemantic compatibilityを証明しない。
schema migrationはprofileが明示的に所有するoperationである。

### 4.3 SemanticRegistry

```text
required_registry_contract
    ⊆ compatible(runtime_registry)
```

The profile compares required contract semantics and revisions. A differing or unresolved
`registry_hash` is non-decisive by itself. A matching hash is not Capability, trust, or authority.

### 4.4 RuntimeProfile

Runtime compatibility is the conjunction of separate scheduler, integrator, replay, and temporal
tolerance decisions required by the consumer. A root artifact revision cannot replace component
revisions. Integrator approximation and tolerance choices remain profile-defined and do not change
physical law.

<a id="language-adapter-compatibility"></a>

### 4.5 LanguageAdapter / lexicon / grammar / normalizer

adapter compatibility profileは次のrelationを所有する。

```text
adapter_id
adapter_revision
source_text_profile_revision
lexicon_revision?
grammar_revision?
normalizer_revision
required capabilities
```

`adapter_id` is compared as the project identity. External language tags and script hints are
metadata and MUST NOT substitute for adapter identity.

revision string間にimplicit orderingやwildcard compatibilityはない。profileはaccepted exact
revision、explicit migration、capability-preserving relationを宣言してよい。profileまたは
required revision relationがなければ`AdapterCompatibilityUndetermined`を伴う
`Undetermined`とする。これによりLatin固有またはcross-language共通algorithmを捏造せず、
判定所有者を固定する。

### 4.6 SemanticFingerprint

fingerprint比較は同じsupported profile/versionを要求する。V1 representationは
`sf:v1:sha256:<digest>`である。profile一致は2値を比較可能にするが、同値にはしない。
異なる/unsupported profileは`SemanticFingerprintProfileMismatch`を伴う`Undetermined`であり、
semantic inequalityの証明ではない。

```text
same fingerprint profile != same fingerprint value
profile mismatch != semantic drift proof
SemanticFingerprint != artifact content_hash
```

### 4.7 WorldIndex

decisionは次のfieldを分離して保持する。

```text
index_schema_revision
world_index_revision
source_world_revision
```

schema compatibility、snapshot mapping consistency、acceptable stalenessは別checkである。
`world_index_revision`一致はsource world revisionがcurrentであることを証明しない。
Visibility metadataはauthorityを付与しない。

## 5. Compatibility-sensitive profile choices

Implementations MUST identify the owning profile and revision for choices including:

- accepted spec/schema versions and explicit migrations;
- required/provided SemanticRegistry contract comparison granularity;
- scheduler/integrator/replay/tolerance admissibility;
- accepted adapter, source-text profile, lexicon, grammar, normalizer revisions;
- adapter capability requirements and explicit revision migrations;
- supported SemanticFingerprint comparison profiles;
- WorldIndex schema support and staleness/query consistency policy;
- handling of missing evidence and any permitted negotiation/fallback.

これらのchoiceはprofile-definedであり、revision spelling、hash equality、external
language tag、「newest」metadataから推測しない。

## 6. Security / admission

Compatibility decisionはadmissionのevidenceであり、authorityではない。

```text
CompatibilityDecision
  + provenance/trust admission
  + schema validation
  + Capability/Lease
  + freshness/revalidation
  → possible LOAD/PREPARE/COMMIT admission
```

`Incompatible`またはsafety-relevantな`Undetermined` resultはunsafe admissionを阻止する。
`Compatible` resultはsandbox、trust、authority、revalidation gateを迂回できない。

## 7. Examples

[`examples/compatibility/decision-cases.json`](../examples/compatibility/decision-cases.json)
contains one decision for every required domain. It demonstrates:

- registry compatibility despite non-decisive hash evidence;
- runtime and adapter decisions remaining profile-owned;
- fingerprint profile mismatch yielding `Undetermined`;
- WorldIndex schema/index/source-world revisions remaining distinct.

このunreleased contractによりhistorical `spec/` snapshotを書き換えない。

## 8. v1.x evolution boundary

v1.x stable scope、patch/minor/major change class、deprecation lifecycle、exact migration evidence、
post-migration validationは[`versioning-and-migration.md`](versioning-and-migration.md)が所有する。

release version policyは本書のdomain-owned decisionを置換しない。migration成功後もtarget schema
validationとtarget compatibility re-evaluationを要求し、authority/trust/admissionは別gateとする。

```text
release version policy != domain compatibility algorithm
migrated output != admitted output
```
