# Selector Reference — v0.6.4

**Status:** normative core + informative examples.

## Purpose

`Selector<T>`、単一 `RESOLVE`、bounded `Selection<T>` とWorld Index queryの意味を定義する。

## Non-goals

- World Index内部database engineは定義しない。
- Selectorを権限tokenにはしない。
- live collection semanticsは提供しない。

## Depends on

- `conventions.md`
- `world-index.md`
- `types.md`

## Key invariants

```text
Selector != Ref
CandidateSet != Ref set
Selection != LiveSet
Visibility != Authority
Index result != authoritative state
```

## 1. Selector

`Selector<T>` は対象Entityを記述する検索式。

```text
Selector<T> --RESOLVE--> Ref<T>
```

selector自体はEntity identityを保持しない。

- late binding: 使用時に再評価。
- early binding: 一度RESOLVEしてRefを保持。

## 2. Query / resolution context

従来の:

```text
C = (I,K,P,A)
```

をv0.6.4では `QueryContext` へ包含する。

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

厳格MIRはIntent依存の暗黙解決を減らすSHOULD。

## 3. Selector categories

### SymbolicSelector

```text
@stone
@water
```

World IndexのSymbolicIndex等を利用できる。symbolic nameは一意とは限らない。

### SpatialSelector

```text
sphere(center=..., radius=..., frame=...)
within(region)
```

SpatialIndexを候補絞り込みに使える。

### RelationalSelector

```text
nearest(@stone, origin)
relative_to(target, frame)
```

RelationIndex / SpatialIndex等を組み合わせる。

### FilteredSelector

```text
where(candidate, predicate)
```

候補集合に型安全なpredicateを適用する高級selector。

## 4. Coordinate frames

```text
WorldFrame
EntityFrame<Ref<Entity>>
AnchorFrame<Ref<Anchor>>
```

Frameが曖昧なら `AmbiguousFrameError`。

Index内spatial summaryが存在しても、必要precisionが高い物理操作ではauthoritative state/OBSERVEによる再検証を行うMUST。

## 5. Resolver query compilation

```text
Selector<T>
    -> ResolverQuery<T>
    -> CandidateSet<T>
```

`ResolverQuery<T>` はWorld Index用の高級query planでありMKI primitiveではない。

同じsemantic selectorでもquery plannerの物理実装はimplementation-defined。

## 6. CandidateSet

```text
CandidateSet<T> {
    candidates
    index_revision
    query_evidence
    truncated
}
```

CandidateSetはRef集合ではない。

Candidate EntityIDはauthoritative identity/type revalidation後に初めてRefへ変換できる。

## 7. Single RESOLVE

[NORMATIVE]

```text
RESOLVE<T>(selector, context) -> Ref<T>
```

概念フロー:

```text
Selector
→ ResolverQuery
→ WorldIndexSnapshot
→ CandidateSet
→ visibility filtering
→ uniqueness/type checks
→ authoritative revalidation
→ Ref<T>
```

候補0件または一意化不能なら `ResolutionFailure`。

暗黙first-matchはMUST NOT。

## 8. Bounded collection selection

```text
select<T>(
    selector,
    limit = N,
    order = order_spec
) -> Selection<T>
```

`select` はresolver service / standard library機能であり、新MKI primitiveではない。

```text
Selection<T> {
    refs           : Vec<Ref<T>>
    selected_at    : Instant
    index_revision : WorldIndexRevision
    order          : OrderSpec
    truncated      : Bool
}
```

Selectionはimmutable snapshot。

```text
Selection<T> != LiveSet<T>
```

## 9. Boundedness

`limit` はMUST。

```text
select<Object>(within(area), limit=32, order=nearest_first(origin))
```

上限なしcollection selectionは `UnboundedSelectionError`。

内部Index処理は別に `QueryBudget` を持つ。

```text
limit != query_budget
```

## 10. Ordering / determinism

例:

```text
nearest_first(origin)
entity_id_order
stable_index_order
```

同じ:

- WorldIndexSnapshot
- Selector
- QueryContext
- OrderSpec
- registry/world contracts

でdeterministic modeなら同じordered resultを返すMUST。

順序未指定の複数候補から暗黙選択してはならない。

## 11. Truncation

候補が `limit` を超えれば:

```text
selection.truncated = true
```

完全列挙が必要なpolicyでは `SelectionTruncated` として拒否できる。

## 12. Index consistency

```text
StrictSnapshot
BoundedStaleness(...)
BestEffort
```

等の `ConsistencyPolicy` を利用できる。

不可逆world effectのtarget確定をBestEffort index結果だけに依存してはならない。

必要なidentity/state/authorityはPREPARE/COMMIT policyに従い再検証するMUST。

## 13. Snapshot / staleness

Selection取得後にworldが変化しても `refs` は自動更新しない。

```text
WorldIndex stale != Ref stale
```

- `IndexStale`: 検索viewの鮮度問題。
- `StaleReference`: Entity lifecycle上Refが無効。

## 14. Early / late binding

### Late binding

```text
proc hit() {
    let target = resolve<Object> @stone;
    ...
}
```

呼出しごとにselector/indexを再評価。

### Early binding

```text
let target : Ref<Object> = resolve<Object> @stone;
...
use(target);
```

後続は同じEntityIDを追跡する。

### Collection snapshot

```text
let targets : Selection<Object> =
    select<Object>(within(area), limit=20, order=entity_id_order);
```

後からareaへ入ったEntityは自動追加されない。

## 15. Continuous sets

継続集合にはevent subscription等を用いる。

```text
on each EntityEntered(region) { ... }
```

Selectionをlive queryとして扱ってはならない。

## 16. Visibility / security

```text
Selector != Ref != Capability != Lease
```

World Indexのvisibility filteringは候補存在の露出を制御する。

候補がvisibleでも操作Capabilityが付与されるわけではない。

秘匿対象について外部へ存在有無を推測させないため、visibility failureを一般 `ResolutionFailure` へ畳むpolicyもMAY。

## 17. Query diagnostics

内部diagnosticでは:

```text
WorldIndexRevision
Candidate count before/after visibility
query budget usage
staleness
revalidation result
```

等を保持できる。

将来Feasibility reportはこれらのうち安全に公開可能な項目を出力できる。
