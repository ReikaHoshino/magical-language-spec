"""Prepare-bound Reactive Hydra contract with a synthetic host anchor."""
from __future__ import annotations

import copy
from dataclasses import replace
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
)

from .magical_program_shadow_debug import (
    HydraRuntime,
    _HYDRA_MODEL,
    _hydra_executor,
    _record,
    _require_hydra_model,
)
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
_CONTRACT_ID = "debug.reactive-budget"
_CONTRACT_REVISION = "1"
_ANCHOR_KIND = "ReactiveControllerAnchor"


def hydra_semantic_registry() -> ProgramContractRegistry:
    registry = default_program_contract_registry()
    registry.register(
        ProgramContractRegistration(
            _CONTRACT_ID,
            _CONTRACT_REVISION,
            "effect.invoke",
            (
                "reference",
                "record:ReactiveHydraModel",
                "record:ReactiveHydraPolicy",
            ),
            "effect_result",
            (
                "capabilities",
                "leases",
                "identities",
                "evidence",
                "accounting",
            ),
            1.0,
            0.0,
            0,
            ("RESOLVE", "OBSERVE", "CONSTRAIN"),
            ("SAMPLE", "TRANSITION", "ACTIVATE", "DEACTIVATE"),
        )
    )
    return registry


def _anchored_executor(capture: dict[str, Any]):
    delegate = _hydra_executor(capture)

    def execute(
        context: RuntimeExecutionContext,
        effect: PreparedProgramEffect,
        world,
    ) -> _JSON:
        anchored = replace(effect, frozen_values=effect.frozen_values[1:])
        return delegate(context, anchored, world)

    return execute


def translate_reactive_hydra(bundle: Mapping[str, Any]) -> ShadowTranslation:
    _require_hydra_model(bundle)
    parameters = bundle["execution"]["parameters"]
    profile = profile_from_bundle(bundle)
    world = world_from_bundle(bundle, profile)
    required = bundle["execution"]["required_evidence"]
    capability_id = str(required["capabilities"][0])
    lease_id = str(required["leases"][0])
    ledger_id = str(required["accounting"][0])
    controller_id = str(parameters["controller_id"])

    anchor_id = "entity:runtime:reactive-controller-anchor"
    anchor_revision = "state:runtime:reactive-controller-anchor:1"
    world.entities[anchor_id] = {
        "entity_id": anchor_id,
        "state_revision": anchor_revision,
        "kind": _ANCHOR_KIND,
        "controller_id": controller_id,
    }
    configure_capability(
        world,
        capability_id,
        entity_id=anchor_id,
        effect="Constrain",
    )
    configure_lease(
        world,
        lease_id,
        entity_id=anchor_id,
        mode="Actuate",
    )
    configure_ledger(
        world,
        ledger_id,
        entity_id=anchor_id,
        kind="ReactiveControllerAccounting",
        default_events=profile.max_events,
    )
    ledger = world.ledgers.get(ledger_id)
    if ledger is not None:
        ledger.update(
            {
                "available_energy_j": 1.0,
                "available_matter_kg": 0.0,
                "events_remaining": profile.max_events,
                "resource_units": int(ledger.get("resource_units", 0)),
                "allocations": {},
                "revision": str(ledger.get("revision", "1")),
            }
        )
    add_identity_record(world, anchor_id, anchor_revision)

    evidence_id = "evidence:reactive-controller:event-batch"
    world.runtime_state["evidence"][evidence_id] = {
        "active": True,
        "entity_id": anchor_id,
        "state_revision": anchor_revision,
        "kind": "ReactiveEventBatch",
        "external_events": sorted(
            copy.deepcopy(parameters["external_events"]),
            key=lambda item: item["event_id"],
        ),
        "tick_id": str(parameters["tick_id"]),
        "revision": "1",
    }

    values = [
        {
            "value_id": "controller_anchor_selector",
            "kind": "selector",
            "selector": {
                "kind": _ANCHOR_KIND,
                "controller_id": controller_id,
            },
        },
        {
            "value_id": "hydra_model",
            **_record(
                "ReactiveHydraModel",
                model_id=_HYDRA_MODEL["model_id"],
                revision=_HYDRA_MODEL["revision"],
                self_triggering=True,
                transaction_scope=_HYDRA_MODEL["transaction_scope"],
                termination=_HYDRA_MODEL["termination"],
            ),
        },
        {
            "value_id": "hydra_policy",
            **_record(
                "ReactiveHydraPolicy",
                controller_id=controller_id,
                reactive_microstep_budget=int(
                    parameters["reactive_microstep_budget"]
                ),
                generated_event_prefix=str(parameters["generated_event_prefix"]),
                tick_id=str(parameters["tick_id"]),
                emergency_stop_on_exhaustion=bool(
                    parameters["emergency_stop_on_exhaustion"]
                ),
            ),
        },
    ]
    program = program_envelope(
        bundle,
        program_id="program:migrated:debug.reactive-budget:1",
        budget_energy=1.0,
        budget_events=0,
        values=values,
        nodes=[
            {
                "node_id": "resolve_controller_anchor",
                "order": 0,
                "instruction": "ref.resolve",
                "inputs": ["controller_anchor_selector"],
                "produces": ["controller_anchor_ref"],
            },
            {
                "node_id": "invoke_reactive_hydra",
                "order": 1,
                "instruction": "effect.invoke",
                "inputs": [
                    "controller_anchor_ref",
                    "hydra_model",
                    "hydra_policy",
                ],
                "produces": ["hydra_result"],
                "contract": {
                    "contract_id": _CONTRACT_ID,
                    "revision": _CONTRACT_REVISION,
                },
                "obligations": {
                    "capabilities": [
                        {
                            "requirement_id": "capability.reactive-hydra",
                            "target_binding": "controller_anchor_ref",
                            "effect": "Constrain",
                            "scope": "local",
                        }
                    ],
                    "leases": [
                        {
                            "requirement_id": "lease.reactive-hydra",
                            "target_binding": "controller_anchor_ref",
                            "mode": "Actuate",
                            "scope": "local",
                        }
                    ],
                    "identities": [
                        {
                            "requirement_id": "identity.reactive-hydra-anchor",
                            "target_binding": "controller_anchor_ref",
                        }
                    ],
                    "evidence": [
                        {
                            "requirement_id": "evidence.reactive-event-batch",
                            "target_binding": "controller_anchor_ref",
                            "kind": "ReactiveEventBatch",
                        }
                    ],
                    "accounting": [
                        {
                            "requirement_id": "accounting.reactive-hydra",
                            "target_binding": "controller_anchor_ref",
                            "kind": "ReactiveControllerAccounting",
                        }
                    ],
                    "resources": {
                        "energy_j": 1.0,
                        "matter_kg": 0.0,
                        "events": 0,
                    },
                },
            },
        ],
        edges=[
            {
                "from": "resolve_controller_anchor",
                "to": "invoke_reactive_hydra",
            }
        ],
        outputs=[
            {
                "name": "result",
                "binding": "hydra_result",
                "kind": "effect_result",
            }
        ],
    )

    capture: dict[str, Any] = {}
    semantic = hydra_semantic_registry()
    runtime = HydraRuntime(
        capture=capture,
        evaluator=MagicalProgramEvaluator(contracts=semantic),
        contracts=ProgramRuntimeContractRegistry(
            (
                RuntimeContractRegistration(
                    _CONTRACT_ID,
                    _CONTRACT_REVISION,
                    "effect.invoke",
                    (
                        "reference",
                        "record:ReactiveHydraModel",
                        "record:ReactiveHydraPolicy",
                    ),
                    "effect_result",
                    0,
                    _anchored_executor(capture),
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


__all__ = [
    "hydra_semantic_registry",
    "translate_reactive_hydra",
]
