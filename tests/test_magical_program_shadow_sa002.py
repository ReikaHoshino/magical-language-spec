from __future__ import annotations

import copy
import inspect
import json
import tempfile
import unittest
from pathlib import Path

from src.extensions.success_arcana.executors import staged_treatment
from src.migration.magical_program_shadow_suite import (
    TREATMENT_STAGED_PAIR,
    bundle_contract_pair,
    default_shadow_translators,
    run_shadow_file,
    translate_staged_treatment,
)
from src.migration.magical_program_shadow_treatment import (
    staged_treatment_executor,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT / "examples" / "spell-instances" / "success-arcana" / "SA-002.json"
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


class MagicalProgramShadowSA002Tests(unittest.TestCase):
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
                "generic_final_world": result.get("generic_final_world"),
                "generic_final_ledgers": result.get("generic_final_ledgers"),
            },
        )

    def test_positive_case_has_three_explicit_stages_and_exact_parity(self) -> None:
        result = run_shadow_file(SOURCE)
        self.assert_shadow_pass(result)
        self.assertEqual("GOLDEN-SA-002", result["golden_expectation_id"])
        self.assertEqual(
            {"legacy": "Feasible", "generic": "ConditionallyFeasible"},
            result["raw_evaluation_status"],
        )
        self.assertIsNone(result["normalized_diagnostic_code"])
        self.assertEqual("Committed", result["generic_execution"]["status"])
        self.assertEqual("Match", result["generic_replay"]["status"])

        program = result["program"]
        stage_nodes = [
            node
            for node in program["nodes"]
            if node["node_id"].startswith("treatment_")
        ]
        self.assertEqual(
            [
                "treatment_stabilize",
                "treatment_repair",
                "treatment_manifest",
            ],
            [node["node_id"] for node in stage_nodes],
        )
        self.assertEqual(
            [120.0, 450.0, 50.0],
            [node["obligations"]["resources"]["energy_j"] for node in stage_nodes],
        )
        self.assertEqual(
            [0.02, 0.005, 0.0],
            [node["obligations"]["resources"]["matter_kg"] for node in stage_nodes],
        )
        self.assertEqual(3, program["budget"]["events"])

        bundle = load()
        text = json.dumps(program, ensure_ascii=False, sort_keys=True)
        self.assertNotIn(SOURCE.read_text(encoding="utf-8"), text)
        self.assertNotIn(bundle["initial_world"]["revision"], text)
        self.assertNotIn(
            bundle["execution"]["parameters"]["result_world_revision"], text
        )
        self.assertNotIn("correspondence_unique", text)
        for record_id in (
            *bundle["execution"]["required_evidence"]["capabilities"],
            *bundle["execution"]["required_evidence"]["leases"],
            *bundle["execution"]["required_evidence"]["accounting"],
        ):
            self.assertNotIn(record_id, text)

        configuration = result["generic_final_world"]
        self.assertEqual("world:sa002:4", configuration["Sigma"]["revision"])
        entities = configuration["Sigma"]["entities"]
        patient = entities["entity:sa002:patient"]
        self.assertEqual(0, patient["injury"]["excess_thermal_energy_j"])
        self.assertEqual(0, patient["injury"]["removable_fluid_kg"])
        self.assertEqual("repaired", patient["injury"]["structural_deviation"])
        self.assertEqual("repaired", patient["injury"]["chemical_deviation"])
        self.assertTrue(patient["tissue_repaired"])
        self.assertEqual("identity:sa002:patient", patient["identity_id"])
        self.assertEqual(
            120.0, entities["entity:sa002:sink"]["absorbed_energy_j"]
        )
        self.assertEqual(
            0.02, entities["entity:sa002:sink"]["absorbed_matter_kg"]
        )
        self.assertEqual(
            0.005, entities["entity:sa002:donor"]["available_matter_kg"]
        )
        self.assertEqual(
            0.0,
            entities["entity:sa002:reservoir"]["available_energy_j"],
        )
        proxy = entities["entity:sa002:proxy"]
        self.assertEqual(
            {
                "kind": "DamageDescriptor",
                "source_patient_id": "entity:sa002:patient",
                "reverse_effect": False,
                "provenance": "token:sa002:red-thread",
            },
            proxy["manifested_descriptor"],
        )
        self.assertEqual(
            [
                "event:sa002:stabilize",
                "event:sa002:repair",
                "event:sa002:manifest",
            ],
            result["generic_execution"]["history_event_ids"][-3:],
        )
        self.assertEqual(
            ["TreatmentStabilize", "TreatmentRepair", "TreatmentManifest"],
            [
                event["effect_kind"]
                for event in configuration["H"][-3:]
            ],
        )

        ledger = result["generic_final_ledgers"]["ledger:sa002"]
        self.assertEqual(120.0, ledger["transferred_to_sink_energy_j"])
        self.assertEqual(500.0, ledger["treatment_energy_consumed_j"])
        self.assertEqual(0.0, ledger["available_energy_j"])
        self.assertAlmostEqual(0.0, ledger["available_matter_kg"])
        self.assertEqual(13, ledger["events_remaining"])
        self.assertEqual(
            {"energy_j": 120.0, "matter_kg": 0.02, "events": 1},
            {
                key: ledger["allocations"]["treatment_stabilize"][key]
                for key in ("energy_j", "matter_kg", "events")
            },
        )
        self.assertEqual(
            {"energy_j": 450.0, "matter_kg": 0.005, "events": 1},
            {
                key: ledger["allocations"]["treatment_repair"][key]
                for key in ("energy_j", "matter_kg", "events")
            },
        )
        self.assertEqual(
            {"energy_j": 50.0, "matter_kg": 0.0, "events": 1},
            {
                key: ledger["allocations"]["treatment_manifest"][key]
                for key in ("energy_j", "matter_kg", "events")
            },
        )

    def test_all_six_external_golden_variants_abort_atomically(self) -> None:
        base = load()
        for variant in base["variants"]:
            variant_id = variant["variant_id"]
            with self.subTest(variant=variant_id):
                result = run_shadow_file(SOURCE, variant_id=variant_id)
                self.assert_shadow_pass(result)
                self.assertEqual(
                    f"GOLDEN-SA-002::{variant_id}",
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
        renamed["instance_id"] = "renamed:treatment"
        renamed["suite_id"] = "renamed:suite"
        renamed["scenario_kind"] = "renamed-scenario"
        self.assertEqual(TREATMENT_STAGED_PAIR, bundle_contract_pair(renamed))
        self.assertIs(selected, registry.resolve(renamed))
        self.assertEqual(
            selected.translator(original).program,
            selected.translator(renamed).program,
        )
        with tempfile.TemporaryDirectory() as directory:
            result = run_shadow_file(
                write_temp(renamed, directory, "arbitrary-treatment.data.json"),
                golden_input=SOURCE,
            )
        self.assert_shadow_pass(result)

    def test_host_registration_and_stage_order_fail_closed(self) -> None:
        for section, field, value in (
            ("structure_schemas", "revision", "999"),
            ("reaction_rules", "revision", "999"),
        ):
            with self.subTest(section=section):
                bundle = load()
                bundle["registry_extensions"][section][0][field] = value
                with self.assertRaisesRegex(ValueError, "host registration"):
                    translate_staged_treatment(bundle)

        translation = translate_staged_treatment(load())
        program = copy.deepcopy(translation.program)
        stage = next(
            item for item in program["values"] if item["value_id"] == "stage_stabilize"
        )
        stage["fields"]["stage"]["value"] = "manifest"
        world = translation.world.clone()
        before = world.configuration()
        trace = translation.runtime.execute(program, world)
        replay = translation.runtime.replay(
            program, translation.world.clone(), trace
        )
        self.assertEqual("Aborted", trace["status"])
        self.assertEqual("COMMIT", trace["abort"]["stage"])
        self.assertEqual("TreatmentStageOrderViolation", trace["abort"]["code"])
        self.assertEqual(before, world.configuration())
        self.assertEqual("DeterministicAbort", replay["status"])

    def test_missing_host_records_remain_absent_and_fail_at_prepare(self) -> None:
        cases = (
            (
                "capabilities",
                "capability:sa002:medical",
                "ProgramAuthorityError",
            ),
            ("leases", "lease:sa002:patient", "ProgramLeaseError"),
            ("ledgers", "ledger:sa002", "ProgramAccountingMissing"),
        )
        for store_name, record_id, expected_code in cases:
            with self.subTest(record=record_id):
                bundle = load()
                del bundle["initial_world"][store_name][record_id]
                translation = translate_staged_treatment(bundle)
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

    def test_generic_contract_has_no_legacy_or_fixture_dispatch(self) -> None:
        source = inspect.getsource(translate_staged_treatment) + inspect.getsource(
            staged_treatment_executor
        )
        self.assertNotIn(inspect.getsource(staged_treatment), source)
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
