# v0.9 Sandboxed Runtime examples

このdirectoryはv0.9 reference runtimeの実行例を示す。normative semanticsは`reference/`、release snapshotは`spec/v0.9.0.md`を参照する。

## Canonical execution

WB-CANON-001のselected NSRをv0.8 evaluatorへ通し、そのreportをv0.9 runtimeへ渡す。

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

Expected stable boundaries:

```text
report.status                  ConditionallyFeasible
initial world revision         world:991
selected plan                  wb:plan:transfer-reconfigure
MKI operations                 RESOLVE, OBSERVE, CHANNEL, TRANSFER, RECONFIGURE, CONSTRAIN
result world revision          world:992
history event                  event:wb-canon-001
water-ball mass                50 kg
water-ball radius              0.01 m
water-ball acceleration        50 m/s^2
source-water remaining mass    50 kg
matter ledger total            100 kg
controller gravity_removed     false
```

The source omitted terminal remains semantic Unknown. The 50 m horizon is retained as a distinct PrepareBound PlanningAssumption.

## Revalidation failure

PREPARE can succeed and COMMIT can still fail if authoritative evidence changes:

```python
prepared = ReferenceRuntimeEngine().runtime.prepare(report, world)
world.capabilities["capability:source-water"]["active"] = False

# commit raises RuntimeExecutionError(code="AuthorityError")
ReferenceRuntimeEngine().runtime.commit(prepared, world)
```

The failed revalidation does not mutate authoritative sandbox state/history.

## Fail-closed public execution

`ReferenceRuntimeEngine.execute()` converts a supported runtime failure into a validated `SandboxExecutionTrace` with `status = Aborted` and an `ABORT` control-plane record.

```python
from src.runtime import SandboxProfile

engine = ReferenceRuntimeEngine(
    sandbox_profile=SandboxProfile(max_energy_j=100.0)
)
trace = engine.execute(report, canonical_sandbox_world())
assert trace["status"] == "Aborted"
assert trace["abort"]["code"] == "SandboxLimitExceeded"
```

## Replay

Replay uses a cloned sandbox and checks profile compatibility plus deterministic result-state hash. It is not rewind.

```python
initial = canonical_sandbox_world()
engine = ReferenceRuntimeEngine()
execution = engine.execute_strict(report, initial.clone())
replay = engine.replay(report, initial, execution)
assert replay["status"] == "Match"
```

## Non-goals

These examples do not imply:

- real-world/hardware effects;
- production persistence;
- arbitrary physical-model integration;
- an English LanguageAdapter;
- REVOKE/DELEGATE implementation;
- replay-as-rewind.
