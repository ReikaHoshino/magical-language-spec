from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from src.artifacts.magical_program import MagicalProgramHostLimits

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "conformance" / "mgls-source-contract.json"
PROGRAM_SCHEMA_PATH = ROOT / "schemas" / "magical-program.schema.json"
SOURCE_MAP_SCHEMA_PATH = ROOT / "schemas" / "mgls-source-map.schema.json"
GRAMMAR_PATH = ROOT / "grammar" / "mgls.ebnf"
REFERENCE_PATH = ROOT / "reference" / "mgls-source-language.md"
NEGATIVE_PATH = ROOT / "examples" / "mgls" / "invalid" / "contract-cases.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class MglsSourceContractTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.contract = load(CONTRACT_PATH)
        self.program_schema = load(PROGRAM_SCHEMA_PATH)
        self.source_map_schema = load(SOURCE_MAP_SCHEMA_PATH)
        self.grammar = GRAMMAR_PATH.read_text(encoding="utf-8")
        self.reference = REFERENCE_PATH.read_text(encoding="utf-8")

    def test_contract_identity_and_preserved_stable_surface(self) -> None:
        self.assertEqual("mgls-source-contract", self.contract["contract_id"])
        self.assertEqual("0", self.contract["revision"])
        self.assertEqual("mgls-source", self.contract["source_contract"]["contract_id"])
        self.assertEqual(".mgls", self.contract["source_contract"]["filename_suffix"])
        self.assertEqual(
            {
                "stable_conformance_classes": 4,
                "stable_conformance_cases": 65,
                "mki_operations": 6,
                "world_kernel_interaction_classes": 5,
                "released_version": "1.0.0-rc.1",
            },
            self.contract["preserved_counts"],
        )

    def test_source_node_forms_match_the_closed_program_instruction_set(self) -> None:
        target = set(
            self.program_schema["$defs"]["node"]["properties"]["instruction"]["enum"]
        )
        lowered = {item["instruction"] for item in self.contract["node_lowering"]}
        self.assertEqual(target, lowered)
        self.assertEqual(
            set(
                self.program_schema["$defs"]["programOutput"]["properties"]["kind"]["enum"]
            ),
            set(self.contract["output_kinds"]),
        )

    def test_source_limits_do_not_widen_magical_program_limits(self) -> None:
        source = self.contract["limits"]
        target = MagicalProgramHostLimits()
        comparisons = {
            "source_utf8_bytes": target.max_bytes,
            "values": target.max_values,
            "nodes": target.max_nodes,
            "edges": target.max_edges,
            "outputs": target.max_outputs,
            "structured_depth": target.max_structured_depth,
            "structured_items": target.max_structured_items,
            "record_fields": target.max_record_fields,
            "sequence_items": target.max_sequence_items,
            "budget_events": target.max_events,
            "budget_microsteps": target.max_microsteps,
            "budget_concurrency": target.max_concurrency,
            "budget_energy_j": target.max_energy_j,
        }
        for key, ceiling in comparisons.items():
            with self.subTest(limit=key):
                self.assertLessEqual(source[key], ceiling)

    def test_grammar_is_closed_and_covers_every_mapping_form(self) -> None:
        for token in (
            '"mgls"',
            '"selector"',
            '"reference_hint"',
            '"evidence_hint"',
            '"resolve"',
            '"calculate"',
            '"compare"',
            '"rank"',
            '"require"',
            '"observe"',
            '"effect"',
            '"requires"',
            '"output"',
        ):
            self.assertIn(token, self.grammar)
        for forbidden in (
            '"import"',
            '"while"',
            '"for"',
            '"repeat"',
            '"async"',
            '"await"',
            '"set"',
            '"python"',
        ):
            self.assertNotIn(forbidden, self.grammar)
        self.assertNotIn("SA-", self.grammar)
        self.assertNotIn("SUCCESS-ARCANA", self.grammar)

    def test_numeric_literal_grammar_has_one_lexical_owner(self) -> None:
        self.assertIn(
            "scalar-literal          = string | number | boolean | null ;",
            self.grammar,
        )
        self.assertIn(
            "selector-scalar         = string | number | boolean ;",
            self.grammar,
        )
        self.assertNotIn("number | integer", self.grammar)
        self.assertIn(
            "integer                 = [ \"-\" ], ( \"0\" | nonzero-digit, { digit } ) ;",
            self.grammar,
        )

    def test_positive_examples_have_authoritative_headers_and_unique_nodes(self) -> None:
        forbidden = re.compile(
            r"\b(import|include|module|macro|eval|while|for|repeat|async|await|spawn|set|shell)\b"
        )
        expected_header = (
            r'^mgls "0";\n'
            r'source "[A-Za-z0-9][A-Za-z0-9._:-]*";\n'
            r'program "[A-Za-z0-9][A-Za-z0-9._:-]*";\n'
            r'registry "[A-Za-z0-9][A-Za-z0-9._:-]*" revision "[A-Za-z0-9][A-Za-z0-9._:-]*";\n'
            r'profile "[A-Za-z0-9][A-Za-z0-9._:-]*" revision "[A-Za-z0-9][A-Za-z0-9._:-]*";'
        )
        for relative in self.contract["positive_examples"]:
            source = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(example=relative):
                self.assertRegex(source, expected_header)
                self.assertIsNone(forbidden.search(source))
                nodes = re.findall(r"(?m)^node\s+([A-Za-z_][A-Za-z0-9_]*)", source)
                self.assertTrue(nodes)
                self.assertEqual(len(nodes), len(set(nodes)))
                outputs = re.findall(r'(?m)^output\s+"([^"]+)"', source)
                self.assertTrue(outputs)
                self.assertEqual(len(outputs), len(set(outputs)))

    def test_diagnostic_catalog_reuses_existing_error_owners(self) -> None:
        errors = (ROOT / "reference" / "errors.md").read_text(encoding="utf-8")
        catalog = {item["code"] for item in self.contract["diagnostics"]}
        for code in catalog:
            with self.subTest(code=code):
                self.assertIn(code, errors)
        self.assertNotIn("MglsDiagnostic", self.reference)
        self.assertNotIn("MGLS_ERROR", self.reference)

    def test_negative_inventory_is_complete_unique_and_fail_closed(self) -> None:
        inventory = load(NEGATIVE_PATH)
        cases = inventory["cases"]
        self.assertEqual(15, len(cases))
        self.assertEqual(len(cases), len({item["case_id"] for item in cases}))
        known = {item["code"] for item in self.contract["diagnostics"]}
        for item in cases:
            with self.subTest(case=item["case_id"]):
                self.assertIn(item["expected_diagnostic"], known)
                self.assertTrue(item["must_not_emit_program"])

    def test_source_map_schema_is_valid_and_accepts_a_minimal_mapping(self) -> None:
        Draft202012Validator.check_schema(self.source_map_schema)
        document = {
            "artifact_kind": "MglsSourceMap",
            "artifact_version": "0",
            "contract": {"contract_id": "mgls-source-map", "revision": "0"},
            "source": {
                "contract_id": "mgls-source",
                "revision": "0",
                "source_id": "source:bounded-transition:001",
                "offset_unit": "unicode-scalar",
                "normalization": "SourceTextNormalizerV1",
            },
            "target": {
                "artifact_kind": "MagicalProgram",
                "artifact_version": "0",
                "program_id": "program:bounded-transition:001",
            },
            "compiler": {
                "compiler_id": "compiler:mgls-reference",
                "compiler_revision": "0",
            },
            "entries": [
                {
                    "entry_id": "map:header:program",
                    "source_span": {"start": 50, "end": 87},
                    "relation": "exact",
                    "target": {
                        "section": "root",
                        "id": "program:bounded-transition:001",
                        "field": "program_id",
                    },
                }
            ],
        }
        Draft202012Validator(self.source_map_schema).validate(document)

    def test_cross_document_owners_reference_the_frozen_contract(self) -> None:
        naming = (ROOT / "reference" / "file-naming.md").read_text(encoding="utf-8")
        ingress = (ROOT / "reference" / "multi-stage-ingress.md").read_text(encoding="utf-8")
        for text in (naming, ingress):
            self.assertIn("mgls-source-language.md", text)
            self.assertIn("mgls-source", text)
            self.assertIn("revision `0`", text)


if __name__ == "__main__":
    unittest.main()
