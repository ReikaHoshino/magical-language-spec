"""Profile-governed scheduler/admission layer for the v0.9 sandbox runtime."""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from .integrator import SyntheticReferenceIntegrator
from .sandbox import (
    CANONICAL_COMMITTED_AT,
    CANONICAL_EFFECTIVE_AT,
    CANONICAL_EPOCH,
    CANONICAL_TICK,
    RuntimeExecutionError,
    SandboxRuntime,
    SandboxWorld,
)
from .schema import RuntimeSchemaValidationError, validate_execution_trace

SCHEDULER_PHASES = (
    "Ingress",
    "ContinuousAdvance",
    "Revalidate",
    "Commit",
    "PublishSnapshot",
    "Control",
    "IndexUpdate",
    "Dispatch",
)


@dataclass(frozen=True)
class SandboxProfile:
    """Minimum enforceable v0.9 sandbox policy for the reference subset."""

    profile_id: str = "sandbox-profile:reference-v09"
    revision: str = "1"
    max_energy_j: float = 500.0
    max_events_per_commit: int = 16
    max_microsteps_per_tick: int = 64
    max_concurrency: int = 1
    allow_external_interaction: bool = False

    def as_record(self) -> dict[str, Any]:
        return {
            "artifact_id": self.profile_id,
            "revision": self.revision,
            "runtime_limits": {
                "max_energy_j": self.max_energy_j,
                "max_events_per_commit": self.max_events_per_commit,
                "max_microsteps_per_tick": self.max_microsteps_per_tick,
                "max_concurrency": self.max_concurrency,
            },
            "external_interaction": {
                "allowed": self.allow_external_interaction,
            },
        }


class ReferenceRuntimeEngine:
    """Deterministic scheduler + sandbox admission over the low-level runtime."""

    def __init__(
        self,
        *,
        sandbox_profile: SandboxProfile | None = None,
        runtime: SandboxRuntime | None = None,
        integrator: SyntheticReferenceIntegrator | None = None,
    ) -> None:
        self.sandbox_profile = sandbox_profile or SandboxProfile()
        self.runtime = runtime or SandboxRuntime()
        self.integrator = integrator or SyntheticReferenceIntegrator()

    def admit(self, report: dict[str, Any]) -> dict[str, Any]:
        """Enforce stage-local sandbox ceilings without granting authority."""

        energy_total = report.get("energy", {}).get("total", {})
        if energy_total.get("kind") != "Exact":
            raise RuntimeExecutionError(
                "SandboxBudgetIndeterminate",
                "Runtime Energy ceiling cannot be proven from a non-Exact estimate.",
                stage="PREPARE",
            )
        value = energy_total.get("value")
        if not isinstance(value, (int, float)):
            raise RuntimeExecutionError(
                "SandboxBudgetIndeterminate",
                "Runtime Energy estimate is missing a numeric value.",
                stage="PREPARE",
            )
        if float(value) > self.sandbox_profile.max_energy_j:
            raise RuntimeExecutionError(
                "SandboxLimitExceeded",
                f"Estimated Energy {value} J exceeds sandbox ceiling {self.sandbox_profile.max_energy_j} J.",
                stage="PREPARE",
            )

        kernel_plan = report.get("interpretations", {}).get("kernel_plan", {})
        operations = kernel_plan.get("operations", [])
        if len(operations) > self.sandbox_profile.max_microsteps_per_tick:
            raise RuntimeExecutionError(
                "MicrostepBudgetExceeded",
                "KernelPlan operation count exceeds the sandbox microstep ceiling.",
                stage="PREPARE",
            )
        if self.sandbox_profile.max_events_per_commit < 1:
            raise RuntimeExecutionError(
                "EventBudgetExceeded",
                "Sandbox profile admits no commit event for this execution.",
                stage="PREPARE",
            )
        if self.sandbox_profile.max_concurrency < 1:
            raise RuntimeExecutionError(
                "ConcurrencyBudgetExceeded",
                "Sandbox profile admits no executable process.",
                stage="PREPARE",
            )

        return {
            "status": "Admitted",
            "sandbox_profile": self.sandbox_profile.as_record(),
            "estimated_energy_j": float(value),
            "planned_microsteps": len(operations),
            "planned_events": 1,
        }

    def execute_strict(self, report: dict[str, Any], world: SandboxWorld) -> dict[str, Any]:
        """Execute one admitted plan and return a validated scheduler/replay artifact."""

        source_world_revision = world.revision
        admission = self.admit(report)
        prepared = self.runtime.prepare(report, world)
        reservation_ids = [
            item["reservation_id"] for item in prepared.resource_reservations
        ]
        acquire_evidence = [
            *prepared.capability_ids,
            *prepared.lease_ids,
            *reservation_ids,
        ]
        integration_report = self.integrator.advance(
            CANONICAL_EFFECTIVE_AT,
            CANONICAL_EFFECTIVE_AT,
        )
        low_level_trace = self.runtime.commit(prepared, world)

        trace = {
            "document_kind": "SandboxExecutionTrace",
            "schema_version": "1",
            "status": "Committed",
            "runtime_profile": copy.deepcopy(self.runtime.runtime_profile),
            "sandbox_profile": self.sandbox_profile.as_record(),
            "source_world_revision": source_world_revision,
            "world_revision": world.revision,
            "admission": admission,
            "control_plane": [
                {
                    "operation": "ACQUIRE",
                    "status": "Acquired",
                    "evidence_ids": acquire_evidence,
                },
                {
                    "operation": "COMMIT",
                    "status": "Committed",
                    "evidence_ids": low_level_trace["revalidation"]["evidence_ids"],
                },
                {
                    "operation": "RELEASE",
                    "status": "Released",
                    "evidence_ids": reservation_ids,
                },
            ],
            "scheduler": self._scheduler_trace(low_level_trace, integration_report),
            "runtime": low_level_trace,
            "history_event_ids": [event["event_id"] for event in world.history],
            "result_state_hash": low_level_trace["result_state_hash"],
        }
        validate_execution_trace(trace)
        return trace

    def execute(self, report: dict[str, Any], world: SandboxWorld) -> dict[str, Any]:
        """Fail-closed execution surface that records and validates ABORT."""

        source_world_revision = world.revision
        before_history = copy.deepcopy(world.history)
        try:
            return self.execute_strict(report, world)
        except RuntimeExecutionError as error:
            trace = {
                "document_kind": "SandboxExecutionTrace",
                "schema_version": "1",
                "status": "Aborted",
                "runtime_profile": copy.deepcopy(self.runtime.runtime_profile),
                "sandbox_profile": self.sandbox_profile.as_record(),
                "source_world_revision": source_world_revision,
                "world_revision": world.revision,
                "abort": {
                    "stage": "ABORT",
                    "cause_stage": error.stage,
                    "code": error.code,
                    "message": error.message,
                    **({"internal_cause": error.internal_cause} if error.internal_cause is not None else {}),
                    **({"internal_trace": copy.deepcopy(error.internal_trace)} if error.internal_trace is not None else {}),
                },
                "control_plane": [
                    {
                        "operation": "ABORT",
                        "status": "Aborted",
                        "reason": error.code,
                    }
                ],
                "world_revision_unchanged": world.revision == source_world_revision,
                "history_unchanged": world.history == before_history,
            }
            validate_execution_trace(trace)
            return trace

    def replay(
        self,
        report: dict[str, Any],
        initial_world: SandboxWorld,
        expected_execution: dict[str, Any],
    ) -> dict[str, Any]:
        """Re-execute in isolation, enforcing trace/profile compatibility first."""

        try:
            validate_execution_trace(expected_execution)
        except RuntimeSchemaValidationError as error:
            return {
                "status": "Incompatible",
                "diagnostic": "ReplayTraceInvalid",
                "errors": list(error.errors),
            }

        if expected_execution.get("status") != "Committed":
            return {
                "status": "Incompatible",
                "diagnostic": "ReplayRequiresCommittedTrace",
            }
        if expected_execution.get("runtime_profile") != self.runtime.runtime_profile:
            return {
                "status": "Incompatible",
                "diagnostic": "RuntimeProfileMismatch",
            }
        if expected_execution.get("sandbox_profile") != self.sandbox_profile.as_record():
            return {
                "status": "Incompatible",
                "diagnostic": "SandboxProfileMismatch",
            }
        integration = expected_execution.get("scheduler", {}).get("integration_report", {})
        if integration.get("integrator") != self.integrator.identity:
            return {
                "status": "Incompatible",
                "diagnostic": "IntegratorProfileMismatch",
            }

        replay_world = initial_world.clone()
        observed = self.execute_strict(report, replay_world)
        expected_hash = expected_execution.get("result_state_hash")
        observed_hash = observed.get("result_state_hash")
        return {
            "status": "Match" if expected_hash == observed_hash else "Diverged",
            "manifest": {
                "runtime_profile": copy.deepcopy(self.runtime.runtime_profile),
                "sandbox_profile": self.sandbox_profile.as_record(),
                "integrator": dict(self.integrator.identity),
                "physical_time_is_runtime_tick": False,
                "replay_is_rewind": False,
            },
            "expected_state_hash": expected_hash,
            "observed_state_hash": observed_hash,
            "trace": observed,
        }

    @staticmethod
    def _scheduler_trace(
        low_level_trace: dict[str, Any],
        integration_report: dict[str, Any],
    ) -> dict[str, Any]:
        records: list[dict[str, Any]] = []
        for ordinal, phase in enumerate(SCHEDULER_PHASES):
            record: dict[str, Any] = {
                "epoch": CANONICAL_EPOCH,
                "tick": CANONICAL_TICK,
                "phase": phase,
                "ordinal": ordinal,
            }
            if phase == "ContinuousAdvance":
                record["interval"] = {
                    "start": CANONICAL_EFFECTIVE_AT,
                    "end": CANONICAL_EFFECTIVE_AT,
                }
                record["status"] = integration_report["status"]
            elif phase == "Revalidate":
                record["status"] = low_level_trace["revalidation"]["status"]
            elif phase == "Commit":
                record["effective_at"] = low_level_trace["commit"]["effective_at"]
                record["committed_at"] = low_level_trace["commit"]["committed_at"]
            elif phase == "PublishSnapshot":
                record["world_revision"] = low_level_trace["world_effect"][
                    "result_world_revision"
                ]
            elif phase == "Control":
                record["controller_registered"] = any(
                    operation["operation"] == "CONSTRAIN"
                    for operation in low_level_trace["operations"]
                )
            elif phase == "IndexUpdate":
                record["source_world_revision"] = low_level_trace["world_effect"][
                    "source_world_revision"
                ]
                record["result_world_revision"] = low_level_trace["world_effect"][
                    "result_world_revision"
                ]
            elif phase == "Dispatch":
                record["history_event_id"] = low_level_trace["world_effect"][
                    "history_event_id"
                ]
            records.append(record)

        return {
            "physical_time_is_runtime_tick": False,
            "phase_order": list(SCHEDULER_PHASES),
            "integration_report": copy.deepcopy(integration_report),
            "records": records,
        }
