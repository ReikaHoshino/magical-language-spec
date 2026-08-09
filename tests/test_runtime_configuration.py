from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from src.evaluator import LocalEvaluator
from src.runtime import RuntimeExecutionError, SandboxRuntime, canonical_sandbox_world


ROOT = Path(__file__).resolve().parents[1]


class RuntimeConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pipeline = json.loads(
            (ROOT / "examples" / "canonical-water-ball" / "pipeline.json").read_text(
                encoding="utf-8"
            )
        )
        cls.report = LocalEvaluator().evaluate_nsr(pipeline["normalization"]["nsr"])

    def test_configuration_domains_are_explicit_and_distinct(self) -> None:
        world = canonical_sandbox_world()
        configuration = world.configuration()

        self.assertEqual(set(configuration), {"Sigma", "H", "Omega", "P"})
        self.assertEqual(configuration["Sigma"]["revision"], "world:991")
        self.assertEqual(configuration["H"], [])
        self.assertEqual(configuration["Omega"]["scheduler_phase"], "Ingress")
        self.assertEqual(configuration["P"]["status"], "Idle")

    def test_prepare_records_reservation_without_mutating_configuration(self) -> None:
        world = canonical_sandbox_world()
        before = world.configuration()

        prepared = SandboxRuntime().prepare(self.report, world)

        self.assertEqual(world.configuration(), before)
        self.assertEqual(len(prepared.resource_reservations), 1)
        self.assertEqual(prepared.resource_reservations[0]["amount_j"], 200.0)
        self.assertEqual(prepared.resource_reservations[0]["status"], "Prepared")

    def test_commit_updates_sigma_history_runtime_and_process_domains(self) -> None:
        world = canonical_sandbox_world()
        runtime = SandboxRuntime()
        prepared = runtime.prepare(self.report, world)

        trace = runtime.commit(prepared, world)

        configuration = trace["configuration"]
        self.assertEqual(configuration["Sigma"]["revision"], "world:992")
        self.assertEqual(configuration["H"][0]["event_id"], "event:wb-canon-001")
        self.assertEqual(configuration["Omega"]["tick"], "tick:fixture:25")
        self.assertEqual(configuration["Omega"]["scheduler_phase"], "Dispatch")
        self.assertEqual(configuration["P"]["status"], "Committed")
        self.assertEqual(configuration["Omega"]["reservations"], {})
        self.assertTrue(
            configuration["Omega"]["channels"]["channel:matter:source-water"]["open"]
        )

    def test_matter_ledger_remains_conserved_across_transfer_and_reconfigure(self) -> None:
        world = canonical_sandbox_world()
        runtime = SandboxRuntime()
        prepared = runtime.prepare(self.report, world)

        runtime.commit(prepared, world)

        ledger = world.ledgers["ledger:matter-energy"]
        self.assertEqual(ledger["accounted_mass_kg"], 100.0)
        self.assertEqual(sum(ledger["allocations_kg"].values()), 100.0)
        self.assertEqual(ledger["allocations_kg"]["entity:source-water"], 50.0)
        self.assertEqual(
            ledger["allocations_kg"]["entity:water-ball:wb-canon-001"], 50.0
        )

    def test_runtime_profile_drift_after_prepare_fails_without_mutation(self) -> None:
        world = canonical_sandbox_world()
        runtime = SandboxRuntime()
        prepared = runtime.prepare(self.report, world)
        world.runtime_state["runtime_profile"] = {
            "artifact_id": "runtime-profile:changed",
            "revision": "2",
        }
        before = copy.deepcopy(world)

        with self.assertRaises(RuntimeExecutionError) as raised:
            runtime.commit(prepared, world)

        self.assertEqual(raised.exception.code, "RuntimeProfileMismatch")
        self.assertEqual(world, before)


if __name__ == "__main__":
    unittest.main()
