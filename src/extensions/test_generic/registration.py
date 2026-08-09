"""Registration surface for the independent generic extension."""
from __future__ import annotations

from src.artifacts.execution_contract_registry import ExecutionContractRegistration, ExecutionContractRegistry
from src.evaluator.handler_registry import SemanticHandlerRegistration, SemanticHandlerRegistry
from src.runtime.executor_registry import ParameterReference, RuntimeExecutorRegistration, RuntimeExecutorRegistry

from .executor import generic_transition_executor
from .handler import generic_transition_handler


GENERIC_PARAMETER_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["source_entity_id", "target_entity_id", "ledger_id", "energy_j", "result_state", "result_world_revision", "event_id"],
    "properties": {
        "source_entity_id": {"type": "string", "minLength": 1},
        "target_entity_id": {"type": "string", "minLength": 1},
        "ledger_id": {"type": "string", "minLength": 1},
        "energy_j": {"type": "number", "minimum": 0},
        "result_state": {"type": "string", "minLength": 1},
        "result_world_revision": {"type": "string", "minLength": 1},
        "event_id": {"type": "string", "minLength": 1},
    },
    "additionalProperties": False,
}


def register_test_generic_extension(
    semantic: SemanticHandlerRegistry,
    runtime: RuntimeExecutorRegistry,
    execution: ExecutionContractRegistry,
) -> None:
    semantic.register(SemanticHandlerRegistration(
        "example.generic-transition", "1", "implemented", generic_transition_handler,
    ))
    runtime.register(RuntimeExecutorRegistration(
        "runtime.generic-transition",
        "1",
        generic_transition_executor,
        GENERIC_PARAMETER_SCHEMA,
        (
            ParameterReference("source_entity_id", "entities"),
            ParameterReference("target_entity_id", "entities"),
            ParameterReference("ledger_id", "ledgers"),
        ),
    ))
    execution.register(ExecutionContractRegistration(
        contract_id="execution:example.generic-transition",
        revision="1",
        semantic_contract=("example.generic-transition", "1"),
        runtime_contract=("runtime.generic-transition", "1"),
    ))
