# MIR Scope and Name Resolution Reference

**Status:** normative

## Purpose

`grammar/mir.ebnf` が受理するMIRについて、識別子の束縛先、字句scope、名前検索、
重複束縛、および名前解決diagnosticを定める。また、構文としてparse可能であることと
静的に妥当であることを区別する。

## Non-goals

- 新しいMIR表面構文を追加しない。
- first-class callable、module/import、overload、pattern destructuringを追加しない。
- type checking、effect checking、termination checking、runtime entity resolutionを
  名前解決へ統合しない。
- `LanguageAdapter<L>` または自然言語frontendの名前解決を定義しない。
- registry、World Index、standard libraryに登録される具体的な名前を定義しない。

## Depends on

- `conventions.md`
- `architecture.md`
- `types.md`
- `registry.md`
- `selectors.md`
- `errors.md`
- `../grammar/mir.ebnf`

## Key invariants

```text
parse != semantic validation != typed elaboration != runtime
lexical name resolution != registry lookup != World Index RESOLVE
Selector != Ref
Registry metadata != Capability
```

## 1. Processing phases

適合実装は少なくとも次の観測可能なphase境界を維持するMUST。

1. **Parse**: token列が `grammar/mir.ebnf` のproductionを満たすか判定し、未解決の
   identifierを含み得るsyntax treeを構築する。
2. **Static semantic validation**: scopeを構築し、bindingを収集し、各lexical/type/
   callable identifierを一意なdeclarationへ対応付け、重複または未解決名を拒否する。
3. **Typed elaboration**: 解決済みdeclarationとregistry contractを用いてtype、
   dimension、effect、authority、termination等を検査し、Typed MIRを構築する。
4. **Runtime / planning resolution**: selectorや`resolve`をWorld Index、snapshot、
   QueryContextに対して評価する。

parserは、後続phaseで拒否されるsourceを受理してよい。逆に、名前解決成功はtype、
effect、registry compatibility、runtime target existenceを保証しない。

## 2. Name classes

同じidentifier文字列でも、出現したproductionが要求するname classに従って解決する。

| Name class | Declaration / provider | Representative uses | Resolution phase |
|---|---|---|---|
| callable | top-level `spell-decl`, `proc-decl`, `fn-decl`; provided callable environment | call target such as `make_matter_payload(...)` | static semantic validation |
| value | parameters, `let`, `for`, event `as` bindings | bare `primary-expression` | static semantic validation |
| type | `type-param`; provided type environment / SemanticRegistry contract | `type`, return type, type arguments | static validation then typed elaboration |
| contextual semantic name | registry/profile-provided effect, transfer kind/mode, invariant, identity, pattern constant, and similar grammar positions | `Channel<Energy>`, `mode = Thermal`, `True =>` | typed elaboration / relevant registry contract |
| selector/operator name | selector environment or World Index-facing selector syntax | `@stone`, `within(...)` inside `selector` | selector validation / runtime resolution |
| member name | the type of the expression before `.` | `water.temperature`, `target.Composition` | typed elaboration |
| argument/clause label | fixed grammar or callee/contract metadata | `limit =`, `order =`, selector named arguments | parse or typed elaboration |

これらは論理的に別namespaceである。value `Energy` が存在してもtype `Energy` または
registryのsemantic kind `Energy`を宣言したことにはならない。

`reference/registry.md` のlogical namespacesも相互に区別される。期待されるregistry
categoryは使用位置とtyped contractが決定し、同じ文字列の別registry namespace entryを
暗黙に代用してはならない。

`@identifier` は字句value参照ではない。`resolve` / `select`によるWorld Index検索も
lexical name resolutionではなく、結果の存在・一意性・freshnessはruntime/planning
diagnosticの対象である。

## 3. Scope tree

### 3.1 Program scope

`program` は単一のcallable scopeを持つ。すべてのtop-level `spell`、`proc`、`fn`
declaration名は、各bodyを解決する前にこのscopeへ収集するMUST。従ってsource順に
依存しないforward referenceは名前解決できる。

この規則はrecursionの実行可能性を保証しない。boundednessやterminationはtyped/static
checksの責任であり、必要なら`TerminationProofFailure`となる。

### 3.2 Declaration scope

各top-level declarationは、そのsignatureとbodyを包含するdeclaration scopeを持つ。

- type parameterは、後続type parameter constraint、value parameter type、return type、
  effect declaration、bodyのtype positionsで可視である。
- value parameterはbody全体で可視である。
- value parameterはtype parameter constraint、parameter type、return type、effect
  declarationでは可視でない。
- declaration自身のcallable名はprogram scopeから解決される。

同じlist内の順序はvisibilityを制限しない。ただし、value parameterはtype positionへ
投入できず、type parameterはvalue expressionへ投入できない。

### 3.3 Block scope

各`block`は親scopeを持つ新しいvalue scopeを作るMUST。これにはdeclaration bodyに加え、
`prepare`、`if`/`else`、各`match` arm、`repeat`、`for`、`while`、`after`、event handler
のblockが含まれる。

`let` bindingはinitializerの名前解決後に、同じblockの後続statementへ導入される。
従ってbindingは自身のinitializerでも、それより前のstatementでも可視でない。

```mir
let previous = seed;
let next = previous; // `previous` is visible
```

同一blockの外側、および兄弟blockのbindingは可視でない。

### 3.4 Construct-specific bindings

| Construct | Binding site | Visible region | Not visible in |
|---|---|---|---|
| `parameter` | parameter identifier | declaration body | signature type/effect positions、他declaration |
| `let-statement` | identifier after `let` | same blockの後続statementsとその子scope | own initializer、先行statement、block外 |
| `for-statement` | identifier after `for` | loop body block | `range-expression`、loop外 |
| `event-handler` | optional identifier after `as` | handler body block | event expression、handler外 |

`match-arm` の現行 `pattern = identifier | literal` はbinding siteではない。identifier
patternは`True`、`False`、`Indeterminate`等のcontextual semantic nameとして検査される。
現行grammarはcatch-all variable patternやdestructuring bindingを定義しない。

`repeat`、`while`、`after`、`prepare`は追加bindingを導入しない。

## 4. Shadowing and duplicates

### 4.1 Shadowing

内側のvalue scopeにあるbindingは、同じ文字列の外側value bindingをshadowしてよい。
shadowingは最も内側のscopeに限定され、scopeを出ると外側bindingが再び可視になる。

```mir
let sample = outer_source;
if condition {
    let sample = inner_source; // valid shadowing
    use(sample);               // inner binding
}
use(sample);                   // outer binding
```

value bindingはcallable、type、contextual semantic、selector/operator、registryの
namespaceをshadowしない。type parameterはdeclaration内のtype positionで同名のprovided
typeをshadowする。

### 4.2 Duplicate rejection

同じscopeかつ同じname classに同名bindingを2回導入してはならない。
static semantic validationは`DuplicateBinding`を報告するMUST。

対象には次が含まれる。

- 同名のtop-level `spell` / `proc` / `fn` の組み合わせ。
- 同一declarationの重複type parameter。
- 同一declarationの重複value parameter。
- 同一blockの重複`let`。
- construct-specific bindingと、そのbindingが導入される同一body scopeの先頭にある
  同名binding。

最後の規則により、`for item ... { let item = ...; }` と
`on each event as event { let event = ...; }` はduplicateである。さらに内側のblockを
明示すれば通常のshadowing規則を適用できる。

異なるname classの同名、または異なるscopeの同名はduplicateではない。

## 5. Lookup

### 5.1 Lexical value lookup

bare `identifier` がvalue expressionとして現れた場合、実装は現在位置から親へ向かって
value scopesを検索し、最初のbindingを選ぶMUST。

1. current block scope。
2. enclosing block scopes（最内側から外側へ）。
3. declaration parameter scope。

bindingがなければ、そのidentifierがcall targetのbaseである場合に限り、program callable
scope、次にprovided callable environmentを検索する。通常のvalue positionに暗黙の
callable valueを生成してはならない。

該当するnameがない場合は`UnresolvedName`を報告するMUST。別namespaceに同じ文字列が
存在しても、期待されるname classで解決したことにはならない。

この契約はcallableをfirst-class valueとして定義しない。calleeが複雑なexpressionで
ある場合、そのcallabilityはtyped elaborationで検査する。

### 5.2 Type lookup

type positionでは、現在のdeclarationのtype parameterを先に、provided type environment /
SemanticRegistryの適切なtype contractを次に検索する。同じ期待namespaceで解決できない
場合は`UnresolvedName`である。解決後のtype argument数、constraint、semantic kind、
dimension等はtyped elaborationで検査する。

### 5.3 Contextual and external lookup

member、effect、transfer kind/mode、invariant、identity、pattern constant、selector/operator、
registry entryは字句value lookupへfallbackしてはならない。それぞれのtyped contract、
registry namespace、selector environmentで検査する。

- registryで要求entryが存在しない場合は、`UnknownSpeciesError`、
  `ReactionUnavailable`等の既存のdomain-specific diagnosticを優先する。
- World Index queryが対象を得られない場合は`ResolutionFailure`等であり、
  `UnresolvedName`ではない。
- memberが型に存在しない、またはcallable/type contractが不適合な場合は`TypeError`
  その他のtyped diagnosticである。

## 6. Diagnostic requirements

### `DuplicateBinding`

同じscope・name classへ同名bindingを複数導入した。diagnosticは少なくともidentifier、
name class、重複したdeclaration span、先行declaration spanを示すSHOULD。

### `UnresolvedName`

識別子を、そのsyntax positionが要求するlexical、callable、またはtype namespaceで
解決できなかった。diagnosticは少なくともidentifier、期待name class、use-site spanを
示すSHOULD。

名前解決は一つのuseを一つのdeclaration identityへ対応付けるMUST。文字列だけを
Typed MIRへ持ち越し、runtimeで偶然一致するbindingを選んではならない。

## 7. EBNF to semantic restriction crosswalk

この表で「parse後」はstatic semantic validationまたはtyped elaborationで追加検査する
ことを意味する。EBNF受理だけで右列を満たしたことにはならない。

| EBNF production | Grammar permits | Additional semantic/static restriction | Typical diagnostic |
|---|---|---|---|
| `program`, `declaration` | 任意順・任意数のdeclaration | callable名を全件収集し、同名`spell`/`proc`/`fn`を拒否 | `DuplicateBinding` |
| `spell-decl`, `proc-decl`, `fn-decl` | identifier、optional generics/signature、block | declaration名をcallableへ、type/value parametersを各namespaceへ束縛。return/effect規則はdeclaration kind別に検査 | `DuplicateBinding`, `UnresolvedName`, `ReturnTypeError`, `EffectMismatch` |
| `type-params`, `type-param` | identifierとoptional identifier constraint | type parameter名は同listで一意。constraint名はtype/trait contractとして解決 | `DuplicateBinding`, `UnresolvedName`, `TypeError` |
| `parameters`, `parameter` | identifierと任意のparseable `type` | parameter名は同listで一意。type parameterとは別namespace。型は解決・検査 | `DuplicateBinding`, `UnresolvedName`, `TypeError` |
| `type`, `type-arg` | identifierとtype/integer arguments | type namespaceで解決し、arity/constraint/semantic kindを検査 | `UnresolvedName`, `TypeError` |
| `effect-decl`, `effect` | identifierとoptional type arguments | effect/registry contractで解決し、declaration bodyのeffectと照合 | `EffectError`, `EffectMismatch` |
| `block` | statement列 | 新しいlexical value scope。bindingはblock外へ漏れない | `DuplicateBinding`, `UnresolvedName` |
| `let-statement` | identifier、optional type、initializer | initializerを先に解決し、bindingは後続へ導入。same-scope duplicate拒否。annotation/inferred typeを検査 | `DuplicateBinding`, `UnresolvedName`, `TypeError` |
| `primary-expression = identifier` | 任意のidentifier token | lexical valueとして最内側から検索。call targetの場合のみcallable fallback | `UnresolvedName`, `TypeError` |
| `postfix-expression`, `call-suffix` | 任意primaryへcall suffix | resolved valueまたはcallableがcall可能で、引数contractに適合すること | `UnresolvedName`, `TypeError` |
| `member-suffix` | `.`の後の任意identifier | lexical scopeではなくreceiver typeのmemberとして検査 | `TypeError` |
| `if-statement` | expressionとbranch blocks | condition typeを検査。各branchは別scope | `TypeError`, `UnresolvedName` |
| `match-statement`, `match-arm`, `pattern` | identifierまたはliteral pattern | identifier patternはbindingではなくcontextual constant。scrutineeとの型・coverage等を検査 | `UnresolvedName`またはdomain/type diagnostic |
| `repeat-statement` | integerとblock | bound/termination要件を検査。追加bindingなし | `TerminationProofFailure` |
| `for-statement`, `range-expression` | loop identifier、任意のrange expressions、block | rangeをouter scopeで解決後、loop valueをbodyへ束縛。body内same-scope duplicate拒否 | `DuplicateBinding`, `UnresolvedName`, `TypeError` |
| `bounded-while` | expression、integer limit、block | condition typeとstatic boundを検査。追加bindingなし | `TypeError`, `TerminationProofFailure` |
| `event-handler` | event expression、optional `as` identifier、block | event expressionをouter scopeで解決後、`as` valueをhandler bodyへ束縛 | `DuplicateBinding`, `UnresolvedName`, `InvalidEventSubscription` |
| `prepare-statement`, `after-statement` | nested block | block scopeのみ導入。authority/time/runtime制約は別phase | compile/typed/runtime diagnostic |
| `selector`, `symbolic-selector`, `selector-call` | `@identifier`またはnamed selector call | lexical valueではなくselector/operator contract。runtime target existenceは保証しない | `ResolutionFailure`等 |
| `selector-argument` | optional identifier labelとexpression | labelはbindingではない。callee selector contractに対して検査 | `TypeError`またはselector diagnostic |
| `transfer-kind`, transfer/reconfigure option identifiers | 任意identifier token | expected registry/profile/contextual namespaceで検査。lexical valueへfallbackしない | `UnsupportedTransferKind`, registry/domain diagnostic |
| `identifier-list` | identifierのcomma list | 使用位置が決めるcontextual semantic namespaceで各項目を検査。variable declarationではない | registry/domain diagnostic |
| `return-statement` | optional expression | enclosing declaration kind/return typeに適合すること | `ReturnTypeError` |
| expression operator productions | grammar上のoperand combinations | precedenceはgrammar、operand type/dimension/semantic kindはtyped elaboration | `TypeError`, `DimensionError` |

## 8. Conformance

適合実装は、成功した各lexical/type/callable useについてdeclaration identityを保持するか、
同等に一意な参照関係を構築するMUST。失敗時は上記のstageとdiagnostic classを維持する
MUST。

この文書が定義しないprovided callable/type/selector/registry entry集合は、
implementationまたはprofileが文書化する。集合の内容が未定義であっても、scope順序、
namespace分離、duplicate rejection、phase separationを変更してはならない。
