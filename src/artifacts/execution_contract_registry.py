"""Versioned admission for semantic/runtime execution contract pairs."""
from __future__ import annotations

from dataclasses import dataclass


class ExecutionContractError(ValueError):
    """Stable failure raised before evaluator or PREPARE execution."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


ContractIdentity = tuple[str, str]


@dataclass(frozen=True)
class ExecutionContractRegistration:
    """One admitted semantic/runtime pairing owned by trusted host code."""

    contract_id: str
    revision: str
    semantic_contract: ContractIdentity
    runtime_contract: ContractIdentity | None


class ExecutionContractRegistry:
    """Fail-closed pair registry; independent identities are not sufficient."""

    def __init__(self) -> None:
        self._registrations: dict[
            tuple[ContractIdentity, ContractIdentity | None],
            ExecutionContractRegistration,
        ] = {}

    def register(self, registration: ExecutionContractRegistration) -> None:
        key = (registration.semantic_contract, registration.runtime_contract)
        if key in self._registrations:
            raise ExecutionContractError(
                "DuplicateExecutionContract",
                f"Duplicate execution contract pair {key!r}.",
            )
        self._registrations[key] = registration

    def resolve(
        self,
        semantic_contract: ContractIdentity,
        runtime_contract: ContractIdentity | None,
    ) -> ExecutionContractRegistration:
        key = (semantic_contract, runtime_contract)
        registration = self._registrations.get(key)
        if registration is None:
            raise ExecutionContractError(
                "ExecutionContractPairNotAdmitted",
                "The declared semantic/runtime contract pair is not admitted.",
            )
        return registration
