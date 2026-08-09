"""Versioned semantic handler registry for experimental artifact ingress."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


class SemanticHandlerError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


SemanticHandler = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class SemanticHandlerRegistration:
    contract_id: str
    revision: str
    support_level: str
    handler: SemanticHandler


class SemanticHandlerRegistry:
    """Fail-closed registry keyed only by declared contract identity/revision."""

    def __init__(self) -> None:
        self._handlers: dict[tuple[str, str], SemanticHandlerRegistration] = {}

    def register(self, registration: SemanticHandlerRegistration) -> None:
        key = (registration.contract_id, registration.revision)
        if key in self._handlers:
            raise SemanticHandlerError("DuplicateSemanticContract", f"Duplicate semantic contract {key!r}.")
        self._handlers[key] = registration

    def resolve(self, contract_id: str, revision: str) -> SemanticHandlerRegistration:
        registration = self._handlers.get((contract_id, revision))
        if registration is None:
            known_id = any(key[0] == contract_id for key in self._handlers)
            code = "UnknownSemanticContractVersion" if known_id else "UnknownSemanticContract"
            raise SemanticHandlerError(code, f"No semantic handler for {contract_id!r}@{revision!r}.")
        return registration
