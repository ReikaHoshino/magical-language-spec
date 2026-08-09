from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference" / "conformance.md"
MANIFEST = ROOT / "conformance" / "manifest.json"


class ConformanceReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reference = REFERENCE.read_text(encoding="utf-8")
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_four_initial_class_names_are_normative_and_manifested(self) -> None:
        class_ids = {item["class_id"] for item in self.manifest["classes"]}
        for class_id in ("Core-1.0", "Evaluator-1.0", "Adapter-lat-1.0", "Runtime-1.0"):
            self.assertIn(class_id, self.reference)
            self.assertIn(class_id, class_ids)

    def test_stable_case_identity_is_distinct_from_test_method_name(self) -> None:
        self.assertIn("stable case ID != test method name", self.reference)
        self.assertIn("test method/fileはimplementation evidence locator", self.reference)

    def test_blocked_measurement_rule_remains_defined_after_runtime_unblocks(self) -> None:
        self.assertIn("blocked baseline all green != class conformance", self.reference)
        self.assertIn("--include-blocked", self.reference)
        runtime = next(
            item for item in self.manifest["classes"] if item["class_id"] == "Runtime-1.0"
        )
        self.assertEqual("candidate", runtime["status"])
        self.assertIn("Issue #55はPR #57で解決済み", self.reference)

    def test_runtime_candidate_owns_kernel_execution_obligations(self) -> None:
        runtime = next(
            item for item in self.manifest["classes"] if item["class_id"] == "Runtime-1.0"
        )
        self.assertIn(
            {
                "document": "reference/kernel-execution.md",
                "heading": "## 13. Runtime-1.0 conformance obligations",
            },
            runtime["normative_references"],
        )
        self.assertIn("five World Kernel interaction classes", self.reference)
        self.assertIn("KernelAtomicGroup all-or-none semantics", self.reference)
        self.assertIn("public serialized ECIR", self.reference)

    def test_identity_resolution_and_serialization_have_stable_cases(self) -> None:
        cases = {item["case_id"] for item in self.manifest["cases"]}
        for case_id in (
            "WB-TEST-008",
            "EVAL-RESOLUTION-001",
            "EVAL-SERIALIZATION-001",
            "RUNTIME-IDENTITY-001",
            "RUNTIME-SERIALIZATION-001",
        ):
            self.assertIn(case_id, cases)

    def test_repository_regression_and_conformance_have_distinct_roles(self) -> None:
        self.assertIn("repository regression = implementation regression breadth", self.reference)
        self.assertIn("conformance runner     = promised semantic/class surface", self.reference)

    def test_compatibility_admission_remains_fail_closed_and_non_authorizing(self) -> None:
        for invariant in (
            "CompatibilityAdmission != Capability",
            "CompatibilityAdmission != Lease",
            "CompatibilityAdmission != trust proof",
        ):
            self.assertIn(invariant, self.reference)
        self.assertIn("required missing/Undetermined -> Indeterminate (not admitted)", self.reference)

    def test_clean_environment_commands_and_packaging_boundary_are_published(self) -> None:
        for command in (
            "python -m pip install --requirement requirements-dev.txt",
            "python tests/validate_schemas.py",
            "python tools/run_conformance.py",
            "python -m unittest discover -s tests -v",
            "python -m pip install --editable .",
            "magical-language-conformance",
            "magical-language-evaluator --source",
        ):
            self.assertIn(command, self.reference)
        self.assertIn("Issue #60", self.reference)
        self.assertIn("isolated wheel/sdist installed", self.reference)
        self.assertIn("historical v0.10 snapshotの限定保証は遡及変更しない", self.reference)

    def test_stabilization_release_does_not_imply_v1_rc_eligibility(self) -> None:
        self.assertIn("v0.12 landingだけを理由にv1.0 RC eligibilityを宣言しない", self.reference)
        self.assertIn("全gateを#40がcertify", self.reference)


if __name__ == "__main__":
    unittest.main()
