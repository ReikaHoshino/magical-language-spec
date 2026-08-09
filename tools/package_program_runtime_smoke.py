#!/usr/bin/env python3
"""Exercise the installed authoritative MagicalProgram runtime outside checkout."""
from __future__ import annotations

import json
from pathlib import Path

from src.evaluator.magical_program import (
    MagicalProgramEvaluator,
    ProgramContractRegistration,
    ProgramContractRegistry,
)
from src.resources import reference_root, resource_path
from src.runtime.magical_program import (
    MagicalProgramRuntime,
    ProgramRuntimeContractRegistry,
    ProgramRuntimeError,
    ProgramRuntimeProfile,
    RuntimeContractRegistration,
    complete_runtime_state,
    program_sandbox_world,
)


def load(relative: str):
    return json.loads(resource_path(relative).read_text(encoding="utf-8"))


def structured_runtime() -> MagicalProgramRuntime:
    semantic = ProgramContractRegistry(
        (
            ProgramContractRegistration(
                "test.structured-consumer",
                "1",
                "effect.invoke",
                (
                    "record:EvidenceFusionModel",
                    "sequence:record:HypothesisScore",
                ),
                "effect_result",
                (),
                0,
                0,
                0,
                ("OBSERVE",),
                ("SAMPLE",),
            ),
        )
    )

    def consume(context, effect, world):
        model, ranking = effect.frozen_values
        winner = max(
            ranking["items"],
            key=lambda item: (
                item["fields"]["score"]["value"],
                item["fields"]["hypothesis_id"]["value"],
            ),
        )
        return {
            "kind": "effect_result",
            "status": "Committed",
            "node_id": effect.node_id,
            "model_id": model["fields"]["model_id"]["value"],
            "winner_hypothesis_id": winner["fields"]["hypothesis_id"]["value"],
        }

    contracts = ProgramRuntimeContractRegistry(
        (
            RuntimeContractRegistration(
                "test.structured-consumer",
                "1",
                "effect.invoke",
                (
                    "record:EvidenceFusionModel",
                    "sequence:record:HypothesisScore",
                ),
                "effect_result",
                0,
                consume,
            ),
        )
    )
    return MagicalProgramRuntime(
        evaluator=MagicalProgramEvaluator(contracts=semantic),
        contracts=contracts,
    )


def main() -> int:
    runtime = MagicalProgramRuntime()
    transition = load("examples/magical-program/MP-001.json")
    observation = load("examples/magical-program/MP-OBSERVE-001.json")
    pure = load("examples/magical-program/MP-PURE-001.json")
    structured = load("examples/magical-program/MP-STRUCTURED-001.json")

    transition_initial = program_sandbox_world()
    transition_world = transition_initial.clone()
    transition_trace = runtime.execute(transition, transition_world)
    transition_replay = runtime.replay(
        transition, transition_initial, transition_trace
    )
    if (
        transition_trace.get("status") != "Committed"
        or transition_replay.get("status") != "Match"
        or transition_world.revision != "world:generic:2"
    ):
        raise RuntimeError("installed transition runtime/replay failed")
    if {item["kind"] for item in transition_trace.get("results", [])} != {
        "effect_result",
        "event",
    }:
        raise RuntimeError("installed transition did not bind committed outputs")

    observation_initial = program_sandbox_world()
    observation_world = observation_initial.clone()
    first_observation = runtime.execute(observation, observation_world)
    observation_replay = runtime.replay(
        observation, observation_initial, first_observation
    )
    second_observation = runtime.execute(observation, observation_world)
    if (
        first_observation.get("status") != "Committed"
        or observation_replay.get("status") != "Match"
        or observation_world.entities != observation_initial.entities
        or observation_world.revision != observation_initial.revision
    ):
        raise RuntimeError("installed observation runtime/replay failed")
    if (
        first_observation["effects"][0]["event_id"]
        == second_observation["effects"][0]["event_id"]
        or first_observation["effects"][0]["artifact_id"]
        == second_observation["effects"][0]["artifact_id"]
    ):
        raise RuntimeError("installed occurrence identities collided")

    pure_world = program_sandbox_world()
    pure_before = complete_runtime_state(pure_world)
    pure_trace = runtime.execute(pure, pure_world)
    if (
        pure_trace.get("status") != "Committed"
        or complete_runtime_state(pure_world) != pure_before
    ):
        raise RuntimeError("installed pure program mutated authoritative state")

    structured_engine = structured_runtime()
    structured_initial = program_sandbox_world()
    structured_trace = structured_engine.execute(
        structured, structured_initial.clone()
    )
    structured_replay = structured_engine.replay(
        structured, structured_initial, structured_trace
    )
    if (
        structured_trace.get("status") != "Committed"
        or structured_replay.get("status") != "Match"
        or structured_trace["effects"][0].get("winner_hypothesis_id")
        != "hypothesis:A"
    ):
        raise RuntimeError("installed structured value runtime/replay failed")

    single_use_world = program_sandbox_world()
    prepared = runtime.prepare(
        observation,
        runtime.evaluate(observation, world=single_use_world),
        single_use_world,
    )
    runtime.commit(prepared, single_use_world)
    try:
        runtime.commit(prepared, single_use_world)
    except ProgramRuntimeError as error:
        if error.code != "ProgramPreparedPlanConsumed":
            raise
    else:
        raise RuntimeError("PreparedProgramPlan was not single-use")

    abort_initial = program_sandbox_world()
    abort_initial.capabilities["capability:host:transition"]["active"] = False
    abort_trace = runtime.execute(transition, abort_initial.clone())
    abort_replay = runtime.replay(transition, abort_initial, abort_trace)
    if (
        abort_trace.get("status") != "Aborted"
        or abort_replay.get("status") != "DeterministicAbort"
        or not abort_trace.get("configuration_unchanged")
        or not abort_trace.get("history_unchanged")
    ):
        raise RuntimeError("installed deterministic abort replay failed")

    strict_runtime = MagicalProgramRuntime(
        profile=ProgramRuntimeProfile(max_events=0)
    )
    strict_trace = strict_runtime.execute(transition, program_sandbox_world())
    if (
        strict_trace.get("abort", {}).get("code")
        != "ProgramRuntimeEventLimitExceeded"
    ):
        raise RuntimeError("artifact budget bypassed the host event ceiling")

    print(
        json.dumps(
            {
                "status": "PASS",
                "package_root": str(reference_root().resolve()),
                "cwd": str(Path.cwd().resolve()),
                "transition": transition_trace["status"],
                "transition_replay": transition_replay["status"],
                "observation": first_observation["status"],
                "observation_replay": observation_replay["status"],
                "distinct_occurrences": True,
                "pure": pure_trace["status"],
                "structured": structured_trace["status"],
                "structured_replay": structured_replay["status"],
                "single_use": True,
                "abort": abort_trace["status"],
                "abort_replay": abort_replay["status"],
                "host_ceiling_abort": strict_trace["abort"]["code"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
