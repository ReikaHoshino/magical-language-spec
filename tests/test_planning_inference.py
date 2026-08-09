from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
FIXTURES = ROOT / "examples" / "planning-inference"
REFERENCE = ROOT / "reference" / "planning-inference.md"

MKI_DATA_PLANE = {
    "RESOLVE",
    "OBSERVE",
    "CHANNEL",
    "TRANSFER",
    "RECONFIGURE",
    "CONSTRAIN",
}
MANDATORY_OBLIGATIONS = {
    "Type",
    "Identity",
    "Conservation",
    "Authority",
    "Lease",
}
SATISFIED_OBLIGATION_STATUSES = {"Verified", "Reserved"}
ELIGIBLE_FEASIBILITY = {"Feasible", "ConditionallyFeasible"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def schema_validator() -> Draft202012Validator:
    schema = load(SCHEMAS / "planning-inference.schema.json")
    registry = Registry()
    for path in SCHEMAS.glob("*.schema.json"):
        document = load(path)
        registry = registry.with_resource(
            document["$id"], Resource.from_contents(document)
        )
    return Draft202012Validator(schema, registry=registry)


def validate_semantic_links(document: dict) -> None:
    """Validate cross-record planning invariants not expressible in JSON Schema."""
    source = document["source_semantics"]
    source_id = source["source_id"]
    constraints = {
        constraint["field_path"]: constraint["source_value"]
        for constraint in source["constraints"]
    }
    explicit_paths = {
        path for path, value in constraints.items() if value["kind"] == "Explicit"
    }

    goal = document["generation_goal"]
    if goal["source_semantics_id"] != source_id:
        raise AssertionError("generation goal detached from source semantics")
    if not explicit_paths <= set(goal["preserved_constraint_paths"]):
        raise AssertionError("generation goal did not preserve every explicit constraint")

    inference_by_id = {}
    for record in document["inference_records"]:
        inference_by_id[record["record_id"]] = record
        target_path = record["target"]["field_path"]
        if "selected_planning_value" in record:
            source_value = constraints.get(target_path)
            if source_value is None or source_value["kind"] != "Unknown":
                raise AssertionError(
                    "planning inference selected a value for explicit source semantics"
                )
            if source_value["reason"] != record["unknown"]["reason"]:
                raise AssertionError("inference record changed the source Unknown reason")
            if record["criticality"] == "MustResolve":
                raise AssertionError("MustResolve obligation was satisfied by inference")

    assumptions_by_id = {
        assumption["assumption_id"]: assumption
        for assumption in document["planning_assumptions"]
    }
    for assumption in assumptions_by_id.values():
        record = inference_by_id.get(assumption["inference_record_id"])
        if record is None:
            raise AssertionError("planning assumption has no inference provenance")
        if assumption["assumption_id"] not in record["assumption_ids"]:
            raise AssertionError("inference record does not name adopted assumption")
        if record.get("selected_planning_value") != assumption["selected_value"]:
            raise AssertionError("adopted value differs from its inference record")
        if record.get("binding") != assumption["binding"]:
            raise AssertionError("assumption binding differs from inference record")

    plans_by_id = {plan["plan_id"]: plan for plan in document["candidate_plans"]}
    selected = plans_by_id.get(document["selection"]["selected_plan_id"])
    if selected is None:
        raise AssertionError("selected plan does not exist")

    for plan in plans_by_id.values():
        if plan["source_semantics_id"] != source_id:
            raise AssertionError("candidate plan detached from source semantics")
        if not set(plan["operations"]) <= MKI_DATA_PLANE:
            raise AssertionError("candidate plan invented an MKI data-plane primitive")

    if selected["source_fidelity"] != "Pass":
        raise AssertionError("selected plan failed source semantic fidelity")
    selected_obligations = {
        obligation["kind"]: obligation for obligation in selected["mandatory_obligations"]
    }
    if not MANDATORY_OBLIGATIONS <= set(selected_obligations):
        raise AssertionError("selected plan omitted a mandatory obligation")
    if any(
        selected_obligations[kind]["status"] not in SATISFIED_OBLIGATION_STATUSES
        for kind in MANDATORY_OBLIGATIONS
    ):
        raise AssertionError("selected plan has an unresolved mandatory obligation")
    if selected["feasibility"] not in ELIGIBLE_FEASIBILITY:
        raise AssertionError("selected plan is not feasible")

    eligible = []
    for plan in plans_by_id.values():
        obligations = {
            obligation["kind"]: obligation
            for obligation in plan["mandatory_obligations"]
        }
        obligations_satisfied = MANDATORY_OBLIGATIONS <= set(obligations) and all(
            obligations[kind]["status"] in SATISFIED_OBLIGATION_STATUSES
            for kind in MANDATORY_OBLIGATIONS
        )
        total = plan["energy"].get("total", {})
        if (
            plan["source_fidelity"] == "Pass"
            and obligations_satisfied
            and plan["feasibility"] in ELIGIBLE_FEASIBILITY
            and total.get("kind") == "Range"
            and isinstance(total.get("min"), (int, float))
            and isinstance(total.get("max"), (int, float))
        ):
            eligible.append((total["max"], total["min"], plan["plan_id"]))
    if eligible and selected["plan_id"] != min(eligible)[2]:
        raise AssertionError("optimization ran before fidelity/obligation/feasibility gates")

    terminal = document["terminal_policy"]
    terminal_source = constraints.get("motion.terminal")
    if terminal_source != terminal["source_terminal"]:
        raise AssertionError("terminal inference rewrote the source Unknown")
    if terminal["inference_record_id"] not in inference_by_id:
        raise AssertionError("terminal policy lacks inference provenance")

    controls = {
        control["control_id"]: control for control in document.get("reactive_controls", [])
    }
    for prediction in document.get("planner_predictions", []):
        binding = prediction["binding"]
        if binding["mode"] == "Dynamic":
            control = controls.get(binding["reactive_control_id"])
            if control is None or control["operation"] != "CONSTRAIN":
                raise AssertionError("Dynamic prediction lacks explicit CONSTRAIN semantics")
            if prediction["late_world_change_behavior"] != "DynamicReactiveControl":
                raise AssertionError("Dynamic prediction has bound late-change behavior")
        elif (
            prediction["late_world_change_behavior"]
            != "RemainBoundUnlessMandatoryInvariant"
        ):
            raise AssertionError("bound prediction silently acquired reactive behavior")
        if prediction["runtime_safety_guarantee"] is not False:
            raise AssertionError("planner prediction became a runtime safety guarantee")


class PlanningInferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = schema_validator()
        cls.bound = load(FIXTURES / "pathological-water-ball-bound.json")
        cls.dynamic = load(FIXTURES / "pathological-water-ball-dynamic.json")
        cls.reference = REFERENCE.read_text(encoding="utf-8")

    def test_positive_fixtures_validate(self) -> None:
        for fixture in (self.bound, self.dynamic):
            self.validator.validate(fixture)
            validate_semantic_links(fixture)

    def test_pathological_explicit_values_are_preserved(self) -> None:
        constraints = {
            item["field_path"]: item["source_value"]
            for item in self.bound["source_semantics"]["constraints"]
        }
        self.assertEqual(50, constraints["goal.mass"]["value"]["value"])
        self.assertEqual(0.01, constraints["goal.radius"]["value"]["value"])
        self.assertEqual(50, constraints["motion.acceleration"]["value"]["value"])
        self.assertEqual(0, constraints["motion.initial_velocity"]["value"]["value"])

        broken = copy.deepcopy(self.bound)
        record = broken["inference_records"][0]
        record["target"]["field_path"] = "goal.mass"
        with self.assertRaisesRegex(
            AssertionError, "explicit source semantics"
        ):
            validate_semantic_links(broken)

        broken = copy.deepcopy(self.bound)
        broken["generation_goal"]["preserved_constraint_paths"].remove("goal.mass")
        with self.assertRaisesRegex(AssertionError, "preserve every explicit"):
            validate_semantic_links(broken)

    def test_unknown_estimate_and_assumption_remain_distinct(self) -> None:
        source_terminal = next(
            item["source_value"]
            for item in self.bound["source_semantics"]["constraints"]
            if item["field_path"] == "motion.terminal"
        )
        record = self.bound["inference_records"][0]
        assumption = self.bound["planning_assumptions"][0]
        self.assertEqual({"kind": "Unknown", "reason": "MissingArgument"}, source_terminal)
        self.assertEqual("Exact", record["estimate"]["kind"])
        self.assertEqual("PlanningAssumption", assumption["semantic_status"])
        self.assertEqual(source_terminal, self.bound["terminal_policy"]["source_terminal"])

    def test_must_resolve_cannot_select_a_planning_value(self) -> None:
        broken = copy.deepcopy(self.bound)
        broken["inference_records"][0]["criticality"] = "MustResolve"
        self.assertTrue(list(self.validator.iter_errors(broken)))

    def test_untrusted_estimators_cannot_masquerade_as_truth(self) -> None:
        broken = copy.deepcopy(self.bound)
        estimator = broken["inference_records"][0]["estimator"]
        estimator.update(
            {
                "class": "AIProposal",
                "id": "model:fixture-ai",
                "revision": "1",
                "trust": "Deterministic",
            }
        )
        self.assertTrue(list(self.validator.iter_errors(broken)))

    def test_selected_terminal_is_bounded_and_world_projection_is_revisioned(self) -> None:
        broken = copy.deepcopy(self.bound)
        del broken["terminal_policy"]["bounds"]["max_distance"]
        self.assertTrue(list(self.validator.iter_errors(broken)))

        broken = copy.deepcopy(self.dynamic)
        del broken["inference_records"][0]["world_context"]
        self.assertTrue(list(self.validator.iter_errors(broken)))

    def test_inference_is_not_an_obligation_basis(self) -> None:
        broken = copy.deepcopy(self.bound)
        selected = next(
            plan
            for plan in broken["candidate_plans"]
            if plan["plan_id"] == broken["selection"]["selected_plan_id"]
        )
        selected["mandatory_obligations"][3]["basis"] = "Inference"
        self.assertTrue(list(self.validator.iter_errors(broken)))

        broken = copy.deepcopy(self.bound)
        selected = next(
            plan
            for plan in broken["candidate_plans"]
            if plan["plan_id"] == broken["selection"]["selected_plan_id"]
        )
        selected["mandatory_obligations"][3]["status"] = "Indeterminate"
        with self.assertRaisesRegex(AssertionError, "unresolved mandatory"):
            validate_semantic_links(broken)

    def test_generation_uses_six_existing_primitives_and_energy_order(self) -> None:
        validate_semantic_links(self.bound)
        for plan in self.bound["candidate_plans"]:
            self.assertLessEqual(set(plan["operations"]), MKI_DATA_PLANE)
            self.assertNotIn("GENERATE", plan["operations"])
            self.assertNotIn("CREATE", plan["operations"])
        self.assertEqual(
            "plan:transfer-reconfigure-water",
            self.bound["selection"]["selected_plan_id"],
        )
        selected = next(
            plan
            for plan in self.bound["candidate_plans"]
            if plan["plan_id"] == self.bound["selection"]["selected_plan_id"]
        )
        self.assertEqual(
            ["evidence:synthetic-fixture-energy-range"],
            selected["energy"]["total"]["evidence_ids"],
        )
        self.assertEqual(
            125000,
            selected["energy"]["components"]["physical_work"]["value"],
        )
        self.assertIn("control", selected["energy"]["components"])
        self.assertEqual(
            "CONSTRAIN", self.bound["reactive_controls"][0]["operation"]
        )
        self.assertEqual(
            [
                "SourceSemanticFidelity",
                "MandatoryObligations",
                "Feasibility",
                "OptimizationObjective",
            ],
            self.bound["selection"]["ordering"],
        )

    def test_bound_and_dynamic_terminal_behavior_are_distinct(self) -> None:
        bound_prediction = self.bound["planner_predictions"][0]
        self.assertEqual("PrepareBound", bound_prediction["binding"]["mode"])
        self.assertEqual(
            "RemainBoundUnlessMandatoryInvariant",
            bound_prediction["late_world_change_behavior"],
        )

        dynamic_prediction = self.dynamic["planner_predictions"][0]
        self.assertEqual("Dynamic", dynamic_prediction["binding"]["mode"])
        self.assertEqual(
            "DynamicReactiveControl",
            dynamic_prediction["late_world_change_behavior"],
        )
        self.assertEqual(
            "CONSTRAIN", self.dynamic["reactive_controls"][0]["operation"]
        )

        broken = copy.deepcopy(self.bound)
        broken["planner_predictions"][0][
            "late_world_change_behavior"
        ] = "DynamicReactiveControl"
        self.assertTrue(list(self.validator.iter_errors(broken)))
        with self.assertRaisesRegex(AssertionError, "silently acquired reactive"):
            validate_semantic_links(broken)

        broken = copy.deepcopy(self.bound)
        broken["planner_predictions"][0]["runtime_safety_guarantee"] = True
        self.assertTrue(list(self.validator.iter_errors(broken)))

    def test_world_index_and_world_revision_domains_are_separate(self) -> None:
        world_context = self.dynamic["inference_records"][0]["world_context"]
        self.assertEqual("index:4201", world_context["world_index_revision"])
        self.assertEqual("world:991", world_context["source_world_revision"])
        self.assertNotEqual(
            world_context["world_index_revision"],
            world_context["source_world_revision"],
        )

    def test_reference_contains_normative_boundaries(self) -> None:
        for invariant in (
            "Unknown != Estimate",
            "Estimate != PlanningAssumption",
            "PlanningAssumption != Observed",
            "PlanningAssumption != Truth",
            "NormalizationAmbiguity != PlanningInference",
            "PlannerPrediction != RuntimeSafetyGuarantee",
            "WorldIndexRevision != WorldRevision",
            "MKI data-plane primitiveではない",
            "minimum estimated total Energy",
        ):
            self.assertIn(invariant, self.reference)


if __name__ == "__main__":
    unittest.main()
