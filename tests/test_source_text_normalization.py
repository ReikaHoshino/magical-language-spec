#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from tools.semantic_fingerprint import semantic_fingerprint_v1
from tools.source_text_normalization import (
    SourceTextDiagnostic,
    normalize_source_text,
    rejected_source_text,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples" / "source-normalization"
SCHEMA = json.loads(
    (ROOT / "schemas" / "source-text-normalization.schema.json").read_text(
        encoding="utf-8"
    )
)
VALIDATOR = Draft202012Validator(SCHEMA)


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class SourceTextNormalizationTests(unittest.TestCase):
    def assert_valid_result(self, result: dict) -> None:
        errors = list(VALIDATOR.iter_errors(result))
        self.assertEqual([], errors, [error.message for error in errors])

    def test_reference_fixtures_are_schema_valid(self) -> None:
        for path in sorted(FIXTURES.glob("*.json")):
            with self.subTest(path=path.name):
                self.assert_valid_result(load_fixture(path.name))

    def test_latin_source_is_unchanged(self) -> None:
        source = "Calorem ab aqua ad aerem transfer."
        result = normalize_source_text(
            source,
            adapter_id="lat",
            external_language_tags=["la"],
            script_hints=["Latn"],
        )
        self.assertEqual(load_fixture("latin-unchanged.json"), result)
        self.assertEqual(source, result["output"]["normalized_text"])
        self.assertTrue(result["source_map"]["entries"][0]["exact"])

    def test_non_latin_combining_sequence_is_nfc_with_recoverable_span(self) -> None:
        result = normalize_source_text(
            "カ\u3099",
            adapter_id="jpn",
            external_language_tags=["ja"],
            script_hints=["Jpan"],
        )
        self.assertEqual(load_fixture("japanese-combining-nfc.json"), result)
        self.assertEqual("ガ", result["output"]["normalized_text"])
        self.assertEqual(
            {"start": 0, "end": 2},
            result["source_map"]["entries"][0]["source_span"],
        )
        self.assertFalse(result["source_map"]["entries"][0]["exact"])

    def test_line_endings_are_canonicalized_without_collapsing_whitespace(self) -> None:
        result = normalize_source_text(
            "a  b\r\nc\rd\n",
            adapter_id="eng",
            external_language_tags=["en"],
            script_hints=["Latn"],
        )
        self.assertEqual("a  b\nc\nd\n", result["output"]["normalized_text"])
        self.assertEqual(
            ["LineEndingCanonicalized", "LineEndingCanonicalized"],
            [
                transformation["kind"]
                for transformation in result["transformations"]
            ],
        )
        self.assertEqual(4, len(result["source_map"]["entries"]))

    def test_compatibility_case_and_punctuation_are_not_folded(self) -> None:
        source = "Ａether ①! AETHER"
        result = normalize_source_text(
            source,
            adapter_id="zho",
            external_language_tags=["zh-Hant"],
            script_hints=["Hant"],
        )
        self.assertEqual(source, result["output"]["normalized_text"])
        self.assertNotEqual(
            result["output"]["normalized_text"], "Aether 1! aether"
        )

    def test_utf8_boundary_is_strict_and_bom_is_recorded(self) -> None:
        accepted = normalize_source_text(
            b"\xef\xbb\xbfcalor",
            adapter_id="lat",
            external_language_tags=["la"],
            script_hints=["Latn"],
        )
        self.assertEqual("calor", accepted["output"]["normalized_text"])
        self.assertTrue(accepted["input"]["utf8_bom_removed"])
        self.assertEqual(
            "Utf8BomRemoved", accepted["transformations"][0]["kind"]
        )

        with self.assertRaises(SourceTextDiagnostic) as raised:
            normalize_source_text(b"\xff", adapter_id="jpn")
        self.assertEqual("InvalidUTF8", raised.exception.code)
        rejected = rejected_source_text(
            raised.exception, adapter_id="jpn", boundary="utf8-bytes"
        )
        self.assertEqual(load_fixture("invalid-utf8.json"), rejected)
        self.assert_valid_result(rejected)

    def test_invalid_or_unsupported_scalars_fail_diagnostically(self) -> None:
        cases = [
            ("\ud800", "InvalidUnicodeScalar"),
            ("\x00", "UnsupportedSourceCharacter"),
        ]
        for source, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(SourceTextDiagnostic) as raised:
                    normalize_source_text(source, adapter_id="lat")
                self.assertEqual(expected_code, raised.exception.code)

    def test_adapter_id_tags_and_scripts_are_separate_explicit_metadata(self) -> None:
        result = normalize_source_text(
            "文字",
            adapter_id="lzh",
            external_language_tags=["zh-Hant"],
            script_hints=["Hant"],
        )
        self.assertEqual("lzh", result["adapter"]["adapter_id"])
        self.assertEqual(["zh-Hant"], result["adapter"]["external_language_tags"])
        self.assertEqual(["Hant"], result["adapter"]["script_hints"])

        invalid_cases = [
            (
                {"adapter_id": "ja-JP"},
                "InvalidAdapterID",
            ),
            (
                {"adapter_id": "jpn", "external_language_tags": ["not_a_tag"]},
                "InvalidExternalLanguageTag",
            ),
            (
                {"adapter_id": "jpn", "script_hints": ["Japanese"]},
                "InvalidScriptTag",
            ),
        ]
        for kwargs, expected_code in invalid_cases:
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(SourceTextDiagnostic) as raised:
                    normalize_source_text("text", **kwargs)
                self.assertEqual(expected_code, raised.exception.code)

    def test_source_normalization_does_not_normalize_semantic_identifiers(self) -> None:
        fullwidth = normalize_source_text("Ａ", adapter_id="jpn")
        ascii_text = normalize_source_text("A", adapter_id="jpn")
        self.assertEqual("Ａ", fullwidth["output"]["normalized_text"])
        self.assertEqual("A", ascii_text["output"]["normalized_text"])

        base = {
            "kind": "NormalizedSemanticRepresentation",
            "schema_version": "0.7.3",
            "action": "Ａ",
            "roles": [],
            "unknowns": [],
        }
        ascii_identifier = copy.deepcopy(base)
        ascii_identifier["action"] = "A"
        self.assertNotEqual(
            semantic_fingerprint_v1(base),
            semantic_fingerprint_v1(ascii_identifier),
        )


if __name__ == "__main__":
    unittest.main()
