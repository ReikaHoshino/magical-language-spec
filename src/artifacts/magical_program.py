"""Structural admission for the experimental MagicalProgram-0 artifact.

The artifact is portable declarative input. It may declare requirements, but
never host-owned Capability, Lease, identity, evidence, or accounting records.
Those records are selected and frozen only by PREPARE.
"""
from __future__ import annotations

import copy
import json
import math
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator

from .magical_program_values import value_signature

_JSON = dict[str, Any]


@dataclass(frozen=True)
class MagicalProgramHostLimits:
    max_bytes: int = 262_144
    max_nodes: int = 256
    max_edges: int = 1_024
    max_depth: int = 64
    max_values: int = 512
    max_outputs: int = 128
    max_events: int = 128
    max_energy_j: float = 1_000_000_000.0
    max_microsteps: int = 4_096
    max_concurrency: int = 16
    max_structured_depth: int = 8
    max_structured_items: int = 1_024
    max_record_fields: int = 128
    max_sequence_items: int = 512


class MagicalProgramAdmissionError(RuntimeError):
    def __init__(self, code: str, message: str, *, path: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.path = path

    def diagnostic(self) -> _JSON:
        return {"code": self.code, "message": str(self), "path": self.path}


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> _JSON:
    result: _JSON = {}
    for key, value in pairs:
        if key in result:
            raise MagicalProgramAdmissionError(
                "ProgramDuplicateJsonProperty",
                f"Duplicate JSON property: {key!r}.",
                path=f"/{key}",
            )
        result[key] = value
    return result


def _reject_nonfinite_constant(token: str) -> None:
    raise MagicalProgramAdmissionError(
        "ProgramNonFiniteNumber",
        f"Non-finite JSON number {token!r} is not admitted.",
    )


def decode_program(
    payload: bytes,
    *,
    limits: MagicalProgramHostLimits = MagicalProgramHostLimits(),
) -> _JSON:
    if len(payload) > limits.max_bytes:
        raise MagicalProgramAdmissionError(
            "ProgramByteLimitExceeded",
            f"Program size {len(payload)} exceeds host ceiling {limits.max_bytes}.",
        )
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise MagicalProgramAdmissionError(
            "ProgramUtf8Required", "Program input must be strict UTF-8."
        ) from error
    try:
        document = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_nonfinite_constant,
        )
    except MagicalProgramAdmissionError:
        raise
    except json.JSONDecodeError as error:
        raise MagicalProgramAdmissionError(
            "ProgramJsonMalformed",
            f"Malformed JSON at line {error.lineno}, column {error.colno}.",
        ) from error
    if not isinstance(document, dict):
        raise MagicalProgramAdmissionError(
            "ProgramRootNotObject", "Program root must be a JSON object."
        )
    return document


def _schema_path(error: Any) -> str:
    return "".join(f"/{item}" for item in error.absolute_path)


def _validate_schema(program: _JSON, schema: Mapping[str, Any]) -> None:
    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(program),
        key=lambda item: (list(item.absolute_path), item.message),
    )
    if errors:
        error = errors[0]
        raise MagicalProgramAdmissionError(
            "ProgramSchemaViolation", error.message, path=_schema_path(error)
        )


def _unique(
    items: Iterable[str], *, code: str, label: str, path: str = ""
) -> set[str]:
    seen: set[str] = set()
    for item in items:
        if item in seen:
            raise MagicalProgramAdmissionError(
                code, f"Duplicate {label}: {item!r}.", path=path
            )
        seen.add(item)
    return seen


def _check_finite(value: Any, *, path: str = "") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise MagicalProgramAdmissionError(
            "ProgramNonFiniteNumber",
            "MagicalProgram numbers must be finite.",
            path=path,
        )
    if isinstance(value, dict):
        for key, child in value.items():
            _check_finite(child, path=f"{path}/{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _check_finite(child, path=f"{path}/{index}")


def _check_structured_value(
    value: Mapping[str, Any],
    *,
    limits: MagicalProgramHostLimits,
    depth: int,
    path: str,
    counter: list[int],
) -> None:
    kind = value.get("kind")
    if kind not in {"record", "sequence"}:
        return
    if depth > limits.max_structured_depth:
        raise MagicalProgramAdmissionError(
            "ProgramStructuredDepthLimitExceeded",
            f"Structured value depth {depth} exceeds host ceiling "
            f"{limits.max_structured_depth}.",
            path=path,
        )
    if kind == "record":
        fields = value.get("fields", {})
        if not isinstance(fields, dict):
            return
        if len(fields) > limits.max_record_fields:
            raise MagicalProgramAdmissionError(
                "ProgramRecordFieldLimitExceeded",
                f"Record field count {len(fields)} exceeds host ceiling "
                f"{limits.max_record_fields}.",
                path=f"{path}/fields",
            )
        counter[0] += len(fields)
        for key, child in fields.items():
            if isinstance(child, dict):
                _check_structured_value(
                    child,
                    limits=limits,
                    depth=depth + 1,
                    path=f"{path}/fields/{key}",
                    counter=counter,
                )
    else:
        items = value.get("items", [])
        if not isinstance(items, list):
            return
        if len(items) > limits.max_sequence_items:
            raise MagicalProgramAdmissionError(
                "ProgramSequenceItemLimitExceeded",
                f"Sequence item count {len(items)} exceeds host ceiling "
                f"{limits.max_sequence_items}.",
                path=f"{path}/items",
            )
        counter[0] += len(items)
        expected = value.get("element_type")
        for index, child in enumerate(items):
            if isinstance(child, dict):
                observed = value_signature(child)
                if observed != expected:
                    raise MagicalProgramAdmissionError(
                        "ProgramSequenceElementTypeMismatch",
                        f"Sequence expects {expected!r} but item {index} has "
                        f"signature {observed!r}.",
                        path=f"{path}/items/{index}",
                    )
                _check_structured_value(
                    child,
                    limits=limits,
                    depth=depth + 1,
                    path=f"{path}/items/{index}",
                    counter=counter,
                )
    if counter[0] > limits.max_structured_items:
        raise MagicalProgramAdmissionError(
            "ProgramStructuredItemLimitExceeded",
            f"Structured item total {counter[0]} exceeds host ceiling "
            f"{limits.max_structured_items}.",
            path=path,
        )


def _check_structured_values(
    program: _JSON, limits: MagicalProgramHostLimits
) -> None:
    counter = [0]
    for index, value in enumerate(program.get("values", [])):
        if isinstance(value, dict):
            _check_structured_value(
                value,
                limits=limits,
                depth=1,
                path=f"/values/{index}",
                counter=counter,
            )


def _canonical_size(program: Mapping[str, Any]) -> int:
    try:
        payload = json.dumps(
            program,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise MagicalProgramAdmissionError(
            "ProgramCanonicalizationFailure",
            "Program cannot be canonically serialized.",
        ) from error
    return len(payload)


def _check_host_limits(program: _JSON, limits: MagicalProgramHostLimits) -> None:
    counts = {
        "nodes": (len(program["nodes"]), limits.max_nodes, "ProgramNodeLimitExceeded"),
        "edges": (len(program["edges"]), limits.max_edges, "ProgramEdgeLimitExceeded"),
        "values": (
            len(program["values"]),
            limits.max_values,
            "ProgramValueLimitExceeded",
        ),
        "outputs": (
            len(program["outputs"]),
            limits.max_outputs,
            "ProgramOutputLimitExceeded",
        ),
    }
    for label, (actual, ceiling, code) in counts.items():
        if actual > ceiling:
            raise MagicalProgramAdmissionError(
                code, f"Program {label} {actual} exceeds host ceiling {ceiling}."
            )

    budget = program["budget"]
    ceilings = (
        (
            "energy_j",
            float(budget["energy_j"]),
            float(limits.max_energy_j),
            "ProgramEnergyLimitExceeded",
        ),
        (
            "events",
            int(budget["events"]),
            limits.max_events,
            "ProgramEventLimitExceeded",
        ),
        (
            "microsteps",
            int(budget["microsteps"]),
            limits.max_microsteps,
            "ProgramMicrostepLimitExceeded",
        ),
        (
            "concurrency",
            int(budget["concurrency"]),
            limits.max_concurrency,
            "ProgramConcurrencyLimitExceeded",
        ),
    )
    for label, actual, ceiling, code in ceilings:
        if actual > ceiling:
            raise MagicalProgramAdmissionError(
                code, f"Requested {label} {actual} exceeds host ceiling {ceiling}."
            )


def _check_contracts(
    program: _JSON, registered_contracts: set[tuple[str, str]]
) -> None:
    for index, node in enumerate(program["nodes"]):
        contract = node.get("contract")
        if contract is None:
            continue
        pair = (contract["contract_id"], contract["revision"])
        if pair not in registered_contracts:
            raise MagicalProgramAdmissionError(
                "ProgramUnknownContract",
                f"Node {node['node_id']!r} references unregistered contract "
                f"{pair[0]!r}@{pair[1]!r}.",
                path=f"/nodes/{index}/contract",
            )


def _check_requirement_targets(node: _JSON, index: int) -> None:
    obligations = node.get("obligations")
    if obligations is None:
        return
    inputs = set(node["inputs"])
    all_ids: list[str] = []
    for category in (
        "capabilities",
        "leases",
        "identities",
        "evidence",
        "accounting",
    ):
        for requirement_index, requirement in enumerate(obligations[category]):
            all_ids.append(requirement["requirement_id"])
            target = requirement.get("target_binding")
            if target is not None and target not in inputs:
                raise MagicalProgramAdmissionError(
                    "ProgramRequirementTargetNotInput",
                    f"Requirement {requirement['requirement_id']!r} targets "
                    f"binding {target!r}, which is not an input of node "
                    f"{node['node_id']!r}.",
                    path=(
                        f"/nodes/{index}/obligations/{category}/"
                        f"{requirement_index}/target_binding"
                    ),
                )
    _unique(
        all_ids,
        code="ProgramDuplicateRequirement",
        label="requirement ID",
        path=f"/nodes/{index}/obligations",
    )


def _check_graph(program: _JSON, limits: MagicalProgramHostLimits) -> None:
    nodes = program["nodes"]
    node_ids = _unique(
        (node["node_id"] for node in nodes),
        code="ProgramDuplicateNode",
        label="node ID",
    )
    _unique(
        (str(node["order"]) for node in nodes),
        code="ProgramDuplicateOrder",
        label="node order",
    )
    order_by_id = {node["node_id"]: node["order"] for node in nodes}

    edge_pairs: set[tuple[str, str]] = set()
    outgoing: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    incoming_count: dict[str, int] = {node_id: 0 for node_id in node_ids}
    for index, edge in enumerate(program["edges"]):
        source = edge["from"]
        target = edge["to"]
        if source not in node_ids or target not in node_ids:
            raise MagicalProgramAdmissionError(
                "ProgramEdgeUnknownNode",
                f"Edge references unknown node: {source!r} -> {target!r}.",
                path=f"/edges/{index}",
            )
        pair = (source, target)
        if pair in edge_pairs:
            raise MagicalProgramAdmissionError(
                "ProgramDuplicateEdge", f"Duplicate edge: {source!r} -> {target!r}."
            )
        edge_pairs.add(pair)
        if source == target or order_by_id[source] >= order_by_id[target]:
            raise MagicalProgramAdmissionError(
                "ProgramOrderViolation",
                "Edge must point from lower to higher deterministic order: "
                f"{source!r} -> {target!r}.",
                path=f"/edges/{index}",
            )
        outgoing[source].append(target)
        incoming_count[target] += 1

    ready = sorted(
        (node_id for node_id, count in incoming_count.items() if count == 0),
        key=lambda node_id: (order_by_id[node_id], node_id),
    )
    topological: list[str] = []
    depth: dict[str, int] = {node_id: 1 for node_id in ready}
    while ready:
        node_id = ready.pop(0)
        topological.append(node_id)
        for target in sorted(
            outgoing[node_id], key=lambda item: (order_by_id[item], item)
        ):
            depth[target] = max(depth.get(target, 1), depth[node_id] + 1)
            incoming_count[target] -= 1
            if incoming_count[target] == 0:
                ready.append(target)
                ready.sort(key=lambda item: (order_by_id[item], item))
    if len(topological) != len(nodes):
        raise MagicalProgramAdmissionError(
            "ProgramCycleDetected", "Program graph contains a cycle."
        )
    graph_depth = max(depth.values(), default=0)
    if graph_depth > limits.max_depth:
        raise MagicalProgramAdmissionError(
            "ProgramDepthLimitExceeded",
            f"Program graph depth {graph_depth} exceeds host ceiling {limits.max_depth}.",
        )

    initial_bindings = _unique(
        (value["value_id"] for value in program["values"]),
        code="ProgramDuplicateBinding",
        label="initial value binding",
    )
    producer: dict[str, str] = {}
    for node in sorted(nodes, key=lambda item: (item["order"], item["node_id"])):
        for binding in node["produces"]:
            if binding in initial_bindings or binding in producer:
                raise MagicalProgramAdmissionError(
                    "ProgramDuplicateBinding",
                    f"Binding {binding!r} has more than one producer.",
                    path=f"/nodes/{node['order']}/produces",
                )
            producer[binding] = node["node_id"]

    known_bindings = set(initial_bindings)
    for node in sorted(nodes, key=lambda item: (item["order"], item["node_id"])):
        for binding in node["inputs"]:
            if binding not in known_bindings:
                if binding in producer:
                    raise MagicalProgramAdmissionError(
                        "ProgramBindingBeforeDefinition",
                        f"Node {node['node_id']!r} reads binding {binding!r} "
                        "before its producer.",
                    )
                raise MagicalProgramAdmissionError(
                    "ProgramUnknownBinding",
                    f"Node {node['node_id']!r} reads unknown binding {binding!r}.",
                )
            source = producer.get(binding)
            if source is not None and (source, node["node_id"]) not in edge_pairs:
                raise MagicalProgramAdmissionError(
                    "ProgramMissingDataEdge",
                    f"Binding {binding!r} requires explicit edge "
                    f"{source!r} -> {node['node_id']!r}.",
                )
        known_bindings.update(node["produces"])

    for index, node in enumerate(nodes):
        _check_requirement_targets(node, index)

    _unique(
        (output["name"] for output in program["outputs"]),
        code="ProgramDuplicateOutput",
        label="program output",
    )
    for index, output in enumerate(program["outputs"]):
        if output["binding"] not in known_bindings:
            raise MagicalProgramAdmissionError(
                "ProgramOutputUnknownBinding",
                f"Output {output['name']!r} references unknown binding "
                f"{output['binding']!r}.",
                path=f"/outputs/{index}/binding",
            )


def admit_program(
    program: Mapping[str, Any],
    *,
    schema: Mapping[str, Any],
    registered_contracts: Iterable[tuple[str, str]],
    encoded_size: int = 0,
    limits: MagicalProgramHostLimits = MagicalProgramHostLimits(),
) -> _JSON:
    document = copy.deepcopy(dict(program))
    _check_finite(document)
    actual_size = encoded_size or _canonical_size(document)
    if actual_size > limits.max_bytes:
        raise MagicalProgramAdmissionError(
            "ProgramByteLimitExceeded",
            f"Program size {actual_size} exceeds host ceiling {limits.max_bytes}.",
        )
    _validate_schema(document, schema)
    _check_host_limits(document, limits)
    _check_structured_values(document, limits)
    _check_contracts(document, set(registered_contracts))
    _check_graph(document, limits)
    ordered_nodes = [
        node["node_id"]
        for node in sorted(
            document["nodes"], key=lambda item: (item["order"], item["node_id"])
        )
    ]
    return {
        "status": "Accepted",
        "artifact_kind": "MagicalProgram",
        "artifact_version": "0",
        "program_id": document["program_id"],
        "deterministic_node_order": ordered_nodes,
        "node_count": len(document["nodes"]),
        "edge_count": len(document["edges"]),
        "structured_item_count": sum(
            len(value.get("fields", value.get("items", {})))
            for value in document["values"]
            if value.get("kind") in {"record", "sequence"}
        ),
        "stable_surface_changed": False,
    }


def admit_program_bytes(
    payload: bytes,
    *,
    schema: Mapping[str, Any],
    registered_contracts: Iterable[tuple[str, str]],
    limits: MagicalProgramHostLimits = MagicalProgramHostLimits(),
) -> _JSON:
    program = decode_program(payload, limits=limits)
    return admit_program(
        program,
        schema=schema,
        registered_contracts=registered_contracts,
        encoded_size=len(payload),
        limits=limits,
    )
