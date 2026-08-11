from __future__ import annotations

import importlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = json.loads(
    (ROOT / "conformance" / "experimental-user-workflow.json").read_text(
        encoding="utf-8"
    )
)
REFERENCE = (ROOT / "reference" / "user-workflow.md").read_text(encoding="utf-8")
MANIFEST = json.loads(
    (ROOT / "conformance" / "manifest.json").read_text(encoding="utf-8")
)


class UserWorkflowConformanceTests(unittest.TestCase):
    maxDiff = None

    def test_inventory_is_experimental_unique_and_release_aligned(self) -> None:
        self.assertEqual("ExperimentalConformanceInventory", INVENTORY["artifact_kind"])
        self.assertEqual("0", INVENTORY["artifact_version"])
        self.assertEqual("experimental", INVENTORY["stability"])
        self.assertEqual("1.0.0-rc.1", INVENTORY["spec_version"])
        self.assertTrue(INVENTORY["excluded_from_stable_manifest"])
        cases = INVENTORY["cases"]
        self.assertEqual(
            [f"UX-E2E-{index:03d}" for index in range(1, 12)],
            [item["case_id"] for item in cases],
        )
        self.assertEqual(len(cases), len({item["case_id"] for item in cases}))
        self.assertTrue(all(item["rules"] for item in cases))

    def test_every_owned_rule_has_a_normative_heading(self) -> None:
        rules = {
            rule for item in INVENTORY["cases"] for rule in item["rules"]
        }
        for rule in sorted(rules):
            with self.subTest(rule=rule):
                self.assertIn(f"### {rule} —", REFERENCE)

    def test_every_python_test_locator_resolves(self) -> None:
        for item in INVENTORY["cases"]:
            locator = item["test"]
            if locator == "tools.package_program_eval_smoke.main":
                module = importlib.import_module("tools.package_program_eval_smoke")
                self.assertTrue(callable(module.main))
                continue
            module_name, class_name, method_name = locator.rsplit(".", 2)
            module = importlib.import_module(module_name)
            owner = getattr(module, class_name)
            self.assertTrue(callable(getattr(owner, method_name)))

    def test_stable_manifest_remains_four_classes_and_sixty_five_cases(self) -> None:
        expected = INVENTORY["stable_manifest_expectation"]
        self.assertEqual(expected["class_count"], len(MANIFEST["classes"]))
        self.assertEqual(expected["required_case_count"], len(MANIFEST["cases"]))
        self.assertEqual(
            ["Core-1.0", "Evaluator-1.0", "Adapter-lat-1.0", "Runtime-1.0"],
            [item["class_id"] for item in MANIFEST["classes"]],
        )
        self.assertFalse(
            any(item["case_id"].startswith("UX-E2E-") for item in MANIFEST["cases"])
        )

    def test_reference_preserves_authority_and_compatibility_boundaries(self) -> None:
        for marker in (
            "CLI routing != semantic dispatch",
            "compiler success != target admission",
            "Evaluation != Execution",
            "syntax != authority",
            "same semantic dispatch\n!= same occurrence identity",
            "package version                     1.0.0rc1",
        ):
            self.assertIn(marker, REFERENCE)


if __name__ == "__main__":
    unittest.main()
