"""Independent generic transition migration used as the shadow-path control."""
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


def generic_semantic_registry() -> ProgramContractRegistry:
    registry = default_program_contract_registry()
    registry.register(
        ProgramContractRegistration(
            "example.generic-transition",
            "1",
            "effect.invoke",
            (
                "reference",
                "reference",
                "literal:string",
                "literal:number",
                "literal:string",
            ),
            "effect_result",
            ("capabilities", "leases", "identities", "accounting"),
            0.0,
            0.0,
            1,
            ("TRANSFER", "RECONFIGURE"),
            ("TRANSITION",),
        )
    )
    return registry


def generic_executor(
    context: RuntimeExecutionContext,
    effect: PreparedProgramEffect,
    world: SandboxWorld,
) -> _JSON:
    source_ref, target_ref, state, energy, event_hint = effect.frozen_values
    source_id, target_id = source_ref.get("entity_id"), target_ref.get("entity_id")
    if source_id not in world.entities or target_id not in world.entities:
        raise RuntimeError("resolved generic entities are absent")
    desired = state.get("value")
    amount = float(energy.get("value"))
    event_id = event_hint.get("value")
    if not isinstance(desired, str) or not isinstance(event_id, str):
        raise RuntimeError("invalid explicit generic transition values")
    for bound in effect.accounting_records:
        ledger = world.ledgers[bound.record_id]
        ledger["consumed_energy_j"] = (
            float(ledger.get("consumed_energy_j", 0.0)) + amount
        )
    source_revision = world.revision
    world.entities[target_id]["transition_state"] = desired
    world.revision = next_world_revision(source_revision)
    world.history.append(
        {
            "event_id": event_id,
            "effect_kind": "IndependentGenericTransition",
            "source_world_revision": source_revision,
            "result_world_revision": world.revision,
        }
    )
    return {
        "kind": "effect_result",
        "status": "Committed",
        "node_id": effect.node_id,
        "contract_id": effect.contract_id,
        "contract_revision": effect.contract_revision,
        "entity_ids": [source_id, target_id],
        "event_id": event_id,
        "source_world_revision": source_revision,
        "result_world_revision": world.revision,
        "desired_state": desired,
    }


def translate_generic_transition(bundle: Mapping[str, Any]) -> ShadowTranslation:
    parameters = bundle["execution"]["parameters"]
    source_id = str(parameters["source_entity_id"])
    target_id = str(parameters["target_entity_id"])
    ledger_id = str(parameters["ledger_id"])
    profile = profile_from_bundle(bundle)
    world = world_from_bundle(bundle, profile)
    source_revision = str(world.entities[source_id]["state_revision"])
    target_revision = str(world.entities[target_id]["state_revision"])

    capability_id = str(
        bundle["execution"]["required_evidence"]["capabilities"][0]
    )
    lease_id = str(bundle["execution"]["required_evidence"]["leases"][0])
    configure_capability(
        world,
        capability_id,
        entity_id=target_id,
        effect="Reconfigure",
    )
    configure_lease(world, lease_id, entity_id=target_id, mode="Write")
    configure_ledger(
        world,
        ledger_id,
        entity_id=target_id,
        kind="EnergyMatter",
        default_events=profile.max_events,
    )
    add_identity_record(world, target_id, target_revision)

    values = [
        {
            "value_id": "source_hint",
            "kind": "reference_hint",
            "handle_id": source_id,
            "revision": source_revision,
        },
        {
            "value_id": "target_hint",
            "kind": "reference_hint",
            "handle_id": target_id,
            "revision": target_revision,
        },
        {
            "value_id": "desired_state",
            "kind": "literal",
            "value": str(parameters["result_state"]),
        },
        {
            "value_id": "energy_j",
            "kind": "literal",
            "value": float(parameters["energy_j"]),
        },
        {
            "value_id": "event_hint",
            "kind": "literal",
            "value": str(parameters["event_id"]),
        },
    ]
    nodes = [
        {
            "node_id": "resolve_source",
            "order": 0,
            "instruction": "ref.resolve",
            "inputs": ["source_hint"],
            "produces": ["source_ref"],
        },
        {
            "node_id": "resolve_target",
            "order": 1,
            "instruction": "ref.resolve",
            "inputs": ["target_hint"],
            "produces": ["target_ref"],
        },
        {
            "node_id": "apply_transition",
            "order": 2,
            "instruction": "effect.invoke",
            "inputs": [
                "source_ref",
                "target_ref",
                "desired_state",
                "energy_j",
                "event_hint",
            ],
            "produces": ["transition_result"],
            "contract": {
                "contract_id": "example.generic-transition",
                "revision": "1",
            },
            "obligations": {
                "capabilities": [
                    {
                        "requirement_id": "capability.transition",
                        "target_binding": "target_ref",
                        "effect": "Reconfigure",
                        "scope": "local",
                    }
                ],
                "leases": [
                    {
                        "requirement_id": "lease.transition",
                        "target_binding": "target_ref",
                        "mode": "Write",
                        "scope": "local",
                    }
                ],
                "identities": [
                    {
                        "requirement_id": "identity.target",
                        "target_binding": "target_ref",
                    }
                ],
                "evidence": [],
                "accounting": [
                    {
                        "requirement_id": "accounting.transition",
                        "kind": "EnergyMatter",
                        "target_binding": "target_ref",
                    }
                ],
                "resources": {
                    "energy_j": float(parameters["energy_j"]),
                    "matter_kg": 0.0,
                    "events": 1,
                },
            },
        },
    ]
    program = program_envelope(
        bundle,
        program_id="program:migrated:example.generic-transition:1",
        budget_energy=float(bundle["execution"]["energy_budget_j"]),
        budget_events=1,
        values=values,
        nodes=nodes,
        edges=[
            {"from": "resolve_source", "to": "apply_transition"},
            {"from": "resolve_target", "to": "apply_transition"},
        ],
        outputs=[
            {
                "name": "result",
                "binding": "transition_result",
                "kind": "effect_result",
            },
            {
                "name": "event",
                "binding": "transition_result",
                "kind": "event",
            },
        ],
    )
    semantic = generic_semantic_registry()
    runtime_contracts = ProgramRuntimeContractRegistry(
        (
            RuntimeContractRegistration(
                "example.generic-transition",
                "1",
                "effect.invoke",
                (
                    "reference",
                    "reference",
                    "literal:string",
                    "literal:number",
                    "literal:string",
                ),
                "effect_result",
                1,
                generic_executor,
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


__all__ = [
    "generic_executor",
    "generic_semantic_registry",
    "translate_generic_transition",
]
