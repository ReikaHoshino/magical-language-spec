# WORKFLOW.md — Executor-Neutral Implementation Workflow

この文書は、実装主体を特定のAI製品やUIへ固定せずに `magical-language-spec` を安全に進める標準フローを定義する。

実装者はChatGPT Work、Codex、Copilot、Gemini CLI、その他のagent、人間のいずれでもよい。

## 1. Control plane and canonical state

```text
executor(s)
    ↕
 Git / GitHub
    ↕
main + TODO.md + reference/
```

- semantic source of truth: current `reference/`
- planning/resume source of truth: root `TODO.md`
- durable synchronization point: GitHub `main`
- historical release snapshots: `spec/`
- common executor instructions: `AGENTS.md`

executorのconversation memory、local checkout、Issue本文、PR本文をcanonical project stateにしない。

必要に応じてexecutor-specific profileを追加で読む:

- autonomous / end-to-end executor: `docs/executors/autonomous-work.md`
- Codex / implementation worker: `docs/executors/codex-worker.md`

profileは共通workflowを置き換えず、製品/役割固有の追加指示だけを与える。

## 2. Standard cycle

```text
read current main
→ read TODO RESUME POINT
→ read relevant reference
→ identify READY work
→ design only as needed
→ implement on branch
→ focused validation
→ full regression gate
→ second-pass review
→ consistency check
→ PR
→ verify PR head/diff
→ verify exact-head merge gate
→ merge when safe
→ re-read main
→ reconcile TODO if needed
→ continue
```

ユーザーが各工程を手動で中継することを前提にしない。
一つのexecutorがend-to-endで安全に処理できる場合、そのまま完了まで進めてよい。

## 3. When to use Issues

Issue-per-taskは必須ではない。

Issueを使う主な場合:

- 長期間残る設計課題
- 現在解決不能なblocker
- 独立した大規模作業
- dependencyを長期追跡する必要がある作業
- 複数案の議論・設計判断をGitHubへ永続化する場合

短いimplementation/cleanup/fixは、TODO/referenceからscopeが明確ならbranch/PRだけで処理してよい。

## 4. Branch / PR policy

- `main`へ直接実装しない。
- taskまたは意味的に一まとまりの変更ごとにbranchを使う。
- PRはchange isolation / review / history / rollback boundaryとして残す。
- follow-upは可能なら同じPRを更新する。
- PRのcurrent head/diffを、executor local stateより優先する。
- stale taskが既存PR headを取得できない場合、古いbaseから推測して再実装しない。

PR本文には変更の規模に応じて最低限:

- Summary
- semantic/non-semantic scope
- validation results
- unresolved/deferred items
- related TODO/Issue when useful

を記録する。

## 5. Parallel work

依存関係とfile ownershipが独立していれば並列化できる。

避ける:

- 同じbranchへの複数executor同時編集
- `TODO.md`, README, CHANGELOG, broad consistency report等の共有stateを複数PRが競合更新
- 同じsemantic contractを別branchで並行定義

並列PRをmergeした後は、共有stateとregression harnessにmerge loss/driftがないか確認する。

## 6. Semantic decision boundary

executorが自律的に処理してよい:

- current referenceから導ける実装
- schema/fixture/test formalization
- refactor
- documentation synchronization
- stale state cleanup
- non-semantic naming/layout改善
- acceptance criteriaを満たす補助tooling
- regression failure修正

ユーザー/設計判断へエスカレーションする:

- current reference/TODOから導けない新semantic rule
- breaking compatibility
- authority/identity/conservation/MKI/fingerprint等の根幹変更
- 複数の妥当案があり、選択がarchitectureを実質的に変える場合

## 7. Validation and exact-head merge gate

標準:

```text
python tests/validate_schemas.py
python -m unittest discover -s tests -v
git diff --check
```

task-specific checkがある場合は追加する。

CIが導入されている場合も、CI greenだけでsemantic correctnessを証明したと扱わない。

PRをmerge-readyと宣言するには、second-pass review後の**同一PR current head SHA**について、次のrequired workflowがすべて`completed/success`でなければならない。

```text
Repository regression
Conformance package smoke
MagicalProgram runtime smoke
```

古いheadの成功、workflow欠落、queued/in-progress、failure、cancelled、timed_out、skippedはすべてfail-closedとする。review後にheadが変わった場合はreviewとgateをやり直す。

repository-owned checker:

```text
GITHUB_TOKEN=... python scripts/check_pr_merge_gate.py \
  --repository ReikaHoshino/magical-language-spec \
  --pr <PR_NUMBER> \
  --expected-head-sha <REVIEWED_HEAD_SHA>
```

このcheckerをmerge直前に実行し、可能なmerge APIでは同じexpected head SHAを条件として渡す。checker成功だけでsemantic correctnessを代替せず、上記validation・second-pass review・consistency checkも必要である。

## 8. Second-pass review

merge前に実装者とは別の視点で確認する。
同一agentが担当する場合もreview phaseを明示的に分ける。

最低限:

```text
What semantic claims changed?
Were any semantics changed unintentionally?
Did conflict resolution remove existing work?
Are invariants preserved?
Do tests cover the claimed behavior?
Are negative cases sufficient?
Are TODO/docs overstating completion?
Is the diff limited to justified scope?
```

## 9. Consistency check

通常task:

- relevant reference ↔ schemas/examples/tests
- diagnostics ↔ owning reference
- TODO lifecycle ↔ actual completion

cross-domain / integration task:

- repository-wide reference links/ownership
- schema/fixture compatibility
- duplicated normative prose
- stale READY/BLOCKED/PR-specific wording
- regression entry points

release:

root `TODO.md` のrelease gateを完全に実行する。

## 10. Merge completion

merge後:

1. current `main` を新しい同期点として再取得する。
2. `TODO.md` のRESUME POINTを確認する。
3. dependencyが解放された場合は次のREADY workを再評価する。
4. releaseの場合はrelease finalization evidenceとtimestampを確定する。
5. issue/PR/conversationだけに重要stateを残さない。
6. required workflowが`push`でも実行される場合はmerge SHAのpost-merge resultも確認する。PR merge commitとmainが一致しない、またはpost-merge regressionが失敗した場合は次作業へ進まない。

## 11. Safe cleanup

安全に削減しやすい:

- merged PRを前提にした一時的status prose
- 成立済みdependency condition
- executor固有UI手順
- 重複したcurrent-state説明
- obsolete ad-hoc validation notes

安易に削除しない:

- historical `spec/`
- unresolved/deferred design boundary
- compatibility ownership
- still-referenced fixtures/tests
- semantic extension point

## 12. Product-specific notes

製品固有のtransport/UI制約はcanonical workflowではない。
必要ならexecutorごとのprofileで補足する。

`CODEX_WORKFLOW.md` は過去リンク互換用の入口として残すが、現行の標準workflowは本ファイルと `AGENTS.md` である。
