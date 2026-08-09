from __future__ import annotations

import copy
import inspect
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from src.migration.magical_program_shadow import (
    BOUNDARY_REFLECTION_PAIR,
    EVIDENCE_FUSION_PAIR,
    UNSUPPORTED_CONTRACTS,
    _generic_executor,
    bundle_contract_pair,
    default_shadow_translators,
    run_shadow_file,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "conformance" / "magical-program-shadow-migration.json"
SCHEMA_PATH = ROOT / "schemas" / "magical-program-shadow-migration.schema.json"
SOURCE_ROOT = ROOT / "examples" / "spell-instances"
GENERIC_PATH = SOURCE_ROOT / "generic" / "GENERIC-001.json"
UNSUPPORTED_PATHS = tuple(
    SOURCE_ROOT / "success-arcana" / f"SA-00{number}.json"
    for number in range(5, 9)
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class MagicalProgramShadowFoundationTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load(SCHEMA_PATH)
        cls.manifest = load(MANIFEST_PATH)
        Draft202012Validator.check_schema(cls.schema)
        Draft202012Validator(cls.schema).validate(cls.manifest)

    def test_manifest_mechanically_covers_every_current_bundle(self) -> None:
        observed = {
            path.relative_to(ROOT).as_posix()
            for path in SOURCE_ROOT.rglob("*.json")
        }
        declared = {item["path"] for item in self.manifest["inventory"]}
        self.assertEqual(12, len(observed))
        self.assertEqual(observed, declared)
        self.assertEqual(
            list(range(1, 13)),
            sorted(item["order"] for item in self.manifest["inventory"]),
        )
        self.assertEqual(
            12,
            len({item["migration_id"] for item in self.manifest["inventory"]}),
        )
        self.assertEqual(
            ["semantic_contract", "runtime_contract"],
            self.manifest["selection_policy"]["dispatch_keys"],
        )
        self.assertEqual(
            "external-frozen-oracle-only",
            self.manifest["selection_policy"]["legacy_executor_role"],
        )

    def test_foundation_translator_selection_uses_only_contract_pair(self) -> None:
        registry = default_shadow_translators()
        generic = load(GENERIC_PATH)
        selected = registry.resolve(generic)
        renamed = copy.deepcopy(generic)
        renamed["instance_id"] = "RENAMED-INSTANCE"
        renamed["suite_id"] = "RENAMED-SUITE"
        renamed["scenario_kind"] = "renamed-scenario"
        self.assertIs(selected, registry.resolve(renamed))
        self.assertEqual(bundle_contract_pair(generic), bundle_contract_pair(renamed))

        expected_pairs = {
            (
                ("example.generic-transition", "1"),
                ("runtime.generic-transition", "1"),
            ),
            BOUNDARY_REFLECTION_PAIR,
            EVIDENCE_FUSION_PAIR,
        }
        expected_pairs.update(
            ((contract_id, "1"), None)
            for contract_id in UNSUPPORTED_CONTRACTS
        )
        self.assertEqual(expected_pairs, registry.pairs())

    def test_independent_generic_case_has_exact_owned_runtime_parity(self) -> None:
        result = run_shadow_file(GENERIC_PATH)
        self.assertEqual("PASS", result["status"], result)
        self.assertEqual("implemented", result["classification"])
        self.assertEqual(
            {"legacy": "Feasible", "generic": "ConditionallyFeasible"},
            result["raw_evaluation_status"],
        )
        self.assertEqual(
            "ExecutablePendingOrCompletedAuthorityBinding",
            result["normalized_evaluation_status"],
        )
        self.assertTrue(all(result["comparisons"].values()), result)
        self.assertEqual("Committed", result["generic_execution"]["status"])
        self.assertEqual("Match", result["generic_replay"]["status"])
        self.assertEqual(
            "world:GENERIC-001:2",
            result["generic_final_world"]["Sigma"]["revision"],
        )
        self.assertEqual(
            "transitioned",
            result["generic_final_world"]["Sigma"]["entities"][
                "entity:GENERIC-001:target"
            ]["transition_state"],
        )
        self.assertIn(
            "event:GENERIC-001:transition",
            result["generic_execution"]["history_event_ids"],
        )

        program_text = json.dumps(result["program"], sort_keys=True)
        source_bundle_text = GENERIC_PATH.read_text(encoding="utf-8")
        self.assertNotIn(source_bundle_text, program_text)
        for forbidden in (
            "embedded_payload",
            "shadow.spell-instance",
            "registry_extensions",
            "expected_outcome",
            "initial_world",
        ):
            self.assertNotIn(forbidden, program_text)
        executor_source = inspect.getsource(_generic_executor)
        self.assertNotIn("default_service", executor_source)
        self.assertNotIn("generic_transition_executor", executor_source)

    def test_all_recognized_unsupported_cases_remain_indeterminate(self) -> None:
        observed_contracts = set()
        for path in UNSUPPORTED_PATHS:
            with self.subTest(path=path.name):
                result = run_shadow_file(path)
                self.assertEqual("PASS", result["status"], result)
                self.assertEqual("recognized-unsupported", result["classification"])
                self.assertEqual(
                    {"legacy": "Indeterminate", "generic": "Indeterminate"},
                    result["raw_evaluation_status"],
                )
                self.assertTrue(all(result["comparisons"].values()), result)
                self.assertIsNone(result["generic_execution"])
                self.assertEqual(
                    ["UnsupportedSemanticSubset"],
                    [
                        item["code"]
                        for item in result["generic_evaluation"]["diagnostics"]
                    ],
                )
                program = result["program"]
                observed_contracts.add(
                    program["nodes"][0]["contract"]["contract_id"]
                )
                self.assertNotIn("embedded_payload", json.dumps(program))
        self.assertEqual(set(UNSUPPORTED_CONTRACTS), observed_contracts)

    def test_source_audit_prohibits_filename_and_fixture_dispatch(self) -> None:
        migration_root = ROOT / "src" / "migration"
        sources = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(migration_root.glob("magical_program_shadow*.py"))
        )
        translation_region = sources.split("def run_shadow_file", 1)[0]
        for forbidden in (
            "SUCCESS-ARCANA-005",
            "SUCCESS-ARCANA-006",
            "SUCCESS-ARCANA-007",
            "SUCCESS-ARCANA-008",
            "GENERIC-001.json",
            "suite_id ==",
            "instance_id ==",
            "filename",
            "embedded_payload",
            "shadow.spell-instance",
            "base64",
        ):
            self.assertNotIn(forbidden, translation_region)


if __name__ == "__main__":
    unittest.main()
