#!/usr/bin/env python3
"""Regression checks for the MIR scope/name-resolution crosswalk."""
from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference" / "mir-name-resolution.md"
GRAMMAR = ROOT / "grammar" / "mir.ebnf"
ERRORS = ROOT / "reference" / "errors.md"
EXAMPLES = ROOT / "examples" / "mir-name-resolution.md"


class MirNameResolutionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reference = REFERENCE.read_text(encoding="utf-8")
        cls.grammar = GRAMMAR.read_text(encoding="utf-8")
        cls.errors = ERRORS.read_text(encoding="utf-8")
        cls.examples = EXAMPLES.read_text(encoding="utf-8")

    def test_layer_and_namespace_boundaries_remain_explicit(self) -> None:
        for invariant in (
            "parse != semantic validation != typed elaboration != runtime",
            "lexical name resolution != registry lookup != World Index RESOLVE",
            "Selector != Ref",
            "Registry metadata != Capability",
        ):
            self.assertIn(invariant, self.reference)

        for name_class in (
            "| callable |",
            "| value |",
            "| type |",
            "| contextual semantic name |",
            "| selector/operator name |",
            "| member name |",
            "| argument/clause label |",
        ):
            self.assertIn(name_class, self.reference)

    def test_diagnostics_are_cross_referenced(self) -> None:
        for diagnostic in ("DuplicateBinding", "UnresolvedName"):
            self.assertIn(f"### `{diagnostic}`", self.reference)
            self.assertIn(diagnostic, self.errors)

    def test_crosswalk_tracks_existing_grammar_productions(self) -> None:
        self.assertIn(
            "reference/mir-name-resolution.md",
            self.grammar,
        )
        grammar_productions = set(
            re.findall(r"^([a-z][a-z-]*)\s*=", self.grammar, flags=re.MULTILINE)
        )
        required_crosswalk = {
            "program",
            "declaration",
            "spell-decl",
            "proc-decl",
            "fn-decl",
            "block",
            "let-statement",
            "primary-expression",
            "for-statement",
            "event-handler",
            "selector",
            "return-statement",
        }
        self.assertTrue(required_crosswalk <= grammar_productions)
        for production in required_crosswalk:
            self.assertIn(f"`{production}`", self.reference)

    def test_positive_and_negative_examples_remain_available(self) -> None:
        for marker in (
            "ACCEPT: nested-shadowing",
            "ACCEPT: initializer-uses-outer-binding",
            "ACCEPT: separate-namespaces",
            "REJECT DuplicateBinding: duplicate-parameters",
            "REJECT UnresolvedName: self-reference-in-initializer",
            "REJECT UnresolvedName: block-local-escape",
        ):
            self.assertIn(marker, self.examples)


if __name__ == "__main__":
    unittest.main()
