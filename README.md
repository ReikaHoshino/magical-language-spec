# Magical Language Specification

魔法を「世界状態に対する型付き・権限付きプログラム」として記述するための架空言語仕様です。

このリポジトリは **魔術言語仕様 v0.1〜v1.0.0-rc.1**、current `reference/`、machine-readable contracts、reference implementation、versioned conformance suiteを追跡します。

このrepositoryは2026-08-09に、公開用のclean historyへ移行しました。current workはこのpublic repositoryのIssueとPRで追跡します。current document内のtracker参照は`public Issue/PR #N`または`pre-public archive Issue/PR #N`としてnamespaceを明示します。active release trainは [public Issue #1 audit](https://github.com/ReikaHoshino/magical-language-spec/issues/1) → [public Issue #2 RC](https://github.com/ReikaHoshino/magical-language-spec/issues/2) → [public Issue #3 final](https://github.com/ReikaHoshino/magical-language-spec/issues/3) → [public Issue #4 umbrella](https://github.com/ReikaHoshino/magical-language-spec/issues/4) です。

## 現行版

**v1.0.0-rc.1 — Release Candidate 1**

v1.0.0-rc.1はpublic Issue #1のrenewed no-waiver auditとpublic Issue #2のrelease gateを経て、complete v1.0-required conformance surfaceを凍結する最初のrelease candidateです。4 class / 65 required case / 14 required claim、six MKI operations、five World Kernel interaction classesを維持します。

```text
Core-1.0
Evaluator-1.0
Adapter-lat-1.0
Runtime-1.0
```

各classはstable case ID、current normative rule owner、fixture/test evidence、required/deferred breadthを`conformance/manifest.json`で明示します。required compatibility domain/profile inventoryは`conformance/compatibility-coverage.json`、14 required conformance claimは`conformance/v1-required-surface.json`が所有します。

```text
implementation test passing
!= conformance claim by itself

stable case ID
!= Python test method name
```

`Runtime-1.0`はpre-public archive Issue #55 / pre-public archive PR #57で確定したWorld Kernel lower semantic boundaryを含みます。

```text
MKI public semantic ABI = 6 operations

lower World Kernel classes =
  QUERY / SAMPLE / TRANSITION / ACTIVATE / DEACTIVATE
```

lower interaction classは新MKI primitiveでも、public ECIR serializationでも、solver/integrator microstepでもありません。

### v1.0 RC preserved boundaries

```text
Evaluation != Execution
PREPARE success != COMMIT permission
Estimate != Reservation
Feasibility != Authority grant
WorldIndex != WorldState
Visibility != Authority
Registry metadata != Capability
Physical time != runtime tick
Integrator approximation != physical law
DeterministicReplay != Rewind
SemanticFingerprint != artifact content_hash
CompatibilityAdmission != Capability
release version != compatibility oracle
migration success != admission
control-plane COMMIT != all future consequences already occurred
DEACTIVATE != rollback
```

v1.0.0-rc.1はfinal v1.0.0ではありません。RCではcore breaking changeを計画せず、blocker fix、conformance/compatibility/migration correction、documentation、release engineeringだけを原則とします。final releaseはpublic Issue #3が所有し、RCでmaterial semantic redesignが必要と判明した場合は新しいv0.x stabilizationへ戻ります。

## Reference implementation / conformanceを使う

clean checkoutでのvalidation dependency:

```text
python -m pip install -r requirements-dev.txt
```

editable reference package:

```text
python -m pip install --editable .
```

Conformance suite:

```text
magical-language-conformance
magical-language-conformance --class Core-1.0
magical-language-conformance --class Runtime-1.0
```

Experimental success-path suite（v1.0 required count外）:

```text
magical-language-experimental-arcana
python tools/run_success_arcana.py
magical-language-spell-instances
magical-language-artifact check /path/to/instance.json
magical-language-artifact eval /path/to/instance.json
magical-language-artifact run /path/to/instance.json
```

`SUCCESS-ARCANA-001..008`は`Experimental-Arcana-0`であり、stable required
`conformance/manifest.json`とは分離されます。ownerは
[`reference/success-arcana.md`](reference/success-arcana.md)です。

汎用single-file ingressのownerは
[`reference/spell-instance-bundles.md`](reference/spell-instance-bundles.md)です。
SA-001..008、DEBUG-HELL-001..003、non-suite genericity caseは同じ
`SpellInstanceBundle` schema/registry/CLIを通り、stable required countを変更しません。


Experimental unified user workflow（v1.0 stable direct-entry count外）:

```text
magical-language check examples/mgls/independent-transition.mgls
magical-language eval examples/mgls/independent-transition.mgls
magical-language run examples/mgls/independent-transition.mgls
magical-language compile examples/mgls/independent-transition.mgls \
  --emit-program /tmp/transition.program.mga.json \
  --emit-source-map /tmp/transition.source-map.mga.json
magical-language run /tmp/transition.program.mga.json
magical-language run examples/spell-instances/generic/GENERIC-001.json
```

このcommandは`.mgls`、decoded `MagicalProgram-0`、decoded
`SpellInstanceBundle-0`を一つのdeterministic JSON envelopeで扱います。filename/suffixはdecoder hintと
一致検査だけに用い、contract/runtime dispatchには使いません。compiler成功、target admission、
evaluation、PREPARE/COMMIT、replayは別の境界です。詳細ownerは
[`reference/user-workflow.md`](reference/user-workflow.md)、experimental evidenceは
[`conformance/experimental-user-workflow.json`](conformance/experimental-user-workflow.json)です。

`magical-language-evaluator`、`magical-language-conformance`、`magical-language-artifact`等の既存
entry pointは維持されます。`magical-language`はpackage version `1.0.0rc1`上のexperimental additive
surfaceであり、stable 4 class / 65 caseやv0.8 public direct-entry contractを変更しません。

repository-local equivalent:

```text
python tools/run_conformance.py
```

v0.8 evaluator — Latin source:

```text
magical-language-evaluator \
  --source "Calorem ab aqua ad aerem transfer." \
  --lang lat \
  --format human \
  --level report
```

または:

```text
python -m src.evaluator \
  --source "Calorem ab aqua ad aerem transfer." \
  --lang lat \
  --format human \
  --level report
```

v0.8 evaluator — NSR JSON:

```text
python -m src.evaluator \
  --nsr path/to/nsr.json \
  --format json \
  --level report
```

v0.9 sandbox runtimeはv0.8 reportを消費します。

```python
import json
from pathlib import Path

from src.evaluator import LocalEvaluator
from src.runtime import ReferenceRuntimeEngine, canonical_sandbox_world

pipeline = json.loads(
    Path("examples/canonical-water-ball/pipeline.json").read_text(encoding="utf-8")
)
report = LocalEvaluator().evaluate_nsr(pipeline["normalization"]["nsr"])
world = canonical_sandbox_world()
trace = ReferenceRuntimeEngine().execute_strict(report, world)
```

v0.10 release時点のpackaging guaranteeは**clean checkout + declared dependencies / editable install**でした。post-v0.10 pre-public archive Issue #60 / pre-public archive PR #62では、single authoring sourceを維持したpackage-owned projectionとisolated editable/wheel/sdist smokeをcurrent reference implementationへ追加済みです。これはhistorical v0.10 snapshotの保証を遡及変更せず、pre-public archive Issue #40の全readiness gate完了も意味しません。

## 最初に読むもの

1. [`reference/scope-and-ownership.md`](reference/scope-and-ownership.md) — 保証範囲・DefinitionSource・未決定事項のowner。
2. [`reference/conventions.md`](reference/conventions.md) — 規範語彙。
3. [`reference/architecture.md`](reference/architecture.md) — 全体構造。
4. [`reference/language-adapters.md`](reference/language-adapters.md) — 多言語frontend / NSR。
5. [`reference/mir-name-resolution.md`](reference/mir-name-resolution.md) — MIR scope / name resolution。
6. [`reference/registry.md`](reference/registry.md) — SemanticRegistry contract。
7. [`reference/machine-values.md`](reference/machine-values.md) — common JSON value / hash boundary。
8. [`reference/compatibility.md`](reference/compatibility.md) — domain-owned compatibility decision。
9. [`reference/versioning-and-migration.md`](reference/versioning-and-migration.md) — v1.x stable scope / deprecation / exact migration boundary。
10. [`reference/world-index.md`](reference/world-index.md) — RESOLVE database contract。
11. [`reference/runtime-time.md`](reference/runtime-time.md) — tick/scheduler/replay。
12. [`reference/temporal-causality.md`](reference/temporal-causality.md) — historical access / Restore / Rewind / causal authority。
13. [`reference/security-sandbox.md`](reference/security-sandbox.md) — sandbox / emergency stop / threat boundary。
14. [`reference/planning-inference.md`](reference/planning-inference.md) — Unknown / Estimate / PlanningAssumption / generation planning。
15. [`reference/estimator-models.md`](reference/estimator-models.md) — Energy/resource/timing model ownership。
16. [`reference/feasibility.md`](reference/feasibility.md) — dry-run evaluator contract。
17. [`reference/evaluator-implementation.md`](reference/evaluator-implementation.md) — v0.8 reference evaluator profile。
18. [`reference/runtime-implementation.md`](reference/runtime-implementation.md) — v0.9 sandbox runtime profile。
19. [`reference/kernel-execution.md`](reference/kernel-execution.md) — World Kernel lower semantic execution boundary。
20. [`reference/conformance.md`](reference/conformance.md) — v0.12 conformance class / stable case / lifecycle contract。
21. [`reference/canonical-water-ball.md`](reference/canonical-water-ball.md) — 全pipeline conformance path。
22. [`reference/terminology.md`](reference/terminology.md) — 術語索引。
23. [`reference/user-workflow.md`](reference/user-workflow.md) — experimental MGLS / MagicalProgram / bundle user workflow。
23. [`CHANGELOG.md`](CHANGELOG.md) — release差分。
24. [`SECURITY.md`](SECURITY.md) — vulnerability reportingとpublic disclosure policy。

> `spec/` はimmutable historical snapshot、`reference/` はcurrent live referenceです。

## 現行pipeline

```text
Natural Language Source
 lat / lzh / ger / jpn / eng / zho / ...
        ↓ LanguageAdapter<L>
SurfaceAnalysis<L>
        ↓ normalization
NormalizationCandidateSet
        ↓ AmbiguityPolicy
NSR
        ↓ deterministic semantic validation
SemanticAST
        ↓ typed elaboration
TypedMIR
        ↓ static checks / SemanticRegistry
Resolver / WorldIndex → candidate evidence
        ↓
Feasibility Evaluator / PREPARE planning
        ↓
KernelPlan / PreparedPlan
        ├─ dry-run → FeasibilityReport → STOP
        └─ sandbox execution
             ↓ Revalidate → control-plane COMMIT(initial atomic group)
             ↓ six MKI operations
             ↓ World Kernel semantic interactions
             ↓ scheduler / admitted models / integrator approximation
             ↓
             Σ + H + Ω + P
```

v0.8.0がdry-run evaluator、v0.9.0がsupported sandbox execution、v0.10.0がconformance harness、v0.11.0がversioned compatibility guarantee evidence、v0.12.0がcomplete v1.0 candidate conformance matrix、v1.0.0-rc.1がfrozen RC surfaceを追加します。

## Language Adapter priority

```text
1 lat  Latin
2 lzh  Literary / Classical Chinese
3 ger  German
4 jpn  Japanese
5 eng  English
6 zho  Modern Chinese
```

これらはproject adapter IDです。ISO/BCP47等のexternal tagはmetadata mappingとして扱います。

source→NSR conformanceを持つreference adapterは現時点で`lat`だけです。canonical water-ballのEnglish surfaceはprovenance evidenceであり、`eng` adapter実装済みの主張ではありません。

## NSR / SemanticFingerprint

```text
Language-specific parse != NSR
NSR != SemanticAST
SemanticAST != TypedMIR
```

SemanticFingerprint V1:

```text
SemanticFingerprintV1(NSR)
  = SHA-256(UTF-8(JCS(CanonicalSemanticProjectionV1(NSR))))

sf:v1:sha256:<64 lowercase hexadecimal digits>
```

```text
SemanticFingerprint != artifact content_hash
Unknown != omitted
Unknown != null
null != omitted
```

参照ツールは [`tools/semantic_fingerprint.py`](tools/semantic_fingerprint.py)、fixtureは [`examples/semantic-fingerprint/`](examples/semantic-fingerprint/) にあります。

## AI normalization / ambiguity

AIはoptional candidate providerでありsemantic authorityではありません。

```text
AI proposal != semantic truth
Confidence != proof
```

```text
AmbiguityPolicy =
    StrictReject
  | InteractiveResolve
  | ContextualDeterministic
  | LegacyPermissive
```

`LegacyPermissive`でもmandatory type/authority/conservation/identity checksは回避しません。

```text
Unexpected result != undefined behavior
```

## Planning inference / evaluator

```text
Unknown
!= Estimate
!= PlanningAssumption
!= observed/authoritative truth
```

v0.8 evaluatorはsource/NSR Unknownを書き換えず、許可された場合だけ別のprovenance-bearing `PlanningAssumption`を採用します。

Evaluatorはworldへ作用せず、Surface / NSR / SemanticAST / TypedMIR / KernelPlan、Energy/resource/timing estimates、Selector/WorldIndex evidence、SemanticRegistry evidence、Capability/Lease/conservation/identity obligations、planning assumptions、diagnosticsをFeasibilityReportへまとめます。

## Sandboxed Runtime / World Kernel

reference runtime configuration:

```text
C = <Σ,H,Ω,P>
```

PREPAREはreversible `PreparedPlan`とreservation intentを作り、authoritative Σ/Hを変更しません。COMMIT直前にworld/state revision、RuntimeProfile、Capability、Lease、conservation、stop fenceを再検証します。

World Kernel lower semantic classes:

```text
QUERY
SAMPLE
TRANSITION
ACTIVATE
DEACTIVATE
```

causally relevant persistent Transit / Channel / Controller / Dynamics semanticsはauthoritative WorldState/world-evolution projectionを持ちます。Ωはruntime realization/bookkeepingを保持できますが、future world semanticsの唯一のopaque ownerにはなりません。

`KernelAtomicGroup`はmandatory guard failure時にpartial authoritative transition/activationを残しません。

## Scheduler / Integrator / Replay

canonical logical scheduler phases:

```text
Ingress
ContinuousAdvance
Revalidate
Commit
PublishSnapshot
Control
IndexUpdate
Dispatch
```

```text
Physical time != runtime tick
Integrator approximation != physical law
DeterministicReplay != Rewind
```

continuous RECONFIGUREのmodel semanticsとnumerical integrationは分離されます。solver/integrator substepをworld ontologyや新primitiveとして扱いません。

## Canonical water-ball

WB-CANON-001はv0.8 evaluator、v0.9 runtime、v0.10+ conformanceのcanonical pathです。

```text
material             water
mass                 50 kg
radius               0.01 m
distance             3 m
initial velocity     0 m/s
acceleration         50 m/s^2
trajectory           horizontal-forward
terminal             Unknown(MissingArgument)
```

canonical selected plan `wb:plan:transfer-reconfigure`、synthetic estimator total `200 J`、sandbox COMMITは`world:991 → world:992` / `event:wb-canon-001`です。

horizontal trajectoryはgravityを削除せず`CONSTRAIN` controllerとして扱います。

## MKI

Data planeは6 primitiveだけです。

```text
RESOLVE
OBSERVE
CHANNEL
TRANSFER
RECONFIGURE
CONSTRAIN
```

Control plane specification:

```text
ACQUIRE
RELEASE
COMMIT
ABORT
REVOKE
DELEGATE
```

World Kernel interaction classes、LanguageAdapter、AI normalizer、NSR、Evaluator、WorldIndex、scheduler、integrator、replayはいずれも新MKI primitiveではありません。

## Machine-oriented files

Core schemas/tools:

- [`schemas/nsr.schema.json`](schemas/nsr.schema.json)
- [`schemas/feasibility-report.schema.json`](schemas/feasibility-report.schema.json)
- [`schemas/runtime-execution.schema.json`](schemas/runtime-execution.schema.json)
- [`schemas/conformance-manifest.schema.json`](schemas/conformance-manifest.schema.json)
- [`schemas/conformance-coverage.schema.json`](schemas/conformance-coverage.schema.json)
- [`schemas/artifact-metadata.schema.json`](schemas/artifact-metadata.schema.json)
- [`schemas/common-values.schema.json`](schemas/common-values.schema.json)
- [`schemas/compatibility.schema.json`](schemas/compatibility.schema.json)
- [`schemas/compatibility-evolution.schema.json`](schemas/compatibility-evolution.schema.json)
- [`schemas/compatibility-coverage.schema.json`](schemas/compatibility-coverage.schema.json)
- [`schemas/semantic-registry.schema.json`](schemas/semantic-registry.schema.json)
- [`schemas/world-index.schema.json`](schemas/world-index.schema.json)
- [`schemas/runtime-profile.schema.json`](schemas/runtime-profile.schema.json)
- [`schemas/latin-lexicon.schema.json`](schemas/latin-lexicon.schema.json)
- [`schemas/source-text-normalization.schema.json`](schemas/source-text-normalization.schema.json)
- [`schemas/ambiguity-decision-trace.schema.json`](schemas/ambiguity-decision-trace.schema.json)
- [`schemas/planning-inference.schema.json`](schemas/planning-inference.schema.json)
- [`schemas/estimator-profile.schema.json`](schemas/estimator-profile.schema.json)
- [`schemas/canonical-water-ball.schema.json`](schemas/canonical-water-ball.schema.json)
- [`schemas/success-arcana.schema.json`](schemas/success-arcana.schema.json)
- [`schemas/experimental-arcana-manifest.schema.json`](schemas/experimental-arcana-manifest.schema.json)
- [`schemas/artifact-envelope.schema.json`](schemas/artifact-envelope.schema.json)
- [`schemas/spell-instance-bundle.schema.json`](schemas/spell-instance-bundle.schema.json)
- [`schemas/spell-instance-manifest.schema.json`](schemas/spell-instance-manifest.schema.json)
- [`tools/run_conformance.py`](tools/run_conformance.py)
- [`tools/run_success_arcana.py`](tools/run_success_arcana.py)
- [`tools/run_spell_instances.py`](tools/run_spell_instances.py)
- [`tools/package_spell_smoke.py`](tools/package_spell_smoke.py) — installed wheel/sdist entry-point security smoke。
- [`tools/semantic_fingerprint.py`](tools/semantic_fingerprint.py)
- [`tools/source_text_normalization.py`](tools/source_text_normalization.py)
- [`tools/latin_adapter.py`](tools/latin_adapter.py)

Reference implementation:

- [`src/evaluator/`](src/evaluator/) — v0.8 evaluator。
- [`src/runtime/`](src/runtime/) — v0.9 sandbox runtime。
- [`src/compatibility/`](src/compatibility/) — aggregate admission + exact compatibility evolution/migration helpers。
- [`conformance/manifest.json`](conformance/manifest.json) — stable class/case mapping。
- [`conformance/rule-coverage.json`](conformance/rule-coverage.json) — normative rule ↔ case coverage / explicit deferral inventory。
- [`conformance/compatibility-coverage.json`](conformance/compatibility-coverage.json) — required reference-path artifact ↔ domain/profile inventory。
- [`conformance/experimental-arcana.json`](conformance/experimental-arcana.json) — separate experimental class/case mapping; stable required claimではない。
- [`conformance/experimental-arcana-rule-coverage.json`](conformance/experimental-arcana-rule-coverage.json) — experimental rule reverse coverage。
- [`conformance/spell-instance-experimental.json`](conformance/spell-instance-experimental.json) — success/adversarial/non-suite bundle inventory; stable required claimではない。
- [`examples/kernel-execution/`](examples/kernel-execution/) — pre-public archive Issue #55 lower-boundary semantic cases。
- [`examples/sandbox-runtime/`](examples/sandbox-runtime/) — runtime examples。

Conformance fixtures:

- [`examples/semantic-fingerprint/`](examples/semantic-fingerprint/)
- [`examples/source-normalization/`](examples/source-normalization/)
- [`examples/core-config/`](examples/core-config/)
- [`examples/runtime-profiles/`](examples/runtime-profiles/)
- [`examples/compatibility/`](examples/compatibility/)
- [`examples/latin-adapter/`](examples/latin-adapter/)
- [`examples/ambiguity-policy/`](examples/ambiguity-policy/)
- [`examples/planning-inference/`](examples/planning-inference/)
- [`examples/estimator-profiles/`](examples/estimator-profiles/)
- [`examples/canonical-water-ball/`](examples/canonical-water-ball/)
- [`examples/success-arcana/`](examples/success-arcana/) — experimental success/negative/replay fixtures。
- [`examples/spell-instances/`](examples/spell-instances/) — canonical self-contained success/adversarial/generic bundles。

## Regression / release checks

```text
python tests/validate_schemas.py
python tools/run_conformance.py
python tools/run_success_arcana.py
python tools/run_spell_instances.py
python -m tools.package_spell_smoke  # installed environment / repository外cwd専用
python -m unittest discover -s tests -v
git diff --check
```

GitHub Actions:

- `Repository regression`
- `Conformance package smoke`
- `MagicalProgram runtime smoke`

package smokeはeditable install後、repository外cwdからinstalled conformance/evaluator entry pointを実行します。

## SI normalization

```text
(kg, m, s, A, K, mol, cd)
```

## 重要な設計原則

```text
Language-specific parse != NSR
NSR != SemanticAST != TypedMIR != KernelPlan
AI proposal != semantic truth
Confidence != proof
Lexical meaning != Entity resolution
SemanticFingerprint != artifact content_hash
Unexpected result != undefined behavior
Evaluation != Execution
PREPARE success != COMMIT permission
Estimate != Reservation
Feasibility != Authority grant
Unknown != zero
WorldIndex != WorldState
IndexRecord != Entity
Reference != Identity != Authority != Ownership != State
Selector != Ref
PayloadOf<K> != Quantity<K> in general
ReactionRule != ReactionPathway
Stoichiometry != RateLaw
Kinetics != Thermodynamics
Physical time != runtime tick
Tick execution order != causal order
Integrator approximation != physical law
DeterministicReplay != Rewind
Registry metadata != Capability
Dimension equality != Semantic type equality
PlannerPrediction != RuntimeSafetyGuarantee
Sandbox allowance != Capability
Kernel interaction class != MKI primitive
runtime bookkeeping != semantic active-effect ownership
control-plane COMMIT != all future consequences already occurred
DEACTIVATE != rollback
```

詳細は`reference/`、作業計画と次resume pointは [`TODO.md`](TODO.md) を参照してください。

## Security

脆弱性やsensitive security informationはpublic Issueへ投稿せず、GitHubのprivate vulnerability reportingを使用してください。詳細は [`SECURITY.md`](SECURITY.md) を参照してください。

## License

このrepositoryには現時点で明示的なopen-source licenseを付与していません。sourceは閲覧可能ですが、licenseが明示されるまで著作権上の権利は留保されます。利用・複製・再配布の許諾を推定しないでください。
