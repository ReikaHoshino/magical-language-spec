# AGENTS.md — Executor-Neutral Repository Instructions

このファイルは、ChatGPT Work、Codex、Copilot、Gemini CLI、その他のcoding agent、または人間の実装者が
同じrepository contractから安全に作業できるようにするための共通入口である。

特定の製品、モデル、UI、usage planをproject workflowの前提にしない。

## Canonical sources

優先順位:

1. current user instruction
2. current `reference/` — 現行の意味論・仕様の正本
3. root `TODO.md` — work plan / lifecycle / RESUME POINTの正本
4. current GitHub `main` — 全実行環境間のdurable synchronization point
5. `spec/` — historical release snapshots
6. `PROJECT_HANDOFF.md` / `WORKFLOW.md` — 運用・handoff guidance
7. Issue / PR / conversation history — 補助資料

古いIssue本文、PR本文、会話、executorのlocal stateがcurrent `main` / `reference/` / `TODO.md` と矛盾する場合、
current canonical stateを優先する。

## Executor-specific profiles

共通規則はこの `AGENTS.md` と `WORKFLOW.md` が所有する。
必要に応じて、次のexecutor profileを追加で読む:

- autonomous / end-to-end executor: [`docs/executors/autonomous-work.md`](docs/executors/autonomous-work.md)
- Codex / implementation worker: [`docs/executors/codex-worker.md`](docs/executors/codex-worker.md)

profileが共通規則やcurrent `TODO.md` / `reference/` と矛盾する場合、共通規則とcurrent canonical stateを優先する。
profileへcurrent Issue番号やrelease stateを固定せず、作業開始時に必ず再読込する。

## Start-of-work procedure

新しい作業を開始するときは必ず:

1. current `main` から開始する。
2. `TODO.md` の `RESUME POINT` を読む。
3. 対象domainのcurrent `reference/` を読む。
4. 必要なら `README.md`, `CHANGELOG.md`, `reference/consistency-report.md` を確認する。
5. 既存Issue/PRを使う場合は、そのstatus/dependencyがcurrent stateと一致するか再確認する。

既存PRのfollow-upでは、そのPRのcurrent head/diffを実装状態の正として扱い、stale baseから再構築しない。

## Semantic change policy

次は勝手に決めない:

- 新しい言語意味論
- 新しいMKI primitive
- authority / identity / conservation semanticsの変更
- semantic equality / fingerprint semanticsの変更
- breaking compatibility policy
- 複数の妥当案があり、選択が将来architectureを実質的に変える事項

current referenceから合理的に一意化できるserialization、refactor、test、fixture、documentation sync、
non-semantic cleanupは自律的に実施してよい。

未定義のsemantic choiceが必要なら、推測で埋めずBLOCKED/open questionとして残す。
独立して進められる作業は継続する。

## Core invariants

current referenceの方が強い規則を定義している場合はそちらを優先する。最低限:

```text
Language-specific parse != NSR
NSR != SemanticAST
SemanticAST != TypedMIR
SemanticFingerprint != artifact content_hash
AI proposal != semantic truth
Confidence != proof
Lexical meaning != Entity resolution
Visibility != Authority
Registry metadata != Capability
WorldIndex != WorldState
IndexRecord != Entity
Physical time != runtime tick
Tick order != causal order
Integrator approximation != physical law
Replay != Rewind
Evaluation != Execution
Estimate != Reservation
Feasibility != Authority grant
Unknown != zero
Unexpected result != undefined behavior
```

## Repository editing

- `main`への直接実装を避け、branchで作業する。
- 意味的に一まとまりの変更としてcommitする。
- unrelated workを同じdiffへ混ぜない。
- merge conflictでは両側の意味を確認し、片側を機械的に捨てない。
- historical `spec/` snapshotをcurrent stateへ追従させて書き換えない。
- temporary/generated filesをcommitしない。

GitHub Issueは全taskで必須ではない。長寿命の設計課題、blocker、独立した大規模作業、議論を永続化する必要がある場合に使う。
PRは変更の隔離、diff review、履歴、rollback boundaryとして利用する。

## Validation

merge前の標準gate:

```text
python tests/validate_schemas.py
python -m unittest discover -s tests -v
git diff --check
```

変更固有のofficial checkが存在する場合は追加で実行する。

semantic contractを追加・変更したのに永続的な回帰test/fixtureがない場合、合理的に可能なら追加する。
PR時だけのad-hoc確認で終わらせない。

## Consistency check

consistency checkは通常workflowの一部とする。少なくとも以下を照合する:

- `reference/` ↔ schemas
- `reference/` ↔ examples / fixtures
- schemas ↔ fixtures
- diagnostics ↔ owning reference
- terminology ↔ normative owner
- tests ↔ claimed behavior
- `TODO.md` ↔ actual GitHub state
- README / CHANGELOG ↔ released vs unreleased state

複数domain変更、release、merge conflict解消ではrepo-wideに範囲を広げる。

## Release gate

version updateではroot `TODO.md` に定義されたrelease gateを実施する。
release前後にcurrent reference、historical snapshot、README、CHANGELOG、terminology、consistency report、
relevant schema/examples/tests、TODO/RESUME POINTを同期する。

release finalization timestampは実際の統合完了後のevidenceに基づいて記録する。
pre-merge candidate時刻をfinal timestampとして扱わない。

## Second-pass review

自分で実装した変更でもmerge前にreviewerとして再確認する:

- 意味論を意図せず変えていないか
- conflict resolutionで既存成果が消えていないか
- testsが主張を本当に検査しているか
- negative casesが必要十分か
- TODO/docsが完了状態を過大評価していないか
- current mainをbaseとしているか
- diffがscope内か

## Escalation format

ユーザー判断が本当に必要な場合は、単に質問して止まらず次を提示する:

```text
Problem
Canonical evidence
Why the current spec cannot decide it
Option A
Option B
Recommended option
Consequences
Work that can continue without the decision
```

## Current project state

現在地はこのファイルへ複製しない。
必ずroot `TODO.md` の `RESUME POINT` を読む。
