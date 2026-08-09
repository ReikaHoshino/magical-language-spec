"""Generic MagicalProgram migrations for DEBUG-HELL-001..003."""
from __future__ import annotations

import copy
import math
from typing import Any, Mapping, Sequence

from src.evaluator.magical_program import MagicalProgramEvaluator
from src.evaluator.magical_program_contracts import (
    ProgramContractRegistration,
    ProgramContractRegistry,
    default_program_contract_registry,
)
from src.evaluator.schema import validate_feasibility_report
from src.runtime.magical_program import (
    MagicalProgramRuntime,
    ProgramRuntimeContractRegistry,
    ProgramRuntimeError,
    RuntimeContractRegistration,
)
from src.runtime.magical_program_model import (
    PreparedProgramEffect,
    PreparedProgramPlan,
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
_PATHOLOGICAL_MODEL = {
    "model_id": "model:debug-water-domain",
    "revision": "1",
    "maximum_density_kg_m3": 2000,
    "may_rewrite_explicit_constraints": False,
}
_HYDRA_MODEL = {
    "model_id": "controller:debug003:hydra",
    "revision": "1",
    "self_triggering": True,
    "transaction_scope": "all-microsteps",
    "termination": "budget-or-emergency-stop",
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


def _empty_obligations() -> _JSON:
    return {
        "capabilities": [],
        "leases": [],
        "identities": [],
        "evidence": [],
        "accounting": [],
        "resources": {"energy_j": 0.0, "matter_kg": 0.0, "events": 0},
    }


def debug_semantic_registry() -> ProgramContractRegistry:
    registry = default_program_contract_registry()
    registry.register(
        ProgramContractRegistration(
            "debug.pathological-planning",
            "1",
            "effect.invoke",
            ("record:PathologicalPlanningModel", "record:PathologicalConstraints"),
            "effect_result",
            (),
            0.0,
            0.0,
            0,
            ("RESOLVE", "CHANNEL", "TRANSFER", "RECONFIGURE", "CONSTRAIN"),
            ("QUERY", "TRANSITION"),
        )
    )
    registry.register(
        ProgramContractRegistration(
            "debug.prepare-bound-transit",
            "1",
            "effect.invoke",
            (
                "reference",
                "reference",
                "record:PrepareBoundTransitPolicy",
                "record:PrepareBoundTransitPublication",
            ),
            "effect_result",
            ("capabilities", "leases", "identities", "accounting"),
            1.0,
            0.0,
            1,
            ("RESOLVE", "OBSERVE", "RECONFIGURE"),
            ("QUERY", "SAMPLE", "TRANSITION"),
        )
    )
    registry.register(
        ProgramContractRegistration(
            "debug.reactive-budget",
            "1",
            "effect.invoke",
            ("record:ReactiveHydraModel", "record:ReactiveHydraPolicy"),
            "effect_result",
            ("capabilities", "leases", "evidence", "accounting"),
            1.0,
            0.0,
            0,
            ("RESOLVE", "OBSERVE", "CONSTRAIN"),
            ("SAMPLE", "TRANSITION", "ACTIVATE", "DEACTIVATE"),
        )
    )
    return registry


class PathologicalPlanningEvaluator(MagicalProgramEvaluator):
    """Host-owned evaluator extension for preserved pathological constraints."""

    def evaluate_program(
        self,
        program: Mapping[str, Any],
        *,
        encoded_size: int = 0,
        world_state: Mapping[str, Any] | None = None,
        history: Sequence[Any] | None = None,
    ) -> _JSON:
        report = super().evaluate_program(
            program,
            encoded_size=encoded_size,
            world_state=world_state,
            history=history,
        )
        if report["status"] == "Infeasible":
            return report
        values = {item["value_id"]: item for item in program["values"]}
        model = values["planning_model"]
        constraints = values["pathological_constraints"]
        mass = float(_literal(constraints, "mass_kg"))
        radius = float(_literal(constraints, "radius_m"))
        acceleration = float(_literal(constraints, "acceleration_m_s2"))
        duration = float(_literal(constraints, "duration_s"))
        density = mass / ((4.0 / 3.0) * math.pi * radius**3)
        diagnostic = {
            "id": "diag:program:001:PlanningAssumptionCannotSatisfyAuthority",
            "stage": "PROGRAM_SEMANTICS",
            "code": "PlanningAssumptionCannotSatisfyAuthority",
            "severity": "fatal",
            "message": (
                "Explicit pathological constraints were preserved; missing "
                "authority cannot be synthesized by planning."
            ),
            "evidence_ids": [],
            "program_location": {
                "node_id": "analyze_pathological_constraints",
                "order": 0,
                "path": "/nodes/0",
            },
            "details": {
                "computed_density_kg_m3": density,
                "model_max_density_kg_m3": float(
                    _literal(model, "maximum_density_kg_m3")
                ),
                "explicit_constraints_rewritten": False,
                "planning_assumption_adopted": False,
                "feasible_is_authorized": False,
            },
        }
        typed = report["interpretations"]["typed_mir"]
        typed["pathological_analysis"] = {
            "explicit_source_constraints": {
                "MassKg": mass,
                "RadiusM": radius,
                "AccelerationMPerS2": acceleration,
                "DurationS": duration,
                "PreserveSphere": bool(_literal(constraints, "preserve_sphere")),
            },
            "computed_density_kg_m3": density,
            "model_max_density_kg_m3": float(
                _literal(model, "maximum_density_kg_m3")
            ),
            "explicit_constraints_rewritten": False,
            "terminal": {"kind": "Unknown", "arbitrary_binding": False},
            "mechanical_energy_j": 0.5
            * mass
            * (acceleration * duration) ** 2,
            "gravity_control_energy_is_mechanical_work": False,
            "planning_assumption_adopted": False,
            "feasible_is_authorized": False,
            "late_unrelated_entity_retarget": False,
        }
        report["status"] = "Infeasible"
        report["diagnostics"] = [diagnostic]
        report["assessments"].append(
            {
                "dimension": "planning_authority_boundary",
                "status": "Fail",
                "summary": "Planning cannot create missing authority or rewrite explicit constraints.",
                "diagnostic_ids": [diagnostic["id"]],
                "evidence_ids": [],
            }
        )
        validate_feasibility_report(report)
        return report


def _require_pathological_model(bundle: Mapping[str, Any]) -> None:
    observed = bundle.get("registry_extensions", {}).get("planning_models", [])
    if observed != [_PATHOLOGICAL_MODEL]:
        raise ValueError(
            "pathological planning model must exactly match the host registration"
        )


def translate_pathological_planning(
    bundle: Mapping[str, Any],
) -> ShadowTranslation:
    _require_pathological_model(bundle)
    constraints = {
        item["semantic_kind"]: item.get("value")
        for item in bundle["ingress"]["payload"].get("constraints", [])
    }
    values = [
        {
            "value_id": "planning_model",
            **_record(
                "PathologicalPlanningModel",
                model_id=_PATHOLOGICAL_MODEL["model_id"],
                revision=_PATHOLOGICAL_MODEL["revision"],
                maximum_density_kg_m3=_PATHOLOGICAL_MODEL[
                    "maximum_density_kg_m3"
                ],
                may_rewrite_explicit_constraints=False,
            ),
        },
        {
            "value_id": "pathological_constraints",
            **_record(
                "PathologicalConstraints",
                mass_kg=float(constraints["MassKg"]),
                radius_m=float(constraints["RadiusM"]),
                acceleration_m_s2=float(constraints["AccelerationMPerS2"]),
                duration_s=float(constraints["DurationS"]),
                preserve_sphere=bool(constraints["PreserveSphere"]),
                terminal_kind="Unknown",
                terminal_reason="OmittedBySource",
            ),
        },
    ]
    program = program_envelope(
        bundle,
        program_id="program:migrated:debug.pathological-planning:1",
        budget_energy=0.0,
        budget_events=0,
        values=values,
        nodes=[
            {
                "node_id": "analyze_pathological_constraints",
                "order": 0,
                "instruction": "effect.invoke",
                "inputs": ["planning_model", "pathological_constraints"],
                "produces": ["planning_result"],
                "contract": {
                    "contract_id": "debug.pathological-planning",
                    "revision": "1",
                },
                "obligations": _empty_obligations(),
            }
        ],
        edges=[],
        outputs=[
            {
                "name": "analysis",
                "binding": "planning_result",
                "kind": "effect_result",
            }
        ],
    )
    evaluator = PathologicalPlanningEvaluator(contracts=debug_semantic_registry())
    return ShadowTranslation(
        program,
        world_from_bundle(bundle, profile_from_bundle(bundle)),
        evaluator,
        None,
        "implemented",
        bundle_contract_pair(bundle),
    )


def _transit_executor(
    context: RuntimeExecutionContext,
    effect: PreparedProgramEffect,
    world: SandboxWorld,
) -> _JSON:
    del context
    source_ref, destination_ref, policy, publication = effect.frozen_values
    source_id = str(source_ref["entity_id"])
    destination_id = str(destination_ref["entity_id"])
    source = world.entities[source_id]
    if str(_literal(policy, "binding_mode")) != "PrepareBound":
        raise ProgramRuntimeError(
            "DynamicBindingNotAdmitted",
            "This contract admits only explicit PrepareBound identity.",
            stage="COMMIT",
        )
    if str(_literal(policy, "attached_object_policy")) != "ExplicitExcluded":
        raise ProgramRuntimeError(
            "AttachedObjectAuthorityMissing",
            "Attached inventory requires distinct authority.",
            stage="COMMIT",
        )
    source["location_id"] = destination_id
    source_revision = world.revision
    world.revision = next_world_revision(source_revision)
    event_id = str(_literal(publication, "event_id"))
    world.history.append(
        {
            "event_id": event_id,
            "effect_kind": "PrepareBoundTransit",
            "source_entity_id": source_id,
            "destination_entity_id": destination_id,
            "attached_objects_transferred": False,
        }
    )
    return {
        "kind": "effect_result",
        "status": "Committed",
        "node_id": effect.node_id,
        "contract_id": effect.contract_id,
        "contract_revision": effect.contract_revision,
        "entity_ids": [source_id, destination_id],
        "event_id": event_id,
        "effect_kind": "PrepareBoundTransit",
        "identity_policy": "PrepareBoundExistingIdentity",
        "source_world_revision": source_revision,
        "result_world_revision": world.revision,
    }


class PrepareBoundInterpositionRuntime(MagicalProgramRuntime):
    """Inject the registered TOCTOU change strictly after PREPARE."""

    def __init__(self, *, hook_spec: Mapping[str, Any], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.hook_spec = copy.deepcopy(dict(hook_spec))
        self.last_interposition: _JSON | None = None

    def commit(
        self, prepared: PreparedProgramPlan, world: SandboxWorld
    ) -> _JSON:
        bindings = prepared.runtime_bindings
        source = bindings["source_ref"]
        destination = bindings["destination_ref"]
        source_entity = world.entities[str(source["entity_id"])]
        destination_entity = world.entities[str(destination["entity_id"])]
        source_entity.update(
            {
                "name": "Marcus-Renamed-After-Prepare",
                "distance_to_selector_m": 8,
                "state_revision": self.hook_spec[
                    "mutated_source_state_revision"
                ],
            }
        )
        destination_entity["state_revision"] = self.hook_spec[
            "mutated_destination_state_revision"
        ]
        late_id = str(self.hook_spec["late_candidate_id"])
        world.entities[late_id] = {
            "entity_id": late_id,
            "state_revision": self.hook_spec[
                "late_candidate_state_revision"
            ],
            "kind": "Professor",
            "name": "Marcus",
            "distance_to_selector_m": 0.5,
            "location_id": "location:late",
        }
        lease_id = prepared.effects[0].lease_records[0].record_id
        world.leases[lease_id]["active"] = False
        self.last_interposition = {
            "after_prepare": True,
            "original_bound_source_entity_id": source["entity_id"],
            "original_bound_destination_entity_id": destination["entity_id"],
            "late_candidate_id": late_id,
            "silent_retarget": False,
        }
        try:
            return super().commit(prepared, world)
        except ProgramRuntimeError as error:
            if error.code in {
                "ProgramStaleIdentity",
                "ProgramLeaseDrift",
                "ProgramIdentityStale",
            }:
                raise ProgramRuntimeError(
                    "StaleReference",
                    "Prepare-bound identity or authority changed after PREPARE.",
                    stage=error.stage,
                ) from error
            raise


def translate_prepare_bound_transit(
    bundle: Mapping[str, Any],
) -> ShadowTranslation:
    parameters = bundle["execution"]["parameters"]
    profile = profile_from_bundle(bundle)
    world = world_from_bundle(bundle, profile)
    source_candidates = sorted(
        (
            (float(entity["distance_to_selector_m"]), entity_id, entity)
            for entity_id, entity in world.entities.items()
            if entity.get("kind") == "Professor"
            and entity.get("name") == parameters["source_selector"]["name"]
        ),
        key=lambda item: (item[0], item[1]),
    )
    destinations = sorted(
        (
            (entity_id, entity)
            for entity_id, entity in world.entities.items()
            if entity.get("kind") == "Laboratory"
            and entity.get("owner_id")
            == parameters["destination_selector"]["owner_id"]
        ),
        key=lambda item: item[0],
    )
    if not source_candidates or len(destinations) != 1:
        raise ValueError("prepare-bound transit selectors are not deterministically resolvable")
    nearest_distance = source_candidates[0][0]
    source_id = str(source_candidates[0][1])
    destination_id = str(destinations[0][0])
    required = bundle["execution"]["required_evidence"]
    capability_id = str(required["capabilities"][0])
    lease_id = str(required["leases"][0])
    ledger_id = str(required["accounting"][0])
    configure_capability(world, capability_id, entity_id=source_id, effect="Reconfigure")
    configure_lease(world, lease_id, entity_id=source_id, mode="Write")
    configure_ledger(
        world,
        ledger_id,
        entity_id=source_id,
        kind="PrepareBoundTransitAccounting",
        default_events=profile.max_events,
    )
    add_identity_record(world, source_id, str(world.entities[source_id]["state_revision"]))
    add_identity_record(
        world,
        destination_id,
        str(world.entities[destination_id]["state_revision"]),
    )
    values = [
        {
            "value_id": "source_selector",
            "kind": "selector",
            "selector": {
                "kind": "Professor",
                "name": str(parameters["source_selector"]["name"]),
                "distance_to_selector_m": nearest_distance,
            },
        },
        {
            "value_id": "destination_selector",
            "kind": "selector",
            "selector": {
                "kind": "Laboratory",
                "owner_id": str(
                    parameters["destination_selector"]["owner_id"]
                ),
            },
        },
        {
            "value_id": "transit_policy",
            **_record(
                "PrepareBoundTransitPolicy",
                binding_mode=str(parameters["binding_mode"]),
                attached_object_policy=str(parameters["attached_object_policy"]),
                silent_retarget_allowed=False,
                world_index_is_authority=False,
            ),
        },
        {
            "value_id": "transit_publication",
            **_record(
                "PrepareBoundTransitPublication",
                event_id=str(parameters["event_id"]),
            ),
        },
    ]
    program = program_envelope(
        bundle,
        program_id="program:migrated:debug.prepare-bound-transit:1",
        budget_energy=1.0,
        budget_events=1,
        values=values,
        nodes=[
            {
                "node_id": "resolve_transit_source",
                "order": 0,
                "instruction": "ref.resolve",
                "inputs": ["source_selector"],
                "produces": ["source_ref"],
            },
            {
                "node_id": "resolve_transit_destination",
                "order": 1,
                "instruction": "ref.resolve",
                "inputs": ["destination_selector"],
                "produces": ["destination_ref"],
            },
            {
                "node_id": "invoke_prepare_bound_transit",
                "order": 2,
                "instruction": "effect.invoke",
                "inputs": [
                    "source_ref",
                    "destination_ref",
                    "transit_policy",
                    "transit_publication",
                ],
                "produces": ["transit_result"],
                "contract": {
                    "contract_id": "debug.prepare-bound-transit",
                    "revision": "1",
                },
                "obligations": {
                    "capabilities": [
                        {
                            "requirement_id": "capability.prepare-bound-transit",
                            "target_binding": "source_ref",
                            "effect": "Reconfigure",
                            "scope": "local",
                        }
                    ],
                    "leases": [
                        {
                            "requirement_id": "lease.prepare-bound-transit",
                            "target_binding": "source_ref",
                            "mode": "Write",
                            "scope": "local",
                        }
                    ],
                    "identities": [
                        {
                            "requirement_id": "identity.transit-source",
                            "target_binding": "source_ref",
                        },
                        {
                            "requirement_id": "identity.transit-destination",
                            "target_binding": "destination_ref",
                        },
                    ],
                    "evidence": [],
                    "accounting": [
                        {
                            "requirement_id": "accounting.prepare-bound-transit",
                            "target_binding": "source_ref",
                            "kind": "PrepareBoundTransitAccounting",
                        }
                    ],
                    "resources": {"energy_j": 1.0, "matter_kg": 0.0, "events": 1},
                },
            },
        ],
        edges=[
            {"from": "resolve_transit_source", "to": "invoke_prepare_bound_transit"},
            {"from": "resolve_transit_destination", "to": "invoke_prepare_bound_transit"},
        ],
        outputs=[
            {"name": "result", "binding": "transit_result", "kind": "effect_result"},
            {"name": "event", "binding": "transit_result", "kind": "event"},
        ],
    )
    semantic = debug_semantic_registry()
    runtime = PrepareBoundInterpositionRuntime(
        hook_spec={
            key: parameters[key]
            for key in (
                "mutated_source_state_revision",
                "mutated_destination_state_revision",
                "late_candidate_id",
                "late_candidate_state_revision",
            )
        },
        evaluator=MagicalProgramEvaluator(contracts=semantic),
        contracts=ProgramRuntimeContractRegistry(
            (
                RuntimeContractRegistration(
                    "debug.prepare-bound-transit",
                    "1",
                    "effect.invoke",
                    (
                        "reference",
                        "reference",
                        "record:PrepareBoundTransitPolicy",
                        "record:PrepareBoundTransitPublication",
                    ),
                    "effect_result",
                    1,
                    _transit_executor,
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


def _require_hydra_model(bundle: Mapping[str, Any]) -> None:
    observed = bundle.get("registry_extensions", {}).get("controller_models", [])
    if observed != [_HYDRA_MODEL]:
        raise ValueError("Hydra model must exactly match the host registration")


def _hydra_executor(
    capture: dict[str, Any],
):
    def execute(
        context: RuntimeExecutionContext,
        effect: PreparedProgramEffect,
        world: SandboxWorld,
    ) -> _JSON:
        model, policy = effect.frozen_values
        if {
            "model_id": _literal(model, "model_id"),
            "revision": _literal(model, "revision"),
            "self_triggering": _literal(model, "self_triggering"),
            "transaction_scope": _literal(model, "transaction_scope"),
            "termination": _literal(model, "termination"),
        } != _HYDRA_MODEL:
            raise ProgramRuntimeError(
                "ReactiveModelMismatch",
                "Hydra controller model is not host registered.",
                stage="COMMIT",
            )
        controller_id = str(_literal(policy, "controller_id"))
        controller = world.controllers.get(controller_id)
        if controller is None or controller.get("active") is not True:
            raise ProgramRuntimeError(
                "AuthorityError",
                "Reactive controller is absent or inactive.",
                stage="COMMIT",
            )
        evidence = effect.evidence_records[0].frozen_record
        if evidence.get("kind") != "ReactiveEventBatch":
            raise ProgramRuntimeError(
                "ReactiveEvidenceMismatch",
                "Reactive event evidence has the wrong kind.",
                stage="COMMIT",
            )
        queue = sorted(
            copy.deepcopy(list(evidence["external_events"])),
            key=lambda item: item["event_id"],
        )
        external_order = [item["event_id"] for item in queue]
        budget = int(_literal(policy, "reactive_microstep_budget"))
        profile_budget = int(context.prepared.runtime_profile["limits"]["max_microsteps"])
        if budget != profile_budget or budget < 0:
            raise ProgramRuntimeError(
                "ReactiveModelMismatch",
                "Hydra budget differs from the runtime profile.",
                stage="COMMIT",
            )
        ledger = world.ledgers[effect.accounting_records[0].record_id]
        executed: list[_JSON] = []
        for microstep in range(budget):
            if not queue:
                break
            source_event = queue.pop(0)
            generated_id = (
                f"{_literal(policy, 'generated_event_prefix')}:{microstep}"
            )
            record = {
                "microstep": microstep,
                "tick": str(_literal(policy, "tick_id")),
                "source_event_id": source_event["event_id"],
                "generated_event_id": generated_id,
                "causal_parent_id": source_event["event_id"],
                "execution_ordinal": microstep,
                "resource_units": 1,
            }
            executed.append(record)
            controller["provisional_transition_count"] = microstep + 1
            ledger["resource_units"] = int(ledger.get("resource_units", 0)) - 1
            world.history.append(
                {
                    "event_id": generated_id,
                    "effect_kind": "ProvisionalHydraTransition",
                    "committed": False,
                }
            )
            queue.insert(
                0,
                {
                    "event_id": generated_id,
                    "target_entity_id": source_event["target_entity_id"],
                },
            )
        trace = {
            "controller_id": controller_id,
            "tick": str(_literal(policy, "tick_id")),
            "external_event_order": external_order,
            "executed_microsteps": executed,
            "budget": budget,
            "exhausted_at_microstep": budget,
            "pending_event_ids": [item["event_id"] for item in queue],
            "transaction_committed": False,
            "emergency_stop_requested": bool(
                _literal(policy, "emergency_stop_on_exhaustion")
            ),
        }
        capture["trace"] = copy.deepcopy(trace)
        raise ProgramRuntimeError(
            "MicrostepBudgetExceeded",
            f"Reactive controller exhausted its deterministic budget after {budget} microsteps.",
            stage="COMMIT",
        )

    return execute


class HydraRuntime(MagicalProgramRuntime):
    def __init__(self, *, capture: dict[str, Any], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._capture = capture

    @property
    def last_adversarial_trace(self) -> Mapping[str, Any] | None:
        value = self._capture.get("trace")
        return None if value is None else copy.deepcopy(value)


def translate_reactive_hydra(bundle: Mapping[str, Any]) -> ShadowTranslation:
    _require_hydra_model(bundle)
    parameters = bundle["execution"]["parameters"]
    profile = profile_from_bundle(bundle)
    world = world_from_bundle(bundle, profile)
    required = bundle["execution"]["required_evidence"]
    capability_id = str(required["capabilities"][0])
    lease_id = str(required["leases"][0])
    ledger_id = str(required["accounting"][0])
    capability = world.capabilities.get(capability_id)
    lease = world.leases.get(lease_id)
    ledger = world.ledgers.get(ledger_id)
    if capability is not None:
        capability.update(
            {
                "effects": ["Constrain"],
                "scope": "local",
                "revision": str(capability.get("revision", "1")),
            }
        )
    if lease is not None:
        lease.update(
            {
                "mode": "Actuate",
                "scope": "local",
                "revision": str(lease.get("revision", "1")),
            }
        )
    if ledger is not None:
        ledger.update(
            {
                "kind": "ReactiveControllerAccounting",
                "available_energy_j": 1.0,
                "available_matter_kg": 0.0,
                "events_remaining": profile.max_events,
                "allocations": {},
                "revision": str(ledger.get("revision", "1")),
            }
        )
    evidence_id = "evidence:debug003:reactive-event-batch"
    world.runtime_state["evidence"][evidence_id] = {
        "active": True,
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
                controller_id=str(parameters["controller_id"]),
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
                "node_id": "invoke_reactive_hydra",
                "order": 0,
                "instruction": "effect.invoke",
                "inputs": ["hydra_model", "hydra_policy"],
                "produces": ["hydra_result"],
                "contract": {
                    "contract_id": "debug.reactive-budget",
                    "revision": "1",
                },
                "obligations": {
                    "capabilities": [
                        {
                            "requirement_id": "capability.reactive-hydra",
                            "effect": "Constrain",
                            "scope": "local",
                        }
                    ],
                    "leases": [
                        {
                            "requirement_id": "lease.reactive-hydra",
                            "mode": "Actuate",
                            "scope": "local",
                        }
                    ],
                    "identities": [],
                    "evidence": [
                        {
                            "requirement_id": "evidence.reactive-event-batch",
                            "kind": "ReactiveEventBatch",
                        }
                    ],
                    "accounting": [
                        {
                            "requirement_id": "accounting.reactive-hydra",
                            "kind": "ReactiveControllerAccounting",
                        }
                    ],
                    "resources": {"energy_j": 1.0, "matter_kg": 0.0, "events": 0},
                },
            }
        ],
        edges=[],
        outputs=[
            {"name": "result", "binding": "hydra_result", "kind": "effect_result"}
        ],
    )
    capture: dict[str, Any] = {}
    semantic = debug_semantic_registry()
    runtime = HydraRuntime(
        capture=capture,
        evaluator=MagicalProgramEvaluator(contracts=semantic),
        contracts=ProgramRuntimeContractRegistry(
            (
                RuntimeContractRegistration(
                    "debug.reactive-budget",
                    "1",
                    "effect.invoke",
                    ("record:ReactiveHydraModel", "record:ReactiveHydraPolicy"),
                    "effect_result",
                    0,
                    _hydra_executor(capture),
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
    "HydraRuntime",
    "PathologicalPlanningEvaluator",
    "PrepareBoundInterpositionRuntime",
    "debug_semantic_registry",
    "translate_pathological_planning",
    "translate_prepare_bound_transit",
    "translate_reactive_hydra",
]
