#!/usr/bin/env python3
"""Regression checks for the specification scope and ownership index."""
from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference"
SCOPE = REFERENCE / "scope-and-ownership.md"
TERMINOLOGY = REFERENCE / "terminology.md"
README = ROOT / "README.md"


class ScopeAndOwnershipContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scope = SCOPE.read_text(encoding="utf-8")
        cls.terminology = TERMINOLOGY.read_text(encoding="utf-8")
        cls.readme = README.read_text(encoding="utf-8")

    def test_normative_guarantees_and_boundaries_are_published(self) -> None:
        for marker in (
            "**Status:** normative scope and ownership contract",
            "## 1. Normative guarantees",
            "Language-specific parse != NSR != SemanticAST != TypedMIR != KernelPlan",
            "Evaluation != Execution",
            "Feasibility != Authority grant",
            "Registry metadata != Capability",
            "Unknown != zero",
            "SemanticFingerprint != artifact content_hash",
            "MKI data-plane primitives = 6",
        ):
            self.assertIn(marker, self.scope)

    def test_definition_sources_and_unspecified_remain_distinct(self) -> None:
        for source in (
            "Specification",
            "Implementation",
            "Registry",
            "World",
            "Profile",
        ):
            self.assertIn(f"| `{source}` |", self.scope)
        self.assertIn(
            "`unspecified`は第六の`DefinitionSource`ではない",
            self.scope,
        )
        self.assertIn(
            "Unknown value != unspecified specification choice",
            self.scope,
        )

    def test_project_terms_are_indexed_without_new_core_primitives(self) -> None:
        for term in ("魔法", "術式", "詠唱", "魔法陣", "魔力", "魔子"):
            self.assertIn(f"| {term} |", self.scope)
            self.assertIn(f"| {term} |", self.terminology)
        for invariant in (
            "魔力 != Energy != Capability",
            "魔子 != built-in SpeciesID",
            "詠唱 != semantic authority",
            "魔法陣 != executable permission",
        ):
            self.assertIn(invariant, self.scope)
            self.assertIn(invariant, self.terminology)

    def test_open_semantics_have_explicit_owners(self) -> None:
        for owner in (
            "planning-inference.md",
            "estimator-models.md",
            "canonical-water-ball.md",
            "Issue #36",
            "Issue #37",
        ):
            self.assertIn(owner, self.scope)
        self.assertIn(
            "generic artifact canonical bytes / digest algorithm",
            self.scope,
        )
        self.assertIn("Deferred design", self.scope)

    def test_major_references_publish_annotation_headers(self) -> None:
        documents = (
            "expressions.md",
            "kinetics.md",
            "latin-examples.md",
            "matter.md",
            "observer-models.md",
            "payloads.md",
            "quantities.md",
            "registry.md",
        )
        required_headers = (
            "**Status:**",
            "## Purpose",
            "## Non-goals",
            "## Depends on",
            "## Key invariants",
        )
        for document in documents:
            text = (REFERENCE / document).read_text(encoding="utf-8")
            for header in required_headers:
                with self.subTest(document=document, header=header):
                    self.assertIn(header, text)

    def test_reading_order_points_to_normative_scope_before_conventions(self) -> None:
        scope_link = "reference/scope-and-ownership.md"
        conventions_link = "reference/conventions.md"
        self.assertIn(scope_link, self.readme)
        self.assertLess(
            self.readme.index(scope_link),
            self.readme.index(conventions_link),
        )
        self.assertIn("scope-and-ownership.md", self.terminology)


if __name__ == "__main__":
    unittest.main()
