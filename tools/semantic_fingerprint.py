#!/usr/bin/env python3
"""CanonicalSemanticProjectionV1 and SemanticFingerprintV1 reference utility."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from decimal import Decimal
from pathlib import Path
from typing import Any

FINGERPRINT_PREFIX = "sf:v1:sha256:"
TOP_LEVEL_SEMANTIC_FIELDS = (
    "kind",
    "action",
    "roles",
    "modifiers",
    "conditions",
    "constraints",
)
TOP_LEVEL_METADATA_FIELDS = {
    "schema_version",
    "provenance",
    "ambiguity",
    "semantic_fingerprint",
    "unknowns",
}
SEMANTIC_VALUE_FIELDS = {
    "kind",
    "semantic_kind",
    "mode",
    "selector",
    "value",
    "unit",
    "reason",
}
LANGUAGE_METADATA_FIELDS = {
    "evidence_id",
    "evidence_ids",
    "candidate_id",
    "candidate_ids",
    "source_span",
    "source_spans",
    "span",
    "spans",
    "tokenization",
    "tokens",
    "morphology",
    "provider",
    "commentary",
    "register",
    "style",
    "renderer_revision",
}


class SemanticFingerprintError(ValueError):
    """Base class for deterministic fingerprint diagnostics."""


class UnsupportedSemanticExtension(SemanticFingerprintError):
    """A schema-valid extension has no V1 semantic/provenance classification."""


class JCSRepresentationError(SemanticFingerprintError):
    """A projection value is outside the supported JCS/I-JSON boundary."""


class UnknownSummaryContradiction(SemanticFingerprintError):
    """The diagnostic unknown summary contradicts direct semantic Unknown roles."""


def _unsupported(path: str, fields: set[str]) -> None:
    names = ", ".join(sorted(fields))
    raise UnsupportedSemanticExtension(
        f"unsupported semantic extension at {path}: {names}"
    )


def _project_payload(value: Any, path: str) -> Any:
    """Project nested selector/value payloads, excluding named provenance metadata."""
    if isinstance(value, dict):
        return {
            key: _project_payload(child, f"{path}.{key}")
            for key, child in value.items()
            if key not in LANGUAGE_METADATA_FIELDS
        }
    if isinstance(value, list):
        return [
            _project_payload(child, f"{path}[{index}]")
            for index, child in enumerate(value)
        ]
    return value


def _project_semantic_value(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SemanticFingerprintError(f"semantic value at {path} must be an object")
    unknown = set(value) - SEMANTIC_VALUE_FIELDS - LANGUAGE_METADATA_FIELDS
    if unknown:
        _unsupported(path, unknown)

    projected: dict[str, Any] = {}
    for field in SEMANTIC_VALUE_FIELDS:
        if field not in value:
            continue
        child = value[field]
        if field in {"selector", "value"}:
            if (
                field == "value"
                and value.get("kind") == "NestedNSR"
                and isinstance(child, dict)
                and "kind" in child
                and "roles" in child
            ):
                child = canonical_semantic_projection_v1(child)
            else:
                child = _project_payload(child, f"{path}.{field}")
        projected[field] = child
    return projected


def _project_role(role: Any, path: str) -> dict[str, Any]:
    if not isinstance(role, dict):
        raise SemanticFingerprintError(f"role at {path} must be an object")
    unknown = set(role) - {"role", "value"} - LANGUAGE_METADATA_FIELDS
    if unknown:
        _unsupported(path, unknown)
    if "role" not in role or "value" not in role:
        raise SemanticFingerprintError(f"role at {path} requires role and value")
    return {
        "role": role["role"],
        "value": _project_semantic_value(role["value"], f"{path}.value"),
    }


def _check_unknown_summary(nsr: dict[str, Any], projected_roles: list[dict[str, Any]]) -> None:
    """Diagnose contradictions that are cheap to prove for direct role Unknowns."""
    if "unknowns" not in nsr:
        return
    summary = nsr["unknowns"]
    if not isinstance(summary, list):
        return
    semantic_unknowns = {
        (role["role"], role["value"].get("reason"))
        for role in projected_roles
        if role["value"].get("kind") == "Unknown"
    }
    summary_unknowns = {
        (entry.get("field"), entry.get("reason"))
        for entry in summary
        if isinstance(entry, dict)
    }
    role_names = {role["role"] for role in projected_roles}
    contradictory_summary = {
        occurrence
        for occurrence in summary_unknowns
        if occurrence[0] in role_names and occurrence not in semantic_unknowns
    }
    if not semantic_unknowns <= summary_unknowns or contradictory_summary:
        raise UnknownSummaryContradiction(
            "top-level unknowns summary contradicts direct semantic Unknown roles"
        )


def canonical_semantic_projection_v1(nsr: dict[str, Any]) -> dict[str, Any]:
    """Return the V1 execution-semantic projection of an NSR object."""
    if not isinstance(nsr, dict):
        raise SemanticFingerprintError("NSR must be a JSON object")
    unknown_top_level = (
        set(nsr) - set(TOP_LEVEL_SEMANTIC_FIELDS) - TOP_LEVEL_METADATA_FIELDS
    )
    if unknown_top_level:
        _unsupported("$", unknown_top_level)
    if "kind" not in nsr or "roles" not in nsr:
        raise SemanticFingerprintError("NSR requires kind and roles")
    if not isinstance(nsr["roles"], list):
        raise SemanticFingerprintError("$.roles must be an array")

    roles = [
        _project_role(role, f"$.roles[{index}]")
        for index, role in enumerate(nsr["roles"])
    ]
    roles.sort(key=lambda role: (str(role["role"]), jcs_canonicalize(role["value"])))
    _check_unknown_summary(nsr, roles)

    projection: dict[str, Any] = {"kind": nsr["kind"]}
    if "action" in nsr:
        projection["action"] = nsr["action"]
    projection["roles"] = roles
    for field in ("modifiers", "conditions", "constraints"):
        if field in nsr:
            values = nsr[field]
            if not isinstance(values, list):
                raise SemanticFingerprintError(f"$.{field} must be an array")
            projection[field] = [
                _project_semantic_value(value, f"$.{field}[{index}]")
                for index, value in enumerate(values)
            ]
    return projection


def _validate_string(value: str, path: str) -> None:
    for character in value:
        codepoint = ord(character)
        if 0xD800 <= codepoint <= 0xDFFF:
            raise JCSRepresentationError(
                f"unpaired Unicode surrogate is not valid I-JSON at {path}"
            )


def _serialize_float(value: float, path: str) -> str:
    if not math.isfinite(value):
        raise JCSRepresentationError(f"non-finite number at {path}")
    if value == 0:
        return "0"

    negative = value < 0
    absolute = -value if negative else value
    raw = repr(absolute).lower()
    decimal = Decimal(raw)

    if 1e-6 <= absolute < 1e21:
        rendered = format(decimal, "f")
        if "." in rendered:
            rendered = rendered.rstrip("0").rstrip(".")
    else:
        normalized = decimal.normalize()
        digits = "".join(str(digit) for digit in normalized.as_tuple().digits)
        exponent = normalized.adjusted()
        mantissa = digits[0]
        if len(digits) > 1:
            mantissa += "." + digits[1:].rstrip("0")
            mantissa = mantissa.rstrip(".")
        sign = "+" if exponent >= 0 else ""
        rendered = f"{mantissa}e{sign}{exponent}"
    return f"-{rendered}" if negative else rendered


def _jcs(value: Any, path: str) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        _validate_string(value, path)
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, int):
        try:
            as_double = float(value)
        except OverflowError as error:
            raise JCSRepresentationError(
                f"integer is outside the IEEE 754 double range at {path}"
            ) from error
        if not math.isfinite(as_double) or int(as_double) != value:
            raise JCSRepresentationError(
                f"integer is not exactly representable as an IEEE 754 double at {path}"
            )
        return _serialize_float(as_double, path)
    if isinstance(value, float):
        return _serialize_float(value, path)
    if isinstance(value, list):
        return "[" + ",".join(
            _jcs(child, f"{path}[{index}]")
            for index, child in enumerate(value)
        ) + "]"
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise JCSRepresentationError(f"non-string object key at {path}")
        for key in value:
            _validate_string(key, path)
        keys = sorted(value, key=lambda key: key.encode("utf-16-be"))
        return "{" + ",".join(
            f"{_jcs(key, path)}:{_jcs(value[key], f'{path}.{key}')}"
            for key in keys
        ) + "}"
    raise JCSRepresentationError(
        f"unsupported JSON value {type(value).__name__} at {path}"
    )


def jcs_canonicalize(value: Any) -> str:
    """Serialize JSON-compatible data according to RFC 8785/JCS."""
    return _jcs(value, "$")


def semantic_fingerprint_v1(nsr: dict[str, Any]) -> str:
    projection = canonical_semantic_projection_v1(nsr)
    canonical = jcs_canonicalize(projection).encode("utf-8")
    return FINGERPRINT_PREFIX + hashlib.sha256(canonical).hexdigest()


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise JCSRepresentationError(f"duplicate JSON object property: {key}")
        result[key] = value
    return result


def load_json_document(text: str) -> Any:
    """Parse an I-JSON document while rejecting duplicate object properties."""
    return json.loads(text, object_pairs_hook=_unique_object)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Project an NSR and calculate SemanticFingerprintV1."
    )
    parser.add_argument("nsr", type=Path)
    parser.add_argument(
        "--projection", action="store_true", help="print canonical projection JSON"
    )
    args = parser.parse_args()
    nsr = load_json_document(args.nsr.read_text(encoding="utf-8"))
    if args.projection:
        print(jcs_canonicalize(canonical_semantic_projection_v1(nsr)))
    print(semantic_fingerprint_v1(nsr))


if __name__ == "__main__":
    main()
