#!/usr/bin/env python3
"""Regression checks for common machine-readable values and hash domains."""
from __future__ import annotations

import copy
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from validate_schemas import load


ROOT = Path(__file__).resolve().parents[1]
COMMON_SCHEMA = ROOT / "schemas" / "common-values.schema.json"
REFERENCE = ROOT / "reference" / "machine-values.md"
EXAMPLES = ROOT / "examples" / "common-values.md"
TIME_DIMENSION = {"kg": 0, "m": 0, "s": 1, "A": 0, "K": 0, "mol": 0, "cd": 0}


class CommonValueContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load(COMMON_SCHEMA)
        cls.reference = REFERENCE.read_text(encoding="utf-8")
        cls.examples = EXAMPLES.read_text(encoding="utf-8")
        cls.registry = Registry().with_resource(
            cls.schema["$id"], Resource.from_contents(cls.schema)
        )

    def definition_validator(self, name: str) -> Draft202012Validator:
        return Draft202012Validator(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$ref": f"{self.schema['$id']}#/$defs/{name}",
            },
            registry=self.registry,
        )

    def test_identifier_and_revision_are_exact_nonempty_strings(self) -> None:
        for definition in ("identifier", "version", "revision"):
            check = self.definition_validator(definition)
            check.validate("01")
            self.assertTrue(list(check.iter_errors("")))
            self.assertTrue(list(check.iter_errors(1)))

        self.assertIn(
            "identifier JSON encoding != source-language normalization",
            self.reference,
        )
        self.assertIn(
            "owning\n`LanguageAdapter` / domain contract",
            self.reference,
        )
        self.assertIn(
            "`SourceTextNormalizerV1` とこの\nserialization contract",
            self.reference,
        )

    def test_quantity_keeps_semantic_type_and_dimension_separate(self) -> None:
        quantity = {
            "semantic_type": "Energy",
            "dimension": {"kg": 1, "m": 2, "s": -2, "A": 0, "K": 0, "mol": 0, "cd": 0},
            "value": 12.5,
            "unit": "J",
        }
        check = self.definition_validator("quantity")
        check.validate(quantity)

        missing_semantic_type = copy.deepcopy(quantity)
        del missing_semantic_type["semantic_type"]
        self.assertTrue(list(check.iter_errors(missing_semantic_type)))

        incomplete_dimension = copy.deepcopy(quantity)
        del incomplete_dimension["dimension"]["cd"]
        self.assertTrue(list(check.iter_errors(incomplete_dimension)))

    def test_duration_is_explicit_time_quantity(self) -> None:
        duration = {
            "semantic_type": "Time",
            "dimension": TIME_DIMENSION,
            "value": 10,
            "unit": "ms",
        }
        check = self.definition_validator("duration")
        check.validate(duration)

        wrong_type = copy.deepcopy(duration)
        wrong_type["semantic_type"] = "RuntimeTick"
        self.assertTrue(list(check.iter_errors(wrong_type)))

        wrong_dimension = copy.deepcopy(duration)
        wrong_dimension["dimension"]["s"] = 0
        self.assertTrue(list(check.iter_errors(wrong_dimension)))

    def test_unresolved_hash_cannot_masquerade_as_digest(self) -> None:
        unresolved = {
            "scope": "artifact-content",
            "status": "unresolved",
            "reason": "Canonical bytes and digest algorithm are deferred.",
        }
        check = self.definition_validator("artifactContentHash")
        check.validate(unresolved)

        invented = copy.deepcopy(unresolved)
        invented["algorithm"] = "sha256"
        invented["value"] = "not-a-digest"
        self.assertTrue(list(check.iter_errors(invented)))

        wrong_scope = copy.deepcopy(unresolved)
        wrong_scope["scope"] = "registry-contract-set"
        self.assertTrue(list(check.iter_errors(wrong_scope)))

    def test_resolved_digest_requires_profile_algorithm_and_value(self) -> None:
        digest = {
            "scope": "artifact-content",
            "status": "digest",
            "canonicalization_profile": "future-profile",
            "algorithm": "future-algorithm",
            "value": "profile-defined-encoding",
        }
        check = self.definition_validator("artifactContentHash")
        check.validate(digest)

        missing_profile = copy.deepcopy(digest)
        del missing_profile["canonicalization_profile"]
        self.assertTrue(list(check.iter_errors(missing_profile)))

    def test_source_evidence_hash_is_a_separate_scope(self) -> None:
        source_hash = {
            "scope": "source-evidence",
            "status": "unresolved",
            "reason": "The owning capture profile has not selected source bytes.",
        }
        check = self.definition_validator("sourceEvidenceHash")
        check.validate(source_hash)

        wrong_scope = copy.deepcopy(source_hash)
        wrong_scope["scope"] = "artifact-content"
        self.assertTrue(list(check.iter_errors(wrong_scope)))

    def test_semantic_fingerprint_boundary_remains_explicit(self) -> None:
        for invariant in (
            "SemanticFingerprint != artifact content_hash",
            "registry hash mismatch alone != incompatibility",
            "hash equality != compatibility",
        ):
            self.assertIn(invariant, self.reference)

    def test_positive_and_negative_examples_remain_published(self) -> None:
        for marker in (
            "ACCEPT: exact identifier",
            "ACCEPT: Energy quantity",
            "ACCEPT: duration",
            "ACCEPT: unresolved artifact hash",
            "REJECT: dimension without semantic type",
            "REJECT: duration collapsed to value/unit",
            "REJECT: unresolved placeholder masquerading as digest",
            "REJECT: cross-domain hash scope",
        ):
            self.assertIn(marker, self.examples)


if __name__ == "__main__":
    unittest.main()
