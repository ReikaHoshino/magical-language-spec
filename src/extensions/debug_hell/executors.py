"""Deterministic adversarial runtime state machines owned by Issue #46."""
from __future__ import annotations

import copy
from typing import Any

from src.runtime.sandbox import PreparedPlan, RuntimeExecutionError, SandboxWorld


def prepare_bound_toctou_hook(prepared: PreparedPlan, world: SandboxWorld) -> None:
    """Apply an external symbolic-world change after PREPARE, before revalidation."""

    p = prepared.typed_mir["typed_parameters"]
    if not p["simulate_precommit_change"]:
        return
    bound_source = world.entities[p["bound_source_entity_id"]]
    bound_destination = world.entities[p["bound_destination_entity_id"]]
    bound_source["name"] = "Marcus-Renamed-After-Prepare"
    bound_source["distance_to_selector_m"] = 8
    bound_source["state_revision"] = p["mutated_source_state_revision"]
    bound_destination["state_revision"] = p["mutated_destination_state_revision"]
    world.entities[p["late_candidate_id"]] = {
        "entity_id": p["late_candidate_id"],
        "state_revision": p["late_candidate_state_revision"],
        "kind": "Professor",
        "name": "Marcus",
        "distance_to_selector_m": 0.5,
    }
    world.leases[p["transit_lease_id"]]["active"] = False
    world.runtime_state["external_change"] = {
        "after_prepare": True,
        "original_bound_source_entity_id": p["bound_source_entity_id"],
        "late_candidate_id": p["late_candidate_id"],
        "silent_retarget": False,
    }


def prepare_bound_transit(prepared: PreparedPlan, world: SandboxWorld) -> dict[str, Any]:
    p = prepared.typed_mir["typed_parameters"]
    source = world.entities.get(p["bound_source_entity_id"])
    destination = world.entities.get(p["bound_destination_entity_id"])
    if source is None or destination is None:
        raise RuntimeExecutionError("ResolutionFailure", "Prepare-bound transit identities are absent.", stage="COMMIT")
    if source.get("state_revision") != p["bound_source_state_revision"] or destination.get("state_revision") != p["bound_destination_state_revision"]:
        raise RuntimeExecutionError(
            "PrepareBoundIdentityChanged",
            "Prepare-bound identity/revision changed; silent retargeting is forbidden.",
            stage="COMMIT",
            internal_trace={
                "bound_source_entity_id": p["bound_source_entity_id"],
                "bound_destination_entity_id": p["bound_destination_entity_id"],
                "binding_mode": p["binding_mode"],
                "silent_retarget": False,
            },
        )
    source["location_id"] = p["bound_destination_entity_id"]
    world.revision = p["result_world_revision"]
    world.history.append({
        "event_id": p["event_id"],
        "effect_kind": "PrepareBoundTransit",
        "source_entity_id": p["bound_source_entity_id"],
        "destination_entity_id": p["bound_destination_entity_id"],
        "attached_objects_transferred": False,
    })
    return {
        "operations": [{"operation": operation, "ordinal": index, "status": "Committed"} for index, operation in enumerate(prepared.operations)],
        "world_effect": {
            "source_world_revision": prepared.source_world_revision,
            "result_world_revision": world.revision,
            "history_event_id": p["event_id"],
            "effect_kind": "PrepareBoundTransit",
            "entity_identity_policy": "PrepareBoundExistingIdentity",
        },
    }


def reactive_hydra_abort(prepared: PreparedPlan, world: SandboxWorld) -> dict[str, Any]:
    """Execute bounded self-triggering microsteps, then abort deterministically."""

    p = prepared.typed_mir["typed_parameters"]
    controller = world.controllers.get(p["controller_id"])
    if controller is None or not controller.get("active"):
        raise RuntimeExecutionError("AuthorityError", "Reactive controller is absent or inactive.", stage="COMMIT")
    queue = sorted(copy.deepcopy(p["external_events"]), key=lambda item: item["event_id"])
    executed: list[dict[str, Any]] = []
    budget = int(p["reactive_microstep_budget"])
    for microstep in range(budget):
        if not queue:
            break
        source_event = queue.pop(0)
        generated_id = f"{p['generated_event_prefix']}:{microstep}"
        record = {
            "microstep": microstep,
            "tick": p["tick_id"],
            "source_event_id": source_event["event_id"],
            "generated_event_id": generated_id,
            "causal_parent_id": source_event["event_id"],
            "execution_ordinal": microstep,
            "resource_units": 1,
        }
        executed.append(record)
        controller["provisional_transition_count"] = microstep + 1
        world.history.append({"event_id": generated_id, "effect_kind": "ProvisionalHydraTransition", "committed": False})
        queue.insert(0, {"event_id": generated_id, "target_entity_id": source_event["target_entity_id"]})

    trace = {
        "controller_id": p["controller_id"],
        "tick": p["tick_id"],
        "external_event_order": [item["event_id"] for item in sorted(p["external_events"], key=lambda item: item["event_id"])],
        "executed_microsteps": executed,
        "budget": budget,
        "exhausted_at_microstep": budget,
        "pending_event_ids": [item["event_id"] for item in queue],
        "transaction_committed": False,
        "emergency_stop_requested": bool(p["emergency_stop_on_exhaustion"]),
    }
    raise RuntimeExecutionError(
        "MicrostepBudgetExceeded",
        f"Reactive controller exhausted its deterministic budget after {budget} executed microsteps.",
        stage="COMMIT",
        internal_trace=trace,
    )
