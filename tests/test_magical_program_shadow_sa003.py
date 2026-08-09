from __future__ import annotations

import copy
import inspect
import json
import tempfile
import unittest
from pathlib import Path

from src.migration.magical_program_shadow import (
    EVIDENCE_FUSION_PAIR,
    bundle_contract_pair,
    default_shadow_translators,
    run_shadow_file,
    translate_evidence_fusion,
)
from src.migration.magical_program_shadow_success_arcana import (
    evidence_fusion_executor,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT / "examples" / "spell-instances" / "success-arcana" / "SA-003.json"
)


def load():
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def write_temp(document, directory: str, filename: str = "arbitrary-input.json") -> Path:
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


class MagicalProgramShadowSA003Tests(unittest.TestCase):
    maxDiff = None

    def assert_shadow_pass(self, result):
        self.assertEqual(
            "PASS",
            result["status"],
            {
                "false_comparisons": false_comparisons(result),
                "raw_status": result.get("raw_evaluation_status"),
                "normalized_status": result.get("normalized_evaluation_status"),
                "diagnostic": result.get("normalized_diagnostic_code"),
                "legacy_golden": result.get("legacy_golden"),
                "generic_golden": result.get("generic_golden"),
                "generic_execution": result.get("generic_execution"),
                "generic_replay": result.get("generic_replay"),
            },
        )

    def test_positive_case_has_exact_artifact_event_accounting_and_replay_parity(self) -> None:
        result = run_shadow_file(SOURCE)
        self.assert_shadow_pass(result)
        self.assertEqual("implemented", result["classification"])
        self.assertEqual("GOLDEN-SA-003", result["golden_expectation_id"])
        self.assertEqual(
            {"legacy": "Feasible", "generic": "ConditionallyFeasible"},
            result["raw_evaluation_status"],
        )
        self.assertEqual(
            "ExecutablePendingOrCompletedAuthorityBinding",
            result["normalized_evaluation_status"],
        )
        self.assertIsNone(result["normalized_diagnostic_code"])
        self.assertEqual("PASS", result["legacy_golden"]["status"])
        self.assertEqual("PASS", result["generic_golden"]["status"])
        self.assertEqual("Committed", result["generic_execution"]["status"])
        self.assertEqual("Match", result["generic_replay"]["status"])

        program = result["program"]
        values = {item["value_id"]: item for item in program["values"]}
        self.assertEqual("selector", values["subject_hint"]["kind"])
        self.assertEqual("record", values["fusion_model"]["kind"])
        self.assertEqual("EvidenceFusionModel", values["fusion_model"]["type_id"])
        self.assertEqual("sequence", values["ranking"]["kind"])
        self.assertEqual(
            "record:HypothesisScore", values["ranking"]["element_type"]
        )
        node = next(
            item for item in program["nodes"] if item["node_id"] == "fuse_evidence"
        )
        self.assertEqual("evidence.observe", node["instruction"])
        self.assertEqual(
            {"evidence", "artifact", "event"},
            {item["kind"] for item in program["outputs"]},
        )

        program_text = json.dumps(program, ensure_ascii=False, sort_keys=True)
        bundle = load()
        self.assertNotIn(SOURCE.read_text(encoding="utf-8"), program_text)
        for record_id in (
            *bundle["execution"]["required_evidence"]["capabilities"],
            *bundle["execution"]["required_evidence"]["leases"],
            *bundle["execution"]["required_evidence"]["accounting"],
        ):
            self.assertNotIn(record_id, program_text)
        for forbidden in (
            "initial_world",
            "expected_outcome",
            "registry_extensions",
            "embedded_payload",
            "base64",
        ):
            self.assertNotIn(forbidden, program_text)

        configuration = result["generic_final_world"]
        self.assertEqual("world:sa003:7", configuration["Sigma"]["revision"])
        artifact = configuration["Omega"]["evidence_store"]["artifacts"][
            "artifact:sa003:observation"
        ]
        self.assertEqual("hypothesis:A", artifact["winner_hypothesis_id"])
        self.assertEqual(
            [
                {"hypothesis_id": "hypothesis:A", "score": 0.82},
                {"hypothesis_id": "hypothesis:B", "score": 0.61},
            ],
            artifact["ranking"],
        )
        self.assertEqual(
            [
                {
                    "event_id": "m:h1",
                    "effect_kind": "HistoricalMeasurement",
                    "source_id": "archive:A",
                },
                {
                    "event_id": "m:h2",
                    "effect_kind": "HistoricalMeasurement",
                    "source_id": "archive:B",
                },
                {
                    "event_id": "m:current",
                    "effect_kind": "TraceMeasurement",
                    "source_id": "observer:trace",
                    "value": "trace:blue",
                },
            ],
            artifact["evidence_bundle"],
        )
        self.assertFalse(artifact["confidence_is_truth"])
        self.assertFalse(artifact["physical_display_effect"])
        event = next(
            item
            for item in configuration["H"]
            if item["event_id"] == "event:sa003:artifact"
        )
        self.assertEqual("ObservationArtifactPublished", event["effect_kind"])
        self.assertFalse(event["world_state_changed"])
        self.assertFalse(event["future_prediction"])
        self.assertFalse(event["history_rewind"])

        ledger = result["generic_final_ledgers"]["ledger:sa003"]
        self.assertEqual(40.0, ledger["consumed_energy_j"])
        self.assertEqual(50.0, ledger["available_energy_j"])
        self.assertEqual(15, ledger["events_remaining"])

    def test_all_six_variants_use_external_golden_and_abort_deterministically(self) -> None:
        base = load()
        for variant in base["variants"]:
            variant_id = variant["variant_id"]
            with self.subTest(variant=variant_id):
                result = run_shadow_file(SOURCE, variant_id=variant_id)
                self.assert_shadow_pass(result)
                self.assertEqual(
                    f"GOLDEN-SA-003::{variant_id}",
                    result["golden_expectation_id"],
                )
                self.assertEqual("PASS", result["legacy_golden"]["status"])
                self.assertEqual("PASS", result["generic_golden"]["status"])
                self.assertEqual("Aborted", result["generic_execution"]["status"])
                self.assertEqual(
                    "DeterministicAbort", result["generic_replay"]["status"]
                )
                self.assertTrue(
                    result["generic_execution"]["configuration_unchanged"]
                )
                self.assertTrue(result["generic_execution"]["history_unchanged"])
                self.assertEqual(
                    base["initial_world"]["revision"],
                    result["generic_final_world"]["Sigma"]["revision"],
                )
                self.assertNotIn(
                    "artifact:sa003:observation",
                    result["generic_final_world"]
                    .get("Omega", {})
                    .get("evidence_store", {})
                    .get("artifacts", {}),
                )

    def test_embedded_expected_outcome_cannot_change_shadow_truth(self) -> None:
        altered = load()
        altered["expected_outcome"]["final_invariants"]["Sigma"][
            "revision"
        ] = "world:invented"
        altered["expected_outcome"]["expected_event_ids"] = ["event:invented"]
        with tempfile.TemporaryDirectory() as directory:
            result = run_shadow_file(
                write_temp(altered, directory, filename="altered-expectation.json"),
                golden_input=SOURCE,
            )
        self.assert_shadow_pass(result)
        self.assertEqual("GOLDEN-SA-003", result["golden_expectation_id"])

    def test_missing_host_record_remains_absent_and_fails_closed_at_prepare(self) -> None:
        bundle = load()
        del bundle["initial_world"]["capabilities"]["capability:sa003:privacy"]
        translation = translate_evidence_fusion(bundle)
        self.assertNotIn(
            "capability:sa003:privacy", translation.world.capabilities
        )
        report = translation.evaluator.evaluate_program(translation.program)
        world = translation.world.clone()
        before = world.configuration()
        trace = translation.runtime.execute(translation.program, world)
        replay = translation.runtime.replay(
            translation.program, translation.world.clone(), trace
        )
        self.assertEqual("ConditionallyFeasible", report["status"])
        self.assertEqual("Aborted", trace["status"])
        self.assertEqual("PREPARE", trace["abort"]["stage"])
        self.assertEqual("ProgramAuthorityError", trace["abort"]["code"])
        self.assertEqual(before, world.configuration())
        self.assertEqual("DeterministicAbort", replay["status"])

    def test_contract_pair_not_names_or_filename_selects_the_translator(self) -> None:
        registry = default_shadow_translators()
        original = load()
        selected = registry.resolve(original)
        renamed = copy.deepcopy(original)
        renamed["instance_id"] = "renamed:instance"
        renamed["suite_id"] = "renamed:suite"
        renamed["scenario_kind"] = "renamed-scenario"
        self.assertEqual(EVIDENCE_FUSION_PAIR, bundle_contract_pair(renamed))
        self.assertIs(selected, registry.resolve(renamed))

        original_program = selected.translator(original).program
        renamed_program = selected.translator(renamed).program
        self.assertEqual(original_program, renamed_program)
        with tempfile.TemporaryDirectory() as directory:
            result = run_shadow_file(
                write_temp(renamed, directory, filename="not-a-spell-name.data.json"),
                golden_input=SOURCE,
            )
        self.assert_shadow_pass(result)

    def test_success_arcana_generic_path_has_no_legacy_executor_dependency(self) -> None:
        source = inspect.getsource(translate_evidence_fusion) + inspect.getsource(
            evidence_fusion_executor
        )
        for forbidden in (
            "default_service",
            "src.extensions",
            "suite_id ==",
            "instance_id ==",
            "path.name",
            "embedded_payload",
            "base64",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
