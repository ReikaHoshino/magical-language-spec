"""Strict deterministic compiler from MGLS-0 source to MagicalProgram-0."""
from __future__ import annotations

import copy
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from jsonschema import Draft202012Validator

from src.artifacts.magical_program import (
    MagicalProgramAdmissionError,
    MagicalProgramHostLimits,
    admit_program,
)
from src.artifacts.magical_program_values import value_signature
from src.resources import resource_path
from tools.source_text_normalization import (
    SourceTextDiagnostic,
    normalize_source_text,
)

_JSON = dict[str, Any]
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_CONTRACT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_FORBIDDEN = {
    "import",
    "include",
    "module",
    "package",
    "use",
    "macro",
    "eval",
    "reflection",
    "plugin",
    "native",
    "python",
    "wasm",
    "if",
    "match",
    "switch",
    "for",
    "while",
    "loop",
    "repeat",
    "recurse",
    "async",
    "await",
    "spawn",
    "thread",
    "parallel",
    "set",
    "mutate",
    "write",
    "path",
    "file",
    "filesystem",
    "network",
    "http",
    "environment",
    "shell",
}
_PUNCTUATION = set("{}()[]:;,<>=")
_CALCULATE = {"add", "subtract", "multiply", "divide", "minimum", "maximum"}
_COMPARE = {
    "equal",
    "not_equal",
    "less",
    "less_equal",
    "greater",
    "greater_equal",
}
_OUTPUT_KINDS = {"value", "reference", "evidence", "effect_result", "event", "artifact"}


@dataclass(frozen=True)
class Token:
    kind: str
    value: Any
    lexeme: str
    start: int
    end: int


@dataclass(frozen=True)
class Span:
    start: int
    end: int

    def payload(self) -> _JSON:
        return {"start": self.start, "end": self.end}


@dataclass(frozen=True)
class ContractSpec:
    contract_id: str
    revision: str
    instruction: str
    inputs: tuple[str, ...]
    output: str
    required_capabilities: frozenset[str] = frozenset()
    required_leases: frozenset[str] = frozenset()
    required_identities: frozenset[str] = frozenset()
    required_evidence: frozenset[str] = frozenset()
    required_accounting: frozenset[str] = frozenset()
    emitted_events: int = 0


_CONTRACTS: dict[tuple[str, str], ContractSpec] = {
    ("generic.transition", "1"): ContractSpec(
        "generic.transition",
        "1",
        "effect.invoke",
        ("reference", "literal:string"),
        "effect_result",
        frozenset({"capability.transition"}),
        frozenset({"lease.transition"}),
        frozenset({"identity.target"}),
        frozenset(),
        frozenset({"accounting.transition"}),
        1,
    ),
    ("generic.observe", "1"): ContractSpec(
        "generic.observe",
        "1",
        "evidence.observe",
        ("reference",),
        "evidence",
        frozenset({"capability.observe"}),
        frozenset(),
        frozenset({"identity.subject"}),
        frozenset({"evidence.subject"}),
        frozenset({"accounting.observe"}),
        1,
    ),
    ("controller.boundary-reflection", "1"): ContractSpec(
        "controller.boundary-reflection",
        "1",
        "effect.invoke",
        (
            "reference",
            "reference",
            "record:BoundaryReflectionModel",
            "record:BoundaryReflectionPolicy",
            "record:BoundaryReflectionPublication",
        ),
        "effect_result",
        frozenset({"capability.boundary-actuation"}),
        frozenset({"lease.boundary-controller"}),
        frozenset({"identity.boundary-target", "identity.reaction-anchor"}),
        frozenset(),
        frozenset({"accounting.boundary-momentum-energy"}),
        1,
    ),
}


class MglsCompileError(RuntimeError):
    """Fatal source diagnostic. No partial program may escape this exception."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        start: int = 0,
        end: int | None = None,
        stage: str = "SOURCE",
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.start = max(0, start)
        self.end = max(self.start, self.start + 1 if end is None else end)
        self.stage = stage
        self.details = copy.deepcopy(dict(details or {}))

    def diagnostic(self) -> _JSON:
        payload: _JSON = {
            "stage": self.stage,
            "code": self.code,
            "severity": "fatal",
            "message": str(self),
            "normalized_span": {"start": self.start, "end": self.end},
        }
        if self.details:
            payload["details"] = copy.deepcopy(self.details)
        return payload


class Lexer:
    def __init__(self, text: str, *, token_limit: int = 65_536) -> None:
        self.text = text
        self.token_limit = token_limit
        self.index = 0
        self.tokens: list[Token] = []

    def _append(self, token: Token) -> None:
        self.tokens.append(token)
        if len(self.tokens) > self.token_limit:
            raise MglsCompileError(
                "InputLimitExceeded",
                f"MGLS token count exceeds ceiling {self.token_limit}.",
                start=token.start,
                end=token.end,
                stage="LEX",
            )

    def _string(self) -> Token:
        start = self.index
        self.index += 1
        escaped = False
        while self.index < len(self.text):
            char = self.text[self.index]
            if char == "\n" and not escaped:
                raise MglsCompileError(
                    "ParseError",
                    "MGLS strings cannot contain an unescaped line break.",
                    start=start,
                    end=self.index,
                    stage="LEX",
                )
            if char == '"' and not escaped:
                self.index += 1
                lexeme = self.text[start : self.index]
                try:
                    value = json.loads(lexeme)
                except (json.JSONDecodeError, UnicodeDecodeError) as error:
                    raise MglsCompileError(
                        "ParseError",
                        "Invalid JSON-compatible MGLS string literal.",
                        start=start,
                        end=self.index,
                        stage="LEX",
                    ) from error
                if not isinstance(value, str) or "\x00" in value:
                    raise MglsCompileError(
                        "UnsupportedSourceCharacter",
                        "MGLS strings must contain supported Unicode scalar values.",
                        start=start,
                        end=self.index,
                        stage="LEX",
                    )
                return Token("STRING", value, lexeme, start, self.index)
            if char == "\\" and not escaped:
                escaped = True
            else:
                escaped = False
            self.index += 1
        raise MglsCompileError(
            "ParseError",
            "Unterminated MGLS string literal.",
            start=start,
            end=len(self.text),
            stage="LEX",
        )

    def _number(self) -> Token:
        start = self.index
        match = re.match(
            r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?",
            self.text[start:],
        )
        assert match is not None
        lexeme = match.group(0)
        self.index += len(lexeme)
        try:
            if "." in lexeme or "e" in lexeme.lower():
                value: int | float = float(lexeme)
            else:
                value = int(lexeme)
        except ValueError as error:
            raise MglsCompileError(
                "ParseError",
                "Invalid MGLS numeric literal.",
                start=start,
                end=self.index,
                stage="LEX",
            ) from error
        if isinstance(value, float) and not math.isfinite(value):
            raise MglsCompileError(
                "ParseError",
                "MGLS numeric literals must be finite.",
                start=start,
                end=self.index,
                stage="LEX",
            )
        return Token("NUMBER", value, lexeme, start, self.index)

    def scan(self) -> list[Token]:
        while self.index < len(self.text):
            char = self.text[self.index]
            if char.isspace():
                self.index += 1
                continue
            if self.text.startswith("//", self.index):
                newline = self.text.find("\n", self.index + 2)
                self.index = len(self.text) if newline < 0 else newline + 1
                continue
            if self.text.startswith("/*", self.index):
                start = self.index
                end = self.text.find("*/", self.index + 2)
                if end < 0:
                    raise MglsCompileError(
                        "ParseError",
                        "Unterminated non-nesting MGLS block comment.",
                        start=start,
                        end=len(self.text),
                        stage="LEX",
                    )
                if "/*" in self.text[self.index + 2 : end]:
                    raise MglsCompileError(
                        "ParseError",
                        "MGLS block comments do not nest.",
                        start=start,
                        end=end + 2,
                        stage="LEX",
                    )
                self.index = end + 2
                continue
            if char == '"':
                self._append(self._string())
                continue
            if char in _PUNCTUATION:
                start = self.index
                self.index += 1
                self._append(Token(char, char, char, start, self.index))
                continue
            if char.isalpha() or char == "_":
                start = self.index
                self.index += 1
                while self.index < len(self.text) and (
                    self.text[self.index].isalnum() or self.text[self.index] == "_"
                ):
                    if not self.text[self.index].isascii():
                        break
                    self.index += 1
                lexeme = self.text[start : self.index]
                if not lexeme.isascii() or not _IDENTIFIER_RE.fullmatch(lexeme):
                    raise MglsCompileError(
                        "UnsupportedSourceCharacter",
                        "MGLS identifiers are ASCII only.",
                        start=start,
                        end=self.index,
                        stage="LEX",
                    )
                self._append(Token("IDENT", lexeme, lexeme, start, self.index))
                continue
            if char == "-" or char.isdigit():
                self._append(self._number())
                continue
            raise MglsCompileError(
                "ParseError",
                f"Unexpected MGLS character {char!r}.",
                start=self.index,
                end=self.index + 1,
                stage="LEX",
            )
        self._append(Token("EOF", None, "", len(self.text), len(self.text)))
        return self.tokens


@dataclass
class ParsedValue:
    name: str
    signature: str
    artifact: _JSON
    span: Span


@dataclass
class ParsedNode:
    name: str
    after: list[str]
    kind: str
    produced: list[str]
    inputs: list[str]
    payload: _JSON
    span: Span


@dataclass
class ParsedOutput:
    name: str
    kind: str
    binding: str
    span: Span


class Parser:
    def __init__(self, tokens: Sequence[Token]) -> None:
        self.tokens = tokens
        self.index = 0

    @property
    def current(self) -> Token:
        return self.tokens[self.index]

    def _advance(self) -> Token:
        token = self.current
        if token.kind != "EOF":
            self.index += 1
        return token

    def _error(self, message: str, *, code: str = "ParseError", stage: str = "PARSE") -> MglsCompileError:
        token = self.current
        return MglsCompileError(
            code,
            message,
            start=token.start,
            end=max(token.end, token.start + 1),
            stage=stage,
        )

    def _accept(self, kind_or_value: str) -> Token | None:
        token = self.current
        if token.kind == kind_or_value or token.value == kind_or_value:
            self._advance()
            return token
        return None

    def _expect(self, kind_or_value: str, message: str | None = None) -> Token:
        token = self._accept(kind_or_value)
        if token is None:
            raise self._error(message or f"Expected {kind_or_value!r}.")
        return token

    def _keyword(self, value: str) -> Token:
        token = self.current
        if token.kind == "IDENT" and token.value == value:
            return self._advance()
        if token.kind == "IDENT" and token.value in _FORBIDDEN:
            raise self._error(
                f"MGLS-0 forbids construct {token.value!r}.",
                code="UnsupportedSemanticExtension",
            )
        raise self._error(f"Expected keyword {value!r}.")

    def _identifier(self) -> Token:
        token = self._expect("IDENT", "Expected an ASCII MGLS identifier.")
        if token.value in _FORBIDDEN:
            raise MglsCompileError(
                "UnsupportedSemanticExtension",
                f"MGLS-0 forbids construct {token.value!r}.",
                start=token.start,
                end=token.end,
                stage="PARSE",
            )
        return token

    def _identity_string(self) -> Token:
        token = self._expect("STRING", "Expected a quoted contract/identity string.")
        if not _CONTRACT_ID_RE.fullmatch(token.value):
            raise MglsCompileError(
                "StructuredInputInvalid",
                f"Invalid MGLS identity {token.value!r}.",
                start=token.start,
                end=token.end,
                stage="STATIC",
            )
        return token

    def _number(self, *, integer: bool = False) -> Token:
        token = self._expect("NUMBER", "Expected a finite numeric literal.")
        if integer and not isinstance(token.value, int):
            raise MglsCompileError(
                "TypeError",
                "This MGLS field requires an integer literal.",
                start=token.start,
                end=token.end,
                stage="TYPECHECK",
            )
        return token

    def _header(self) -> tuple[_JSON, Span]:
        start = self.current.start
        self._keyword("mgls")
        version = self._expect("STRING", "Expected MGLS source revision string.")
        self._expect(";")
        if version.value != "0":
            raise MglsCompileError(
                "SpecVersionIncompatible",
                f"Unsupported MGLS source revision {version.value!r}.",
                start=version.start,
                end=version.end,
                stage="INGRESS",
            )
        self._keyword("source")
        source_id = self._identity_string()
        self._expect(";")
        self._keyword("program")
        program_id = self._identity_string()
        self._expect(";")
        self._keyword("registry")
        registry_id = self._identity_string()
        self._keyword("revision")
        registry_revision = self._identity_string()
        self._expect(";")
        self._keyword("profile")
        profile_id = self._identity_string()
        self._keyword("revision")
        profile_revision = self._identity_string()
        self._expect(";")
        self._keyword("budget")
        self._expect("{")
        self._keyword("energy")
        energy = self._number()
        self._expect(";")
        self._keyword("events")
        events = self._number(integer=True)
        self._expect(";")
        self._keyword("microsteps")
        microsteps = self._number(integer=True)
        self._expect(";")
        self._keyword("concurrency")
        concurrency = self._number(integer=True)
        self._expect(";")
        end = self._expect("}").end
        if any(value.value < 0 for value in (energy, events, microsteps)) or concurrency.value < 1:
            raise MglsCompileError(
                "InputLimitExceeded",
                "MGLS budgets must be non-negative and concurrency at least one.",
                start=energy.start,
                end=end,
                stage="LIMIT",
            )
        return (
            {
                "version": "0",
                "source_id": source_id.value,
                "program_id": program_id.value,
                "registry_id": registry_id.value,
                "registry_revision": registry_revision.value,
                "profile_id": profile_id.value,
                "profile_revision": profile_revision.value,
                "budget": {
                    "energy_j": energy.value,
                    "events": events.value,
                    "microsteps": microsteps.value,
                    "concurrency": concurrency.value,
                },
            },
            Span(start, end),
        )

    def _type(self) -> tuple[str, _JSON]:
        token = self._identifier()
        scalar = {
            "bool": "literal:boolean",
            "int": "literal:number",
            "number": "literal:number",
            "string": "literal:string",
            "null": "literal:null",
        }
        if token.value in scalar:
            return scalar[token.value], {"form": token.value}
        if token.value == "quantity":
            self._expect("<")
            semantic = self._identifier().value
            self._expect(",")
            dimension = self._identifier().value
            self._expect(",")
            unit = self._identifier().value
            self._expect(">")
            return "quantity", {
                "form": "quantity",
                "semantic_type": semantic,
                "dimension": dimension,
                "unit": unit,
            }
        if token.value == "record":
            self._expect("<")
            type_id = self._identifier().value
            self._expect(">")
            return f"record:{type_id}", {"form": "record", "type_id": type_id}
        if token.value == "sequence":
            self._expect("<")
            element_signature, element_type = self._type()
            self._expect(">")
            element = self._element_signature(element_signature, element_type)
            return f"sequence:{element}", {
                "form": "sequence",
                "element_signature": element,
                "element_type": element_type,
            }
        raise MglsCompileError(
            "TypeError",
            f"Unknown MGLS type {token.value!r}.",
            start=token.start,
            end=token.end,
            stage="TYPECHECK",
        )

    @staticmethod
    def _element_signature(signature: str, type_info: Mapping[str, Any]) -> str:
        if type_info["form"] == "quantity":
            return (
                f"quantity:{type_info['semantic_type']}:"
                f"{type_info['dimension']}:{type_info['unit']}"
            )
        return signature

    def _scalar_literal(self, type_info: Mapping[str, Any]) -> _JSON:
        form = type_info["form"]
        token = self.current
        if form == "string":
            value = self._expect("STRING").value
        elif form == "bool":
            literal = self._identifier()
            if literal.value not in {"true", "false"}:
                raise MglsCompileError(
                    "TypeError",
                    "Expected true or false.",
                    start=literal.start,
                    end=literal.end,
                    stage="TYPECHECK",
                )
            value = literal.value == "true"
        elif form == "null":
            literal = self._identifier()
            if literal.value != "null":
                raise MglsCompileError(
                    "TypeError",
                    "Expected null.",
                    start=literal.start,
                    end=literal.end,
                    stage="TYPECHECK",
                )
            value = None
        elif form in {"int", "number"}:
            number = self._number(integer=form == "int")
            value = number.value
        else:
            raise self._error("Expected a scalar type.", code="TypeError", stage="TYPECHECK")
        return {"kind": "literal", "value": value}

    def _constant(self, signature: str, type_info: Mapping[str, Any]) -> _JSON:
        form = type_info["form"]
        if form in {"bool", "int", "number", "string", "null"}:
            return self._scalar_literal(type_info)
        if form == "quantity":
            self._keyword("quantity")
            self._expect("(")
            value = self._number().value
            self._expect(")")
            return {
                "kind": "quantity",
                "semantic_type": type_info["semantic_type"],
                "dimension": type_info["dimension"],
                "unit": type_info["unit"],
                "value": value,
            }
        if form == "record":
            self._keyword("record")
            self._expect("<")
            observed = self._identifier()
            self._expect(">")
            if observed.value != type_info["type_id"]:
                raise MglsCompileError(
                    "TypeError",
                    "Record declaration and constructor type must match exactly.",
                    start=observed.start,
                    end=observed.end,
                    stage="TYPECHECK",
                )
            self._expect("{")
            fields: _JSON = {}
            while not self._accept("}"):
                name = self._identifier()
                if name.value in fields:
                    raise MglsCompileError(
                        "DuplicateBinding",
                        f"Duplicate record field {name.value!r}.",
                        start=name.start,
                        end=name.end,
                        stage="STATIC",
                    )
                self._expect(":")
                field_signature, field_type = self._type()
                self._expect("=")
                fields[name.value] = self._constant(field_signature, field_type)
                self._expect(";")
            return {"kind": "record", "type_id": type_info["type_id"], "fields": fields}
        if form == "sequence":
            self._keyword("sequence")
            self._expect("<")
            observed_signature, observed_type = self._type()
            self._expect(">")
            observed_element = self._element_signature(observed_signature, observed_type)
            if observed_element != type_info["element_signature"]:
                raise MglsCompileError(
                    "TypeError",
                    "Sequence declaration and constructor element type must match exactly.",
                    start=self.current.start,
                    end=self.current.end,
                    stage="TYPECHECK",
                )
            self._expect("[")
            items: list[_JSON] = []
            if not self._accept("]"):
                while True:
                    items.append(self._constant(observed_signature, observed_type))
                    if self._accept("]"):
                        break
                    self._expect(",")
                    if self._accept("]"):
                        break
            return {
                "kind": "sequence",
                "element_type": type_info["element_signature"],
                "items": items,
            }
        raise self._error("Unsupported constant type.", code="TypeError", stage="TYPECHECK")

    def _value(self) -> ParsedValue:
        start = self.current.start
        keyword = self._identifier()
        if keyword.value == "let":
            name = self._identifier()
            self._expect(":")
            signature, type_info = self._type()
            self._expect("=")
            artifact = self._constant(signature, type_info)
            end = self._expect(";").end
            artifact["value_id"] = name.value
            return ParsedValue(name.value, signature, artifact, Span(start, end))
        if keyword.value == "selector":
            name = self._identifier()
            self._expect("=")
            self._expect("{")
            selector: _JSON = {}
            while True:
                field = self._identifier()
                self._expect("=")
                token = self.current
                if token.kind == "STRING":
                    value = self._advance().value
                elif token.kind == "NUMBER":
                    value = self._advance().value
                elif token.kind == "IDENT" and token.value in {"true", "false"}:
                    value = self._advance().value == "true"
                else:
                    raise self._error("Selector values must be scalar.", code="TypeError", stage="TYPECHECK")
                if field.value in selector:
                    raise MglsCompileError(
                        "DuplicateBinding",
                        f"Duplicate selector field {field.value!r}.",
                        start=field.start,
                        end=field.end,
                        stage="STATIC",
                    )
                selector[field.value] = value
                if self._accept("}"):
                    break
                self._expect(",")
                if self._accept("}"):
                    break
            end = self._expect(";").end
            return ParsedValue(
                name.value,
                "selector",
                {"value_id": name.value, "kind": "selector", "selector": selector},
                Span(start, end),
            )
        if keyword.value in {"reference_hint", "evidence_hint"}:
            name = self._identifier()
            self._expect("=")
            handle = self._identity_string()
            self._keyword("revision")
            revision = self._identity_string()
            end = self._expect(";").end
            return ParsedValue(
                name.value,
                keyword.value,
                {
                    "value_id": name.value,
                    "kind": keyword.value,
                    "handle_id": handle.value,
                    "revision": revision.value,
                },
                Span(start, end),
            )
        raise MglsCompileError(
            "ParseError",
            f"Unexpected declaration {keyword.value!r}; values must precede nodes.",
            start=keyword.start,
            end=keyword.end,
            stage="PARSE",
        )

    def _binding_list(self) -> list[str]:
        items: list[str] = []
        if self.current.kind == ")":
            return items
        while True:
            items.append(self._identifier().value)
            if not self._accept(","):
                return items

    def _obligations(self) -> _JSON:
        self._keyword("requires")
        self._expect("{")
        result: _JSON = {
            "capabilities": [],
            "leases": [],
            "identities": [],
            "evidence": [],
            "accounting": [],
        }
        while not (self.current.kind == "IDENT" and self.current.value == "resources"):
            keyword = self._identifier()
            requirement_id = self._identity_string().value
            item: _JSON = {"requirement_id": requirement_id}
            if keyword.value == "capability":
                self._keyword("on")
                item["target_binding"] = self._identifier().value
                self._keyword("effect")
                item["effect"] = self._identity_string().value
                if self.current.kind == "IDENT" and self.current.value == "scope":
                    self._advance()
                    item["scope"] = self._identity_string().value
                result["capabilities"].append(item)
            elif keyword.value == "lease":
                self._keyword("on")
                item["target_binding"] = self._identifier().value
                self._keyword("mode")
                item["mode"] = self._identity_string().value
                if self.current.kind == "IDENT" and self.current.value == "scope":
                    self._advance()
                    item["scope"] = self._identity_string().value
                result["leases"].append(item)
            elif keyword.value == "identity":
                self._keyword("on")
                item["target_binding"] = self._identifier().value
                result["identities"].append(item)
            elif keyword.value == "evidence":
                self._keyword("on")
                item["target_binding"] = self._identifier().value
                self._keyword("kind")
                item["kind"] = self._identity_string().value
                result["evidence"].append(item)
            elif keyword.value == "accounting":
                self._keyword("kind")
                item["kind"] = self._identity_string().value
                if self.current.kind == "IDENT" and self.current.value == "on":
                    self._advance()
                    item["target_binding"] = self._identifier().value
                result["accounting"].append(item)
            else:
                raise MglsCompileError(
                    "UnsupportedSemanticExtension",
                    f"Unknown obligation form {keyword.value!r}.",
                    start=keyword.start,
                    end=keyword.end,
                    stage="EFFECTCHECK",
                )
            self._expect(";")
        self._keyword("resources")
        self._expect("{")
        self._keyword("energy")
        energy = self._number().value
        self._expect(";")
        self._keyword("matter")
        matter = self._number().value
        self._expect(";")
        self._keyword("events")
        events = self._number(integer=True).value
        self._expect(";")
        self._expect("}")
        self._expect("}")
        if energy < 0 or matter < 0 or events < 0:
            raise self._error(
                "Obligation resources must be non-negative.",
                code="ConservationProofFailure",
                stage="EFFECTCHECK",
            )
        result["resources"] = {
            "energy_j": energy,
            "matter_kg": matter,
            "events": events,
        }
        return result

    def _node(self) -> ParsedNode:
        start = self._keyword("node").start
        name = self._identifier()
        after: list[str] = []
        if self.current.kind == "IDENT" and self.current.value == "after":
            self._advance()
            while True:
                after.append(self._identifier().value)
                if not self._accept(","):
                    break
        self._expect(":")
        kind = self._identifier()
        inputs: list[str]
        produced: list[str]
        payload: _JSON = {}
        if kind.value == "resolve":
            produced = [self._identifier().value]
            self._keyword("from")
            inputs = [self._identifier().value]
        elif kind.value in {"calculate", "compare"}:
            produced = [self._identifier().value]
            self._expect("=")
            operator = self._identifier()
            allowed = _CALCULATE if kind.value == "calculate" else _COMPARE
            if operator.value not in allowed:
                raise MglsCompileError(
                    "EffectMismatch",
                    f"Unsupported {kind.value} operator {operator.value!r}.",
                    start=operator.start,
                    end=operator.end,
                    stage="TYPECHECK",
                )
            self._expect("(")
            inputs = self._binding_list()
            self._expect(")")
            payload["operator"] = operator.value
        elif kind.value == "rank":
            produced = [self._identifier().value]
            self._expect("=")
            direction = self._identifier()
            if direction.value not in {"ascending", "descending"}:
                raise MglsCompileError(
                    "EffectMismatch",
                    "Rank direction must be ascending or descending.",
                    start=direction.start,
                    end=direction.end,
                    stage="TYPECHECK",
                )
            self._expect("(")
            inputs = [self._identifier().value]
            self._expect(")")
            payload["direction"] = direction.value
        elif kind.value == "require":
            inputs = [self._identifier().value]
            produced = []
            self._keyword("else")
            diagnostic = self._identity_string()
            payload["diagnostic_code"] = diagnostic.value
        elif kind.value in {"observe", "effect"}:
            produced = [self._identifier().value]
            self._expect("=")
            self._keyword("invoke")
            contract = self._identity_string()
            self._keyword("revision")
            revision = self._identity_string()
            self._expect("(")
            inputs = self._binding_list()
            self._expect(")")
            payload["contract"] = {
                "contract_id": contract.value,
                "revision": revision.value,
            }
            payload["obligations"] = self._obligations()
        else:
            code = "UnsupportedSemanticExtension" if kind.value in _FORBIDDEN else "ParseError"
            raise MglsCompileError(
                code,
                f"Unknown MGLS node form {kind.value!r}.",
                start=kind.start,
                end=kind.end,
                stage="PARSE",
            )
        end = self._expect(";").end
        return ParsedNode(
            name.value,
            after,
            kind.value,
            produced,
            inputs,
            payload,
            Span(start, end),
        )

    def _output(self) -> ParsedOutput:
        start = self._keyword("output").start
        name = self._identity_string()
        kind = self._identifier()
        if kind.value not in _OUTPUT_KINDS:
            raise MglsCompileError(
                "EffectMismatch",
                f"Unknown MGLS output kind {kind.value!r}.",
                start=kind.start,
                end=kind.end,
                stage="OUTPUT",
            )
        self._keyword("from")
        binding = self._identifier()
        end = self._expect(";").end
        return ParsedOutput(name.value, kind.value, binding.value, Span(start, end))

    def parse(self) -> _JSON:
        header, header_span = self._header()
        values: list[ParsedValue] = []
        nodes: list[ParsedNode] = []
        outputs: list[ParsedOutput] = []
        phase = "values"
        while self.current.kind != "EOF":
            if self.current.kind != "IDENT":
                raise self._error("Expected a declaration.")
            keyword = self.current.value
            if keyword in _FORBIDDEN:
                raise self._error(
                    f"MGLS-0 forbids construct {keyword!r}.",
                    code="UnsupportedSemanticExtension",
                )
            if keyword in {"let", "selector", "reference_hint", "evidence_hint"}:
                if phase != "values":
                    raise self._error("MGLS values must precede nodes and outputs.")
                values.append(self._value())
            elif keyword == "node":
                if phase == "outputs":
                    raise self._error("MGLS nodes must precede outputs.")
                phase = "nodes"
                nodes.append(self._node())
            elif keyword == "output":
                phase = "outputs"
                outputs.append(self._output())
            else:
                raise self._error(f"Unexpected top-level declaration {keyword!r}.")
        if not nodes or not outputs:
            raise MglsCompileError(
                "StructuredInputInvalid",
                "MGLS source requires at least one node and one output.",
                start=header_span.start,
                end=header_span.end,
                stage="STATIC",
            )
        return {
            "header": header,
            "header_span": header_span,
            "values": values,
            "nodes": nodes,
            "outputs": outputs,
        }


class Compiler:
    def __init__(
        self,
        parsed: Mapping[str, Any],
        *,
        normalized_text: str,
        limits: Mapping[str, Any],
    ) -> None:
        self.parsed = parsed
        self.normalized_text = normalized_text
        self.limits = limits
        self.signatures: dict[str, str] = {}
        self.producer: dict[str, str] = {}
        self.node_order: dict[str, int] = {}
        self.map_entries: list[_JSON] = []

    def _duplicate(self, name: str, span: Span, label: str) -> None:
        raise MglsCompileError(
            "DuplicateBinding",
            f"Duplicate MGLS {label} {name!r}.",
            start=span.start,
            end=span.end,
            stage="STATIC",
        )

    def _map(self, entry_id: str, span: Span, relation: str, section: str, target_id: str, *, field: str | None = None, binding: str | None = None) -> None:
        target: _JSON = {"section": section, "id": target_id}
        if field is not None:
            target["field"] = field
        if binding is not None:
            target["binding"] = binding
        self.map_entries.append(
            {
                "entry_id": entry_id,
                "source_span": span.payload(),
                "relation": relation,
                "target": target,
            }
        )

    def _require_known(self, binding: str, node: ParsedNode) -> str:
        signature = self.signatures.get(binding)
        if signature is None:
            raise MglsCompileError(
                "UnresolvedName",
                f"Node {node.name!r} references unresolved binding {binding!r}.",
                start=node.span.start,
                end=node.span.end,
                stage="STATIC",
            )
        return signature

    @staticmethod
    def _requirement_ids(obligations: Mapping[str, Any], category: str) -> set[str]:
        return {str(item["requirement_id"]) for item in obligations[category]}

    def _check_contract(self, node: ParsedNode, instruction: str, input_signatures: tuple[str, ...]) -> ContractSpec:
        contract = node.payload["contract"]
        key = (contract["contract_id"], contract["revision"])
        spec = _CONTRACTS.get(key)
        if spec is None:
            raise MglsCompileError(
                "RegistryMismatch",
                f"Unknown MGLS contract {key[0]!r}@{key[1]!r}.",
                start=node.span.start,
                end=node.span.end,
                stage="CONTRACT",
            )
        if spec.instruction != instruction or spec.inputs != input_signatures:
            raise MglsCompileError(
                "EffectMismatch",
                f"Contract {key[0]!r}@{key[1]!r} expects {spec.inputs!r} under "
                f"{spec.instruction}, observed {input_signatures!r} under {instruction}.",
                start=node.span.start,
                end=node.span.end,
                stage="EFFECTCHECK",
            )
        obligations = node.payload["obligations"]
        missing_authority = (
            spec.required_capabilities - self._requirement_ids(obligations, "capabilities")
        ) | (spec.required_leases - self._requirement_ids(obligations, "leases")) | (
            spec.required_identities - self._requirement_ids(obligations, "identities")
        ) | (spec.required_evidence - self._requirement_ids(obligations, "evidence"))
        if missing_authority:
            raise MglsCompileError(
                "StaticAuthorityError",
                f"Missing required authority/evidence declarations: {sorted(missing_authority)!r}.",
                start=node.span.start,
                end=node.span.end,
                stage="EFFECTCHECK",
            )
        missing_accounting = spec.required_accounting - self._requirement_ids(
            obligations, "accounting"
        )
        if missing_accounting:
            raise MglsCompileError(
                "ConservationProofFailure",
                f"Missing required accounting declarations: {sorted(missing_accounting)!r}.",
                start=node.span.start,
                end=node.span.end,
                stage="EFFECTCHECK",
            )
        all_ids: list[str] = []
        for category in ("capabilities", "leases", "identities", "evidence", "accounting"):
            for requirement in obligations[category]:
                all_ids.append(requirement["requirement_id"])
                target = requirement.get("target_binding")
                if target is not None and target not in node.inputs:
                    raise MglsCompileError(
                        "StaticAuthorityError",
                        f"Requirement {requirement['requirement_id']!r} targets non-input binding {target!r}.",
                        start=node.span.start,
                        end=node.span.end,
                        stage="EFFECTCHECK",
                    )
        if len(all_ids) != len(set(all_ids)):
            raise MglsCompileError(
                "DuplicateBinding",
                "Requirement IDs must be unique within an effect node.",
                start=node.span.start,
                end=node.span.end,
                stage="EFFECTCHECK",
            )
        resources = obligations["resources"]
        if resources["events"] < spec.emitted_events:
            raise MglsCompileError(
                "ConservationProofFailure",
                f"Contract requires at least {spec.emitted_events} event reservations.",
                start=node.span.start,
                end=node.span.end,
                stage="EFFECTCHECK",
            )
        return spec

    def compile(self) -> tuple[_JSON, _JSON]:
        values: list[_JSON] = []
        for value in self.parsed["values"]:
            if value.name in self.signatures:
                self._duplicate(value.name, value.span, "value")
            self.signatures[value.name] = value.signature
            values.append(copy.deepcopy(value.artifact))
            self._map(
                f"map:value:{value.name}",
                value.span,
                "exact",
                "value",
                value.name,
                binding=value.name,
            )
        if len(values) > int(self.limits["values"]):
            raise MglsCompileError(
                "InputLimitExceeded",
                "MGLS value declaration limit exceeded.",
                start=0,
                end=len(self.normalized_text),
                stage="LIMIT",
            )

        nodes: list[_JSON] = []
        edge_pairs: set[tuple[str, str]] = set()
        for order, node in enumerate(self.parsed["nodes"]):
            if node.name in self.node_order:
                self._duplicate(node.name, node.span, "node")
            self.node_order[node.name] = order
            input_signatures = tuple(self._require_known(binding, node) for binding in node.inputs)
            instruction: str
            output_signature: str | None = None
            artifact: _JSON = {
                "node_id": node.name,
                "order": order,
                "inputs": list(node.inputs),
                "produces": list(node.produced),
            }
            if node.kind == "resolve":
                instruction = "ref.resolve"
                if input_signatures != ("selector",):
                    raise MglsCompileError(
                        "TypeError",
                        "resolve requires one selector input.",
                        start=node.span.start,
                        end=node.span.end,
                        stage="TYPECHECK",
                    )
                output_signature = "reference"
            elif node.kind == "calculate":
                instruction = "pure.calculate"
                if len(input_signatures) < 2 or len(set(input_signatures)) != 1:
                    raise MglsCompileError(
                        "TypeError",
                        "calculate requires at least two exactly compatible inputs.",
                        start=node.span.start,
                        end=node.span.end,
                        stage="TYPECHECK",
                    )
                if not (
                    input_signatures[0] == "literal:number"
                    or input_signatures[0] == "quantity"
                ):
                    raise MglsCompileError(
                        "TypeError",
                        "calculate admits numeric literals or compatible quantities only.",
                        start=node.span.start,
                        end=node.span.end,
                        stage="TYPECHECK",
                    )
                artifact["operator"] = node.payload["operator"]
                output_signature = input_signatures[0]
            elif node.kind == "compare":
                instruction = "pure.compare"
                if len(input_signatures) != 2 or input_signatures[0] != input_signatures[1]:
                    raise MglsCompileError(
                        "TypeError",
                        "compare requires two exactly compatible inputs.",
                        start=node.span.start,
                        end=node.span.end,
                        stage="TYPECHECK",
                    )
                operator = node.payload["operator"]
                if input_signatures[0].startswith(("record:", "sequence:")) and operator not in {"equal", "not_equal"}:
                    raise MglsCompileError(
                        "EffectMismatch",
                        "Structured values support only equality comparison.",
                        start=node.span.start,
                        end=node.span.end,
                        stage="TYPECHECK",
                    )
                artifact["operator"] = operator
                output_signature = "literal:boolean"
            elif node.kind == "rank":
                instruction = "pure.rank"
                if len(input_signatures) != 1 or not input_signatures[0].startswith("sequence:"):
                    raise MglsCompileError(
                        "TypeError",
                        "rank requires one sequence input.",
                        start=node.span.start,
                        end=node.span.end,
                        stage="TYPECHECK",
                    )
                artifact["direction"] = node.payload["direction"]
                output_signature = input_signatures[0]
            elif node.kind == "require":
                instruction = "assert.require"
                if input_signatures != ("literal:boolean",):
                    raise MglsCompileError(
                        "TypeError",
                        "require consumes exactly one bool binding.",
                        start=node.span.start,
                        end=node.span.end,
                        stage="TYPECHECK",
                    )
                artifact["diagnostic_code"] = node.payload["diagnostic_code"]
            elif node.kind in {"effect", "observe"}:
                instruction = "effect.invoke" if node.kind == "effect" else "evidence.observe"
                spec = self._check_contract(node, instruction, input_signatures)
                artifact["contract"] = copy.deepcopy(node.payload["contract"])
                artifact["obligations"] = copy.deepcopy(node.payload["obligations"])
                output_signature = spec.output
            else:
                raise AssertionError(node.kind)
            artifact["instruction"] = instruction
            if output_signature is not None:
                produced = node.produced[0]
                if produced in self.signatures:
                    self._duplicate(produced, node.span, "binding")
                self.signatures[produced] = output_signature
                self.producer[produced] = node.name
            for predecessor in node.after:
                predecessor_order = self.node_order.get(predecessor)
                if predecessor_order is None or predecessor_order >= order:
                    raise MglsCompileError(
                        "CausalityCycleError",
                        f"after dependency {predecessor!r} must name an earlier node.",
                        start=node.span.start,
                        end=node.span.end,
                        stage="GRAPH",
                    )
                edge_pairs.add((predecessor, node.name))
            for binding in node.inputs:
                source = self.producer.get(binding)
                if source is not None:
                    edge_pairs.add((source, node.name))
            nodes.append(artifact)
            self._map(
                f"map:node:{node.name}",
                node.span,
                "exact",
                "node",
                node.name,
            )
        if len(nodes) > int(self.limits["nodes"]):
            raise MglsCompileError(
                "InputLimitExceeded",
                "MGLS node declaration limit exceeded.",
                start=0,
                end=len(self.normalized_text),
                stage="LIMIT",
            )

        edges = [
            {"from": source, "to": target}
            for target in sorted(self.node_order, key=lambda item: self.node_order[item])
            for source in sorted(
                (candidate for candidate, destination in edge_pairs if destination == target),
                key=lambda item: self.node_order[item],
            )
        ]
        if len(edges) > int(self.limits["edges"]):
            raise MglsCompileError(
                "InputLimitExceeded",
                "MGLS emitted edge limit exceeded.",
                start=0,
                end=len(self.normalized_text),
                stage="LIMIT",
            )
        node_by_name = {node.name: node for node in self.parsed["nodes"]}
        for edge in edges:
            span = node_by_name[edge["to"]].span
            edge_id = f"{edge['from']}:{edge['to']}"
            self._map(
                f"map:edge:{edge_id}",
                span,
                "derived",
                "edge",
                edge_id,
            )

        outputs: list[_JSON] = []
        output_names: set[str] = set()
        for output in self.parsed["outputs"]:
            if output.name in output_names:
                self._duplicate(output.name, output.span, "output")
            output_names.add(output.name)
            signature = self.signatures.get(output.binding)
            if signature is None:
                raise MglsCompileError(
                    "UnresolvedName",
                    f"Output {output.name!r} references unresolved binding {output.binding!r}.",
                    start=output.span.start,
                    end=output.span.end,
                    stage="OUTPUT",
                )
            compatible = {
                "value": signature.startswith(("literal:", "record:", "sequence:")) or signature == "quantity",
                "reference": signature == "reference",
                "evidence": signature == "evidence",
                "effect_result": signature == "effect_result",
                "event": signature in {"effect_result", "evidence"},
                "artifact": signature == "evidence",
            }[output.kind]
            if not compatible:
                raise MglsCompileError(
                    "EffectMismatch",
                    f"Output kind {output.kind!r} is incompatible with binding signature {signature!r}.",
                    start=output.span.start,
                    end=output.span.end,
                    stage="OUTPUT",
                )
            outputs.append(
                {"name": output.name, "binding": output.binding, "kind": output.kind}
            )
            self._map(
                f"map:output:{output.name}",
                output.span,
                "exact",
                "output",
                output.name,
                binding=output.binding,
            )
        if len(outputs) > int(self.limits["outputs"]):
            raise MglsCompileError(
                "InputLimitExceeded",
                "MGLS output declaration limit exceeded.",
                start=0,
                end=len(self.normalized_text),
                stage="LIMIT",
            )

        header = self.parsed["header"]
        header_span = self.parsed["header_span"]
        program: _JSON = {
            "artifact_kind": "MagicalProgram",
            "artifact_version": "0",
            "contract": {"contract_id": "magical-program", "revision": "0"},
            "stability": "experimental",
            "program_id": header["program_id"],
            "provenance": {
                "relation": "lowered",
                "input_stage": "program",
                "source": {
                    "artifact_kind": "MagicalSource",
                    "artifact_version": "0",
                    "artifact_id": header["source_id"],
                    "stage": "source",
                },
            },
            "compatibility": {
                "registry_id": header["registry_id"],
                "registry_revision": header["registry_revision"],
                "profile_id": header["profile_id"],
                "profile_revision": header["profile_revision"],
            },
            "budget": copy.deepcopy(header["budget"]),
            "values": values,
            "nodes": nodes,
            "edges": edges,
            "outputs": outputs,
        }
        self._map(
            "map:header:program",
            header_span,
            "exact",
            "root",
            header["program_id"],
            field="program_id",
        )
        self._map(
            "map:header:fixed-contract",
            header_span,
            "synthesized",
            "root",
            header["program_id"],
            field="contract",
        )
        source_map: _JSON = {
            "artifact_kind": "MglsSourceMap",
            "artifact_version": "0",
            "contract": {"contract_id": "mgls-source-map", "revision": "0"},
            "source": {
                "contract_id": "mgls-source",
                "revision": "0",
                "source_id": header["source_id"],
                "offset_unit": "unicode-scalar",
                "normalization": "SourceTextNormalizerV1",
            },
            "target": {
                "artifact_kind": "MagicalProgram",
                "artifact_version": "0",
                "program_id": header["program_id"],
            },
            "compiler": {
                "compiler_id": "compiler:mgls-reference",
                "compiler_revision": "0",
            },
            "entries": sorted(self.map_entries, key=lambda item: item["entry_id"]),
        }
        return program, source_map


def _load_json_resource(path: str) -> _JSON:
    return json.loads(resource_path(path).read_text(encoding="utf-8"))


def _limits() -> _JSON:
    contract = _load_json_resource("conformance/mgls-source-contract.json")
    return copy.deepcopy(contract["limits"])


def _normalize(source: str | bytes, limits: Mapping[str, Any]) -> tuple[str, _JSON]:
    raw_bytes = source if isinstance(source, bytes) else source.encode("utf-8")
    if len(raw_bytes) > int(limits["source_utf8_bytes"]):
        raise MglsCompileError(
            "InputLimitExceeded",
            "MGLS source byte limit exceeded.",
            start=0,
            end=1,
            stage="INGRESS",
        )
    try:
        normalized = normalize_source_text(source, adapter_id="mgls")
    except SourceTextDiagnostic as error:
        raise MglsCompileError(
            error.code,
            error.message,
            start=error.source_offset or 0,
            end=(error.source_offset or 0) + 1,
            stage="INGRESS",
        ) from error
    return normalized["output"]["normalized_text"], normalized


def compile_source(source: str | bytes) -> _JSON:
    """Compile one complete source or raise one fatal shared diagnostic."""

    limits = _limits()
    normalized_text, normalization = _normalize(source, limits)
    tokens = Lexer(normalized_text, token_limit=int(limits["tokens"])).scan()
    parsed = Parser(tokens).parse()
    program, source_map = Compiler(
        parsed, normalized_text=normalized_text, limits=limits
    ).compile()
    program_schema = _load_json_resource("schemas/magical-program.schema.json")
    source_map_schema = _load_json_resource("schemas/mgls-source-map.schema.json")
    try:
        admission = admit_program(
            program,
            schema=program_schema,
            registered_contracts=_CONTRACTS,
            limits=MagicalProgramHostLimits(),
        )
    except MagicalProgramAdmissionError as error:
        raise MglsCompileError(
            "StructuredInputInvalid",
            "Emitted MagicalProgram failed independent target admission.",
            start=0,
            end=len(normalized_text),
            stage="TARGET_ADMISSION",
            details={"target_code": error.code, "target_path": error.path},
        ) from error
    validation = sorted(
        Draft202012Validator(source_map_schema).iter_errors(source_map),
        key=lambda item: (list(item.absolute_path), item.message),
    )
    if validation:
        error = validation[0]
        raise MglsCompileError(
            "NormalizationFailed",
            f"Emitted source map is invalid: {error.message}",
            start=0,
            end=len(normalized_text),
            stage="SOURCE_MAP",
        )
    return {
        "status": "Compiled",
        "source_contract": {"contract_id": "mgls-source", "revision": "0"},
        "normalization": normalization,
        "program": program,
        "source_map": source_map,
        "target_admission": admission,
    }


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
    projection = {
        "program": result["program"],
        "source_map": result["source_map"],
    }
    return json.dumps(
        projection,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


__all__ = [
    "MglsCompileError",
    "canonical_compilation_bytes",
    "check_source",
    "compile_file",
    "compile_source",
]
