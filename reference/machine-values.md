# Common Machine-readable Value Reference — pre-v0.8

**Status:** normative serialization boundary

## Purpose

identifier、version/revision、SI quantity、duration、hash recordのportable JSON表現を
`schemas/common-values.schema.json` と同期して定義する。

## Non-goals

- source textのUnicode/script/orthography normalizationを決定しない。
- unit conversion、物理法則、quantity kindのregistry contractを決定しない。
- domain compatibility algorithmをhash equalityへ置き換えない。
- generic artifactのcanonical bytes、digest algorithm、digest text encodingを選択しない。
- `SemanticFingerprintV1` のprojection/JCS/SHA-256 contractを変更しない。

## Depends on

- `conventions.md`
- `types.md`
- `quantities.md`
- `registry.md`
- `runtime-time.md`
- `world-index.md`

## Key invariants

```text
SemanticFingerprint != artifact content_hash
registry hash mismatch alone != incompatibility
identifier JSON encoding != source-language normalization
quantity semantic type != SI dimension
quantity encoding != physical law
revision identity != revision ordering
hash equality != compatibility
```

## 1. Identifier

machine-readable identifierはnon-empty JSON stringである。JSON decoding後のUnicode
code-point sequenceをexact tokenとして扱い、consumerはcase folding、Unicode
normalization、transliteration、language-specific spelling equivalenceを追加してはならない。

```json
"registry:species:H2O"
```

identifier namespaceはfieldのowning contractが決める。同じ文字列でもnamespaceが異なれば
同一identityを意味しない。source languageからidentifierを作る規則はowning
`LanguageAdapter` / domain contractが所有する。`SourceTextNormalizerV1` とこの
serialization contractは、そのmappingを推測または実行しない。

## 2. Version and revision

portable `version` / `revision` scalarはnon-empty JSON stringとする。

```json
{"schema_version": "1", "revision": "world-9001"}
```

stringはopaque identity tokenであり、lexicographic/numeric orderingを意味しない。
integer revisionを持つlegacy producerは、値を変えずbase-10 JSON stringへ移行する。
例えばJSON number `4201` はstring `"4201"` へ移行する。leading zeroやsignを追加して
別identityを作ってはならない。順序やsuccessor relationが必要ならowning domainが別field/
contractとして定義する。

## 3. SI dimension

SI dimensionは7 base exponentを名前付きobjectで全て記録する。

```json
{"kg": 1, "m": 2, "s": -2, "A": 0, "K": 0, "mol": 0, "cd": 0}
```

field省略をzeroと解釈してはならない。semantic quantity typeはdimensionと別fieldである。
同じdimensionを持つ異なるsemantic typeを暗黙castしない。

## 4. Quantity

portable scalar quantityは次を持つ。

```json
{
  "semantic_type": "Energy",
  "dimension": {"kg": 1, "m": 2, "s": -2, "A": 0, "K": 0, "mol": 0, "cd": 0},
  "value": 12.5,
  "unit": "J"
}
```

- `semantic_type`: registry/type contractが所有するidentifier。
- `dimension`: SI base exponent。
- `value`: finite JSON number。
- `unit`: unit vocabularyのidentifier。

この形はserializationであり、unitのscale/conversion、valid range、uncertainty、
conservation、physical lawを定義しない。exact rational、interval、distribution、
measurement uncertainty、composite payloadはowning domainの別contractを使い、
このscalar shapeへ黙って縮約しない。

## 5. Duration

durationは`Quantity<Time>`のportable specializationである。

```json
{
  "semantic_type": "Time",
  "dimension": {"kg": 0, "m": 0, "s": 1, "A": 0, "K": 0, "mol": 0, "cd": 0},
  "value": 10,
  "unit": "ms"
}
```

runtime tick、event order、causal orderとは別である。

```text
duration != runtime tick
duration != causal order
```

## 6. Scoped hash record

hash-like fieldはscopeと状態を明示する。

未解決:

```json
{
  "scope": "artifact-content",
  "status": "unresolved",
  "reason": "Generic artifact canonical bytes and digest algorithm are not selected pre-v0.8."
}
```

digestを記録する将来形:

```json
{
  "scope": "artifact-content",
  "status": "digest",
  "canonicalization_profile": "profile-id",
  "algorithm": "algorithm-id",
  "value": "profile-defined-encoding"
}
```

`status: digest` はcanonicalization profile、algorithm、valueを全て要求する。
algorithm名とopaque valueだけでcanonical bytesを推測してはならない。

pre-v0.8ではgeneric artifact `content_hash` とSemanticRegistry `registry_hash` の
canonicalization profile / digest algorithmを**明示的にdefer**する。理由は、artifact
ごとのincluded/excluded field、extension ordering、number/string treatment、Unicode
source-normalizationとの境界が共通仕様から一意に決まっていないためである。このdeferは
v0.8 Local Evaluatorをblockしない。Evaluatorはschema validation、artifact identity/
revision、provenance、trust/admission、domain compatibilityを使用でき、digest未解決を
「内容が一致する」「compatibleである」と解釈しなければよい。

## 7. Hash domains

| field | scope | identity target | compatibilityを決めるか |
|---|---|---|---|
| `metadata.content_hash` | `artifact-content` | serialized artifact content | no |
| `registry_hash` | `registry-contract-set` | registry contract set | no |
| input / NSR `source_hash` | `source-evidence` | exact source/evidence bytes under an owning capture profile | no |
| `semantic_fingerprint` | `sf:v1` contract | NSR semantic projection | no; semantic equality signal only |
| `revision` | owning domain | revision identity token | no |

```text
content_hash equality != RegistryCompatible
registry_hash mismatch != incompatible
revision equality != content equality
SemanticFingerprintV1 != either hash record above
```

`source-evidence` hashはcaptured source/evidenceのtraceability用であり、artifact content
identityやregistry contract identityではない。resolved digestを記録する場合は、owning
capture contractがcanonicalization profile（byte capture/encodingを含む）を指定する。
未指定ならnullまたはscoped `status: unresolved` とし、digestを捏造しない。

compatibility decisionは別domainであり、`compatibility.md` /
`schemas/compatibility.schema.json` が所有する。hash recordはdecision evidenceとして
記録できるが、owning profileが判定根拠としないhashは`decisive: false`とする。

## 8. Migration

既存fixtureは次のようにdeterministically移行する。

1. identifier spellingは変更しない。
2. portable revision JSON numberは同じdigitsのstringへ変換する。
3. dimension stringは7 exponent objectへ展開する。
4. duration `{value, unit}` は`semantic_type: Time`とtime dimensionを追加する。
5. `algorithm: fixture-placeholder` / `value: unresolved:*` はdigestではないため、
   scoped `status: unresolved` recordへ変換する。
6. generic hash algorithm、canonicalization profile、compatibility resultを移行時に発明しない。

historical `spec/` snapshotは移行対象外である。
