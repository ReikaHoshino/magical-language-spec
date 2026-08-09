from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from src.evaluator.magical_program import (
    MagicalProgramEvaluator,
    ProgramContractRegistration as SemanticContractRegistration,
    ProgramContractRegistry as SemanticContractRegistry,
)
from src.runtime.magical_program import (
    MagicalProgramRuntime,
    ProgramRuntimeContractRegistry,
    ProgramRuntimeError,
    RuntimeContractRegistration,
    complete_runtime_state,
    program_sandbox_world,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "magical-program"
PURE = json.loads((EXAMPLES / "MP-PURE-001.json").read_text(encoding="utf-8"))
TRANSITION = json.loads((EXAMPLES / "MP-001.json").read_text(encoding="utf-8"))


class MagicalProgramRuntimeExtensionTests(unittest.TestCase):
    def test_prior_pure_binding_can_feed_a_registered_effect(self) -> None:
        program = copy.deepcopy(PURE)
        program["program_id"] = "program:pure-output-to-effect:001"
        program["budget"] = {
            "energy_j": 0,
            "events": 0,
            "microsteps": 8,
            "concurrency": 1,
        }
        program["nodes"] = [
            copy.deepcopy(program["nodes"][0]),
            {
                "node_id": "invoke_numeric_effect",
                "order": 1,
                "instruction": "effect.invoke",
                "inputs": ["total"],
                "produces": ["effect_result"],
                "contract": {
                    "contract_id": "test.numeric-effect",
                    "revision": "1",
                },
                "obligations": {
                    "capabilities": [],
                    "leases": [],
                    "identities": [],
                    "evidence": [],
                    "accounting": [],
                    "resources": {
                        "energy_j": 0,
                        "matter_kg": 0,
                        "events": 0,
                    },
                },
            },
        ]
        program["edges"] = [
            {"from": "sum", "to": "invoke_numeric_effect"}
        ]
        program["outputs"] = [
            {
                "name": "effect",
                "binding": "effect_result",
                "kind": "effect_result",
            }
        ]

        semantic = SemanticContractRegistry(
            (
                SemanticContractRegistration(
                    "test.numeric-effect",
                    "1",
                    "effect.invoke",
                    ("quantity",),
                    "effect_result",
                    (),
                    0,
                    0,
                    0,
                    ("CONSTRAIN",),
                    ("ACTIVATE",),
                ),
            )
        )

        def execute_numeric(context, effect, world):
            return {
                "kind": "effect_result",
                "status": "Committed",
                "numeric_value": effect.frozen_values[0]["value"],
                "node_id": effect.node_id,
            }

        runtime_contracts = ProgramRuntimeContractRegistry(
            (
                RuntimeContractRegistration(
                    "test.numeric-effect",
                    "1",
                    "effect.invoke",
                    ("quantity",),
                    "effect_result",
                    0,
                    execute_numeric,
                ),
            )
        )
        runtime = MagicalProgramRuntime(
            evaluator=MagicalProgramEvaluator(contracts=semantic),
            contracts=runtime_contracts,
        )
        trace = runtime.execute(program, program_sandbox_world())
        self.assertEqual("Committed", trace["status"])
        self.assertEqual(5.0, trace["effects"][0]["numeric_value"])

    def test_trace_validation_failure_rolls_back_every_domain(self) -> None:
        runtime = MagicalProgramRuntime()
        world = program_sandbox_world()
        before = complete_runtime_state(world)
        report = runtime.evaluate(TRANSITION, world=world)
        prepared = runtime.prepare(TRANSITION, report, world)
        with patch(
            "src.runtime.magical_program_commit.validate_program_execution_trace",
            side_effect=ValueError("synthetic trace failure"),
        ):
            with self.assertRaises(ProgramRuntimeError) as caught:
                runtime.commit(prepared, world)
        self.assertEqual("ProgramCommitInternalFailure", caught.exception.code)
        self.assertEqual(before, complete_runtime_state(world))

    def test_compatibility_imports_reexport_the_same_runtime_class(self) -> None:
        from src.runtime.magical_program_entrypoint import (
            MagicalProgramRuntime as EntrypointRuntime,
        )
        from src.runtime.magical_program_release import (
            MagicalProgramRuntime as ReleaseRuntime,
        )
        from src.runtime.magical_program_release_entrypoint import (
            MagicalProgramRuntime as ReleaseEntrypointRuntime,
        )
        from src.runtime.magical_program_runtime import (
            MagicalProgramRuntime as RuntimeAlias,
        )

        self.assertIs(MagicalProgramRuntime, EntrypointRuntime)
        self.assertIs(MagicalProgramRuntime, ReleaseRuntime)
        self.assertIs(MagicalProgramRuntime, ReleaseEntrypointRuntime)
        self.assertIs(MagicalProgramRuntime, RuntimeAlias)


if __name__ == "__main__":
    unittest.main()
