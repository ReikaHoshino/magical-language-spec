"""Runtime behavior independent of every fixture suite extension."""
from __future__ import annotations

from typing import Any

from src.runtime.sandbox import PreparedPlan, RuntimeExecutionError, SandboxWorld


def generic_transition_executor(prepared: PreparedPlan, world: SandboxWorld) -> dict[str, Any]:
    parameters = prepared.typed_mir["typed_parameters"]
    source = world.entities.get(parameters["source_entity_id"])
    target = world.entities.get(parameters["target_entity_id"])
    ledger = world.ledgers.get(parameters["ledger_id"])
    if source is None or target is None:
        raise RuntimeExecutionError("ResolutionFailure", "Generic extension entities are absent.", stage="COMMIT")
    if ledger is None or not ledger.get("active"):
        raise RuntimeExecutionError("ConservationProofFailure", "Generic extension ledger is unavailable.", stage="COMMIT")
    energy = float(parameters["energy_j"])
    if float(ledger.get("available_energy_j", 0)) < energy:
        raise RuntimeExecutionError("ConservationProofFailure", "Generic extension Energy is not accounted.", stage="COMMIT")
    ledger["available_energy_j"] -= energy
    ledger["consumed_energy_j"] = float(ledger.get("consumed_energy_j", 0)) + energy
    target["transition_state"] = parameters["result_state"]
    world.revision = parameters["result_world_revision"]
    world.history.append({
        "event_id": parameters["event_id"],
        "effect_kind": "IndependentGenericTransition",
        "source_world_revision": prepared.source_world_revision,
        "result_world_revision": world.revision,
    })
    return {
        "operations": [
            {"operation": operation, "ordinal": index, "status": "Committed"}
            for index, operation in enumerate(prepared.operations)
        ],
        "world_effect": {
            "source_world_revision": prepared.source_world_revision,
            "result_world_revision": world.revision,
            "history_event_id": parameters["event_id"],
            "effect_kind": "IndependentGenericTransition",
            "entity_identity_policy": "PreserveExistingIdentity",
        },
    }
