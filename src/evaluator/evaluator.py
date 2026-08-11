"""Public v0.8 evaluator facade.

The core pipeline owns stage construction. This facade owns public release
metadata and final report-level classification so missing estimator evidence
remains Indeterminate rather than being misreported as a violated
physical/control obligation.
"""
from __future__ import annotations

from typing import Any

from .core import LocalEvaluator as _CoreLocalEvaluator
from .schema import validate_feasibility_report

PUBLIC_SPEC_VERSION = "1.0.0-rc.1"


def _report_status(assessments: list[dict[str, Any]]) -> str:
    statuses = {assessment["status"] for assessment in assessments}
    if "Fail" in statuses:
        return "Infeasible"
    if "Unknown" in statuses:
        return "Indeterminate"
    if "Conditional" in statuses:
        return "ConditionallyFeasible"
    return "Feasible"


class LocalEvaluator(_CoreLocalEvaluator):
    """Public evaluator with fail-closed report classification semantics."""

    def _finalize(self, report: dict[str, Any]) -> dict[str, Any]:
        report["spec_version"] = PUBLIC_SPEC_VERSION

        energy_total = report.get("energy", {}).get("total", {})
        kernel_plan = report.get("interpretations", {}).get("kernel_plan", {})
        constrain_present = "CONSTRAIN" in kernel_plan.get("operations", [])

        if energy_total.get("kind") == "Unknown" and constrain_present:
            for assessment in report.get("assessments", []):
                if (
                    assessment.get("dimension") == "trajectory_control"
                    and assessment.get("status") == "Fail"
                ):
                    assessment["status"] = "Unknown"
                    assessment["summary"] = (
                        "Horizontal trajectory lowers to CONSTRAIN, but the required "
                        "control-Energy estimator evidence is unavailable. This is "
                        "Indeterminate, not proof that the control obligation failed."
                    )
            if report.get("assessments"):
                report["status"] = _report_status(report["assessments"])

        validate_feasibility_report(report)
        return report


_DEFAULT: LocalEvaluator | None = None


def default_evaluator() -> LocalEvaluator:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = LocalEvaluator()
    return _DEFAULT


def evaluate_latin_source(
    source: str | bytes,
    *,
    ambiguity_policy: str = "StrictReject",
) -> dict[str, Any]:
    return default_evaluator().evaluate_latin_source(
        source,
        ambiguity_policy=ambiguity_policy,
    )


def evaluate_nsr(nsr: Any) -> dict[str, Any]:
    return default_evaluator().evaluate_nsr(nsr)


def evaluate_nsr_json(payload: str | bytes) -> dict[str, Any]:
    return default_evaluator().evaluate_nsr_json(payload)
