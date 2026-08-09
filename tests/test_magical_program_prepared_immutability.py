from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from src.evaluator.magical_program import (
    MagicalProgramEvaluator,
    ProgramContractRegistration,
    ProgramContractRegistry,
)
from src.runtime.magical_program import (
    MagicalProgramRuntime,
    ProgramRuntimeContractRegistry,
    RuntimeContractRegistration,
    complete_runtime_state,
    program_sandbox_world,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "magical-program"
STRUCTURED = json.loads(
    (EXAMPLES / "MP-STRUCTURED-001.json").read_text(encoding="utf-8")
)
TRANSITION = json.loads((EXAMPLES / "MP-001.json").read_text(encoding="utf-8"))


def structured_runtime(observed: list[dict] | None = None) -> MagicalProgramRuntime:
    semantic = ProgramContractRegistry(
        (
            ProgramContractRegistration(
                "test.structured-consumer",
                "1",
                "effect.invoke",
                (
                    "record:EvidenceFusionModel",
                    "sequence:record:HypothesisScore",
                ),
                "effect_result",
                (),
                0,
                0,
                0,
                ("OBSERVE",),
                ("SAMPLE",),
            ),
        )
    )

    def consume(context, effect, world):
        model, ranking = effect.frozen_values
        if observed is not None:
            observed.append(
                {
                    "model_id": model["fields"]["model_id"]["value"],
                    "first_hypothesis": ranking["items"][0]["fields"][
                        "hypothesis_id"
                    ]["value"],
                }
            )
        return {
            "kind": "effect_result",
            "status": "Committed",
            "node_id": effect.node_id,
            "model_id": model["fields"]["model_id"]["value"],
            "first_hypothesis": ranking["items"][0]["fields"][
                "hypothesis_id"
            ]["value"],
        }

    runtime_contracts = ProgramRuntimeContractRegistry(
        (
            RuntimeContractRegistration(
                "test.structured-consumer",
                "1",
                "effect.invoke",
                (
                    "record:EvidenceFusionModel",
                    "sequence:record:HypothesisScore",
                ),
                "effect_result",
                0,
                consume,
            ),
        )
    )
    return MagicalProgramRuntime(
        evaluator=MagicalProgramEvaluator(contracts=semantic),
        contracts=runtime_contracts,
    )


class MagicalProgramPreparedImmutabilityTests(unittest.TestCase):
    def test_every_prepared_structured_surface_is_recursively_immutable(self) -> None:
        runtime = structured_runtime()
        world = program_sandbox_world()
        prepared = runtime.prepare(
            STRUCTURED,
            runtime.evaluate(STRUCTURED, world=world),
            world,
        )

        attempts = (
            lambda: prepared.runtime_bindings.__setitem__("new", {}),
            lambda: prepared.runtime_bindings["model"]["fields"].__setitem__(
                "model_id", {"kind": "literal", "value": "forged"}
            ),
            lambda: prepared.effects[0].frozen_values[0]["fields"].__setitem__(
                "revision", {"kind": "literal", "value": "forged"}
            ),
            lambda: prepared.effects[0].frozen_values[1]["items"][0][
                "fields"
            ].__setitem__(
                "hypothesis_id", {"kind": "literal", "value": "forged"}
            ),
            lambda: prepared.output_declarations[0].__setitem__(
                "binding", "forged"
            ),
            lambda: prepared.effects[0].frozen_values[1]["items"].append(
                {"kind": "record", "type_id": "HypothesisScore", "fields": {}}
            ),
        )
        for attempt in attempts:
            with self.subTest(attempt=attempt), self.assertRaises(TypeError):
                attempt()

        self.assertIsInstance(
            prepared.effects[0].frozen_values[1]["items"], list
        )

    def test_bound_host_records_are_recursively_immutable(self) -> None:
        runtime = MagicalProgramRuntime()
        world = program_sandbox_world()
        prepared = runtime.prepare(
            TRANSITION,
            runtime.evaluate(TRANSITION, world=world),
            world,
        )
        effect = prepared.effects[0]
        records = (
            *effect.capability_records,
            *effect.lease_records,
            *effect.identity_records,
            *effect.accounting_records,
        )
        self.assertTrue(records)
        for bound in records:
            with self.subTest(record_id=bound.record_id), self.assertRaises(TypeError):
                bound.frozen_record["active"] = False
            nested = bound.frozen_record.get("effects")
            if nested is not None:
                self.assertIsInstance(nested, list)
                with self.assertRaises(TypeError):
                    nested.append("Forged")

    def test_post_prepare_source_mutation_cannot_change_commit_inputs(self) -> None:
        observed: list[dict] = []
        runtime = structured_runtime(observed)
        program = copy.deepcopy(STRUCTURED)
        world = program_sandbox_world()
        prepared = runtime.prepare(
            program,
            runtime.evaluate(program, world=world),
            world,
        )
        program["values"][0]["fields"]["model_id"]["value"] = "forged"
        program["values"][1]["items"][0]["fields"]["hypothesis_id"][
            "value"
        ] = "hypothesis:forged"

        trace = runtime.commit(prepared, world)
        self.assertEqual("Committed", trace["status"])
        self.assertEqual(
            [
                {
                    "model_id": "evidence.snapshot-fusion",
                    "first_hypothesis": "hypothesis:A",
                }
            ],
            observed,
        )
        self.assertEqual(
            "evidence.snapshot-fusion", trace["effects"][0]["model_id"]
        )
        self.assertEqual(
            "hypothesis:A", trace["effects"][0]["first_hypothesis"]
        )

    def test_executor_cannot_mutate_prepared_input_and_atomic_abort_restores_world(self) -> None:
        semantic = ProgramContractRegistry(
            (
                ProgramContractRegistration(
                    "test.structured-consumer",
                    "1",
                    "effect.invoke",
                    (
                        "record:EvidenceFusionModel",
                        "sequence:record:HypothesisScore",
                    ),
                    "effect_result",
                    (),
                    0,
                    0,
                    0,
                    ("OBSERVE",),
                    ("SAMPLE",),
                ),
            )
        )

        def malicious(context, effect, world):
            world.entities["entity:generic:target"]["status"] = "partial"
            effect.frozen_values[0]["fields"]["model_id"]["value"] = "forged"
            return {
                "kind": "effect_result",
                "status": "Committed",
                "node_id": effect.node_id,
            }

        runtime = MagicalProgramRuntime(
            evaluator=MagicalProgramEvaluator(contracts=semantic),
            contracts=ProgramRuntimeContractRegistry(
                (
                    RuntimeContractRegistration(
                        "test.structured-consumer",
                        "1",
                        "effect.invoke",
                        (
                            "record:EvidenceFusionModel",
                            "sequence:record:HypothesisScore",
                        ),
                        "effect_result",
                        0,
                        malicious,
                    ),
                )
            ),
        )
        world = program_sandbox_world()
        before = complete_runtime_state(world)
        trace = runtime.execute(STRUCTURED, world)
        self.assertEqual("Aborted", trace["status"])
        self.assertEqual("ProgramCommitInternalFailure", trace["abort"]["code"])
        self.assertEqual(before, complete_runtime_state(world))


if __name__ == "__main__":
    unittest.main()
