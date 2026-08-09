from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from src.evaluator import LocalEvaluator
from src.runtime import ReferenceRuntimeEngine, SandboxProfile, canonical_sandbox_world


ROOT = Path(__file__).resolve().parents[1]


class ReferenceRuntimeEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pipeline = json.loads(
            (ROOT / "examples" / "canonical-water-ball" / "pipeline.json").read_text(
                encoding="utf-8"
            )
        )
        cls.report = LocalEvaluator().evaluate_nsr(pipeline["normalization"]["nsr"])

    def test_scheduler_records_canonical_phase_order(self) -> None:
        world = canonical_sandbox_world()
        result = ReferenceRuntimeEngine().execute_strict(self.report, world)

        self.assertEqual(result["status"], "Committed")
        self.assertEqual(
            result["scheduler"]["phase_order"],
            [
                "Ingress",
                "ContinuousAdvance",
                "Revalidate",
                "Commit",
                "PublishSnapshot",
                "Control",
                "IndexUpdate",
                "Dispatch",
            ],
        )
        self.assertFalse(result["scheduler"]["physical_time_is_runtime_tick"])
        records = {record["phase"]: record for record in result["scheduler"]["records"]}
        self.assertEqual(records["Revalidate"]["status"], "Pass")
        self.assertEqual(records["PublishSnapshot"]["world_revision"], "world:992")
        self.assertTrue(records["Control"]["controller_registered"])
        self.assertEqual(records["Dispatch"]["history_event_id"], "event:wb-canon-001")

    def test_sandbox_energy_ceiling_fails_closed_without_mutation(self) -> None:
        world = canonical_sandbox_world()
        profile = SandboxProfile(max_energy_j=100.0)
        result = ReferenceRuntimeEngine(sandbox_profile=profile).execute(self.report, world)

        self.assertEqual(result["status"], "Aborted")
        self.assertEqual(result["abort"]["code"], "SandboxLimitExceeded")
        self.assertTrue(result["world_revision_unchanged"])
        self.assertTrue(result["history_unchanged"])
        self.assertEqual(world.revision, "world:991")

    def test_unknown_energy_does_not_become_zero_for_runtime_admission(self) -> None:
        report = copy.deepcopy(self.report)
        report["energy"]["total"] = {
            "kind": "Unknown",
            "reason": "EstimatorModelUnavailable",
            "unit": "J",
            "dimension": "Energy",
            "assumption_ids": [],
            "evidence_ids": [],
        }
        world = canonical_sandbox_world()

        result = ReferenceRuntimeEngine().execute(report, world)

        self.assertEqual(result["status"], "Aborted")
        self.assertEqual(result["abort"]["code"], "SandboxBudgetIndeterminate")
        self.assertEqual(world.revision, "world:991")

    def test_zero_microstep_budget_aborts_before_prepare(self) -> None:
        world = canonical_sandbox_world()
        profile = SandboxProfile(max_microsteps_per_tick=0)

        result = ReferenceRuntimeEngine(sandbox_profile=profile).execute(self.report, world)

        self.assertEqual(result["status"], "Aborted")
        self.assertEqual(result["abort"]["code"], "MicrostepBudgetExceeded")
        self.assertEqual(world.history, [])

    def test_zero_event_budget_aborts_before_commit(self) -> None:
        world = canonical_sandbox_world()
        profile = SandboxProfile(max_events_per_commit=0)

        result = ReferenceRuntimeEngine(sandbox_profile=profile).execute(self.report, world)

        self.assertEqual(result["status"], "Aborted")
        self.assertEqual(result["abort"]["code"], "EventBudgetExceeded")
        self.assertEqual(world.revision, "world:991")

    def test_replay_manifest_distinguishes_replay_from_rewind(self) -> None:
        initial = canonical_sandbox_world()
        engine = ReferenceRuntimeEngine()
        result = engine.execute_strict(self.report, initial.clone())

        replay = engine.replay(self.report, initial, result)

        self.assertEqual(replay["status"], "Match")
        self.assertFalse(replay["manifest"]["replay_is_rewind"])
        self.assertFalse(replay["manifest"]["physical_time_is_runtime_tick"])
        self.assertEqual(initial.revision, "world:991")

    def test_late_unrelated_entity_does_not_retarget_prepare_bound_terminal(self) -> None:
        world = canonical_sandbox_world()
        engine = ReferenceRuntimeEngine()
        prepared = engine.runtime.prepare(self.report, world)
        world.entities["entity:late-entry"] = {
            "entity_id": "entity:late-entry",
            "state_revision": "state-revision:late-entry@world:991",
            "kind": "Agent",
            "visible": True,
        }
        before_assumptions = copy.deepcopy(prepared.assumptions)

        trace = engine.runtime.commit(prepared, world)

        ball = world.entities["entity:water-ball:wb-canon-001"]
        self.assertEqual(ball["terminal_binding"], before_assumptions)
        self.assertEqual(trace["world_effect"]["history_event_id"], "event:wb-canon-001")


if __name__ == "__main__":
    unittest.main()
