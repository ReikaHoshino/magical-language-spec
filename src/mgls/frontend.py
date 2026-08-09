"""Verified public frontend for the deterministic MGLS-0 compiler.

The parser/compiler in :mod:`src.mgls.compiler` owns source lowering.  This
module adds an independent, fail-closed verification boundary for exact scalar
literals, registry-backed quantity tuples, source-to-instruction preservation,
and complete source-map coverage.
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import compiler as _core

_JSON = dict[str, Any]
MglsCompileError = _core.MglsCompileError

# The source revision is closed and registry/profile bound.  These are the
# quantity signatures admitted by the reference experimental frontend profile.
# A semantic type may intentionally project to a different physical dimension
# (for example Radius -> Length), but no spelling-based inference occurs.
_QUANTITY_TYPES: dict[str, frozenset[tuple[str, str]]] = {
    "Energy": frozenset({("Energy", "J")}),
    "Mass": frozenset({("Mass", "kg")}),
    "Length": frozenset({("Length", "m")}),
    "Distance": frozenset({("Length", "m")}),
    "Radius": frozenset({("Length", "m")}),
    "Duration": frozenset({("Time", "s")}),
    "Acceleration": frozenset({("Acceleration", "m_s2")}),
    "Momentum": frozenset({("Momentum", "kg_m_s")}),
}

_INSTRUCTION_BY_SOURCE = {
    "resolve": "ref.resolve",
    "observe": "evidence.observe",
    "calculate": "pure.calculate",
    "compare": "pure.compare",
    "rank": "pure.rank",
    "require": "assert.require",
    "effect": "effect.invoke",
}


def _raise(
    code: str,
    message: str,
    token: Any,
    *,
    stage: str,
    details: Mapping[str, Any] | None = None,
) -> None:
    raise MglsCompileError(
        code,
        message,
        start=int(token.start),
        end=max(int(token.end), int(token.start) + 1),
        stage=stage,
        details=details,
    )


def _normalized_tokens(source: str | bytes) -> tuple[str, Sequence[Any]]:
    limits = _core._limits()
    normalized_text, _ = _core._normalize(source, limits)
    tokens = _core.Lexer(
        normalized_text,
        token_limit=int(limits["tokens"]),
    ).scan()
    return normalized_text, tokens


def _preflight_types(source: str | bytes) -> None:
    """Reject exact scalar and quantity mismatches before generic parsing.

    This is intentionally a second checker over the bounded token stream.  It
    does not accept syntax or produce an artifact; the canonical parser remains
    the sole source AST owner.
    """

    _, tokens = _normalized_tokens(source)

    # Validate every explicit quantity<S,D,U> tuple, including nested record and
    # sequence element declarations.
    for index, token in enumerate(tokens[:-6]):
        if token.kind != "IDENT" or token.value != "quantity":
            continue
        if tokens[index + 1].kind != "<":
            continue
        semantic, comma1 = tokens[index + 2], tokens[index + 3]
        dimension, comma2, unit = tokens[index + 4], tokens[index + 5], tokens[index + 6]
        if not (
            semantic.kind == "IDENT"
            and comma1.kind == ","
            and dimension.kind == "IDENT"
            and comma2.kind == ","
            and unit.kind == "IDENT"
        ):
            continue
        admitted = _QUANTITY_TYPES.get(str(semantic.value))
        if admitted is None:
            _raise(
                "RegistryMismatch",
                f"Unknown quantity semantic type {semantic.value!r}.",
                semantic,
                stage="CONTRACT",
            )
        observed = (str(dimension.value), str(unit.value))
        if observed not in admitted:
            _raise(
                "DimensionError",
                "Quantity semantic type, dimension, and unit are not an admitted exact tuple.",
                dimension,
                stage="TYPECHECK",
                details={
                    "semantic_type": semantic.value,
                    "dimension": dimension.value,
                    "unit": unit.value,
                    "admitted": sorted(admitted),
                },
            )

    # Validate scalar literal token kinds independently.  The canonical parser
    # then performs the complete structured-value and graph checks.
    scalar_types = {"bool", "int", "number", "string", "null"}
    for index, token in enumerate(tokens):
        if token.kind != "IDENT" or token.value != "let":
            continue
        if index + 4 >= len(tokens):
            continue
        colon, type_token = tokens[index + 2], tokens[index + 3]
        if colon.kind != ":" or type_token.kind != "IDENT":
            continue
        declared = str(type_token.value)
        if declared not in scalar_types or tokens[index + 4].kind != "=":
            continue
        literal = tokens[index + 5]
        valid = {
            "bool": literal.kind == "IDENT" and literal.value in {"true", "false"},
            "int": literal.kind == "NUMBER" and isinstance(literal.value, int),
            "number": literal.kind == "NUMBER",
            "string": literal.kind == "STRING",
            "null": literal.kind == "IDENT" and literal.value == "null",
        }[declared]
        if not valid:
            _raise(
                "TypeError",
                f"Declared scalar type {declared!r} does not match the source literal.",
                literal,
                stage="TYPECHECK",
            )


def _parse_for_verification(source: str | bytes) -> Mapping[str, Any]:
    normalized_text, tokens = _normalized_tokens(source)
    parsed = _core.Parser(tokens).parse()
    return {"normalized_text": normalized_text, "parsed": parsed}


def _semantic_drift(message: str, parsed: Mapping[str, Any]) -> None:
    span = parsed["header_span"]
    raise MglsCompileError(
        "SourceSemanticDrift",
        message,
        start=span.start,
        end=span.end,
        stage="LOWERING",
    )


def _verify_semantic_projection(
    parsed: Mapping[str, Any],
    program: Mapping[str, Any],
) -> None:
    header = parsed["header"]
    fixed = {
        "artifact_kind": "MagicalProgram",
        "artifact_version": "0",
        "contract": {"contract_id": "magical-program", "revision": "0"},
        "stability": "experimental",
        "program_id": header["program_id"],
        "compatibility": {
            "registry_id": header["registry_id"],
            "registry_revision": header["registry_revision"],
            "profile_id": header["profile_id"],
            "profile_revision": header["profile_revision"],
        },
        "budget": header["budget"],
    }
    for field, expected in fixed.items():
        if program.get(field) != expected:
            _semantic_drift(
                f"Lowering changed explicit or fixed field {field!r}.", parsed
            )

    source_values = {item.name: item for item in parsed["values"]}
    emitted_values = {
        str(item.get("value_id")): item for item in program.get("values", [])
    }
    if set(source_values) != set(emitted_values):
        _semantic_drift("Lowering changed the source value namespace.", parsed)
    for name, source_value in source_values.items():
        if emitted_values[name] != source_value.artifact:
            _semantic_drift(f"Lowering changed value {name!r}.", parsed)

    source_nodes = {item.name: item for item in parsed["nodes"]}
    emitted_nodes = {str(item.get("node_id")): item for item in program.get("nodes", [])}
    if set(source_nodes) != set(emitted_nodes):
        _semantic_drift("Lowering changed the source node namespace.", parsed)
    for order, source_node in enumerate(parsed["nodes"]):
        emitted = emitted_nodes[source_node.name]
        expected_instruction = _INSTRUCTION_BY_SOURCE[source_node.kind]
        if emitted.get("order") != order or emitted.get("instruction") != expected_instruction:
            _semantic_drift(
                f"Lowering changed node {source_node.name!r} instruction or order.",
                parsed,
            )
        if emitted.get("inputs") != source_node.inputs or emitted.get("produces") != source_node.produced:
            _semantic_drift(
                f"Lowering changed node {source_node.name!r} bindings.", parsed
            )
        if source_node.kind in {"effect", "observe"}:
            if emitted.get("contract") != source_node.payload.get("contract"):
                _semantic_drift(
                    f"Lowering changed node {source_node.name!r} contract.", parsed
                )
            if emitted.get("obligations") != source_node.payload.get("obligations"):
                _semantic_drift(
                    f"Lowering changed node {source_node.name!r} obligations.", parsed
                )

    expected_outputs = [
        {"name": item.name, "binding": item.binding, "kind": item.kind}
        for item in parsed["outputs"]
    ]
    if program.get("outputs") != expected_outputs:
        _semantic_drift("Lowering changed source outputs.", parsed)


def _verify_source_map(
    parsed: Mapping[str, Any],
    program: Mapping[str, Any],
    source_map: Mapping[str, Any],
) -> None:
    entries = source_map.get("entries")
    if not isinstance(entries, list):
        raise MglsCompileError(
            "NormalizationFailed",
            "MGLS source map has no entry array.",
            start=0,
            end=1,
            stage="SOURCE_MAP",
        )
    entry_ids = {
        str(item.get("entry_id"))
        for item in entries
        if isinstance(item, Mapping)
    }
    required = {
        "map:header:program",
        "map:header:fixed-contract",
        *(f"map:value:{item.name}" for item in parsed["values"]),
        *(f"map:node:{item.name}" for item in parsed["nodes"]),
        *(f"map:output:{item.name}" for item in parsed["outputs"]),
    }
    missing = sorted(required - entry_ids)
    if missing:
        span = parsed["header_span"]
        raise MglsCompileError(
            "NormalizationFailed",
            f"MGLS source map omits required mappings: {missing!r}.",
            start=span.start,
            end=span.end,
            stage="SOURCE_MAP",
        )
    target = source_map.get("target", {})
    if target.get("program_id") != program.get("program_id"):
        span = parsed["header_span"]
        raise MglsCompileError(
            "NormalizationFailed",
            "MGLS source map target does not identify the emitted program.",
            start=span.start,
            end=span.end,
            stage="SOURCE_MAP",
        )


def _verify_compilation(source: str | bytes, result: Mapping[str, Any]) -> None:
    verification = _parse_for_verification(source)
    parsed = verification["parsed"]
    program = result.get("program")
    source_map = result.get("source_map")
    if not isinstance(program, Mapping):
        _semantic_drift("Compiler returned no MagicalProgram artifact.", parsed)
    if not isinstance(source_map, Mapping):
        span = parsed["header_span"]
        raise MglsCompileError(
            "NormalizationFailed",
            "Compiler returned no MGLS source map.",
            start=span.start,
            end=span.end,
            stage="SOURCE_MAP",
        )
    _verify_semantic_projection(parsed, program)
    _verify_source_map(parsed, program, source_map)


def compile_source(source: str | bytes) -> _JSON:
    _preflight_types(source)
    result = _core.compile_source(source)
    _verify_compilation(source, result)
    return copy.deepcopy(result)


def check_source(source: str | bytes) -> _JSON:
    try:
        compiled = compile_source(source)
    except MglsCompileError as error:
        return {
            "status": "Rejected",
            "program": None,
            "source_map": None,
            "diagnostics": [error.diagnostic()],
        }
    return {
        "status": "Accepted",
        "program_id": compiled["program"]["program_id"],
        "source_contract": compiled["source_contract"],
        "target_admission": compiled["target_admission"],
        "diagnostics": [],
    }


def compile_file(path: str | Path) -> _JSON:
    candidate = Path(path)
    if candidate.is_symlink():
        raise MglsCompileError(
            "InputSymlinkRejected",
            "MGLS source input may not be a symbolic link.",
            start=0,
            end=1,
            stage="INGRESS",
        )
    return compile_source(candidate.read_bytes())


def canonical_compilation_bytes(result: Mapping[str, Any]) -> bytes:
    return _core.canonical_compilation_bytes(result)


__all__ = [
    "MglsCompileError",
    "canonical_compilation_bytes",
    "check_source",
    "compile_file",
    "compile_source",
]
