"""Schema validation helpers for v0.9 runtime execution artifacts."""
from __future__ import annotations

import json
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from src.resources import reference_root, resource_path

ROOT = reference_root()
SCHEMA_PATH = resource_path("schemas/runtime-execution.schema.json")


class RuntimeSchemaValidationError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors


def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate_execution_trace(value: Any) -> None:
    errors = sorted(
        _validator().iter_errors(value),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        rendered = []
        for error in errors:
            path = "$"
            for item in error.absolute_path:
                path += f"[{item!r}]" if isinstance(item, int) else f".{item}"
            rendered.append(f"{path}: {error.message}")
        raise RuntimeSchemaValidationError(rendered)
