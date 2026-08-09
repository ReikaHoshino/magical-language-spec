"""Generic MagicalProgram migration for a finite prepare-bound explosion."""
from __future__ import annotations

import copy
from typing import Any, Mapping

from src.evaluator.magical_program import MagicalProgramEvaluator
from src.evaluator.magical_program_contracts import (
    ProgramContractRegistration,
    ProgramContractRegistry,
    default_program_contract_registry,
)
from src.runtime.magical_program import (
    MagicalProgramRuntime,
    ProgramRuntimeContractRegistry,
    ProgramRuntimeError,
    RuntimeContractRegistration,
)
from src.runtime.magical_program_model import (
    PreparedProgramEffect,
    RuntimeExecutionContext,
    next_world_revision,
)
from src.runtime.sandbox import SandboxWorld

from .magical_program_shadow_support import (
    ShadowTranslation,
    add_identity_record,
    bundle_contract_pair,
    configure_capability,
    configure_lease,
    configure_ledger,
    profile_from_bundle,
    program_envelope,
    world_from_bundle,
)

_JSON = dict[str, Any]
_CONTRACT_ID = "dynamics.explosion"
_CONTRACT_REVISION = "1"
_MODEL = {
    "model_id": "model:explosion-fixture",
    "revision": "1",
    "medium": "synthetic-air",
    "valid_radius_m": 10,
    "attenuation_policy": "LinearRadialV1",
    "occlusion_policy": "NoOcclusionFixtureDomain",
    "provenance": "reference/success-arcana.md#success-arcana-004",
}


def _record(type_id: str, **fields: Any) -> _JSON:
    return {
        "kind": "record",
        "type_id": type_id,
        "fields": {
            key: {"kind": "literal", "value": value}
            for key, value in fields.items()
        },
    }


def _literal(record: Mapping[str, Any], field: str) -> Any:
    return record["fields"][field]["value"]


def explosion_semantic_registry() -> ProgramContractRegistry:
    registry = default_program_contract_registry()
    registry.register(
        ProgramContractRegistration(
            _CONTRACT_ID,
            _CONTRACT_REVISION,
            "effect.invoke",
            (
                "reference",
                "reference",
                "record:ExplosionModel",
                "record:ExplosionPolicy",
                "record:ExplosionPublication",
            ),
            "effect_result",
            ("capabilities", "leases", "identities", "evidence", "accounting"),
            0.0,
            0.0,
            2,
            ("RESOLVE", "OBSERVE", "CHANNEL", "TRANSFER", "RECONFIGURE", "CONSTRAIN"),
            ("SAMPLE", "TRANSITION", "ACTIVATE"),
        )
    )
    return registry


def _require_exact_host_model(bundle: Mapping[str, Any]) -> None:
    models = bundle.get("registry_extensions", {}).get("explosion_models", [])
    if models != [_MODEL]:
        raise ValueError(
            "explosion model declaration must exactly match the host registration"
        )


def _validate_model(model: Mapping[str, Any]) -> None:
    observed = {
        "model_id": str(_literal(model, "model_id")),
        "revision": str(_literal(model, "revision")),
        "medium": str(_literal(model, "medium")),
        "valid_radius_m": int(_literal(model, "valid_radius_m")),
        "attenuation_policy": str(_literal(model, "attenuation_policy")),
        "occlusion_policy": str(_literal(model, "occlusion_policy")),
    }
    expected = {key: _MODEL[key] for key in observed}
    if observed != expected:
        raise ProgramRuntimeError(
            "ExplosionModelMismatch",
            "Explosion model identity or host safety policy is invalid.",
            stage="COMMIT",
        )


def _evidence(effect: PreparedProgramEffect) -> Mapping[str, Any]:
    if len(effect.evidence_records) != 1:
        raise ProgramRuntimeError(
            "StaleReference",
            "Exactly one prepare-bound affected-set record is required.",
            stage="COMMIT",
        )
    record = effect.evidence_records[0].frozen_record
    if record.get("kind") != "ExplosionAffectedSet":
        raise ProgramRuntimeError(
            "StaleReference",
            "Explosion affected-set evidence has the wrong kind.",
            stage="COMMIT",
        )
    return record


def explosion_executor(
    context: RuntimeExecutionContext,
    effect: PreparedProgramEffect,
    world: SandboxWorld,
) -> _JSON:
    del context
    origin_ref, anchor_ref, model, policy, publication = effect.frozen_values
    origin_id = str(origin_ref["entity_id"])
    anchor_id = str(anchor_ref["entity_id"])
    origin = world.entities.get(origin_id)
    anchor = world.entities.get(anchor_id)
    if origin is None or anchor is None:
        raise ProgramRuntimeError(
            "ResolutionFailure",
            "Explosion origin or reaction anchor is absent.",
            stage="COMMIT",
        )

    _validate_model(model)
    evidence = _evidence(effect)
    if evidence.get("source_world_revision") != world.revision:
        raise ProgramRuntimeError(
            "StaleReference",
            "Explosion observation revision is stale.",
            stage="COMMIT",
        )
    if (
        evidence.get("medium_revision") != origin.get("medium_revision")
        or evidence.get("medium_revision")
        != str(_literal(policy, "medium_revision"))
    ):
        raise ProgramRuntimeError(
            "ExplosionModelMismatch",
            "Explosion medium model revision is not authoritative.",
            stage="COMMIT",
        )

    radius = float(_literal(policy, "radius_m"))
    maximum_radius = float(_literal(policy, "maximum_radius_m"))
    peak_pressure = float(_literal(policy, "peak_pressure_pa"))
    maximum_pressure = float(_literal(policy, "maximum_peak_pressure_pa"))
    maximum_impulse = float(_literal(policy, "maximum_impulse_kg_m_s"))
    energy = float(_literal(policy, "release_energy_j"))
    pressure_fraction = float(_literal(policy, "pressure_energy_fraction"))
    thermal_fraction = float(_literal(policy, "thermal_energy_fraction"))
    maximum_thermal = float(_literal(policy, "maximum_thermal_energy_j"))
    duration = float(_literal(policy, "duration_s"))
    maximum_targets = int(_literal(policy, "maximum_affected_entities"))
    region_id = str(_literal(policy, "region_id"))

    if radius <= 0.0 or radius > maximum_radius or radius > float(_MODEL["valid_radius_m"]):
        raise ProgramRuntimeError(
            "ExplosionDomainExceeded",
            "Explosion radius exceeds the admitted domain.",
            stage="COMMIT",
        )
    if peak_pressure < 0.0 or peak_pressure > maximum_pressure:
        raise ProgramRuntimeError(
            "ExplosionPressureExceeded",
            "Explosion peak pressure exceeds the admitted envelope.",
            stage="COMMIT",
        )
    if (
        energy < 0.0
        or maximum_impulse < 0.0
        or maximum_thermal < 0.0
        or duration < 0.0
        or pressure_fraction < 0.0
        or thermal_fraction < 0.0
        or abs((pressure_fraction + thermal_fraction) - 1.0) > 1e-12
    ):
        raise ProgramRuntimeError(
            "ExplosionAccountingMismatch",
            "Explosion Energy allocation or bounds are invalid.",
            stage="COMMIT",
        )
    thermal_energy = energy * thermal_fraction
    if thermal_energy > maximum_thermal:
        raise ProgramRuntimeError(
            "ExplosionThermalExceeded",
            "Explosion thermal allocation exceeds the admitted envelope.",
            stage="COMMIT",
        )

    targets = list(evidence.get("targets", []))
    if len(targets) > maximum_targets:
        raise ProgramRuntimeError(
            "ExplosionTargetLimitExceeded",
            "Prepare-bound target count exceeds the admitted envelope.",
            stage="COMMIT",
        )
    previous_distance = -1.0
    previous_pressure = float("inf")
    affected: list[tuple[dict[str, Any], float, float, float]] = []
    weights: list[float] = []
    for target in targets:
        entity_id = str(target.get("entity_id"))
        entity = world.entities.get(entity_id)
        if (
            entity is None
            or entity.get("state_revision") != target.get("state_revision")
            or entity.get("region_id") != region_id
            or entity.get("blast_subject") is not True
        ):
            raise ProgramRuntimeError(
                "StaleReference",
                "Prepare-bound explosion target is no longer authoritative.",
                stage="COMMIT",
            )
        distance = float(entity.get("distance_from_origin_m", -1.0))
        if distance < 0.0 or distance > radius or distance + 1e-12 < previous_distance:
            raise ProgramRuntimeError(
                "ExplosionAttenuationViolation",
                "Affected targets must remain in deterministic radial order.",
                stage="COMMIT",
            )
        attenuation = max(0.0, 1.0 - distance / radius)
        pressure = peak_pressure * attenuation
        impulse = maximum_impulse * attenuation
        if pressure > previous_pressure + 1e-12:
            raise ProgramRuntimeError(
                "ExplosionAttenuationViolation",
                "Explosion attenuation must be non-increasing by distance.",
                stage="COMMIT",
            )
        previous_distance = distance
        previous_pressure = pressure
        weights.append(attenuation)
        affected.append((entity, attenuation, pressure, impulse))

    total_weight = sum(weights)
    reaction_impulse = 0.0
    for entity, attenuation, pressure, impulse in affected:
        allocated_thermal = (
            0.0 if total_weight == 0.0 else thermal_energy * attenuation / total_weight
        )
        entity["blast_effect"] = {
            "pressure_pa": pressure,
            "radial_impulse_kg_m_s": impulse,
            "thermal_energy_j": allocated_thermal,
            "duration_s": duration,
        }
        reaction_impulse += impulse

    anchor["reaction_impulse_kg_m_s"] = float(
        anchor.get("reaction_impulse_kg_m_s", 0.0)
    ) - reaction_impulse
    ledger = world.ledgers[effect.accounting_records[0].record_id]
    ledger.update(
        {
            "released_energy_j": energy,
            "pressure_energy_j": energy * pressure_fraction,
            "thermal_energy_j": thermal_energy,
            "reaction_impulse_kg_m_s": -reaction_impulse,
        }
    )
    source_revision = world.revision
    world.revision = next_world_revision(source_revision)
    activation_event_id = str(_literal(publication, "activation_event_id"))
    termination_event_id = str(_literal(publication, "termination_event_id"))
    affected_ids = [str(target["entity_id"]) for target in targets]
    world.history.extend(
        [
            {
                "event_id": activation_event_id,
                "effect_kind": "BoundedExplosionActivated",
                "affected_entity_ids": affected_ids,
                "released_energy_j": energy,
                "source_world_revision": source_revision,
            },
            {
                "event_id": termination_event_id,
                "effect_kind": "BoundedExplosionTerminated",
                "duration_s": duration,
                "result_world_revision": world.revision,
            },
        ]
    )
    return {
        "kind": "effect_result",
        "status": "Committed",
        "node_id": effect.node_id,
        "contract_id": effect.contract_id,
        "contract_revision": effect.contract_revision,
        "entity_ids": [origin_id, anchor_id, *affected_ids],
        "event_id": termination_event_id,
        "history_event_ids": [activation_event_id, termination_event_id],
        "effect_kind": "BoundedExplosion",
        "identity_policy": "PrepareBoundExistingIdentity",
        "source_world_revision": source_revision,
        "result_world_revision": world.revision,
    }


def _affected_set(bundle: Mapping[str, Any], world: SandboxWorld) -> list[_JSON]:
    parameters = bundle["execution"]["parameters"]
    region_id = str(parameters["region_id"])
    radius = float(parameters["radius_m"])
    rows = []
    for entity in world.entities.values():
        if (
            entity.get("blast_subject") is True
            and entity.get("region_id") == region_id
            and 0.0 <= float(entity.get("distance_from_origin_m", -1.0)) <= radius
        ):
            rows.append(
                {
                    "entity_id": str(entity["entity_id"]),
                    "state_revision": str(entity["state_revision"]),
                    "distance_from_origin_m": float(entity["distance_from_origin_m"]),
                }
            )
    return sorted(rows, key=lambda item: (item["distance_from_origin_m"], item["entity_id"]))


def translate_explosion(bundle: Mapping[str, Any]) -> ShadowTranslation:
    _require_exact_host_model(bundle)
    parameters = bundle["execution"]["parameters"]
    required = bundle["execution"]["required_evidence"]
    origin_id = str(parameters["origin_entity_id"])
    anchor_id = str(parameters["reaction_anchor_id"])
    ledger_id = str(parameters["ledger_id"])
    profile = profile_from_bundle(bundle)
    world = world_from_bundle(bundle, profile)

    capability_ids = [str(item) for item in required["capabilities"]]
    lease_ids = [str(item) for item in required["leases"]]
    accounting_ids = [str(item) for item in required["accounting"]]
    if len(capability_ids) != 1 or len(lease_ids) != 1 or accounting_ids != [ledger_id]:
        raise ValueError("bounded explosion requires one Capability, Lease, and ledger")
    configure_capability(
        world,
        capability_ids[0],
        entity_id=origin_id,
        effect="Reconfigure",
    )
    configure_lease(world, lease_ids[0], entity_id=origin_id, mode="Actuate")
    configure_ledger(
        world,
        ledger_id,
        entity_id=origin_id,
        kind="BoundedExplosionAccounting",
        default_events=profile.max_events,
    )
    add_identity_record(world, origin_id, str(world.entities[origin_id]["state_revision"]))
    add_identity_record(world, anchor_id, str(world.entities[anchor_id]["state_revision"]))

    evidence_id = "evidence:bounded-explosion:affected-set"
    world.runtime_state["evidence"][evidence_id] = {
        "active": True,
        "entity_id": origin_id,
        "state_revision": str(world.entities[origin_id]["state_revision"]),
        "kind": "ExplosionAffectedSet",
        "source_world_revision": str(parameters["observation_world_revision"]),
        "medium_revision": str(parameters["medium_model"]["medium_revision"]),
        "targets": _affected_set(bundle, world),
        "revision": "1",
    }

    values = [
        {"value_id": "origin_selector", "kind": "selector", "selector": {"entity_id": origin_id}},
        {"value_id": "anchor_selector", "kind": "selector", "selector": {"entity_id": anchor_id}},
        {
            "value_id": "explosion_model",
            **_record(
                "ExplosionModel",
                model_id=_MODEL["model_id"],
                revision=_MODEL["revision"],
                medium=_MODEL["medium"],
                valid_radius_m=_MODEL["valid_radius_m"],
                attenuation_policy=_MODEL["attenuation_policy"],
                occlusion_policy=_MODEL["occlusion_policy"],
            ),
        },
        {
            "value_id": "explosion_policy",
            **_record(
                "ExplosionPolicy",
                region_id=str(parameters["region_id"]),
                medium_revision=str(parameters["medium_model"]["medium_revision"]),
                radius_m=float(parameters["radius_m"]),
                maximum_radius_m=float(parameters["maximum_radius_m"]),
                duration_s=float(parameters["duration_s"]),
                release_energy_j=float(parameters["release_energy_j"]),
                pressure_energy_fraction=float(parameters["pressure_energy_fraction"]),
                thermal_energy_fraction=float(parameters["thermal_energy_fraction"]),
                peak_pressure_pa=float(parameters["peak_pressure_pa"]),
                maximum_peak_pressure_pa=float(parameters["maximum_peak_pressure_pa"]),
                maximum_impulse_kg_m_s=float(parameters["maximum_impulse_kg_m_s"]),
                maximum_thermal_energy_j=float(parameters["maximum_thermal_energy_j"]),
                maximum_affected_entities=int(parameters["maximum_affected_entities"]),
            ),
        },
        {
            "value_id": "explosion_publication",
            **_record(
                "ExplosionPublication",
                activation_event_id=str(parameters["activation_event_id"]),
                termination_event_id=str(parameters["termination_event_id"]),
            ),
        },
    ]
    nodes = [
        {
            "node_id": "resolve_explosion_origin",
            "order": 0,
            "instruction": "ref.resolve",
            "inputs": ["origin_selector"],
            "produces": ["origin_ref"],
        },
        {
            "node_id": "resolve_reaction_anchor",
            "order": 1,
            "instruction": "ref.resolve",
            "inputs": ["anchor_selector"],
            "produces": ["anchor_ref"],
        },
        {
            "node_id": "invoke_bounded_explosion",
            "order": 2,
            "instruction": "effect.invoke",
            "inputs": [
                "origin_ref",
                "anchor_ref",
                "explosion_model",
                "explosion_policy",
                "explosion_publication",
            ],
            "produces": ["explosion_result"],
            "contract": {"contract_id": _CONTRACT_ID, "revision": _CONTRACT_REVISION},
            "obligations": {
                "capabilities": [
                    {
                        "requirement_id": "capability.bounded-explosion",
                        "target_binding": "origin_ref",
                        "effect": "Reconfigure",
                        "scope": "local",
                    }
                ],
                "leases": [
                    {
                        "requirement_id": "lease.bounded-explosion",
                        "target_binding": "origin_ref",
                        "mode": "Actuate",
                        "scope": "local",
                    }
                ],
                "identities": [
                    {"requirement_id": "identity.explosion-origin", "target_binding": "origin_ref"},
                    {"requirement_id": "identity.reaction-anchor", "target_binding": "anchor_ref"},
                ],
                "evidence": [
                    {
                        "requirement_id": "evidence.explosion-affected-set",
                        "target_binding": "origin_ref",
                        "kind": "ExplosionAffectedSet",
                    }
                ],
                "accounting": [
                    {
                        "requirement_id": "accounting.bounded-explosion",
                        "target_binding": "origin_ref",
                        "kind": "BoundedExplosionAccounting",
                    }
                ],
                "resources": {
                    "energy_j": float(parameters["release_energy_j"]),
                    "matter_kg": 0.0,
                    "events": 2,
                },
            },
        },
    ]
    program = program_envelope(
        bundle,
        program_id="program:migrated:dynamics.explosion:1",
        budget_energy=float(bundle["execution"]["energy_budget_j"]),
        budget_events=2,
        values=values,
        nodes=nodes,
        edges=[
            {"from": "resolve_explosion_origin", "to": "invoke_bounded_explosion"},
            {"from": "resolve_reaction_anchor", "to": "invoke_bounded_explosion"},
        ],
        outputs=[
            {"name": "result", "binding": "explosion_result", "kind": "effect_result"},
            {"name": "event", "binding": "explosion_result", "kind": "event"},
        ],
    )

    signature = (
        "reference",
        "reference",
        "record:ExplosionModel",
        "record:ExplosionPolicy",
        "record:ExplosionPublication",
    )
    semantic = explosion_semantic_registry()
    runtime = MagicalProgramRuntime(
        evaluator=MagicalProgramEvaluator(contracts=semantic),
        contracts=ProgramRuntimeContractRegistry(
            (
                RuntimeContractRegistration(
                    _CONTRACT_ID,
                    _CONTRACT_REVISION,
                    "effect.invoke",
                    signature,
                    "effect_result",
                    2,
                    explosion_executor,
                ),
            )
        ),
        profile=profile,
    )
    return ShadowTranslation(
        program,
        world,
        runtime.evaluator,
        runtime,
        "implemented",
        bundle_contract_pair(bundle),
    )


def explosion_projection(
    configuration: Mapping[str, Any],
    *,
    entity_ids: list[str],
    event_ids: list[str],
) -> _JSON:
    sigma = configuration.get("Sigma", {})
    entities = sigma.get("entities", {})
    return {
        "world_revision": sigma.get("revision"),
        "entities": {entity_id: copy.deepcopy(entities.get(entity_id)) for entity_id in entity_ids},
        "events": [
            copy.deepcopy(item)
            for event_id in event_ids
            for item in configuration.get("H", [])
            if item.get("event_id") == event_id
        ],
    }


__all__ = [
    "explosion_executor",
    "explosion_projection",
    "explosion_semantic_registry",
    "translate_explosion",
]
