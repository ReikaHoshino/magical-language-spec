# Conformance Reference — v1.0.0-rc.1

**Status:** normative released v1.0 RC conformance contract. public Issue #2 freezes the four required classes and 65 required cases at `v1.0.0-rc.1`; experimental inventories remain excluded.

## Purpose

このreferenceは、実装が「tests passed」と主張するだけでstable core適合を名乗ることを防ぎ、versioned conformance class、stable case ID、normative rule ownership、fixture/test evidence、blocked stateをmachine-readableに結び付ける。

v1.0.0-rc.1がreleaseするclassは:

```text
Core-1.0
Evaluator-1.0
Adapter-lat-1.0
Runtime-1.0
```

である。

machine-readable正本は:

- `schemas/conformance-manifest.schema.json`
- `conformance/manifest.json`

reference runnerは:

```text
python tools/run_conformance.py
```

とする。

## Non-goals

- 全repository unittestをstable public guaranteeへ自動昇格しない。
- implementation outputからexpected resultを自動生成しない。
- test coverage率だけでsemantic completenessを証明しない。
- blocked/provisional classをflag一つでstableへ昇格しない。
- implementation-specific scheduler microstep、solver substep、storage layoutをRuntime-1.0へ固定しない。
- public serialized ECIRをRuntime-1.0要件にしない。
- v0.12 landingだけを理由にv1.0 RC eligibilityを宣言しない。

## Key invariants

```text
repository test != conformance case merely by existing
stable case ID != test method name
implementation output != conformance truth
schema-valid manifest != class pass
blocked class != conformant class
provisional measurement != required conformance pass
rule reference != duplicate normative definition
compatibility admission != authority grant
Runtime-1.0 semantics != runtime microstep representation
Kernel interaction class != MKI primitive
```

## 1. ConformanceManifest

`ConformanceManifest`はsuite、class、caseのversioned mappingを持つ。

```text
ConformanceManifest {
    suite
    classes[]
    cases[]
}
```

manifestは少なくとも次を保証するMUST:

- stable case IDが一意。
- class IDが一意。
- required caseが実在し、そのclassを明示。
- released/candidate classはprovisional caseをrequiredにしない。
- blocked classはblocking dependencyを明示。
- rule referenceのdocument/headingがcurrent referenceに実在。
- executable caseが参照するtest/fixtureが実在。

JSON Schemaだけで表現できないcross-file/cross-record invariantはreference runnerが検証する。

## 2. Stable conformance case ID

case IDはtest method名から独立したstable project identityである。

例:

```text
WB-TEST-006
CORE-COMPAT-001
EVAL-AUTH-001
ADAPTER-LAT-AMBIG-001
RUNTIME-PREPARE-001
RUNTIME-KERNEL-ATOMIC-001
```

規則:

1. 同じsemantic obligationをtest refactorだけで別IDへrenumberしない SHOULD。
2. 既存stable IDの意味を別obligationへ再利用してはならない MUST NOT。
3. semantic contractがmaterialに変わり旧expected semanticsを維持できない場合、新IDまたは明示migrationを用いる MUST。
4. `WB-TEST-*`等の既存stable canonical IDは同じ意味なら再利用する SHOULD。
5. test method/fileはimplementation evidence locatorでありcase identityではない。

## 3. Normative rule reference

各caseは少なくとも一つのcurrent normative document/headingを参照する。

```text
rule_ref {
    document
    heading
}
```

この参照はownership locatorであり、manifest側へnormative proseを複製するものではない。

```text
rule reference != second specification source
```

headingが削除・移動された場合、manifestも更新してintentional migrationを示す。存在しないrule ownerはfail closed。

## 4. Class lifecycle

class status:

```text
released
candidate
blocked
```

### released

owning release gateがexact required surface、normative owner、expected truth、package path、
fail-closed boundaryを凍結し、required casesをwaiverなしで通過した状態。released classへcaseを追加・削除・
再解釈するにはversioning-and-migration contractに従う新しいrelease actionを要求する。

### candidate

release candidateとしてrequired surfaceを定義できる。class passには:

- manifest/schema/integrity validation成功。
- classが`blocked`でない。
- required caseすべて成功。
- required rule/test/fixture ownerが欠落していない。

を要求する。

### blocked

semantic dependencyまたはrelease-critical ownerが未確定で、stable class definitionを宣言できない状態。

blocked classの既存testを測定目的で実行してもよいが:

```text
blocked baseline all green != class conformance
```

reference runnerの`--include-blocked`は測定専用でありstatusを変更しない。

pre-public archive Issue #55はpre-public archive PR #57で解決済みであり、public Issue #2のRC gateで
`Core-1.0 / Evaluator-1.0 / Adapter-lat-1.0 / Runtime-1.0`を`released`へ移行した。
将来別dependencyでclassがblockedになった場合も上記lifecycleを使う。

## 5. Initial class definitions

### Core-1.0

stable-core semanticsの候補surface。少なくとも:

- representation/layer separation;
- MKI six-operation boundary;
- type/dimension/value boundaries;
- identity/authority/ownership separation;
- Unknown / Estimate / PlanningAssumption separation;
- SemanticFingerprint boundary;
- compatibility decision/admission boundary;
- required conservation/accounting and fail-closed ownership rules;

を対象とする。

production storage algorithm、全domain model、formal proof engineはclass breadthそのものではない。

### Evaluator-1.0

v0.8から継承するsupported evaluator surface:

- explicit Latin source ingress;
- schema-valid NSR ingress;
- internal later stages are not public direct ingress;
- semantic type / SI dimension validation;
- read-only resolution/registry evidence;
- Unknown/planning/estimation separation;
- mandatory authority/Lease/conservation assessment;
- deterministic validated FeasibilityReport;
- no authoritative COMMIT/world mutation;

をrequired released RC surfaceとする。

### Adapter-lat-1.0

reference `LanguageAdapter<lat>` supported surface:

- common source normalization boundary;
- explicit adapter identity/dispatch;
- lexicon/morphology/frame evidence;
- deterministic candidate/NSR generation for supported corpus;
- ambiguity preservation/policy behavior;
- no automatic language detection;
- lexical proposal != identity/authority;

を対象とする。

### Runtime-1.0

v0.9 runtimeから発展し、v1.0.0-rc.1でreleaseされたstable runtime surfaceである。

pre-public archive Issue #55 / pre-public archive PR #57でWorld Kernel lower semantic execution boundary、active-effect semantic ownership、`KernelAtomicGroup`、COMMIT/lifecycle distinctionが確定したため、本classはそれらをrequired surfaceへ含める。

少なくとも:

- PREPARE non-mutation;
- current-state/Capability/Lease/accounting/profile revalidation;
- control-plane COMMIT / ABORT;
- exact six MKI public semantic ABI;
- scheduler/time/integrator separation;
- sandbox limits/emergency-stop semantics;
- deterministic replay/divergence;
- five World Kernel interaction classes `QUERY / SAMPLE / TRANSITION / ACTIVATE / DEACTIVATE`;
- authoritative active-effect semantic projection;
- KernelAtomicGroup all-or-none semantics;
- non-zero Transit accounting/lifecycle;
- continuous model vs integrator separation;
- bounded Controller future-actuation revalidation;
- DEACTIVATE/emergency stop is settlement/termination, not rollback;

をrequired released RC surfaceとする。

Runtime-1.0はpublic serialized ECIR、one storage layout、solver microsteps、高性能parallel schedulerをrequired stable surfaceにしない。

## 6. Expected semantics ownership

conformance fixture/test expected resultはSpecification/conformance-owned evidenceである。

実装を実行して得たoutputを無審査でexpected fixtureへcopyしてはならない。

```text
implementation output -> human/spec review -> conformance expectation
```

であり:

```text
implementation output -> expected truth
```

ではない。

既存canonical fixtureはそのownershipを維持し、manifestはlocatorとして再利用する。

## 7. Deterministic runner

reference runnerは:

- manifest schema/integrityを先にvalidate;
- selected class/caseをstable ID順に実行;
- required testのskipをpassとして扱わない;
- blocked classの通常実行を拒否;
- explicit measurement時もblocked statusを保持;
- failureをstable case IDで報告;

する。

runnerはrepository unittest discoveryを置換しない。repository regressionとconformance suiteは目的が異なる。

```text
repository regression = implementation regression breadth
conformance runner     = promised semantic/class surface
```

release gateでは両方を使う。

## 8. Compatibility admission

各domainのcompatibility判定は引き続き`compatibility.md`のowning profileが生成する。

reference aggregate admissionはそのdecisionを再計算せず、required domainごとにexplicit resultを消費する。

```text
all required = Compatible   -> Allowed
any required = Incompatible -> Denied
required missing/Undetermined -> Indeterminate (not admitted)
```

`Incompatible`と`Undetermined`は区別を維持する。

profile-owned negotiation/fallbackが存在する場合、その結果をdomain decisionとして明示した後にaggregate gateへ渡す。aggregate gate自身がrevision/hash/tagからcompatibilityを推測しない。

```text
CompatibilityAdmission != Capability
CompatibilityAdmission != Lease
CompatibilityAdmission != trust proof
```

reference implementationは`src.compatibility.admit_compatibility_decisions`。

v0.12ではrequired reference pathが消費するartifact/profile coverageを
`conformance/compatibility-coverage.json`へversionedに列挙する。inventoryはdomain/profile ownerを
指し示すだけで、互換性resultを再計算しない。

pre-public archive Issue #64のrelease evolution/deprecation/migration rulesはCore-1.0 required stable casesへ昇格する。
exact migrationはtarget schema validationとtarget profile compatibility re-evaluationを要求し、
Capability、Lease、authority、trust、semantic proof、admissionを生成しない。

## 9. Clean-environment execution

v1.0.0-rc.1 release gateの最低source-checkout reference path:

```text
python -m pip install --requirement requirements-dev.txt
python tests/validate_schemas.py
python tools/run_conformance.py
python -m unittest discover -s tests -v
```

加えて、editable package pathをCIで検証する:

```text
python -m pip install --editable .
magical-language-conformance
magical-language-evaluator --source "Calorem ab aqua ad aerem transfer." --lang lat --format json --level report
```

installed entry point smokeはrepository外cwdから実行し、current canonical resource lookupがcwd依存でないことを確認する。

このpathはproduction deploymentを意味しない。pre-public archive Issue #60 / pre-public archive PR #62で追加したsingle-authoring-source
resource projectionにより、v1.0.0-rc.1 release gateはeditable installに加えisolated wheel/sdist installed
executionも検証する。historical v0.10 snapshotの限定保証は遡及変更しない。

release PRでは`git diff --check`も実施する。

## 10. Traceability and gap handling

manifestにrequired rule/caseを追加する際、ruleにexecutable conformance caseが存在しない場合は:

- caseを追加する;
- またはclass breadth外/deferred/non-executableである理由を明示する。

暗黙にcoverage済みとみなしてはならない。

v0.12もrepository内の全testを無差別にpublic guaranteeへ昇格しない。代わりに
`conformance/v1-required-surface.json`がpre-public archive Issue #38から継承してpublic Issue #2がreleaseする14 required conformance claimを列挙し、各claimを
stable required case IDへmappingする。matrix caseはmanifestでrequiredであり、owning classの
`required_case_ids`へ含まれ、reverse rule coverageを持たなければならない。

v0.12でpromoteする追加surfaceは、common source normalization、ContextualDeterministic /
LegacyPermissive ambiguity trace、planning binding/generation/minimum-Energy selection、complete
`WB-TEST-001..011`、canonical evaluator path、six-operation runtime execution、resource ceiling、
PrepareBound vs Dynamic runtime behaviorである。これはpre-public archive Issue #38 required promiseのfreezeであり、
non-reference adapter、production storage/distributed runtime、public ECIR等のexplicit non-goalを
requiredへ昇格しない。

## 11. v1.0 readiness boundary

4 classのcomplete required matrixはv0.12でcandidate evidenceを獲得し、renewed public Issue #1 auditのGOと
public Issue #2 release gateを経てv1.0.0-rc.1でreleasedとなる。

v1.0 RC eligibilityには別途:

- Core Semantics Stable;
- Reference Implementation Stable;
- Compatibility Guarantee Ready;
- Conformance Guarantee Ready;
- Release Guarantee Ready;

の全gateをpre-public archive Issue #40がcertifyする必要がある。v0.12はGate 4 evidenceを所有し、pre-public archive Issue #72はexact
post-v0.12 `main`でGate 5のno-waiver rehearsalをPASSした。pre-public archive Issue #72 / pre-public archive PR #75はlanding済みで、pre-public archive Issue #38のv1.0 RC entryはREADY。
