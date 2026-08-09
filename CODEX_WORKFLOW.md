# CODEX_WORKFLOW.md — Compatibility Entry for Codex

**Status:** compatibility / product-specific note. The canonical implementation workflow is now [`WORKFLOW.md`](WORKFLOW.md), with shared executor instructions in [`AGENTS.md`](AGENTS.md).

このファイルは、過去のIssue / PR / conversationからのリンクを壊さないために残す。
Codexを必須の実装環境とはしない。

Codexを使う場合は、共通規則に加えて [`docs/executors/codex-worker.md`](docs/executors/codex-worker.md) をexecutor-specific profileとして読む。

## Canonical project rules

Codexを使う場合も他のexecutorと同じ規則に従う。

- semantic source of truth: current `reference/`
- planning / RESUME POINT: root `TODO.md`
- durable synchronization point: GitHub `main`
- general workflow: `WORKFLOW.md`
- executor rules: `AGENTS.md`

```text
GitHub is the control plane.
Executor UI / browser / shell are transport and execution layers.
Conversation memory is not canonical project state.
```

## Codex-specific transport notes

Codex環境ではshellの`git push`が常に利用できるとは限らない。
`origin`、network、credentialが利用できず、製品側のCreate PR / Update branch機能だけがpublish経路になる場合がある。

その場合も完了判定はGitHub側で行う:

1. PR / branchが存在する。
2. base / headが意図どおりである。
3. GitHub上のhead SHA / diffが更新されている。
4. requested changesがdiffへ反映されている。
5. validation結果とunresolved事項が確認できる。

Codex local commit SHAとpublish後のGitHub SHAが異なる場合、GitHubのhead/diffを正とする。

## Existing PR follow-up

既存PRを修正するときはcurrent PR head/diffから作業する。
古い`main`しか取得できないfresh taskから既存PRを推測して再構築しない。
取得不能ならその制約を報告し、PR headへアクセス可能な経路を使う。

## Validation

最低限:

```text
python tests/validate_schemas.py
python -m unittest discover -s tests -v
git diff --check
```

新しい意味論をCodex固有の都合で導入しない。
