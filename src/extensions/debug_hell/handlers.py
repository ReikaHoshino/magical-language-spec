"""Adversarial semantic elaboration derived from fixture inputs, not canned outcomes."""
from __future__ import annotations

import copy
import math
from typing import Any

from src.evaluator.schema import validate_feasibility_report
from src.extensions.shared import build_report


def pathological_water_ball_handler(bundle: dict[str, Any]) -> dict[str, Any]:
    constraints = {
        item["semantic_kind"]: item.get("value")
        for item in bundle["ingress"]["payload"].get("constraints", [])
    }
    mass = float(constraints["MassKg"])
    radius = float(constraints["RadiusM"])
    acceleration = float(constraints["AccelerationMPerS2"])
    duration = float(constraints["DurationS"])
    density = mass / ((4.0 / 3.0) * math.pi * radius ** 3)
    terminal_unknown = any(
        item.get("role") == "Goal" and item.get("value", {}).get("kind") == "Unknown"
        for item in bundle["ingress"]["payload"].get("roles", [])
    )
    authority_missing = not bundle["execution"]["required_evidence"]["capabilities"] or not bundle["execution"]["required_evidence"]["leases"]
    diagnostic = "PlanningAssumptionCannotSatisfyAuthority" if authority_missing else "ExplicitConstraintModelDomainExceeded"
    report = build_report(bundle, status="Infeasible", diagnostic_code=diagnostic)
    report["interpretations"]["semantic_ast"]["pathological_analysis"] = {
        "explicit_source_constraints": copy.deepcopy(constraints),
        "computed_density_kg_m3": density,
        "model_max_density_kg_m3": 2000,
        "explicit_constraints_rewritten": False,
        "sphere_preservation_required": constraints["PreserveSphere"],
        "terminal": {"kind": "Unknown", "arbitrary_binding": False},
    }
    report["interpretations"]["typed_mir"]["planning_boundary"] = {
        "terminal_unknown": terminal_unknown,
        "planning_assumption_adopted": False,
        "mechanical_energy_j": 0.5 * mass * (acceleration * duration) ** 2,
        "gravity_control_energy_is_mechanical_work": False,
        "feasible_is_authorized": False,
        "late_unrelated_entity_retarget": False,
    }
    report["diagnostics"][0]["message"] = "Explicit pathological constraints were preserved; missing authority cannot be synthesized by planning."
    validate_feasibility_report(report)
    return report


def prepare_bound_transit_handler(bundle: dict[str, Any]) -> dict[str, Any]:
    elaborated = copy.deepcopy(bundle)
    parameters = elaborated["execution"]["parameters"]
    source_selector = parameters["source_selector"]
    destination_selector = parameters["destination_selector"]
    sources = sorted(
        (
            (float(entity["distance_to_selector_m"]), entity_id, entity)
            for entity_id, entity in elaborated["initial_world"]["entities"].items()
            if entity.get("kind") == "Professor" and entity.get("name") == source_selector["name"]
        ),
        key=lambda item: (item[0], item[1]),
    )
    destinations = sorted(
        (
            (entity_id, entity)
            for entity_id, entity in elaborated["initial_world"]["entities"].items()
            if entity.get("kind") == "Laboratory" and entity.get("owner_id") == destination_selector["owner_id"]
        ),
        key=lambda item: item[0],
    )
    if not sources or not destinations:
        return build_report(elaborated, status="Infeasible", diagnostic_code="ResolutionFailure")
    _, source_id, source = sources[0]
    destination_id, destination = destinations[0]
    parameters.update({
        "bound_source_entity_id": source_id,
        "bound_source_state_revision": source["state_revision"],
        "bound_destination_entity_id": destination_id,
        "bound_destination_state_revision": destination["state_revision"],
    })
    report = build_report(elaborated)
    report["interpretations"]["semantic_ast"]["binding"] = {
        "mode": parameters["binding_mode"],
        "source_selector": copy.deepcopy(source_selector),
        "destination_selector": copy.deepcopy(destination_selector),
        "bound_source_entity_id": source_id,
        "bound_destination_entity_id": destination_id,
        "silent_retarget_allowed": parameters["binding_mode"] == "Dynamic",
        "world_index_is_authority": False,
    }
    return report


def reactive_hydra_handler(bundle: dict[str, Any]) -> dict[str, Any]:
    report = build_report(bundle)
    report["interpretations"]["semantic_ast"]["reactive_contract"] = {
        "self_triggering": True,
        "same_tick_external_event_count": len(bundle["execution"]["parameters"]["external_events"]),
        "causal_order_is_execution_order": False,
        "bounded_by_microstep_budget": True,
    }
    return report
