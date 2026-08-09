# magical-language-spec — Codex Worker Instructions

Repository:

`ReikaHoshino/magical-language-spec`

あなたはこのrepositoryのimplementation workerです。

> この文書は Codex / implementation-worker 向けのexecutor-specific profileです。共通規則はroot `AGENTS.md` と `WORKFLOW.md` を優先し、current stateは `TODO.md` / `reference/` / GitHub `main` を正としてください。

上位のproject stateはGitHub `main` にあります。

## Canonical sources

- semantic specification: current `reference/`
- roadmap / RESUME POINT: root `TODO.md`
- historical releases: `spec/`
- durable implementation state: GitHub branches / commits / PRs

会話履歴だけを根拠に仕様を変更しないでください。

## Before work

必ずcurrent `main`を確認し、対象taskのcontractと関連referenceを読んでください。

既存branch/PRのfollow-upの場合は、そのPR headをcanonical baseとして扱ってください。

stale baseから既存PRを再構築しないでください。

## Implementation rules

- mainへ直接作業しない
- task専用branchを使用
- task scope外のsemantic decisionを勝手に行わない
- unspecified semantic choiceが必要ならBLOCKEDとして報告
- refactorやimplementation detailはsemantic contractを変えない範囲で自律的に処理
- tests/fixtures/docsを変更内容と同期
- merge conflictでは両側の意味を理解して解決し、片側を機械的に捨てない

## Required invariants

current referenceのinvariantを維持してください。

特に:

```text
Language-specific parse != NSR
NSR != SemanticAST
SemanticFingerprint != artifact content_hash
AI proposal != semantic truth
Lexical meaning != Entity resolution
Registry metadata != Capability
Visibility != Authority
Physical time != runtime tick
Replay != Rewind
Evaluation != Execution
Unknown != zero
```

## Validation

最低限:

```text
python tests/validate_schemas.py
python -m unittest discover -s tests -v
git diff --check
```

変更に固有のtestがあればそれも実行してください。

## Completion

完了後は:

- branchをpublish
- PRを作成または既存PRを更新
- PR head/diffを確認
- tests結果をPR本文へ記録
- unresolved事項を明示

してください。

Codex自身がproject roadmapを独自に再設計したり、次Issueを勝手に大量作成する必要はありません。

coordination / autonomous executor layerから渡されたtaskを正確に実装することを優先してください。
