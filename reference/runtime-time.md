# Runtime Time Reference — v0.7

**Status:** normative timing/scheduling contract + informative implementation guidance.

## Purpose

v0.5の`Instant`/async/Eventとv0.6.2のcontinuous kineticsを、runtime scheduler・tick・numerical integration・replayへ接続する。

## Non-goals

- tickを物理時間量子として扱わない。
- 特定solverを全実装へ強制しない。
- TickIDを通常呪文APIへ公開しない。
- replayをRewindにしない。

## Depends on

- `conventions.md`
- `semantics.md`
- `world-index.md`
- `kinetics.md`
- `mki.md`

## Key invariants

```text
Physical time != runtime tick
Tick order != causal order
Event effective time != runtime commit time in general
Event commit time != continuation resume time
Integrator approximation != physical law
Replay != Rewind
TickID != Instant
```

## 1. Time domains

### Instant

monotonic physical/runtime time coordinate。

`sleep`, `after`, timeout, transfer propagation等のportable semanticsはInstant上で定義する。

### RuntimeEpochID

runtime execution session identity。

### RuntimeTickID

同一epoch内で単調増加するscheduler step ID。

TickIDはdurationを意味しない。

## 2. TickStamp

```text
TickStamp {
    epoch
    tick
    phase
    ordinal
}
```

runtime execution/replay用total order metadata。

```text
TickStamp order != happens-before
```

## 3. TickInterval

```text
TickInterval {
    start : Instant
    end   : Instant
}

Δt = end - start
```

Δtは固定不要。zero-time microstepは同一Instant上のordinalで表現する。

## 4. SchedulingPolicy

```text
FixedStep(dt)
AdaptiveStep(min_dt,max_dt,error_policy)
EventDriven
Hybrid(baseline_policy,split_on_events)
```

policy identity/revisionはdeterministic/replay modeで記録するMUST。

## 5. Logical scheduler phases

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

実装はobservable semanticsを維持すればphaseを統合してよい。

### Ingress

external input、scheduled work、ready continuationを取り込む。

### ContinuousAdvance

`[start,end]` 上のcontinuous processを前進。

### Revalidate

commit guard、EntityID/state revision、Capability、Lease等を再検証。

### Commit

due discrete transitionをruntime上で確定しWorld State/Historyへ反映。

### PublishSnapshot

post-commit coherent WorldRevisionを公開。

### Control

Controllerがsnapshotを読み、後続actuationを計画。

### IndexUpdate

WorldRevision変更をWorld Index updaterへ通知/反映。

### Dispatch

Event通知、await continuation ready化、handler/microstep scheduling。

## 6. Same-tick order

同tick内runtime executionは `(phase,ordinal)` でtotal orderを持てる。

```text
execution-before != happens-before
```

単なるserializationだけでcausal edgeを追加しない。

## 7. Microsteps

```text
MicrostepOrdinal
MicrostepBudget
```

同一Instantのzero-time workをboundedに処理する。

超過:

```text
MicrostepBudgetExceeded
```

## 8. Event time model

v0.7ではEventの**物理的有効時刻**と**runtime確定時刻**を分離する。

```text
EventTimeRecord {
    effective_at : Instant
    committed_at : Instant
}
```

### effective_at

world model上、そのeffectが有効になったと解釈する物理時刻。

### committed_at

runtimeがCommit phaseでそのtransitionを確定し、World State/Historyへ反映した時刻。

Event-driven scheduler等で境界をexact eventへ置ける場合:

```text
effective_at == committed_at
```

coarse numerical schedulingでは:

```text
|committed_at - effective_at| <= required event-time tolerance
```

をMUST満たす。

runtimeは `committed_at` を過去時刻へbackdateしてはならない。

## 9. Transfer propagation

物理model:

```text
τ = d / v_m
effective_arrival_at = sent_at + τ
```

schedulerはこのtheoretical/effective arrivalを変更しない。

FixedStep等で後続boundaryにcommitする場合:

```text
commit_latency = committed_at - effective_arrival_at
```

を記録しTemporalTolerance内に収める。

## 10. Continuation timing

```text
ResumeRecord {
    event_effective_at
    event_committed_at
    resumed_at
}
```

定義:

```text
CommitLatency   = event_committed_at - event_effective_at
DispatchLatency = resumed_at - event_committed_at
ResponseLatency = resumed_at - event_effective_at
```

`await`の因果規則:

```text
Delivered(tx) ≺ continuation
```

を維持する。

## 11. TemporalTolerance

```text
TemporalTolerance {
    event_time_error?
    dispatch_latency_bound?
    synchronization_error?
    controller_jitter?
}
```

```text
temporal tolerance != tick duration
```

粗いbaseline tickでもevent splitで厳しいtoleranceを満たせる。

## 12. IntegratorContract

```text
IntegratorContract {
    id
    revision
    supported_processes
    deterministic_profile
    local_error_policy
    global_error_policy?
}
```

具体algorithmはimplementation-defined/registry-defined profileにできる。

## 13. IntegrationReport

```text
IntegrationReport {
    process_id
    interval
    integrator_id
    integrator_revision
    substeps
    estimated_local_error
    estimated_global_error?
    required_tolerance
    accepted
}
```

accepted=falseで安全継続不能ならintegration failure。

## 14. Kinetic integration

normative:

```text
dξ/dt = rate(context(t))
```

runtime approximation:

```text
Δξ ≈ integrate(rate,start,end)
```

IntegratorがReactionRule/Stoichiometry/ConservationProfileの意味を変更してはならない。

## 15. Controller timing

```text
ControllerTiming {
    sample_period
    max_jitter
    actuation_latency_bound
    required_phase_relation?
}
```

満たせない場合:

```text
ControllerTimingUnsatisfied
```

## 16. Scheduled work order

```text
ScheduledWork {
    due_at
    stable_source_id
    source_sequence
    dependencies
    priority?
}
```

causal dependency未完workはeligibleではない。

same-time independent workはdeterministic modeでstable orderを持つMUST。

priorityはauthorityではない。

## 17. World Index update

```text
Commit
→ WorldRevision
→ PublishSnapshot
→ IndexUpdate
→ WorldIndexRevision
```

Index updaterは非同期でもよい。revision mappingを保持する。

## 18. ReplayManifest

```text
ReplayManifest {
    initial_world_revision
    code_hashes
    registry_hash
    world_index_schema_revision
    scheduler_policy_id/revision
    integrator_contracts
    deterministic_order_policy
    random_seeds
    external_input_stream_identity
}
```

## 19. TickRecord

```text
TickRecord {
    tick_id
    interval
    world_revision_before
    world_revision_after
    ingress_items
    committed_events
    integration_reports
    scheduler_decisions
    index_revision_after?
}
```

Event recordには必要に応じて `effective_at` と `committed_at` の両方を保持する。

## 20. ReplayProfile

```text
StrictDeterministic
DeterministicWithinTolerance
DiagnosticBestEffort
```

Strict modeはcompatible inputからsame semantic state/event/scheduler decisionsを要求する。

WithinToleranceは明示されたnumeric tolerance内の差を許容。

BestEffortは完全再現を保証しない。

## 21. Replay compatibility

少なくとも:

- code semantics/hash。
- registry contract。
- initial world state/revision。
- scheduler policy。
- integrator contract。
- deterministic ordering。
- external input/random seed。

を検査する。

開始前不一致:

```text
ReplayIncompatible
```

実行中不一致:

```text
ReplayDivergence
```

## 22. Replay vs Rewind

```text
DeterministicReplay != Rewind
```

Replayは別runtime/simulation instanceでexecutionを再構成する。元worldの確定済み履歴Hを書き換えない。

## 23. Source-language boundary

通常呪文はTickID/phase/ordinalへ依存してはならない。

```text
now_monotonic() -> Instant
```

はportable。

TickStamp公開はdebug/non-portable APIとして分離するSHOULD。

## 24. Feasibility metadata

Evaluatorは:

```text
scheduler policy assumption
temporal tolerance
expected duration
integration cost/error budget
controller timing requirement
commit/dispatch latency bounds
replay profile
```

を報告できる。

## 25. Errors

```text
MicrostepBudgetExceeded
SchedulerPolicyUnavailable
TemporalToleranceUnsatisfied
ControllerTimingUnsatisfied
ReplayIncompatible
ReplayDivergence
```

既存 `KineticIntegrationFailure`, `InsufficientTemporalPrecision`, `Timeout` との境界は `errors.md` を参照する。

## 26. RuntimeProfile serialization

`schemas/runtime-profile.schema.json` はscheduler、integrator、replay、temporal toleranceを
一つのversioned configuration artifactとして直列化する。各componentは独立した
`id`、`revision`、domain compatibility metadata、`contract` を持つ。

共通metadata schemaはcomponent compatibilityを判定しない。scheduler policy、solver
contract、replay mode、tolerance contractそれぞれの既存domain規則が判定を所有する。

各componentの`contract`は次の既存logical contractを構造化する。

- schedulerは`kind`で`FixedStep`、`AdaptiveStep`、`EventDriven`、`Hybrid`を区別し、
  各variantについて§4の引数を必須にする。§7の`microstep_budget`と§15の
  `controller_timing`を必要に応じて保持できる。
- integratorは§12の`supported_processes`、`deterministic_profile`、
  `local_error_policy`と、任意の`global_error_policy`を保持する。
- replayは§20の`StrictDeterministic`、`DeterministicWithinTolerance`、
  `DiagnosticBestEffort`のいずれかを`mode`として保持する。
- temporal toleranceは§11の4つのtolerance fieldを個別に保持する。

```text
Physical time != runtime tick
Tick order != causal order
Event effective time != runtime commit time in general
Integrator approximation != physical law
Replay != Rewind
```

durationは `machine-values.md` と `schemas/common-values.schema.json` のportable
`Quantity<Time>` specializationを使用する。semantic type、SI dimension、value、unitを
分離し、durationをtick identityやcausal orderへ縮約しない。

generic artifact content hashのcanonical bytes / algorithmはpre-v0.8で明示的にdeferする。
fixtureはscoped `status: unresolved` recordを使用し、架空のdigest algorithm/valueを
記録しない。domain別compatibility algorithmは各runtime contractが引き続き所有する。

共通decision envelopeは [`compatibility.md`](compatibility.md) /
`schemas/compatibility.schema.json` を使用できる。RuntimeProfile全体のrevisionだけで
component compatibilityを代用せず、scheduler、integrator、replay、temporal toleranceの
必要decisionを個別に記録する。必要profile/evidence不足は`Undetermined`であり、
安全境界では明示的fallbackがなければfail closedとする。
