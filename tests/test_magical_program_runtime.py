from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from src.evaluator.magical_program import (
    MagicalProgramEvaluator,
    ProgramContractRegistration as SemanticRegistration,
    ProgramContractRegistry as SemanticRegistry,
)
from src.runtime.magical_program import (
    MagicalProgramRuntime,
    ProgramRuntimeContractRegistry,
    ProgramRuntimeError,
    ProgramRuntimeProfile,
    RuntimeContractRegistration,
    complete_runtime_state,
    program_sandbox_world,
    validate_program_execution_trace,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "magical-program"
TRANSITION = json.loads((EXAMPLES / "MP-001.json").read_text(encoding="utf-8"))
OBSERVE = json.loads((EXAMPLES / "MP-OBSERVE-001.json").read_text(encoding="utf-8"))
PURE = json.loads((EXAMPLES / "MP-PURE-001.json").read_text(encoding="utf-8"))
MANIFEST = ROOT / "conformance" / "manifest.json"


class MagicalProgramRuntimeTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.runtime = MagicalProgramRuntime()

    def test_prepare_binds_portable_requirements_without_mutation(self) -> None:
        world = program_sandbox_world()
        before = complete_runtime_state(world)
        source = json.dumps(TRANSITION, sort_keys=True)
        report = self.runtime.evaluate(TRANSITION, world=world)
        prepared = self.runtime.prepare(TRANSITION, report, world)

        self.assertEqual(before, complete_runtime_state(world))
        self.assertEqual(("entity:generic:target",), prepared.frozen_entity_ids)
        effect = prepared.effects[0]
        self.assertEqual("reference", effect.frozen_values[0]["kind"])
        self.assertEqual(
            ["capability:host:transition"],
            [item.record_id for item in effect.capability_records],
        )
        self.assertEqual(
            ["lease:host:write"],
            [item.record_id for item in effect.lease_records],
        )
        self.assertEqual(
            ["identity:host:target"],
            [item.record_id for item in effect.identity_records],
        )
        self.assertEqual(
            ["ledger:host:energy-matter"],
            [item.record_id for item in effect.accounting_records],
        )
        for record_id in (
            "capability:host:transition",
            "lease:host:write",
            "identity:host:target",
            "ledger:host:energy-matter",
        ):
            self.assertNotIn(record_id, source)

    def test_transition_uses_host_revision_and_binds_committed_outputs(self) -> None:
        initial = program_sandbox_world()
        world = initial.clone()
        trace = self.runtime.execute(TRANSITION, world)
        validate_program_execution_trace(trace)
        self.assertEqual("Committed", trace["status"])
        self.assertEqual("world:generic:2", world.revision)
        self.assertNotIn("world:generic:2", json.dumps(TRANSITION))
        self.assertEqual(
            "transitioned", world.entities["entity:generic:target"]["status"]
        )
        results = {item["kind"]: item for item in trace["results"]}
        self.assertIn(results["event"]["event_id"], trace["history_event_ids"])
        self.assertEqual(
            90.0,
            world.ledgers["ledger:host:energy-matter"]["available_energy_j"],
        )
        self.assertEqual("Match", self.runtime.replay(TRANSITION, initial, trace)["status"])

    def test_observation_is_nonphysical_and_event_accounted(self) -> None:
        initial = program_sandbox_world()
        world = initial.clone()
        trace = self.runtime.execute(OBSERVE, world)
        validate_program_execution_trace(trace)
        self.assertEqual("Committed", trace["status"])
        self.assertEqual(initial.revision, world.revision)
        self.assertEqual(initial.entities, world.entities)
        artifact = next(
            iter(world.runtime_state["evidence_store"]["artifacts"].values())
        )
        self.assertFalse(artifact["truth_claim"])
        self.assertFalse(artifact["physical_effect"])
        self.assertEqual(
            7,
            world.ledgers["ledger:host:event-journal"]["events_remaining"],
        )
        results = {item["kind"]: item for item in trace["results"]}
        self.assertEqual(artifact["artifact_id"], results["artifact"]["artifact_id"])
        self.assertIn(results["event"]["event_id"], trace["history_event_ids"])
        self.assertEqual("Match", self.runtime.replay(OBSERVE, initial, trace)["status"])

    def test_pure_program_has_no_authoritative_effect(self) -> None:
        world = program_sandbox_world()
        before = complete_runtime_state(world)
        trace = self.runtime.execute(PURE, world)
        validate_program_execution_trace(trace)
        self.assertEqual("Committed", trace["status"])
        self.assertEqual([], trace["effects"])
        self.assertEqual([], trace["history_event_ids"])
        self.assertEqual(before, complete_runtime_state(world))
        values = {item["name"]: item["value"] for item in trace["results"]}
        self.assertEqual(5.0, values["total"]["value"])
        self.assertIs(True, values["allowed"]["value"])

    def test_resolution_is_exact_and_does_not_silently_retarget(self) -> None:
        zero = program_sandbox_world()
        zero.entities.clear()
        self.assertEqual(
            "ProgramResolutionFailure",
            self.runtime.execute(TRANSITION, zero)["abort"]["code"],
        )

        ambiguous = program_sandbox_world()
        ambiguous.entities["entity:generic:second"] = {
            "entity_id": "entity:generic:second",
            "state_revision": "state:entity:generic:second@world:generic:1",
            "entity_type": "test-target",
            "scope": "local",
            "status": "second",
        }
        self.assertEqual(
            "ProgramResolutionAmbiguous",
            self.runtime.execute(TRANSITION, ambiguous)["abort"]["code"],
        )

        world = program_sandbox_world()
        prepared = self.runtime.prepare(
            TRANSITION, self.runtime.evaluate(TRANSITION, world=world), world
        )
        world.entities["entity:generic:late"] = {
            "entity_id": "entity:generic:late",
            "state_revision": "state:entity:generic:late@world:generic:1",
            "entity_type": "test-target",
            "scope": "local",
            "status": "late",
        }
        trace = self.runtime.commit(prepared, world)
        self.assertEqual(
            ["entity:generic:target"], trace["effects"][0]["entity_ids"]
        )
        self.assertEqual("late", world.entities["entity:generic:late"]["status"])

    def test_every_frozen_record_is_revalidated_without_erasing_external_drift(self) -> None:
        cases = (
            ("ProgramStaleWorldRevision", lambda world: setattr(world, "revision", "world:drift"), TRANSITION),
            ("ProgramStaleIdentity", lambda world: world.entities["entity:generic:target"].__setitem__("state_revision", "state:drift"), TRANSITION),
            ("ProgramCapabilityDrift", lambda world: world.capabilities["capability:host:transition"].__setitem__("revision", "2"), TRANSITION),
            ("ProgramLeaseDrift", lambda world: world.leases["lease:host:write"].__setitem__("active", False), TRANSITION),
            ("ProgramIdentityStale", lambda world: world.runtime_state["identity_evidence"]["identity:host:target"].__setitem__("revision", "2"), TRANSITION),
            ("ProgramEvidenceStale", lambda world: world.runtime_state["evidence"]["evidence:host:freshness"].__setitem__("revision", "2"), OBSERVE),
            ("ProgramAccountingDrift", lambda world: world.ledgers["ledger:host:energy-matter"].__setitem__("available_energy_j", 0), TRANSITION),
            ("ProgramHistoryDrift", lambda world: world.history.append({"event_id": "event:late"}), TRANSITION),
        )
        for expected, mutate, program in cases:
            with self.subTest(expected=expected):
                world = program_sandbox_world()
                prepared = self.runtime.prepare(
                    program, self.runtime.evaluate(program, world=world), world
                )
                mutate(world)
                state_at_commit_entry = complete_runtime_state(world)
                with self.assertRaises(ProgramRuntimeError) as caught:
                    self.runtime.commit(prepared, world)
                self.assertEqual(expected, caught.exception.code)
                self.assertEqual(state_at_commit_entry, complete_runtime_state(world))

    def test_aggregate_and_host_ceiling_checks_are_independent(self) -> None:
        overdraw = copy.deepcopy(TRANSITION)
        overdraw["budget"]["energy_j"] = 120
        overdraw["budget"]["events"] = 2
        overdraw["nodes"][1]["obligations"]["resources"]["energy_j"] = 60
        second = copy.deepcopy(overdraw["nodes"][1])
        second["node_id"] = "invoke_second"
        second["order"] = 2
        second["produces"] = ["second_result"]
        for category in ("capabilities", "leases", "identities", "accounting"):
            for item in second["obligations"][category]:
                item["requirement_id"] += ".second"
        overdraw["nodes"].append(second)
        overdraw["edges"].append({"from": "resolve_target", "to": "invoke_second"})
        overdraw["outputs"].append(
            {"name": "second", "binding": "second_result", "kind": "effect_result"}
        )
        trace = self.runtime.execute(overdraw, program_sandbox_world())
        self.assertEqual("ProgramEnergyInsufficient", trace["abort"]["code"])
        self.assertTrue(trace["configuration_unchanged"])

        energy = copy.deepcopy(TRANSITION)
        energy["budget"]["energy_j"] = 600
        energy["nodes"][1]["obligations"]["resources"]["energy_j"] = 600
        energy_world = program_sandbox_world()
        energy_world.ledgers["ledger:host:energy-matter"]["available_energy_j"] = 1000
        self.assertEqual(
            "ProgramRuntimeEnergyLimitExceeded",
            self.runtime.execute(energy, energy_world)["abort"]["code"],
        )

        matter = copy.deepcopy(TRANSITION)
        matter["nodes"][1]["obligations"]["resources"]["matter_kg"] = 1001
        matter_world = program_sandbox_world()
        matter_world.ledgers["ledger:host:energy-matter"]["available_matter_kg"] = 2000
        self.assertEqual(
            "ProgramRuntimeAggregateMatterExceeded",
            self.runtime.execute(matter, matter_world)["abort"]["code"],
        )

        strict = MagicalProgramRuntime(profile=ProgramRuntimeProfile(max_events=0))
        self.assertEqual(
            "ProgramRuntimeEventLimitExceeded",
            strict.execute(TRANSITION, program_sandbox_world())["abort"]["code"],
        )

    def test_registry_owns_custom_execution_and_core_has_no_contract_dispatch(self) -> None:
        program = copy.deepcopy(TRANSITION)
        program["program_id"] = "program:custom:001"
        program["budget"]["energy_j"] = 0
        program["budget"]["events"] = 0
        node = program["nodes"][1]
        node["contract"] = {"contract_id": "custom.echo", "revision": "1"}
        node["obligations"] = {
            "capabilities": [], "leases": [], "identities": [],
            "evidence": [], "accounting": [],
            "resources": {"energy_j": 0, "matter_kg": 0, "events": 0},
        }
        program["outputs"] = [
            {"name": "result", "binding": "transition_result", "kind": "effect_result"}
        ]

        def echo(context, effect, world):
            return {
                "kind": "effect_result",
                "status": "Committed",
                "message": effect.frozen_values[1]["value"],
            }

        semantic = SemanticRegistry((
            SemanticRegistration(
                "custom.echo", "1", "effect.invoke",
                ("reference", "literal:string"), "effect_result", (),
                0, 0, 0, ("RECONFIGURE",), ("TRANSITION",),
            ),
        ))
        contracts = ProgramRuntimeContractRegistry((
            RuntimeContractRegistration(
                "custom.echo", "1", "effect.invoke",
                ("reference", "literal:string"), "effect_result", 0, echo,
            ),
        ))
        runtime = MagicalProgramRuntime(
            evaluator=MagicalProgramEvaluator(contracts=semantic),
            contracts=contracts,
        )
        trace = runtime.execute(program, program_sandbox_world())
        self.assertEqual("Committed", trace["status"])
        self.assertEqual("transitioned", trace["effects"][0]["message"])

        core = (ROOT / "src" / "runtime" / "magical_program_engine.py").read_text(encoding="utf-8")
        self.assertNotIn("generic.transition", core)
        self.assertNotIn("generic.observe", core)
        self.assertNotIn("if registration.contract_id", core)

    def test_executor_failure_and_output_forgery_roll_back_every_domain(self) -> None:
        forged = copy.deepcopy(TRANSITION)
        forged["outputs"][0]["kind"] = "artifact"
        world = program_sandbox_world()
        before = complete_runtime_state(world)
        trace = self.runtime.execute(forged, world)
        self.assertEqual("ProgramCommittedOutputMismatch", trace["abort"]["code"])
        self.assertEqual(before, complete_runtime_state(world))

        program = copy.deepcopy(TRANSITION)
        program["program_id"] = "program:failing:001"
        program["budget"]["energy_j"] = 0
        program["budget"]["events"] = 0
        node = program["nodes"][1]
        node["contract"] = {"contract_id": "custom.fail", "revision": "1"}
        node["obligations"] = {
            "capabilities": [], "leases": [], "identities": [],
            "evidence": [], "accounting": [],
            "resources": {"energy_j": 0, "matter_kg": 0, "events": 0},
        }
        program["outputs"] = [
            {"name": "result", "binding": "transition_result", "kind": "effect_result"}
        ]

        def fail(context, effect, mutable_world):
            mutable_world.entities["entity:generic:target"]["status"] = "partial"
            mutable_world.history.append({"event_id": "event:partial"})
            raise RuntimeError("synthetic")

        semantic = SemanticRegistry((
            SemanticRegistration(
                "custom.fail", "1", "effect.invoke",
                ("reference", "literal:string"), "effect_result", (),
                0, 0, 0, ("RECONFIGURE",), ("TRANSITION",),
            ),
        ))
        contracts = ProgramRuntimeContractRegistry((
            RuntimeContractRegistration(
                "custom.fail", "1", "effect.invoke",
                ("reference", "literal:string"), "effect_result", 0, fail,
            ),
        ))
        runtime = MagicalProgramRuntime(
            evaluator=MagicalProgramEvaluator(contracts=semantic),
            contracts=contracts,
        )
        world = program_sandbox_world()
        before = complete_runtime_state(world)
        trace = runtime.execute(program, world)
        self.assertEqual("ProgramCommitInternalFailure", trace["abort"]["code"])
        self.assertEqual(before, complete_runtime_state(world))

    def test_prepared_plan_single_use_abort_replay_and_occurrence_identity(self) -> None:
        world = program_sandbox_world()
        prepared = self.runtime.prepare(
            OBSERVE, self.runtime.evaluate(OBSERVE, world=world), world
        )
        self.runtime.commit(prepared, world)
        with self.assertRaises(ProgramRuntimeError) as caught:
            self.runtime.commit(prepared, world)
        self.assertEqual("ProgramPreparedPlanConsumed", caught.exception.code)

        initial = program_sandbox_world()
        initial.capabilities["capability:host:transition"]["active"] = False
        abort = self.runtime.execute(TRANSITION, initial.clone())
        self.assertEqual("DeterministicAbort", self.runtime.replay(TRANSITION, initial, abort)["status"])

        repeat_world = program_sandbox_world()
        first = self.runtime.execute(OBSERVE, repeat_world)
        second = self.runtime.execute(OBSERVE, repeat_world)
        self.assertNotEqual(first["effects"][0]["event_id"], second["effects"][0]["event_id"])
        self.assertNotEqual(first["effects"][0]["artifact_id"], second["effects"][0]["artifact_id"])

    def test_no_fixture_or_opaque_payload_dispatch_and_stable_surface_is_unchanged(self) -> None:
        paths = (
            "magical_program_engine.py", "magical_program_prepare.py",
            "magical_program_commit.py", "magical_program_binding.py",
            "magical_program_contracts.py", "magical_program_model.py",
        )
        source = "\n".join(
            (ROOT / "src" / "runtime" / name).read_text(encoding="utf-8")
            for name in paths
        )
        for forbidden in (
            "SUCCESS-ARCANA", "DEBUG-HELL", "embedded_payload",
            "shadow.spell-instance", "base64", "filename", "display_name",
        ):
            self.assertNotIn(forbidden, source)

        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual("0.12.0", manifest["suite"]["suite_version"])
        self.assertEqual(65, sum(len(item["required_case_ids"]) for item in manifest["classes"]))


if __name__ == "__main__":
    unittest.main()
