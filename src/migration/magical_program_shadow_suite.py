"""Current contract suite layered on the stable shadow differential core."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Mapping

from . import magical_program_shadow as core
from .magical_program_shadow_debug import (
    translate_pathological_planning,
    translate_prepare_bound_transit,
    translate_reactive_hydra,
)
from .magical_program_shadow_explosion import (
    explosion_projection,
    translate_explosion,
)
from .magical_program_shadow_support import ShadowTranslation
from .magical_program_shadow_treatment import (
    staged_treatment_projection,
    translate_staged_treatment as _translate_staged_treatment,
)

core.DIAGNOSTIC_ALIASES.setdefault(
    "ProgramEnergyInsufficient", "ConservationProofFailure"
)

_JSON = dict[str, Any]
PATHOLOGICAL_PLANNING_PAIR: core.ContractPair = (
    ("debug.pathological-planning", "1"),
    None,
)
PREPARE_BOUND_TRANSIT_PAIR: core.ContractPair = (
    ("debug.prepare-bound-transit", "1"),
    ("runtime.prepare-bound-transit", "1"),
)
REACTIVE_HYDRA_PAIR: core.ContractPair = (
    ("debug.reactive-budget", "1"),
    ("runtime.reactive-hydra", "1"),
)
EXPLOSION_PAIR: core.ContractPair = (
    ("dynamics.explosion", "1"),
    ("runtime.explosion", "1"),
)
TREATMENT_STAGED_PAIR: core.ContractPair = (
    ("treatment.staged-repair", "1"),
    ("runtime.staged-treatment", "1"),
)


def translate_staged_treatment(bundle: Mapping[str, Any]) -> ShadowTranslation:
    normalized = copy.deepcopy(bundle)
    original_unique = bool(
        bundle["execution"]["parameters"]["correspondence_unique"]
    )
    normalized["execution"]["parameters"]["correspondence_unique"] = True
    built = _translate_staged_treatment(normalized)
    evidence = built.world.runtime_state.get("evidence", {})
    for record in evidence.values():
        if record.get("kind") == "UniqueCorrespondence":
            record["unique"] = original_unique
    return ShadowTranslation(
        built.program,
        built.world,
        built.evaluator,
        built.runtime,
        built.classification,
        core.bundle_contract_pair(bundle),
    )


def default_shadow_translators() -> core.ShadowTranslatorRegistry:
    registry = core.default_shadow_translators()
    registrations = (
        core.ShadowTranslatorRegistration(
            TREATMENT_STAGED_PAIR[0],
            TREATMENT_STAGED_PAIR[1],
            translate_staged_treatment,
        ),
        core.ShadowTranslatorRegistration(
            EXPLOSION_PAIR[0], EXPLOSION_PAIR[1], translate_explosion
        ),
        core.ShadowTranslatorRegistration(
            PATHOLOGICAL_PLANNING_PAIR[0],
            PATHOLOGICAL_PLANNING_PAIR[1],
            translate_pathological_planning,
        ),
        core.ShadowTranslatorRegistration(
            PREPARE_BOUND_TRANSIT_PAIR[0],
            PREPARE_BOUND_TRANSIT_PAIR[1],
            translate_prepare_bound_transit,
        ),
        core.ShadowTranslatorRegistration(
            REACTIVE_HYDRA_PAIR[0],
            REACTIVE_HYDRA_PAIR[1],
            translate_reactive_hydra,
        ),
    )
    for registration in registrations:
        registry.register(registration)
    return registry


def _treatment_projection(
    configuration: Mapping[str, Any], bundle: Mapping[str, Any]
) -> _JSON:
    parameters = bundle["execution"]["parameters"]
    return staged_treatment_projection(
        configuration,
        entity_ids={
            "patient": str(parameters["patient_id"]),
            "proxy": str(parameters["proxy_id"]),
            "sink": str(parameters["sink_id"]),
            "donor": str(parameters["donor_id"]),
            "reservoir": str(parameters["energy_reservoir_id"]),
        },
        event_ids=[str(item) for item in parameters["event_ids"]],
    )


def _treatment_accounting_matches(
    bundle: Mapping[str, Any], ledgers: Mapping[str, Any]
) -> bool:
    parameters = bundle["execution"]["parameters"]
    ledger = ledgers.get(str(parameters["ledger_id"]), {})
    thermal = float(parameters["excess_thermal_energy_j"])
    fluid = float(parameters["removable_fluid_kg"])
    donor = float(parameters["donor_matter_kg"])
    treatment_energy = float(parameters["repair_energy_j"]) + float(
        parameters["manifest_energy_j"]
    )
    allocations = ledger.get("allocations", {})
    expected_allocations = {
        "treatment_stabilize": {
            "energy_j": thermal,
            "matter_kg": fluid,
            "events": 1,
        },
        "treatment_repair": {
            "energy_j": float(parameters["repair_energy_j"]),
            "matter_kg": donor,
            "events": 1,
        },
        "treatment_manifest": {
            "energy_j": float(parameters["manifest_energy_j"]),
            "matter_kg": 0.0,
            "events": 1,
        },
    }
    allocation_match = all(
        key in allocations
        and all(
            allocations[key].get(field) == value
            for field, value in expected.items()
        )
        for key, expected in expected_allocations.items()
    )
    return (
        abs(float(ledger.get("transferred_to_sink_energy_j", -1.0)) - thermal)
        <= 1e-12
        and abs(
            float(ledger.get("treatment_energy_consumed_j", -1.0))
            - treatment_energy
        )
        <= 1e-12
        and abs(float(ledger.get("available_energy_j", -1.0))) <= 1e-12
        and abs(float(ledger.get("available_matter_kg", -1.0))) <= 1e-12
        and int(ledger.get("events_remaining", -1)) == 13
        and allocation_match
    )


def _explosion_entity_ids(bundle: Mapping[str, Any]) -> list[str]:
    parameters = bundle["execution"]["parameters"]
    region_id = str(parameters["region_id"])
    radius = float(parameters["radius_m"])
    affected = sorted(
        (
            (float(entity["distance_from_origin_m"]), str(entity_id))
            for entity_id, entity in bundle["initial_world"]["entities"].items()
            if entity.get("blast_subject") is True
            and entity.get("region_id") == region_id
            and 0.0
            <= float(entity.get("distance_from_origin_m", -1.0))
            <= radius
        ),
        key=lambda item: (item[0], item[1]),
    )
    return [
        str(parameters["origin_entity_id"]),
        str(parameters["reaction_anchor_id"]),
        *(entity_id for _, entity_id in affected),
    ]


def _explosion_projection(
    configuration: Mapping[str, Any], bundle: Mapping[str, Any]
) -> _JSON:
    parameters = bundle["execution"]["parameters"]
    return explosion_projection(
        configuration,
        entity_ids=_explosion_entity_ids(bundle),
        event_ids=[
            str(parameters["activation_event_id"]),
            str(parameters["termination_event_id"]),
        ],
    )


def _explosion_accounting_matches(
    bundle: Mapping[str, Any], ledgers: Mapping[str, Any]
) -> bool:
    parameters = bundle["execution"]["parameters"]
    ledger = ledgers.get(str(parameters["ledger_id"]), {})
    energy = float(parameters["release_energy_j"])
    pressure = energy * float(parameters["pressure_energy_fraction"])
    thermal = energy * float(parameters["thermal_energy_fraction"])
    radius = float(parameters["radius_m"])
    impulse_limit = float(parameters["maximum_impulse_kg_m_s"])
    reaction = -sum(
        impulse_limit
        * max(0.0, 1.0 - float(entity["distance_from_origin_m"]) / radius)
        for entity in bundle["initial_world"]["entities"].values()
        if entity.get("blast_subject") is True
        and entity.get("region_id") == parameters["region_id"]
        and 0.0
        <= float(entity.get("distance_from_origin_m", -1.0))
        <= radius
    )
    allocation = ledger.get("allocations", {}).get(
        "invoke_bounded_explosion", {}
    )
    return (
        abs(float(ledger.get("available_energy_j", -1.0)) - 1000.0)
        <= 1e-12
        and abs(float(ledger.get("released_energy_j", -1.0)) - energy)
        <= 1e-12
        and abs(float(ledger.get("pressure_energy_j", -1.0)) - pressure)
        <= 1e-12
        and abs(float(ledger.get("thermal_energy_j", -1.0)) - thermal)
        <= 1e-12
        and abs(
            float(ledger.get("reaction_impulse_kg_m_s", 1.0)) - reaction
        )
        <= 1e-12
        and allocation.get("energy_j") == energy
        and allocation.get("matter_kg") == 0.0
        and allocation.get("events") == 2
        and int(ledger.get("events_remaining", -1)) == 14
    )


def run_shadow_file(
    path: str | Path,
    *,
    translators: core.ShadowTranslatorRegistry | None = None,
    golden_input: str | Path | None = None,
    variant_id: str | None = None,
    golden_manifest: str | Path = core._DEFAULT_GOLDEN_MANIFEST,
) -> _JSON:
    registry = translators or default_shadow_translators()
    result = core.run_shadow_file(
        path,
        translators=registry,
        golden_input=golden_input,
        variant_id=variant_id,
        golden_manifest=golden_manifest,
    )
    pair: core.ContractPair = (
        tuple(result["source_contract_pair"]["semantic"]),
        None
        if result["source_contract_pair"]["runtime"] is None
        else tuple(result["source_contract_pair"]["runtime"]),
    )
    if pair == PATHOLOGICAL_PLANNING_PAIR:
        result["comparisons"]["runtime_status"] = (
            result.get("generic_execution") is None
            and result.get("legacy", {}).get("execution") is None
        )
        result["comparisons"]["replay_status"] = (
            result.get("generic_replay") is None
            and result.get("legacy", {}).get("replay") is None
        )
        result["status"] = (
            "PASS" if all(result["comparisons"].values()) else "FAIL"
        )
        return result
    if pair not in {TREATMENT_STAGED_PAIR, EXPLOSION_PAIR}:
        return result

    execution = result.get("generic_execution")
    if isinstance(execution, dict) and execution.get("status") == "Committed":
        bundle = json.loads(Path(path).read_text(encoding="utf-8"))
        if pair == TREATMENT_STAGED_PAIR:
            result["comparisons"]["contract_projection"] = (
                _treatment_projection(
                    result["legacy"].get("final_world", {}), bundle
                )
                == _treatment_projection(result["generic_final_world"], bundle)
            )
            result["comparisons"]["contract_accounting"] = (
                _treatment_accounting_matches(
                    bundle, result["generic_final_ledgers"]
                )
            )
        else:
            result["comparisons"]["contract_projection"] = (
                _explosion_projection(
                    result["legacy"].get("final_world", {}), bundle
                )
                == _explosion_projection(result["generic_final_world"], bundle)
            )
            result["comparisons"]["contract_accounting"] = (
                _explosion_accounting_matches(
                    bundle, result["generic_final_ledgers"]
                )
            )
    result["status"] = (
        "PASS" if all(result["comparisons"].values()) else "FAIL"
    )
    return result


BOUNDARY_REFLECTION_PAIR = core.BOUNDARY_REFLECTION_PAIR
EVIDENCE_FUSION_PAIR = core.EVIDENCE_FUSION_PAIR
UNSUPPORTED_CONTRACTS = core.UNSUPPORTED_CONTRACTS
ShadowTranslatorRegistration = core.ShadowTranslatorRegistration
ShadowTranslatorRegistry = core.ShadowTranslatorRegistry
bundle_contract_pair = core.bundle_contract_pair

__all__ = [
    "BOUNDARY_REFLECTION_PAIR",
    "EVIDENCE_FUSION_PAIR",
    "EXPLOSION_PAIR",
    "PATHOLOGICAL_PLANNING_PAIR",
    "PREPARE_BOUND_TRANSIT_PAIR",
    "REACTIVE_HYDRA_PAIR",
    "TREATMENT_STAGED_PAIR",
    "UNSUPPORTED_CONTRACTS",
    "ShadowTranslatorRegistration",
    "ShadowTranslatorRegistry",
    "bundle_contract_pair",
    "default_shadow_translators",
    "run_shadow_file",
    "translate_explosion",
    "translate_pathological_planning",
    "translate_prepare_bound_transit",
    "translate_reactive_hydra",
    "translate_staged_treatment",
]
