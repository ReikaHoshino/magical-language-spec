from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
COVERAGE = ROOT / "conformance" / "rule-coverage.json"
MANIFEST = ROOT / "conformance" / "manifest.json"
SCHEMA = ROOT / "schemas" / "conformance-coverage.schema.json"


class ConformanceRuleCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.coverage = json.loads(COVERAGE.read_text(encoding="utf-8"))
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    def test_coverage_inventory_is_schema_valid_and_version_aligned(self) -> None:
        Draft202012Validator(self.schema).validate(self.coverage)
        self.assertEqual(
            self.manifest["suite"]["suite_version"],
            self.coverage["suite_version"],
        )

    def test_rule_ids_are_unique_and_normative_headings_exist(self) -> None:
        rule_ids = [item["rule_id"] for item in self.coverage["rules"]]
        self.assertEqual(len(rule_ids), len(set(rule_ids)))
        for rule in self.coverage["rules"]:
            document = ROOT / rule["document"]
            self.assertTrue(document.is_file(), rule["document"])
            self.assertIn(
                rule["heading"],
                document.read_text(encoding="utf-8").splitlines(),
                f"missing heading for {rule['rule_id']}",
            )

    def test_covered_rules_reference_existing_cases_in_the_same_class(self) -> None:
        cases = {item["case_id"]: item for item in self.manifest["cases"]}
        for rule in self.coverage["rules"]:
            if rule["status"] != "covered":
                continue
            for case_id in rule["case_ids"]:
                self.assertIn(case_id, cases, rule["rule_id"])
                self.assertIn(rule["class_id"], cases[case_id]["class_ids"], case_id)

    def test_every_candidate_required_case_has_reverse_rule_coverage(self) -> None:
        covered_case_ids = {
            case_id
            for rule in self.coverage["rules"]
            if rule["status"] == "covered"
            for case_id in rule["case_ids"]
        }
        required_case_ids = {
            case_id
            for class_def in self.manifest["classes"]
            if class_def["status"] == "candidate"
            for case_id in class_def["required_case_ids"]
        }
        self.assertEqual(required_case_ids, required_case_ids & covered_case_ids)

    def test_deferred_or_non_executable_rules_have_explicit_rationale(self) -> None:
        deferred = [
            item
            for item in self.coverage["rules"]
            if item["status"] in {"deferred", "non-executable"}
        ]
        self.assertTrue(deferred)
        for rule in deferred:
            self.assertTrue(rule.get("rationale", "").strip(), rule["rule_id"])
            self.assertFalse(rule.get("case_ids"), rule["rule_id"])

    def test_all_four_candidate_classes_have_coverage_inventory_entries(self) -> None:
        classes = {item["class_id"] for item in self.coverage["rules"]}
        self.assertEqual(
            {"Core-1.0", "Evaluator-1.0", "Adapter-lat-1.0", "Runtime-1.0"},
            classes,
        )


if __name__ == "__main__":
    unittest.main()
