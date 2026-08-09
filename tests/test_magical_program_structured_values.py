from __future__ import annotations

import copy
import json
import math
import unittest
from pathlib import Path

from src.artifacts.magical_program import (
    MagicalProgramAdmissionError,
    MagicalProgramHostLimits,
    admit_program,
    decode_program,
)
from src.evaluator.magical_program import (
    MagicalProgramEvaluator,
    ProgramContractRegistration,
    ProgramContractRegistry,
)
from src.evaluator.schema import validator
from src.runtime.magical_program import (
    MagicalProgramRuntime,
    ProgramRuntimeContractRegistry,
    RuntimeContractRegistration,
    program_sandbox_world,
)
from src.runtime.magical_program_model import program_digest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "magical-program" / "MP-STRUCTURED-001.json"


def load_program():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def semantic_registry() -> ProgramContractRegistry:
    return ProgramContractRegistry(
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


def runtime_registry(observed: list[dict]) -> ProgramRuntimeContractRegistry:
    def consume(context, effect, world):
        model, ranking = effect.frozen_values
        observed.append(
            {
                "model": copy.deepcopy(model),
                "ranking": copy.deepcopy(ranking),
            }
        )
        winner = max(
            ranking["items"],
            key=lambda item: (
                item["fields"]["score"]["value"],
                item["fields"]["hypothesis_id"]["value"],
            ),
        )
        return {
            "kind": "effect_result",
            "status": "Committed",
            "node_id": effect.node_id,
            "model_id": model["fields"]["model_id"]["value"],
            "winner_hypothesis_id": winner["fields"]["hypothesis_id"]["value"],
        }

    return ProgramRuntimeContractRegistry(
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


class MagicalProgramStructuredValueTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.program = load_program()
        self.schema = validator("magical-program.schema.json").schema
        self.semantic = semantic_registry()

    def admit(self, program=None, *, limits=MagicalProgramHostLimits()):
        return admit_program(
            self.program if program is None else program,
            schema=self.schema,
            registered_contracts=self.semantic.admitted_pairs(),
            limits=limits,
        )

    def assert_code(self, program, code, *, limits=MagicalProgramHostLimits()):
        with self.assertRaises(MagicalProgramAdmissionError) as caught:
            self.admit(program, limits=limits)
        self.assertEqual(code, caught.exception.code, caught.exception.diagnostic())

    def test_exact_structured_signatures_flow_through_evaluator_runtime_and_replay(self) -> None:
        admission = self.admit()
        self.assertEqual("Accepted", admission["status"])
        evaluator = MagicalProgramEvaluator(contracts=self.semantic)
        report = evaluator.evaluate_program(self.program)
        self.assertEqual("ConditionallyFeasible", report["status"])
        node = report["interpretations"]["typed_mir"]["nodes"][0]
        self.assertEqual(
            [
                "record:EvidenceFusionModel",
                "sequence:record:HypothesisScore",
            ],
            node["input_types"],
        )

        observed: list[dict] = []
        runtime = MagicalProgramRuntime(
            evaluator=evaluator,
            contracts=runtime_registry(observed),
        )
        initial = program_sandbox_world()
        world = initial.clone()
        original = copy.deepcopy(self.program)
        trace = runtime.execute(self.program, world)
        self.assertEqual("Committed", trace["status"])
        self.assertEqual("hypothesis:A", trace["effects"][0]["winner_hypothesis_id"])
        self.assertEqual(original, self.program)
        self.assertEqual(original["values"][0], observed[0]["model"])
        self.assertEqual(original["values"][1], observed[0]["ranking"])
        self.assertEqual("Match", runtime.replay(self.program, initial, trace)["status"])

    def test_record_key_order_is_canonical_but_sequence_order_is_semantic(self) -> None:
        reordered = copy.deepcopy(self.program)
        fields = reordered["values"][0]["fields"]
        reordered["values"][0]["fields"] = dict(reversed(list(fields.items())))
        self.assertEqual(program_digest(self.program), program_digest(reordered))

        reversed_sequence = copy.deepcopy(self.program)
        reversed_sequence["values"][1]["items"].reverse()
        self.assertNotEqual(
            program_digest(self.program), program_digest(reversed_sequence)
        )

    def test_sequence_is_homogeneous_and_registry_has_no_object_wildcard(self) -> None:
        heterogeneous = copy.deepcopy(self.program)
        heterogeneous["values"][1]["items"][1] = {
            "kind": "literal",
            "value": "not-a-hypothesis-record",
        }
        self.assert_code(heterogeneous, "ProgramSequenceElementTypeMismatch")

        for wildcard in ("object", "array", "any", "*"):
            with self.subTest(wildcard=wildcard), self.assertRaises(ValueError):
                ProgramContractRegistration(
                    "bad.structured",
                    "1",
                    "effect.invoke",
                    (wildcard,),
                    "effect_result",
                    (),
                    0,
                    0,
                    0,
                    (),
                    (),
                )

    def test_depth_field_sequence_and_total_item_limits_fail_before_prepare(self) -> None:
        self.assert_code(
            self.program,
            "ProgramRecordFieldLimitExceeded",
            limits=MagicalProgramHostLimits(max_record_fields=2),
        )
        self.assert_code(
            self.program,
            "ProgramSequenceItemLimitExceeded",
            limits=MagicalProgramHostLimits(max_sequence_items=1),
        )
        self.assert_code(
            self.program,
            "ProgramStructuredItemLimitExceeded",
            limits=MagicalProgramHostLimits(max_structured_items=4),
        )

        nested = copy.deepcopy(self.program)
        nested["values"][0]["fields"]["nested"] = {
            "kind": "record",
            "type_id": "NestedOne",
            "fields": {
                "nested": {
                    "kind": "record",
                    "type_id": "NestedTwo",
                    "fields": {},
                }
            },
        }
        self.assert_code(
            nested,
            "ProgramStructuredDepthLimitExceeded",
            limits=MagicalProgramHostLimits(max_structured_depth=2),
        )

    def test_nonfinite_numbers_and_duplicate_nested_fields_are_rejected(self) -> None:
        direct = copy.deepcopy(self.program)
        direct["values"][1]["items"][0]["fields"]["score"]["value"] = math.nan
        self.assert_code(direct, "ProgramNonFiniteNumber")

        with self.assertRaises(MagicalProgramAdmissionError) as nan:
            decode_program(b'{"value":NaN}')
        self.assertEqual("ProgramNonFiniteNumber", nan.exception.code)

        text = EXAMPLE.read_text(encoding="utf-8")
        duplicate = text.replace(
            '"model_id": {',
            '"model_id": {"kind":"literal","value":"duplicate"},'
            '"model_id": {',
            1,
        )
        with self.assertRaises(MagicalProgramAdmissionError) as duplicated:
            decode_program(duplicate.encode("utf-8"))
        self.assertEqual("ProgramDuplicateJsonProperty", duplicated.exception.code)


if __name__ == "__main__":
    unittest.main()
