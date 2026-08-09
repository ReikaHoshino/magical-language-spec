# MIR Name Resolution Examples

These focused fixtures accompany `reference/mir-name-resolution.md`. `ACCEPT` and `REJECT`
describe static name-resolution results after successful parsing; they do not claim that every
example passes later type, effect, feasibility, or runtime checks.

## Positive fixtures

### `ACCEPT: nested-shadowing`

```mir
fn choose(source : Ref<Region>) -> Ref<Region> {
    let selected = source;
    if condition {
        let selected = fallback;
        consume(selected);
    }
    return selected;
}
```

- The inner `selected` denotes the inner `let`.
- The returned `selected` denotes the outer `let`.
- `source` is visible throughout the function body.
- `condition`, `fallback`, and `consume` are assumed to be provided bindings/callables; their
  contracts are checked separately.

### `ACCEPT: initializer-uses-outer-binding`

```mir
fn convert(input : Energy) -> Energy {
    let value = input;
    if condition {
        let value = transform(value);
        return value;
    }
    return value;
}
```

The inner initializer's `value` denotes the outer binding because the inner binding is introduced
only after its initializer has been resolved.

### `ACCEPT: construct-binding-regions`

```mir
proc watch(events : EventStream) ! { Read } {
    for event in events {
        inspect(event);
    }

    on each next_event(events) as event {
        inspect(event);
    }
}
```

The two `event` bindings occupy distinct sibling body scopes. The `for` binding is not visible in
`events`; the handler binding is not visible in `next_event(events)`.

### `ACCEPT: separate-namespaces`

```mir
fn identity<Energy>(Energy : Energy) -> Energy {
    return Energy;
}
```

The type parameter `Energy` and value parameter `Energy` are distinct bindings. Type positions
denote the type parameter; the return expression denotes the value parameter. This fixture only
tests name classes, not whether shadowing a provided type is advisable.

### `ACCEPT: match-identifier-is-not-a-binding`

```mir
fn classify(value : Truth) {
    match value {
        True => {
            accept();
        }
        False => {
            reject();
        }
        Indeterminate => {
            defer();
        }
    }
}
```

`True`, `False`, and `Indeterminate` are contextual semantic names. They do not bind catch-all
variables.

## Negative fixtures

### `REJECT DuplicateBinding: duplicate-parameters`

```mir
fn invalid(value : Energy, value : Energy) {
    return;
}
```

Both parameters attempt to bind `value` in the same declaration value scope.

### `REJECT DuplicateBinding: duplicate-let`

```mir
fn invalid(input : Energy) {
    let result = input;
    let result = input;
}
```

Both `let` statements introduce `result` into the same block.

### `REJECT UnresolvedName: self-reference-in-initializer`

```mir
fn invalid(input : Energy) {
    let result = result;
}
```

The new `result` is not visible in its own initializer. No outer `result` is provided.

### `REJECT UnresolvedName: loop-binding-in-range`

```mir
fn invalid(end : Integer) {
    for index in index..end {
        consume(index);
    }
}
```

The loop binding is visible only in the body, not in its range expression.

### `REJECT UnresolvedName: block-local-escape`

```mir
fn invalid(input : Energy) -> Energy {
    if condition {
        let local = input;
    }
    return local;
}
```

`local` is not visible outside the `if` block.

### `REJECT DuplicateBinding: construct-body`

```mir
proc invalid(events : EventStream) ! { Read } {
    on each next_event(events) as event {
        let event = next_event(events);
    }
}
```

The handler binding and `let` attempt to bind `event` in the same handler body scope. An additional
nested block would permit ordinary shadowing.

## Parse acceptance is not semantic validity

The following source is parseable under `grammar/mir.ebnf`, but it fails after parsing:

```mir
fn invalid(value : MissingType) {
    let output = missing_input;
    return;
}
```

- `MissingType` produces `UnresolvedName` in the type namespace if no provided type has that name.
- `missing_input` produces `UnresolvedName` in the value namespace.
- A parser that constructs an AST before reporting these diagnostics is conforming.

Conversely, resolving all names does not prove that operator operands, dimensions, effects,
authority, registry contracts, or runtime selector results are valid.
