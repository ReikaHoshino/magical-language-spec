# Cross-language Normalization Example — v0.7.3

**Status:** informative example.

以下は同じ意図を異なるsurface languageから同じNSRへ寄せる例。

## Latin (`lat`)

```text
Calorem ab aqua ad aerem transfer.
```

## German (`ger`)

```text
Übertrage Wärme vom Wasser auf die Luft.
```

## Japanese (`jpn`)

```text
水から空気へ熱を移せ。
```

## English (`eng`)

```text
Transfer heat from the water to the air.
```

## Modern Chinese (`zho`)

```text
把热量从水转移到空气中。
```

`lzh` はhistorical/technical register設計が未確定のため、この例ではcanonical surface sentenceを固定しない。

## Shared NSR

```text
TransferCommand {
    Patient = SemanticKind(Energy, mode=Thermal)
    Source  = SelectorProposal(Symbolic("water"))
    Goal    = SelectorProposal(Symbolic("air"))
    Quantity = Unknown(MissingSurfaceArgument)
}
```

各言語の表層文法は異なるが、semantic-critical contentが同じなら同じ `SemanticFingerprint` を得ることを目標とする。

v0.7.3のmachine-readable NSR-layer equivalence fixtureとexpected fingerprintは
[`semantic-fingerprint/thermal-transfer-v1.json`](semantic-fingerprint/thermal-transfer-v1.json)
を参照する。rendererは未実装であり、以下はcontractであって実装済みround-tripの主張ではない。

## Conversion

Latinから日本語表示を得る場合:

```text
lat source
→ LanguageAdapter<lat>
→ NSR
→ SurfaceRenderer<jpn>
→ Japanese source
```

直接Latin→Japanese翻訳をsemantic authorityとはしない。

## Round-trip

```text
N0 = normalize(lat_source)
jp = render(N0, jpn)
N1 = normalize(jp)

assert SemanticFingerprint(N0) == SemanticFingerprint(N1)
```

一致しない場合:

```text
CrossLanguageDrift
```

## Ambiguity example

日本語:

```text
火の近くの石を飛ばせ。
```

候補例:

```text
Candidate A:
    Patient = nearest(stone, fire)

Candidate B:
    Patient = any stone in region_near(fire)
```

### StrictReject

複数candidateがsemantic-criticalなら停止。

### LegacyPermissive

profile-defined orderingでCandidate Aが選ばれた場合、術者がCandidate Bを意図していてもAへ作用する可能性がある。

これは:

```text
Unexpected result
```

であり、選択規則・candidate・provenanceが記録されている限り:

```text
undefined behavior
```

とは異なる。

このstrict/permissive比較のmachine-readable traceは:

- [`ambiguity-policy/strict-reject.json`](ambiguity-policy/strict-reject.json)
- [`ambiguity-policy/legacy-permissive-unexpected-result.json`](ambiguity-policy/legacy-permissive-unexpected-result.json)

にある。後者は選択後もtype/authority/conservation/identity checkがmandatoryであることを
明示し、意図外結果を安全検査の省略やreplay divergenceとして扱わない。
