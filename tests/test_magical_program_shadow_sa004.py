from __future__ import annotations

import copy
import inspect
import json
import tempfile
import unittest
from pathlib import Path

from src.extensions.success_arcana.executors import explosion
from src.migration.magical_program_shadow_explosion import explosion_executor
from src.migration.magical_program_shadow_suite import (
    EXPLOSION_PAIR,
    bundle_contract_pair,
    default_shadow_translators,
    run_shadow_file,
    translate_explosion,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT / "examples" / "spell-instances" / "success-arcana" / "SA-004.json"
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


class MagicalProgramShadowSA004Tests(unittest.TestCase):
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
                "world": result.get("generic_final_world"),
                "ledgers": result.get("generic_final_ledgers"),
            },
        )

    def assert_blast_effect(
        self,
        observed,
        *,
        pressure_pa,
        impulse_kg_m_s,
        thermal_energy_j,
        duration_s,
    ):
        self.assertEqual(
            {
                "pressure_pa",
                "radial_impulse_kg_m_s",
                "thermal_energy_j",
                "duration_s",
            },
            set(observed),
        )
        self.assertAlmostEqual(pressure_pa, observed["pressure_pa"], places=9)
        self.assertAlmostEqual(
            impulse_kg_m_s, observed["radial_impulse_kg_m_s"], places=9
        )
        self.assertAlmostEqual(
            thermal_energy_j, observed["thermal_energy_j"], places=9
        )
        self.assertAlmostEqual(duration_s, observed["duration_s"], places=12)

    def test_positive_case_has_prepare_bound_targets_attenuation_and_accounting(self) -> None:
        result = run_shadow_file(SOURCE)
        self.assert_shadow_pass(result)
        self.assertEqual("GOLDEN-SA-004", result["golden_expectation_id"])
        self.assertEqual(
            {"legacy": "Feasible", "generic": "ConditionallyFeasible"},
            result["raw_evaluation_status"],
        )
        self.assertEqual("Committed", result["generic_execution"]["status"])
        self.assertEqual("Match", result["generic_replay"]["status"])
        self.assertIsNone(result["normalized_diagnostic_code"])

        program = result["program"]
        text = json.dumps(program, ensure_ascii=False, sort_keys=True)
        bundle = load()
        self.assertNotIn(SOURCE.read_text(encoding="utf-8"), text)
        self.assertNotIn(bundle["initial_world"]["revision"], text)
        self.assertNotIn(
            bundle["execution"]["parameters"]["result_world_revision"], text
        )
        for entity_id in (
            "entity:sa004:near",
            "entity:sa004:far",
            "entity:sa004:outside",
        ):
            self.assertNotIn(entity_id, text)
        for record_id in (
            *bundle["execution"]["required_evidence"]["capabilities"],
            *bundle["execution"]["required_evidence"]["leases"],
            *bundle["execution"]["required_evidence"]["accounting"],
        ):
            self.assertNotIn(record_id, text)

        configuration = result["generic_final_world"]
        self.assertEqual("world:sa004:2", configuration["Sigma"]["revision"])
        entities = configuration["Sigma"]["entities"]
        self.assert_blast_effect(
            entities["entity:sa004:near"]["blast_effect"],
            pressure_pa=120000.0,
            impulse_kg_m_s=60.0,
            thermal_energy_j=1125.0,
            duration_s=0.25,
        )
        self.assert_blast_effect(
            entities["entity:sa004:far"]["blast_effect"],
            pressure_pa=40000.0,
            impulse_kg_m_s=20.0,
            thermal_energy_j=375.0,
            duration_s=0.25,
        )
        self.assertNotIn("blast_effect", entities["entity:sa004:outside"])
        self.assertAlmostEqual(
            -80.0,
            entities["entity:sa004:anchor"]["reaction_impulse_kg_m_s"],
            places=9,
        )
        self.assertEqual(
            [
                "event:sa004:blast-activated",
                "event:sa004:blast-terminated",
            ],
            result["generic_execution"]["history_event_ids"][-2:],
        )

        ledger = result["generic_final_ledgers"]["ledger:sa004:blast"]
        self.assertEqual(1000.0, ledger["available_energy_j"])
        self.assertEqual(5000.0, ledger["released_energy_j"])
        self.assertEqual(3500.0, ledger["pressure_energy_j"])
        self.assertEqual(1500.0, ledger["thermal_energy_j"])
        self.assertAlmostEqual(
            -80.0, ledger["reaction_impulse_kg_m_s"], places=9
        )
        self.assertEqual(14, ledger["events_remaining"])

    def test_all_nine_external_golden_variants_abort_atomically(self) -> None:
        base = load()
        for variant in base["variants"]:
            variant_id = variant["variant_id"]
            with self.subTest(variant=variant_id):
                result = run_shadow_file(SOURCE, variant_id=variant_id)
                self.assert_shadow_pass(result)
                self.assertEqual(
                    f"GOLDEN-SA-004::{variant_id}",
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
        renamed["instance_id"] = "renamed:explosion"
        renamed["suite_id"] = "renamed:suite"
        renamed["scenario_kind"] = "renamed-scenario"
        self.assertEqual(EXPLOSION_PAIR, bundle_contract_pair(renamed))
        self.assertIs(selected, registry.resolve(renamed))
        self.assertEqual(
            selected.translator(original).program,
            selected.translator(renamed).program,
        )
        with tempfile.TemporaryDirectory() as directory:
            result = run_shadow_file(
                write_temp(renamed, directory, "arbitrary-blast.data.json"),
                golden_input=SOURCE,
            )
        self.assert_shadow_pass(result)

    def test_host_model_and_affected_set_tampering_fail_closed(self) -> None:
        bundle = load()
        bundle["registry_extensions"]["explosion_models"][0][
            "valid_radius_m"
        ] = 1000
        with self.assertRaisesRegex(ValueError, "host registration"):
            translate_explosion(bundle)

        translation = translate_explosion(load())
        evidence = next(
            record
            for record in translation.world.runtime_state["evidence"].values()
            if record["kind"] == "ExplosionAffectedSet"
        )
        evidence["targets"][0]["state_revision"] = "state:tampered"
        world = translation.world.clone()
        before = world.configuration()
        trace = translation.runtime.execute(translation.program, world)
        replay = translation.runtime.replay(
            translation.program, translation.world.clone(), trace
        )
        self.assertEqual("Aborted", trace["status"])
        self.assertEqual("COMMIT", trace["abort"]["stage"])
        self.assertEqual("StaleReference", trace["abort"]["code"])
        self.assertEqual(before, world.configuration())
        self.assertEqual("DeterministicAbort", replay["status"])

    def test_missing_host_records_remain_absent_and_fail_at_prepare(self) -> None:
        cases = (
            ("capabilities", "capability:sa004:blast", "ProgramAuthorityError"),
            ("leases", "lease:sa004:blast", "ProgramLeaseError"),
            ("ledgers", "ledger:sa004:blast", "ProgramAccountingMissing"),
        )
        for store_name, record_id, expected_code in cases:
            with self.subTest(record=record_id):
                bundle = load()
                del bundle["initial_world"][store_name][record_id]
                translation = translate_explosion(bundle)
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
        source = inspect.getsource(translate_explosion) + inspect.getsource(
            explosion_executor
        )
        self.assertNotIn(inspect.getsource(explosion), source)
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
