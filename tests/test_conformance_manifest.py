from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.run_conformance import ConformanceManifestError, load_manifest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "conformance" / "manifest.json"
RUNNER = ROOT / "tools" / "run_conformance.py"


class ConformanceManifestTests(unittest.TestCase):
    def test_initial_manifest_has_exact_four_classes_and_unique_stable_ids(self) -> None:
        manifest = load_manifest(MANIFEST)
        classes = {item["class_id"]: item for item in manifest["classes"]}
        self.assertEqual(
            {"Core-1.0", "Evaluator-1.0", "Adapter-lat-1.0", "Runtime-1.0"},
            set(classes),
        )
        case_ids = [item["case_id"] for item in manifest["cases"]]
        self.assertEqual(len(case_ids), len(set(case_ids)))
        self.assertIn("WB-TEST-006", case_ids)
        self.assertIn("WB-TEST-008", case_ids)
        self.assertIn("EVAL-RESOLUTION-001", case_ids)
        self.assertIn("EVAL-SERIALIZATION-001", case_ids)
        self.assertIn("RUNTIME-IDENTITY-001", case_ids)
        self.assertIn("RUNTIME-KERNEL-SEMANTICS-001", case_ids)
        self.assertIn("RUNTIME-SERIALIZATION-001", case_ids)
        self.assertIn("CORE-COMPAT-COVERAGE-001", case_ids)
        self.assertIn("CORE-COMPAT-COVERAGE-002", case_ids)
        self.assertIn("CORE-COMPAT-MIGRATION-PROFILE-001", case_ids)

    def test_runtime_class_is_released_in_v1_rc1(self) -> None:
        manifest = load_manifest(MANIFEST)
        runtime = next(
            item for item in manifest["classes"] if item["class_id"] == "Runtime-1.0"
        )
        self.assertEqual("released", runtime["status"])
        self.assertNotIn("blocked_by", runtime)
        self.assertNotIn("pending_rule_areas", runtime)
        self.assertIn(
            {
                "document": "reference/kernel-execution.md",
                "heading": "## 13. Runtime-1.0 conformance obligations",
            },
            runtime["normative_references"],
        )
        self.assertTrue(
            {
                "RUNTIME-KERNEL-ABI-001",
                "RUNTIME-KERNEL-CLASS-001",
                "RUNTIME-ACTIVE-EFFECT-001",
                "RUNTIME-KERNEL-LIFECYCLE-001",
                "RUNTIME-KERNEL-ATOMIC-001",
                "RUNTIME-KERNEL-SEMANTICS-001",
                "RUNTIME-KERNEL-TIME-001",
                "RUNTIME-IDENTITY-001",
                "RUNTIME-SERIALIZATION-001",
            }.issubset(runtime["required_case_ids"])
        )

    def test_released_and_candidate_classes_require_only_required_cases(self) -> None:
        manifest = load_manifest(MANIFEST)
        cases = {item["case_id"]: item for item in manifest["cases"]}
        for class_def in manifest["classes"]:
            if class_def["status"] not in {"released", "candidate"}:
                continue
            for case_id in class_def["required_case_ids"]:
                self.assertEqual("required", cases[case_id]["requirement"])

    def test_duplicate_case_id_is_rejected_even_when_schema_shape_is_valid(self) -> None:
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
        payload["cases"].append(copy.deepcopy(payload["cases"][0]))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ConformanceManifestError, "duplicate case ID"):
                load_manifest(path)

    def test_missing_normative_heading_is_rejected(self) -> None:
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
        payload["cases"][0]["rule_refs"][0]["heading"] = "## Definitely Missing Heading"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ConformanceManifestError, "missing normative heading"):
                load_manifest(path)

    def test_runner_lists_manifest_deterministically(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(RUNNER), "--list"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("CLASS Core-1.0 released", completed.stdout)
        self.assertIn("CLASS Runtime-1.0 released", completed.stdout)
        self.assertIn("CASE WB-TEST-006 requirement=required", completed.stdout)
        self.assertIn("CASE WB-TEST-008 requirement=required", completed.stdout)
        self.assertIn("CASE EVAL-RESOLUTION-001 requirement=required", completed.stdout)
        self.assertIn(
            "CASE RUNTIME-KERNEL-SEMANTICS-001 requirement=required",
            completed.stdout,
        )
        self.assertIn("CASE RUNTIME-SERIALIZATION-001 requirement=required", completed.stdout)

    def test_runner_executes_core_class_by_stable_case_id_mapping(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(RUNNER), "--class", "Core-1.0"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertIn("PASS CORE-COMPAT-001", completed.stdout)
        self.assertIn("PASS CORE-COMPAT-COVERAGE-001", completed.stdout)
        self.assertIn("PASS CORE-COMPAT-COVERAGE-002", completed.stdout)
        self.assertIn("PASS CORE-COMPAT-MIGRATION-001", completed.stdout)
        self.assertIn("PASS CORE-COMPAT-MIGRATION-AUTHORITY-001", completed.stdout)
        self.assertIn("PASS WB-TEST-006", completed.stdout)
        self.assertIn("PASS WB-TEST-008", completed.stdout)
        self.assertIn("RESULT passed=29 failed=0", completed.stdout)

    def test_runner_executes_runtime_class_with_kernel_boundary_cases(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(RUNNER), "--class", "Runtime-1.0"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertIn("PASS RUNTIME-IDENTITY-001", completed.stdout)
        self.assertIn("PASS RUNTIME-KERNEL-ABI-001", completed.stdout)
        self.assertIn("PASS RUNTIME-KERNEL-SEMANTICS-001", completed.stdout)
        self.assertIn("PASS RUNTIME-SERIALIZATION-001", completed.stdout)
        self.assertIn("RESULT passed=20 failed=0", completed.stdout)

    def test_blocked_class_path_remains_fail_closed_for_future_dependencies(self) -> None:
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
        runtime = next(
            item for item in payload["classes"] if item["class_id"] == "Runtime-1.0"
        )
        runtime["status"] = "blocked"
        runtime["blocked_by"] = ["synthetic future dependency"]

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--manifest",
                    str(path),
                    "--class",
                    "Runtime-1.0",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(2, completed.returncode)
            self.assertIn("blocked conformance class selected", completed.stderr)

            measured = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--manifest",
                    str(path),
                    "--class",
                    "Runtime-1.0",
                    "--include-blocked",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, measured.returncode, measured.stdout + measured.stderr)
            self.assertIn("CLASS Runtime-1.0 blocked", measured.stdout)
        self.assertIn("RESULT passed=20 failed=0", measured.stdout)


if __name__ == "__main__":
    unittest.main()
