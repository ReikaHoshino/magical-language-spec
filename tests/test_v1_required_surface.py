from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "conformance" / "manifest.json"
MATRIX = ROOT / "conformance" / "v1-required-surface.json"
SCHEMA = ROOT / "schemas" / "v1-required-surface.schema.json"


class V1RequiredSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    def test_matrix_is_schema_valid_and_release_aligned(self) -> None:
        Draft202012Validator(self.schema).validate(self.matrix)
        self.assertEqual(
            self.manifest["suite"]["suite_version"],
            self.matrix["suite_version"],
        )

    def test_all_issue_38_required_claims_are_present_exactly_once(self) -> None:
        expected = {f"V1-CONF-{number:03d}" for number in range(1, 15)}
        actual = {
            requirement["requirement_id"]
            for requirement in self.matrix["requirements"]
        }
        self.assertEqual(expected, actual)

    def test_every_matrix_case_is_required_by_a_named_class(self) -> None:
        cases = {item["case_id"]: item for item in self.manifest["cases"]}
        required_by_class = {
            item["class_id"]: set(item["required_case_ids"])
            for item in self.manifest["classes"]
        }
        for requirement in self.matrix["requirements"]:
            named_classes = set(requirement["class_ids"])
            for case_id in requirement["case_ids"]:
                self.assertIn(case_id, cases, requirement["requirement_id"])
                self.assertEqual("required", cases[case_id]["requirement"])
                owning_classes = set(cases[case_id]["class_ids"])
                self.assertTrue(
                    named_classes & owning_classes,
                    f"{case_id} has no class overlap for {requirement['requirement_id']}",
                )
                self.assertTrue(
                    any(case_id in required_by_class[class_id] for class_id in owning_classes),
                    f"{case_id} is not required by its owning class",
                )


if __name__ == "__main__":
    unittest.main()
