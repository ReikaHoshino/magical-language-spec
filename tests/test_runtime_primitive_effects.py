from __future__ import annotations

import json
import unittest
from pathlib import Path

from src.evaluator import LocalEvaluator
from src.runtime import ReferenceRuntimeEngine, canonical_sandbox_world


ROOT = Path(__file__).resolve().parents[1]


class RuntimePrimitiveEffectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pipeline = json.loads(
            (ROOT / "examples" / "canonical-water-ball" / "pipeline.json").read_text(
                encoding="utf-8"
            )
        )
        cls.report = LocalEvaluator().evaluate_nsr(pipeline["normalization"]["nsr"])

    def test_canonical_execution_exercises_exactly_six_mki_primitives(self) -> None:
        world = canonical_sandbox_world()
        trace = ReferenceRuntimeEngine().execute_strict(self.report, world)
        operations = [item["operation"] for item in trace["runtime"]["operations"]]

        self.assertEqual(
            operations,
            ["RESOLVE", "OBSERVE", "CHANNEL", "TRANSFER", "RECONFIGURE", "CONSTRAIN"],
        )
        self.assertNotIn("GENERATE", operations)
        self.assertNotIn("CREATE", operations)
        self.assertNotIn("COMMIT", operations)

    def test_resolve_and_observe_require_authoritative_source_evidence(self) -> None:
        world = canonical_sandbox_world()
        trace = ReferenceRuntimeEngine().execute_strict(self.report, world)

        evidence = trace["runtime"]["revalidation"]["evidence_ids"]
        self.assertIn("state-revision:source-water@world:991", evidence)
        self.assertIn("capability:source-water", evidence)
        self.assertIn("ledger:matter-energy", evidence)
        self.assertIn("entity:source-water", world.entities)

    def test_channel_transfer_and_reconfigure_have_concrete_poststate(self) -> None:
        world = canonical_sandbox_world()
        ReferenceRuntimeEngine().execute_strict(self.report, world)

        channel = world.runtime_state["channels"]["channel:matter:source-water"]
        self.assertTrue(channel["open"])
        self.assertEqual(channel["payload_entity_id"], "entity:water-ball:wb-canon-001")
        self.assertEqual(world.entities["entity:source-water"]["mass_kg"], 50.0)
        self.assertEqual(
            world.entities["entity:water-ball:wb-canon-001"]["mass_kg"], 50.0
        )
        self.assertEqual(world.revision, "world:992")

    def test_constrain_registers_controller_without_removing_gravity(self) -> None:
        world = canonical_sandbox_world()
        ReferenceRuntimeEngine().execute_strict(self.report, world)

        controller = world.controllers["controller:wb-canon-001"]
        self.assertTrue(controller["active"])
        self.assertEqual(controller["mode"], "horizontal-trajectory")
        self.assertFalse(controller["gravity_removed"])

    def test_control_plane_release_releases_prepared_reservation_not_authority(self) -> None:
        world = canonical_sandbox_world()
        trace = ReferenceRuntimeEngine().execute_strict(self.report, world)

        release = next(
            record for record in trace["control_plane"] if record["operation"] == "RELEASE"
        )
        self.assertEqual(
            release["evidence_ids"], ["reservation:wb-canon-001:energy"]
        )
        self.assertTrue(world.leases["lease:source-water"]["active"])
        self.assertEqual(world.runtime_state["reservations"], {})


if __name__ == "__main__":
    unittest.main()
