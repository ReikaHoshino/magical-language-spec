"""Versioned DEBUG-HELL contracts owned by Issue #46."""
from __future__ import annotations

from src.artifacts.execution_contract_registry import ExecutionContractRegistration, ExecutionContractRegistry
from src.evaluator.handler_registry import SemanticHandlerRegistration, SemanticHandlerRegistry
from src.runtime.executor_registry import ParameterReference, RuntimeExecutorRegistration, RuntimeExecutorRegistry

from .executors import prepare_bound_toctou_hook, prepare_bound_transit, reactive_hydra_abort
from .handlers import pathological_water_ball_handler, prepare_bound_transit_handler, reactive_hydra_handler


STRING = {"type": "string", "minLength": 1}
SELECTOR = {
    "type": "object",
    "required": ["kind"],
    "properties": {"kind": STRING, "name": STRING, "owner_id": STRING},
    "additionalProperties": False,
}
PREPARE_BOUND_PARAMETERS = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": [
        "source_selector", "destination_selector", "binding_mode", "simulate_precommit_change",
        "mutated_source_state_revision", "mutated_destination_state_revision", "late_candidate_id",
        "late_candidate_state_revision", "transit_lease_id", "attached_object_policy", "result_world_revision", "event_id",
    ],
    "properties": {
        "source_selector": SELECTOR,
        "destination_selector": SELECTOR,
        "binding_mode": {"enum": ["PrepareBound", "Dynamic"]},
        "simulate_precommit_change": {"type": "boolean"},
        "mutated_source_state_revision": STRING,
        "mutated_destination_state_revision": STRING,
        "late_candidate_id": STRING,
        "late_candidate_state_revision": STRING,
        "transit_lease_id": STRING,
        "attached_object_policy": {"const": "ExplicitExcluded"},
        "result_world_revision": STRING,
        "event_id": STRING,
    },
    "additionalProperties": False,
}
REACTIVE_PARAMETERS = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["controller_id", "reactive_microstep_budget", "external_events", "generated_event_prefix", "tick_id", "emergency_stop_on_exhaustion"],
    "properties": {
        "controller_id": STRING,
        "reactive_microstep_budget": {"type": "integer", "minimum": 1},
        "external_events": {
            "type": "array",
            "minItems": 3,
            "items": {
                "type": "object",
                "required": ["event_id", "target_entity_id"],
                "properties": {"event_id": STRING, "target_entity_id": STRING},
                "additionalProperties": False,
            },
        },
        "generated_event_prefix": STRING,
        "tick_id": STRING,
        "emergency_stop_on_exhaustion": {"type": "boolean"},
    },
    "additionalProperties": False,
}


def register_debug_hell_extensions(
    semantic: SemanticHandlerRegistry,
    runtime: RuntimeExecutorRegistry,
    execution: ExecutionContractRegistry,
) -> None:
    semantic.register(SemanticHandlerRegistration("debug.pathological-planning", "1", "implemented", pathological_water_ball_handler))
    semantic.register(SemanticHandlerRegistration("debug.prepare-bound-transit", "1", "implemented", prepare_bound_transit_handler))
    semantic.register(SemanticHandlerRegistration("debug.reactive-budget", "1", "implemented", reactive_hydra_handler))
    runtime.register(RuntimeExecutorRegistration(
        "runtime.prepare-bound-transit", "1", prepare_bound_transit, PREPARE_BOUND_PARAMETERS,
        (ParameterReference("transit_lease_id", "leases"),), prepare_bound_toctou_hook,
    ))
    runtime.register(RuntimeExecutorRegistration(
        "runtime.reactive-hydra", "1", reactive_hydra_abort, REACTIVE_PARAMETERS,
        (ParameterReference("controller_id", "controllers"),),
    ))
    for semantic_id, runtime_id in (
        ("debug.pathological-planning", None),
        ("debug.prepare-bound-transit", "runtime.prepare-bound-transit"),
        ("debug.reactive-budget", "runtime.reactive-hydra"),
    ):
        execution.register(ExecutionContractRegistration(
            contract_id=f"execution:{semantic_id}", revision="1",
            semantic_contract=(semantic_id, "1"),
            runtime_contract=None if runtime_id is None else (runtime_id, "1"),
        ))
