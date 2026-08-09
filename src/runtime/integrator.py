"""Deterministic synthetic integrator boundary for the v0.9 reference runtime."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from .sandbox import RuntimeExecutionError


def _instant(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


class SyntheticReferenceIntegrator:
    """A bounded reference integrator; it never invents missing physical models."""

    identity = {"artifact_id": "integrator:synthetic-reference", "revision": "1"}

    def advance(
        self,
        start: str,
        end: str,
        *,
        continuous_processes: Iterable[dict[str, Any]] = (),
    ) -> dict[str, Any]:
        start_time = _instant(start)
        end_time = _instant(end)
        if end_time < start_time:
            raise RuntimeExecutionError(
                "InvalidTickInterval",
                "ContinuousAdvance end precedes start.",
                stage="ContinuousAdvance",
            )

        processes = list(continuous_processes)
        duration_seconds = (end_time - start_time).total_seconds()
        if duration_seconds == 0:
            return {
                "integrator": dict(self.identity),
                "status": "NoAdvanceRequired",
                "start": start,
                "end": end,
                "duration_seconds": 0.0,
                "steps": 0,
                "process_count": len(processes),
                "physical_law_modified": False,
            }

        if processes:
            raise RuntimeExecutionError(
                "IntegratorModelUnavailable",
                "The v0.9 synthetic integrator has no model for non-zero continuous processes.",
                stage="ContinuousAdvance",
            )

        return {
            "integrator": dict(self.identity),
            "status": "AdvancedNoProcesses",
            "start": start,
            "end": end,
            "duration_seconds": duration_seconds,
            "steps": 1,
            "process_count": 0,
            "physical_law_modified": False,
        }
