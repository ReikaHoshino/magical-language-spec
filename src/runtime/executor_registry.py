"""Versioned runtime executor registry for implementation-owned extensions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from jsonschema import Draft202012Validator

from .sandbox import PreparedPlan, SandboxWorld


class RuntimeExecutorError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


RuntimeExecutor = Callable[[PreparedPlan, SandboxWorld], dict[str, Any]]
PrecommitHook = Callable[[PreparedPlan, SandboxWorld], None]


@dataclass(frozen=True)
class ParameterReference:
    field: str
    collection: str


@dataclass(frozen=True)
class RuntimeExecutorRegistration:
    contract_id: str
    revision: str
    executor: RuntimeExecutor
    parameter_schema: dict[str, Any]
    parameter_references: tuple[ParameterReference, ...] = ()
    precommit_hook: PrecommitHook | None = None


class RuntimeExecutorRegistry:
    """Fail-closed registry; registration never grants Capability or Lease."""

    def __init__(self) -> None:
        self._executors: dict[tuple[str, str], RuntimeExecutorRegistration] = {}

    def register(self, registration: RuntimeExecutorRegistration) -> None:
        key = (registration.contract_id, registration.revision)
        if key in self._executors:
            raise RuntimeExecutorError("DuplicateRuntimeContract", f"Duplicate runtime contract {key!r}.")
        Draft202012Validator.check_schema(registration.parameter_schema)
        self._executors[key] = registration

    def resolve(self, contract_id: str, revision: str) -> RuntimeExecutorRegistration:
        registration = self._executors.get((contract_id, revision))
        if registration is None:
            known_id = any(key[0] == contract_id for key in self._executors)
            code = "UnknownRuntimeContractVersion" if known_id else "UnknownRuntimeContract"
            raise RuntimeExecutorError(code, f"No runtime executor for {contract_id!r}@{revision!r}.")
        return registration

    @staticmethod
    def validate_parameters(
        registration: RuntimeExecutorRegistration,
        parameters: Any,
        bundle: dict[str, Any],
    ) -> None:
        errors = sorted(
            Draft202012Validator(registration.parameter_schema).iter_errors(parameters),
            key=lambda error: (list(error.absolute_path), error.validator),
        )
        if errors:
            error = errors[0]
            code = {
                "required": "ExecutionParameterMissing",
                "type": "ExecutionParameterTypeMismatch",
                "additionalProperties": "ExecutionParameterUnknown",
                "enum": "ExecutionParameterValueInvalid",
                "const": "ExecutionParameterValueInvalid",
            }.get(error.validator, "ExecutionParameterSchemaViolation")
            location = "execution.parameters"
            for part in error.absolute_path:
                location += f"[{part}]" if isinstance(part, int) else f".{part}"
            raise RuntimeExecutorError(code, f"{location}: {error.message}")

        sources: dict[str, Any] = {
            "entities": bundle["initial_world"]["entities"],
            "capabilities": bundle["initial_world"]["capabilities"],
            "leases": bundle["initial_world"]["leases"],
            "ledgers": bundle["initial_world"]["ledgers"],
            "controllers": bundle["initial_world"].get("controllers", {}),
        }
        for reference in registration.parameter_references:
            value = parameters.get(reference.field)
            collection = sources[reference.collection]
            if value not in collection:
                raise RuntimeExecutorError(
                    "ExecutionParameterReferenceInvalid",
                    f"execution.parameters.{reference.field} does not identify an admitted {reference.collection} record.",
                )
