# magical-language-spec — Autonomous Work Instructions

Repository:

`ReikaHoshino/magical-language-spec`

このリポジトリの設計・仕様整理・実装・検証・GitHub運用を、可能な範囲で自律的に進めてください。

> この文書は autonomous executor 向けのexecutor-specific profileです。共通規則はroot `AGENTS.md` と `WORKFLOW.md` を優先し、current stateは `TODO.md` / `reference/` / GitHub `main` を正としてください。

## 1. 正本

常に以下を正本として扱ってください。

- current specification: `reference/`
- historical release snapshots: `spec/`
- project roadmap / work state / RESUME POINT: root `TODO.md`
- GitHub `main`: 全環境間のdurable synchronization point

会話履歴、過去のagent task、PR本文、Issue本文は補助情報です。

それらがcurrent `main` / `reference/` / `TODO.md` と矛盾する場合は、GitHub上のcurrent stateを優先してください。

Issueはtask contractとして利用できますが、古いdependency/status記述を無条件に信用せず、現在のGitHub状態と照合してください。

---

## 2. 基本目標

ユーザーから明示的に停止を指示されない限り、`TODO.md` の `RESUME POINT` から開始し、依存関係上実行可能な作業を継続してください。

基本サイクル:

```text
read current main
→ inspect TODO RESUME POINT
→ inspect relevant reference
→ determine next READY work
→ design if necessary
→ implement
→ validate
→ self-review
→ consistency check
→ update documentation/project state
→ commit
→ PR
→ final PR/head review
→ merge
→ re-read main
→ determine next READY work
→ continue
```

単一タスクごとにユーザーへ操作を返さず、複数タスクを連続して処理できる場合は継続してください。

依存関係のない作業は安全な範囲で並列化して構いません。

ただし、同じ共有ファイル・同じsemantic contract・同じbranchを複数taskが同時編集する構成は避けてください。

---

## 3. GitHub運用

GitHubをcontrol planeとして使用してください。

原則:

- `main`へ直接作業しない
- taskごと、または意味的に一まとまりの変更ごとにbranchを使用
- commitを明確な単位にする
- PRを作成する
- PR head/diffをcanonical implementation stateとして再確認する
- validation完了後にmergeする
- merge後は必ずcurrent `main`を再読込する

Issueは必須ではありません。

Issueを新規作成するのは主に以下の場合です。

- 長期間残る設計課題
- 現在解決できないblocker
- 将来の独立した大規模作業
- 複数案の設計議論を永続化する必要がある場合
- dependency graph上、別taskとして追跡する価値が高い場合

単純な実装作業のためだけにIssueを増やす必要はありません。

既存Issueについては、実装完了・merge済みならstatusを適切に更新してください。

---

## 4. 自律的に決めてよいもの

以下はcurrent reference / TODO /既存設計から一意または十分明確に導ける限り、自律的に決定・実装して構いません。

- schema formalization
- fixture追加
- test追加
- regression fix
- documentation synchronization
- TODO lifecycle更新
- stale status cleanup
- duplicate documentationの削減
- reference間cross-link整理
- refactor
- naming/layoutの非意味論的整理
- deterministic implementation detail
- compatibilityを変えないinternal representation改善
- acceptance criteriaを満たすための補助tooling
- CI/regression harness整備
- merge conflict解消
- dependency解放
- 完了済み項目のcleanup
- versionを変えないmaintenance work

「会話へ戻せば安全」という理由だけで停止しないでください。

current specificationから合理的に一意化できるなら、そのまま進めてください。

---

## 5. ユーザーへエスカレーションする条件

以下の場合のみ、原則としてユーザーの設計判断を求めてください。

### 新しい意味論

既存reference/TODO/accepted designから導けない新しい意味論を選択する必要がある。

例:

- 新しいMKI primitive
- 新しいtype semantics
- 新しいauthority model
- 新しいconservation semantics
- 新しいambiguity semantics
- 新しいcompatibility semantics
- semantic equalityの意味変更
- language-independent semantic roleの追加・意味変更

### 複数の妥当な設計案

A/B両方が現在の仕様と矛盾せず、選択によって将来の言語設計やruntime architectureが実質的に変わる。

### Breaking change

既存仕様・fixture・public contractとの互換性を意図的に破る必要がある。

### 世界設定に踏み込む判断

language/runtime specificationではなく、世界観側の創作設定を新たに確定しなければ進められない。

### 不可逆な大規模変更

大量削除、history rewrite、重要な仕様ファイルの廃止など、誤判断時の復旧コストが大きい。

---

## 6. エスカレーション方法

エスカレーションが必要な場合も、単に「どうしますか？」で停止しないでください。

必ず以下を整理してください。

```text
Problem
Current canonical evidence
Why current specification cannot decide it
Option A
Option B
Recommended option
Consequences of each
Work that can continue without this decision
```

可能なら、判断待ち部分だけをBLOCKEDにして、独立して進められる他作業は継続してください。

---

## 7. Semantic safety rules

既存invariantを常に維持してください。

特に:

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

current referenceにさらに強い/新しいinvariantが存在する場合はそちらを優先してください。

---

## 8. Test / validation policy

変更内容に応じてfocused testsを実行した上で、merge前には可能な限りrepository-wide regressionを実行してください。

最低限の標準gate:

```text
python tests/validate_schemas.py
python -m unittest discover -s tests -v
git diff --check
```

repository stateが変化して別のofficial regression commandが追加された場合は、それも実行してください。

テストが存在しないsemantic contractを追加・変更した場合、合理的に可能ならregression testまたはfixtureを追加してください。

「PR作成時に一度手で確認しただけ」の検証を残さず、再実行可能なtestへ落としてください。

---

## 9. Consistency check

consistency checkは別タスクではなく、通常workflowの一部です。

各変更で最低限確認:

- reference ↔ schema
- reference ↔ examples
- schema ↔ fixtures
- TODO ↔ actual GitHub state
- terminology ↔ normative owner
- diagnostics ↔ owning reference
- tests ↔ normative rules

複数domainにまたがる変更ではさらに広いcross-reference auditを実行してください。

過去のstatusや「次にやること」が現在のmainと食い違っていれば、可能な範囲で同じ作業中にreconcileしてください。

ただしhistorical `spec/` snapshotをcurrent stateへ追従させて書き換えてはいけません。

---

## 10. Release policy

version updateを行う場合は、root `TODO.md` に定義されたrelease gateを必ず実施してください。

release前後で少なくとも:

- `TODO.md`
- `reference/`
- `spec/vX.Y[.Z].md`
- `README.md`
- `CHANGELOG.md`
- `reference/terminology.md`
- `reference/consistency-report.md`
- relevant schemas
- relevant examples
- relevant tests
- relevant grammar/data

を照合してください。

release終了後:

- current version
- completed work
- unresolved/deferred work
- next RESUME POINT
- release finalization timestamp

を同期してください。

release finalization timestampは、実際にrelease統合が完了した後の証拠に基づいて記録し、pre-merge candidate時刻をfinal timestampとして扱わないでください。

---

## 11. Historical snapshot policy

`spec/` はhistorical release snapshotです。

release後にcurrent `reference/`へ追加されたunreleased workを、過去snapshotへretroactively追加してはいけません。

current mainがreleased versionより先行している場合は、README/CHANGELOG等でreleased stateとcurrent referenceのunreleased stateを明確に分離してください。

---

## 12. Cleanup policy

定期的に安全なcleanupを行ってください。

削減対象:

- merge済みPRを前提にした古い「READY」記述
- 成立済みdependency condition
- TODO/HANDOFF間の一時的なcurrent-state重複
- obsolete implementation notes
- duplicated normative prose
- ad-hoc validation paths
- unused temporary files
- stale fixture descriptions

ただし以下は安易に削除しないでください。

- historical `spec/`
- unresolved design sentinels
- compatibility boundary documentation
- still-referenced fixtures
- workflow history that remains operationally relevant
- semantic extension points whose semantics are intentionally undecided

削除前にreference/usage/testsを確認してください。

---

## 13. Review discipline

自分で実装した変更についても、merge直前にsecond-pass reviewを行ってください。

その際は実装者としてではなく、外部PR reviewerとして以下を確認してください。

```text
What semantic claims changed?
Were any semantics changed unintentionally?
Did anything disappear during conflict resolution?
Are existing invariants preserved?
Are tests actually testing the claimed behavior?
Are negative cases sufficient?
Are TODO/docs overstating completion?
Did the branch inherit current main?
Is the PR diff limited to justified scope?
```

問題があればmerge前に修正し、再検証してください。

---

## 14. Current project checkpoint

current stateをこのprofileへ固定しないでください。

作業開始時に必ず:

- current GitHub `main`
- root `TODO.md` の `RESUME POINT`
- relevant current `reference/`
- 必要に応じてcurrent release / roadmap Issue

を再読込し、その時点のDONE / READY / BLOCKED状態を再計算してください。

過去のIssue番号、旧dependency graph、旧release milestoneをこの文書の記述だけから復元しないでください。

---

## 15. Current objective

上位目標とrelease milestoneはroot `TODO.md` の `RESUME POINT` を正とします。

このprofileは特定versionや特定Issueを固定しません。
pre-release / implementation / stabilization / release gateのどの段階でも、current TODO/referenceから次作業を決定してください。

---

## 16. Reporting

通常は細かな操作ごとにユーザーへ確認を求めないでください。

意味のあるcheckpointで、短く以下を報告してください。

```text
Completed
Merged PR / commit
Validation result
Important design decisions
Remaining blockers
Next work being taken
```

重大なsemantic decisionが必要な場合のみユーザーへ停止・エスカレーションしてください。

目標は、ユーザーがIssue / agent prompt / PR review / merge / consistency checkの間を手動で中継しなくても、repository自身の正本とvalidationから安全に作業が継続することです。
