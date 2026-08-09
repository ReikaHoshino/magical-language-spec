"""Deterministic human/machine formatting for FeasibilityReport."""
from __future__ import annotations

import json
from typing import Any

LEVELS = (
    "report",
    "surface",
    "nsr",
    "semantic-ast",
    "typed-mir",
    "kernel-plan",
    "all",
)
_STAGE_KEYS = {
    "surface": "surface",
    "nsr": "nsr",
    "semantic-ast": "semantic_ast",
    "typed-mir": "typed_mir",
    "kernel-plan": "kernel_plan",
}


def select_output(report: dict[str, Any], level: str) -> Any:
    if level not in LEVELS:
        raise ValueError(f"unsupported output level: {level}")
    if level in {"report", "all"}:
        return report
    return report.get("interpretations", {}).get(_STAGE_KEYS[level])


def format_json(report: dict[str, Any], *, level: str = "all") -> str:
    return json.dumps(
        select_output(report, level),
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )


def format_human(report: dict[str, Any], *, level: str = "report") -> str:
    if level not in LEVELS:
        raise ValueError(f"unsupported output level: {level}")
    if level not in {"report", "all"}:
        value = select_output(report, level)
        heading = level.replace("-", " ").title()
        return f"{heading}\n{'=' * len(heading)}\n{json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)}"

    lines = [
        "Magical Language Local Evaluator",
        "================================",
        f"Status: {report['status']}",
        f"Input: {report['input']['kind']}",
    ]
    provenance = report.get("provenance", {})
    fingerprint = provenance.get("semantic_fingerprint")
    if fingerprint:
        lines.append(f"SemanticFingerprint: {fingerprint}")
    energy = report.get("energy", {}).get("total")
    if isinstance(energy, dict):
        if energy.get("kind") == "Exact":
            lines.append(f"Energy: {energy.get('value')} {energy.get('unit')}")
        else:
            lines.append(f"Energy: {energy.get('kind')} ({energy.get('reason')})")

    lines.extend(["", "Assessments"])
    for assessment in report.get("assessments", []):
        lines.append(
            f"- {assessment['dimension']}: {assessment['status']} — "
            f"{assessment.get('summary') or ''}".rstrip()
        )

    diagnostics = report.get("diagnostics", [])
    if diagnostics:
        lines.extend(["", "Diagnostics"])
        for diagnostic in diagnostics:
            message = diagnostic.get("message") or ""
            lines.append(
                f"- [{diagnostic['severity']}] {diagnostic['stage']}/{diagnostic['code']}"
                + (f": {message}" if message else "")
            )

    assumptions = report.get("assumptions", [])
    if assumptions:
        lines.extend(["", "Planning assumptions"])
        for assumption in assumptions:
            lines.append(f"- {assumption['id']}: {assumption['statement']}")

    if level == "all":
        interpretations = report.get("interpretations", {})
        for label, key in (
            ("Surface", "surface"),
            ("NSR", "nsr"),
            ("SemanticAST", "semantic_ast"),
            ("TypedMIR", "typed_mir"),
            ("KernelPlan", "kernel_plan"),
        ):
            if key in interpretations:
                lines.extend(
                    [
                        "",
                        label,
                        "-" * len(label),
                        json.dumps(
                            interpretations[key],
                            indent=2,
                            sort_keys=True,
                            ensure_ascii=False,
                        ),
                    ]
                )
    return "\n".join(lines)
