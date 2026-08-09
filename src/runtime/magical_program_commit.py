"""Atomic COMMIT, abort trace, and deterministic replay for MagicalProgram-0."""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .sandbox import SandboxWorld
from .magical_program_model import (
    PreparedProgramPlan,
    ProgramRuntimeError,
    RuntimeExecutionContext,
    complete_runtime_state,
    complete_runtime_state_hash,
    deep_thaw,
    records_for,
    restore_all,
    validate_program_execution_trace,
)
from .magical_program_prepare import consume_effect, verify_output

_JSON = dict[str, Any]


def commit_program(
    runtime: Any, prepared: PreparedProgramPlan, world: SandboxWorld
) -> _JSON:
    if prepared.plan_id in runtime._consumed_plan_ids:
        raise ProgramRuntimeError(
            "ProgramPreparedPlanConsumed",
            "PreparedProgramPlan is runtime-local and single-use.",
            stage="REVALIDATE",
        )
    before = world.clone()
    runtime._consumed_plan_ids.add(prepared.plan_id)
    try:
        revalidation = runtime.revalidate(prepared, world)
        bindings = deep_thaw(prepared.runtime_bindings)
        effects: list[_JSON] = []
        if prepared.effects:
            world.process_state = {
                "process_id": f"process:{prepared.program_digest[:16]}",
                "status": "Committing",
                "prepared_plan_id": prepared.plan_id,
            }
            world.runtime_state["prepared_plans"] = {
                prepared.plan_id: {"status": "Committing"}
            }
        for effect in prepared.effects:
            registration = runtime.contracts.resolve(
                effect.contract_id, effect.contract_revision
            )
            before_events = len(world.history)
            value = registration.executor(
                RuntimeExecutionContext(prepared, registration), effect, world
            )
            if value.get("kind") != registration.output_kind:
                raise ProgramRuntimeError(
                    "ProgramRuntimeContractOutputMismatch",
                    "Runtime contract returned the wrong output kind.",
                    stage="COMMIT",
                )
            new_events = world.history[before_events:]
            if len(new_events) != registration.emitted_events:
                raise ProgramRuntimeError(
                    "ProgramRuntimeEventAccountingMismatch",
                    "Runtime contract emitted an undeclared event count.",
                    stage="COMMIT",
                )
            if (
                registration.emitted_events == 1
                and new_events[0].get("event_id") != value.get("event_id")
            ):
                raise ProgramRuntimeError(
                    "ProgramRuntimeEventIdentityMismatch",
                    "Runtime result does not match committed History.",
                    stage="COMMIT",
                )
            consume_effect(effect, world)
            bindings[effect.output_binding] = copy.deepcopy(value)
            effects.append(copy.deepcopy(value))

        results: list[_JSON] = []
        for declaration in prepared.output_declarations:
            value = bindings.get(declaration["binding"])
            if not isinstance(value, dict):
                raise ProgramRuntimeError(
                    "ProgramCommittedOutputMismatch",
                    f"Output binding {declaration['binding']!r} has no committed value.",
                    stage="COMMIT",
                )
            results.append(verify_output(declaration, value))

        if prepared.effects:
            world.runtime_state["prepared_plans"] = {}
            world.process_state.update(
                {"status": "Committed", "prepared_plan_id": None}
            )
        if not prepared.effects and complete_runtime_state(world) != complete_runtime_state(before):
            raise ProgramRuntimeError(
                "ProgramPureCommitMutation",
                "A pure program changed authoritative runtime state.",
                stage="COMMIT",
            )

        trace = {
            "document_kind": "MagicalProgramExecutionTrace",
            "schema_version": "0",
            "status": "Committed",
            "program_id": prepared.program_id,
            "runtime_profile": runtime.profile.record(),
            "source_world_revision": prepared.source_world_revision,
            "world_revision": world.revision,
            "prepared_plan_id": prepared.plan_id,
            "preparation": {
                "program_digest": prepared.program_digest,
                "source_history_digest": prepared.source_history_digest,
                "frozen_entity_ids": list(prepared.frozen_entity_ids),
                "frozen_state_revisions": list(prepared.frozen_state_revisions),
                "bound_record_ids": {
                    category: sorted(
                        {
                            item.record_id
                            for effect in prepared.effects
                            for item in records_for(effect)
                            if item.category == category
                        }
                    )
                    for category in (
                        "capabilities",
                        "leases",
                        "identities",
                        "evidence",
                        "accounting",
                    )
                },
                "reserved_energy_j": prepared.reserved_energy_j,
                "reserved_matter_kg": prepared.reserved_matter_kg,
                "reserved_events": prepared.reserved_events,
                "authoritative_state_mutated": False,
            },
            "revalidation": revalidation,
            "effects": effects,
            "results": results,
            "history_event_ids": [item["event_id"] for item in world.history],
            "result_state_hash": complete_runtime_state_hash(world),
        }
        validate_program_execution_trace(trace)
        return trace
    except Exception as error:
        restore_all(world, before)
        if isinstance(error, ProgramRuntimeError):
            raise
        raise ProgramRuntimeError(
            "ProgramCommitInternalFailure",
            "Registered effect failed and every authoritative domain was rolled back.",
            stage="COMMIT",
        ) from error


def execute_program(
    runtime: Any, program: Mapping[str, Any], world: SandboxWorld
) -> _JSON:
    before = world.clone()
    source_revision = world.revision
    try:
        report = runtime.evaluate(program, world=world)
        prepared = runtime.prepare(program, report, world)
        return runtime.commit(prepared, world)
    except ProgramRuntimeError as error:
        restore_all(world, before)
        trace = {
            "document_kind": "MagicalProgramExecutionTrace",
            "schema_version": "0",
            "status": "Aborted",
            "program_id": str(program.get("program_id", "unknown")),
            "runtime_profile": runtime.profile.record(),
            "source_world_revision": source_revision,
            "world_revision": world.revision,
            "abort": {
                "stage": error.stage,
                "code": error.code,
                "message": error.message,
            },
            "world_revision_unchanged": world.revision == source_revision,
            "history_unchanged": world.history == before.history,
            "configuration_unchanged": (
                complete_runtime_state(world) == complete_runtime_state(before)
            ),
        }
        validate_program_execution_trace(trace)
        return trace


def replay_program(
    runtime: Any,
    program: Mapping[str, Any],
    initial_world: SandboxWorld,
    expected: Mapping[str, Any],
) -> _JSON:
    try:
        validate_program_execution_trace(expected)
    except ValueError as error:
        return {
            "status": "Incompatible",
            "diagnostic": "ProgramReplayTraceInvalid",
            "message": str(error),
        }
    if expected.get("runtime_profile") != runtime.profile.record():
        return {
            "status": "Incompatible",
            "diagnostic": "ProgramReplayProfileMismatch",
        }
    observed = runtime.execute(program, initial_world.clone())
    if expected["status"] == "Committed":
        match = (
            observed.get("status") == "Committed"
            and expected.get("result_state_hash")
            == observed.get("result_state_hash")
            and expected.get("history_event_ids")
            == observed.get("history_event_ids")
            and expected.get("effects") == observed.get("effects")
            and expected.get("results") == observed.get("results")
        )
        return {
            "status": "Match" if match else "Diverged",
            "expected_state_hash": expected.get("result_state_hash"),
            "observed_state_hash": observed.get("result_state_hash"),
            "trace": observed,
        }
    match = (
        observed.get("status") == "Aborted"
        and expected.get("abort", {}).get("code")
        == observed.get("abort", {}).get("code")
        and observed.get("configuration_unchanged") is True
        and observed.get("history_unchanged") is True
    )
    return {
        "status": "DeterministicAbort" if match else "Diverged",
        "expected_abort": expected.get("abort"),
        "observed_abort": observed.get("abort"),
        "trace": observed,
    }
