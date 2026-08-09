"""JSON Schema helpers shared by the v0.8 local evaluator."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from src.resources import reference_root, resource_path

ROOT = reference_root()
SCHEMAS = resource_path("schemas")


class SchemaValidationError(ValueError):
    """Raised when a public evaluator artifact is not schema-valid."""

    def __init__(self, schema_name: str, errors: list[str]) -> None:
        self.schema_name = schema_name
        self.errors = errors
        super().__init__(f"{schema_name} validation failed: {'; '.join(errors)}")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def validator(schema_name: str) -> Draft202012Validator:
    schema = _load_json(SCHEMAS / schema_name)
    registry = Registry()
    for path in sorted(SCHEMAS.glob("*.schema.json")):
        document = _load_json(path)
        resource = Resource.from_contents(document)
        registry = registry.with_resource(document["$id"], resource)
        registry = registry.with_resource(path.resolve().as_uri(), resource)
    return Draft202012Validator(
        schema,
        registry=registry,
        format_checker=FormatChecker(),
    )


def validation_errors(schema_name: str, instance: Any) -> list[str]:
    errors = sorted(validator(schema_name).iter_errors(instance), key=lambda error: list(error.path))
    rendered: list[str] = []
    for error in errors:
        location = "$"
        for part in error.absolute_path:
            location += f"[{part}]" if isinstance(part, int) else f".{part}"
        rendered.append(f"{location}: {error.message}")
    return rendered


def require_valid(schema_name: str, instance: Any) -> None:
    errors = validation_errors(schema_name, instance)
    if errors:
        raise SchemaValidationError(schema_name, errors)


def validate_nsr(nsr: Any) -> None:
    require_valid("nsr.schema.json", nsr)


def validate_feasibility_report(report: Any) -> None:
    require_valid("feasibility-report.schema.json", report)
