# PROJECT_HANDOFF.md — Project Handoff / Execution Environment Guide

このファイルは、個別の会話・AI製品・ローカル環境が失われても、魔術言語仕様プロジェクトをGitHubから再開できるようにするためのhandoff文書である。

- 仕様の正本: current `reference/`。
- historical release snapshot: `spec/`。
- 作業計画・現在release・再開地点の正本: root `TODO.md`。
- release差分: `CHANGELOG.md`。
- 共通executor instructions: `AGENTS.md`。
- 標準実装フロー: `WORKFLOW.md`。
- autonomous executor profile: `docs/executors/autonomous-work.md`。
- Codex / implementation-worker profile: `docs/executors/codex-worker.md`。
- 会話・agent memory・local checkoutは正本にしない。

2026-08-09以降のactive workはpublic `ReikaHoshino/magical-language-spec`で追跡する。clean public historyより前のIssue/PR番号はhistorical archive identifierであり、current task stateはroot `TODO.md`とpublic Issue/PRから復元する。

この文書へlatest version、current task、current DONE / READY / BLOCKED setを固定値として複製しない。release stateは`TODO.md` / `CHANGELOG.md` / current GitHub Issue・PR evidenceを読む。

---

## 1. 現在の再開地点

**current DONE / READY / BLOCKED状態をこの文書へ複製しない。**

新しい作業では必ず**root `TODO.md` の `RESUME POINT` を正本として読む**。
release train / long-lived dependencyはGitHubのrelease/roadmap Issueを補助indexとして参照できるが、TODOを置き換えない。

current `reference/`がlatest released `spec/` snapshotより先行する場合がある。
`spec/` はimmutable historical snapshotとして固定し、unreleased/current workを過去snapshotへ遡及追加しない。

---

## 2. Project / environment migration policy

GitHubを長期記憶・同期点として使う。

ChatGPT Project、Codex、Copilot、Gemini CLI、その他agent、local editor、人間の実装者など、execution environmentは交換可能である。

新しい環境へ移るとき:

1. current GitHub `main` を取得する。
2. `AGENTS.md` を読む。
3. 必要ならexecutor-specific profileを読む。
4. `TODO.md` の `RESUME POINT` を読む。
5. 対象domainのcurrent `reference/` を読む。
6. release関連なら `README.md`、`CHANGELOG.md`、`reference/consistency-report.md`、release Issue/PRを照合する。
7. 過去conversation/taskの記憶ではなくcurrent repo stateから再開する。

特定AI製品のUI、usage plan、memory機能をproject correctnessの前提にしない。

---

## 3. Execution model

### Semantic / coordination work

対象:

- 仕様・意味論・scope判断
- version scope
- cross-domain trade-off
- TODO prioritization
- release判断

chat、agent、人間のいずれが担当してもよい。重要な決定は必ずrepoへ永続化する。

### Implementation work

対象:

- parser / evaluator / runtime / CLI
- schemas / validators
- tests / fixtures / conformance artifacts
- refactor
- CI / automation
- documentation synchronization

実装主体を特定AIへ限定しない。current referenceから導けないsemantic choiceが必要なら推測せずエスカレーションする。

### Audit / integration work

対象:

- repo-wide consistency audit
- release gate
- large reference cleanup
- schema / fixture / conformance横断確認
- merge-loss / stale-state検査

実装したexecutor自身がauditする場合も、merge前にsecond-pass reviewを分ける。

### GitHub

GitHubを全実行環境間のdurable synchronization pointとする。

```text
Chat / agents / local tools / humans
              ↕
            GitHub
              ↕
       main / PR / history
```

**他環境の記憶だけを根拠に仕様や作業状態を変更しない。**

---

## 4. Common operating rules

新しいsession/taskを始めるとき:

1. `AGENTS.md` を読む。
2. 必要なら `docs/executors/` のexecutor profileを読む。
3. `TODO.md` の `RESUME POINT` を読む。
4. 対象domainのcurrent `reference/` を読む。
5. release関連ならREADME / CHANGELOG / consistency report / release Issue・PRを確認する。
6. Issue/PR/conversationとrepoが食い違う場合はcurrent repoを優先し、必要ならstatusをreconcileする。

割り込みが入る場合:

1. `TODO.md` の`Suspended work` / RESUME POINTへcheckpointを残す。
2. 必要ならInbox/Backlogへ要求を保存する。
3. 割り込みへ対応する。
4. 終了時に次のresume pointを再設定する。

「Todoに追加して」と言われた場合:

- project課題なら原則root `TODO.md` に追加する。
- scheduled notificationは将来時刻/定期実行が明示的に必要な場合だけ使う。

---

## 5. Version update gate

### Before release

最低限:

- `TODO.md`
- `README.md`
- `CHANGELOG.md`
- `reference/consistency-report.md`
- 変更対象reference/schema/grammar/examples/data/tests/conformance artifacts
- release Issue / PR dependency state

を照合し、TODOでrelease scope / lifecycle / dependencyを確認する。

### After release

最低限:

- `spec/vX.Y[.Z].md`
- current `reference/`
- `README.md`
- `CHANGELOG.md`
- `reference/terminology.md`
- relevant types/errors/grammar/schemas/examples/data/tests/conformance artifacts
- `reference/consistency-report.md`
- `TODO.md` のprogress / next RESUME POINT
- `TODO.md` のrelease最終整理時刻

を同期する。

release finalization timestampは、release後チェック・文書同期・次RESUME POINT設定が完了した時点のevidenceに基づいて記録する。pre-merge candidate時刻をfinalとして扱わない。

---

## 6. Stable project invariants worth carrying across environments

正式定義はcurrent `reference/` を読む。この節はhandoff時の探索用indexであり第二正本ではない。

Language Adapter priority:

```text
1. lat — Latin
2. lzh — Literary / Classical Chinese
3. ger — German
4. jpn — Japanese
5. eng — English
6. zho — Modern Chinese
```

Cross-language normalization:

```text
Source<L1>
→ LanguageAdapter<L1>
→ NSR
→ SurfaceRenderer<L2>
→ Source<L2>
```

Ambiguity policy family:

```text
StrictReject
InteractiveResolve
ContextualDeterministic
LegacyPermissive
```

Important boundaries:

```text
Language-specific parse != NSR
AI proposal != semantic truth
Confidence != proof
Lexical meaning != Entity resolution
Unexpected result != undefined behavior
SemanticFingerprint != artifact content_hash
Evaluation != Execution
PREPARE success != COMMIT permission
Registry metadata != Capability
Visibility != Authority
Physical time != runtime tick
Integrator approximation != physical law
Replay != Rewind
```

具体的なMKI / World Kernel / conformance class等のcurrent stable surfaceはこのhandoffへ複製せず、current `reference/` とrelease artifactsを読む。

---

## 7. Handoff durability checklist

project stateを特定conversationに依存させない条件:

- [x] persistent `TODO.md` が存在する。
- [x] current specificationが`reference/`に存在する。
- [x] historical releasesが`spec/`に存在する。
- [x] machine-readable schemas / fixtures / regression / conformance checksがrepoに存在する。
- [x] executor-neutral `AGENTS.md` / `WORKFLOW.md` が用意されている。
- [x] autonomous / Codex executor-specific profilesがrepoに保存されている。
- [ ] 必要な過去conversationの未永続化情報が残っていないことを、削除前に都度確認する。

---

## 8. Recommended Project instructions

Project/chat側の指示は次の趣旨で十分である:

```text
このProjectは magical-language-spec の設計・実装用。
仕様の正本はGitHub current reference、作業計画の正本はroot TODO.md。
新しい作業開始時にAGENTS.md、必要なexecutor profile、TODO.md RESUME POINTを確認する。
会話だけに重要な決定や未完課題を残さずGitHubへ永続化する。
version update前後はTODO.mdのrelease gateとconsistency checkを実施する。
割り込み時はcheckpointをTODO.mdへ残す。
「Todoに追加」は原則GitHub TODO.mdへの追加を意味する。
実装主体は特定AI製品へ固定せず、GitHub mainを全環境の同期点とする。
```

この指示はrepo側の運用規約を要約したものであり、仕様本文を置き換えない。
