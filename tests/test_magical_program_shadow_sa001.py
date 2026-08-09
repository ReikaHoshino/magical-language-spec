from __future__ import annotations

import copy
import inspect
import json
import tempfile
import unittest
from pathlib import Path

from src.extensions.success_arcana.executors import boundary_reflection
from src.migration.magical_program_shadow import (
    BOUNDARY_REFLECTION_PAIR,
    bundle_contract_pair,
    default_shadow_translators,
    run_shadow_file,
    translate_boundary_reflection,
)
from src.migration.magical_program_shadow_boundary import (
    boundary_reflection_executor,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT / "examples" / "spell-instances" / "success-arcana" / "SA-001.json"
)


def load():
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def write_temp(document, directory: str, filename: str) -> Path:
    path = Path(directory) / filename
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def false_comparisons(result):
    return {
        key: value
        for key, value in result.get("comparisons", {}).items()
        if value is not True
    }


class MagicalProgramShadowSA001Tests(unittest.TestCase):
    maxDiff = None

    def assert_shadow_pass(self, result):
        self.assertEqual(
            "PASS",
            result["status"],
            {
                "false_comparisons": false_comparisons(result),
                "raw_status": result.get("raw_evaluation_status"),
                "diagnostic": result.get("normalized_diagnostic_code"),
                "legacy_golden": result.get("legacy_golden"),
                "generic_golden": result.get("generic_golden"),
                "execution": result.get("generic_execution"),
                "replay": result.get("generic_replay"),
            },
        )

    def test_positive_case_has_atomic_momentum_energy_controller_and_replay_parity(self) -> None:
        result = run_shadow_file(SOURCE)
        self.assert_shadow_pass(result)
        self.assertEqual("GOLDEN-SA-001", result["golden_expectation_id"])
        self.assertEqual(
            {"legacy": "Feasible", "generic": "ConditionallyFeasible"},
            result["raw_evaluation_status"],
        )
        self.assertIsNone(result["normalized_diagnostic_code"])
        self.assertEqual("Committed", result["generic_execution"]["status"])
        self.assertEqual("Match", result["generic_replay"]["status"])

        program = result["program"]
        values = {item["value_id"]: item for item in program["values"]}
        self.assertEqual("selector", values["target_selector"]["kind"])
        self.assertEqual("selector", values["anchor_selector"]["kind"])
        self.assertEqual(
            "BoundaryReflectionModel", values["controller_model"]["type_id"]
        )
        self.assertEqual(
            "BoundaryReflectionPolicy", values["boundary_policy"]["type_id"]
        )
        program_text = json.dumps(program, ensure_ascii=False, sort_keys=True)
        bundle = load()
        self.assertNotIn(SOURCE.read_text(encoding="utf-8"), program_text)
        self.assertNotIn(bundle["initial_world"]["revision"], program_text)
        self.assertNotIn(
            bundle["execution"]["parameters"]["result_world_revision"],
            program_text,
        )
        for record_id in (
            *bundle["execution"]["required_evidence"]["capabilities"],
            *bundle["execution"]["required_evidence"]["leases"],
            *bundle["execution"]["required_evidence"]["accounting"],
        ):
            self.assertNotIn(record_id, program_text)

        configuration = result["generic_final_world"]
        entities = configuration["Sigma"]["entities"]
        self.assertEqual("world:sa001:2", configuration["Sigma"]["revision"])
        self.assertAlmostEqual(
            -16.0,
            entities["entity:sa001:intruder"]["normal_momentum_kg_m_s"],
        )
        self.assertAlmostEqual(
            36.0,
            entities["entity:sa001:anchor"]["normal_momentum_kg_m_s"],
        )
        controller = configuration["Sigma"]["controllers"][
            "controller:sa001:boundary-reflection"
        ]
        self.assertTrue(controller["active"])
        self.assertTrue(controller["per_actuation_revalidation"])
        self.assertEqual(
            bundle["execution"]["parameters"],
            controller["semantic_projection"],
        )
        event = next(
            item
            for item in configuration["H"]
            if item["event_id"] == "event:sa001:reflection"
        )
        self.assertEqual("BoundaryReflectionActuation", event["effect_kind"])
        self.assertEqual(
            ["TargetMomentum", "AnchorReaction", "DissipatedEnergy"],
            event["atomic_accounting"],
        )
        ledger = result["generic_final_ledgers"]["ledger:sa001:momentum-energy"]
        self.assertAlmostEqual(-16.0, ledger["target_momentum_kg_m_s"])
        self.assertAlmostEqual(36.0, ledger["anchor_momentum_kg_m_s"])
        self.assertAlmostEqual(7.2, ledger["dissipated_energy_j"])
        self.assertEqual(15, ledger["events_remaining"])

    def test_all_four_external_golden_variants_abort_deterministically(self) -> None:
        base = load()
        for variant in base["variants"]:
            variant_id = variant["variant_id"]
            with self.subTest(variant=variant_id):
                result = run_shadow_file(SOURCE, variant_id=variant_id)
                self.assert_shadow_pass(result)
                self.assertEqual(
                    f"GOLDEN-SA-001::{variant_id}",
                    result["golden_expectation_id"],
                )
                self.assertEqual(
                    variant["expected_diagnostic"],
                    result["normalized_diagnostic_code"],
                )
                self.assertEqual("Aborted", result["generic_execution"]["status"])
                self.assertEqual(
                    "DeterministicAbort", result["generic_replay"]["status"]
                )
                self.assertTrue(
                    result["generic_execution"]["configuration_unchanged"]
                )
                self.assertTrue(result["generic_execution"]["history_unchanged"])
                self.assertTrue(
                    result["generic_execution"]["world_revision_unchanged"]
                )

    def test_contract_pair_not_names_or_filename_selects_translation(self) -> None:
        registry = default_shadow_translators()
        original = load()
        selected = registry.resolve(original)
        renamed = copy.deepcopy(original)
        renamed["instance_id"] = "renamed:boundary"
        renamed["suite_id"] = "renamed:suite"
        renamed["scenario_kind"] = "renamed-scenario"
        self.assertEqual(BOUNDARY_REFLECTION_PAIR, bundle_contract_pair(renamed))
        self.assertIs(selected, registry.resolve(renamed))
        self.assertEqual(
            selected.translator(original).program,
            selected.translator(renamed).program,
        )
        with tempfile.TemporaryDirectory() as directory:
            result = run_shadow_file(
                write_temp(renamed, directory, "arbitrary.data.json"),
                golden_input=SOURCE,
            )
        self.assert_shadow_pass(result)

    def test_missing_host_records_remain_absent_and_fail_closed(self) -> None:
        cases = (
            (
                "capabilities",
                "capability:sa001:boundary-actuation",
                "ProgramAuthorityError",
            ),
            ("leases", "lease:sa001:controller", "ProgramLeaseError"),
            (
                "ledgers",
                "ledger:sa001:momentum-energy",
                "ProgramAccountingMissing",
            ),
        )
        for store_name, record_id, expected_code in cases:
            with self.subTest(record=record_id):
                bundle = load()
                del bundle["initial_world"][store_name][record_id]
                translation = translate_boundary_reflection(bundle)
                world = translation.world.clone()
                before = world.configuration()
                trace = translation.runtime.execute(translation.program, world)
                replay = translation.runtime.replay(
                    translation.program, translation.world.clone(), trace
                )
                self.assertEqual("Aborted", trace["status"])
                self.assertEqual("PREPARE", trace["abort"]["stage"])
                self.assertEqual(expected_code, trace["abort"]["code"])
                self.assertEqual(before, world.configuration())
                self.assertEqual("DeterministicAbort", replay["status"])

    def test_generic_path_has_no_legacy_executor_or_name_dispatch(self) -> None:
        source = inspect.getsource(translate_boundary_reflection) + inspect.getsource(
            boundary_reflection_executor
        )
        self.assertNotIn(inspect.getsource(boundary_reflection), source)
        for forbidden in (
            "default_service",
            "src.extensions",
            "suite_id ==",
            "instance_id ==",
            "path.name",
            "expected_outcome",
            "embedded_payload",
            "base64",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
