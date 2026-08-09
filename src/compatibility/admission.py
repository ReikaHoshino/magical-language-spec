from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping


class AdmissionStatus(str, Enum):
    ALLOWED = "Allowed"
    DENIED = "Denied"
    INDETERMINATE = "Indeterminate"


class CompatibilityAdmissionError(ValueError):
    """Raised when compatibility decision envelopes cannot be aggregated safely."""


@dataclass(frozen=True)
class CompatibilityAdmissionResult:
    status: AdmissionStatus
    required_domains: tuple[str, ...]
    decision_ids: tuple[str, ...]
    blocking_domains: tuple[str, ...]
    reason_codes: tuple[str, ...]

    @property
    def admitted(self) -> bool:
        return self.status is AdmissionStatus.ALLOWED

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "admitted": self.admitted,
            "required_domains": list(self.required_domains),
            "decision_ids": list(self.decision_ids),
            "blocking_domains": list(self.blocking_domains),
            "reason_codes": list(self.reason_codes),
        }


def _decision_domain(decision: Mapping[str, Any]) -> str:
    try:
        domain = decision["profile"]["domain"]
    except (KeyError, TypeError) as exc:
        raise CompatibilityAdmissionError("decision is missing profile.domain") from exc
    if not isinstance(domain, str) or not domain:
        raise CompatibilityAdmissionError("decision profile.domain must be a non-empty string")
    return domain


def _decision_id(decision: Mapping[str, Any]) -> str:
    value = decision.get("decision_id")
    if not isinstance(value, str) or not value:
        raise CompatibilityAdmissionError("decision_id must be a non-empty string")
    return value


def _decision_result(decision: Mapping[str, Any]) -> tuple[str, str]:
    try:
        result = decision["result"]
        status = result["status"]
        reason_code = result["reason_code"]
    except (KeyError, TypeError) as exc:
        raise CompatibilityAdmissionError(
            "decision is missing result.status or result.reason_code"
        ) from exc
    if status not in {"Compatible", "Incompatible", "Undetermined"}:
        raise CompatibilityAdmissionError(f"unsupported compatibility status: {status!r}")
    if not isinstance(reason_code, str) or not reason_code:
        raise CompatibilityAdmissionError("result.reason_code must be a non-empty string")
    return status, reason_code


def admit_compatibility_decisions(
    decisions: Iterable[Mapping[str, Any]],
    *,
    required_domains: Iterable[str],
) -> CompatibilityAdmissionResult:
    """Aggregate profile-owned compatibility decisions for a fail-closed consumer.

    This function does not compare versions, revisions, hashes, language tags,
    registry contracts, or fingerprint payloads. Those decisions must already
    have been produced by the owning compatibility profile. The aggregate gate
    admits only when every required domain has exactly one `Compatible`
    decision.

    Missing or `Undetermined` evidence is therefore not treated as compatible.
    Profile-specific negotiation/fallback, if any, must happen before this gate
    and produce the resulting domain decision explicitly.
    """

    required = tuple(required_domains)
    if not required:
        raise CompatibilityAdmissionError("required_domains must not be empty")
    if any(not isinstance(domain, str) or not domain for domain in required):
        raise CompatibilityAdmissionError("required_domains must contain non-empty strings")
    if len(set(required)) != len(required):
        raise CompatibilityAdmissionError("required_domains contains duplicates")

    by_domain: dict[str, Mapping[str, Any]] = {}
    for decision in decisions:
        domain = _decision_domain(decision)
        _decision_id(decision)
        _decision_result(decision)
        if domain in by_domain:
            raise CompatibilityAdmissionError(
                f"multiple compatibility decisions provided for required aggregation domain {domain}"
            )
        by_domain[domain] = decision

    decision_ids: list[str] = []
    blocking_domains: list[str] = []
    reason_codes: list[str] = []
    saw_incompatible = False
    saw_indeterminate = False

    for domain in required:
        decision = by_domain.get(domain)
        if decision is None:
            blocking_domains.append(domain)
            reason_codes.append(f"CompatibilityDecisionMissing:{domain}")
            saw_indeterminate = True
            continue

        decision_ids.append(_decision_id(decision))
        status, reason_code = _decision_result(decision)
        if status == "Incompatible":
            blocking_domains.append(domain)
            reason_codes.append(reason_code)
            saw_incompatible = True
        elif status == "Undetermined":
            blocking_domains.append(domain)
            reason_codes.append(reason_code)
            saw_indeterminate = True

    if saw_incompatible:
        status = AdmissionStatus.DENIED
    elif saw_indeterminate:
        status = AdmissionStatus.INDETERMINATE
    else:
        status = AdmissionStatus.ALLOWED

    return CompatibilityAdmissionResult(
        status=status,
        required_domains=required,
        decision_ids=tuple(decision_ids),
        blocking_domains=tuple(blocking_domains),
        reason_codes=tuple(reason_codes),
    )
