"""D-01 representation tests; these do not claim grouped execution support."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator

from src.artifacts.magical_program import (
    MagicalProgramAdmissionError, MagicalProgramHostLimits, admit_program,
)
from src.evaluator.magical_program import MagicalProgramEvaluator
from src.evaluator.schema import validator
from src.mgls import check_source, compile_file, compile_source
from src.runtime.magical_program import (
    MagicalProgramRuntime, ProgramRuntimeError, complete_runtime_state,
    program_sandbox_world,
)
from src.user_workflow import UserWorkflow

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "examples/execution-admission/explicit-groups.mgls").read_text(
    encoding="utf-8"
)


class ExecutionAdmissionStructureTests(unittest.TestCase):
    def setUp(self):
        self.compiled = compile_source(SOURCE)
        self.program = self.compiled["program"]
        self.schema = validator("magical-program.schema.json").schema
        self.evaluator = MagicalProgramEvaluator()

    def admit(self, program, **kwargs):
        return admit_program(
            program, schema=self.schema,
            registered_contracts=self.evaluator.contracts.admitted_pairs(), **kwargs,
        )

    def assert_rejected(self, program, code):
        with self.assertRaises(MagicalProgramAdmissionError) as caught:
            self.admit(program)
        self.assertEqual(code, caught.exception.code)

    def test_explicit_policies_compile_and_re_admit(self):
        for policy in ("Incremental", "WholePlanPreflight"):
            with self.subTest(policy=policy):
                result = compile_source(SOURCE.replace("admission Incremental;", f"admission {policy};"))
                execution = result["program"]["execution_admission"]
                self.assertEqual(policy, execution["policy"])
                self.assertEqual("execution-admission", execution["contract_id"])
                self.assertEqual("1", execution["revision"])
                self.assertEqual(
                    [["resolve_target", "invoke_transition"], ["sum"]],
                    [group["node_ids"] for group in execution["atomic_groups"]],
                )
                self.assertEqual("Accepted", self.admit(result["program"])["status"])
                Draft202012Validator(self.schema).validate(result["program"])

    def test_source_map_preserves_explicit_policy_and_group_spans(self):
        entries = self.compiled["source_map"]["entries"]
        policy = next(entry for entry in entries if entry["entry_id"] == "map:admission:policy")
        span = policy["source_span"]
        self.assertEqual("admission Incremental;", SOURCE[span["start"]:span["end"]])
        self.assertEqual("exact", policy["relation"])
        for index, name in enumerate(("bind_and_transition", "calculate_later")):
            entry = next(item for item in entries if item["entry_id"] == f"map:atomic-group:{index}")
            span = entry["source_span"]
            self.assertTrue(SOURCE[span["start"]:span["end"]].startswith(f"atomic {name} {{"))
            self.assertEqual(f"execution_admission.atomic_groups.{index}", entry["target"]["field"])
        self.assertEqual("lowered", self.program["provenance"]["relation"])
        Draft202012Validator(validator("mgls-source-map.schema.json").schema).validate(
            self.compiled["source_map"]
        )

    def test_closed_execution_record_rejects_unknown_or_missing_fields(self):
        cases = [
            lambda item: item.update(policy="Unsafe"),
            lambda item: item.update(revision="future"),
            lambda item: item.update(contract_id="unknown"),
            lambda item: item.update(capability={"grant": True}),
            lambda item: item.pop("policy"),
            lambda item: item.pop("atomic_groups"),
            lambda item: item.update(atomic_groups=[]),
            lambda item: item["atomic_groups"][0].update(node_ids=[]),
            lambda item: item["atomic_groups"][0].update(rollback_prior=True),
            lambda item: item["atomic_groups"][0]["node_ids"].append("resolve_target"),
        ]
        for mutate in cases:
            program = copy.deepcopy(self.program)
            mutate(program["execution_admission"])
            with self.subTest(execution=program["execution_admission"]):
                self.assert_rejected(program, "ProgramSchemaViolation")
        for invalid in (None, True, [], "Incremental"):
            program = copy.deepcopy(self.program)
            program["execution_admission"] = invalid
            self.assert_rejected(program, "ProgramSchemaViolation")

    def test_group_partition_rejects_duplicate_missing_unknown_and_overlapping_nodes(self):
        cases = [
            ("ProgramDuplicateAtomicGroup", lambda groups: groups[1].update(group_id=groups[0]["group_id"])),
            ("ProgramAtomicGroupIncomplete", lambda groups: groups[0]["node_ids"].remove("resolve_target")),
            ("ProgramAtomicGroupUnknownNode", lambda groups: groups[0]["node_ids"].append("unknown")),
            ("ProgramAtomicGroupOverlap", lambda groups: groups[1]["node_ids"].append("resolve_target")),
            ("ProgramAtomicGroupOrderViolation", lambda groups: groups.reverse()),
        ]
        for code, mutate in cases:
            program = copy.deepcopy(self.program)
            mutate(program["execution_admission"]["atomic_groups"])
            with self.subTest(code=code):
                self.assert_rejected(program, code)
        program = copy.deepcopy(self.program)
        program["execution_admission"]["atomic_groups"][0]["node_ids"] = ["resolve_target", "sum"]
        program["execution_admission"]["atomic_groups"][1]["node_ids"] = ["invoke_transition"]
        self.assert_rejected(program, "ProgramAtomicGroupOrderViolation")

    def test_group_metadata_does_not_replace_data_edges_or_host_limits(self):
        program = copy.deepcopy(self.program)
        program["execution_admission"]["atomic_groups"] = [
            {"group_id": "resolve", "node_ids": ["resolve_target"]},
            {"group_id": "rest", "node_ids": ["invoke_transition", "sum"]},
        ]
        self.assertEqual("Accepted", self.admit(program)["status"])
        program["edges"] = [edge for edge in program["edges"] if edge["from"] != "resolve_target"]
        self.assert_rejected(program, "ProgramMissingDataEdge")
        with self.assertRaises(MagicalProgramAdmissionError) as caught:
            self.admit(self.program, limits=MagicalProgramHostLimits(max_nodes=2))
        self.assertEqual("ProgramNodeLimitExceeded", caught.exception.code)

    def test_irrelevant_presentation_and_names_do_not_select_execution(self):
        program = copy.deepcopy(self.program)
        program["nodes"].reverse()
        program["execution_admission"]["atomic_groups"][0]["node_ids"].reverse()
        program["execution_admission"]["atomic_groups"][0]["group_id"] = "unseen-group"
        program["program_id"] = "program:unseen"
        program = dict(reversed(list(program.items())))
        self.assertEqual("Accepted", self.admit(program)["status"])
        report = self.evaluator.evaluate_program(program)
        self.assertEqual("UnsupportedExecutionAdmission", report["diagnostics"][0]["code"])

    def test_source_filename_is_not_a_group_discriminator(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "not-a-canonical-name.data"
            path.write_text(SOURCE, encoding="utf-8")
            self.assertEqual(self.program, compile_file(path)["program"])

    def test_public_source_and_emitted_program_check_but_never_run(self):
        workflow = UserWorkflow()
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "renamed.mgls"
            program_path = Path(directory) / "renamed.json"
            source_path.write_text(SOURCE, encoding="utf-8")
            program_path.write_text(json.dumps(self.program), encoding="utf-8")
            for path in (source_path, program_path):
                with self.subTest(path=path.name):
                    checked = workflow.execute_path("check", path)
                    self.assertEqual("Accepted", checked["status"])
                    executed = workflow.execute_path("run", path)
                    self.assertEqual("Aborted", executed["status"])
                    trace = executed["result"]["execution"]
                    self.assertEqual("UnsupportedExecutionAdmission", trace["abort"]["code"])
                    self.assertTrue(trace["configuration_unchanged"])
                    self.assertTrue(trace["history_unchanged"])

    def test_group_names_follow_source_identifier_syntax(self):
        result = compile_source(SOURCE.replace("atomic calculate_later", "atomic _later"))
        self.assertEqual("_later", result["program"]["execution_admission"]["atomic_groups"][1]["group_id"])

    def test_unknown_policy_diagnostic_points_to_the_policy(self):
        text = SOURCE.replace("admission Incremental;", "admission Unsafe;")
        diagnostic = check_source(text)["diagnostics"][0]
        span = diagnostic["normalized_span"]
        self.assertEqual("Unsafe", text[span["start"]:span["end"]])
        self.assertEqual("UnsupportedSemanticExtension", diagnostic["code"])

    def test_structure_evidence_maps_only_implemented_rules(self):
        mapping = json.loads((ROOT / "conformance/execution-admission-structure.json").read_text(encoding="utf-8"))
        reference = (ROOT / mapping["owner"]).read_text(encoding="utf-8")
        self.assertFalse(mapping["execution_implemented"])
        self.assertFalse(mapping["released_surface_changed"])
        ids = [rule["id"] for rule in mapping["rules"]]
        self.assertEqual(len(ids), len(set(ids)))
        for rule in mapping["rules"]:
            self.assertIn(rule["id"], reference)
            self.assertTrue(rule["tests"])
            for test in rule["tests"]:
                self.assertTrue(callable(getattr(type(self), test, None)), test)
        self.assertTrue(mapping["outstanding"])

    def test_source_rejects_implicit_mixed_nested_or_empty_groups(self):
        cases = {
            "missing policy": SOURCE.replace("admission Incremental;", ""),
            "unknown policy": SOURCE.replace("admission Incremental;", "admission Unsafe;"),
            "duplicate policy": SOURCE.replace("admission Incremental;", "admission Incremental; admission Incremental;"),
            "ungrouped node": SOURCE.replace("atomic calculate_later {", "").replace(
                "add(first, second);\n}", "add(first, second);"
            ),
            "empty group": SOURCE.replace("atomic calculate_later {", "atomic empty {} atomic calculate_later {"),
            "duplicate group": SOURCE.replace("atomic calculate_later", "atomic bind_and_transition"),
            "nested group": SOURCE.replace("atomic calculate_later {", "atomic outer { atomic calculate_later {").replace(
                "add(first, second);\n}", "add(first, second);\n}}"
            ),
            "value in group": SOURCE.replace("atomic calculate_later {", "atomic calculate_later { let hidden: int = 7;"),
            "late group": SOURCE + "\natomic late { node last: calculate value = add(first, second); }",
        }
        for label, text in cases.items():
            with self.subTest(case=label):
                result = check_source(text)
                self.assertEqual("Rejected", result["status"])
                self.assertIsNone(result["program"])
                self.assertIsNone(result["source_map"])

    def test_evaluate_and_execute_fail_closed_for_both_policies(self):
        for policy in ("Incremental", "WholePlanPreflight"):
            program = copy.deepcopy(self.program)
            program["execution_admission"]["policy"] = policy
            world = program_sandbox_world()
            before = complete_runtime_state(world)
            runtime = MagicalProgramRuntime()
            report = runtime.evaluate(program, world=world)
            self.assertEqual("Infeasible", report["status"])
            self.assertEqual("UnsupportedExecutionAdmission", report["diagnostics"][0]["code"])
            with patch.object(runtime, "commit", side_effect=AssertionError("COMMIT must not run")):
                trace = runtime.execute(program, world)
            self.assertEqual("Aborted", trace["status"])
            self.assertEqual("UnsupportedExecutionAdmission", trace["abort"]["code"])
            self.assertEqual(before, complete_runtime_state(world))
            self.assertEqual(0, runtime._prepare_sequence)
            self.assertEqual("DeterministicAbort", runtime.replay(program, world, trace)["status"])

    def test_prepare_cannot_bypass_denial_with_a_forged_report(self):
        runtime = MagicalProgramRuntime()
        world = program_sandbox_world()
        before = complete_runtime_state(world)
        flat = copy.deepcopy(self.program)
        del flat["execution_admission"]
        report = runtime.evaluate(flat, world=world)
        self.assertEqual("ConditionallyFeasible", report["status"])
        with self.assertRaises(ProgramRuntimeError) as caught:
            runtime.prepare(self.program, report, world)
        self.assertEqual("UnsupportedExecutionAdmission", caught.exception.code)
        self.assertEqual(before, complete_runtime_state(world))

    def test_unchanged_inputs_do_not_gain_groups_and_still_commit(self):
        legacy = compile_file(ROOT / "examples/mgls/independent-transition.mgls")["program"]
        self.assertNotIn("execution_admission", legacy)
        world = program_sandbox_world()
        runtime = MagicalProgramRuntime()
        trace = runtime.execute(legacy, world)
        self.assertEqual("Committed", trace["status"])
        self.assertEqual(1, len(world.history))
        self.assertEqual("transitioned", world.entities["entity:generic:target"]["status"])

    def test_one_explicit_group_is_not_silently_downgraded(self):
        program = copy.deepcopy(self.program)
        program["execution_admission"]["atomic_groups"] = [{
            "group_id": "single", "node_ids": [node["node_id"] for node in program["nodes"]],
        }]
        self.assertEqual("Accepted", self.admit(program)["status"])
        trace = MagicalProgramRuntime().execute(program, program_sandbox_world())
        self.assertEqual("UnsupportedExecutionAdmission", trace["abort"]["code"])


if __name__ == "__main__":
    unittest.main()
