# World Index Reference — v0.6.4

**Status:** normative schema + informative implementation notes.

## Purpose

`RESOLVE` / `select<T>` が候補Entityを検索するためのdatabase/index contractを定義する。実world dataはこの版では用意しない。

## Non-goals

- World State `Σ` の代替にはしない。
- Entity状態の完全コピーをindexへ要求しない。
- index query自体をMKI primitiveにしない。
- 利用者へ全EntityIDを公開しない。

## Depends on

- `conventions.md`
- `selectors.md`
- `types.md`
- `architecture.md`
- `semantics.md`

## Key invariants

```text
WorldIndex != WorldState
IndexRecord != Entity
CandidateSet != Ref set
Visibility != Authority
IndexStale != StaleReference
```

## 1. Authoritative source

[NORMATIVE]

World State / identity serviceがEntityの存在・identity・current authoritative stateの正本である。

World Indexは検索を高速化するための派生viewであり、Index recordだけを根拠に不可逆world mutationをCOMMITしてはならない。

## 2. Root schema

```text
WorldIndex {
    schema_revision       : IndexSchemaRevision
    index_revision        : WorldIndexRevision
    source_world_revision : WorldRevision
    identity_index        : IdentityIndex
    symbolic_index        : SymbolicIndex
    spatial_index         : SpatialIndex
    relation_index        : RelationIndex
    visibility_index      : VisibilityIndex
}
```

具体的なdatabase engine、serialization、table layoutはimplementation-defined。

## 3. Snapshot

```text
WorldIndexSnapshot {
    index_revision
    source_world_revision
    captured_at
    schema_revision
}
```

queryはsnapshot identityを結果へ付与するSHOULD。

同じsnapshot / query / QueryContext / OrderSpecから得られる順序付き結果は、deterministic modeでは同一であるMUST。

## 4. EntityIndexRecord

```text
EntityIndexRecord<T> {
    entity_id            : EntityID<T>
    type_tags            : Set<TypeTag>
    symbolic_names       : Set<SymbolicName>
    spatial_summary      : SpatialSummary?
    relation_keys        : Set<RelationKey>
    visibility_metadata  : VisibilityMetadata
    record_revision
    source_world_revision
}
```

### type_tags

候補絞り込み用。最終的な型適合性はauthoritative sourceで再検証できる。

### symbolic_names

alias/name。重複可能。

### spatial_summary

coarse pose、bounding volume、region membership等を保持できるが、精密物理状態ではない。

### visibility_metadata

候補列挙そのものを許すかのfilter用metadata。Capabilityそのものではない。

## 5. IdentityIndex

```text
EntityID -> EntityIndexRecord
```

EntityIDは再利用しない既存規則を継承する。

Indexにrecordが残っていてもauthoritative worldでEntityが終了していればRef生成は失敗する。

## 6. SymbolicIndex

```text
SymbolicName -> Set<EntityID>
```

名前は一意であるMUST NOT。

例:

```text
"lapis" -> [#A12,#B55,#F02]
```

「最初の一件」を暗黙採用してはならない。

## 7. SpatialIndex

SpatialSelector用。

例として:

```text
bounding volume
coarse pose
frame association
region membership
spatial partition key
```

を保持できる。

位置precisionが術式の安全性に影響する場合、OBSERVEまたはauthoritative state revalidationを要求する。

## 8. RelationIndex

```text
Relation(subject, predicate, object, revision, evidence)
```

例:

```text
inside(A, region)
attached_to(A, B)
owner_of(agent, artifact)
embodied_by(agent, organism)
```

relationが権限を示唆してもCapabilityへ暗黙変換してはならない。

## 9. VisibilityIndex

候補存在の露出policyを扱う。

```text
VisibilityMetadata {
    discoverability_class
    required_discovery_context?
    redaction_policy
}
```

`required_discovery_context` は権限/知識/知覚条件を参照できるが、実操作権限とは別。

## 10. QueryContext

```text
QueryContext {
    intent_context
    knowledge_context
    perception_context
    authority_context
    frame_context
    snapshot_policy
    consistency_policy
    query_budget
}
```

従来の `C=(I,K,P,A)` を包含する。

`authority_context` は候補可視性filterに利用できるが、最終Capability checkを置換しない。

## 11. ResolverQuery

```text
Selector<T>
  -> ResolverQuery<T>
  -> CandidateSet<T>
```

```text
ResolverQuery<T> {
    selector_plan
    required_type
    frame_requirements
    visibility_requirements
    order?
    limit
    consistency_policy
}
```

## 12. CandidateSet

```text
CandidateSet<T> {
    candidates      : Vec<Candidate<T>>
    index_revision  : WorldIndexRevision
    query_evidence
    truncated       : Bool
}
```

```text
Candidate<T> {
    entity_id
    type_evidence
    selection_evidence
    visibility_evidence
    record_revision
}
```

CandidateはRefではない。

## 13. RESOLVE pipeline

```text
Selector<T>
→ compile ResolverQuery<T>
→ acquire WorldIndexSnapshot
→ query relevant indexes
→ CandidateSet<T>
→ visibility filter
→ uniqueness / order rule
→ authoritative identity/type revalidation
→ Ref<T>
```

0件または一意化不能なら `ResolutionFailure`。

## 14. Selection pipeline

```text
Selector<T>
→ CandidateSet<T>
→ visibility/type/revalidation
→ bounded Vec<Ref<T>>
→ Selection<T>
```

`Selection.index_revision` は `WorldIndexRevision` とする。

## 15. ConsistencyPolicy

```text
StrictSnapshot
BoundedStaleness {
    max_age?
    max_revision_lag?
}
BestEffort
```

### StrictSnapshot

同一snapshot上でqueryし、指定されたrevalidation requirementを満たす。

### BoundedStaleness

許容stalenessを超えれば `IndexStale`。

### BestEffort

informative browsing等に利用可能。不可逆world effectのtarget確定だけをBestEffort index結果へ依存してはならない。

## 16. SnapshotPolicy

```text
Current
AtLeast(WorldRevision)
Pinned(WorldIndexRevision)
```

等を実装できる。

exact policy集合は将来拡張可能だが、使用したrevisionはresult/reportへ記録するSHOULD。

## 17. QueryBudget

```text
QueryBudget {
    max_candidates
    max_index_work?
    max_spatial_extent?
    deadline?
}
```

`select<T>` の `limit` と内部query budgetは別。

- `limit`: 返す最大件数。
- `query_budget`: 検索処理に許すresource。

budget超過は `QueryBudgetExceeded`。

## 18. Revalidation

[NORMATIVE]

不可逆または危険なworld effectについて:

1. candidate EntityIDが現在有効か。
2. expected typeを満たすか。
3. target revision/state条件が必要なら満たすか。
4. authority/Leaseが現在有効か。

をPREPARE/COMMIT policyに従い再検証するMUST。

## 19. Update model

Index update方式はimplementation-defined。

例:

```text
Synchronous
EventDriven
Batch
Hybrid
```

実装は少なくとも以下を文書化するMUST。

- revisionの意味。
- worst-caseまたはpolicy上のstaleness。
- snapshot consistency。
- relation/spatial updateのordering。

## 20. Security

Indexはmetadata side channelになりうる。

実装は:

- hidden Entityのcount漏洩。
- timing差による存在推測。
- alias検索による権限迂回。
- stale relationによる誤認。

を考慮するSHOULD。

外部errorを `ResolutionFailure` に畳み、内部診断だけにVisibility原因を残すpolicyも許容する。

## 21. Errors

```text
IndexUnavailable
IndexSchemaMismatch
IndexStale
QueryBudgetExceeded
IndexConsistencyFailure
```

`StaleReference` はindex errorではなくRef/Entity lifecycle error。

## 22. Feasibility / replay metadata

将来のEvaluatorは最低限:

```text
world_index_revision
source_world_revision
query policy
resolved EntityIDs
assumptions / revalidation requirements
```

をreportへ含められるSHOULD。

これにより同じ呪文解析結果が「どのworld snapshotを前提にしたか」を追跡できる。

## 23. Machine-readable serialization

JSON serializationの正本は `schemas/world-index.schema.json`、共通artifact metadataは
`schemas/artifact-metadata.schema.json` とする。rootとsnapshotはそれぞれ
`world_index_revision`、`source_world_revision`、`index_schema_revision` を明示し、
fixture validationでは同一artifact内のmapping一致を検査する。
identifierとrevision tokenは `machine-values.md` /
`schemas/common-values.schema.json` のexact string contractを使用する。source-language
normalization、numeric revision ordering、cross-namespace identityをこのschemaから
推測しない。

```text
WorldIndexRevision != WorldRevision
WorldIndex != WorldState
IndexRecord != Entity
Visibility != Authority
```

`records` は検索viewの `EntityIndexRecord` serializationであり、authoritative Entityを
埋め込まない。`indexes` の物理layoutと各summary/relation payloadの詳細は既存どおり
implementation-definedであり、このserializationは新しいstorage engine semanticsを
規定しない。

compatibility判定は [`compatibility.md`](compatibility.md) のcommon envelopeを使用できる。
ただし`index_schema_revision` support、snapshot mapping、staleness/query consistencyは
別々のprofile-owned checkである。`world_index_revision`一致だけから
`source_world_revision` freshnessまたはauthorityを推測してはならない。

Historical evidenceについて、WorldIndexはcandidate Measurement/evidence-store recordを列挙できるが、
record自体をpast WorldStateまたはcommitted Historyとして扱わない。retention/freshness/redaction/privacyは
evidence store/profile ownerが定義し、History queryはMKI primitiveではない。snapshot-consistent
evidence fusionのownerは`evidence-inference.md`とする。
