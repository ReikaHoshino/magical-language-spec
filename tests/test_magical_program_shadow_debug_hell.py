from __future__ import annotations

import inspect
import json
import tempfile
import unittest
from pathlib import Path

from src.migration import legacy_program_oracle as shadow

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "conformance" / "magical-program-golden-parity.json"
DEBUG_ROOT = ROOT / "examples" / "spell-instances" / "debug-hell"
PATHS = {
    "001": DEBUG_ROOT / "DEBUG-HELL-001.json",
    "002": DEBUG_ROOT / "DEBUG-HELL-002.json",
    "003": DEBUG_ROOT / "DEBUG-HELL-003.json",
}


def load(number: str):
    return json.loads(PATHS[number].read_text(encoding="utf-8"))


def write_temp(document, directory: str, filename: str) -> Path:
    path = Path(directory) / filename
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def run(number: str, path: Path | None = None):
    return shadow.run_shadow_file(
        PATHS[number] if path is None else path,
        golden_input=PATHS[number],
        golden_manifest=GOLDEN,
    )


class MagicalProgramShadowDebugHellTests(unittest.TestCase):
    maxDiff = None

    def test_current_registry_covers_all_12_bundle_contract_pairs(self) -> None:
        manifest = json.loads(
            (ROOT / "conformance" / "magical-program-shadow-migration.json").read_text(
                encoding="utf-8"
            )
        )
        expected = {
            shadow.bundle_contract_pair(
                json.loads((ROOT / item["path"]).read_text(encoding="utf-8"))
            )
            for item in manifest["inventory"]
        }
        self.assertEqual(expected, shadow.default_shadow_translators().pairs())
        self.assertEqual(12, len(expected))

    def test_pathological_planning_preserves_constraints_and_fails_semantically(self) -> None:
        result = run("001")
        self.assertEqual("PASS", result["status"], result)
        report = result["generic_evaluation"]
        self.assertEqual("Infeasible", report["status"])
        codes = [item["code"] for item in report["diagnostics"]]
        self.assertIn("PlanningAssumptionCannotSatisfyAuthority", codes)
        program_text = json.dumps(result["program"], sort_keys=True)
        for value in ("1000000000", "0.1", "1000000"):
            self.assertIn(value, program_text)

    def test_prepare_bound_transit_aborts_after_trusted_interposition(self) -> None:
        result = run("002")
        self.assertEqual("PASS", result["status"], result)
        execution = result["generic_execution"]
        self.assertEqual("Aborted", execution["status"])
        self.assertEqual("StaleReference", execution["abort"]["code"])
        self.assertTrue(execution["world_revision_unchanged"])
        self.assertTrue(execution["history_unchanged"])
        self.assertEqual("DeterministicAbort", result["generic_replay"]["status"])

    def test_reactive_hydra_executes_three_provisional_microsteps_then_rolls_back(self) -> None:
        bundle = load("003")
        registration = shadow.default_shadow_translators().resolve(bundle)
        translation = registration.translator(bundle)
        self.assertIsNotNone(translation.runtime)
        world = translation.world.clone()
        initial = world.clone()
        execution = translation.runtime.execute(translation.program, world)
        trace = translation.runtime.last_adversarial_trace
        self.assertIsNotNone(trace)
        self.assertEqual("MicrostepBudgetExceeded", execution["abort"]["code"])
        self.assertEqual(
            [0, 1, 2],
            [item["microstep"] for item in trace["executed_microsteps"]],
        )
        self.assertEqual(3, trace["exhausted_at_microstep"])
        self.assertTrue(trace["emergency_stop_requested"])
        self.assertTrue(execution["world_revision_unchanged"])
        self.assertTrue(execution["history_unchanged"])
        replay = translation.runtime.replay(
            translation.program, initial, execution
        )
        replay_trace = translation.runtime.last_adversarial_trace
        self.assertEqual("DeterministicAbort", replay["status"])
        self.assertEqual(trace, replay_trace)

    def test_missing_authority_and_accounting_records_fail_closed(self) -> None:
        for record, expected_code in (
            ("capability:debug003:ward", "ProgramAuthorityError"),
            ("ledger:debug003:ward", "ProgramAccountingMissing"),
        ):
            document = load("003")
            if record.startswith("capability:"):
                document["initial_world"]["capabilities"].pop(record)
            else:
                document["initial_world"]["ledgers"].pop(record)
            with tempfile.TemporaryDirectory() as directory:
                path = write_temp(document, directory, "renamed.json")
                result = run("003", path)
            with self.subTest(record=record):
                execution = result["generic_execution"]
                self.assertEqual(expected_code, execution["abort"]["code"])
                self.assertTrue(execution["world_revision_unchanged"])
                self.assertTrue(execution["history_unchanged"])

    def test_contract_pairs_ignore_fixture_names_and_filenames(self) -> None:
        for number in PATHS:
            document = load(number)
            document["instance_id"] = f"renamed:{number}"
            with tempfile.TemporaryDirectory() as directory:
                path = write_temp(document, directory, f"unrelated-{number}.data")
                result = run(number, path)
            with self.subTest(number=number):
                self.assertEqual("PASS", result["status"], result)

    def test_debug_contract_modules_have_no_dispatch_or_oracle_calls(self) -> None:
        source = inspect.getsource(
            __import__(
                "src.migration.magical_program_shadow_debug_hydra",
                fromlist=["translate_reactive_hydra"],
            )
        ) + inspect.getsource(
            __import__(
                "src.migration.magical_program_shadow_debug",
                fromlist=["translate_prepare_bound_transit"],
            )
        )
        for token in (
            "instance_id ==",
            "suite_id ==",
            "path.name",
            "filename ==",
            "observe_frozen(",
            "default_service(",
            'expected_outcome[',
        ):
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
