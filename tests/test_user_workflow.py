from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from src.user_workflow import InputSnapshot, UserWorkflow

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "examples" / "mgls" / "independent-transition.mgls"
BUNDLE = ROOT / "examples" / "spell-instances" / "generic" / "GENERIC-001.json"


class UserWorkflowTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.workflow = UserWorkflow()

    def test_source_and_emitted_program_share_one_runtime_path(self) -> None:
        checked = self.workflow.execute_path("check", SOURCE)
        evaluated = self.workflow.execute_path("eval", SOURCE)
        source_run = self.workflow.execute_path("run", SOURCE)
        compiled = self.workflow.execute_path("compile", SOURCE)

        self.assertEqual("Accepted", checked["status"], checked)
        self.assertEqual("Evaluated", evaluated["status"], evaluated)
        self.assertEqual("Committed", source_run["status"], source_run)
        self.assertEqual("Compiled", compiled["status"], compiled)
        self.assertEqual("Match", source_run["result"]["replay"]["status"])

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "emitted.program.mga.json"
            path.write_text(
                json.dumps(compiled["result"]["program"]), encoding="utf-8"
            )
            program_check = self.workflow.execute_path("check", path)
            program_eval = self.workflow.execute_path("eval", path)
            program_run = self.workflow.execute_path("run", path)

        self.assertEqual("Accepted", program_check["status"], program_check)
        self.assertEqual("Evaluated", program_eval["status"], program_eval)
        self.assertEqual("Committed", program_run["status"], program_run)
        self.assertEqual("Match", program_run["result"]["replay"]["status"])
        self.assertEqual(
            source_run["result"]["execution"],
            program_run["result"]["execution"],
        )
        self.assertEqual(
            source_run["result"]["final_world"],
            program_run["result"]["final_world"],
        )

    def test_repository_bundle_uses_the_same_commands_and_replays(self) -> None:
        checked = self.workflow.execute_path("check", BUNDLE)
        evaluated = self.workflow.execute_path("eval", BUNDLE)
        run = self.workflow.execute_path("run", BUNDLE)
        self.assertEqual("Accepted", checked["status"], checked)
        self.assertEqual("Evaluated", evaluated["status"], evaluated)
        self.assertEqual("PASS", run["status"], run)
        self.assertEqual("Match", run["result"]["replay"]["status"])
        self.assertEqual("Committed", run["result"]["execution"]["status"])

    def test_filename_and_identity_renaming_do_not_select_behavior(self) -> None:
        compilation = self.workflow.execute_path("compile", SOURCE)
        program = copy.deepcopy(compilation["result"]["program"])
        program["program_id"] = "program:renamed-without-dispatch"
        bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
        bundle["instance_id"] = "RENAMED-WITHOUT-DISPATCH"

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "unrelated-source.data"
            program_path = root / "unrelated-program.data"
            bundle_path = root / "unrelated-bundle.data"
            source_path.write_bytes(SOURCE.read_bytes())
            program_path.write_text(json.dumps(program), encoding="utf-8")
            bundle_path.write_text(json.dumps(bundle), encoding="utf-8")

            self.assertEqual(
                "Rejected", self.workflow.execute_path("check", source_path)["status"]
            )
            source_result = self.workflow.execute_path(
                "run", source_path, input_kind="mgls"
            )
            program_result = self.workflow.execute_path(
                "run", program_path, input_kind="magical-program"
            )
            bundle_result = self.workflow.execute_path(
                "run", bundle_path, input_kind="spell-instance-bundle"
            )

        self.assertEqual("Committed", source_result["status"], source_result)
        self.assertEqual("Committed", program_result["status"], program_result)
        self.assertEqual("PASS", bundle_result["status"], bundle_result)
        self.assertEqual(
            source_result["result"]["final_world"]["Sigma"],
            program_result["result"]["final_world"]["Sigma"],
        )
        self.assertNotEqual(
            source_result["result"]["execution"]["history_event_ids"],
            program_result["result"]["execution"]["history_event_ids"],
        )

    def test_stage_suffix_and_decoded_kind_must_agree(self) -> None:
        compilation = self.workflow.execute_path("compile", SOURCE)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wrong_program = root / "bundle-as-program.program.mga.json"
            wrong_bundle = root / "program-as-bundle.bundle.mga.json"
            source_as_json = root / "source.program.mga.json"
            wrong_program.write_bytes(BUNDLE.read_bytes())
            wrong_bundle.write_text(
                json.dumps(compilation["result"]["program"]), encoding="utf-8"
            )
            source_as_json.write_bytes(SOURCE.read_bytes())

            results = (
                self.workflow.execute_path("check", wrong_program),
                self.workflow.execute_path("check", wrong_bundle),
                self.workflow.execute_path(
                    "check", source_as_json, input_kind="mgls"
                ),
            )

        for result in results:
            self.assertEqual("Rejected", result["status"], result)
            self.assertEqual(
                "InputKindHintMismatch", result["diagnostics"][0]["code"]
            )

    def test_single_read_snapshot_is_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.mgls"
            path.write_bytes(SOURCE.read_bytes())
            snapshot = InputSnapshot.read(path)
            path.write_text('mgls "999";', encoding="utf-8")
            result = self.workflow.execute_snapshot("check", snapshot)
        self.assertEqual("Accepted", result["status"], result)

    def test_unknown_contract_and_forbidden_source_fail_without_partial_program(self) -> None:
        source = SOURCE.read_text(encoding="utf-8").replace(
            'let desired_state: string = "transitioned";',
            'import "network:model";\nlet desired_state: string = "transitioned";',
        )
        compilation = self.workflow.execute_path("compile", SOURCE)
        program = copy.deepcopy(compilation["result"]["program"])
        program["nodes"][1]["contract"] = {
            "contract_id": "unknown.transition",
            "revision": "1",
        }

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "forbidden.mgls"
            program_path = root / "unknown.program.mga.json"
            source_path.write_text(source, encoding="utf-8")
            program_path.write_text(json.dumps(program), encoding="utf-8")
            rejected_source = self.workflow.execute_path("compile", source_path)
            rejected_program = self.workflow.execute_path("check", program_path)

        self.assertEqual("Rejected", rejected_source["status"], rejected_source)
        self.assertIsNone(rejected_source["result"])
        self.assertEqual(
            "UnsupportedSemanticExtension",
            rejected_source["diagnostics"][0]["code"],
        )
        self.assertEqual("Rejected", rejected_program["status"], rejected_program)
        self.assertEqual(
            "ProgramUnknownContract", rejected_program["diagnostics"][0]["code"]
        )

    def test_authority_resource_and_sandbox_failures_are_deterministic(self) -> None:
        original = json.loads(BUNDLE.read_text(encoding="utf-8"))
        cases: list[tuple[str, dict]] = []

        authority = copy.deepcopy(original)
        authority["initial_world"]["capabilities"]["capability:GENERIC-001"][
            "active"
        ] = False
        cases.append(("AuthorityError", authority))

        energy = copy.deepcopy(original)
        energy["initial_world"]["ledgers"]["ledger:GENERIC-001"][
            "available_energy_j"
        ] = 0
        cases.append(("ConservationProofFailure", energy))

        limit = copy.deepcopy(original)
        limit["profiles"]["sandbox"]["limits"]["max_energy_j"] = 1_000_000_001
        cases.append(("HostSandboxLimitExceeded", limit))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, (expected, document) in enumerate(cases):
                with self.subTest(expected=expected):
                    path = root / f"case-{index}.bundle.mga.json"
                    path.write_text(json.dumps(document), encoding="utf-8")
                    first = self.workflow.execute_path("run", path)
                    second = self.workflow.execute_path("run", path)
                    self.assertEqual(first, second)
                    self.assertIn(first["status"], {"FAIL", "Rejected"})
                    self.assertIn(
                        expected,
                        [item["code"] for item in first["diagnostics"]],
                        first,
                    )
                    execution = (first.get("result") or {}).get("execution")
                    if isinstance(execution, dict) and execution.get("status") == "Aborted":
                        self.assertTrue(execution.get("configuration_unchanged"))

    def test_common_envelope_and_explicit_kind_mismatch(self) -> None:
        result = self.workflow.execute_path(
            "check", SOURCE, input_kind="magical-program"
        )
        self.assertEqual(
            {
                "contract_id": "magical-language-workflow",
                "revision": "0",
                "stability": "experimental",
            },
            result["workflow"],
        )
        self.assertEqual("Rejected", result["status"])
        self.assertEqual("InputKindHintMismatch", result["diagnostics"][0]["code"])
        self.assertEqual(SOURCE.read_bytes(), SOURCE.read_bytes())


if __name__ == "__main__":
    unittest.main()
