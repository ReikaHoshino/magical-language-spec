# Expression Reference — v0.5.2

**Status:** normative expression/type rules; examples and implementation strategies are informative.

## Purpose

MIR expression、operator、generic/type inference、effectful callのstatic contractを定義する。

## Non-goals

- parserまたはtype-checker implementation algorithmを固定しない。
- dimension equalityをsemantic type equalityとして扱わない。

## Depends on

- `scope-and-ownership.md`
- `types.md`
- `quantities.md`
- `mir-name-resolution.md`

## Key invariants

```text
parse != semantic validation != typed elaboration
Dimension equality != Semantic type equality
pure expression != world effect
```

## 1. Precedence

MIRの式優先順位は次の通り。上ほど弱い。

| level | operators | associativity |
|---:|---|---|
| 1 | `or` | left |
| 2 | `and` | left |
| 3 | `==`, `!=` | left |
| 4 | `<`, `<=`, `>`, `>=` | non-chaining |
| 5 | `+`, `-` | left |
| 6 | `*`, `/` | left |
| 7 | unary `-`, `not` | prefix |
| 8 | `^` | right |
| 9 | member/call postfix | left |

例:

```text
a + b * c      == a + (b * c)
-a^2           == -(a^2)
a^b^c          == a^(b^c)
not a and b    == (not a) and b
```

## 2. Comparison

関係演算子は暗黙にchainしない。

禁止:

```text
a < b < c
```

明示:

```text
a < b and b < c
```

観測不確かさを含む比較は `Truth` を返しうる。

```text
True | False | Indeterminate
```

従って、`Truth` を要求する分岐では `Indeterminate` の扱いを明示する。

## 3. Arithmetic typing

加減算は原則として同じ意味型・同じ次元を要求する。

```text
Energy + Energy      // valid
Length + Time        // DimensionError
Energy + Torque      // semantic TypeError even if dimensions match
```

乗除算は次元ベクトルを加減するが、得られた意味型は文脈・型規則によって精緻化する。

例:

```text
Mass * Velocity -> Momentum
```

は許された意味型規則がある場合に成立する。

## 4. Exponentiation

`^` は右結合。

指数が次元付き量の場合は原則禁止。MIR coreでは次元式の安全性を保つため、次元付き基底に対する指数は整数または静的に妥当性を証明できる無次元値に制限する。

```text
velocity^2
```

は合法で、次元は:

```text
m^2 s^-2
```

となる。

## 5. Postfix

メンバ参照と関数呼出しは最強のpostfix演算。

```text
measurement.revision
f(x)
object.position.y
```

ただしRefから任意propertyへ直接アクセスできることを意味しない。世界状態propertyは通常 `OBSERVE` を経由し、postfixは値/record側の構造参照にも使う。

## 6. Purity

構文上expressionでもeffectfulなものがある。

```text
transfer ...
acquire ...
await ...
```

従って:

```text
expression != pure expression
```

である。純粋性はeffect systemで判定する。
