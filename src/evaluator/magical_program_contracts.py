"""Portable MagicalProgram-0 semantic contract registry and typing helpers."""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from src.artifacts.magical_program_values import value_signature

_JSON = dict[str, Any]
MKI_OPERATIONS = frozenset(
    {"RESOLVE", "OBSERVE", "CHANNEL", "TRANSFER", "RECONFIGURE", "CONSTRAIN"}
)
WORLD_KERNEL_CLASSES = frozenset(
    {"QUERY", "SAMPLE", "TRANSITION", "ACTIVATE", "DEACTIVATE"}
)


@dataclass(frozen=True)
class ProgramContractRegistration:
    contract_id: str
    revision: str
    instruction: str
    input_kinds: tuple[str, ...]
    output_kind: str
    required_obligation_categories: tuple[str, ...]
    minimum_energy_j: float
    minimum_matter_kg: float
    minimum_events: int
    mki_operations: tuple[str, ...]
    world_kernel_classes: tuple[str, ...]
    support_level: str = "implemented"

    def __post_init__(self) -> None:
        if self.instruction not in {"evidence.observe", "effect.invoke"}:
            raise ValueError("unsupported instruction")
        if self.support_level not in {"implemented", "recognized-unsupported"}:
            raise ValueError("unknown support level")
        if not set(self.mki_operations) <= MKI_OPERATIONS:
            raise ValueError("non-MKI operation")
        if not set(self.world_kernel_classes) <= WORLD_KERNEL_CLASSES:
            raise ValueError("unknown World Kernel class")
        if self.support_level != "implemented" and (
            self.mki_operations or self.world_kernel_classes
        ):
            raise ValueError("unsupported contracts cannot claim executable lowering")
        for signature in self.input_kinds:
            if signature in {"object", "array", "any", "*"}:
                raise ValueError("untyped structured contract signature")


class ProgramSemanticError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        node_id: str | None = None,
        order: int | None = None,
        path: str = "",
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code, self.node_id, self.order, self.path = code, node_id, order, path
        self.details = dict(details or {})


class ProgramContractRegistry:
    def __init__(
        self, registrations: Iterable[ProgramContractRegistration] = ()
    ) -> None:
        self._items: dict[tuple[str, str], ProgramContractRegistration] = {}
        for item in registrations:
            self.register(item)

    def register(self, item: ProgramContractRegistration) -> None:
        key = (item.contract_id, item.revision)
        if key in self._items:
            raise ValueError(f"duplicate program contract: {key!r}")
        self._items[key] = item

    def lookup(self, contract_id: str, revision: str) -> ProgramContractRegistration:
        item = self._items.get((contract_id, revision))
        if item is None:
            raise ProgramSemanticError(
                "ProgramUnknownContract",
                f"Unknown program contract {contract_id!r}@{revision!r}.",
            )
        return item

    def resolve(self, contract_id: str, revision: str) -> ProgramContractRegistration:
        item = self.lookup(contract_id, revision)
        if item.support_level != "implemented":
            raise ProgramSemanticError(
                "ProgramContractUnsupported",
                f"Program contract {contract_id!r}@{revision!r} is not implemented.",
            )
        return item

    def admitted_pairs(self) -> set[tuple[str, str]]:
        return set(self._items)

    def registrations(self) -> tuple[ProgramContractRegistration, ...]:
        return tuple(
            sorted(
                self._items.values(),
                key=lambda item: (item.contract_id, item.revision),
            )
        )

    def evidence(self) -> list[_JSON]:
        return [
            {
                "id": f"evidence:program-contract:{item.contract_id}:{item.revision}",
                "source_kind": "ProgramContractRegistry",
                "source_id": item.contract_id,
                "revision": item.revision,
                "path": None,
            }
            for item in self.registrations()
        ]


def default_program_contract_registry() -> ProgramContractRegistry:
    return ProgramContractRegistry(
        (
            ProgramContractRegistration(
                "generic.transition",
                "1",
                "effect.invoke",
                ("reference", "literal:string"),
                "effect_result",
                ("capabilities", "leases", "identities", "accounting"),
                1.0,
                0.0,
                1,
                ("RECONFIGURE",),
                ("TRANSITION",),
            ),
            ProgramContractRegistration(
                "generic.observe",
                "1",
                "evidence.observe",
                ("reference",),
                "evidence",
                ("capabilities", "identities", "evidence", "accounting"),
                0.0,
                0.0,
                1,
                ("OBSERVE",),
                ("SAMPLE",),
            ),
        )
    )


def _sig(value: Mapping[str, Any]) -> str:
    return value_signature(value)


def _typed(value: Mapping[str, Any]) -> _JSON:
    result = copy.deepcopy(dict(value))
    result["type_signature"] = _sig(value)
    return result


def _error(
    node: Mapping[str, Any], code: str, message: str, **details: Any
) -> ProgramSemanticError:
    return ProgramSemanticError(
        code,
        message,
        node_id=str(node["node_id"]),
        order=int(node["order"]),
        path=f"/nodes/{node['order']}",
        details=details,
    )


def _compatible(
    left: Mapping[str, Any], right: Mapping[str, Any], node: Mapping[str, Any]
) -> None:
    if left.get("kind") == right.get("kind") == "quantity":
        for field, code in (
            ("semantic_type", "ProgramTypeMismatch"),
            ("dimension", "ProgramDimensionMismatch"),
            ("unit", "ProgramUnitMismatch"),
        ):
            if left.get(field) != right.get(field):
                raise _error(node, code, f"Quantity {field} differs.")
        return
    if _sig(left) != _sig(right):
        raise _error(node, "ProgramTypeMismatch", "Input values have incompatible types.")


def _comparable_payload(value: Mapping[str, Any]) -> Any:
    result = copy.deepcopy(dict(value))
    result.pop("value_id", None)
    result.pop("type_signature", None)
    return result


def _pure(
    node: Mapping[str, Any], values: Sequence[Mapping[str, Any]]
) -> list[_JSON]:
    instruction = node["instruction"]
    if instruction == "assert.require":
        if len(values) != 1 or _sig(values[0]) != "literal:boolean":
            raise _error(
                node, "ProgramTypeMismatch", "assert.require requires one Boolean."
            )
        if values[0]["value"] is not True:
            raise _error(
                node,
                "ProgramAssertionFailed",
                "Program assertion evaluated to false.",
                requested_diagnostic=node.get("diagnostic_code"),
            )
        return []
    if instruction == "pure.rank":
        if not values:
            raise _error(node, "ProgramOperatorArity", "pure.rank requires an input.")
        for value in values[1:]:
            _compatible(values[0], value, node)
        if any(value.get("kind") in {"record", "sequence"} for value in values):
            raise _error(
                node,
                "ProgramStructuredPureOperationUnsupported",
                "Structured values are not orderable in revision 0.",
            )
        return [
            {
                "kind": "ranked_sequence",
                "type_signature": f"ranked:{_sig(values[0])}",
                "value": sorted(
                    (item.get("value", item.get("handle_id")) for item in values),
                    reverse=node["direction"] == "descending",
                ),
            }
        ]
    if len(values) != 2:
        raise _error(
            node, "ProgramOperatorArity", f"{instruction} requires two inputs."
        )
    left, right = values
    operator = node["operator"]
    _compatible(left, right, node)
    if instruction == "pure.compare":
        if operator not in {
            "equal",
            "not_equal",
            "less",
            "less_equal",
            "greater",
            "greater_equal",
        }:
            raise _error(
                node, "ProgramOperatorMismatch", "Invalid comparison operator."
            )
        if left.get("kind") in {"record", "sequence"}:
            if operator not in {"equal", "not_equal"}:
                raise _error(
                    node,
                    "ProgramStructuredPureOperationUnsupported",
                    "Structured values admit equality comparison only in revision 0.",
                )
            a, b = _comparable_payload(left), _comparable_payload(right)
        else:
            a, b = left.get("value"), right.get("value")
        value = {
            "equal": a == b,
            "not_equal": a != b,
            "less": a < b,
            "less_equal": a <= b,
            "greater": a > b,
            "greater_equal": a >= b,
        }[operator]
        return [_typed({"kind": "literal", "value": value})]
    if operator not in {
        "add",
        "subtract",
        "multiply",
        "divide",
        "minimum",
        "maximum",
    }:
        raise _error(node, "ProgramOperatorMismatch", "Invalid calculation operator.")
    if left.get("kind") == "quantity":
        if operator not in {"add", "subtract", "minimum", "maximum"}:
            raise _error(
                node,
                "ProgramDimensionOperationUnsupported",
                "Quantity multiply/divide is not admitted.",
            )
        result = copy.deepcopy(dict(left))
        result.pop("value_id", None)
        a, b = float(left["value"]), float(right["value"])
    elif _sig(left) == "literal:number":
        result = {"kind": "literal"}
        a, b = left["value"], right["value"]
    else:
        raise _error(
            node, "ProgramTypeMismatch", "Calculation requires numeric inputs."
        )
    if operator == "divide" and b == 0:
        raise _error(node, "ProgramDivisionByZero", "Division by zero.")
    result["value"] = {
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b else 0,
        "minimum": min(a, b),
        "maximum": max(a, b),
    }[operator]
    return [_typed(result)]


def _requirements(
    node: Mapping[str, Any],
    registration: ProgramContractRegistration,
    bindings: Mapping[str, Mapping[str, Any]],
) -> _JSON:
    declared = copy.deepcopy(node["obligations"])
    for category in registration.required_obligation_categories:
        if not declared.get(category):
            raise _error(
                node,
                "ProgramObligationMissing",
                f"Contract requires {category}.",
                category=category,
            )
    for category in (
        "capabilities",
        "leases",
        "identities",
        "evidence",
        "accounting",
    ):
        for requirement in declared[category]:
            target = requirement.get("target_binding")
            if target is not None and _sig(bindings.get(target, {})) != "reference":
                raise _error(
                    node,
                    "ProgramRequirementTargetTypeMismatch",
                    f"Requirement {requirement['requirement_id']!r} must target "
                    "a resolved reference.",
                )
    minima = {
        "energy_j": registration.minimum_energy_j,
        "matter_kg": registration.minimum_matter_kg,
        "events": registration.minimum_events,
    }
    for key, minimum in minima.items():
        if float(declared["resources"][key]) < float(minimum):
            raise _error(
                node,
                "ProgramResourceDeclarationInsufficient",
                f"Declared {key} is below the contract minimum.",
                resource=key,
            )
    return {
        "declared_requirements": declared,
        "required_categories": list(registration.required_obligation_categories),
        "contract_minimum_resources": minima,
        "authority_granted": False,
        "resources_reserved": False,
        "host_records_bound": False,
        "requires_runtime_revalidation": True,
    }


__all__ = [
    "MKI_OPERATIONS",
    "WORLD_KERNEL_CLASSES",
    "ProgramContractRegistration",
    "ProgramContractRegistry",
    "ProgramSemanticError",
    "default_program_contract_registry",
    "_sig",
    "_typed",
    "_error",
    "_pure",
    "_requirements",
]
