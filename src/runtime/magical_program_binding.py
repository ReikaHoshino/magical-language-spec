"""PREPARE-time reference and portable requirement binding."""
from __future__ import annotations

import copy
from typing import Any, Mapping, Sequence

from src.artifacts.magical_program_values import value_signature

from .sandbox import SandboxWorld
from .magical_program_model import (
    BoundHostRecord,
    ProgramRuntimeError,
    deep_freeze,
)

_JSON = dict[str, Any]


def selector_matches(entity: Mapping[str, Any], selector: Mapping[str, Any]) -> bool:
    return all(entity.get(key) == value for key, value in selector.items())


def resolve_reference(request: Mapping[str, Any], world: SandboxWorld) -> _JSON:
    if "selector" in request:
        matches = sorted(
            (
                (entity_id, entity)
                for entity_id, entity in world.entities.items()
                if selector_matches(entity, request["selector"])
            ),
            key=lambda item: item[0],
        )
    else:
        handle = request.get("handle_hint")
        matches = (
            [(handle, world.entities[handle])]
            if isinstance(handle, str) and handle in world.entities
            else []
        )
    if not matches:
        raise ProgramRuntimeError(
            "ProgramResolutionFailure",
            "Reference request resolved no entity.",
            stage="PREPARE",
        )
    if len(matches) != 1:
        raise ProgramRuntimeError(
            "ProgramResolutionAmbiguous",
            "Reference request resolved multiple entities.",
            stage="PREPARE",
        )
    entity_id, entity = matches[0]
    revision = entity.get("state_revision")
    if not isinstance(revision, str):
        raise ProgramRuntimeError(
            "ProgramIdentityRevisionMissing",
            "Selected entity has no state revision.",
            stage="PREPARE",
        )
    if request.get("revision_hint") not in {None, revision}:
        raise ProgramRuntimeError(
            "ProgramStaleIdentity",
            "Reference hint revision is stale.",
            stage="PREPARE",
        )
    return {
        "kind": "reference",
        "type_signature": "reference",
        "entity_id": entity_id,
        "state_revision": revision,
    }


def runtime_bindings(
    program: Mapping[str, Any],
    report: Mapping[str, Any],
    world: SandboxWorld,
) -> Mapping[str, Any]:
    """Realize and recursively freeze every binding available before COMMIT."""

    bindings: _JSON = {
        item["value_id"]: copy.deepcopy(item) for item in program["values"]
    }
    typed = {
        item["node_id"]: item
        for item in report["interpretations"]["typed_mir"]["nodes"]
    }
    for node in sorted(
        program["nodes"], key=lambda item: (item["order"], item["node_id"])
    ):
        instruction = node["instruction"]
        if instruction == "ref.resolve":
            produced = [
                resolve_reference(
                    typed[node["node_id"]]["evaluated_outputs"][0], world
                )
            ]
        elif instruction.startswith("pure.") or instruction == "assert.require":
            produced = typed[node["node_id"]]["evaluated_outputs"]
        else:
            continue
        for name, value in zip(node["produces"], produced, strict=True):
            bindings[name] = copy.deepcopy(value)
    return deep_freeze(bindings)


def record_matches(
    record: Mapping[str, Any],
    requirement: Mapping[str, Any],
    target: Mapping[str, Any] | None,
    *,
    category: str,
) -> bool:
    if not record.get("active"):
        return False
    if target is not None and record.get("entity_id") != target.get("entity_id"):
        return False
    scope = requirement.get("scope")
    if scope is not None and record.get("scope") != scope:
        return False
    if category == "capabilities":
        return requirement["effect"] in record.get("effects", [])
    if category == "leases":
        return record.get("mode") == requirement["mode"]
    if category in {"evidence", "accounting"}:
        return record.get("kind") == requirement["kind"]
    return True


def bind_requirements(
    *,
    category: str,
    requirements: Sequence[Mapping[str, Any]],
    records: Mapping[str, Mapping[str, Any]],
    bindings: Mapping[str, Mapping[str, Any]],
) -> tuple[BoundHostRecord, ...]:
    result: list[BoundHostRecord] = []
    for requirement in requirements:
        target_name = requirement.get("target_binding")
        target = bindings.get(target_name) if target_name else None
        if target is not None and target.get("kind") != "reference":
            raise ProgramRuntimeError(
                "ProgramRequirementTargetTypeMismatch",
                f"Requirement {requirement['requirement_id']!r} target is not a reference.",
                stage="PREPARE",
            )
        matches = [
            (record_id, record)
            for record_id, record in sorted(records.items())
            if record_matches(record, requirement, target, category=category)
        ]
        if not matches:
            code = {
                "capabilities": "ProgramAuthorityError",
                "leases": "ProgramLeaseError",
                "identities": "ProgramIdentityMissing",
                "evidence": "ProgramEvidenceMissing",
                "accounting": "ProgramAccountingMissing",
            }[category]
            raise ProgramRuntimeError(
                code,
                f"No host {category} record satisfies requirement {requirement['requirement_id']!r}.",
                stage="PREPARE",
            )
        if len(matches) != 1:
            raise ProgramRuntimeError(
                "ProgramRequirementAmbiguous",
                f"Multiple host {category} records satisfy requirement {requirement['requirement_id']!r}.",
                stage="PREPARE",
            )
        record_id, record = matches[0]
        if (
            target is not None
            and category in {"identities", "evidence"}
            and record.get("state_revision") != target.get("state_revision")
        ):
            code = (
                "ProgramIdentityStale"
                if category == "identities"
                else "ProgramEvidenceStale"
            )
            raise ProgramRuntimeError(
                code, f"Host {category} record is stale.", stage="PREPARE"
            )
        result.append(
            BoundHostRecord(
                category,
                str(requirement["requirement_id"]),
                record_id,
                deep_freeze(copy.deepcopy(dict(record))),
            )
        )
    return tuple(result)


def require_capacity(
    records: Sequence[BoundHostRecord],
    resources: Mapping[str, Any],
    *,
    stage: str,
) -> None:
    for bound in records:
        ledger = bound.frozen_record
        if float(ledger.get("available_energy_j", 0.0)) < float(
            resources["energy_j"]
        ):
            raise ProgramRuntimeError(
                "ProgramEnergyInsufficient",
                f"Ledger {bound.record_id!r} lacks Energy.",
                stage=stage,
            )
        if float(ledger.get("available_matter_kg", 0.0)) < float(
            resources["matter_kg"]
        ):
            raise ProgramRuntimeError(
                "ProgramMatterInsufficient",
                f"Ledger {bound.record_id!r} lacks Matter.",
                stage=stage,
            )
        if int(ledger.get("events_remaining", 0)) < int(resources["events"]):
            raise ProgramRuntimeError(
                "ProgramEventBudgetInsufficient",
                f"Ledger {bound.record_id!r} lacks event capacity.",
                stage=stage,
            )
