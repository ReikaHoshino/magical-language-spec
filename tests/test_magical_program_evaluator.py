from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from src.evaluator.magical_program import (
    MKI_OPERATIONS,
    WORLD_KERNEL_CLASSES,
    MagicalProgramEvaluator,
    ProgramContractRegistration,
    ProgramContractRegistry,
)
from src.evaluator.schema import validate_feasibility_report

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "magical-program"
MP_PATH = EXAMPLES / "MP-001.json"
OBSERVE_PATH = EXAMPLES / "MP-OBSERVE-001.json"
PURE_PATH = EXAMPLES / "MP-PURE-001.json"
MANIFEST_PATH = ROOT / "conformance" / "manifest.json"
SOURCE_PATHS = (
    ROOT / "src" / "evaluator" / "magical_program.py",
    ROOT / "src" / "evaluator" / "magical_program_contracts.py",
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def first_code(report):
    diagnostics = report.get("diagnostics", [])
    return None if not diagnostics else diagnostics[0]["code"]


class MagicalProgramEvaluatorTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.evaluator = MagicalProgramEvaluator()
        self.effect = load(MP_PATH)
        self.observe = load(OBSERVE_PATH)
        self.pure = load(PURE_PATH)

    def test_effect_program_is_conditional_and_resolution_is_first_class(self) -> None:
        world = {
            "revision": "world:test:1",
            "entities": {"entity:untouched": {"state": "same"}},
        }
        history = [{"event_id": "event:existing"}]
        before_world = copy.deepcopy(world)
        before_history = copy.deepcopy(history)
        report = self.evaluator.evaluate_program(
            self.effect, world_state=world, history=history
        )
        validate_feasibility_report(report)
        self.assertEqual("ConditionallyFeasible", report["status"])
        self.assertEqual(before_world, world)
        self.assertEqual(before_history, history)

        typed_nodes = report["interpretations"]["typed_mir"]["nodes"]
        resolve = next(item for item in typed_nodes if item["node_id"] == "resolve_target")
        invoke = next(item for item in typed_nodes if item["node_id"] == "invoke_transition")
        self.assertEqual("reference", resolve["output_types"][0])
        self.assertEqual("reference", invoke["input_types"][0])
        self.assertFalse(resolve["evaluated_outputs"][0]["authority_granted"])

        kernel = report["interpretations"]["kernel_plan"]
        self.assertEqual(["RECONFIGURE", "RESOLVE"], kernel["mki_operations"])
        self.assertEqual(["QUERY", "TRANSITION"], kernel["world_kernel_classes"])
        effect = next(
            item for item in kernel["effect_nodes"] if item.get("contract")
        )
        obligations = effect["obligations"]
        self.assertFalse(obligations["authority_granted"])
        self.assertFalse(obligations["resources_reserved"])
        self.assertFalse(obligations["host_records_bound"])
        self.assertTrue(obligations["requires_runtime_revalidation"])
        declared = obligations["declared_requirements"]
        self.assertEqual("target_ref", declared["capabilities"][0]["target_binding"])
        self.assertNotIn(
            "capability:host:", json.dumps(declared, sort_keys=True)
        )

    def test_observation_requires_one_declared_history_event(self) -> None:
        valid = self.evaluator.evaluate_program(self.observe)
        self.assertEqual("ConditionallyFeasible", valid["status"])
        effect = next(
            item
            for item in valid["interpretations"]["kernel_plan"]["effect_nodes"]
            if item.get("contract")
        )
        self.assertEqual(
            1, effect["obligations"]["contract_minimum_resources"]["events"]
        )

        insufficient = copy.deepcopy(self.observe)
        insufficient["nodes"][1]["obligations"]["resources"]["events"] = 0
        report = self.evaluator.evaluate_program(insufficient)
        self.assertEqual("Infeasible", report["status"])
        self.assertEqual("ProgramResourceDeclarationInsufficient", first_code(report))

    def test_pure_program_is_feasible_and_immutable(self) -> None:
        report = self.evaluator.evaluate_program(self.pure)
        validate_feasibility_report(report)
        self.assertEqual("Feasible", report["status"])
        outputs = report["interpretations"]["typed_mir"]["outputs"]
        self.assertEqual(5.0, outputs["total"]["value"])
        self.assertEqual("quantity", outputs["total"]["type_signature"])
        self.assertIs(True, outputs["allowed"]["value"])
        kernel = report["interpretations"]["kernel_plan"]
        self.assertEqual([], kernel["mki_operations"])
        self.assertEqual([], kernel["effect_nodes"])
        self.assertFalse(kernel["prepared"])
        self.assertFalse(kernel["committed"])

    def test_type_dimension_unit_and_operator_errors_have_locations(self) -> None:
        mutations = (
            (
                "ProgramTypeMismatch",
                lambda program: program["values"][1].__setitem__(
                    "semantic_type", "Time"
                ),
            ),
            (
                "ProgramDimensionMismatch",
                lambda program: program["values"][1].__setitem__(
                    "dimension", "T1"
                ),
            ),
            (
                "ProgramUnitMismatch",
                lambda program: program["values"][1].__setitem__("unit", "cm"),
            ),
            (
                "ProgramOperatorMismatch",
                lambda program: program["nodes"][0].__setitem__(
                    "operator", "less_equal"
                ),
            ),
        )
        for expected, mutate in mutations:
            with self.subTest(expected=expected):
                program = copy.deepcopy(self.pure)
                mutate(program)
                report = self.evaluator.evaluate_program(program)
                self.assertEqual("Infeasible", report["status"])
                self.assertEqual(expected, first_code(report))
                location = report["diagnostics"][0]["program_location"]
                self.assertEqual("sum", location["node_id"])
                self.assertEqual(0, location["order"])

    def test_unknown_and_mismatched_contracts_fail_closed(self) -> None:
        unknown = copy.deepcopy(self.effect)
        unknown["nodes"][1]["contract"]["contract_id"] = "unknown.transition"
        report = self.evaluator.evaluate_program(unknown)
        self.assertEqual("Infeasible", report["status"])
        self.assertEqual("ProgramUnknownContract", first_code(report))

        mismatched_registry = ProgramContractRegistry(
            (
                ProgramContractRegistration(
                    contract_id="generic.transition",
                    revision="1",
                    instruction="evidence.observe",
                    input_kinds=("reference", "literal:string"),
                    output_kind="evidence",
                    required_obligation_categories=("capabilities",),
                    minimum_energy_j=0,
                    minimum_matter_kg=0,
                    minimum_events=1,
                    mki_operations=("OBSERVE",),
                    world_kernel_classes=("SAMPLE",),
                ),
            )
        )
        report = MagicalProgramEvaluator(
            contracts=mismatched_registry
        ).evaluate_program(self.effect)
        self.assertEqual("Infeasible", report["status"])
        self.assertEqual("ProgramContractInstructionMismatch", first_code(report))

    def test_portable_obligations_are_monotonic_not_authorizing(self) -> None:
        missing = copy.deepcopy(self.effect)
        missing["nodes"][1]["obligations"]["capabilities"] = []
        report = self.evaluator.evaluate_program(missing)
        self.assertEqual("Infeasible", report["status"])
        self.assertEqual("ProgramObligationMissing", first_code(report))

        wrong_target_type = copy.deepcopy(self.effect)
        wrong_target_type["nodes"][1]["inputs"][0] = "target_selector"
        wrong_target_type["edges"] = []
        for category in ("capabilities", "leases", "identities", "accounting"):
            for requirement in wrong_target_type["nodes"][1]["obligations"][category]:
                if "target_binding" in requirement:
                    requirement["target_binding"] = "target_selector"
        report = self.evaluator.evaluate_program(wrong_target_type)
        self.assertEqual("Infeasible", report["status"])
        self.assertEqual("ProgramContractInputMismatch", first_code(report))

    def test_output_declaration_must_match_binding_semantics(self) -> None:
        forged = copy.deepcopy(self.pure)
        forged["outputs"][0]["kind"] = "event"
        report = self.evaluator.evaluate_program(forged)
        self.assertEqual("Infeasible", report["status"])
        self.assertEqual("ProgramOutputKindMismatch", first_code(report))

    def test_compatibility_and_host_limits_fail_before_runtime(self) -> None:
        mismatched = copy.deepcopy(self.effect)
        mismatched["compatibility"]["profile_revision"] = "2"
        report = self.evaluator.evaluate_program(mismatched)
        self.assertEqual("Infeasible", report["status"])
        self.assertEqual("ProgramCompatibilityMismatch", first_code(report))

        excessive = copy.deepcopy(self.effect)
        excessive["budget"]["energy_j"] = 1_000_000_001
        report = self.evaluator.evaluate_program(excessive)
        self.assertEqual("Infeasible", report["status"])
        self.assertEqual("ProgramEnergyLimitExceeded", first_code(report))
        self.assertFalse(report["interpretations"]["kernel_plan"])

    def test_renaming_filename_and_program_id_does_not_dispatch(self) -> None:
        original = self.evaluator.evaluate_bytes(MP_PATH.read_bytes())
        renamed = copy.deepcopy(self.effect)
        renamed["program_id"] = "program:renamed-arbitrary:999"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "SA-NOT-A-DISPATCH-NAME.data"
            path.write_text(json.dumps(renamed), encoding="utf-8")
            observed = self.evaluator.evaluate_bytes(path.read_bytes())
        self.assertEqual(original["status"], observed["status"])
        self.assertEqual(
            original["interpretations"]["kernel_plan"],
            observed["interpretations"]["kernel_plan"],
        )
        self.assertNotEqual(
            original["input"]["program_id"], observed["input"]["program_id"]
        )

    def test_lowering_cannot_introduce_new_mki_or_kernel_classes(self) -> None:
        self.assertEqual(
            {"RESOLVE", "OBSERVE", "CHANNEL", "TRANSFER", "RECONFIGURE", "CONSTRAIN"},
            set(MKI_OPERATIONS),
        )
        self.assertEqual(
            {"QUERY", "SAMPLE", "TRANSITION", "ACTIVATE", "DEACTIVATE"},
            set(WORLD_KERNEL_CLASSES),
        )
        with self.assertRaises(ValueError):
            ProgramContractRegistration(
                "bad",
                "1",
                "effect.invoke",
                (),
                "effect_result",
                (),
                0,
                0,
                0,
                ("SET",),
                ("TRANSITION",),
            )
        with self.assertRaises(ValueError):
            ProgramContractRegistration(
                "bad-kernel",
                "1",
                "effect.invoke",
                (),
                "effect_result",
                (),
                0,
                0,
                0,
                ("RECONFIGURE",),
                ("RAW_WRITE",),
            )

    def test_source_has_no_fixture_dispatch_or_legacy_payload_path(self) -> None:
        source = "\n".join(path.read_text(encoding="utf-8") for path in SOURCE_PATHS)
        for forbidden in (
            "SUCCESS-ARCANA",
            "SA-001",
            "SA-002",
            "SA-003",
            "DEBUG-HELL",
            "embedded_payload",
            "shadow.spell-instance",
        ):
            self.assertNotIn(forbidden, source)
        self.assertNotIn("filename", source.lower())
        self.assertNotIn("display_name", source)

    def test_stable_conformance_manifest_is_unchanged(self) -> None:
        manifest = load(MANIFEST_PATH)
        self.assertEqual("0.12.0", manifest["suite"]["suite_version"])
        self.assertEqual("v0.12.0", manifest["suite"]["release_target"])
        self.assertEqual(
            ["Core-1.0", "Evaluator-1.0", "Adapter-lat-1.0", "Runtime-1.0"],
            [item["class_id"] for item in manifest["classes"]],
        )
        self.assertEqual(
            65,
            sum(len(item["required_case_ids"]) for item in manifest["classes"]),
        )


if __name__ == "__main__":
    unittest.main()
