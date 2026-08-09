"""Runtime-local data model and deterministic helpers for MagicalProgram-0."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from jsonschema import Draft202012Validator
from src.resources import resource_path
from .sandbox import SandboxWorld

_JSON = dict[str, Any]


class FrozenDict(dict):
    """Recursively immutable JSON-object representation for PreparedPlans."""

    @staticmethod
    def _immutable(*args: Any, **kwargs: Any) -> None:
        raise TypeError("prepared runtime data is immutable")

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    pop = _immutable
    popitem = _immutable
    setdefault = _immutable
    update = _immutable
    __ior__ = _immutable

    def __deepcopy__(self, memo: dict[int, Any]) -> "FrozenDict":
        return self


class FrozenList(list):
    """Immutable JSON-array representation that remains equal to normal lists."""

    @staticmethod
    def _immutable(*args: Any, **kwargs: Any) -> None:
        raise TypeError("prepared runtime data is immutable")

    __setitem__ = _immutable
    __delitem__ = _immutable
    append = _immutable
    clear = _immutable
    extend = _immutable
    insert = _immutable
    pop = _immutable
    remove = _immutable
    reverse = _immutable
    sort = _immutable
    __iadd__ = _immutable
    __imul__ = _immutable

    def __deepcopy__(self, memo: dict[int, Any]) -> "FrozenList":
        return self


def deep_freeze(value: Any) -> Any:
    """Freeze a JSON-like value without changing JSON equality or meaning."""

    if isinstance(value, (FrozenDict, FrozenList)):
        return value
    if isinstance(value, dict):
        return FrozenDict({key: deep_freeze(child) for key, child in value.items()})
    if isinstance(value, (list, tuple)):
        return FrozenList(deep_freeze(child) for child in value)
    return value


def deep_thaw(value: Any) -> Any:
    """Return a mutable deep copy of runtime-local frozen JSON data."""

    if isinstance(value, dict):
        return {key: deep_thaw(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [deep_thaw(child) for child in value]
    return copy.deepcopy(value)


@dataclass(frozen=True)
class ProgramRuntimeProfile:
    profile_id: str = "program-runtime:reference-experimental"
    revision: str = "0"
    max_energy_j: float = 500.0
    max_matter_kg: float = 1_000.0
    max_events: int = 16
    max_microsteps: int = 64
    max_concurrency: int = 1

    def record(self) -> _JSON:
        return {
            "profile_id": self.profile_id,
            "revision": self.revision,
            "limits": {
                "max_energy_j": self.max_energy_j,
                "max_matter_kg": self.max_matter_kg,
                "max_events": self.max_events,
                "max_microsteps": self.max_microsteps,
                "max_concurrency": self.max_concurrency,
            },
        }


class ProgramRuntimeError(RuntimeError):
    def __init__(self, code: str, message: str, *, stage: str) -> None:
        super().__init__(message)
        self.code, self.message, self.stage = code, message, stage


@dataclass(frozen=True)
class BoundHostRecord:
    category: str
    requirement_id: str
    record_id: str
    frozen_record: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "frozen_record", deep_freeze(self.frozen_record))


@dataclass(frozen=True)
class PreparedProgramEffect:
    node_id: str
    order: int
    contract_id: str
    contract_revision: str
    input_bindings: tuple[str, ...]
    frozen_values: tuple[Mapping[str, Any], ...]
    output_binding: str
    capability_records: tuple[BoundHostRecord, ...]
    lease_records: tuple[BoundHostRecord, ...]
    identity_records: tuple[BoundHostRecord, ...]
    evidence_records: tuple[BoundHostRecord, ...]
    accounting_records: tuple[BoundHostRecord, ...]
    energy_j: float
    matter_kg: float
    event_count: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "frozen_values",
            tuple(deep_freeze(value) for value in self.frozen_values),
        )


@dataclass(frozen=True)
class PreparedProgramPlan:
    plan_id: str
    program_id: str
    program_digest: str
    source_world_revision: str
    source_history_digest: str
    runtime_profile: Mapping[str, Any]
    runtime_bindings: Mapping[str, Any]
    effects: tuple[PreparedProgramEffect, ...]
    output_declarations: tuple[Mapping[str, Any], ...]
    reserved_energy_j: float
    reserved_matter_kg: float
    reserved_events: int
    frozen_entity_ids: tuple[str, ...]
    frozen_state_revisions: tuple[str, ...]
    report_status: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "runtime_profile", deep_freeze(self.runtime_profile))
        object.__setattr__(self, "runtime_bindings", deep_freeze(self.runtime_bindings))
        object.__setattr__(
            self,
            "output_declarations",
            tuple(deep_freeze(value) for value in self.output_declarations),
        )


@dataclass(frozen=True)
class RuntimeExecutionContext:
    prepared: PreparedProgramPlan
    registration: Any


RuntimeExecutor = Callable[
    [RuntimeExecutionContext, PreparedProgramEffect, SandboxWorld], _JSON
]


def stable_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def program_digest(program: Mapping[str, Any]) -> str:
    return stable_hash(program)


def history_digest(history: Sequence[Mapping[str, Any]]) -> str:
    return stable_hash(list(history))


def complete_runtime_state(world: SandboxWorld) -> _JSON:
    return {
        "configuration": world.configuration(),
        "capabilities": copy.deepcopy(world.capabilities),
        "leases": copy.deepcopy(world.leases),
        "ledgers": copy.deepcopy(world.ledgers),
        "stop_state": world.stop_state,
        "commit_fenced": world.commit_fenced,
    }


def complete_runtime_state_hash(world: SandboxWorld) -> str:
    return stable_hash(complete_runtime_state(world))


def restore_all(world: SandboxWorld, before: SandboxWorld) -> None:
    world.revision = before.revision
    world.entities = before.entities
    world.capabilities = before.capabilities
    world.leases = before.leases
    world.ledgers = before.ledgers
    world.history = before.history
    world.controllers = before.controllers
    world.runtime_state = before.runtime_state
    world.process_state = before.process_state
    world.stop_state = before.stop_state
    world.commit_fenced = before.commit_fenced


def validate_program_execution_trace(trace: Mapping[str, Any]) -> None:
    schema = json.loads(
        resource_path("schemas/magical-program-execution-trace.schema.json").read_text(
            encoding="utf-8"
        )
    )
    errors = sorted(
        Draft202012Validator(schema).iter_errors(trace),
        key=lambda item: list(item.absolute_path),
    )
    if errors:
        rendered = [
            f"/{'/'.join(str(part) for part in error.absolute_path)}: {error.message}"
            for error in errors
        ]
        raise ValueError("; ".join(rendered))


def next_world_revision(source: str) -> str:
    match = re.fullmatch(r"(.*?)(\d+)", source)
    if match:
        return f"{match.group(1)}{int(match.group(2)) + 1}"
    return f"world:successor:{hashlib.sha256(source.encode()).hexdigest()[:12]}"


def occurrence_seed(
    prepared: PreparedProgramPlan, effect: PreparedProgramEffect
) -> str:
    return ":".join(
        (
            prepared.program_digest,
            prepared.source_world_revision,
            prepared.source_history_digest,
            str(effect.order),
            effect.node_id,
            effect.contract_id,
            effect.contract_revision,
        )
    )


def event_id(prepared: PreparedProgramPlan, effect: PreparedProgramEffect) -> str:
    return (
        "event:program:"
        f"{hashlib.sha256(occurrence_seed(prepared, effect).encode()).hexdigest()[:24]}"
    )


def records_for(effect: PreparedProgramEffect) -> tuple[BoundHostRecord, ...]:
    return (
        *effect.capability_records,
        *effect.lease_records,
        *effect.identity_records,
        *effect.evidence_records,
        *effect.accounting_records,
    )


def program_sandbox_world() -> SandboxWorld:
    profile = ProgramRuntimeProfile().record()
    state_revision = "state:entity:generic:target@world:generic:1"
    return SandboxWorld(
        revision="world:generic:1",
        entities={
            "entity:generic:target": {
                "entity_id": "entity:generic:target",
                "state_revision": state_revision,
                "entity_type": "test-target",
                "scope": "local",
                "status": "initial",
            }
        },
        capabilities={
            "capability:host:transition": {
                "active": True,
                "entity_id": "entity:generic:target",
                "effects": ["Reconfigure"],
                "scope": "local",
                "revision": "1",
            },
            "capability:host:observe": {
                "active": True,
                "entity_id": "entity:generic:target",
                "effects": ["Observe"],
                "scope": "local",
                "revision": "1",
            },
        },
        leases={
            "lease:host:write": {
                "active": True,
                "entity_id": "entity:generic:target",
                "mode": "Write",
                "scope": "local",
                "revision": "1",
            }
        },
        ledgers={
            "ledger:host:energy-matter": {
                "active": True,
                "entity_id": "entity:generic:target",
                "kind": "EnergyMatter",
                "available_energy_j": 100.0,
                "available_matter_kg": 0.0,
                "events_remaining": 8,
                "allocations": {},
                "revision": "1",
            },
            "ledger:host:event-journal": {
                "active": True,
                "entity_id": "entity:generic:target",
                "kind": "EventJournal",
                "available_energy_j": 0.0,
                "available_matter_kg": 0.0,
                "events_remaining": 8,
                "allocations": {},
                "revision": "1",
            },
        },
        runtime_state={
            "runtime_profile": profile,
            "reservations": {},
            "prepared_plans": {},
            "identity_evidence": {
                "identity:host:target": {
                    "active": True,
                    "entity_id": "entity:generic:target",
                    "state_revision": state_revision,
                    "kind": "ResolvedIdentity",
                    "revision": "1",
                }
            },
            "evidence": {
                "evidence:host:freshness": {
                    "active": True,
                    "entity_id": "entity:generic:target",
                    "state_revision": state_revision,
                    "kind": "FreshnessAnchor",
                    "revision": "1",
                }
            },
        },
        process_state={
            "process_id": "process:program:idle",
            "status": "Idle",
            "prepared_plan_id": None,
        },
    )
