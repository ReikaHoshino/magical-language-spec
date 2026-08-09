from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from src.artifacts.magical_program import (
    MagicalProgramAdmissionError,
    admit_program,
)
from src.evaluator.magical_program import (
    ProgramContractRegistration,
    ProgramContractRegistry,
)
from src.evaluator.schema import validator

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "examples" / "magical-program" / "MP-STRUCTURED-001.json"


class MagicalProgramStructuredQuantitySequenceTests(unittest.TestCase):
    def test_anonymous_quantity_sequence_requires_exact_type_dimension_and_unit(self) -> None:
        program = json.loads(BASE.read_text(encoding="utf-8"))
        program["program_id"] = "program:structured-quantity-sequence:001"
        program["values"][1] = {
            "value_id": "ranking",
            "kind": "sequence",
            "element_type": "quantity:Mass:M1:kg",
            "items": [
                {
                    "kind": "quantity",
                    "semantic_type": "Mass",
                    "dimension": "M1",
                    "unit": "kg",
                    "value": 1.0,
                },
                {
                    "kind": "quantity",
                    "semantic_type": "Mass",
                    "dimension": "M1",
                    "unit": "kg",
                    "value": 2.0,
                },
            ],
        }
        program["nodes"][0]["inputs"] = ["model", "ranking"]
        registry = ProgramContractRegistry(
            (
                ProgramContractRegistration(
                    "test.structured-consumer",
                    "1",
                    "effect.invoke",
                    (
                        "record:EvidenceFusionModel",
                        "sequence:quantity:Mass:M1:kg",
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
        schema = validator("magical-program.schema.json").schema
        admitted = admit_program(
            program,
            schema=schema,
            registered_contracts=registry.admitted_pairs(),
        )
        self.assertEqual("Accepted", admitted["status"])

        for field, value in (
            ("semantic_type", "Length"),
            ("dimension", "L1"),
            ("unit", "g"),
        ):
            with self.subTest(field=field):
                mismatched = copy.deepcopy(program)
                mismatched["values"][1]["items"][1][field] = value
                with self.assertRaises(MagicalProgramAdmissionError) as caught:
                    admit_program(
                        mismatched,
                        schema=schema,
                        registered_contracts=registry.admitted_pairs(),
                    )
                self.assertEqual(
                    "ProgramSequenceElementTypeMismatch", caught.exception.code
                )


if __name__ == "__main__":
    unittest.main()
