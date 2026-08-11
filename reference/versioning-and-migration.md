# v1.x Versioning, Deprecation, and Migration Guarantee

**Status:** normative RC contract for the v1.x stable line. `v1.0.0-rc.1` freezes the required core surface for validation; the final `v1.0.0` release remains owned by public Issue #3.

## Purpose

本書は、v1.xで安定と宣言するcore semantics、public artifact/schema contract、conformance classを
どのように維持し、非推奨化し、明示migrationするかを定義する。

release versionは変更の許容範囲を表すが、個別artifactの互換性を自動判定するoracleではない。
domain固有の互換性判定は引き続き[`compatibility.md`](compatibility.md)のowning profileが所有する。

## Non-goals

- version文字列、hash、SemanticFingerprintだけから互換性を判定しない。
- 全domainへ一つのmigration algorithmを適用しない。
- migrationによってCapability、Lease、authority、trust、semantic equalityを生成しない。
- v1.0でpublic serialized ECIRを固定しない。
- experimental、implementation-internal、明示deferredなsurfaceを自動的にstableへ昇格しない。
- historical `spec/` snapshotをcurrent contractへ追従させて書き換えない。

## Depends on

- [`compatibility.md`](compatibility.md)
- [`scope-and-ownership.md`](scope-and-ownership.md)
- [`conformance.md`](conformance.md)
- [`errors.md`](errors.md)
- [`../planning/v1.0-roadmap.md`](../planning/v1.0-roadmap.md)

machine-readable released RC policyは
[`schemas/compatibility-evolution.schema.json`](../schemas/compatibility-evolution.schema.json)、
reference fixtureは
[`examples/compatibility/evolution-policy-v1.json`](../examples/compatibility/evolution-policy-v1.json)
とする。

## Key invariants

```text
release version policy != domain compatibility algorithm
version ordering != compatibility proof
same major != automatic compatibility
explicit migration != semantic equality proof
migrated output != admitted output
deprecation != silent removal
compatibility evidence != authority or trust
SemanticFingerprint != artifact content_hash
```

## 1. Stable guarantee scope

v1.x guaranteeは、release gateで明示的に`RequiredCore`または`StablePublic`へ分類されたcontractに限る。

- `RequiredCore`: v1.xで必須となるcore semanticsとreleased conformance-class contract。
- `StablePublic`: releaseがpublic/stableと明記したschema、artifact、CLI/library contract。
- `OptIn`: separately versioned profile/capabilityとして明示選択した場合だけ保証されるsurface。
- `Experimental`: 互換性保証を持たず、stable consumerが暗黙依存してはならないsurface。
- `ImplementationInternal`: specification-level互換性保証の対象外。

statusはartifact名、directory、実装での存在だけから推測しない。machine-readable policyの
`guarantee_scope`またはrelease-owned normative declarationをDefinitionSourceとする。

現時点でpublic serialized ECIR、non-reference adapter breadth、production distributed runtime、
implementation-specific solver/scheduler microstepsはv1 stable scopeへ自動昇格しない。

## 2. Release-number contract

v1.x release numberはstrict `MAJOR.MINOR.PATCH`表現を使う。これはrelease change classを表すだけで、
opaque artifact/profile revisionの大小関係を定義しない。

### 2.1 Patch

同じminor内のpatch releaseは、既存`RequiredCore`/`StablePublic` contractを再解釈、削除、または
新しいmandatory field/capabilityによって拒否してはならないMUST NOT。

許容されるのは、既存意味を変えないcorrection、documentation、compatible security hardening、
および既存consumerを拒否しないinternal changeである。

### 2.2 Minor

同じmajor内のminor releaseは、backward-compatible additive contract、optional field、optional
capability、またはexplicit `OptIn` profileを追加してよいMAY。既存v1-valid required-core artifactを
新しいoptional capabilityの不在だけで拒否してはならないMUST NOT。

deprecationを開始できるが、`RequiredCore`/`StablePublic` contractをv1.x内でsilent removalまたは
semantic reuseしてはならない。

### 2.3 Major

required-core breaking changeは新major、または既存consumerが暗黙選択しないseparately versioned
explicit opt-in contractを要求するMUST。新majorであってもchange、replacement/migration、または
移行不能理由を明示する。

```text
patch correction != semantic reinterpretation
minor additive != new mandatory requirement
major change != implicit migration
```

## 3. Deprecation lifecycle

deprecationはmachine-readable recordを持つMUST。最低限:

```text
deprecation_id
owner
rule_source
affected_contract (exact identity + revision)
deprecated_in
earliest_removal_major
replacement? OR rationale
```

`earliest_removal_major`はstable majorより大きくなければならない。v1.xでdeprecateした
`RequiredCore`/`StablePublic` contractをv1.x内で削除または別意味へ再利用しない。

replacementが存在しない場合も黙って削除せず、理由とmajor boundaryを記録する。

## 4. Explicit migration contract

migrationはdomain/profile ownerが宣言したexact relationである。

```text
MigrationEntry {
    migration_id
    domain
    owner
    rule_source
    source_contract { contract_id, contract_revision, profile_id, profile_revision }
    target_contract { contract_id, contract_revision, profile_id, profile_revision }
    transformation { transformation_id, transformation_revision }
    required_postconditions [SchemaValidation, CompatibilityReevaluation]
}
```

source/target revisionとcompatibility profile identity/revisionはopaque exact tokenであり、lexicographic
ordering、prefix、wildcard、hash equality、SemanticFingerprint equalityからmigration pathを推測しない。

同じdomain/source/targetに複数pathがあり、consumer profileが一つを明示選択できない場合は
`MigrationPathAmbiguous`でfail closedする。pathがなければ`MigrationPathMissing`とする。

## 5. Migration execution boundary

reference helperは次の順序だけを共通化する。

```text
exact migration selection
→ named transformation
→ target schema validation
→ target compatibility re-evaluation
→ separate trust/authority/admission gates
```

transformation本体とdomain semanticsはowning implementation/profileが所有する。共通helperは
version、revision、hash、payloadを解釈してmigrationを発明しない。

- transformation implementationがない場合は`MigrationImplementationMissing`。
- outputがtarget schemaに不適合なら`MigratedArtifactInvalid`。
- post-migration compatibilityが`Incompatible`なら`PostMigrationIncompatible`。
- post-migration compatibilityが`Undetermined`なら`PostMigrationCompatibilityUndetermined`。
- compatibility decisionのdomain/profileがtarget contractの宣言と一致しなければ
  `PostMigrationCompatibilityProfileMismatch`。

成功resultは選択したmigrationとpostcondition evidenceを記録するだけで、Capability、Lease、authority、
trust、semantic equalityを含めない。

## 6. Compatibility/admission boundary

migration後も通常のdomain-owned `CompatibilityDecision`を新しく生成し、schema validation、trust、
authority、freshness等のgateを別々に満たすMUST。

```text
MigrationSucceeded
!= Compatible
!= trusted
!= authorized
!= admitted
```

## 7. Conformance and release-gate ownership

v0.11.0は本contractのrelease classification、deprecation、exact migration selection/execution、
non-authorizing boundaryをCore-1.0 stable case IDとreverse rule coverageへ昇格する。

required reference-path artifact/profile coverageは`conformance/compatibility-coverage.json`が列挙する。
このinventoryもdomain algorithmを定義せず、missing owner/profileをrelease gateで検出するためのevidenceである。

historical v0.10 suite/snapshotは変更しない。pre-public archive Issue #66完了はCompatibility Guaranteeをversioned evidenceへ
進めるが、pre-public archive Issue #40の他gate、最終release rehearsal、pre-public archive Issue #38のRC eligibilityを自動的に完了させない。
