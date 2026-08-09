"""Explicit default extension registration; no suite or fixture dispatch."""
from __future__ import annotations

from src.artifacts.execution_contract_registry import ExecutionContractRegistration, ExecutionContractRegistry
from src.evaluator.handler_registry import SemanticHandlerRegistration, SemanticHandlerRegistry
from src.runtime.executor_registry import ParameterReference, RuntimeExecutorRegistration, RuntimeExecutorRegistry

from .debug_hell.registration import register_debug_hell_extensions
from .parameter_schemas import (
    BOUNDARY_REFLECTION_PARAMETERS,
    EVIDENCE_FUSION_PARAMETERS,
    EXPLOSION_PARAMETERS,
    STAGED_TREATMENT_PARAMETERS,
)
from .shared import feasible_handler, unsupported_handler
from .success_arcana.executors import boundary_reflection, evidence_fusion, explosion, staged_treatment
from .success_arcana.handlers import explosion_handler
from .test_generic.registration import register_test_generic_extension


def register_default_extensions(
    semantic: SemanticHandlerRegistry,
    runtime: RuntimeExecutorRegistry,
    execution: ExecutionContractRegistry,
) -> None:
    feasible = (
        "controller.boundary-reflection",
        "treatment.staged-repair",
        "evidence.snapshot-fusion",
    )
    unsupported = (
        "light.guidance",
        "dynamics.levitation",
        "matter.purification",
        "observer.poison-detection",
    )
    for contract_id in feasible:
        semantic.register(SemanticHandlerRegistration(contract_id, "1", "implemented", feasible_handler))
    for contract_id in unsupported:
        semantic.register(SemanticHandlerRegistration(contract_id, "1", "recognized-unsupported", unsupported_handler))
    semantic.register(SemanticHandlerRegistration("dynamics.explosion", "1", "implemented", explosion_handler))

    for contract_id, executor, parameter_schema, references in (
        (
            "runtime.boundary-controller", boundary_reflection, BOUNDARY_REFLECTION_PARAMETERS,
            (ParameterReference("target_entity_id", "entities"), ParameterReference("reaction_anchor_id", "entities"), ParameterReference("ledger_id", "ledgers")),
        ),
        (
            "runtime.staged-treatment", staged_treatment, STAGED_TREATMENT_PARAMETERS,
            tuple(ParameterReference(field, "entities") for field in ("patient_id", "proxy_id", "sink_id", "donor_id", "energy_reservoir_id"))
            + (ParameterReference("patient_lease_id", "leases"), ParameterReference("ledger_id", "ledgers")),
        ),
        (
            "runtime.evidence-artifact", evidence_fusion, EVIDENCE_FUSION_PARAMETERS,
            (ParameterReference("subject_id", "entities"), ParameterReference("ledger_id", "ledgers")),
        ),
        (
            "runtime.explosion", explosion, EXPLOSION_PARAMETERS,
            (
                ParameterReference("origin_entity_id", "entities"), ParameterReference("reaction_anchor_id", "entities"),
                ParameterReference("ledger_id", "ledgers"), ParameterReference("capability_id", "capabilities"), ParameterReference("lease_id", "leases"),
            ),
        ),
    ):
        runtime.register(RuntimeExecutorRegistration(contract_id, "1", executor, parameter_schema, references))

    pairs = (
        ("controller.boundary-reflection", "runtime.boundary-controller"),
        ("treatment.staged-repair", "runtime.staged-treatment"),
        ("evidence.snapshot-fusion", "runtime.evidence-artifact"),
        ("dynamics.explosion", "runtime.explosion"),
    )
    for semantic_id, runtime_id in pairs:
        execution.register(ExecutionContractRegistration(
            contract_id=f"execution:{semantic_id}",
            revision="1",
            semantic_contract=(semantic_id, "1"),
            runtime_contract=(runtime_id, "1"),
        ))
    for semantic_id in unsupported:
        execution.register(ExecutionContractRegistration(
            contract_id=f"execution:{semantic_id}",
            revision="1",
            semantic_contract=(semantic_id, "1"),
            runtime_contract=None,
        ))
    register_debug_hell_extensions(semantic, runtime, execution)
    register_test_generic_extension(semantic, runtime, execution)
