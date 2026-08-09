# Package Resource Contract — post-v0.10 stabilization

**Status:** normative reference-implementation distribution/resource contract for standalone wheel and sdist execution; it does not change language, evaluator, runtime, or SemanticFingerprint semantics.

## Purpose

このreferenceは、source checkoutではrepository-root resourceを使い、standalone wheel/sdist installationではpackage-owned immutable bundleを使うためのownership、lookup、build、failure contractを定義する。

Issue #60以前のreference implementationは`schemas/`や`examples/`をcheckout-relative pathで参照していた。その構成はeditable installでは動作するが、standalone wheelへcanonical resourcesが含まれる保証を持たなかった。本contractはそのRelease Guarantee gapを閉じる。

## Non-goals

- repository-root canonical filesとは別の、手編集可能な第二の仕様正本を作らない。
- resource packagingによってSemanticFingerprint、artifact content hash、compatibility、authority、Lease、conservation、runtime execution semanticsを変更しない。
- normative resourcesをnetworkから取得しない。
- arbitrary zip importer、remote filesystem、production deployment layoutを一般保証しない。
- wheel/sdist内のresource copyをauthoring sourceとして参照・編集しない。

## Depends on

- [`scope-and-ownership.md`](scope-and-ownership.md)
- [`conformance.md`](conformance.md)
- [`machine-values.md`](machine-values.md)
- [`compatibility.md`](compatibility.md)
- root `pyproject.toml`
- root `MANIFEST.in`

## Key invariants

```text
repository-root canonical resource != generated distribution copy
build-time bundle != second semantic truth
source checkout lookup != cwd-relative lookup
missing package resource != fallback to unrelated checkout/cwd file
package resource handling != SemanticFingerprint/content-hash semantics
editable-install success != standalone artifact proof
wheel/sdist execution != implicit network fetch
```

## 1. Canonical ownership

Tracked canonical sources remain in repository-root paths, including:

```text
schemas/
examples/
reference/
conformance/
grammar/
data/
tests/
planning/
spec/
README.md
CHANGELOG.md
TODO.md
PROJECT_HANDOFF.md
requirements-dev.txt
```

`magical_language_spec_resources/` contains only its tracked package marker. Reviewed root resources are copied below that package **during wheel build only**. Generated copies MUST NOT be committed or manually maintained as an independent source.

The build MUST fail rather than overwrite pre-existing generated paths. Build completion or failure MUST clean generated copies from the source tree.

```text
tracked root files = authoring source
build-generated bundle = immutable distribution projection
```

## 2. Resource root selection

The reference implementation exposes one shared locator through `src.resources`.

### Source/editable execution

A source root is accepted only when it is a verified project checkout:

- `pyproject.toml` exists;
- project name is `magical-language-spec-reference`;
- required canonical directories exist.

The selected root derives from the installed module location, not the process current working directory.

### Standalone installed execution

When the module is not running from a verified checkout, the locator selects the installed `magical_language_spec_resources` package through `importlib.resources`.

The installed bundle MUST contain all required directories. An incomplete or unavailable bundle fails closed. The current supported artifact contract assumes a standard unpacked wheel/sdist installation that exposes package resources as filesystem paths.

```text
verified source checkout
OR
verified installed resource bundle
```

No third search path, parent-directory scan, cwd fallback, or network fallback is permitted.

## 3. Path and failure contract

`resource_path(relative)` accepts only a path below the selected root.

It MUST reject:

- absolute paths;
- parent traversal using `..`;
- paths that resolve outside the selected root;
- missing required files/directories.

Stable fatal diagnostics are:

```text
ReferenceResourceBundleUnavailable
ReferenceResourceFilesystemUnavailable
ReferenceResourceBundleIncomplete
ReferenceResourcePathInvalid
ReferenceResourceMissing
```

A missing installed resource MUST NOT silently resolve to an unrelated repository checkout, current working directory, or user-provided filesystem location.

## 4. Build contract

The project uses an in-tree PEP 517 backend wrapper:

```text
build-backend = "backend"
backend-path = ["_custom_build"]
```

For direct wheel builds, the wrapper:

1. validates all canonical source inputs;
2. refuses pre-existing generated resource paths;
3. copies reviewed root resources into `magical_language_spec_resources`;
4. delegates wheel construction to `setuptools.build_meta`;
5. removes generated copies in `finally`.

The sdist includes the canonical root inputs and the in-tree backend. Building/installing that sdist therefore constructs a wheel using the same bundle-generation contract rather than a separately maintained archive layout.

`MANIFEST.in` and `pyproject.toml` are distribution metadata, not semantic definition sources.

## 5. Installed entry points

The installed reference commands remain:

```text
magical-language-evaluator
magical-language-conformance
```

Evaluator/runtime schema lookup, canonical fixtures, Latin adapter defaults, and installed conformance execution MUST use the shared resource locator for their default resources.

Repository-local scripts may retain direct source-checkout behavior when executed explicitly from the checkout, but installed commands MUST NOT depend on repository layout or current working directory.

## 6. Artifact validation

Release/stabilization CI MUST build both:

```text
wheel
sdist
```

Each artifact is installed in a fresh isolated virtual environment and executed outside the repository checkout. Validation covers at least:

- `Core-1.0` conformance;
- `Runtime-1.0` conformance;
- Latin evaluator ingress;
- canonical evaluator → sandbox runtime execution;
- expected committed world revision;
- installed root is package-owned and does not leak back to checkout;
- deliberate bundled-resource removal produces `ReferenceResourceMissing`;
- build leaves no generated resource copy in the source tree.

Passing only editable-install smoke is insufficient evidence for this contract.

## 7. Semantic and compatibility boundary

Packaging is a transport/distribution concern. It MUST NOT:

- change canonical JSON bytes or SemanticFingerprint projection rules;
- treat bundle path/location as semantic identity;
- infer artifact compatibility from filesystem equality;
- grant Capability, Lease, authority, or trust;
- alter evaluator or runtime outcomes for identical canonical resources.

```text
same canonical resource content through a different installation layout
!= semantic change
```

Issue #60 closes the known standalone package-resource blocker. Issue #40 still owns the complete v1.0 Release Guarantee and the other four readiness gates; resolving this contract alone does not make v1.0 RC ready.
