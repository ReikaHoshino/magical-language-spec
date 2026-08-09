from __future__ import annotations

import json
import unittest
from pathlib import Path

from src.evaluator import LocalEvaluator
from src.runtime import ReferenceRuntimeEngine, SandboxProfile, canonical_sandbox_world
from src.runtime.schema import validate_execution_trace


ROOT = Path(__file__).resolve().parents[1]


class RuntimeExecutionSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pipeline = json.loads(
            (ROOT / "examples" / "canonical-water-ball" / "pipeline.json").read_text(
                encoding="utf-8"
            )
        )
        cls.report = LocalEvaluator().evaluate_nsr(pipeline["normalization"]["nsr"])

    def test_committed_runtime_trace_validates(self) -> None:
        trace = ReferenceRuntimeEngine().execute_strict(
            self.report, canonical_sandbox_world()
        )
        validate_execution_trace(trace)
        self.assertEqual(trace["source_world_revision"], "world:991")
        self.assertEqual(trace["world_revision"], "world:992")
        self.assertEqual(
            [record["operation"] for record in trace["control_plane"]],
            ["ACQUIRE", "COMMIT", "RELEASE"],
        )

    def test_aborted_runtime_trace_validates(self) -> None:
        trace = ReferenceRuntimeEngine(
            sandbox_profile=SandboxProfile(max_energy_j=100.0)
        ).execute(self.report, canonical_sandbox_world())
        validate_execution_trace(trace)
        self.assertEqual(trace["status"], "Aborted")
        self.assertEqual(trace["control_plane"][0]["operation"], "ABORT")
        self.assertTrue(trace["world_revision_unchanged"])
        self.assertTrue(trace["history_unchanged"])

    def test_v09_control_plane_does_not_claim_revoke_or_delegate(self) -> None:
        trace = ReferenceRuntimeEngine().execute_strict(
            self.report, canonical_sandbox_world()
        )
        operations = {record["operation"] for record in trace["control_plane"]}
        self.assertNotIn("REVOKE", operations)
        self.assertNotIn("DELEGATE", operations)


if __name__ == "__main__":
    unittest.main()
