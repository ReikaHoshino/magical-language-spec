from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from src.evaluator.magical_program import MagicalProgramEvaluator
from src.mgls import (
    MglsCompileError,
    canonical_compilation_bytes,
    check_source,
    compile_file,
    compile_source,
)
from src.runtime.magical_program import MagicalProgramRuntime, program_sandbox_world
from src.runtime.magical_program_contracts import default_runtime_contracts

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "examples" / "mgls"
PROGRAM_SCHEMA = json.loads(
    (ROOT / "schemas" / "magical-program.schema.json").read_text(encoding="utf-8")
)
SOURCE_MAP_SCHEMA = json.loads(
    (ROOT / "schemas" / "mgls-source-map.schema.json").read_text(encoding="utf-8")
)


def source(name: str = "independent-transition.mgls") -> str:
    return (SOURCE_ROOT / name).read_text(encoding="utf-8")


class MglsCompilerTests(unittest.TestCase):
    maxDiff = None

    def test_positive_sources_compile_and_re_admit(self) -> None:
        for name in ("independent-transition.mgls", "boundary-reflection.mgls"):
            with self.subTest(name=name):
                result = compile_file(SOURCE_ROOT / name)
                self.assertEqual("Compiled", result["status"])
                Draft202012Validator(PROGRAM_SCHEMA).validate(result["program"])
                Draft202012Validator(SOURCE_MAP_SCHEMA).validate(result["source_map"])
                self.assertEqual("Accepted", result["target_admission"]["status"])
                self.assertTrue(result["source_map"]["entries"])

    def test_repeated_comment_and_filename_independent_compilation_is_byte_deterministic(self) -> None:
        original = source()
        decorated = original.replace(
            'source "source:bounded-transition:001";',
            'source "source:bounded-transition:001"; // same semantics',
        )
        first = compile_source(original)
        second = compile_source(original)
        third = compile_source(decorated)
        self.assertEqual(
            canonical_compilation_bytes(first),
            canonical_compilation_bytes(second),
        )
        self.assertEqual(first["program"], third["program"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "completely-renamed.data"
            path.write_text(original, encoding="utf-8")
            renamed = compile_file(path)
        self.assertEqual(first["program"], renamed["program"])

    def test_independent_source_evaluates_and_executes_through_generic_runtime(self) -> None:
        program = compile_source(source())["program"]
        evaluator = MagicalProgramEvaluator()
        report = evaluator.evaluate_program(program)
        self.assertEqual("ConditionallyFeasible", report["status"], report)
        world = program_sandbox_world()
        runtime = MagicalProgramRuntime(
            evaluator=evaluator,
            contracts=default_runtime_contracts(),
        )
        execution = runtime.execute(program, world)
        self.assertEqual("Committed", execution["status"], execution)
        self.assertEqual(
            "transitioned",
            world.entities["entity:generic:target"]["status"],
        )

    def test_shared_diagnostics_have_exact_spans_and_no_partial_program(self) -> None:
        cases = {
            "SpecVersionIncompatible": source().replace('mgls "0";', 'mgls "1";', 1),
            "UnsupportedSemanticExtension": source().replace(
                'let desired_state: string = "transitioned";',
                'import "network:model";\nlet desired_state: string = "transitioned";',
            ),
            "DuplicateBinding": source().replace(
                'let desired_state: string = "transitioned";',
                'let desired_state: string = "first";\nlet desired_state: string = "transitioned";',
            ),
            "UnresolvedName": source().replace(
                "(target_ref, desired_state)",
                "(missing_ref, desired_state)",
            ),
            "RegistryMismatch": source().replace(
                '"generic.transition" revision "1"',
                '"unknown.transition" revision "1"',
            ),
            "TypeError": source().replace(
                'let desired_state: string = "transitioned";',
                "let desired_state: int = 1.5;",
            ),
            "StaticAuthorityError": source().replace(
                '    capability "capability.transition" on target_ref effect "Reconfigure";\n',
                "",
            ),
            "ConservationProofFailure": source().replace(
                '    accounting "accounting.transition" kind "EnergyMatter" on target_ref;\n',
                "",
            ),
            "CausalityCycleError": source().replace(
                "node resolve_target: resolve target_ref from target_selector;",
                "node resolve_target after invoke_transition: resolve target_ref from target_selector;",
            ),
            "EffectMismatch": source().replace(
                'output "result" effect_result from transition_result;',
                'output "result" reference from transition_result;',
            ),
            "ParseError": source().replace("energy 10;", "energy NaN;", 1),
        }
        for expected, text in cases.items():
            with self.subTest(expected=expected):
                result = check_source(text)
                self.assertEqual("Rejected", result["status"], result)
                self.assertIsNone(result["program"])
                self.assertIsNone(result["source_map"])
                diagnostic = result["diagnostics"][0]
                self.assertEqual(expected, diagnostic["code"])
                span = diagnostic["normalized_span"]
                self.assertLessEqual(0, span["start"])
                self.assertGreater(span["end"], span["start"])

    def test_strict_utf8_symlink_and_source_limits_fail_closed(self) -> None:
        invalid = check_source(b"\xff\xfe")
        self.assertEqual("InvalidUTF8", invalid["diagnostics"][0]["code"])
        oversized = check_source(b"a" * 262_145)
        self.assertEqual("InputLimitExceeded", oversized["diagnostics"][0]["code"])
        with tempfile.TemporaryDirectory() as directory:
            link = Path(directory) / "source.mgls"
            try:
                link.symlink_to(SOURCE_ROOT / "independent-transition.mgls")
            except OSError:
                self.skipTest("symlink creation not permitted")
            with self.assertRaises(MglsCompileError) as raised:
                compile_file(link)
            self.assertEqual("InputSymlinkRejected", raised.exception.code)

    def test_no_source_filename_fixture_or_spell_dispatch(self) -> None:
        compiler = (ROOT / "src" / "mgls" / "compiler.py").read_text(encoding="utf-8")
        for token in (
            "SA-001",
            "SUCCESS-ARCANA",
            "DEBUG-HELL",
            "path.name",
            "instance_id",
            "suite_id",
            "spell_name",
        ):
            self.assertNotIn(token, compiler)


if __name__ == "__main__":
    unittest.main()
