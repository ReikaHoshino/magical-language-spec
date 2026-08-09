# Common machine-readable value examples

Normative contract: [`../reference/machine-values.md`](../reference/machine-values.md)

## ACCEPT: exact identifier

```json
"registry:species:H2O"
```

JSON escape spelling is not identity. After JSON decoding, consumers compare the exact resulting
string and do not add case folding, Unicode normalization, or source-language equivalence.

## ACCEPT: Energy quantity

```json
{
  "semantic_type": "Energy",
  "dimension": {"kg": 1, "m": 2, "s": -2, "A": 0, "K": 0, "mol": 0, "cd": 0},
  "value": 12.5,
  "unit": "J"
}
```

## ACCEPT: duration

```json
{
  "semantic_type": "Time",
  "dimension": {"kg": 0, "m": 0, "s": 1, "A": 0, "K": 0, "mol": 0, "cd": 0},
  "value": 10,
  "unit": "ms"
}
```

## ACCEPT: unresolved artifact hash

```json
{
  "scope": "artifact-content",
  "status": "unresolved",
  "reason": "Generic artifact canonical bytes and digest algorithm are not selected pre-v0.8."
}
```

## REJECT: dimension without semantic type

```json
{
  "dimension": {"kg": 1, "m": 2, "s": -2, "A": 0, "K": 0, "mol": 0, "cd": 0},
  "value": 12.5,
  "unit": "J"
}
```

## REJECT: duration collapsed to value/unit

```json
{"value": 10, "unit": "ms"}
```

## REJECT: unresolved placeholder masquerading as digest

```json
{
  "scope": "artifact-content",
  "status": "unresolved",
  "algorithm": "sha256",
  "value": "not-a-digest",
  "reason": "Canonical input is unknown."
}
```

## REJECT: cross-domain hash scope

`metadata.content_hash` cannot use `scope: registry-contract-set`; `registry_hash` cannot use
`scope: artifact-content`.
