"""Strict bounded JSON decoding for untrusted experimental artifacts."""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HostCeilings:
    """Immutable host policy; artifact-authored profiles cannot raise it."""

    max_file_bytes: int = 1_048_576
    max_json_depth: int = 64
    max_json_nodes: int = 50_000
    max_parameter_bytes: int = 131_072
    max_abs_number: float = 1_000_000_000_000_000.0
    max_energy_j: float = 1_000_000_000.0
    max_events_per_commit: int = 4_096
    max_microsteps_per_tick: int = 4_096
    max_concurrency: int = 64
    max_entities: int = 4_096
    max_history_records: int = 16_384


DEFAULT_HOST_CEILINGS = HostCeilings()


class ArtifactIngressError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def as_diagnostic(self) -> dict[str, str]:
        return {
            "stage": "INGRESS",
            "code": self.code,
            "severity": "fatal",
            "message": self.message,
        }


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ArtifactIngressError(
                "DuplicateJSONKey", f"Duplicate JSON object key {key!r}."
            )
        result[key] = value
    return result


def _measure(
    value: Any,
    depth: int = 0,
    *,
    ceilings: HostCeilings = DEFAULT_HOST_CEILINGS,
) -> tuple[int, int]:
    if depth > ceilings.max_json_depth:
        raise ArtifactIngressError(
            "ArtifactNestingLimitExceeded",
            f"Artifact nesting exceeds {ceilings.max_json_depth} levels.",
        )
    count = 1
    maximum = depth
    children = (
        value.values()
        if isinstance(value, dict)
        else value
        if isinstance(value, list)
        else ()
    )
    for child in children:
        child_count, child_depth = _measure(
            child, depth + 1, ceilings=ceilings
        )
        count += child_count
        maximum = max(maximum, child_depth)
        if count > ceilings.max_json_nodes:
            raise ArtifactIngressError(
                "ArtifactResourceLimitExceeded",
                f"Artifact exceeds {ceilings.max_json_nodes:,} JSON nodes.",
            )
    return count, maximum


def _reject_unsafe_numbers(
    value: Any, *, ceilings: HostCeilings = DEFAULT_HOST_CEILINGS
) -> None:
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ArtifactIngressError(
                "InvalidJSONNumber", "Non-finite JSON numbers are forbidden."
            )
        if abs(value) > ceilings.max_abs_number:
            raise ArtifactIngressError(
                "JSONNumberMagnitudeExceeded",
                "JSON number exceeds the host magnitude ceiling.",
            )
        return
    if isinstance(value, int):
        if abs(value) > int(ceilings.max_abs_number):
            raise ArtifactIngressError(
                "JSONNumberMagnitudeExceeded",
                "JSON integer exceeds the host magnitude ceiling.",
            )
        return
    if isinstance(value, dict):
        for child in value.values():
            _reject_unsafe_numbers(child, ceilings=ceilings)
    elif isinstance(value, list):
        for child in value:
            _reject_unsafe_numbers(child, ceilings=ceilings)


_RESOURCE_KEYS = {
    "external_path",
    "resource_path",
    "include",
    "path",
    "file",
    "uri",
    "url",
}
_EXECUTABLE_KEYS = {
    "module",
    "python_module",
    "class",
    "entry_point",
    "callable",
    "plugin",
}
_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def _reject_external_resources(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in _EXECUTABLE_KEYS:
                raise ArtifactIngressError(
                    "ExecutableResourceForbidden",
                    f"Artifact-owned executable selector {key!r} is forbidden.",
                )
            if key in _RESOURCE_KEYS and isinstance(child, str):
                normalized = child.replace("\\", "/")
                if (
                    normalized.startswith("/")
                    or normalized.startswith("//")
                    or ".." in normalized.split("/")
                    or _SCHEME.match(normalized)
                ):
                    raise ArtifactIngressError(
                        "ExternalResourceForbidden",
                        f"External resource reference in {key!r} is forbidden.",
                    )
            _reject_external_resources(child)
    elif isinstance(value, list):
        for child in value:
            _reject_external_resources(child)


def decode_artifact_bytes(
    payload: bytes,
    *,
    ceilings: HostCeilings = DEFAULT_HOST_CEILINGS,
) -> dict[str, Any]:
    """Decode exactly one immutable byte snapshot under artifact ceilings."""

    if not isinstance(payload, bytes):
        raise TypeError("artifact payload must be bytes")
    if len(payload) > ceilings.max_file_bytes:
        raise ArtifactIngressError(
            "ArtifactTooLarge",
            f"Artifact exceeds the {ceilings.max_file_bytes}-byte ingress limit.",
        )
    if payload.startswith(b"\xef\xbb\xbf"):
        raise ArtifactIngressError("InvalidUTF8", "UTF-8 BOM is not admitted.")
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ArtifactIngressError(
            "InvalidUTF8", "Artifact is not strict UTF-8."
        ) from error
    try:
        document = json.loads(
            text,
            object_pairs_hook=_object_pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ArtifactIngressError(
                    "InvalidJSONNumber",
                    f"Non-finite JSON number {value!r} is forbidden.",
                )
            ),
        )
    except ArtifactIngressError:
        raise
    except (json.JSONDecodeError, RecursionError) as error:
        raise ArtifactIngressError(
            "MalformedJSON", f"Malformed JSON: {error}"
        ) from error
    if not isinstance(document, dict):
        raise ArtifactIngressError(
            "ArtifactRootType", "Artifact root must be a JSON object."
        )
    _measure(document, ceilings=ceilings)
    _reject_unsafe_numbers(document, ceilings=ceilings)
    _reject_external_resources(document)
    return document


def read_artifact_snapshot(
    path: str | Path,
    *,
    ceilings: HostCeilings = DEFAULT_HOST_CEILINGS,
) -> bytes:
    """Read an untrusted path once without following a symlink input."""

    candidate = Path(path)
    if candidate.is_symlink():
        raise ArtifactIngressError(
            "InputSymlinkRejected",
            "Artifact path must not be a symbolic link.",
        )
    try:
        payload = candidate.read_bytes()
    except OSError as error:
        raise ArtifactIngressError("ArtifactReadFailure", str(error)) from error
    if len(payload) > ceilings.max_file_bytes:
        raise ArtifactIngressError(
            "ArtifactTooLarge",
            f"Artifact exceeds the {ceilings.max_file_bytes}-byte ingress limit.",
        )
    return payload


def decode_artifact_file(
    path: str | Path,
    *,
    ceilings: HostCeilings = DEFAULT_HOST_CEILINGS,
) -> dict[str, Any]:
    return decode_artifact_bytes(
        read_artifact_snapshot(path, ceilings=ceilings), ceilings=ceilings
    )


__all__ = [
    "ArtifactIngressError",
    "DEFAULT_HOST_CEILINGS",
    "HostCeilings",
    "decode_artifact_bytes",
    "decode_artifact_file",
    "read_artifact_snapshot",
]
