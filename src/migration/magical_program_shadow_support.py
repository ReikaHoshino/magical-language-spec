"""Shared types and construction helpers for true MagicalProgram migration."""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Mapping

from src.evaluator.magical_program import MagicalProgramEvaluator
from src.runtime.magical_program import MagicalProgramRuntime, ProgramRuntimeProfile
from src.runtime.sandbox import SandboxWorld

_JSON = dict[str, Any]
ContractPair = tuple[tuple[str, str], tuple[str, str] | None]


@dataclass(frozen=True)
class ShadowTranslation:
    program: _JSON
    world: SandboxWorld
    evaluator: MagicalProgramEvaluator
    runtime: MagicalProgramRuntime | None
    classification: str
    source_pair: ContractPair


def bundle_contract_pair(bundle: Mapping[str, Any]) -> ContractPair:
    semantic = bundle["semantic_contract"]
    runtime = bundle.get("runtime_contract")
    return (
        (str(semantic["contract_id"]), str(semantic["revision"])),
        None
        if runtime is None
        else (str(runtime["contract_id"]), str(runtime["revision"])),
    )


def compatibility() -> _JSON:
    return {
        "registry_id": "registry:reference-experimental",
        "registry_revision": "1",
        "profile_id": "profile:reference-experimental",
        "profile_revision": "1",
    }


def profile_from_bundle(bundle: Mapping[str, Any]) -> ProgramRuntimeProfile:
    limits = bundle["profiles"]["sandbox"]["limits"]
    return ProgramRuntimeProfile(
        max_energy_j=float(limits["max_energy_j"]),
        max_matter_kg=1_000.0,
        max_events=int(limits["max_events_per_commit"]),
        max_microsteps=int(limits["max_microsteps_per_tick"]),
        max_concurrency=int(limits["max_concurrency"]),
    )


def world_from_bundle(
    bundle: Mapping[str, Any], profile: ProgramRuntimeProfile
) -> SandboxWorld:
    source = bundle["initial_world"]
    runtime_state = copy.deepcopy(source.get("runtime_state", {}))
    runtime_state["runtime_profile"] = profile.record()
    runtime_state.setdefault("reservations", {})
    runtime_state.setdefault("prepared_plans", {})
    runtime_state.setdefault("identity_evidence", {})
    runtime_state.setdefault("evidence", {})
    return SandboxWorld(
        revision=str(source["revision"]),
        entities=copy.deepcopy(source["entities"]),
        capabilities=copy.deepcopy(source["capabilities"]),
        leases=copy.deepcopy(source["leases"]),
        ledgers=copy.deepcopy(source["ledgers"]),
        history=copy.deepcopy(source["history"]),
        controllers=copy.deepcopy(source.get("controllers", {})),
        runtime_state=runtime_state,
        process_state=copy.deepcopy(
            source.get(
                "process_state",
                {
                    "process_id": "process:shadow-migration",
                    "status": "Idle",
                    "prepared_plan_id": None,
                },
            )
        ),
    )


def program_envelope(
    bundle: Mapping[str, Any],
    *,
    program_id: str,
    budget_energy: float,
    budget_events: int,
    values: list[_JSON],
    nodes: list[_JSON],
    edges: list[_JSON],
    outputs: list[_JSON],
) -> _JSON:
    semantic = bundle["semantic_contract"]
    return {
        "artifact_kind": "MagicalProgram",
        "artifact_version": "0",
        "contract": {"contract_id": "magical-program", "revision": "0"},
        "stability": "experimental",
        "program_id": program_id,
        "provenance": {
            "relation": "lowered",
            "input_stage": "program",
            "source": {
                "artifact_kind": "SpellInstanceBundle",
                "artifact_version": str(bundle["artifact_version"]),
                "artifact_id": (
                    f"contract:{semantic['contract_id']}:{semantic['revision']}"
                ),
                "stage": "bundle",
            },
        },
        "compatibility": compatibility(),
        "budget": {
            "energy_j": budget_energy,
            "events": budget_events,
            "microsteps": max(1, len(nodes) + len(edges)),
            "concurrency": 1,
        },
        "values": values,
        "nodes": nodes,
        "edges": edges,
        "outputs": outputs,
    }


def add_identity_record(
    world: SandboxWorld, entity_id: str, state_revision: str
) -> None:
    world.runtime_state["identity_evidence"][f"identity:shadow:{entity_id}"] = {
        "active": True,
        "entity_id": entity_id,
        "state_revision": state_revision,
        "kind": "ResolvedIdentity",
        "revision": "1",
    }


def configure_capability(
    world: SandboxWorld,
    capability_id: str,
    *,
    entity_id: str,
    effect: str,
    scope: str = "local",
) -> None:
    capability = world.capabilities.get(capability_id)
    if capability is None:
        return
    capability.update(
        {
            "entity_id": entity_id,
            "effects": [effect],
            "scope": scope,
            "revision": str(capability.get("revision", "1")),
        }
    )


def configure_lease(
    world: SandboxWorld,
    lease_id: str,
    *,
    entity_id: str,
    mode: str,
    scope: str = "local",
) -> None:
    lease = world.leases.get(lease_id)
    if lease is None:
        return
    lease.update(
        {
            "entity_id": entity_id,
            "mode": mode,
            "scope": scope,
            "revision": str(lease.get("revision", "1")),
        }
    )


def configure_ledger(
    world: SandboxWorld,
    ledger_id: str,
    *,
    entity_id: str,
    kind: str,
    default_events: int,
) -> None:
    ledger = world.ledgers.get(ledger_id)
    if ledger is None:
        return
    ledger.update(
        {
            "entity_id": entity_id,
            "kind": kind,
            "available_energy_j": float(ledger.get("available_energy_j", 0.0)),
            "available_matter_kg": float(ledger.get("available_matter_kg", 0.0)),
            "events_remaining": int(ledger.get("events_remaining", default_events)),
            "allocations": copy.deepcopy(ledger.get("allocations", {})),
            "revision": str(ledger.get("revision", "1")),
        }
    )


__all__ = [
    "ContractPair",
    "ShadowTranslation",
    "add_identity_record",
    "bundle_contract_pair",
    "compatibility",
    "configure_capability",
    "configure_lease",
    "configure_ledger",
    "profile_from_bundle",
    "program_envelope",
    "world_from_bundle",
]
