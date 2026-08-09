# Source Text Normalization Reference — Unreleased pre-v0.8

**Status:** normative common source-representation contract for all `LanguageAdapter<L>` implementations.

## Purpose

language-specific tokenization / segmentationより前に、source textの受領、最小限の
Unicode representation normalization、provenance mapping、fail-closed diagnosticsを
共通化する。

本contractはsource representationだけを扱い、lexical candidate、semantic role、NSR、
identifier、SemanticFingerprint、artifact hashを決定しない。

## Key invariants

```text
source normalization != semantic normalization
orthographic equivalence != semantic authority
project adapter ID != external language tag
Unicode normalization inside source processing
  != identifier normalization inside SemanticFingerprint
normalized source text != canonical NSR
```

`SemanticFingerprintV1` がidentifierへUnicode normalization、case folding、whitespace
trimmingを行わない既存規則は維持する。source normalization済みのsurface spellingを
canonical NSR identifierとして暗黙に再利用してはならない。

## 1. Pipeline position

```text
UTF-8 bytes / Unicode scalar text
→ SourceTextNormalizerV1
→ normalized source + source map
→ LanguageAdapter<L> tokenization / segmentation
→ lexical / morphology / syntax candidates
→ NormalizationCandidateSet
→ NSR
```

`SourceTextNormalizerV1` の出力は依然としてsource textである。adapterはこの出力を
evidenceとして使えるが、source spellingだけをsemantic truth、Entity resolution、
Capability、authorityへ昇格させてはならない。

## 2. Input and encoding

### 2.1 File / byte boundary

- byte inputはUTF-8であるMUST。
- decoderはill-formed byte sequenceをreplacement characterへ黙って置換せず、
  `InvalidUTF8` で拒否するMUST。
- byte stream先頭のUTF-8 BOM (`EF BB BF`) はtransport markerとして除去できる。
  除去した事実を`Utf8BomRemoved` transformationとして記録するMUST。
- UTF-16/UTF-32、locale-dependent encoding、encoding auto-detectionはV1の共通境界に
  含めない。callerが明示的transcodingを行い、そのprovenanceを保持する。

### 2.2 In-memory text boundary

- inputはUnicode scalar value sequenceであるMUST。
- surrogate code pointは`InvalidUnicodeScalar`で拒否するMUST。
- U+0000はV1 source transportでunsupportedとし、`UnsupportedSourceCharacter`で拒否する。
- in-memory string先頭のU+FEFFはtransport BOMと推測して除去してはならない。
  byte boundaryで確認されたBOMだけを除去する。

## 3. Common transformation policy

V1は次の順序だけを共通処理として定義する。

1. strict UTF-8 decodeとbyte-boundary BOM処理。
2. CRLF / CR line endingをLFへ変換。
3. 各line bodyをUnicode NFCへ変換。

NFCはcanonical compositionのためのsource representation規則であり、orthographic
variantをsemanticに同一化する規則ではない。

### 3.1 Common layerが行わない処理

```text
NFKC / NFKD compatibility normalization
case folding / lowercasing / uppercasing
whitespace trim / collapse / indentation rewrite
punctuation substitution
full-width / half-width folding
compatibility character expansion
transliteration / romanization
historical spelling rewrite
language-specific tokenization / segmentation
```

したがってfull-width form、circled character、compatibility ideograph等はNFCが
canonicalに変更する場合を除いて保持される。case sensitivity、punctuation meaning、
space segmentationは各adapterのgrammar / lexiconが所有する。

## 4. Adapter identity and language/script tags

`adapter_id` はproject内の安定実装identityであり、明示的に渡すMUST。
external language tagやscript hintからadapter IDを推測してはならない。

```text
adapter_id: lat
external_language_tags: [la]
script_hints: [Latn]
```

- external language tagはBCP 47 styleのmetadataであり、common V1はalphabetic primary
  subtag（2〜8文字）と1〜8文字のsubtag列からなるsupported syntax subsetを検査して
  そのまま保持する。subset外のgrandfathered/private-use form等を推測して受理しない。
- script hintはfour-letter ISO 15924 style metadataとして保持する。
- tagのcase canonicalization、likely-subtag expansion、language detectionはV1では行わない。
- tag/script mismatchはcommon Unicode変換だけで意味を推測せず、adapter selection/configuration
  stageでdiagnoseする。

adapter/revision compatibilityは `compatibility.md` のLanguageAdapter domainが所有する。
source normalizerはexternal tagやscript hintから`adapter_id`互換性を判定しない。

## 5. Orthographic variants

case variant、historical spelling、旧字体/新字体、異体字、送り仮名、Latin ligature、
transliteration等はadapter-level lexical / orthographic candidateとして扱う。

```text
surface variant
→ candidate + evidence + source span
→ adapter policy / lexicon
→ zero or more semantic proposals
```

variant tableはsemantic registry entry identityそのものではない。orthographic
equivalenceを理由にcandidateを一つへ黙ってcollapseしてはならず、semantic-criticalな
差が残る場合は既存ambiguity contractへ渡す。

## 6. Source spans and provenance

offset unitはUnicode scalar value、spanは0-based half-open `[start, end)` とする。

accepted resultは最低限:

- original decoded source text。
- normalized source text。
- applied transformationとinput/output span。
- normalized output spanからoriginal decoded source spanへのsource map。
- mapがexact one-to-oneか、coarse many-to-manyか。

を保持するMUST。

canonical composition、combining-mark reordering、line-ending変換のためscalar数が変わる
場合、adapterはnormalized offsetをoriginal offsetとして再利用してはならない。
mappingが一意に細分化できなければ、包含するcoarse source spanを返し`exact=false`とする。
diagnostic/provenanceは狭いが誤ったspanより、正しいcoarse spanを優先する。

original decoded source textを保持することで、common normalization後もoriginal spellingを
audit / rendering evidenceとして回収できる。secret/redaction policyは
`security-sandbox.md` が所有し、本contractは無制限のraw source exportを許可しない。

## 7. Machine-readable result

schema:
[`schemas/source-text-normalization.schema.json`](../schemas/source-text-normalization.schema.json)

reference utility:
[`tools/source_text_normalization.py`](../tools/source_text_normalization.py)

fixtures:
[`examples/source-normalization/`](../examples/source-normalization/)

accepted result:

```text
SourceTextNormalizationResult {
    contract_version
    status = Accepted
    adapter {
        adapter_id
        external_language_tags
        script_hints
    }
    input {
        boundary
        encoding = UTF-8
        original_text
        utf8_bom_removed
    }
    output {
        normalization_form = NFC
        normalized_text
    }
    transformations
    source_map
}
```

このserializationのproperty order、generic artifact hashing、content hashは本Issueの
scope外であり、Issue #13が所有する。

## 8. Failure policy

common layerはunsupported inputを推測、置換、transliterateして成功扱いにしない。

```text
InvalidUTF8
InvalidUnicodeScalar
UnsupportedSourceCharacter
InvalidAdapterID
InvalidExternalLanguageTag
InvalidScriptTag
```

rejected resultはstable diagnostic code、message、既知ならsource offsetを保持する。
`utf8-bytes` boundaryのoffsetはbyte index、`unicode-text` boundaryのoffsetはUnicode
scalar indexとし、boundaryを伴わないoffset解釈をしてはならない。
rejectionからNSR candidateを生成してはならない。

## 9. Conformance

common source normalizationに準拠するadapterは:

1. V1 pipeline positionとtransformation orderを維持する。
2. original-source provenanceをrecoverableにする。
3. NFKC/case/width/punctuation/orthography処理をcommon ruleとして追加しない。
4. project adapter IDとexternal tag/script metadataを分離する。
5. source outputをsemantic identifier canonicalizationへ流用しない。
6. invalid/unsupported inputをdiagnosticとしてfail closedする。

これによりfuture `lzh`, `jpn`, `zho` adapterは共通Unicode ingress policyを再定義せず、
segmentation、ellipsis、orthography等のlanguage-specific contractだけを追加できる。
