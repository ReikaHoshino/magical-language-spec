from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from tools.semantic_fingerprint import semantic_fingerprint_v1


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
FIXTURES = ROOT / "examples" / "canonical-water-ball"
REFERENCE = ROOT / "reference" / "canonical-water-ball.md"

STAGE_ORDER = [
    "NaturalLanguageSource",
    "SourceNormalization",
    "NormalizationCandidateSet",
    "NSR",
    "SemanticAST",
    "TypedMIR",
    "ResolutionAndRegistryInputs",
    "KernelPlan",
    "FeasibilityAndPrepare",
    "RuntimeScheduleAndCommit",
    "WorldStateAndHistory",
]
MKI_PRIMITIVES = {
    "RESOLVE", "OBSERVE", "CHANNEL", "TRANSFER", "RECONFIGURE", "CONSTRAIN"
}
MANDATORY = {"Type", "Identity", "Conservation", "Authority", "Lease"}
FAILURE_CATEGORIES = {
    "ParseNormalization", "Ambiguity", "Type", "Dimension", "Resolution",
    "AuthorityLease", "Conservation", "EstimatorUnavailable",
    "MustResolveInference", "SourceFidelity", "PlanSelection", "Binding",
    "RuntimeRevalidation",
}
TEST_IDS = {f"WB-TEST-{index:03d}" for index in range(1, 12)}
EXPECTED_TYPED_VALUES = {
    "mass": ("Mass", {"kg": 1, "m": 0, "s": 0, "A": 0, "K": 0, "mol": 0, "cd": 0}, 50),
    "radius": ("Length", {"kg": 0, "m": 1, "s": 0, "A": 0, "K": 0, "mol": 0, "cd": 0}, 0.01),
    "distance": ("Length", {"kg": 0, "m": 1, "s": 0, "A": 0, "K": 0, "mol": 0, "cd": 0}, 3),
    "initial_velocity": ("Velocity", {"kg": 0, "m": 1, "s": -1, "A": 0, "K": 0, "mol": 0, "cd": 0}, 0),
    "acceleration": ("Acceleration", {"kg": 0, "m": 1, "s": -2, "A": 0, "K": 0, "mol": 0, "cd": 0}, 50),
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validator(schema_name: str) -> Draft202012Validator:
    schema = load(SCHEMAS / schema_name)
    registry = Registry()
    for path in SCHEMAS.glob("*.schema.json"):
        document = load(path)
        registry = registry.with_resource(
            document["$id"], Resource.from_contents(document)
        )
    return Draft202012Validator(schema, registry=registry)


def validate_cross_stage_semantics(document: dict) -> None:
    typed = document["typed_mir"]["typed_constraints"]
    for field, (semantic_type, dimension, value) in EXPECTED_TYPED_VALUES.items():
        quantity = typed[field]
        if quantity["semantic_type"] != semantic_type:
            raise AssertionError(f"{field} semantic type drift")
        if quantity["dimension"] != dimension:
            raise AssertionError(f"{field} dimension drift")
        if quantity["value"] != value:
            raise AssertionError(f"{field} explicit source value drift")

    plans = document["planning"]["candidate_plans"]
    eligible = [
        plan
        for plan in plans
        if plan["source_fidelity"] == "Pass"
        and plan["feasibility"] in {"Feasible", "ConditionallyFeasible"}
        and all(
            obligation["status"] in {"Verified", "Reserved"}
            for obligation in plan["mandatory_obligations"]
            if obligation["kind"] in MANDATORY
        )
    ]
    selected = min(
        eligible,
        key=lambda plan: plan["estimated_total_energy"]["value"]["value"],
    )
    if selected["plan_id"] != document["planning"]["selected_plan_id"]:
        raise AssertionError("invalid minimum-Energy plan selection")
    if document["kernel_plan"]["source_plan_id"] != selected["plan_id"]:
        raise AssertionError("KernelPlan detached from selected candidate")

    runtime = document["runtime"]
    if (
        runtime["world_effect"]["source_world_revision"]
        != document["resolution_inputs"]["source_world_revision"]
    ):
        raise AssertionError("runtime effect detached from PREPARE world revision")
    if runtime["physical_time_is_runtime_tick"]:
        raise AssertionError("physical time collapsed into runtime tick")


class CanonicalWaterBallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pipeline = load(FIXTURES / "pipeline.json")
        cls.failures = load(FIXTURES / "failure-cases.json")
        cls.traceability = load(FIXTURES / "traceability.json")
        cls.schema = validator("canonical-water-ball.schema.json")
        cls.reference = REFERENCE.read_text(encoding="utf-8")

    def test_wb_001_documents_and_owned_references_validate(self) -> None:
        """WB-TEST-001: every machine-readable document and reused schema validates."""
        for document in (self.pipeline, self.failures, self.traceability):
            self.schema.validate(document)
        validate_cross_stage_semantics(self.pipeline)
        validator("nsr.schema.json").validate(self.pipeline["normalization"]["nsr"])
        validator("feasibility-report.schema.json").validate(
            self.pipeline["feasibility_report"]
        )
        for path in (
            self.pipeline["planning"]["inference_fixture"],
            self.pipeline["planning"]["dynamic_fixture"],
            self.pipeline["failure_catalog"],
            self.pipeline["traceability_matrix"],
        ):
            self.assertTrue((ROOT / path).is_file(), path)

    def test_wb_002_pipeline_stages_and_representations_remain_distinct(self) -> None:
        """WB-TEST-002: the complete ordered pipeline has distinct representation IDs."""
        stages = self.pipeline["stages"]
        self.assertEqual(STAGE_ORDER, [stage["stage"] for stage in stages])
        ids = [stage["representation_id"] for stage in stages]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn(
            "NaturalLanguageSource != NSR != SemanticAST != TypedMIR != KernelPlan",
            self.reference,
        )

    def test_wb_003_semantic_fingerprint_matches_nsr_not_artifact_hash(self) -> None:
        """WB-TEST-003: SemanticFingerprintV1 is computed from NSR semantics."""
        nsr = self.pipeline["normalization"]["nsr"]
        expected = nsr["semantic_fingerprint"]
        self.assertEqual(expected, semantic_fingerprint_v1(nsr))
        self.assertEqual(
            expected,
            self.pipeline["feasibility_report"]["provenance"][
                "semantic_fingerprint"
            ],
        )
        self.assertNotIn("content_hash", nsr)

    def test_wb_004_pathological_explicit_constraints_survive_elaboration(self) -> None:
        """WB-TEST-004: mass/radius/distance/acceleration are never optimized away."""
        patient = next(
            role["value"]
            for role in self.pipeline["normalization"]["nsr"]["roles"]
            if role["role"] == "Patient"
        )
        acceleration = next(
            role["value"]["value"]
            for role in self.pipeline["normalization"]["nsr"]["roles"]
            if role["role"] == "Quantity"
        )
        typed = self.pipeline["typed_mir"]["typed_constraints"]
        self.assertEqual(patient["value"]["mass"], typed["mass"])
        self.assertEqual(patient["value"]["radius"], typed["radius"])
        self.assertEqual(acceleration, typed["acceleration"])
        self.assertEqual(50, typed["mass"]["value"])
        self.assertEqual(0.01, typed["radius"]["value"])
        self.assertEqual(0, typed["initial_velocity"]["value"])
        self.assertEqual(50, typed["acceleration"]["value"])

        broken = copy.deepcopy(self.pipeline)
        broken["typed_mir"]["typed_constraints"]["mass"]["semantic_type"] = "Time"
        with self.assertRaisesRegex(AssertionError, "semantic type drift"):
            validate_cross_stage_semantics(broken)

        broken = copy.deepcopy(self.pipeline)
        broken["typed_mir"]["typed_constraints"]["acceleration"]["dimension"]["s"] = 0
        with self.assertRaisesRegex(AssertionError, "dimension drift"):
            validate_cross_stage_semantics(broken)

        broken = copy.deepcopy(self.pipeline)
        broken["typed_mir"]["typed_constraints"]["mass"]["value"] = 5
        with self.assertRaisesRegex(AssertionError, "source value drift"):
            validate_cross_stage_semantics(broken)

    def test_wb_005_unknown_estimate_assumption_and_binding_are_distinct(self) -> None:
        """WB-TEST-005: the omitted terminal reuses Issue #34 planning semantics."""
        terminal = self.pipeline["planning"]["terminal_assumption"]
        self.assertEqual(
            {"kind": "Unknown", "reason": "MissingArgument"},
            terminal["source_value"],
        )
        self.assertEqual("Exact", terminal["estimate"]["kind"])
        self.assertEqual(50, terminal["estimate"]["value"]["value"])
        self.assertEqual("PrepareBound", terminal["binding"]["mode"])
        self.assertEqual(
            {"kind": "Unknown", "reason": "MissingArgument"},
            self.pipeline["typed_mir"]["terminal"]["source_value"],
        )

    def test_wb_006_generation_lowers_only_to_six_mki_primitives(self) -> None:
        """WB-TEST-006: generate remains a desired-state goal, not a seventh primitive."""
        self.assertEqual("generate", self.pipeline["semantic_ast"]["action"])
        for plan in self.pipeline["planning"]["candidate_plans"]:
            self.assertLessEqual(set(plan["operations"]), MKI_PRIMITIVES)
            self.assertNotIn("GENERATE", plan["operations"])
            self.assertNotIn("CREATE", plan["operations"])
        kernel_plan = self.pipeline["kernel_plan"]
        self.assertEqual(
            self.pipeline["planning"]["selected_plan_id"],
            kernel_plan["source_plan_id"],
        )
        self.assertLessEqual(set(kernel_plan["operations"]), MKI_PRIMITIVES)
        self.assertTrue(kernel_plan["revalidation_required"])

    def test_wb_007_only_eligible_plans_enter_energy_optimization(self) -> None:
        """WB-TEST-007: minimum Energy follows fidelity, obligations, and feasibility."""
        plans = self.pipeline["planning"]["candidate_plans"]
        for plan in plans:
            obligations = {item["kind"]: item for item in plan["mandatory_obligations"]}
            self.assertLessEqual(MANDATORY, set(obligations))
            self.assertTrue(
                all(
                    obligations[kind]["basis"] != "Inference"
                    for kind in MANDATORY
                )
            )
        eligible = [
            plan
            for plan in plans
            if plan["source_fidelity"] == "Pass"
            and plan["feasibility"] in {"Feasible", "ConditionallyFeasible"}
            and all(
                item["status"] in {"Verified", "Reserved"}
                for item in plan["mandatory_obligations"]
                if item["kind"] in MANDATORY
            )
        ]
        selected = min(
            eligible,
            key=lambda plan: plan["estimated_total_energy"]["value"]["value"],
        )
        self.assertEqual(
            selected["plan_id"], self.pipeline["planning"]["selected_plan_id"]
        )
        self.assertEqual(
            200, self.pipeline["feasibility_report"]["energy"]["total"]["value"]
        )

        broken = copy.deepcopy(self.pipeline)
        broken["planning"]["selected_plan_id"] = "wb:plan:assemble-alternative"
        with self.assertRaisesRegex(AssertionError, "minimum-Energy"):
            validate_cross_stage_semantics(broken)

    def test_wb_008_registry_index_and_world_revision_domains_are_explicit(self) -> None:
        """WB-TEST-008: resolver inputs preserve registry/index/world identities."""
        inputs = self.pipeline["resolution_inputs"]
        self.assertNotEqual(
            inputs["world_index_revision"], inputs["source_world_revision"]
        )
        self.assertTrue(inputs["required_registry_contracts"])
        self.assertNotEqual(
            inputs["semantic_registry"]["artifact_id"],
            inputs["world_index"]["artifact_id"],
        )

    def test_wb_009_authority_lease_and_conservation_are_not_estimates(self) -> None:
        """WB-TEST-009: mandatory proof/reservation evidence stays authoritative."""
        selected = next(
            plan
            for plan in self.pipeline["planning"]["candidate_plans"]
            if plan["plan_id"] == self.pipeline["planning"]["selected_plan_id"]
        )
        obligations = {item["kind"]: item for item in selected["mandatory_obligations"]}
        self.assertEqual("AuthoritativeEvidence", obligations["Authority"]["basis"])
        self.assertEqual("Reservation", obligations["Lease"]["basis"])
        self.assertEqual("DeterministicProof", obligations["Conservation"]["basis"])

        broken = copy.deepcopy(self.pipeline)
        plan = broken["planning"]["candidate_plans"][0]
        plan["mandatory_obligations"][3]["basis"] = "Inference"
        self.assertTrue(list(self.schema.iter_errors(broken)))

    def test_wb_010_bound_dynamic_and_runtime_commit_are_distinct(self) -> None:
        """WB-TEST-010: binding, revalidation, TickStamp, and world effect stay separate."""
        bound = load(ROOT / self.pipeline["planning"]["inference_fixture"])
        dynamic = load(ROOT / self.pipeline["planning"]["dynamic_fixture"])
        self.assertEqual(
            "PrepareBound", bound["planner_predictions"][0]["binding"]["mode"]
        )
        self.assertEqual(
            "Dynamic", dynamic["planner_predictions"][0]["binding"]["mode"]
        )
        self.assertEqual("CONSTRAIN", dynamic["reactive_controls"][0]["operation"])
        runtime = self.pipeline["runtime"]
        self.assertFalse(runtime["physical_time_is_runtime_tick"])
        self.assertEqual("Pass", runtime["revalidation"]["status"])
        self.assertEqual("Committed", runtime["commit"]["status"])
        self.assertNotEqual(
            runtime["world_effect"]["source_world_revision"],
            runtime["world_effect"]["result_world_revision"],
        )

        broken = copy.deepcopy(self.pipeline)
        broken["runtime"]["world_effect"]["source_world_revision"] = "world:stale"
        with self.assertRaisesRegex(AssertionError, "detached from PREPARE"):
            validate_cross_stage_semantics(broken)

    def test_wb_011_failure_and_traceability_coverage_is_stable(self) -> None:
        """WB-TEST-011: failure categories and rule/test/fixture links remain complete."""
        cases = self.failures["cases"]
        self.assertEqual(FAILURE_CATEGORIES, {case["category"] for case in cases})
        failure_ids = {case["test_id"] for case in cases}
        self.assertEqual(len(failure_ids), len(cases))
        errors = (ROOT / "reference" / "errors.md").read_text(encoding="utf-8")
        for case in cases:
            self.assertIn(case["diagnostic"], errors)
        referenced_tests = set()
        for entry in self.traceability["entries"]:
            referenced_tests.update(entry["test_ids"])
            for path in entry["fixture_paths"]:
                self.assertTrue((ROOT / path).is_file(), path)
        self.assertLessEqual(TEST_IDS, referenced_tests)
        self.assertLessEqual(failure_ids, referenced_tests)


if __name__ == "__main__":
    unittest.main()
