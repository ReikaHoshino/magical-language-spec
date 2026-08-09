from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from src.artifacts.magical_program import (
    MagicalProgramAdmissionError,
    MagicalProgramHostLimits,
    admit_program,
    admit_program_bytes,
    decode_program,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "magical-program.schema.json"
EXAMPLE_ROOT = ROOT / "examples" / "magical-program"
MP_PATH = EXAMPLE_ROOT / "MP-001.json"
OBSERVE_PATH = EXAMPLE_ROOT / "MP-OBSERVE-001.json"
PURE_PATH = EXAMPLE_ROOT / "MP-PURE-001.json"
INVALID_MATRIX_PATH = EXAMPLE_ROOT / "invalid" / "structural-cases.json"
MALFORMED_PATH = EXAMPLE_ROOT / "invalid" / "MALFORMED.json.txt"
REFERENCE_PATH = ROOT / "reference" / "magical-program-artifact.md"
MANIFEST_PATH = ROOT / "conformance" / "manifest.json"
REGISTERED = {("generic.transition", "1"), ("generic.observe", "1")}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def pointer_tokens(pointer: str) -> list[str]:
    if not pointer.startswith("/"):
        raise ValueError(pointer)
    return [
        token.replace("~1", "/").replace("~0", "~")
        for token in pointer[1:].split("/")
    ]


def apply_case(document, case):
    mutated = copy.deepcopy(document)
    tokens = pointer_tokens(case["pointer"])
    parent = mutated
    for token in tokens[:-1]:
        parent = parent[int(token)] if isinstance(parent, list) else parent[token]
    final = tokens[-1]
    if case["operation"] in {"replace", "add"}:
        if isinstance(parent, list):
            parent[int(final)] = copy.deepcopy(case["value"])
        else:
            parent[final] = copy.deepcopy(case["value"])
    elif case["operation"] == "remove":
        if isinstance(parent, list):
            del parent[int(final)]
        else:
            del parent[final]
    else:
        raise AssertionError(case["operation"])
    return mutated


class MagicalProgramContractTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load(SCHEMA_PATH)
        cls.program = load(MP_PATH)
        cls.observe = load(OBSERVE_PATH)
        cls.pure = load(PURE_PATH)
        Draft202012Validator.check_schema(cls.schema)

    def admit(
        self,
        document,
        *,
        limits=MagicalProgramHostLimits(),
        registered=REGISTERED,
    ):
        return admit_program(
            document,
            schema=self.schema,
            registered_contracts=registered,
            encoded_size=len(json.dumps(document).encode("utf-8")),
            limits=limits,
        )

    def assert_diagnostic(
        self,
        document,
        code,
        *,
        limits=MagicalProgramHostLimits(),
        registered=REGISTERED,
    ):
        with self.assertRaises(MagicalProgramAdmissionError) as caught:
            self.admit(document, limits=limits, registered=registered)
        self.assertEqual(code, caught.exception.code, caught.exception.diagnostic())

    def test_positive_examples_are_portable_and_explicitly_resolved(self) -> None:
        validator = Draft202012Validator(self.schema)
        for document in (self.program, self.observe, self.pure):
            validator.validate(document)
            self.assertEqual("Accepted", self.admit(document)["status"])

        self.assertEqual(
            ["resolve_target", "invoke_transition"],
            self.admit(self.program)["deterministic_node_order"],
        )
        self.assertEqual(
            ["resolve_target", "observe_target"],
            self.admit(self.observe)["deterministic_node_order"],
        )
        self.assertEqual(
            ["sum", "within_limit", "require_limit"],
            self.admit(self.pure)["deterministic_node_order"],
        )
        for document in (self.program, self.observe):
            self.assertEqual("ref.resolve", document["nodes"][0]["instruction"])
            self.assertEqual(
                document["nodes"][0]["produces"][0],
                document["nodes"][1]["inputs"][0],
            )

    def test_programs_declare_requirements_not_host_record_ids(self) -> None:
        for document in (self.program, self.observe):
            text = json.dumps(document, sort_keys=True)
            for prefix in (
                "capability:host:",
                "lease:host:",
                "identity:host:",
                "evidence:host:",
                "ledger:host:",
            ):
                self.assertNotIn(prefix, text)
            obligations = document["nodes"][1]["obligations"]
            self.assertTrue(obligations["capabilities"])
            self.assertTrue(obligations["identities"])
            for category in (
                "capabilities",
                "leases",
                "identities",
                "evidence",
                "accounting",
            ):
                for requirement in obligations[category]:
                    self.assertIn("requirement_id", requirement)
                    if "target_binding" in requirement:
                        self.assertEqual(
                            document["nodes"][1]["inputs"][0],
                            requirement["target_binding"],
                        )

        forged = copy.deepcopy(self.program)
        forged["nodes"][1]["obligations"]["capabilities"] = [
            "capability:forged"
        ]
        self.assert_diagnostic(forged, "ProgramSchemaViolation")

    def test_requirement_target_must_be_an_input_of_the_effect_node(self) -> None:
        wrong = copy.deepcopy(self.program)
        wrong["nodes"][1]["obligations"]["capabilities"][0][
            "target_binding"
        ] = "target_selector"
        self.assert_diagnostic(wrong, "ProgramRequirementTargetNotInput")

        duplicate = copy.deepcopy(self.program)
        duplicate["nodes"][1]["obligations"]["identities"][0][
            "requirement_id"
        ] = "capability.transition"
        self.assert_diagnostic(duplicate, "ProgramDuplicateRequirement")

    def test_state_write_dynamic_code_and_opaque_legacy_tunnelling_are_inexpressible(self) -> None:
        unknown_instruction = copy.deepcopy(self.program)
        unknown_instruction["nodes"][1]["instruction"] = "state.set"
        self.assert_diagnostic(unknown_instruction, "ProgramSchemaViolation")

        raw_path = copy.deepcopy(self.program)
        raw_path["nodes"][1]["state_path"] = "/Sigma/entities/target/raw"
        self.assert_diagnostic(raw_path, "ProgramSchemaViolation")

        payload = copy.deepcopy(self.program)
        payload["embedded_payload"] = "base64:legacy"
        self.assert_diagnostic(payload, "ProgramSchemaViolation")

        schema_text = SCHEMA_PATH.read_text(encoding="utf-8")
        for forbidden in (
            '"state.set"',
            '"SET"',
            "embedded_payload",
            "shadow.spell-instance",
            "base64",
            "python_module",
        ):
            self.assertNotIn(forbidden, schema_text)

    def test_effect_nodes_require_registered_contract_and_obligations(self) -> None:
        missing = copy.deepcopy(self.program)
        del missing["nodes"][1]["obligations"]
        self.assert_diagnostic(missing, "ProgramSchemaViolation")

        unknown = copy.deepcopy(self.program)
        unknown["nodes"][1]["contract"] = {
            "contract_id": "unknown.transition",
            "revision": "1",
        }
        self.assert_diagnostic(unknown, "ProgramUnknownContract")
        self.assert_diagnostic(self.program, "ProgramUnknownContract", registered=set())

    def test_deterministic_order_and_explicit_edges(self) -> None:
        reordered = copy.deepcopy(self.pure)
        reordered["nodes"] = list(reversed(reordered["nodes"]))
        self.assertEqual(
            ["sum", "within_limit", "require_limit"],
            self.admit(reordered)["deterministic_node_order"],
        )

        duplicate = copy.deepcopy(self.program)
        duplicate["nodes"][1]["order"] = 0
        self.assert_diagnostic(duplicate, "ProgramDuplicateOrder")

        backward = copy.deepcopy(self.program)
        backward["edges"][0] = {
            "from": "invoke_transition",
            "to": "resolve_target",
        }
        self.assert_diagnostic(backward, "ProgramOrderViolation")

        missing_edge = copy.deepcopy(self.program)
        missing_edge["edges"] = []
        self.assert_diagnostic(missing_edge, "ProgramMissingDataEdge")

    def test_bindings_have_one_producer_and_outputs_are_existing_bindings(self) -> None:
        duplicate = copy.deepcopy(self.program)
        duplicate["nodes"][0]["produces"] = ["target_selector"]
        self.assert_diagnostic(duplicate, "ProgramDuplicateBinding")

        unknown_input = copy.deepcopy(self.program)
        unknown_input["nodes"][1]["inputs"][0] = "not_defined"
        self.assert_diagnostic(unknown_input, "ProgramUnknownBinding")

        unknown_output = copy.deepcopy(self.program)
        unknown_output["outputs"][0]["binding"] = "not_defined"
        self.assert_diagnostic(unknown_output, "ProgramOutputUnknownBinding")

    def test_every_host_ceiling_fails_before_prepare(self) -> None:
        cases = [
            (self.program, MagicalProgramHostLimits(max_nodes=1), "ProgramNodeLimitExceeded"),
            (self.program, MagicalProgramHostLimits(max_edges=0), "ProgramEdgeLimitExceeded"),
            (self.program, MagicalProgramHostLimits(max_depth=1), "ProgramDepthLimitExceeded"),
            (self.pure, MagicalProgramHostLimits(max_values=2), "ProgramValueLimitExceeded"),
            (self.pure, MagicalProgramHostLimits(max_outputs=1), "ProgramOutputLimitExceeded"),
            (self.program, MagicalProgramHostLimits(max_energy_j=9), "ProgramEnergyLimitExceeded"),
            (self.program, MagicalProgramHostLimits(max_events=0), "ProgramEventLimitExceeded"),
            (self.program, MagicalProgramHostLimits(max_microsteps=7), "ProgramMicrostepLimitExceeded"),
        ]
        for document, limits, code in cases:
            with self.subTest(code=code):
                self.assert_diagnostic(document, code, limits=limits)

        payload = MP_PATH.read_bytes()
        with self.assertRaises(MagicalProgramAdmissionError) as caught:
            admit_program_bytes(
                payload,
                schema=self.schema,
                registered_contracts=REGISTERED,
                limits=MagicalProgramHostLimits(max_bytes=len(payload) - 1),
            )
        self.assertEqual("ProgramByteLimitExceeded", caught.exception.code)

    def test_strict_decode_and_invalid_fixture_matrix(self) -> None:
        with self.assertRaises(MagicalProgramAdmissionError) as malformed:
            decode_program(MALFORMED_PATH.read_bytes())
        self.assertEqual("ProgramJsonMalformed", malformed.exception.code)

        with self.assertRaises(MagicalProgramAdmissionError) as duplicated:
            decode_program(b'{"artifact_kind":"MagicalProgram","artifact_kind":"Other"}')
        self.assertEqual("ProgramDuplicateJsonProperty", duplicated.exception.code)

        fixture = load(INVALID_MATRIX_PATH)
        base = load(ROOT / fixture["base"])
        seen: set[str] = set()
        for case in fixture["cases"]:
            with self.subTest(case=case["case_id"]):
                self.assertNotIn(case["case_id"], seen)
                seen.add(case["case_id"])
                self.assert_diagnostic(
                    apply_case(base, case), case["expected_diagnostic"]
                )

    def test_provenance_and_stable_surface_remain_separate(self) -> None:
        fabricated = copy.deepcopy(self.program)
        fabricated["provenance"]["source"] = {
            "artifact_kind": "SurfaceSource",
            "artifact_version": "0",
            "artifact_id": "fabricated:source",
            "stage": "source",
        }
        self.assert_diagnostic(fabricated, "ProgramSchemaViolation")

        manifest = load(MANIFEST_PATH)
        self.assertEqual("0.12.0", manifest["suite"]["suite_version"])
        self.assertEqual("v0.12.0", manifest["suite"]["release_target"])
        self.assertEqual(
            65,
            sum(len(item["required_case_ids"]) for item in manifest["classes"]),
        )

        text = REFERENCE_PATH.read_text(encoding="utf-8")
        self.assertIn("portable requirement", text)
        self.assertIn("runtime-local PreparedPlan", text)


if __name__ == "__main__":
    unittest.main()
