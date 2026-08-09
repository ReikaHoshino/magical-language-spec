from __future__ import annotations

import json
import unittest
from pathlib import Path

from src.evaluator import LocalEvaluator
from src.runtime import RuntimeExecutionError, SandboxRuntime, canonical_sandbox_world


ROOT = Path(__file__).resolve().parents[1]


class SandboxRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pipeline = json.loads(
            (ROOT / "examples" / "canonical-water-ball" / "pipeline.json").read_text(
                encoding="utf-8"
            )
        )
        cls.canonical_nsr = pipeline["normalization"]["nsr"]
        cls.report = LocalEvaluator().evaluate_nsr(cls.canonical_nsr)

    def setUp(self) -> None:
        self.runtime = SandboxRuntime()
        self.world = canonical_sandbox_world()

    def test_prepare_is_reversible_and_does_not_mutate_world(self) -> None:
        before = self.world.clone()
        prepared = self.runtime.prepare(self.report, self.world)

        self.assertEqual(prepared.plan_id, "wb:plan:transfer-reconfigure")
        self.assertEqual(self.world, before)
        self.assertEqual(prepared.source_world_revision, "world:991")
        self.assertIn("CONSTRAIN", prepared.operations)

    def test_canonical_plan_commits_expected_world_and_history(self) -> None:
        trace = self.runtime.execute(self.report, self.world)

        self.assertEqual(self.world.revision, "world:992")
        self.assertEqual(len(self.world.history), 1)
        self.assertEqual(self.world.history[0]["event_id"], "event:wb-canon-001")
        ball = self.world.entities["entity:water-ball:wb-canon-001"]
        self.assertEqual(ball["mass_kg"], 50.0)
        self.assertEqual(ball["radius_m"], 0.01)
        self.assertEqual(ball["relative_distance_m"], 3.0)
        self.assertEqual(ball["initial_velocity_m_s"], 0.0)
        self.assertEqual(ball["acceleration_m_s2"], 50.0)
        self.assertEqual(ball["trajectory"], "horizontal-forward")
        self.assertTrue(ball["terminal_binding"])
        self.assertFalse(
            self.world.controllers["controller:wb-canon-001"]["gravity_removed"]
        )
        self.assertEqual(trace["commit"]["tick_stamp"]["phase"], "Commit")
        self.assertFalse(trace["physical_time_is_runtime_tick"])
        self.assertEqual(trace["world_effect"]["result_world_revision"], "world:992")
        self.assertEqual(self.world.process_state["process_id"], "process:wb-canon-001")
        self.assertEqual(
            trace["reservations"][0]["reservation_id"],
            "reservation:wb-canon-001:energy",
        )

    def test_stale_world_revision_fails_before_mutation(self) -> None:
        prepared = self.runtime.prepare(self.report, self.world)
        self.world.revision = "world:992-unrelated-change"
        before = self.world.clone()

        with self.assertRaises(RuntimeExecutionError) as raised:
            self.runtime.commit(prepared, self.world)

        self.assertEqual(raised.exception.code, "StaleReference")
        self.assertEqual(self.world, before)

    def test_revoked_capability_fails_before_mutation(self) -> None:
        prepared = self.runtime.prepare(self.report, self.world)
        self.world.capabilities["capability:source-water"]["active"] = False
        before = self.world.clone()

        with self.assertRaises(RuntimeExecutionError) as raised:
            self.runtime.commit(prepared, self.world)

        self.assertEqual(raised.exception.code, "AuthorityError")
        self.assertEqual(self.world, before)

    def test_expired_lease_fails_before_mutation(self) -> None:
        prepared = self.runtime.prepare(self.report, self.world)
        self.world.leases["lease:source-water"]["active"] = False
        before = self.world.clone()

        with self.assertRaises(RuntimeExecutionError) as raised:
            self.runtime.commit(prepared, self.world)

        self.assertEqual(raised.exception.code, "AuthorityError")
        self.assertEqual(self.world, before)

    def test_missing_conservation_evidence_fails_before_mutation(self) -> None:
        prepared = self.runtime.prepare(self.report, self.world)
        self.world.ledgers["ledger:matter-energy"]["active"] = False
        before = self.world.clone()

        with self.assertRaises(RuntimeExecutionError) as raised:
            self.runtime.commit(prepared, self.world)

        self.assertEqual(raised.exception.code, "ConservationProofFailure")
        self.assertEqual(self.world, before)

    def test_emergency_stop_fences_prepare_and_commit(self) -> None:
        prepared = self.runtime.prepare(self.report, self.world)
        stop = self.runtime.request_emergency_stop(self.world, reason="test stop")
        self.assertEqual(stop["state"], "Fenced")
        before = self.world.clone()

        with self.assertRaises(RuntimeExecutionError) as commit_error:
            self.runtime.commit(prepared, self.world)
        self.assertEqual(commit_error.exception.code, "EmergencyStopFence")
        self.assertEqual(self.world, before)

        with self.assertRaises(RuntimeExecutionError) as prepare_error:
            self.runtime.prepare(self.report, self.world)
        self.assertEqual(prepare_error.exception.code, "EmergencyStopFence")

    def test_replay_runs_in_separate_world_and_matches_trace(self) -> None:
        initial = self.world.clone()
        trace = self.runtime.execute(self.report, self.world)

        replay = self.runtime.replay(self.report, initial, trace)

        self.assertEqual(replay["status"], "Match")
        self.assertFalse(replay["same_world_object"])
        self.assertEqual(
            replay["expected_state_hash"], replay["observed_state_hash"]
        )
        self.assertEqual(initial.revision, "world:991")

    def test_replay_detects_divergence(self) -> None:
        initial = self.world.clone()
        trace = self.runtime.execute(self.report, self.world)
        trace["result_state_hash"] = "0" * 64

        replay = self.runtime.replay(self.report, initial, trace)

        self.assertEqual(replay["status"], "Diverged")
        self.assertNotEqual(
            replay["expected_state_hash"], replay["observed_state_hash"]
        )


if __name__ == "__main__":
    unittest.main()
