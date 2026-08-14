"""Deterministic public Issue #23 execution-admission reference cases.

This module demonstrates the normative boundary between mandatory local
admission and explicitly requested whole-plan preflight.  Its dictionaries are
implementation-owned fixture inputs, not a stable serialized ECIR.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any


SUPPORTED_MKI = {
    "RESOLVE",
    "OBSERVE",
    "CHANNEL",
    "TRANSFER",
    "RECONFIGURE",
    "CONSTRAIN",
}
MANDATORY_LOCAL_GUARDS = {
    "Type",
    "Identity",
    "Capability",
    "Lease",
    "Conservation",
    "Accounting",
    "RuntimeSafety",
}


class ExecutionAdmissionError(RuntimeError):
    """Fail-closed error for unsupported fixture contracts."""


@dataclass
class AdmissionWorld:
    """Small authoritative world used by the paired semantic cases."""

    world_revision: str
    source_mass_kg: float
    destination_mass_kg: float
    constraint_active: bool
    gravity_applies: bool
    capability_active: bool
    lease_active: bool
    accounted_total_mass_kg: float
    history_event_ids: list[str]

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "AdmissionWorld":
        return cls(
            world_revision=str(record["world_revision"]),
            source_mass_kg=float(record["source_mass_kg"]),
            destination_mass_kg=float(record["destination_mass_kg"]),
            constraint_active=bool(record["constraint_active"]),
            gravity_applies=bool(record["gravity_applies"]),
            capability_active=bool(record["capability_active"]),
            lease_active=bool(record["lease_active"]),
            accounted_total_mass_kg=float(record["accounted_total_mass_kg"]),
            history_event_ids=[],
        )

    def clone(self) -> "AdmissionWorld":
        return copy.deepcopy(self)

    def record(self) -> dict[str, Any]:
        return {
            "world_revision": self.world_revision,
            "source_mass_kg": self.source_mass_kg,
            "destination_mass_kg": self.destination_mass_kg,
            "constraint_active": self.constraint_active,
            "gravity_applies": self.gravity_applies,
            "capability_active": self.capability_active,
            "lease_active": self.lease_active,
            "accounted_total_mass_kg": self.accounted_total_mass_kg,
        }


class ExecutionAdmissionRuntime:
    """Execute the paired bounded plan without weakening local guards."""

    def execute(self, case: dict[str, Any]) -> dict[str, Any]:
        self._validate_contract(case)
        policy = case["policy"]
        plan = case["plan"]
        world = AdmissionWorld.from_record(case["initial_world"])

        if policy["mode"] == "WholePlanPreflight":
            failure = self._whole_plan_preflight(plan, world)
            if failure is not None:
                failed_group, failed_guard = failure
                return self._trace(
                    status="Rejected",
                    code="WholePlanPreflightRejected",
                    phase="BeforeFirstEffect",
                    failed_group_id=failed_group,
                    failed_guard=failed_guard,
                    committed_group_ids=[],
                    world=world,
                )

        committed: list[str] = []
        for group in plan["atomic_groups"]:
            failure = self._local_admission_failure(group, world)
            if failure is not None:
                if committed:
                    self._terminate_constraint(world)
                    return self._trace(
                        status="PartialCommitTerminated",
                        code="ContinuationInfeasibleAfterPartialCommit",
                        phase="AfterPartialCommit",
                        failed_group_id=group["group_id"],
                        failed_guard=failure,
                        committed_group_ids=committed,
                        world=world,
                    )
                return self._trace(
                    status="Rejected",
                    code="LocalAdmissionRejected",
                    phase="BeforeFirstEffect",
                    failed_group_id=group["group_id"],
                    failed_guard=failure,
                    committed_group_ids=[],
                    world=world,
                )
            self._commit_atomic_group(group, world)
            committed.append(group["group_id"])

        raise ExecutionAdmissionError(
            "The bounded public Issue #23 reference case must exercise a failure boundary."
        )

    def replay(self, case: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
        """Replay from the same fixture; replay is comparison, not rewind."""

        observed = self.execute(copy.deepcopy(case))
        return {
            "status": "Match" if observed == expected else "Diverged",
            "replay_is_rewind": False,
            "observed_trace": observed,
        }

    def _validate_contract(self, case: dict[str, Any]) -> None:
        policy = case.get("policy", {})
        mode = policy.get("mode")
        if mode not in {"Incremental", "WholePlanPreflight"}:
            raise ExecutionAdmissionError(f"Unsupported execution admission mode: {mode!r}")
        definition_source = policy.get("definition_source")
        provenance_owner = policy.get("provenance", {}).get("owner")
        if definition_source not in {"SourceContract", "RuntimeProfile"}:
            raise ExecutionAdmissionError("Execution-admission DefinitionSource is missing.")
        if provenance_owner != definition_source:
            raise ExecutionAdmissionError(
                "Execution-admission provenance does not match its DefinitionSource."
            )
        if policy.get("source_explicit") and definition_source != "SourceContract":
            raise ExecutionAdmissionError(
                "A source-explicit policy must remain owned by SourceContract."
            )
        if mode == "WholePlanPreflight":
            scope = policy.get("assessment_scope")
            if not isinstance(scope, dict):
                raise ExecutionAdmissionError(
                    "WholePlanPreflight requires a recorded assessment scope."
                )
            if scope.get("source_world_revision") != case.get("initial_world", {}).get(
                "world_revision"
            ):
                raise ExecutionAdmissionError(
                    "WholePlanPreflight assessment scope is stale for the fixture world."
                )
            if any(
                scope.get(field) is not False
                for field in (
                    "creates_reservation",
                    "grants_authority",
                    "guarantees_runtime_completion",
                )
            ):
                raise ExecutionAdmissionError(
                    "WholePlanPreflight cannot reserve, grant authority, or guarantee completion."
                )
        groups = case.get("plan", {}).get("atomic_groups")
        if not isinstance(groups, list) or not groups:
            raise ExecutionAdmissionError("Execution plan has no atomic groups.")
        for group in groups:
            operations = set(group.get("mki_operations", []))
            if not operations or not operations <= SUPPORTED_MKI:
                raise ExecutionAdmissionError(
                    f"Unsupported MKI operation in {group.get('group_id')!r}."
                )
            guards = set(group.get("local_guards", []))
            if not MANDATORY_LOCAL_GUARDS <= guards:
                raise ExecutionAdmissionError(
                    f"Mandatory local guards are missing from {group.get('group_id')!r}."
                )
            if group.get("constraint_action") not in {
                "Activate",
                "Maintain",
                "Deactivate",
            }:
                raise ExecutionAdmissionError(
                    f"Unsupported constraint action in {group.get('group_id')!r}."
                )

    def _whole_plan_preflight(
        self, plan: dict[str, Any], world: AdmissionWorld
    ) -> tuple[str, str] | None:
        shadow = world.clone()
        for group in plan["atomic_groups"]:
            failure = self._local_admission_failure(group, shadow)
            if failure is not None:
                return str(group["group_id"]), failure
            self._apply_group(group, shadow, record_history=False)
        return None

    @staticmethod
    def _local_admission_failure(
        group: dict[str, Any], world: AdmissionWorld
    ) -> str | None:
        if not world.capability_active:
            return "Capability"
        if not world.lease_active:
            return "Lease"
        amount = group.get("transfer_mass_kg")
        if not isinstance(amount, (int, float)) or amount <= 0:
            return "Type"
        if float(amount) > world.source_mass_kg:
            return "Conservation"
        if abs(
            world.source_mass_kg
            + world.destination_mass_kg
            - world.accounted_total_mass_kg
        ) > 1e-9:
            return "Accounting"
        return None

    def _commit_atomic_group(
        self, group: dict[str, Any], world: AdmissionWorld
    ) -> None:
        before = world.clone()
        try:
            self._apply_group(group, world, record_history=True)
            self._assert_conservation(world)
        except Exception:
            world.__dict__.update(before.__dict__)
            raise

    @staticmethod
    def _apply_group(
        group: dict[str, Any], world: AdmissionWorld, *, record_history: bool
    ) -> None:
        amount = float(group["transfer_mass_kg"])
        world.source_mass_kg -= amount
        world.destination_mass_kg += amount
        action = group["constraint_action"]
        if action == "Activate":
            world.constraint_active = True
            world.gravity_applies = True
        elif action == "Deactivate":
            world.constraint_active = False
            world.gravity_applies = True
        if record_history:
            world.world_revision = ExecutionAdmissionRuntime._next_revision(
                world.world_revision
            )
            world.history_event_ids.append(
                f"event:admission:{group['group_id']}"
            )

    @staticmethod
    def _terminate_constraint(world: AdmissionWorld) -> None:
        if not world.constraint_active:
            return
        world.constraint_active = False
        world.gravity_applies = True
        world.world_revision = ExecutionAdmissionRuntime._next_revision(
            world.world_revision
        )
        world.history_event_ids.append("event:admission:constraint-terminated")

    @staticmethod
    def _assert_conservation(world: AdmissionWorld) -> None:
        observed = world.source_mass_kg + world.destination_mass_kg
        if abs(observed - world.accounted_total_mass_kg) > 1e-9:
            raise ExecutionAdmissionError("Matter accounting diverged during commit.")

    @staticmethod
    def _next_revision(revision: str) -> str:
        prefix, separator, suffix = revision.rpartition(":")
        if not separator or not suffix.isdigit():
            raise ExecutionAdmissionError(
                f"Fixture world revision is not incrementable: {revision!r}."
            )
        return f"{prefix}:{int(suffix) + 1}"

    @staticmethod
    def _trace(
        *,
        status: str,
        code: str,
        phase: str,
        failed_group_id: str,
        failed_guard: str,
        committed_group_ids: list[str],
        world: AdmissionWorld,
    ) -> dict[str, Any]:
        return {
            "status": status,
            "diagnostic": {
                "code": code,
                "phase": phase,
                "failed_group_id": failed_group_id,
                "failed_guard": failed_guard,
                "committed_group_count": len(committed_group_ids),
            },
            "committed_group_ids": list(committed_group_ids),
            "history_event_ids": list(world.history_event_ids),
            "final_world": world.record(),
            "prior_commits_rolled_back": False,
            "preflight_created_reservation": False,
            "preflight_granted_authority": False,
            "replay_expected": "Match",
        }
