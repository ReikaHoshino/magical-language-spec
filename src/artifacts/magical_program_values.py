"""Shared immutable value typing for MagicalProgram-0."""
from __future__ import annotations

from typing import Any, Mapping


def _quantity_element_signature(value: Mapping[str, Any]) -> str:
    semantic_type = value.get("semantic_type")
    dimension = value.get("dimension")
    unit = value.get("unit")
    if all(isinstance(item, str) for item in (semantic_type, dimension, unit)):
        return f"quantity:{semantic_type}:{dimension}:{unit}"
    return "quantity:invalid"


def value_signature(value: Mapping[str, Any]) -> str:
    """Return the exact graph or anonymous-element signature.

    Top-level and evaluator-produced quantity bindings retain the historical
    `quantity` signature. Anonymous quantities inside structured values have
    neither a `value_id` nor a graph `type_signature`; their semantic type,
    dimension, and unit become part of the homogeneous-sequence signature.
    """

    kind = str(value.get("kind"))
    if kind == "literal":
        literal = value.get("value")
        if isinstance(literal, bool):
            return "literal:boolean"
        if isinstance(literal, (int, float)) and not isinstance(literal, bool):
            return "literal:number"
        if isinstance(literal, str):
            return "literal:string"
        if literal is None:
            return "literal:null"
        return "literal:unsupported"
    if kind == "quantity":
        if "value_id" in value or value.get("type_signature") == "quantity":
            return "quantity"
        return _quantity_element_signature(value)
    if kind == "record":
        type_id = value.get("type_id")
        return f"record:{type_id}" if isinstance(type_id, str) else "record:invalid"
    if kind == "sequence":
        element_type = value.get("element_type")
        return (
            f"sequence:{element_type}"
            if isinstance(element_type, str)
            else "sequence:invalid"
        )
    return kind


def structured_element_signature(value: Mapping[str, Any]) -> str:
    """Return the exact signature required for an anonymous sequence item."""

    if value.get("kind") == "quantity":
        return _quantity_element_signature(value)
    return value_signature(value)


__all__ = ["structured_element_signature", "value_signature"]
