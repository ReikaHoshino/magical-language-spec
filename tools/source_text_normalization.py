#!/usr/bin/env python3
"""Deterministic representation-layer preprocessing for language adapters."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable

CONTRACT_VERSION = "source-text-normalization-v1"
ADAPTER_ID_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
LANGUAGE_TAG_RE = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$")
SCRIPT_TAG_RE = re.compile(r"^[A-Za-z]{4}$")


@dataclass(frozen=True)
class SourceTextDiagnostic(Exception):
    """A stable source-ingress diagnostic with an optional boundary offset."""

    code: str
    message: str
    source_offset: int | None = None

    def __str__(self) -> str:
        if self.source_offset is None:
            return f"{self.code}: {self.message}"
        return f"{self.code} at offset {self.source_offset}: {self.message}"


def _validate_metadata(
    adapter_id: str,
    external_language_tags: Iterable[str],
    script_hints: Iterable[str],
) -> tuple[list[str], list[str]]:
    if not ADAPTER_ID_RE.fullmatch(adapter_id):
        raise SourceTextDiagnostic(
            "InvalidAdapterID",
            "project adapter ID must match ^[a-z][a-z0-9_-]*$",
        )

    language_tags = list(external_language_tags)
    scripts = list(script_hints)
    if len(language_tags) != len(set(language_tags)):
        raise SourceTextDiagnostic(
            "InvalidExternalLanguageTag",
            "external language tags must be unique",
        )
    if len(scripts) != len(set(scripts)):
        raise SourceTextDiagnostic(
            "InvalidScriptTag",
            "script hints must be unique",
        )
    for tag in language_tags:
        if not LANGUAGE_TAG_RE.fullmatch(tag):
            raise SourceTextDiagnostic(
                "InvalidExternalLanguageTag",
                f"unsupported external language-tag syntax: {tag!r}",
            )
    for script in scripts:
        if not SCRIPT_TAG_RE.fullmatch(script):
            raise SourceTextDiagnostic(
                "InvalidScriptTag",
                f"script hint must be a four-letter ISO 15924-style tag: {script!r}",
            )
    return language_tags, scripts


def _decode_source(source: str | bytes) -> tuple[str, str, bool]:
    if isinstance(source, bytes):
        boundary = "utf8-bytes"
        had_bom = source.startswith(b"\xef\xbb\xbf")
        payload = source[3:] if had_bom else source
        try:
            return payload.decode("utf-8", errors="strict"), boundary, had_bom
        except UnicodeDecodeError as exc:
            raise SourceTextDiagnostic(
                "InvalidUTF8",
                "byte input is not well-formed UTF-8",
                exc.start,
            ) from exc
    if isinstance(source, str):
        return source, "unicode-text", False
    raise TypeError("source must be str or bytes")


def _validate_scalars(text: str) -> None:
    for offset, char in enumerate(text):
        value = ord(char)
        if 0xD800 <= value <= 0xDFFF:
            raise SourceTextDiagnostic(
                "InvalidUnicodeScalar",
                "surrogate code points are not Unicode scalar values",
                offset,
            )
        if value == 0:
            raise SourceTextDiagnostic(
                "UnsupportedSourceCharacter",
                "U+0000 is not supported in source text",
                offset,
            )


def _line_segments(text: str) -> list[tuple[int, int, str, str]]:
    """Return source offsets plus line body and terminator without losing CR forms."""
    segments: list[tuple[int, int, str, str]] = []
    start = 0
    index = 0
    while index < len(text):
        if text[index] not in "\r\n":
            index += 1
            continue
        body = text[start:index]
        if text[index] == "\r" and index + 1 < len(text) and text[index + 1] == "\n":
            end = index + 2
            terminator = "\r\n"
        else:
            end = index + 1
            terminator = text[index]
        segments.append((start, end, body, terminator))
        start = end
        index = end
    segments.append((start, len(text), text[start:], ""))
    return segments


def normalize_source_text(
    source: str | bytes,
    *,
    adapter_id: str,
    external_language_tags: Iterable[str] = (),
    script_hints: Iterable[str] = (),
) -> dict:
    """Apply the common V1 source representation contract.

    The output is still source text. It is not an NSR, does not normalize
    semantic identifiers, and does not calculate any semantic or artifact hash.
    """

    language_tags, scripts = _validate_metadata(
        adapter_id, external_language_tags, script_hints
    )
    decoded, boundary, had_bom = _decode_source(source)
    _validate_scalars(decoded)

    output_parts: list[str] = []
    source_map: list[dict] = []
    transformations: list[dict] = []
    output_offset = 0

    for source_start, source_end, body, terminator in _line_segments(decoded):
        normalized_body = unicodedata.normalize("NFC", body)
        normalized_terminator = "\n" if terminator else ""
        normalized_segment = normalized_body + normalized_terminator
        original_segment = body + terminator
        output_start = output_offset
        output_end = output_start + len(normalized_segment)

        source_map.append(
            {
                "output_span": {"start": output_start, "end": output_end},
                "source_span": {"start": source_start, "end": source_end},
                "exact": normalized_segment == original_segment,
            }
        )
        if normalized_body != body:
            transformations.append(
                {
                    "kind": "CanonicalComposition",
                    "source_span": {
                        "start": source_start,
                        "end": source_start + len(body),
                    },
                    "output_span": {
                        "start": output_start,
                        "end": output_start + len(normalized_body),
                    },
                }
            )
        if terminator in {"\r", "\r\n"}:
            transformations.append(
                {
                    "kind": "LineEndingCanonicalized",
                    "source_span": {
                        "start": source_start + len(body),
                        "end": source_end,
                    },
                    "output_span": {
                        "start": output_start + len(normalized_body),
                        "end": output_end,
                    },
                }
            )
        output_parts.append(normalized_segment)
        output_offset = output_end

    normalized_text = "".join(output_parts)
    if had_bom:
        transformations.insert(
            0,
            {
                "kind": "Utf8BomRemoved",
                "source_span": {"start": 0, "end": 0},
                "output_span": {"start": 0, "end": 0},
            },
        )

    return {
        "contract_version": CONTRACT_VERSION,
        "status": "Accepted",
        "adapter": {
            "adapter_id": adapter_id,
            "external_language_tags": language_tags,
            "script_hints": scripts,
        },
        "input": {
            "boundary": boundary,
            "encoding": "UTF-8",
            "original_text": decoded,
            "utf8_bom_removed": had_bom,
        },
        "output": {
            "normalization_form": "NFC",
            "normalized_text": normalized_text,
        },
        "transformations": transformations,
        "source_map": {
            "offset_unit": "unicode-scalar-value",
            "entries": source_map,
        },
    }


def rejected_source_text(
    diagnostic: SourceTextDiagnostic,
    *,
    adapter_id: str,
    boundary: str,
) -> dict:
    """Create the machine-readable failure shape without guessing replacement text."""

    payload = {
        "code": diagnostic.code,
        "message": diagnostic.message,
    }
    if diagnostic.source_offset is not None:
        payload["source_offset"] = diagnostic.source_offset
    return {
        "contract_version": CONTRACT_VERSION,
        "status": "Rejected",
        "adapter_id": adapter_id,
        "boundary": boundary,
        "diagnostic": payload,
    }
