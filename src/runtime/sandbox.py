"""Deterministic v0.9 sandbox runtime for the supported reference subset.

The runtime consumes v0.8 evaluator output. It does not introduce a second
frontend/compiler path. PREPARE is reversible and does not mutate authoritative
WorldState/History; COMMIT revalidates current evidence before changing Σ/H.
Runtime/process bookkeeping is represented explicitly as Ω/P.
"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

MKI_PRIMITIVES = {
    "RESOLVE",
    "OBSERVE",
    "CHANNEL",
    "TRANSFER",
    "RECONFIGURE",
    "CONSTRAIN",
}

CANONICAL_RUNTIME_PROFILE = {
    "artifact_id": "runtime-profile:reference-fixture",
    "revision": "1",
}
CANONICAL_EPOCH = "epoch:fixture:1"
CANONICAL_TICK = "tick:fixture:25"
CANONICAL_EFFECTIVE_AT = "2026-01-01T00:00:00Z"
CANONICAL_COMMITTED_AT = "2026-01-01T00:00:00.005Z"


class RuntimeExecutionError(RuntimeError):
    """Fail-closed runtime error with stable diagnostic identity."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        stage: str,
        internal_cause: str | None = None,
        internal_trace: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.message = message
        self.internal_cause = internal_cause
        self.internal_trace = copy.deepcopy(internal_trace)

    def as_diagnostic(self) -> dict[str, Any]:
        diagnostic = {
            "stage": self.stage,
            "code": self.code,
            "severity": "fatal",
            "message": self.message,
        }
        if self.internal_cause is not None:
            diagnostic["internal_cause"] = self.internal_cause
        if self.internal_trace is not None:
            diagnostic["internal_trace"] = copy.deepcopy(self.internal_trace)
        return diagnostic


@dataclass
class SandboxWorld:
    """Authoritative sandbox configuration C=<Σ,H,Ω,P> for the reference runtime."""

    revision: str
    entities: dict[str, dict[str, Any]]
    capabilities: dict[str, dict[str, Any]]
    leases: dict[str, dict[str, Any]]
    ledgers: dict[str, dict[str, Any]]
    history: list[dict[str, Any]] = field(default_factory=list)
    controllers: dict[str, dict[str, Any]] = field(default_factory=dict)
    runtime_state: dict[str, Any] = field(default_factory=dict)
    process_state: dict[str, Any] = field(default_factory=dict)
    stop_state: str = "Running"
    commit_fenced: bool = False

    def clone(self) -> "SandboxWorld":
        return copy.deepcopy(self)

    def configuration(self) -> dict[str, Any]:
        """Expose the four specification domains without conflating them."""

        return {
            "Sigma": {
                "revision": self.revision,
                "entities": copy.deepcopy(self.entities),
                "controllers": copy.deepcopy(self.controllers),
            },
            "H": copy.deepcopy(self.history),
            "Omega": copy.deepcopy(self.runtime_state),
            "P": copy.deepcopy(self.process_state),
        }


@dataclass(frozen=True)
class PreparedPlan:
    """Reversible PREPARE result bound to the evidence seen at preparation."""

    plan_id: str
    operations: tuple[str, ...]
    typed_mir: dict[str, Any]
    kernel_plan: dict[str, Any]
    assumptions: tuple[dict[str, Any], ...]
    resource_reservations: tuple[dict[str, Any], ...]
    source_world_revision: str
    world_index_revision: str | None
    capability_ids: tuple[str, ...]
    lease_ids: tuple[str, ...]
    accounting_evidence_ids: tuple[str, ...]
    resolution_evidence_ids: tuple[str, ...]
    runtime_profile: dict[str, Any]
    report_status: str


def canonical_sandbox_world() -> SandboxWorld:
    """Return the deterministic sandbox world used by WB-CANON-001."""

    return SandboxWorld(
        revision="world:991",
        entities={
            "entity:source-water": {
                "entity_id": "entity:source-water",
                "state_revision": "state-revision:source-water@world:991",
                "kind": "MatterSource",
                "material": "water",
                "mass_kg": 100.0,
                "visible": True,
            }
        },
        capabilities={
            "capability:source-water": {
                "active": True,
                "entity_id": "entity:source-water",
                "effects": ["Read", "Transfer", "Reconfigure", "Constrain"],
            }
        },
        leases={
            "lease:source-water": {
                "active": True,
                "entity_id": "entity:source-water",
                "mode": "Write",
            }
        },
        ledgers={
            "ledger:matter-energy": {
                "active": True,
                "material": "water",
                "accounted_mass_kg": 100.0,
                "allocations_kg": {"entity:source-water": 100.0},
            }
        },
        runtime_state={
            "epoch": CANONICAL_EPOCH,
            "tick": "tick:fixture:24",
            "scheduler_phase": "Ingress",
            "channels": {
                "channel:matter:source-water": {
                    "kind": "Matter",
                    "open": False,
                }
            },
            "reservations": {},
            "active_processes": {},
            "runtime_profile": copy.deepcopy(CANONICAL_RUNTIME_PROFILE),
        },
        process_state={
            "process_id": "process:wb-canon-001",
            "status": "Idle",
            "prepared_plan_id": None,
        },
    )


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class SandboxRuntime:
    """Reference PREPARE/REVALIDATE/COMMIT runtime for v0.9."""

    def __init__(self, *, runtime_profile: dict[str, Any] | None = None) -> None:
        self.runtime_profile = copy.deepcopy(runtime_profile or CANONICAL_RUNTIME_PROFILE)

    def prepare(self, report: dict[str, Any], world: SandboxWorld) -> PreparedPlan:
        """Build a reversible PreparedPlan without changing Σ/H/Ω/P."""

        if world.commit_fenced or world.stop_state != "Running":
            raise RuntimeExecutionError(
                "EmergencyStopFence",
                "Sandbox is fenced; new PREPARE admission is forbidden.",
                stage="PREPARE",
            )
        if report.get("status") not in {"Feasible", "ConditionallyFeasible"}:
            raise RuntimeExecutionError(
                "FeasibilityNotExecutable",
                "Only Feasible or ConditionallyFeasible evaluator reports may enter PREPARE.",
                stage="PREPARE",
            )

        interpretations = report.get("interpretations", {})
        typed_mir = interpretations.get("typed_mir")
        kernel_plan = interpretations.get("kernel_plan")
        if not isinstance(typed_mir, dict) or not isinstance(kernel_plan, dict):
            raise RuntimeExecutionError(
                "PreparedPlanInputMissing",
                "TypedMIR and KernelPlan must come from the v0.8 evaluator report.",
                stage="PREPARE",
            )

        operations = tuple(kernel_plan.get("operations", ()))
        invalid = [operation for operation in operations if operation not in MKI_PRIMITIVES]
        if invalid:
            raise RuntimeExecutionError(
                "InvalidMKIPrimitive",
                f"KernelPlan contains non-MKI operation(s): {invalid!r}.",
                stage="PREPARE",
            )
        if not kernel_plan.get("revalidation_required", False):
            raise RuntimeExecutionError(
                "RevalidationRequired",
                "Executable plans must require COMMIT-boundary revalidation.",
                stage="PREPARE",
            )

        provenance = report.get("provenance", {})
        source_world_revision = provenance.get("source_world_revision")
        if not isinstance(source_world_revision, str):
            raise RuntimeExecutionError(
                "SourceWorldRevisionMissing",
                "Evaluator provenance must bind the plan to a source world revision.",
                stage="PREPARE",
            )

        required_profile = kernel_plan.get("runtime_profile")
        if required_profile != self.runtime_profile:
            raise RuntimeExecutionError(
                "RuntimeProfileMismatch",
                "Prepared plan runtime profile is incompatible with this sandbox runtime.",
                stage="PREPARE",
            )

        energy_total = report.get("energy", {}).get("total", {})
        reservations: list[dict[str, Any]] = []
        if energy_total.get("kind") == "Exact" and isinstance(
            energy_total.get("value"), (int, float)
        ):
            reservations.append(
                {
                    "reservation_id": (
                        "reservation:wb-canon-001:energy"
                        if kernel_plan.get("source_plan_id") == "wb:plan:transfer-reconfigure"
                        else f"reservation:{kernel_plan.get('source_plan_id')}:energy"
                    ),
                    "kind": "EnergyBudget",
                    "amount_j": float(energy_total["value"]),
                    "status": "Prepared",
                }
            )

        return PreparedPlan(
            plan_id=str(kernel_plan.get("source_plan_id")),
            operations=operations,
            typed_mir=copy.deepcopy(typed_mir),
            kernel_plan=copy.deepcopy(kernel_plan),
            assumptions=tuple(copy.deepcopy(report.get("assumptions", []))),
            resource_reservations=tuple(reservations),
            source_world_revision=source_world_revision,
            world_index_revision=provenance.get("world_index_revision"),
            capability_ids=tuple(kernel_plan.get("capability_ids", ())),
            lease_ids=tuple(kernel_plan.get("lease_ids", ())),
            accounting_evidence_ids=tuple(kernel_plan.get("accounting_evidence_ids", ())),
            resolution_evidence_ids=tuple(kernel_plan.get("resolution_evidence_ids", ())),
            runtime_profile=copy.deepcopy(required_profile),
            report_status=str(report.get("status")),
        )

    def revalidate(self, prepared: PreparedPlan, world: SandboxWorld) -> dict[str, Any]:
        """Revalidate current authoritative evidence immediately before COMMIT."""

        if world.commit_fenced or world.stop_state != "Running":
            raise RuntimeExecutionError(
                "EmergencyStopFence",
                "Sandbox stop fence forbids COMMIT.",
                stage="Revalidate",
            )
        if world.revision != prepared.source_world_revision:
            raise RuntimeExecutionError(
                "StaleReference",
                f"Prepared world revision {prepared.source_world_revision!r} is stale; current is {world.revision!r}.",
                stage="Revalidate",
            )
        if prepared.runtime_profile != self.runtime_profile:
            raise RuntimeExecutionError(
                "RuntimeProfileMismatch",
                "Runtime profile changed after PREPARE.",
                stage="Revalidate",
            )
        if world.runtime_state.get("runtime_profile") != self.runtime_profile:
            raise RuntimeExecutionError(
                "RuntimeProfileMismatch",
                "Authoritative runtime state no longer matches the prepared profile.",
                stage="Revalidate",
            )

        for evidence_id in prepared.resolution_evidence_ids:
            if evidence_id.startswith("state-revision:") and not any(
                entity.get("state_revision") == evidence_id
                for entity in world.entities.values()
            ):
                raise RuntimeExecutionError(
                    "StaleReference",
                    f"Required state revision evidence {evidence_id!r} is no longer authoritative.",
                    stage="Revalidate",
                )

        for capability_id in prepared.capability_ids:
            capability = world.capabilities.get(capability_id)
            if not capability or not capability.get("active"):
                raise RuntimeExecutionError(
                    "AuthorityError",
                    f"Capability {capability_id!r} is absent or inactive at COMMIT.",
                    stage="Revalidate",
                )

        for lease_id in prepared.lease_ids:
            lease = world.leases.get(lease_id)
            if not lease or not lease.get("active"):
                raise RuntimeExecutionError(
                    "AuthorityError",
                    f"Lease {lease_id!r} is absent or inactive at COMMIT.",
                    stage="Revalidate",
                )

        for ledger_id in prepared.accounting_evidence_ids:
            ledger = world.ledgers.get(ledger_id)
            if not ledger or not ledger.get("active"):
                raise RuntimeExecutionError(
                    "ConservationProofFailure",
                    f"Accounting evidence {ledger_id!r} is absent or inactive at COMMIT.",
                    stage="Revalidate",
                )

        return {
            "stage": "Revalidate",
            "status": "Pass",
            "evidence_ids": [
                *prepared.resolution_evidence_ids,
                *prepared.capability_ids,
                *prepared.lease_ids,
                *prepared.accounting_evidence_ids,
            ],
        }

    def commit(self, prepared: PreparedPlan, world: SandboxWorld) -> dict[str, Any]:
        """Atomically apply the supported sandbox effect after fresh revalidation."""

        before = world.clone()
        revalidation = self.revalidate(prepared, world)
        try:
            world.process_state = {
                "process_id": (
                    "process:wb-canon-001"
                    if prepared.plan_id == "wb:plan:transfer-reconfigure"
                    else f"process:{prepared.plan_id}"
                ),
                "status": "Committing",
                "prepared_plan_id": prepared.plan_id,
            }
            world.runtime_state["scheduler_phase"] = "Commit"
            world.runtime_state["tick"] = CANONICAL_TICK
            world.runtime_state["reservations"] = {
                item["reservation_id"]: copy.deepcopy(item)
                for item in prepared.resource_reservations
            }
            execution = self._execute_supported_plan(prepared, world)
            world.runtime_state["reservations"] = {}
            world.runtime_state["scheduler_phase"] = "Dispatch"
            world.process_state["status"] = "Committed"
        except Exception:
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
            raise

        tick_stamp = {
            "epoch": CANONICAL_EPOCH,
            "tick": CANONICAL_TICK,
            "phase": "Commit",
            "ordinal": 0,
        }
        commit_record = {
            "stage": "COMMIT",
            "status": "Committed",
            "effective_at": CANONICAL_EFFECTIVE_AT,
            "committed_at": CANONICAL_COMMITTED_AT,
            "tick_stamp": tick_stamp,
        }
        trace = {
            "runtime_profile": copy.deepcopy(self.runtime_profile),
            "physical_time_is_runtime_tick": False,
            "prepare_status": "Prepared",
            "reservations": [copy.deepcopy(item) for item in prepared.resource_reservations],
            "revalidation": revalidation,
            "commit": commit_record,
            "operations": execution["operations"],
            "world_effect": execution["world_effect"],
            "history": copy.deepcopy(world.history),
            "configuration": world.configuration(),
            "result_state_hash": _stable_hash(world.configuration()),
        }
        return trace

    def execute(self, report: dict[str, Any], world: SandboxWorld) -> dict[str, Any]:
        """Convenience path: PREPARE → Revalidate → COMMIT."""

        prepared = self.prepare(report, world)
        return self.commit(prepared, world)

    def request_emergency_stop(self, world: SandboxWorld, *, reason: str) -> dict[str, Any]:
        """Fence new PREPARE/COMMIT work in the supported single-process sandbox."""

        previous = world.stop_state
        world.stop_state = "Fenced"
        world.commit_fenced = True
        world.runtime_state["scheduler_phase"] = "Quiescing"
        return {
            "previous_state": previous,
            "state": "Fenced",
            "reason": reason,
            "new_commits_allowed": False,
        }

    def replay(
        self,
        report: dict[str, Any],
        initial_world: SandboxWorld,
        expected_trace: dict[str, Any],
    ) -> dict[str, Any]:
        """Replay in a separate cloned world and detect deterministic divergence."""

        replay_world = initial_world.clone()
        observed = self.execute(report, replay_world)
        expected_hash = expected_trace.get("result_state_hash")
        observed_hash = observed.get("result_state_hash")
        return {
            "status": "Match" if expected_hash == observed_hash else "Diverged",
            "expected_state_hash": expected_hash,
            "observed_state_hash": observed_hash,
            "same_world_object": replay_world is initial_world,
            "trace": observed,
        }

    def _execute_supported_plan(
        self,
        prepared: PreparedPlan,
        world: SandboxWorld,
    ) -> dict[str, Any]:
        if prepared.plan_id != "wb:plan:transfer-reconfigure":
            raise RuntimeExecutionError(
                "UnsupportedRuntimeSubset",
                f"Reference runtime does not implement plan {prepared.plan_id!r}.",
                stage="COMMIT",
            )
        constraints = prepared.typed_mir.get("typed_constraints", {})
        mass = constraints.get("mass", {}).get("value")
        radius = constraints.get("radius", {}).get("value")
        distance = constraints.get("distance", {}).get("value")
        acceleration = constraints.get("acceleration", {}).get("value")
        initial_velocity = constraints.get("initial_velocity", {}).get("value")
        trajectory = constraints.get("trajectory")
        if mass != 50 or radius != 0.01 or distance != 3 or acceleration != 50:
            raise RuntimeExecutionError(
                "SourceSemanticDrift",
                "Canonical runtime refuses to rewrite explicit water-ball constraints.",
                stage="COMMIT",
            )

        source = world.entities.get("entity:source-water")
        if not source or source.get("mass_kg", 0) < mass:
            raise RuntimeExecutionError(
                "ConservationProofFailure",
                "Source water inventory cannot account for the requested payload.",
                stage="COMMIT",
            )

        source["mass_kg"] -= float(mass)
        source["state_revision"] = "state-revision:source-water@world:992"
        ledger = world.ledgers["ledger:matter-energy"]

        entity_id = "entity:water-ball:wb-canon-001"
        world.entities[entity_id] = {
            "entity_id": entity_id,
            "state_revision": "state-revision:water-ball@world:992",
            "kind": "MatterEntity",
            "material": constraints.get("material"),
            "mass_kg": float(mass),
            "radius_m": float(radius),
            "relative_distance_m": float(distance),
            "initial_velocity_m_s": float(initial_velocity),
            "acceleration_m_s2": float(acceleration),
            "trajectory": trajectory,
            "terminal_binding": copy.deepcopy(prepared.assumptions),
        }
        ledger["allocations_kg"] = {
            "entity:source-water": float(source["mass_kg"]),
            entity_id: float(mass),
        }
        if sum(ledger["allocations_kg"].values()) != ledger["accounted_mass_kg"]:
            raise RuntimeExecutionError(
                "ConservationProofFailure",
                "Committed matter allocations do not match the accounted ledger total.",
                stage="COMMIT",
            )

        channel = world.runtime_state["channels"]["channel:matter:source-water"]
        channel["open"] = True
        channel["payload_entity_id"] = entity_id

        if "CONSTRAIN" in prepared.operations:
            world.controllers["controller:wb-canon-001"] = {
                "entity_id": entity_id,
                "mode": "horizontal-trajectory",
                "active": True,
                "gravity_removed": False,
            }

        world.revision = "world:992"
        event = {
            "event_id": "event:wb-canon-001",
            "effect_kind": "MatterTransferAndReconfiguration",
            "source_world_revision": "world:991",
            "result_world_revision": "world:992",
            "entity_identity_policy": "NewEntityFromAccountedMatter",
            "effective_at": CANONICAL_EFFECTIVE_AT,
            "committed_at": CANONICAL_COMMITTED_AT,
        }
        world.history.append(event)

        return {
            "operations": [
                {
                    "operation": operation,
                    "ordinal": index,
                    "status": "Committed",
                }
                for index, operation in enumerate(prepared.operations)
            ],
            "world_effect": {
                "source_world_revision": "world:991",
                "result_world_revision": "world:992",
                "history_event_id": "event:wb-canon-001",
                "effect_kind": "MatterTransferAndReconfiguration",
                "entity_identity_policy": "NewEntityFromAccountedMatter",
            },
        }
