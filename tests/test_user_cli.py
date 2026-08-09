from __future__ import annotations

import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path

from src.user_cli import main
from src.user_workflow import UserWorkflow

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "examples" / "mgls" / "independent-transition.mgls"


def invoke(arguments: list[str]) -> tuple[int, dict, str]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = main(arguments)
    text = output.getvalue()
    return code, json.loads(text), text


class UserCliTests(unittest.TestCase):
    maxDiff = None

    def test_compile_emits_program_and_source_map_then_runs_program(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            program = root / "emitted.program.mga.json"
            source_map = root / "emitted.source-map.mga.json"
            code, compiled, _ = invoke(
                [
                    "compile",
                    str(SOURCE),
                    "--emit-program",
                    str(program),
                    "--emit-source-map",
                    str(source_map),
                ]
            )
            self.assertEqual(0, code, compiled)
            self.assertEqual("Compiled", compiled["status"])
            self.assertEqual(
                {"program": True, "source_map": True},
                compiled["result"]["emitted"],
            )
            self.assertEqual(
                "MagicalProgram", json.loads(program.read_text())["artifact_kind"]
            )
            self.assertEqual(
                "MglsSourceMap", json.loads(source_map.read_text())["artifact_kind"]
            )

            check_code, checked, _ = invoke(["check", str(program)])
            eval_code, evaluated, _ = invoke(["eval", str(program)])
            run_code, run, _ = invoke(["run", str(program)])

        self.assertEqual(0, check_code, checked)
        self.assertEqual(0, eval_code, evaluated)
        self.assertEqual(0, run_code, run)
        self.assertEqual("Accepted", checked["status"])
        self.assertEqual("Evaluated", evaluated["status"])
        self.assertEqual("Committed", run["status"])
        self.assertEqual("Match", run["result"]["replay"]["status"])

    def test_rejection_and_abort_exit_codes_are_stable_json_without_traceback(self) -> None:
        compiled = UserWorkflow().execute_path("compile", SOURCE)["result"]["program"]
        aborted = copy.deepcopy(compiled)
        aborted["values"][0]["selector"]["entity_type"] = "absent-target"

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            malformed = root / "malformed.mgls"
            aborting = root / "abort.program.mga.json"
            malformed.write_text('mgls "0"; import "host";', encoding="utf-8")
            aborting.write_text(json.dumps(aborted), encoding="utf-8")

            reject_code, rejected, reject_text = invoke(["check", str(malformed)])
            abort_code, abort, abort_text = invoke(["run", str(aborting)])

        self.assertEqual(2, reject_code, rejected)
        self.assertEqual("Rejected", rejected["status"])
        self.assertNotIn("Traceback", reject_text)
        self.assertEqual(3, abort_code, abort)
        self.assertEqual("Aborted", abort["status"])
        self.assertNotIn("Traceback", abort_text)
        self.assertEqual(
            ["ProgramResolutionDeferred", "ProgramRuntimeRevalidationRequired", "ProgramResolutionFailure"],
            [item["code"] for item in abort["diagnostics"]],
        )
        self.assertEqual(
            "ProgramResolutionFailure",
            abort["result"]["execution"]["abort"]["code"],
        )

    def test_output_paths_do_not_collide_or_overwrite_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            duplicate = root / "same.json"
            collision_code, collision, _ = invoke(
                [
                    "compile",
                    str(SOURCE),
                    "--emit-program",
                    str(duplicate),
                    "--emit-source-map",
                    str(duplicate),
                ]
            )
            overwrite_code, overwrite, _ = invoke(
                [
                    "compile",
                    str(SOURCE),
                    "--emit-program",
                    str(SOURCE),
                ]
            )
        self.assertEqual(2, collision_code)
        self.assertEqual(
            "OutputPathCollision", collision["diagnostics"][0]["code"]
        )
        self.assertEqual(2, overwrite_code)
        self.assertEqual(
            "OutputOverwritesInput", overwrite["diagnostics"][0]["code"]
        )

    def test_existing_stable_entry_points_remain_published(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        for marker in (
            'magical-language = "src.user_cli:main"',
            'magical-language-evaluator = "src.evaluator.cli:main"',
            'magical-language-conformance = "src.conformance_cli:main"',
            'magical-language-artifact = "src.artifacts.cli:main"',
            'magical-language-spell-instances = "tools.run_spell_instances:main"',
        ):
            self.assertIn(marker, pyproject)


if __name__ == "__main__":
    unittest.main()
