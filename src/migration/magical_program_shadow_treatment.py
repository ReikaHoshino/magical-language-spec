"""Generic MagicalProgram migration for staged treatment."""
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
_CONTRACT_ID = "treatment.staged-repair"
_CONTRACT_REVISION = "1"
_STRUCTURE_SCHEMA = {"id": "TissueArchitecture", "revision": "1"}
_REACTION_RULE = {"id": _CONTRACT_ID, "revision": _CONTRACT_REVISION}
_IDENTITY_POLICY = "IdentityPolicy<Organism>"
_STAGE_ORDER = ("stabilize", "repair", "manifest")


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


def staged_treatment_semantic_registry() -> ProgramContractRegistry:
    registry = default_program_contract_registry()
    registry.register(
        ProgramContractRegistration(
            _CONTRACT_ID,
            _CONTRACT_REVISION,
            "effect.invoke",
            (
                "reference",
                "reference",
                "reference",
                "reference",
                "reference",
                "record:StagedTreatmentModel",
                "record:StagedTreatmentPolicy",
                "record:TreatmentStage",
            ),
            "effect_result",
            (
                "capabilities",
                "leases",
                "identities",
                "evidence",
                "accounting",
            ),
            0.0,
            0.0,
            1,
            ("OBSERVE", "CHANNEL", "TRANSFER", "RECONFIGURE"),
            ("SAMPLE", "TRANSITION"),
        )
    )
    return registry


def _require_exact_host_extensions(
    bundle: Mapping[str, Any], ledger_id: str
) -> None:
    extensions = bundle.get("registry_extensions", {})
    if extensions.get("structure_schemas") != [_STRUCTURE_SCHEMA]:
        raise ValueError(
            "structure schema declaration must exactly match the host registration"
        )
    if extensions.get("reaction_rules") != [_REACTION_RULE]:
        raise ValueError(
            "reaction rule declaration must exactly match the host registration"
        )
    if extensions.get("conservation_ledgers") != [
        {"id": ledger_id, "revision": "1"}
    ]:
        raise ValueError(
            "conservation ledger declaration must match the bound host ledger"
        )


def _validate_model_and_policy(
    model: Mapping[str, Any], policy: Mapping[str, Any]
) -> None:
    if (
        str(_literal(model, "structure_schema_id"))
        != _STRUCTURE_SCHEMA["id"]
        or str(_literal(model, "structure_schema_revision"))
        != _STRUCTURE_SCHEMA["revision"]
        or str(_literal(model, "reaction_rule_id"))
        != _REACTION_RULE["id"]
        or str(_literal(model, "reaction_rule_revision"))
        != _REACTION_RULE["revision"]
        or str(_literal(model, "identity_policy")) != _IDENTITY_POLICY
    ):
        raise ProgramRuntimeError(
            "TreatmentModelMismatch",
            "Staged-treatment model identity is not host registered.",
            stage="COMMIT",
        )
    if bool(_literal(policy, "reverse_proxy_effect")):
        raise ProgramRuntimeError(
            "ReverseCorrespondenceForbidden",
            "Proxy correspondence cannot reverse onto the patient.",
            stage="COMMIT",
        )
    if bool(_literal(policy, "irreversible_information_loss")):
        raise ProgramRuntimeError(
            "IdentityPreservationFailure",
            "Treatment would erase identity-critical information.",
            stage="COMMIT",
        )
    numeric = (
        float(_literal(policy, "excess_thermal_energy_j")),
        float(_literal(policy, "removable_fluid_kg")),
        float(_literal(policy, "donor_matter_kg")),
        float(_literal(policy, "repair_energy_j")),
        float(_literal(policy, "manifest_energy_j")),
    )
    if any(value < 0.0 for value in numeric):
        raise ProgramRuntimeError(
            "TreatmentModelMismatch",
            "Treatment quantities must be finite nonnegative values.",
            stage="COMMIT",
        )


def _bound_evidence(effect: PreparedProgramEffect) -> Mapping[str, Any]:
    if len(effect.evidence_records) != 1:
        raise ProgramRuntimeError(
            "ResolutionFailure",
            "Exactly one correspondence evidence record is required.",
            stage="COMMIT",
        )
    return effect.evidence_records[0].frozen_record


def _check_correspondence(
    effect: PreparedProgramEffect,
    policy: Mapping[str, Any],
    proxy_id: str,
) -> None:
    evidence = _bound_evidence(effect)
    if (
        evidence.get("kind") != "UniqueCorrespondence"
        or evidence.get("entity_id") != proxy_id
        or evidence.get("token_id")
        != str(_literal(policy, "correspondence_token_id"))
        or evidence.get("unique") is not True
    ):
        raise ProgramRuntimeError(
            "ResolutionFailure",
            "Correspondence evidence is missing, stale, or non-unique.",
            stage="COMMIT",
        )


def _require_initial_resources(
    *,
    patient: Mapping[str, Any],
    sink: Mapping[str, Any],
    donor: Mapping[str, Any],
    reservoir: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> None:
    thermal = float(_literal(policy, "excess_thermal_energy_j"))
    fluid = float(_literal(policy, "removable_fluid_kg"))
    donor_matter = float(_literal(policy, "donor_matter_kg"))
    repair_energy = float(_literal(policy, "repair_energy_j"))
    manifest_energy = float(_literal(policy, "manifest_energy_j"))
    injury = patient.get("injury", {})
    if (
        float(injury.get("excess_thermal_energy_j", -1.0)) != thermal
        or float(injury.get("removable_fluid_kg", -1.0)) != fluid
        or sink.get("energy_capacity_j", 0.0) < thermal
        or sink.get("matter_capacity_kg", 0.0) < fluid
        or donor.get("available_matter_kg", 0.0) < donor_matter
        or reservoir.get("available_energy_j", 0.0)
        < repair_energy + manifest_energy
    ):
        raise ProgramRuntimeError(
            "ResourceInsufficient",
            "Sink, donor, reservoir, or patient state cannot satisfy treatment.",
            stage="COMMIT",
        )


def _event(event_id: str, effect_kind: str) -> _JSON:
    return {
        "event_id": event_id,
        "effect_kind": effect_kind,
        "rollback": False,
    }


def staged_treatment_executor(
    context: RuntimeExecutionContext,
    effect: PreparedProgramEffect,
    world: SandboxWorld,
) -> _JSON:
    del context
    (
        patient_ref,
        proxy_ref,
        sink_ref,
        donor_ref,
        reservoir_ref,
        model,
        policy,
        stage_record,
    ) = effect.frozen_values
    patient_id = str(patient_ref["entity_id"])
    proxy_id = str(proxy_ref["entity_id"])
    sink_id = str(sink_ref["entity_id"])
    donor_id = str(donor_ref["entity_id"])
    reservoir_id = str(reservoir_ref["entity_id"])
    patient = world.entities[patient_id]
    proxy = world.entities[proxy_id]
    sink = world.entities[sink_id]
    donor = world.entities[donor_id]
    reservoir = world.entities[reservoir_id]

    _validate_model_and_policy(model, policy)
    _check_correspondence(effect, policy, proxy_id)
    if not any(
        bound.frozen_record.get("consent") is True
        for bound in effect.lease_records
    ):
        raise ProgramRuntimeError(
            "AuthorityError",
            "Patient consent is required for staged treatment.",
            stage="COMMIT",
        )

    stage = str(_literal(stage_record, "stage"))
    ordinal = int(_literal(stage_record, "ordinal"))
    event_id = str(_literal(stage_record, "event_id"))
    if (
        stage not in _STAGE_ORDER
        or ordinal < 0
        or ordinal >= len(_STAGE_ORDER)
        or _STAGE_ORDER[ordinal] != stage
    ):
        raise ProgramRuntimeError(
            "TreatmentStageOrderViolation",
            "Treatment stage identity/order is invalid.",
            stage="COMMIT",
        )

    thermal = float(_literal(policy, "excess_thermal_energy_j"))
    fluid = float(_literal(policy, "removable_fluid_kg"))
    donor_matter = float(_literal(policy, "donor_matter_kg"))
    repair_energy = float(_literal(policy, "repair_energy_j"))
    manifest_energy = float(_literal(policy, "manifest_energy_j"))
    ledger = world.ledgers[effect.accounting_records[0].record_id]
    source_revision = world.revision

    if stage == "stabilize":
        _require_initial_resources(
            patient=patient,
            sink=sink,
            donor=donor,
            reservoir=reservoir,
            policy=policy,
        )
        patient["injury"]["excess_thermal_energy_j"] = 0
        patient["injury"]["removable_fluid_kg"] = 0
        sink["absorbed_energy_j"] = float(
            sink.get("absorbed_energy_j", 0.0)
        ) + thermal
        sink["absorbed_matter_kg"] = float(
            sink.get("absorbed_matter_kg", 0.0)
        ) + fluid
        ledger["transferred_to_sink_energy_j"] = thermal
        effect_kind = "TreatmentStabilize"
    elif stage == "repair":
        if (
            patient["injury"].get("excess_thermal_energy_j") != 0
            or patient["injury"].get("removable_fluid_kg") != 0
            or patient.get("tissue_repaired") is not False
        ):
            raise ProgramRuntimeError(
                "TreatmentStageOrderViolation",
                "Repair requires a completed stabilization stage.",
                stage="COMMIT",
            )
        if (
            donor.get("available_matter_kg", 0.0) < donor_matter
            or reservoir.get("available_energy_j", 0.0) < repair_energy
        ):
            raise ProgramRuntimeError(
                "ResourceInsufficient",
                "Repair resources are insufficient.",
                stage="COMMIT",
            )
        donor["available_matter_kg"] -= donor_matter
        reservoir["available_energy_j"] -= repair_energy
        patient["injury"]["structural_deviation"] = "repaired"
        patient["tissue_repaired"] = True
        effect_kind = "TreatmentRepair"
    else:
        if (
            patient.get("tissue_repaired") is not True
            or patient["injury"].get("structural_deviation") != "repaired"
            or patient["injury"].get("chemical_deviation")
            != "reversible-minor"
        ):
            raise ProgramRuntimeError(
                "TreatmentStageOrderViolation",
                "Manifestation requires a completed repair stage.",
                stage="COMMIT",
            )
        if reservoir.get("available_energy_j", 0.0) < manifest_energy:
            raise ProgramRuntimeError(
                "ResourceInsufficient",
                "Manifestation Energy is insufficient.",
                stage="COMMIT",
            )
        reservoir["available_energy_j"] -= manifest_energy
        patient["injury"]["chemical_deviation"] = "repaired"
        proxy["manifested_descriptor"] = {
            "kind": "DamageDescriptor",
            "source_patient_id": patient["entity_id"],
            "reverse_effect": False,
            "provenance": str(
                _literal(policy, "correspondence_token_id")
            ),
        }
        ledger["treatment_energy_consumed_j"] = repair_energy + manifest_energy
        effect_kind = "TreatmentManifest"

    world.revision = next_world_revision(source_revision)
    world.history.append(_event(event_id, effect_kind))
    return {
        "kind": "effect_result",
        "status": "Committed",
        "node_id": effect.node_id,
        "contract_id": effect.contract_id,
        "contract_revision": effect.contract_revision,
        "entity_ids": [
            patient_id,
            proxy_id,
            sink_id,
            donor_id,
            reservoir_id,
        ],
        "stage": stage,
        "event_id": event_id,
        "effect_kind": effect_kind,
        "identity_policy": "PreserveExistingIdentity",
        "source_world_revision": source_revision,
        "result_world_revision": world.revision,
    }


def _requirements() -> _JSON:
    return {
        "capabilities": [
            {
                "requirement_id": "capability.medical-reconfigure",
                "target_binding": "patient_ref",
                "effect": "Reconfigure",
                "scope": "local",
            },
            {
                "requirement_id": "capability.proxy-channel",
                "target_binding": "proxy_ref",
                "effect": "Channel",
                "scope": "local",
            },
        ],
        "leases": [
            {
                "requirement_id": "lease.patient-write",
                "target_binding": "patient_ref",
                "mode": "Write",
                "scope": "local",
            },
            {
                "requirement_id": "lease.resource-consume",
                "target_binding": "reservoir_ref",
                "mode": "Consume",
                "scope": "local",
            },
        ],
        "identities": [
            {
                "requirement_id": f"identity.{name}",
                "target_binding": f"{name}_ref",
            }
            for name in ("patient", "proxy", "sink", "donor", "reservoir")
        ],
        "evidence": [
            {
                "requirement_id": "evidence.unique-correspondence",
                "target_binding": "proxy_ref",
                "kind": "UniqueCorrespondence",
            }
        ],
        "accounting": [
            {
                "requirement_id": "accounting.staged-treatment",
                "target_binding": "patient_ref",
                "kind": "StagedTreatmentAccounting",
            }
        ],
    }


def translate_staged_treatment(bundle: Mapping[str, Any]) -> ShadowTranslation:
    parameters = bundle["execution"]["parameters"]
    required = bundle["execution"]["required_evidence"]
    ids = {
        "patient": str(parameters["patient_id"]),
        "proxy": str(parameters["proxy_id"]),
        "sink": str(parameters["sink_id"]),
        "donor": str(parameters["donor_id"]),
        "reservoir": str(parameters["energy_reservoir_id"]),
    }
    ledger_id = str(parameters["ledger_id"])
    _require_exact_host_extensions(bundle, ledger_id)

    profile = profile_from_bundle(bundle)
    world = world_from_bundle(bundle, profile)
    capability_ids = [str(item) for item in required["capabilities"]]
    lease_ids = [str(item) for item in required["leases"]]
    accounting_ids = [str(item) for item in required["accounting"]]
    if (
        len(capability_ids) != 2
        or len(lease_ids) != 2
        or accounting_ids != [ledger_id]
    ):
        raise ValueError(
            "staged treatment requires two capabilities, two leases, and one ledger"
        )

    configure_capability(
        world,
        capability_ids[0],
        entity_id=ids["patient"],
        effect="Reconfigure",
    )
    configure_capability(
        world,
        capability_ids[1],
        entity_id=ids["proxy"],
        effect="Channel",
    )
    configure_lease(
        world,
        lease_ids[0],
        entity_id=ids["patient"],
        mode="Write",
    )
    configure_lease(
        world,
        lease_ids[1],
        entity_id=ids["reservoir"],
        mode="Consume",
    )
    configure_ledger(
        world,
        ledger_id,
        entity_id=ids["patient"],
        kind="StagedTreatmentAccounting",
        default_events=profile.max_events,
    )
    ledger = world.ledgers.get(ledger_id)
    if ledger is not None:
        ledger.update(
            {
                "available_energy_j": float(
                    bundle["execution"]["energy_budget_j"]
                ),
                "available_matter_kg": float(parameters["removable_fluid_kg"])
                + float(parameters["donor_matter_kg"]),
                "events_remaining": profile.max_events,
            }
        )
    for entity_id in ids.values():
        add_identity_record(
            world,
            entity_id,
            str(world.entities[entity_id]["state_revision"]),
        )

    if bool(parameters["correspondence_unique"]):
        proxy_revision = str(world.entities[ids["proxy"]]["state_revision"])
        evidence_id = "evidence:staged-treatment:unique-correspondence"
        world.runtime_state["evidence"][evidence_id] = {
            "active": True,
            "entity_id": ids["proxy"],
            "state_revision": proxy_revision,
            "kind": "UniqueCorrespondence",
            "token_id": str(parameters["correspondence_token_id"]),
            "unique": True,
            "revision": "1",
        }

    values: list[_JSON] = [
        {
            "value_id": f"{name}_selector",
            "kind": "selector",
            "selector": {"entity_id": entity_id},
        }
        for name, entity_id in ids.items()
    ]
    values.extend(
        [
            {
                "value_id": "treatment_model",
                **_record(
                    "StagedTreatmentModel",
                    structure_schema_id=_STRUCTURE_SCHEMA["id"],
                    structure_schema_revision=_STRUCTURE_SCHEMA["revision"],
                    reaction_rule_id=_REACTION_RULE["id"],
                    reaction_rule_revision=_REACTION_RULE["revision"],
                    identity_policy=_IDENTITY_POLICY,
                ),
            },
            {
                "value_id": "treatment_policy",
                **_record(
                    "StagedTreatmentPolicy",
                    correspondence_token_id=str(
                        parameters["correspondence_token_id"]
                    ),
                    reverse_proxy_effect=bool(
                        parameters["reverse_proxy_effect"]
                    ),
                    irreversible_information_loss=bool(
                        parameters["irreversible_information_loss"]
                    ),
                    excess_thermal_energy_j=float(
                        parameters["excess_thermal_energy_j"]
                    ),
                    removable_fluid_kg=float(
                        parameters["removable_fluid_kg"]
                    ),
                    donor_matter_kg=float(parameters["donor_matter_kg"]),
                    repair_energy_j=float(parameters["repair_energy_j"]),
                    manifest_energy_j=float(parameters["manifest_energy_j"]),
                ),
            },
        ]
    )

    event_ids = [str(item) for item in parameters["event_ids"]]
    if len(event_ids) != 3:
        raise ValueError("staged treatment requires exactly three event IDs")
    stage_specs = (
        (
            "stabilize",
            event_ids[0],
            float(parameters["excess_thermal_energy_j"]),
            float(parameters["removable_fluid_kg"]),
        ),
        (
            "repair",
            event_ids[1],
            float(parameters["repair_energy_j"]),
            float(parameters["donor_matter_kg"]),
        ),
        (
            "manifest",
            event_ids[2],
            float(parameters["manifest_energy_j"]),
            0.0,
        ),
    )
    for ordinal, (stage, event_id, energy_j, matter_kg) in enumerate(
        stage_specs
    ):
        values.append(
            {
                "value_id": f"stage_{stage}",
                **_record(
                    "TreatmentStage",
                    stage=stage,
                    ordinal=ordinal,
                    event_id=event_id,
                    energy_j=energy_j,
                    matter_kg=matter_kg,
                ),
            }
        )

    nodes: list[_JSON] = []
    for order, name in enumerate(ids):
        nodes.append(
            {
                "node_id": f"resolve_{name}",
                "order": order,
                "instruction": "ref.resolve",
                "inputs": [f"{name}_selector"],
                "produces": [f"{name}_ref"],
            }
        )
    base_requirements = _requirements()
    for offset, (stage, _, energy_j, matter_kg) in enumerate(stage_specs):
        obligations = copy.deepcopy(base_requirements)
        obligations["resources"] = {
            "energy_j": energy_j,
            "matter_kg": matter_kg,
            "events": 1,
        }
        nodes.append(
            {
                "node_id": f"treatment_{stage}",
                "order": len(ids) + offset,
                "instruction": "effect.invoke",
                "inputs": [
                    "patient_ref",
                    "proxy_ref",
                    "sink_ref",
                    "donor_ref",
                    "reservoir_ref",
                    "treatment_model",
                    "treatment_policy",
                    f"stage_{stage}",
                ],
                "produces": [f"{stage}_result"],
                "contract": {
                    "contract_id": _CONTRACT_ID,
                    "revision": _CONTRACT_REVISION,
                },
                "obligations": obligations,
            }
        )

    edges = [
        {"from": f"resolve_{name}", "to": f"treatment_{stage}"}
        for stage in _STAGE_ORDER
        for name in ids
    ]
    edges.extend(
        [
            {"from": "treatment_stabilize", "to": "treatment_repair"},
            {"from": "treatment_repair", "to": "treatment_manifest"},
        ]
    )
    outputs = [
        {
            "name": "result",
            "binding": "manifest_result",
            "kind": "effect_result",
        }
    ]
    outputs.extend(
        {
            "name": f"{stage}_event",
            "binding": f"{stage}_result",
            "kind": "event",
        }
        for stage in _STAGE_ORDER
    )
    program = program_envelope(
        bundle,
        program_id="program:migrated:treatment.staged-repair:1",
        budget_energy=float(bundle["execution"]["energy_budget_j"]),
        budget_events=3,
        values=values,
        nodes=nodes,
        edges=edges,
        outputs=outputs,
    )

    signature = (
        "reference",
        "reference",
        "reference",
        "reference",
        "reference",
        "record:StagedTreatmentModel",
        "record:StagedTreatmentPolicy",
        "record:TreatmentStage",
    )
    semantic = staged_treatment_semantic_registry()
    runtime_contracts = ProgramRuntimeContractRegistry(
        (
            RuntimeContractRegistration(
                _CONTRACT_ID,
                _CONTRACT_REVISION,
                "effect.invoke",
                signature,
                "effect_result",
                1,
                staged_treatment_executor,
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


def staged_treatment_projection(
    configuration: Mapping[str, Any],
    *,
    entity_ids: Mapping[str, str],
    event_ids: list[str],
) -> _JSON:
    sigma = configuration.get("Sigma", {})
    entities = sigma.get("entities", {})
    selected_events = [
        copy.deepcopy(item)
        for event_id in event_ids
        for item in configuration.get("H", [])
        if item.get("event_id") == event_id
    ]
    return {
        "world_revision": sigma.get("revision"),
        "entities": {
            name: copy.deepcopy(entities.get(entity_id))
            for name, entity_id in entity_ids.items()
        },
        "events": selected_events,
    }


__all__ = [
    "staged_treatment_executor",
    "staged_treatment_projection",
    "staged_treatment_semantic_registry",
    "translate_staged_treatment",
]
