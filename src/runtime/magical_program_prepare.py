"""PREPARE, revalidation, accounting, and committed-output checks."""
from __future__ import annotations

import copy
from collections import defaultdict
from typing import Any, Mapping

from .sandbox import SandboxWorld
from .magical_program_binding import (
    bind_requirements,
    require_capacity,
    runtime_bindings,
    value_signature,
)
from .magical_program_model import (
    BoundHostRecord,
    PreparedProgramEffect,
    PreparedProgramPlan,
    ProgramRuntimeError,
    complete_runtime_state,
    history_digest,
    program_digest,
    records_for,
)

_JSON = dict[str, Any]


def check_profile_and_budget(
    runtime: Any,
    program: Mapping[str, Any],
    report: Mapping[str, Any],
    world: SandboxWorld,
) -> None:
    if report.get("status") not in {"Feasible", "ConditionallyFeasible"}:
        raise ProgramRuntimeError(
            "ProgramFeasibilityNotExecutable",
            "Program is not executable.",
            stage="PREPARE",
        )
    checks = (
        (
            float(program["budget"]["energy_j"]),
            runtime.profile.max_energy_j,
            "ProgramRuntimeEnergyLimitExceeded",
        ),
        (
            int(program["budget"]["events"]),
            runtime.profile.max_events,
            "ProgramRuntimeEventLimitExceeded",
        ),
        (
            int(program["budget"]["microsteps"]),
            runtime.profile.max_microsteps,
            "ProgramRuntimeMicrostepLimitExceeded",
        ),
        (
            int(program["budget"]["concurrency"]),
            runtime.profile.max_concurrency,
            "ProgramRuntimeConcurrencyLimitExceeded",
        ),
    )
    for actual, ceiling, code in checks:
        if actual > ceiling:
            raise ProgramRuntimeError(
                code,
                f"Requested budget {actual} exceeds host ceiling {ceiling}.",
                stage="PREPARE",
            )
    provenance = report.get("provenance", {})
    if (
        provenance.get("runtime_profile") != runtime.evaluator.profile_id
        or provenance.get("profile_revision")
        != runtime.evaluator.profile_revision
    ):
        raise ProgramRuntimeError(
            "ProgramEvaluatorProfileMismatch",
            "Evaluator profile is incompatible.",
            stage="PREPARE",
        )
    if world.runtime_state.get("runtime_profile") != runtime.profile.record():
        raise ProgramRuntimeError(
            "ProgramRuntimeProfileMismatch",
            "Authoritative runtime profile is incompatible.",
            stage="PREPARE",
        )


def _bind_effect(
    runtime: Any,
    node: Mapping[str, Any],
    lowering: Mapping[str, Any],
    bindings: Mapping[str, Mapping[str, Any]],
    world: SandboxWorld,
) -> PreparedProgramEffect:
    registration = runtime.contracts.resolve(
        node["contract"]["contract_id"], node["contract"]["revision"]
    )
    if registration.instruction != node["instruction"]:
        raise ProgramRuntimeError(
            "ProgramRuntimeContractMismatch",
            "Runtime contract instruction mismatch.",
            stage="PREPARE",
        )
    frozen = tuple(copy.deepcopy(bindings[name]) for name in node["inputs"])
    observed = tuple(value_signature(value) for value in frozen)
    if observed != registration.input_kinds:
        raise ProgramRuntimeError(
            "ProgramRuntimeContractInputMismatch",
            f"Runtime input signature {observed!r} does not match "
            f"{registration.input_kinds!r}.",
            stage="PREPARE",
        )
    requirements = lowering["obligations"]["declared_requirements"]
    capability_records = bind_requirements(
        category="capabilities",
        requirements=requirements["capabilities"],
        records=world.capabilities,
        bindings=bindings,
    )
    lease_records = bind_requirements(
        category="leases",
        requirements=requirements["leases"],
        records=world.leases,
        bindings=bindings,
    )
    identity_records = bind_requirements(
        category="identities",
        requirements=requirements["identities"],
        records=world.runtime_state.get("identity_evidence", {}),
        bindings=bindings,
    )
    evidence_records = bind_requirements(
        category="evidence",
        requirements=requirements["evidence"],
        records=world.runtime_state.get("evidence", {}),
        bindings=bindings,
    )
    accounting_records = bind_requirements(
        category="accounting",
        requirements=requirements["accounting"],
        records=world.ledgers,
        bindings=bindings,
    )
    resources = requirements["resources"]
    if int(resources["events"]) < registration.emitted_events:
        raise ProgramRuntimeError(
            "ProgramEventDeclarationInsufficient",
            "Contract emits more History events than the artifact declared.",
            stage="PREPARE",
        )
    require_capacity(accounting_records, resources, stage="PREPARE")
    return PreparedProgramEffect(
        node_id=str(node["node_id"]),
        order=int(node["order"]),
        contract_id=registration.contract_id,
        contract_revision=registration.revision,
        input_bindings=tuple(node["inputs"]),
        frozen_values=frozen,
        output_binding=str(node["produces"][0]),
        capability_records=capability_records,
        lease_records=lease_records,
        identity_records=identity_records,
        evidence_records=evidence_records,
        accounting_records=accounting_records,
        energy_j=float(resources["energy_j"]),
        matter_kg=float(resources["matter_kg"]),
        event_count=int(resources["events"]),
    )


def _aggregate_accounting(
    effects: list[PreparedProgramEffect], world: SandboxWorld, *, stage: str
) -> None:
    totals: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"energy_j": 0.0, "matter_kg": 0.0, "events": 0}
    )
    requirements: dict[str, BoundHostRecord] = {}
    for effect in effects:
        for bound in effect.accounting_records:
            requirements[bound.record_id] = bound
            totals[bound.record_id]["energy_j"] += effect.energy_j
            totals[bound.record_id]["matter_kg"] += effect.matter_kg
            totals[bound.record_id]["events"] += effect.event_count
    for record_id, resources in totals.items():
        current = world.ledgers.get(record_id)
        if current is None:
            raise ProgramRuntimeError(
                "ProgramAccountingMissing",
                f"Bound ledger {record_id!r} is absent.",
                stage=stage,
            )
        bound = requirements[record_id]
        require_capacity(
            (
                BoundHostRecord(
                    "accounting",
                    bound.requirement_id,
                    record_id,
                    copy.deepcopy(current),
                ),
            ),
            resources,
            stage=stage,
        )


def prepare_program(
    runtime: Any,
    program: Mapping[str, Any],
    report: Mapping[str, Any],
    world: SandboxWorld,
) -> PreparedProgramPlan:
    if world.commit_fenced or world.stop_state != "Running":
        raise ProgramRuntimeError(
            "ProgramEmergencyStopFence",
            "Runtime is fenced before PREPARE.",
            stage="PREPARE",
        )
    before = world.clone()
    check_profile_and_budget(runtime, program, report, world)
    digest = program_digest(program)
    if (
        report.get("input", {}).get("content_sha256") != digest
        or report.get("input", {}).get("program_id") != program.get("program_id")
    ):
        raise ProgramRuntimeError(
            "ProgramReportArtifactMismatch",
            "FeasibilityReport does not describe this exact program.",
            stage="PREPARE",
        )

    bindings = runtime_bindings(program, report, world)
    lowering = {
        item["node_id"]: item
        for item in report["interpretations"]["kernel_plan"]["effect_nodes"]
        if item.get("contract") is not None
    }
    effects: list[PreparedProgramEffect] = []
    entities: set[str] = set()
    revisions: set[str] = set()
    for node in sorted(
        program["nodes"], key=lambda item: (item["order"], item["node_id"])
    ):
        if node["instruction"] not in {"effect.invoke", "evidence.observe"}:
            continue
        effect = _bind_effect(
            runtime, node, lowering[node["node_id"]], bindings, world
        )
        effects.append(effect)
        for value in effect.frozen_values:
            if value.get("kind") == "reference":
                entities.add(str(value["entity_id"]))
                revisions.add(str(value["state_revision"]))

    energy = sum(item.energy_j for item in effects)
    matter = sum(item.matter_kg for item in effects)
    events = sum(item.event_count for item in effects)
    if energy > runtime.profile.max_energy_j:
        raise ProgramRuntimeError(
            "ProgramRuntimeAggregateEnergyExceeded",
            "Prepared effects exceed the host Energy ceiling.",
            stage="PREPARE",
        )
    max_matter = getattr(runtime.profile, "max_matter_kg", float("inf"))
    if matter > max_matter:
        raise ProgramRuntimeError(
            "ProgramRuntimeAggregateMatterExceeded",
            "Prepared effects exceed the host Matter ceiling.",
            stage="PREPARE",
        )
    if events > runtime.profile.max_events:
        raise ProgramRuntimeError(
            "ProgramRuntimeAggregateEventExceeded",
            "Prepared effects exceed the host event ceiling.",
            stage="PREPARE",
        )
    _aggregate_accounting(effects, world, stage="PREPARE")

    runtime._prepare_sequence += 1
    prepared = PreparedProgramPlan(
        plan_id=(
            f"prepared:{digest[:16]}:runtime-local:"
            f"{runtime._prepare_sequence:08d}"
        ),
        program_id=str(program["program_id"]),
        program_digest=digest,
        source_world_revision=world.revision,
        source_history_digest=history_digest(world.history),
        runtime_profile=runtime.profile.record(),
        runtime_bindings=copy.deepcopy(bindings),
        effects=tuple(sorted(effects, key=lambda item: (item.order, item.node_id))),
        output_declarations=tuple(copy.deepcopy(program["outputs"])),
        reserved_energy_j=energy,
        reserved_matter_kg=matter,
        reserved_events=events,
        frozen_entity_ids=tuple(sorted(entities)),
        frozen_state_revisions=tuple(sorted(revisions)),
        report_status=str(report["status"]),
    )
    if complete_runtime_state(world) != complete_runtime_state(before):
        raise RuntimeError("PREPARE mutated authoritative state")
    return prepared


def revalidate_program(
    runtime: Any, prepared: PreparedProgramPlan, world: SandboxWorld
) -> _JSON:
    if world.commit_fenced or world.stop_state != "Running":
        raise ProgramRuntimeError(
            "ProgramEmergencyStopFence",
            "Runtime is fenced before COMMIT.",
            stage="REVALIDATE",
        )
    if world.revision != prepared.source_world_revision:
        raise ProgramRuntimeError(
            "ProgramStaleWorldRevision",
            "World revision changed after PREPARE.",
            stage="REVALIDATE",
        )
    if history_digest(world.history) != prepared.source_history_digest:
        raise ProgramRuntimeError(
            "ProgramHistoryDrift",
            "History changed after PREPARE.",
            stage="REVALIDATE",
        )
    if world.runtime_state.get("runtime_profile") != prepared.runtime_profile:
        raise ProgramRuntimeError(
            "ProgramRuntimeProfileMismatch",
            "Runtime profile changed after PREPARE.",
            stage="REVALIDATE",
        )
    stores = {
        "capabilities": world.capabilities,
        "leases": world.leases,
        "identities": world.runtime_state.get("identity_evidence", {}),
        "evidence": world.runtime_state.get("evidence", {}),
        "accounting": world.ledgers,
    }
    ids: dict[str, list[str]] = {category: [] for category in stores}
    for effect in prepared.effects:
        for value in effect.frozen_values:
            if value.get("kind") != "reference":
                continue
            entity = world.entities.get(value["entity_id"])
            if entity is None or entity.get("state_revision") != value["state_revision"]:
                raise ProgramRuntimeError(
                    "ProgramStaleIdentity",
                    "Resolved entity changed after PREPARE.",
                    stage="REVALIDATE",
                )
        for bound in records_for(effect):
            if stores[bound.category].get(bound.record_id) != bound.frozen_record:
                code = {
                    "capabilities": "ProgramCapabilityDrift",
                    "leases": "ProgramLeaseDrift",
                    "identities": "ProgramIdentityStale",
                    "evidence": "ProgramEvidenceStale",
                    "accounting": "ProgramAccountingDrift",
                }[bound.category]
                raise ProgramRuntimeError(
                    code,
                    f"Bound record {bound.record_id!r} changed after PREPARE.",
                    stage="REVALIDATE",
                )
            ids[bound.category].append(bound.record_id)
    _aggregate_accounting(list(prepared.effects), world, stage="REVALIDATE")
    return {
        "status": "Pass",
        "world_revision": world.revision,
        "history_digest": prepared.source_history_digest,
        "frozen_entity_ids": list(prepared.frozen_entity_ids),
        "frozen_state_revisions": list(prepared.frozen_state_revisions),
        "bound_record_ids": {
            category: sorted(set(values)) for category, values in ids.items()
        },
    }


def consume_effect(effect: PreparedProgramEffect, world: SandboxWorld) -> None:
    for bound in effect.accounting_records:
        ledger = world.ledgers[bound.record_id]
        ledger["available_energy_j"] = (
            float(ledger.get("available_energy_j", 0.0)) - effect.energy_j
        )
        ledger["available_matter_kg"] = (
            float(ledger.get("available_matter_kg", 0.0)) - effect.matter_kg
        )
        ledger["events_remaining"] = (
            int(ledger.get("events_remaining", 0)) - effect.event_count
        )
        ledger.setdefault("allocations", {})[effect.node_id] = {
            "energy_j": effect.energy_j,
            "matter_kg": effect.matter_kg,
            "events": effect.event_count,
            "requirement_id": bound.requirement_id,
        }


def verify_output(
    declaration: Mapping[str, Any], value: Mapping[str, Any]
) -> _JSON:
    kind = declaration["kind"]
    result: _JSON = {
        "name": declaration["name"],
        "binding": declaration["binding"],
        "kind": kind,
    }
    if kind == "event":
        if not isinstance(value.get("event_id"), str):
            raise ProgramRuntimeError(
                "ProgramCommittedOutputMismatch",
                "Declared event was not committed.",
                stage="COMMIT",
            )
        result["event_id"] = value["event_id"]
    elif kind == "artifact":
        if not isinstance(value.get("artifact_id"), str):
            raise ProgramRuntimeError(
                "ProgramCommittedOutputMismatch",
                "Declared artifact was not committed.",
                stage="COMMIT",
            )
        result["artifact_id"] = value["artifact_id"]
    elif kind == "reference":
        if value.get("kind") != "reference":
            raise ProgramRuntimeError(
                "ProgramCommittedOutputMismatch",
                "Declared reference was not resolved.",
                stage="COMMIT",
            )
        result.update(
            {
                "entity_id": value["entity_id"],
                "state_revision": value["state_revision"],
            }
        )
    elif kind in {"evidence", "effect_result"}:
        if value.get("kind") != kind:
            raise ProgramRuntimeError(
                "ProgramCommittedOutputMismatch",
                f"Declared {kind} was not committed.",
                stage="COMMIT",
            )
        result["value"] = copy.deepcopy(dict(value))
    elif kind == "value":
        result["value"] = copy.deepcopy(dict(value))
    else:
        raise ProgramRuntimeError(
            "ProgramCommittedOutputMismatch",
            f"Unsupported output kind {kind!r}.",
            stage="COMMIT",
        )
    return result
