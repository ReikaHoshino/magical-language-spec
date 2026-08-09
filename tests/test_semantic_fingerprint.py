#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import struct
import unittest
from pathlib import Path

from tools.semantic_fingerprint import (
    JCSRepresentationError,
    UnknownSummaryContradiction,
    UnsupportedSemanticExtension,
    canonical_semantic_projection_v1,
    jcs_canonicalize,
    load_json_document,
    semantic_fingerprint_v1,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples" / "semantic-fingerprint"


def load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class SemanticFingerprintV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = load("thermal-transfer-v1.json")
        cls.base = cls.cases["base_nsr"]

    def test_expected_projection_and_fingerprint(self) -> None:
        self.assertEqual(
            canonical_semantic_projection_v1(self.base),
            self.cases["expected_projection"],
        )
        self.assertEqual(
            semantic_fingerprint_v1(self.base),
            self.cases["expected_fingerprint"],
        )

    def test_language_adapter_provenance_and_role_order_do_not_drift(self) -> None:
        equivalent = self.cases["equivalent_adapter_nsr"]
        self.assertEqual(
            semantic_fingerprint_v1(self.base),
            semantic_fingerprint_v1(equivalent),
        )

    def test_object_key_order_does_not_drift(self) -> None:
        reordered = json.loads(
            json.dumps(self.base, sort_keys=True, ensure_ascii=False)
        )
        self.assertEqual(
            semantic_fingerprint_v1(self.base),
            semantic_fingerprint_v1(reordered),
        )

    def test_semantic_changes_drift(self) -> None:
        variants = []
        goal = copy.deepcopy(self.base)
        next(role for role in goal["roles"] if role["role"] == "Goal")[
            "value"
        ]["selector"]["symbol"] = "stone"
        variants.append(goal)

        quantity = copy.deepcopy(self.base)
        quantity_role = next(
            role for role in quantity["roles"] if role["role"] == "Quantity"
        )
        quantity_role["value"] = {
            "kind": "Literal",
            "value": 1000,
            "unit": "J",
        }
        quantity["unknowns"] = []
        variants.append(quantity)

        unknown_reason = copy.deepcopy(self.base)
        unknown_role = next(
            role
            for role in unknown_reason["roles"]
            if role["role"] == "Quantity"
        )
        unknown_role["value"]["reason"] = "AmbiguousSurfaceArgument"
        unknown_reason["unknowns"][0]["reason"] = "AmbiguousSurfaceArgument"
        variants.append(unknown_reason)

        base_fingerprint = semantic_fingerprint_v1(self.base)
        for variant in variants:
            with self.subTest(variant=variant):
                self.assertNotEqual(base_fingerprint, semantic_fingerprint_v1(variant))

    def test_role_duplicates_are_preserved(self) -> None:
        duplicated = copy.deepcopy(self.base)
        duplicated["roles"].append(copy.deepcopy(duplicated["roles"][0]))
        projection = canonical_semantic_projection_v1(duplicated)
        self.assertEqual(len(projection["roles"]), len(self.base["roles"]) + 1)
        self.assertNotEqual(
            semantic_fingerprint_v1(self.base),
            semantic_fingerprint_v1(duplicated),
        )

    def test_non_role_semantic_array_order_is_preserved(self) -> None:
        ordered = copy.deepcopy(self.base)
        ordered["modifiers"] = [
            {"kind": "Literal", "value": "first"},
            {"kind": "Literal", "value": "second"},
        ]
        reversed_order = copy.deepcopy(ordered)
        reversed_order["modifiers"].reverse()
        self.assertNotEqual(
            semantic_fingerprint_v1(ordered),
            semantic_fingerprint_v1(reversed_order),
        )

    def test_identifiers_are_compared_exactly(self) -> None:
        changed_case = copy.deepcopy(self.base)
        changed_case["action"] = "Transfer"
        changed_whitespace = copy.deepcopy(self.base)
        changed_whitespace["action"] = "transfer "
        fingerprints = {
            semantic_fingerprint_v1(self.base),
            semantic_fingerprint_v1(changed_case),
            semantic_fingerprint_v1(changed_whitespace),
        }
        self.assertEqual(len(fingerprints), 3)

    def test_omitted_null_and_unknown_are_distinct(self) -> None:
        omitted = copy.deepcopy(self.base)
        explicit_null = copy.deepcopy(self.base)
        explicit_null["roles"].append(
            {
                "role": "Condition",
                "value": {"kind": "Literal", "value": None},
            }
        )

        unknown = copy.deepcopy(self.base)
        unknown["roles"].append(
            {
                "role": "Condition",
                "value": {"kind": "Unknown", "reason": "MissingActionCondition"},
            }
        )
        unknown["unknowns"].append(
            {"field": "Condition", "reason": "MissingActionCondition"}
        )

        fingerprints = {
            semantic_fingerprint_v1(omitted),
            semantic_fingerprint_v1(explicit_null),
            semantic_fingerprint_v1(unknown),
        }
        self.assertEqual(len(fingerprints), 3)

    def test_evidence_inside_semantic_payload_is_excluded(self) -> None:
        with_metadata = copy.deepcopy(self.base)
        source = next(
            role for role in with_metadata["roles"] if role["role"] == "Source"
        )
        source["value"]["selector"]["source_span"] = {"start": 1, "end": 2}
        source["value"]["selector"]["provider"] = "other-adapter"
        self.assertEqual(
            semantic_fingerprint_v1(self.base),
            semantic_fingerprint_v1(with_metadata),
        )

    def test_unknown_semantic_extension_is_rejected(self) -> None:
        extended = copy.deepcopy(self.base)
        extended["roles"][0]["value"]["future_semantics"] = "undecided"
        with self.assertRaises(UnsupportedSemanticExtension):
            semantic_fingerprint_v1(extended)

    def test_unknown_summary_contradiction_is_rejected(self) -> None:
        contradicted = copy.deepcopy(self.base)
        contradicted["unknowns"][0]["reason"] = "DifferentReason"
        with self.assertRaises(UnknownSummaryContradiction):
            semantic_fingerprint_v1(contradicted)

        extra_non_role_summary = copy.deepcopy(self.base)
        extra_non_role_summary["unknowns"].append(
            {"field": "NestedConstraint", "reason": "NestedUnknown"}
        )
        self.assertEqual(
            semantic_fingerprint_v1(self.base),
            semantic_fingerprint_v1(extra_non_role_summary),
        )

    def test_jcs_numeric_and_unicode_boundaries(self) -> None:
        value = {
            "\U0001f600": 1.0,
            "\ufffd": 0.000001,
            "large": 1e30,
            "plain_large": 1e20,
            "small": 1e-7,
            "negative_zero": -0.0,
        }
        self.assertEqual(
            jcs_canonicalize(value),
            '{"large":1e+30,"negative_zero":0,"plain_large":100000000000000000000,"small":1e-7,"😀":1,"�":0.000001}',
        )
        self.assertEqual(jcs_canonicalize(2**53), "9007199254740992")
        self.assertEqual(jcs_canonicalize(2**68), "295147905179352830000")
        with self.assertRaises(JCSRepresentationError):
            jcs_canonicalize(2**53 + 1)
        with self.assertRaises(JCSRepresentationError):
            jcs_canonicalize(float("nan"))

    def test_rfc8785_serialization_sample(self) -> None:
        sample = {
            "numbers": [333333333.33333329, 1e30, 4.50, 2e-3, 1e-27],
            "string": "€$\u000f\nA'B\"\\\\\"/",
            "literals": [None, True, False],
        }
        self.assertEqual(
            jcs_canonicalize(sample),
            '{"literals":[null,true,false],"numbers":[333333333.3333333,1e+30,4.5,0.002,1e-27],"string":"€$\\u000f\\nA\'B\\"\\\\\\\\\\"/"}',
        )

    def test_rfc8785_appendix_b_number_samples(self) -> None:
        samples = {
            "0000000000000000": "0",
            "8000000000000000": "0",
            "0000000000000001": "5e-324",
            "8000000000000001": "-5e-324",
            "7fefffffffffffff": "1.7976931348623157e+308",
            "ffefffffffffffff": "-1.7976931348623157e+308",
            "4340000000000000": "9007199254740992",
            "c340000000000000": "-9007199254740992",
            "4430000000000000": "295147905179352830000",
            "44b52d02c7e14af5": "9.999999999999997e+22",
            "44b52d02c7e14af6": "1e+23",
            "44b52d02c7e14af7": "1.0000000000000001e+23",
            "444b1ae4d6e2ef4e": "999999999999999700000",
            "444b1ae4d6e2ef4f": "999999999999999900000",
            "444b1ae4d6e2ef50": "1e+21",
            "3eb0c6f7a0b5ed8c": "9.999999999999997e-7",
            "3eb0c6f7a0b5ed8d": "0.000001",
            "41b3de4355555553": "333333333.3333332",
            "41b3de4355555554": "333333333.33333325",
            "41b3de4355555555": "333333333.3333333",
            "41b3de4355555556": "333333333.3333334",
            "41b3de4355555557": "333333333.33333343",
            "becbf647612f3696": "-0.0000033333333333333333",
            "43143ff3c1cb0959": "1424953923781206.2",
        }
        for bits, expected in samples.items():
            value = struct.unpack(">d", bytes.fromhex(bits))[0]
            with self.subTest(bits=bits):
                self.assertEqual(jcs_canonicalize(value), expected)

    def test_rfc8785_utf16_property_sorting(self) -> None:
        sample = {
            "€": "Euro Sign",
            "\r": "Carriage Return",
            "דּ": "Hebrew Letter Dalet With Dagesh",
            "1": "One",
            "😀": "Emoji: Grinning Face",
            "\u0080": "Control",
            "ö": "Latin Small Letter O With Diaeresis",
        }
        self.assertEqual(
            list(json.loads(jcs_canonicalize(sample)).values()),
            [
                "Carriage Return",
                "One",
                "Control",
                "Latin Small Letter O With Diaeresis",
                "Euro Sign",
                "Emoji: Grinning Face",
                "Hebrew Letter Dalet With Dagesh",
            ],
        )

    def test_duplicate_json_property_is_rejected(self) -> None:
        with self.assertRaises(JCSRepresentationError):
            load_json_document('{"kind":"A","kind":"B","roles":[]}')


if __name__ == "__main__":
    unittest.main()
