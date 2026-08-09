from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from src.mgls import check_source
from src.mgls import frontend

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "examples" / "mgls" / "independent-transition.mgls"
INVENTORY_PATH = ROOT / "examples" / "mgls" / "invalid" / "contract-cases.json"


def base_source() -> str:
    return BASE_PATH.read_text(encoding="utf-8")


def pure_calculate_source() -> str:
    return """mgls \"0\";
source \"source:pure-calculate:001\";
program \"program:pure-calculate:001\";
registry \"registry:reference-experimental\" revision \"1\";
profile \"profile:reference-experimental\" revision \"1\";
budget {
  energy 0;
  events 0;
  microsteps 4;
  concurrency 1;
}
let lhs: number = 1;
let rhs: number = 2;
node total: calculate sum = add(lhs, rhs);
output \"sum\" value from sum;
"""


def natural_cases() -> dict[str, tuple[str, str]]:
    source = base_source()
    extras = "\n".join(
        f"node extra_{index:03d}: resolve extra_ref_{index:03d} from target_selector;"
        for index in range(255)
    )
    over_limit = source.replace(
        'output "result" effect_result from transition_result;',
        extras + '\noutput "result" effect_result from transition_result;',
    )
    return {
        "MGLS-NEG-001": (
            "SpecVersionIncompatible",
            source.replace('mgls "0";', 'mgls "1";', 1),
        ),
        "MGLS-NEG-002": (
            "UnsupportedSemanticExtension",
            source.replace(
                'let desired_state: string = "transitioned";',
                'import "network:model";\nlet desired_state: string = "transitioned";',
            ),
        ),
        "MGLS-NEG-003": (
            "DuplicateBinding",
            source.replace(
                'let desired_state: string = "transitioned";',
                'let desired_state: string = "first";\nlet desired_state: string = "transitioned";',
            ),
        ),
        "MGLS-NEG-004": (
            "UnresolvedName",
            source.replace(
                "(target_ref, desired_state)",
                "(missing_ref, desired_state)",
            ),
        ),
        "MGLS-NEG-005": (
            "RegistryMismatch",
            source.replace(
                '"generic.transition" revision "1"',
                '"unknown.transition" revision "1"',
            ),
        ),
        "MGLS-NEG-006": (
            "TypeError",
            source.replace(
                'let desired_state: string = "transitioned";',
                'let desired_state: bool = "transitioned";',
            ),
        ),
        "MGLS-NEG-007": (
            "DimensionError",
            source.replace(
                'let desired_state: string = "transitioned";',
                'let invalid_energy: quantity<Energy, Length, J> = quantity(10);\n'
                'let desired_state: string = "transitioned";',
            ),
        ),
        "MGLS-NEG-008": (
            "StaticAuthorityError",
            source.replace(
                '    capability "capability.transition" on target_ref effect "Reconfigure";\n',
                "",
            ),
        ),
        "MGLS-NEG-009": (
            "ConservationProofFailure",
            source.replace(
                '    accounting "accounting.transition" kind "EnergyMatter" on target_ref;\n',
                "",
            ),
        ),
        "MGLS-NEG-010": (
            "CausalityCycleError",
            source.replace(
                "node resolve_target: resolve target_ref from target_selector;",
                "node resolve_target after invoke_transition: resolve target_ref from target_selector;",
            ),
        ),
        "MGLS-NEG-011": (
            "EffectMismatch",
            source.replace(
                'output "result" effect_result from transition_result;',
                'output "result" reference from transition_result;',
            ),
        ),
        "MGLS-NEG-012": (
            "ParseError",
            source.replace("energy 10;", "energy NaN;", 1),
        ),
        "MGLS-NEG-013": ("InputLimitExceeded", over_limit),
    }


class MglsNegativeInventoryTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))

    def assert_rejected(self, source: str, expected: str) -> None:
        result = check_source(source)
        self.assertEqual("Rejected", result["status"], result)
        self.assertIsNone(result["program"])
        self.assertIsNone(result["source_map"])
        self.assertEqual(expected, result["diagnostics"][0]["code"])
        span = result["diagnostics"][0]["normalized_span"]
        self.assertGreater(span["end"], span["start"])

    def test_inventory_ids_and_expected_diagnostics_are_exact(self) -> None:
        cases = self.inventory["cases"]
        self.assertEqual(
            [f"MGLS-NEG-{index:03d}" for index in range(1, 16)],
            [item["case_id"] for item in cases],
        )
        self.assertTrue(all(item["must_not_emit_program"] for item in cases))
        implemented = natural_cases()
        expected = {
            item["case_id"]: item["expected_diagnostic"] for item in cases[:13]
        }
        self.assertEqual(expected, {key: value[0] for key, value in implemented.items()})

    def test_first_thirteen_source_mutations_fail_closed(self) -> None:
        for case_id, (expected, source) in natural_cases().items():
            with self.subTest(case_id=case_id):
                self.assert_rejected(source, expected)

    def test_lowering_drift_is_detected_independently(self) -> None:
        source = pure_calculate_source()
        original = frontend._core.compile_source

        def drift(payload: str | bytes) -> dict:
            result = copy.deepcopy(original(payload))
            result["program"]["nodes"][0]["instruction"] = "effect.invoke"
            return result

        with patch.object(frontend._core, "compile_source", side_effect=drift):
            self.assert_rejected(source, "SourceSemanticDrift")

    def test_missing_required_source_map_entry_fails_closed(self) -> None:
        source = base_source()
        original = frontend._core.compile_source

        def omit(payload: str | bytes) -> dict:
            result = copy.deepcopy(original(payload))
            result["source_map"]["entries"] = [
                entry
                for entry in result["source_map"]["entries"]
                if entry["entry_id"] != "map:node:invoke_transition"
            ]
            return result

        with patch.object(frontend._core, "compile_source", side_effect=omit):
            self.assert_rejected(source, "NormalizationFailed")


if __name__ == "__main__":
    unittest.main()
