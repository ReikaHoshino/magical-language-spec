from __future__ import annotations

import copy
import json
import unittest

from src.evaluator import LocalEvaluator, format_human, format_json
from src.evaluator.schema import ROOT, validate_feasibility_report


class UnavailableEstimator:
    identity = "estimator-profile:unavailable-test@1"

    def evaluate(self):
        return (
            {
                "total": {
                    "kind": "Unknown",
                    "reason": "ModelDependent",
                    "unit": "J",
                    "dimension": "Energy",
                    "assumption_ids": [],
                    "evidence_ids": [self.identity],
                },
                "components": {},
                "display_unit": "J",
                "accounting_boundary": None,
            },
            [],
            "Timing estimator unavailable.",
        )


class LocalEvaluatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pipeline = json.loads(
            (ROOT / "examples" / "canonical-water-ball" / "pipeline.json").read_text(
                encoding="utf-8"
            )
        )
        cls.canonical_nsr = pipeline["normalization"]["nsr"]

    def setUp(self) -> None:
        self.evaluator = LocalEvaluator()

    def test_canonical_water_ball_reaches_conditional_report_without_commit(self) -> None:
        original = copy.deepcopy(self.canonical_nsr)
        report = self.evaluator.evaluate_nsr(self.canonical_nsr)

        self.assertEqual(self.canonical_nsr, original)
        self.assertEqual(report["status"], "ConditionallyFeasible")
        validate_feasibility_report(report)

        interpretations = report["interpretations"]
        self.assertIn("semantic_ast", interpretations)
        self.assertIn("typed_mir", interpretations)
        self.assertIn("kernel_plan", interpretations)
        self.assertEqual(
            interpretations["kernel_plan"]["source_plan_id"],
            "wb:plan:transfer-reconfigure",
        )
        self.assertEqual(
            interpretations["kernel_plan"]["operations"],
            ["RESOLVE", "OBSERVE", "CHANNEL", "TRANSFER", "RECONFIGURE", "CONSTRAIN"],
        )
        self.assertNotIn("COMMIT", interpretations["kernel_plan"]["operations"])
        self.assertEqual(report["energy"]["total"]["value"], 200)

        terminal = interpretations["typed_mir"]["terminal"]["source_value"]
        self.assertEqual(terminal["kind"], "Unknown")
        self.assertEqual(terminal["reason"], "MissingArgument")
        self.assertEqual(
            report["assumptions"][0]["id"],
            "assumption:terminal:50m-debug",
        )
        self.assertEqual(report["assumptions"][0]["source_value"]["kind"], "Unknown")
        self.assertEqual(report["assumptions"][0]["selected_value"]["value"], 50)
        self.assertEqual(report["assumptions"][0]["binding"]["binding_point"], "PREPARE")
        control = report["energy"]["components"]["control"]
        self.assertEqual(control["kind"], "Exact")
        self.assertGreater(control["value"], 0)
        trajectory_control = next(
            item for item in report["assessments"] if item["dimension"] == "trajectory_control"
        )
        self.assertEqual(trajectory_control["status"], "Pass")

    def test_canonical_explicit_constraints_are_preserved(self) -> None:
        report = self.evaluator.evaluate_nsr(self.canonical_nsr)
        constraints = report["interpretations"]["typed_mir"]["typed_constraints"]
        self.assertEqual(constraints["mass"]["value"], 50)
        self.assertEqual(constraints["radius"]["value"], 0.01)
        self.assertEqual(constraints["distance"]["value"], 3)
        self.assertEqual(constraints["initial_velocity"]["value"], 0)
        self.assertEqual(constraints["acceleration"]["value"], 50)
        self.assertEqual(constraints["trajectory"], "horizontal-forward")

    def test_dimension_error_fails_before_planning(self) -> None:
        nsr = copy.deepcopy(self.canonical_nsr)
        nsr.pop("semantic_fingerprint", None)
        acceleration = next(role for role in nsr["roles"] if role["role"] == "Quantity")
        acceleration["value"]["value"]["dimension"] = {
            "kg": 0,
            "m": 1,
            "s": 0,
            "A": 0,
            "K": 0,
            "mol": 0,
            "cd": 0,
        }

        report = self.evaluator.evaluate_nsr(nsr)
        self.assertEqual(report["status"], "Infeasible")
        self.assertIn("DimensionError", {item["code"] for item in report["diagnostics"]})
        self.assertNotIn("kernel_plan", report["interpretations"])

    def test_type_error_fails_closed(self) -> None:
        nsr = copy.deepcopy(self.canonical_nsr)
        nsr.pop("semantic_fingerprint", None)
        patient = next(role for role in nsr["roles"] if role["role"] == "Patient")
        patient["value"]["semantic_kind"] = "Time"

        report = self.evaluator.evaluate_nsr(nsr)
        self.assertEqual(report["status"], "Infeasible")
        self.assertIn("TypeError", {item["code"] for item in report["diagnostics"]})

    def test_semantic_fingerprint_mismatch_fails_closed(self) -> None:
        nsr = copy.deepcopy(self.canonical_nsr)
        nsr["semantic_fingerprint"] = "sf:v1:sha256:" + ("0" * 64)

        report = self.evaluator.evaluate_nsr(nsr)
        self.assertEqual(report["status"], "Infeasible")
        self.assertIn(
            "SemanticFingerprintMismatch",
            {item["code"] for item in report["diagnostics"]},
        )

    def test_reference_latin_source_enters_same_evaluator_pipeline(self) -> None:
        report = self.evaluator.evaluate_latin_source(
            "Calorem ab aqua ad aerem transfer."
        )
        self.assertEqual(report["input"]["kind"], "NaturalLanguageSource")
        self.assertEqual(report["provenance"]["adapter_id"], "lat")
        self.assertEqual(report["status"], "Indeterminate")
        self.assertEqual(
            report["interpretations"]["nsr"]["semantic_fingerprint"],
            report["provenance"]["semantic_fingerprint"],
        )
        self.assertIn("semantic_ast", report["interpretations"])
        self.assertIn("typed_mir", report["interpretations"])
        self.assertIn("kernel_plan", report["interpretations"])
        self.assertTrue(
            set(report["interpretations"]["kernel_plan"]["operations"])
            <= {"RESOLVE", "OBSERVE", "CHANNEL", "TRANSFER", "RECONFIGURE", "CONSTRAIN"}
        )
        self.assertNotIn("COMMIT", report["interpretations"]["kernel_plan"]["operations"])
        self.assertEqual(report["energy"]["total"]["kind"], "Unknown")
        self.assertIn("ResolutionFailure", {item["code"] for item in report["diagnostics"]})
        validate_feasibility_report(report)

    def test_invalid_latin_source_reports_frontend_failure(self) -> None:
        report = self.evaluator.evaluate_latin_source("Verbum ignotum.")
        self.assertEqual(report["status"], "Infeasible")
        codes = {item["code"] for item in report["diagnostics"]}
        self.assertIn("LexiconEntryMissing", codes)
        self.assertIn("NormalizationFailed", codes)

    def test_invalid_nsr_json_becomes_schema_valid_failure_report(self) -> None:
        report = self.evaluator.evaluate_nsr_json("{not json")
        self.assertEqual(report["status"], "Infeasible")
        self.assertEqual(report["diagnostics"][0]["code"], "InvalidJSON")
        validate_feasibility_report(report)

    def test_schema_invalid_nsr_does_not_enter_internal_stages(self) -> None:
        report = self.evaluator.evaluate_nsr({"schema_version": "0.7.3", "kind": "X"})
        self.assertEqual(report["status"], "Infeasible")
        self.assertNotIn("interpretations", report)
        self.assertIn("NSRSchemaViolation", {item["code"] for item in report["diagnostics"]})

    def test_noncanonical_generation_subset_is_indeterminate_not_invented(self) -> None:
        nsr = copy.deepcopy(self.canonical_nsr)
        nsr.pop("semantic_fingerprint", None)
        patient = next(role for role in nsr["roles"] if role["role"] == "Patient")
        patient["value"]["value"]["mass"]["value"] = 49

        report = self.evaluator.evaluate_nsr(nsr)
        self.assertEqual(report["status"], "Indeterminate")
        self.assertIn(
            "UnsupportedSemanticSubset",
            {item["code"] for item in report["diagnostics"]},
        )
        self.assertNotIn("kernel_plan", report["interpretations"])

    def test_acceleration_semantic_type_and_dimension_are_both_checked(self) -> None:
        nsr = copy.deepcopy(self.canonical_nsr)
        nsr.pop("semantic_fingerprint", None)
        acceleration = next(role for role in nsr["roles"] if role["role"] == "Quantity")
        acceleration["value"]["value"]["semantic_type"] = "Length"
        acceleration["value"]["value"]["dimension"] = {
            "kg": 0,
            "m": 1,
            "s": 0,
            "A": 0,
            "K": 0,
            "mol": 0,
            "cd": 0,
        }

        report = self.evaluator.evaluate_nsr(nsr)
        self.assertEqual(report["status"], "Infeasible")
        codes = {item["code"] for item in report["diagnostics"]}
        self.assertIn("TypeError", codes)
        self.assertIn("DimensionError", codes)

    def test_interactive_latin_ambiguity_stays_pending(self) -> None:
        report = self.evaluator.evaluate_latin_source(
            "aquae",
            ambiguity_policy="InteractiveResolve",
        )
        self.assertEqual(report["status"], "Indeterminate")
        self.assertIn(
            "AmbiguityInteractionRequired",
            {item["code"] for item in report["diagnostics"]},
        )
        self.assertNotIn("nsr", report["interpretations"])

    def test_invalid_utf8_latin_source_is_rejected(self) -> None:
        report = self.evaluator.evaluate_latin_source(b"\xff")
        self.assertEqual(report["status"], "Infeasible")
        self.assertIn("InvalidUTF8", {item["code"] for item in report["diagnostics"]})

    def test_must_resolve_terminal_cannot_be_planning_assumption(self) -> None:
        self.evaluator.water_ball["typed_mir"]["terminal"]["criticality"] = "MustResolve"
        report = self.evaluator.evaluate_nsr(self.canonical_nsr)
        self.assertEqual(report["status"], "Infeasible")
        self.assertIn("InferenceForbidden", {item["code"] for item in report["diagnostics"]})

    def test_unavailable_required_estimator_is_indeterminate_not_zero(self) -> None:
        evaluator = LocalEvaluator(estimator=UnavailableEstimator())
        report = evaluator.evaluate_nsr(self.canonical_nsr)
        self.assertEqual(report["status"], "Indeterminate")
        self.assertEqual(report["energy"]["total"]["kind"], "Unknown")
        self.assertIn(
            "EstimatorModelUnavailable",
            {item["code"] for item in report["diagnostics"]},
        )

    def test_explicit_authority_failure_is_infeasible(self) -> None:
        for candidate in self.evaluator.water_ball["planning"]["candidate_plans"]:
            for obligation in candidate["mandatory_obligations"]:
                if obligation["kind"] == "Authority":
                    obligation["status"] = "Failed"
        report = self.evaluator.evaluate_nsr(self.canonical_nsr)
        self.assertEqual(report["status"], "Infeasible")
        self.assertIn("AuthorityError", {item["code"] for item in report["diagnostics"]})

    def test_explicit_conservation_failure_is_infeasible(self) -> None:
        for candidate in self.evaluator.water_ball["planning"]["candidate_plans"]:
            for obligation in candidate["mandatory_obligations"]:
                if obligation["kind"] == "Conservation":
                    obligation["status"] = "Failed"
        report = self.evaluator.evaluate_nsr(self.canonical_nsr)
        self.assertEqual(report["status"], "Infeasible")
        self.assertIn(
            "ConservationProofFailure",
            {item["code"] for item in report["diagnostics"]},
        )

    def test_plan_selection_uses_minimum_energy_only_after_eligibility(self) -> None:
        candidates = self.evaluator.water_ball["planning"]["candidate_plans"]
        candidates[0]["estimated_total_energy"]["value"]["value"] = 300
        report = self.evaluator.evaluate_nsr(self.canonical_nsr)
        self.assertEqual(
            report["interpretations"]["kernel_plan"]["source_plan_id"],
            "wb:plan:assemble-alternative",
        )

    def test_non_mki_operation_cannot_enter_kernel_plan(self) -> None:
        for candidate in self.evaluator.water_ball["planning"]["candidate_plans"]:
            candidate["operations"].append("COMMIT")
        report = self.evaluator.evaluate_nsr(self.canonical_nsr)
        self.assertEqual(report["status"], "Infeasible")
        self.assertIn(
            "InvalidMKIPrimitive",
            {item["code"] for item in report["diagnostics"]},
        )
        self.assertNotIn("kernel_plan", report["interpretations"])

    def test_formatters_are_deterministic_and_stage_selectable(self) -> None:
        report = self.evaluator.evaluate_nsr(self.canonical_nsr)
        machine_a = format_json(report, level="all")
        machine_b = format_json(report, level="all")
        self.assertEqual(machine_a, machine_b)
        self.assertEqual(json.loads(machine_a)["status"], "ConditionallyFeasible")

        human = format_human(report, level="report")
        self.assertIn("Status: ConditionallyFeasible", human)
        self.assertIn("Energy: 200 J", human)

        kernel = json.loads(format_json(report, level="kernel-plan"))
        self.assertEqual(kernel["source_plan_id"], "wb:plan:transfer-reconfigure")

    def test_internal_stage_ingress_is_not_public_api(self) -> None:
        self.assertFalse(hasattr(self.evaluator, "evaluate_semantic_ast"))
        self.assertFalse(hasattr(self.evaluator, "evaluate_typed_mir"))
        self.assertFalse(hasattr(self.evaluator, "evaluate_normalized_ir"))
        self.assertFalse(hasattr(self.evaluator, "commit"))


if __name__ == "__main__":
    unittest.main()
