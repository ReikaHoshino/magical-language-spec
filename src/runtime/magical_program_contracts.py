"""Host-owned runtime contract registrations for MagicalProgram-0."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable

from .sandbox import SandboxWorld
from .magical_program_model import (
    PreparedProgramEffect,
    ProgramRuntimeError,
    RuntimeExecutionContext,
    RuntimeExecutor,
    event_id,
    next_world_revision,
    occurrence_seed,
)


@dataclass(frozen=True)
class RuntimeContractRegistration:
    contract_id: str
    revision: str
    instruction: str
    input_kinds: tuple[str, ...]
    output_kind: str
    emitted_events: int
    executor: RuntimeExecutor

    def __post_init__(self) -> None:
        if self.instruction not in {"effect.invoke", "evidence.observe"}:
            raise ValueError("unsupported runtime instruction")
        if self.emitted_events < 0 or not callable(self.executor):
            raise ValueError("invalid runtime contract registration")
        for signature in self.input_kinds:
            if signature in {"object", "array", "any", "*"}:
                raise ValueError("untyped structured runtime signature")


class ProgramRuntimeContractRegistry:
    def __init__(
        self, registrations: Iterable[RuntimeContractRegistration] = ()
    ) -> None:
        self._items: dict[tuple[str, str], RuntimeContractRegistration] = {}
        for item in registrations:
            self.register(item)

    def register(self, item: RuntimeContractRegistration) -> None:
        key = (item.contract_id, item.revision)
        if key in self._items:
            raise ValueError(f"duplicate runtime contract: {key!r}")
        self._items[key] = item

    def resolve(self, contract_id: str, revision: str) -> RuntimeContractRegistration:
        item = self._items.get((contract_id, revision))
        if item is None:
            raise ProgramRuntimeError(
                "ProgramRuntimeUnknownContract",
                f"Unknown runtime contract {contract_id!r}@{revision!r}.",
                stage="PREPARE",
            )
        return item

    def admitted_pairs(self) -> set[tuple[str, str]]:
        return set(self._items)


def execute_generic_transition(
    context: RuntimeExecutionContext,
    effect: PreparedProgramEffect,
    world: SandboxWorld,
) -> dict:
    if len(effect.frozen_values) != 2:
        raise ProgramRuntimeError(
            "ProgramRuntimeContractInputMismatch",
            "generic.transition requires a reference and state.",
            stage="COMMIT",
        )
    reference, desired = effect.frozen_values
    entity_id, desired_state = reference.get("entity_id"), desired.get("value")
    if (
        reference.get("kind") != "reference"
        or not isinstance(entity_id, str)
        or not isinstance(desired_state, str)
    ):
        raise ProgramRuntimeError(
            "ProgramRuntimeContractInputMismatch",
            "generic.transition received invalid inputs.",
            stage="COMMIT",
        )
    if entity_id not in world.entities:
        raise ProgramRuntimeError(
            "ProgramStaleIdentity",
            f"Resolved entity {entity_id!r} is absent.",
            stage="COMMIT",
        )
    source_revision = world.revision
    result_revision = next_world_revision(source_revision)
    world.entities[entity_id]["status"] = desired_state
    world.entities[entity_id]["state_revision"] = (
        f"state:{entity_id}@{result_revision}"
    )
    world.revision = result_revision
    emitted = event_id(context.prepared, effect)
    world.history.append(
        {
            "event_id": emitted,
            "kind": "ProgramTransitionCommitted",
            "program_id": context.prepared.program_id,
            "node_id": effect.node_id,
            "contract": {
                "contract_id": effect.contract_id,
                "revision": effect.contract_revision,
            },
            "entity_ids": [entity_id],
            "desired_state": desired_state,
            "source_world_revision": source_revision,
            "result_world_revision": result_revision,
        }
    )
    return {
        "kind": "effect_result",
        "status": "Committed",
        "node_id": effect.node_id,
        "contract_id": effect.contract_id,
        "contract_revision": effect.contract_revision,
        "entity_ids": [entity_id],
        "event_id": emitted,
        "source_world_revision": source_revision,
        "result_world_revision": result_revision,
        "desired_state": desired_state,
    }


def execute_generic_observation(
    context: RuntimeExecutionContext,
    effect: PreparedProgramEffect,
    world: SandboxWorld,
) -> dict:
    if len(effect.frozen_values) != 1:
        raise ProgramRuntimeError(
            "ProgramRuntimeContractInputMismatch",
            "generic.observe requires one reference.",
            stage="COMMIT",
        )
    reference = effect.frozen_values[0]
    entity_id = reference.get("entity_id")
    if reference.get("kind") != "reference" or not isinstance(entity_id, str):
        raise ProgramRuntimeError(
            "ProgramRuntimeContractInputMismatch",
            "generic.observe received an invalid reference.",
            stage="COMMIT",
        )
    occurrence = hashlib.sha256(
        occurrence_seed(context.prepared, effect).encode()
    ).hexdigest()[:24]
    artifact_id = f"artifact:program:{occurrence}"
    store = world.runtime_state.setdefault("evidence_store", {}).setdefault(
        "artifacts", {}
    )
    if artifact_id in store:
        raise ProgramRuntimeError(
            "ProgramArtifactIdentityCollision",
            f"Artifact {artifact_id!r} already exists.",
            stage="COMMIT",
        )
    artifact = {
        "artifact_id": artifact_id,
        "program_id": context.prepared.program_id,
        "node_id": effect.node_id,
        "entity_id": entity_id,
        "entity_state_revision": world.entities[entity_id]["state_revision"],
        "truth_claim": False,
        "physical_effect": False,
        "source_history_digest": context.prepared.source_history_digest,
    }
    store[artifact_id] = artifact
    emitted = event_id(context.prepared, effect)
    world.history.append(
        {
            "event_id": emitted,
            "kind": "ProgramObservationRecorded",
            "program_id": context.prepared.program_id,
            "node_id": effect.node_id,
            "artifact_id": artifact_id,
            "entity_ids": [entity_id],
        }
    )
    return {
        "kind": "evidence",
        "status": "Committed",
        "node_id": effect.node_id,
        "contract_id": effect.contract_id,
        "contract_revision": effect.contract_revision,
        "entity_ids": [entity_id],
        "event_id": emitted,
        "artifact_id": artifact_id,
        "truth_claim": False,
        "physical_effect": False,
    }


def default_runtime_contracts() -> ProgramRuntimeContractRegistry:
    return ProgramRuntimeContractRegistry(
        (
            RuntimeContractRegistration(
                "generic.transition",
                "1",
                "effect.invoke",
                ("reference", "literal:string"),
                "effect_result",
                1,
                execute_generic_transition,
            ),
            RuntimeContractRegistration(
                "generic.observe",
                "1",
                "evidence.observe",
                ("reference",),
                "evidence",
                1,
                execute_generic_observation,
            ),
        )
    )
