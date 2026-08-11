# Runtime Tick Example — v0.7

**Status:** informative example.

この例はsource-language syntaxではなく、runtime内部で一つのTRANSFERとawaitがどう記録されうるかを示す。

## Source-level intent

```text
let tx = transfer ch, q;
await tx;
continue_spell();
```

TRANSFERのモデル上の送信時刻:

```text
sent_at = 10.000 s
propagation_delay = 0.125 s
```

したがって物理的な有効到着時刻は:

```text
effective_arrival_at = 10.125 s
```

## Example scheduler — exact boundary

adaptive/event-aware schedulerが:

```text
tick 40: [10.000, 10.080]
tick 41: [10.080, 10.125]
tick 42: [10.125, 10.170]
```

とevent boundaryへ分割したとする。

この場合:

```text
effective_at = committed_at = 10.125 s
CommitLatency = 0 s
```

にできる。

## Logical trace

```text
TickStamp(epoch=7,tick=40,phase=ContinuousAdvance,ordinal=0)
    transit advances

TickStamp(epoch=7,tick=41,phase=ContinuousAdvance,ordinal=0)
    transit reaches modeled destination at 10.125 s

TickStamp(epoch=7,tick=41,phase=Commit,ordinal=0)
    Event#E900 = Delivered(tx)
    effective_at = 10.125 s
    committed_at = 10.125 s

TickStamp(epoch=7,tick=41,phase=Dispatch,ordinal=0)
    await continuation becomes ready

TickStamp(epoch=7,tick=42,phase=Ingress,ordinal=0)
    continuation admitted
    resumed_at = 10.126 s
```

意味上:

```text
Delivered(tx) ≺ continuation
```

である。

ただし:

```text
TickStamp order != causality by itself
```

## Latencies

この例では:

```text
CommitLatency   = committed_at - effective_at
                = 0 s

DispatchLatency = resumed_at - committed_at
                = 0.001 s

ResponseLatency = resumed_at - effective_at
                = 0.001 s
```

propagation delay 0.125 sとは別の量である。

## Coarse-boundary contrast

仮にschedulerが10.130 sまでCommit boundaryを置けなかった場合:

```text
effective_at = 10.125 s
committed_at = 10.130 s
CommitLatency = 0.005 s
```

となる。

runtimeは:

```text
committed_at = 10.125 s
```

と過去へbackdateしてはならない。

この5 msが許容されるかは `TemporalTolerance.event_time_error` に依存する。

## Replay record sketch

```text
ReplayManifest {
    initial_world_revision = 2201
    registry_hash = "..."
    scheduler_policy = AdaptiveStep@3
    integrator = TransitIntegrator@2
    external_input_stream = "session-17"
}

TickRecord[index=41] {
    interval = [10.080 s, 10.125 s]
    world_revision_before = 2204
    world_revision_after  = 2205
    committed_events = [
        E900 {
            effective_at = 10.125 s
            committed_at = 10.125 s
        }
    ]
    integration_reports = [...]
}
```

別simulationで同じcompatible manifest/inputから再実行できても、これは元worldを10.125 sへ巻き戻す操作ではない。

```text
DeterministicReplay != Rewind
```
