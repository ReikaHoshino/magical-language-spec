"""Generic MagicalProgram migration for the boundary-reflection contract."""
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
_MODEL_ID = "controller.boundary-reflection"
_MODEL_REVISION = "1"
_MODEL_MAXIMUM_TARGET_MASS_KG = 20.0
_MODEL_PER_ACTUATION_REVALIDATION = True
_MODEL_NO_AUTHORITY_AMPLIFICATION = True


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


def boundary_reflection_semantic_registry() -> ProgramContractRegistry:
    registry = default_program_contract_registry()
    registry.register(
        ProgramContractRegistration(
            _MODEL_ID,
            _MODEL_REVISION,
            "effect.invoke",
            (
                "reference",
                "reference",
                "record:BoundaryReflectionModel",
                "record:BoundaryReflectionPolicy",
                "record:BoundaryReflectionPublication",
            ),
            "effect_result",
            ("capabilities", "leases", "identities", "accounting"),
            0.0,
            0.0,
            1,
            ("OBSERVE", "CONSTRAIN"),
            ("SAMPLE", "TRANSITION", "ACTIVATE"),
        )
    )
    return registry


def _validate_model(
    model: Mapping[str, Any], policy: Mapping[str, Any]
) -> None:
    if (
        str(_literal(model, "model_id")) != _MODEL_ID
        or str(_literal(model, "revision")) != _MODEL_REVISION
        or float(_literal(model, "registered_maximum_target_mass_kg"))
        != _MODEL_MAXIMUM_TARGET_MASS_KG
        or bool(_literal(model, "per_actuation_revalidation"))
        is not _MODEL_PER_ACTUATION_REVALIDATION
        or bool(_literal(model, "no_authority_amplification"))
        is not _MODEL_NO_AUTHORITY_AMPLIFICATION
    ):
        raise ProgramRuntimeError(
            "ControllerModelMismatch",
            "BoundaryReflectionController identity or host safety policy is invalid.",
            stage="COMMIT",
        )

    restitution = float(_literal(policy, "coefficient_of_restitution"))
    maximum_target_mass = float(
        _literal(policy, "maximum_target_mass_kg")
    )
    nonnegative_limits = (
        float(_literal(policy, "maximum_incident_momentum_kg_m_s")),
        float(_literal(policy, "maximum_impulse_kg_m_s")),
        float(_literal(policy, "maximum_energy_j")),
        float(_literal(policy, "event_latency_ms")),
        float(_literal(policy, "max_event_latency_ms")),
        float(_literal(policy, "jitter_ms")),
        float(_literal(policy, "max_jitter_ms")),
    )
    if (
        not 0.0 <= restitution <= 1.0
        or maximum_target_mass <= 0.0
        or maximum_target_mass > _MODEL_MAXIMUM_TARGET_MASS_KG
        or any(value < 0.0 for value in nonnegative_limits)
    ):
        raise ProgramRuntimeError(
            "ControllerModelMismatch",
            "Boundary reflection policy is outside the host-owned model contract.",
            stage="COMMIT",
        )


def _semantic_projection(
    *,
    target_id: str,
    anchor_id: str,
    ledger_id: str,
    policy: Mapping[str, Any],
    publication: Mapping[str, Any],
    result_world_revision: str,
) -> _JSON:
    """Build the authoritative legacy-equivalent projection at COMMIT.

    The portable artifact never contains ``result_world_revision``. The host
    derives it from the committed transition and only then publishes it in the
    authoritative Controller record.
    """

    return {
        "target_entity_id": target_id,
        "reaction_anchor_id": anchor_id,
        "ledger_id": ledger_id,
        "controller_id": str(_literal(publication, "controller_id")),
        "protected_region_id": str(
            _literal(publication, "protected_region_id")
        ),
        "coefficient_of_restitution": float(
            _literal(policy, "coefficient_of_restitution")
        ),
        "maximum_target_mass_kg": float(
            _literal(policy, "maximum_target_mass_kg")
        ),
        "maximum_incident_momentum_kg_m_s": float(
            _literal(policy, "maximum_incident_momentum_kg_m_s")
        ),
        "maximum_impulse_kg_m_s": float(
            _literal(policy, "maximum_impulse_kg_m_s")
        ),
        "maximum_energy_j": float(_literal(policy, "maximum_energy_j")),
        "event_latency_ms": float(_literal(policy, "event_latency_ms")),
        "max_event_latency_ms": float(
            _literal(policy, "max_event_latency_ms")
        ),
        "jitter_ms": float(_literal(policy, "jitter_ms")),
        "max_jitter_ms": float(_literal(policy, "max_jitter_ms")),
        "authorized_event_id": str(
            _literal(publication, "authorized_event_id")
        ),
        "reflection_event_id": str(
            _literal(publication, "reflection_event_id")
        ),
        "result_world_revision": result_world_revision,
    }


def boundary_reflection_executor(
    context: RuntimeExecutionContext,
    effect: PreparedProgramEffect,
    world: SandboxWorld,
) -> _JSON:
    del context
    target_ref, anchor_ref, model, policy, publication = effect.frozen_values
    target_id = str(target_ref.get("entity_id"))
    anchor_id = str(anchor_ref.get("entity_id"))
    target = world.entities.get(target_id)
    anchor = world.entities.get(anchor_id)
    if target is None or anchor is None:
        raise ProgramRuntimeError(
            "ResolutionFailure",
            "Boundary target or reaction anchor is absent.",
            stage="COMMIT",
        )

    _validate_model(model, policy)
    mass = float(target.get("mass_kg", 0.0))
    incident = float(target.get("normal_momentum_kg_m_s", 0.0))
    if (
        mass <= 0.0
        or mass > float(_literal(policy, "maximum_target_mass_kg"))
        or abs(incident)
        > float(_literal(policy, "maximum_incident_momentum_kg_m_s"))
    ):
        raise ProgramRuntimeError(
            "ControllerDomainExceeded",
            "Target is outside the admitted controller domain.",
            stage="COMMIT",
        )
    if (
        float(_literal(policy, "event_latency_ms"))
        > float(_literal(policy, "max_event_latency_ms"))
        or float(_literal(policy, "jitter_ms"))
        > float(_literal(policy, "max_jitter_ms"))
    ):
        raise ProgramRuntimeError(
            "ControllerTimingViolation",
            "Controller timing exceeds the admitted bound.",
            stage="COMMIT",
        )

    ledger_bound = effect.accounting_records[0]
    ledger = world.ledgers[ledger_bound.record_id]
    source_revision = world.revision
    event_id = str(_literal(publication, "authorized_event_id"))
    effect_kind = "AuthorizedBoundaryPass"
    impulse = 0.0
    dissipated = 0.0
    final_momentum = incident

    if bool(target.get("crossing")) and not bool(target.get("authorized")):
        restitution = float(_literal(policy, "coefficient_of_restitution"))
        impulse = (1.0 + restitution) * incident
        final_momentum = -restitution * incident
        dissipated = (
            incident * incident / (2.0 * mass)
            - final_momentum * final_momentum / (2.0 * mass)
        )
        if (
            abs(impulse) > float(_literal(policy, "maximum_impulse_kg_m_s"))
            or dissipated > float(_literal(policy, "maximum_energy_j"))
        ):
            raise ProgramRuntimeError(
                "ControllerOverload",
                "Actuation exceeds the saturation envelope.",
                stage="COMMIT",
            )
        target["normal_momentum_kg_m_s"] = final_momentum
        anchor["normal_momentum_kg_m_s"] = float(
            anchor.get("normal_momentum_kg_m_s", 0.0)
        ) + impulse
        ledger.update(
            {
                "target_momentum_kg_m_s": final_momentum,
                "anchor_momentum_kg_m_s": anchor[
                    "normal_momentum_kg_m_s"
                ],
                "dissipated_energy_j": dissipated,
            }
        )
        event_id = str(_literal(publication, "reflection_event_id"))
        effect_kind = "BoundaryReflectionActuation"

    controller_id = str(_literal(publication, "controller_id"))
    if controller_id in world.controllers:
        raise ProgramRuntimeError(
            "ProgramArtifactIdentityCollision",
            f"Controller {controller_id!r} already exists.",
            stage="COMMIT",
        )

    world.revision = next_world_revision(source_revision)
    projection = _semantic_projection(
        target_id=target_id,
        anchor_id=anchor_id,
        ledger_id=ledger_bound.record_id,
        policy=policy,
        publication=publication,
        result_world_revision=world.revision,
    )
    world.controllers[controller_id] = {
        "active": True,
        "semantic_projection": projection,
        "per_actuation_revalidation": True,
    }
    world.history.append(
        {
            "event_id": event_id,
            "effect_kind": effect_kind,
            "source_world_revision": source_revision,
            "result_world_revision": world.revision,
            "atomic_accounting": [
                "TargetMomentum",
                "AnchorReaction",
                "DissipatedEnergy",
            ],
        }
    )
    return {
        "kind": "effect_result",
        "status": "Committed",
        "node_id": effect.node_id,
        "contract_id": effect.contract_id,
        "contract_revision": effect.contract_revision,
        "entity_ids": [target_id, anchor_id],
        "event_id": event_id,
        "controller_id": controller_id,
        "effect_kind": effect_kind,
        "identity_policy": "PreserveExistingIdentity",
        "source_world_revision": source_revision,
        "result_world_revision": world.revision,
        "target_final_momentum_kg_m_s": final_momentum,
        "anchor_reaction_impulse_kg_m_s": impulse,
        "dissipated_energy_j": dissipated,
    }


def _require_exact_host_model(bundle: Mapping[str, Any]) -> None:
    registered_models = bundle.get("registry_extensions", {}).get(
        "controller_models", []
    )
    expected = {
        "model_id": _MODEL_ID,
        "revision": _MODEL_REVISION,
        "valid_domain": {
            "maximum_target_mass_kg": int(_MODEL_MAXIMUM_TARGET_MASS_KG)
        },
        "per_actuation_revalidation": _MODEL_PER_ACTUATION_REVALIDATION,
        "no_authority_amplification": _MODEL_NO_AUTHORITY_AMPLIFICATION,
    }
    if len(registered_models) != 1 or registered_models[0] != expected:
        raise ValueError(
            "controller model declaration must exactly match the host-owned registration"
        )


def translate_boundary_reflection(
    bundle: Mapping[str, Any],
) -> ShadowTranslation:
    parameters = bundle["execution"]["parameters"]
    required = bundle["execution"]["required_evidence"]
    target_id = str(parameters["target_entity_id"])
    anchor_id = str(parameters["reaction_anchor_id"])
    ledger_id = str(parameters["ledger_id"])
    profile = profile_from_bundle(bundle)
    world = world_from_bundle(bundle, profile)
    target_revision = str(world.entities[target_id]["state_revision"])
    anchor_revision = str(world.entities[anchor_id]["state_revision"])

    _require_exact_host_model(bundle)
    capability_ids = [str(item) for item in required["capabilities"]]
    lease_ids = [str(item) for item in required["leases"]]
    if len(capability_ids) != 1 or len(lease_ids) != 1:
        raise ValueError(
            "controller.boundary-reflection requires one Capability and one Lease"
        )
    configure_capability(
        world,
        capability_ids[0],
        entity_id=anchor_id,
        effect="Constrain",
    )
    configure_lease(
        world,
        lease_ids[0],
        entity_id=anchor_id,
        mode="Actuate",
    )
    configure_ledger(
        world,
        ledger_id,
        entity_id=anchor_id,
        kind="BoundaryMomentumEnergyAccounting",
        default_events=profile.max_events,
    )
    add_identity_record(world, target_id, target_revision)
    add_identity_record(world, anchor_id, anchor_revision)

    values = [
        {
            "value_id": "target_selector",
            "kind": "selector",
            "selector": {"entity_id": target_id},
        },
        {
            "value_id": "anchor_selector",
            "kind": "selector",
            "selector": {"entity_id": anchor_id},
        },
        {
            "value_id": "controller_model",
            **_record(
                "BoundaryReflectionModel",
                model_id=_MODEL_ID,
                revision=_MODEL_REVISION,
                registered_maximum_target_mass_kg=(
                    _MODEL_MAXIMUM_TARGET_MASS_KG
                ),
                per_actuation_revalidation=(
                    _MODEL_PER_ACTUATION_REVALIDATION
                ),
                no_authority_amplification=(
                    _MODEL_NO_AUTHORITY_AMPLIFICATION
                ),
            ),
        },
        {
            "value_id": "boundary_policy",
            **_record(
                "BoundaryReflectionPolicy",
                coefficient_of_restitution=float(
                    parameters["coefficient_of_restitution"]
                ),
                maximum_target_mass_kg=float(
                    parameters["maximum_target_mass_kg"]
                ),
                maximum_incident_momentum_kg_m_s=float(
                    parameters["maximum_incident_momentum_kg_m_s"]
                ),
                maximum_impulse_kg_m_s=float(
                    parameters["maximum_impulse_kg_m_s"]
                ),
                maximum_energy_j=float(parameters["maximum_energy_j"]),
                event_latency_ms=float(parameters["event_latency_ms"]),
                max_event_latency_ms=float(parameters["max_event_latency_ms"]),
                jitter_ms=float(parameters["jitter_ms"]),
                max_jitter_ms=float(parameters["max_jitter_ms"]),
            ),
        },
        {
            "value_id": "publication",
            **_record(
                "BoundaryReflectionPublication",
                controller_id=str(parameters["controller_id"]),
                protected_region_id=str(parameters["protected_region_id"]),
                authorized_event_id=str(parameters["authorized_event_id"]),
                reflection_event_id=str(parameters["reflection_event_id"]),
            ),
        },
    ]
    nodes = [
        {
            "node_id": "resolve_boundary_target",
            "order": 0,
            "instruction": "ref.resolve",
            "inputs": ["target_selector"],
            "produces": ["target_ref"],
        },
        {
            "node_id": "resolve_reaction_anchor",
            "order": 1,
            "instruction": "ref.resolve",
            "inputs": ["anchor_selector"],
            "produces": ["anchor_ref"],
        },
        {
            "node_id": "invoke_boundary_reflection",
            "order": 2,
            "instruction": "effect.invoke",
            "inputs": [
                "target_ref",
                "anchor_ref",
                "controller_model",
                "boundary_policy",
                "publication",
            ],
            "produces": ["boundary_result"],
            "contract": {
                "contract_id": _MODEL_ID,
                "revision": _MODEL_REVISION,
            },
            "obligations": {
                "capabilities": [
                    {
                        "requirement_id": "capability.boundary-actuation",
                        "target_binding": "anchor_ref",
                        "effect": "Constrain",
                        "scope": "local",
                    }
                ],
                "leases": [
                    {
                        "requirement_id": "lease.boundary-controller",
                        "target_binding": "anchor_ref",
                        "mode": "Actuate",
                        "scope": "local",
                    }
                ],
                "identities": [
                    {
                        "requirement_id": "identity.boundary-target",
                        "target_binding": "target_ref",
                    },
                    {
                        "requirement_id": "identity.reaction-anchor",
                        "target_binding": "anchor_ref",
                    },
                ],
                "evidence": [],
                "accounting": [
                    {
                        "requirement_id": "accounting.boundary-momentum-energy",
                        "kind": "BoundaryMomentumEnergyAccounting",
                        "target_binding": "anchor_ref",
                    }
                ],
                "resources": {
                    "energy_j": 0.0,
                    "matter_kg": 0.0,
                    "events": 1,
                },
            },
        },
    ]
    program = program_envelope(
        bundle,
        program_id="program:migrated:controller.boundary-reflection:1",
        budget_energy=float(bundle["execution"]["energy_budget_j"]),
        budget_events=1,
        values=values,
        nodes=nodes,
        edges=[
            {
                "from": "resolve_boundary_target",
                "to": "invoke_boundary_reflection",
            },
            {
                "from": "resolve_reaction_anchor",
                "to": "invoke_boundary_reflection",
            },
        ],
        outputs=[
            {
                "name": "result",
                "binding": "boundary_result",
                "kind": "effect_result",
            },
            {
                "name": "event",
                "binding": "boundary_result",
                "kind": "event",
            },
        ],
    )

    semantic = boundary_reflection_semantic_registry()
    runtime_contracts = ProgramRuntimeContractRegistry(
        (
            RuntimeContractRegistration(
                _MODEL_ID,
                _MODEL_REVISION,
                "effect.invoke",
                (
                    "reference",
                    "reference",
                    "record:BoundaryReflectionModel",
                    "record:BoundaryReflectionPolicy",
                    "record:BoundaryReflectionPublication",
                ),
                "effect_result",
                1,
                boundary_reflection_executor,
            ),
        )
    )
    evaluator = MagicalProgramEvaluator(contracts=semantic)
    runtime = MagicalProgramRuntime(
        evaluator=evaluator,
        contracts=runtime_contracts,
        profile=profile,
    )
    return ShadowTranslation(
        program,
        world,
        evaluator,
        runtime,
        "implemented",
        bundle_contract_pair(bundle),
    )


def boundary_reflection_projection(
    configuration: Mapping[str, Any],
    *,
    target_id: str,
    anchor_id: str,
    controller_id: str,
    event_id: str,
) -> _JSON:
    sigma = configuration.get("Sigma", {})
    entities = sigma.get("entities", {})
    controllers = sigma.get("controllers", {})
    event = next(
        (
            copy.deepcopy(item)
            for item in configuration.get("H", [])
            if item.get("event_id") == event_id
        ),
        None,
    )
    controller = controllers.get(controller_id)
    return {
        "world_revision": sigma.get("revision"),
        "target_normal_momentum_kg_m_s": entities.get(target_id, {}).get(
            "normal_momentum_kg_m_s"
        ),
        "anchor_normal_momentum_kg_m_s": entities.get(anchor_id, {}).get(
            "normal_momentum_kg_m_s"
        ),
        "controller": None
        if controller is None
        else {
            "active": controller.get("active"),
            "semantic_projection": copy.deepcopy(
                controller.get("semantic_projection")
            ),
            "per_actuation_revalidation": controller.get(
                "per_actuation_revalidation"
            ),
        },
        "event": event,
    }


__all__ = [
    "boundary_reflection_executor",
    "boundary_reflection_projection",
    "boundary_reflection_semantic_registry",
    "translate_boundary_reflection",
]
