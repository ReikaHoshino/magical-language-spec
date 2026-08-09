#!/usr/bin/env python3
"""Check the normative security contract and its diagnostic cross-reference."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "reference" / "security-sandbox.md"
ERRORS = ROOT / "reference" / "errors.md"
EXAMPLES = ROOT / "examples" / "security-stop-scenarios.md"

REQUIRED_INVARIANTS = {
    "Authority != identity",
    "Visibility != authority",
    "AI proposal != semantic truth",
    "Natural-language input != trusted executable data",
    "PREPARE/dry-run != COMMIT",
    "Sandbox allowance != Capability",
    "Emergency-stop requested != stopped",
    "Stopped != rolled back",
    "Replay/log input != authoritative world state",
}

REQUIRED_THREATS = {
    "prompt/spell injection",
    "type confusion",
    "self-declared EntityID/Capability/Lease",
    "poisoned, substituted, incompatible registry/profile",
    "CPU/memory/event/query/Energy exhaustion",
    "commit race",
    "forged event/state",
}

SECURITY_DIAGNOSTICS = {
    "InputLimitExceeded",
    "StructuredInputInvalid",
    "ExecutableDataInjection",
    "NormalizationBudgetExceeded",
    "ArtifactTrustFailure",
    "SandboxProfileUnavailable",
    "SandboxProfileMismatch",
    "SandboxPolicyDenied",
    "SandboxLimitExceeded",
    "EmergencyStopRequested",
    "EmergencyStopIncomplete",
    "CommitOutcomeIndeterminate",
    "ReplayInputRejected",
}


def require_all(text: str, values: set[str], source: Path) -> None:
    missing = sorted(value for value in values if value not in text)
    if missing:
        raise AssertionError(f"{source}: missing required contract text: {missing}")


def validate_contract() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    errors = ERRORS.read_text(encoding="utf-8")
    examples = EXAMPLES.read_text(encoding="utf-8")

    require_all(contract, REQUIRED_INVARIANTS, CONTRACT)
    require_all(contract, REQUIRED_THREATS, CONTRACT)
    require_all(contract, SECURITY_DIAGNOSTICS, CONTRACT)
    require_all(errors, SECURITY_DIAGNOSTICS, ERRORS)

    expected_header = (
        "| Asset | Trust boundary | Threat | Required mitigation | Diagnostic stage |"
    )
    if expected_header not in contract:
        raise AssertionError("normative threat table does not expose all required columns")

    for stage in (
        "`INGRESS`",
        "`NORMALIZE`",
        "`ELABORATE`",
        "`LOAD`",
        "`RESOLVE`",
        "`PREPARE`",
        "`REVALIDATE/COMMIT`",
        "`RUNTIME`",
        "`REPLAY`",
    ):
        if stage not in contract:
            raise AssertionError(f"trust-boundary pipeline is missing {stage}")

    require_all(
        examples,
        {
            "Natural-language spell injection",
            "Malicious structured NSR",
            "Poisoned registry/profile artifact",
            "Emergency stop racing COMMIT",
            "Forced worker termination",
            "Forged replay log",
        },
        EXAMPLES,
    )


def main() -> None:
    validate_contract()
    print(
        "validated security invariants, threat classes, stages, diagnostics, and examples"
    )


if __name__ == "__main__":
    main()
