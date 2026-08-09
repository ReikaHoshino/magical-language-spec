from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
FIXTURE = (
    ROOT
    / "examples"
    / "estimator-profiles"
    / "synthetic-reference-v1.json"
)
REFERENCE = ROOT / "reference" / "estimator-models.md"

ENERGY_CATEGORIES = {
    "physical_work",
    "reaction_or_thermodynamic",
    "channel_open",
    "channel_maintenance",
    "control",
    "observation_information",
    "synchronization",
    "losses",
    "reserved_margin",
}
ENERGY_DIMENSION = {
    "kg": 1,
    "m": 2,
    "s": -2,
    "A": 0,
    "K": 0,
    "mol": 0,
    "cd": 0,
}
TIME_DIMENSION = {
    "kg": 0,
    "m": 0,
    "s": 1,
    "A": 0,
    "K": 0,
    "mol": 0,
    "cd": 0,
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def schema_validator() -> Draft202012Validator:
    schema = load(SCHEMAS / "estimator-profile.schema.json")
    registry = Registry()
    for path in SCHEMAS.glob("*.schema.json"):
        document = load(path)
        registry = registry.with_resource(
            document["$id"], Resource.from_contents(document)
        )
    return Draft202012Validator(schema, registry=registry)


def validate_semantic_links(profile: dict) -> None:
    """Check model/result invariants that require cross-record comparison."""
    models = {}
    for model in profile["models"]:
        key = (model["model_id"], model["revision"])
        if key in models:
            raise AssertionError("duplicate estimator model identity/revision")
        models[key] = model

        output = model["output_contract"]
        if model["domain"] == "Energy":
            if output["semantic_type"] != "Energy":
                raise AssertionError("Energy model output lost its semantic type")
            if output["dimension"] != ENERGY_DIMENSION:
                raise AssertionError("Energy model output has an invalid dimension")
        if model["domain"] == "Timing":
            if output["semantic_type"] != "Time":
                raise AssertionError("timing model output lost its semantic type")
            if output["dimension"] != TIME_DIMENSION:
                raise AssertionError("timing model output has an invalid dimension")

        if model["availability"]["status"] == "Available":
            if model["evaluation_rule"]["kind"] == "SyntheticFixedCoefficient":
                coefficients = {
                    coefficient["coefficient_id"]: coefficient
                    for coefficient in model["coefficients"]
                }
                coefficient_id = model["evaluation_rule"]["coefficient_id"]
                coefficient = coefficients.get(coefficient_id)
                if coefficient is None:
                    raise AssertionError("evaluation rule names no owned coefficient")
                value = coefficient["value"]
                if value["semantic_type"] != output["semantic_type"]:
                    raise AssertionError(
                        "coefficient semantic type differs from model output"
                    )
                if value["dimension"] != output["dimension"]:
                    raise AssertionError(
                        "coefficient dimension differs from model output"
                    )
                if value["unit"] != output["unit"]:
                    raise AssertionError("coefficient unit differs from model output")
                if (
                    not coefficient["fixture_only"]
                    and profile["profile_kind"] == "SyntheticReference"
                ):
                    raise AssertionError(
                        "synthetic coefficient escaped fixture-only scope"
                    )
        elif "coefficients" in model or "evaluation_rule" in model:
            raise AssertionError("unavailable model exposes an evaluation value")

    for case in profile["reference_cases"]:
        key = (case["model"]["model_id"], case["model"]["revision"])
        model = models.get(key)
        if model is None:
            raise AssertionError("reference case names a missing model identity/revision")
        if case["source_before"] != case["source_after"]:
            raise AssertionError("estimator output rewrote source semantics")

        estimate = case["estimate"]
        if model["availability"]["status"] == "Unavailable":
            if estimate["kind"] != "Unknown":
                raise AssertionError("unavailable model produced a known estimate")
            if estimate["classification"] not in {"ModelDependent", "Unavailable"}:
                raise AssertionError("unavailable model lost Unknown classification")
        elif estimate["kind"] == "Exact":
            result = estimate["value"]
            output = model["output_contract"]
            if result["semantic_type"] != output["semantic_type"]:
                raise AssertionError("estimate semantic type differs from model output")
            if result["dimension"] != output["dimension"]:
                raise AssertionError("estimate dimension differs from model output")
            if result["unit"] != output["unit"]:
                raise AssertionError("estimate unit differs from model output")
            coefficients = {
                coefficient["coefficient_id"]: coefficient
                for coefficient in model["coefficients"]
            }
            coefficient = coefficients[model["evaluation_rule"]["coefficient_id"]]
            if result != coefficient["value"]:
                raise AssertionError("deterministic synthetic result drifted")
        elif estimate["kind"] in {"Range", "LowerBound", "UpperBound"}:
            output = model["output_contract"]
            names = ("min", "max") if estimate["kind"] == "Range" else ("value",)
            for name in names:
                result = estimate[name]
                if result["semantic_type"] != output["semantic_type"]:
                    raise AssertionError("estimate semantic type differs from model output")
                if result["dimension"] != output["dimension"]:
                    raise AssertionError("estimate dimension differs from model output")
                if result["unit"] != output["unit"]:
                    raise AssertionError("estimate unit differs from model output")
            if (
                estimate["kind"] == "Range"
                and estimate["min"]["value"] > estimate["max"]["value"]
            ):
                raise AssertionError("estimate range has inverted bounds")
        elif model["evaluation_rule"]["kind"] == "SyntheticFixedCoefficient":
            raise AssertionError("fixed synthetic rule produced a non-exact result")

        if model["domain"] == "Timing":
            runtime_context = case.get("runtime_context")
            if runtime_context is None:
                raise AssertionError("timing estimate lacks RuntimeProfile context")
            if runtime_context["physical_time_is_runtime_tick"]:
                raise AssertionError("physical time was collapsed into runtime tick")
            if (
                runtime_context["runtime_profile"]
                != profile["runtime_profile_requirement"]["profile"]
            ):
                raise AssertionError("timing case uses a different RuntimeProfile")

        adoption = case.get("adoption")
        if adoption and adoption["criticality"] != "EstimateAllowed":
            raise AssertionError("estimator adoption bypassed Issue #34 criticality")
        if any(
            obligation["status"] != "Indeterminate"
            for obligation in case["mandatory_obligations"]
        ):
            raise AssertionError("estimate satisfied a mandatory obligation")


class EstimatorProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = schema_validator()
        cls.profile = load(FIXTURE)
        cls.reference = REFERENCE.read_text(encoding="utf-8")

    def test_positive_fixture_validates(self) -> None:
        self.validator.validate(self.profile)
        validate_semantic_links(self.profile)

    def test_energy_breakdown_is_complete_and_deterministic(self) -> None:
        energy_models = [
            model for model in self.profile["models"] if model["domain"] == "Energy"
        ]
        self.assertEqual(
            ENERGY_CATEGORIES,
            {model["category"] for model in energy_models},
        )
        total = 0
        for model in energy_models:
            coefficient_id = model["evaluation_rule"]["coefficient_id"]
            coefficient = next(
                value
                for value in model["coefficients"]
                if value["coefficient_id"] == coefficient_id
            )
            total += coefficient["value"]["value"]
        self.assertEqual(200, total)

    def test_missing_model_identity_is_rejected(self) -> None:
        broken = copy.deepcopy(self.profile)
        del broken["models"][0]["model_id"]
        self.assertTrue(list(self.validator.iter_errors(broken)))

        broken = copy.deepcopy(self.profile)
        broken["reference_cases"][0]["model"]["revision"] = "missing"
        with self.assertRaisesRegex(AssertionError, "missing model"):
            validate_semantic_links(broken)

    def test_invalid_units_and_dimensions_are_rejected(self) -> None:
        broken = copy.deepcopy(self.profile)
        energy = next(model for model in broken["models"] if model["domain"] == "Energy")
        energy["output_contract"]["dimension"]["s"] = -1
        self.assertTrue(list(self.validator.iter_errors(broken)))

        broken = copy.deepcopy(self.profile)
        timing = next(model for model in broken["models"] if model["domain"] == "Timing")
        timing["output_contract"]["dimension"]["s"] = 0
        self.assertTrue(list(self.validator.iter_errors(broken)))

        broken = copy.deepcopy(self.profile)
        energy = next(model for model in broken["models"] if model["domain"] == "Energy")
        energy["coefficients"][0]["value"]["dimension"]["s"] = -1
        with self.assertRaisesRegex(AssertionError, "coefficient dimension"):
            validate_semantic_links(broken)

        broken = copy.deepcopy(self.profile)
        energy = next(model for model in broken["models"] if model["domain"] == "Energy")
        energy["coefficients"][0]["value"]["unit"] = "s"
        with self.assertRaisesRegex(AssertionError, "coefficient unit"):
            validate_semantic_links(broken)

    def test_unavailable_model_is_unknown_not_zero(self) -> None:
        unavailable = next(
            model
            for model in self.profile["models"]
            if model["availability"]["status"] == "Unavailable"
        )
        self.assertNotIn("coefficients", unavailable)
        case = next(
            case
            for case in self.profile["reference_cases"]
            if case["model"]["model_id"] == unavailable["model_id"]
        )
        self.assertEqual("Unknown", case["estimate"]["kind"])

        broken = copy.deepcopy(self.profile)
        case = next(
            case
            for case in broken["reference_cases"]
            if case["model"]["model_id"] == unavailable["model_id"]
        )
        case["estimate"] = {
            "kind": "Exact",
            "value": {
                "semantic_type": "MatterBudget",
                "dimension": {
                    "kg": 1,
                    "m": 0,
                    "s": 0,
                    "A": 0,
                    "K": 0,
                    "mol": 0,
                    "cd": 0,
                },
                "value": 0,
                "unit": "kg",
            },
            "uncertainty": "Invented zero.",
            "evidence_ids": ["evidence:world-model-unavailable"],
        }
        with self.assertRaisesRegex(AssertionError, "known estimate"):
            validate_semantic_links(broken)

    def test_range_and_bound_estimates_keep_quantity_contract(self) -> None:
        ranged = copy.deepcopy(self.profile)
        case = next(
            item
            for item in ranged["reference_cases"]
            if item["model"]["model_id"]
            == "estimator:synthetic:resource:information-budget"
        )
        model = next(
            item
            for item in ranged["models"]
            if item["model_id"] == case["model"]["model_id"]
        )
        model["evaluation_rule"] = {
            "kind": "OwnedModel",
            "rule_id": "estimator-rule:synthetic-resource-range",
            "revision": "1",
            "owner": copy.deepcopy(model["owner"]),
        }
        lower = copy.deepcopy(case["estimate"]["value"])
        upper = copy.deepcopy(lower)
        lower["value"] = 2048
        upper["value"] = 4096
        case["estimate"] = {
            "kind": "Range",
            "min": lower,
            "max": upper,
            "uncertainty": "Synthetic bounded range.",
            "evidence_ids": ["evidence:synthetic-resource-budget"],
        }
        self.validator.validate(ranged)
        validate_semantic_links(ranged)

        broken = copy.deepcopy(ranged)
        case = next(
            item
            for item in broken["reference_cases"]
            if item["case_id"] == "case:synthetic-resource-adoption"
        )
        case["estimate"]["max"]["dimension"]["kg"] = 1
        with self.assertRaisesRegex(AssertionError, "estimate dimension"):
            validate_semantic_links(broken)

        broken = copy.deepcopy(ranged)
        case = next(
            item
            for item in broken["reference_cases"]
            if item["case_id"] == "case:synthetic-resource-adoption"
        )
        case["estimate"]["min"]["value"] = 8192
        with self.assertRaisesRegex(AssertionError, "inverted bounds"):
            validate_semantic_links(broken)

    def test_synthetic_values_are_not_world_constants(self) -> None:
        self.assertFalse(
            self.profile["scope"]["values_are_universal_world_constants"]
        )
        broken = copy.deepcopy(self.profile)
        broken["scope"]["values_are_universal_world_constants"] = True
        self.assertTrue(list(self.validator.iter_errors(broken)))

        broken = copy.deepcopy(self.profile)
        energy = next(model for model in broken["models"] if model["domain"] == "Energy")
        energy["coefficients"][0]["fixture_only"] = False
        with self.assertRaisesRegex(AssertionError, "fixture-only"):
            validate_semantic_links(broken)

    def test_source_semantics_and_planning_adoption_remain_distinct(self) -> None:
        adopted = next(
            case for case in self.profile["reference_cases"] if "adoption" in case
        )
        self.assertEqual(adopted["source_before"], adopted["source_after"])
        self.assertEqual(
            "EstimateAllowed", adopted["adoption"]["criticality"]
        )

        broken = copy.deepcopy(self.profile)
        adopted = next(
            case for case in broken["reference_cases"] if "adoption" in case
        )
        adopted["source_after"] = {
            "kind": "Explicit",
            "value": adopted["estimate"]["value"],
        }
        with self.assertRaisesRegex(AssertionError, "rewrote source"):
            validate_semantic_links(broken)

        broken = copy.deepcopy(self.profile)
        adopted = next(
            case for case in broken["reference_cases"] if "adoption" in case
        )
        adopted["adoption"]["criticality"] = "MustResolve"
        self.assertTrue(list(self.validator.iter_errors(broken)))

    def test_estimate_cannot_satisfy_mandatory_obligation(self) -> None:
        broken = copy.deepcopy(self.profile)
        adopted = next(
            case for case in broken["reference_cases"] if "adoption" in case
        )
        adopted["mandatory_obligations"][0]["status"] = "Verified"
        self.assertTrue(list(self.validator.iter_errors(broken)))

    def test_physical_time_is_not_runtime_tick(self) -> None:
        timing_case = next(
            case
            for case in self.profile["reference_cases"]
            if "runtime_context" in case
        )
        self.assertEqual("Time", timing_case["estimate"]["value"]["semantic_type"])
        self.assertFalse(timing_case["runtime_context"]["physical_time_is_runtime_tick"])

        broken = copy.deepcopy(self.profile)
        timing_case = next(
            case for case in broken["reference_cases"] if "runtime_context" in case
        )
        timing_case["runtime_context"]["physical_time_is_runtime_tick"] = True
        self.assertTrue(list(self.validator.iter_errors(broken)))

        broken = copy.deepcopy(self.profile)
        timing_case = next(
            case for case in broken["reference_cases"] if "runtime_context" in case
        )
        timing_case["runtime_context"]["runtime_profile"]["revision"] = "incompatible"
        with self.assertRaisesRegex(AssertionError, "different RuntimeProfile"):
            validate_semantic_links(broken)

        broken = copy.deepcopy(self.profile)
        timing_case = next(
            case for case in broken["reference_cases"] if "runtime_context" in case
        )
        timing_case["estimate"]["value"]["semantic_type"] = "RuntimeTickID"
        with self.assertRaisesRegex(AssertionError, "semantic type"):
            validate_semantic_links(broken)

    def test_reference_contains_normative_boundaries(self) -> None:
        for invariant in (
            "SourceSemanticValue != Estimate != PlanningAssumption",
            "EstimatorOutput != MandatoryProof",
            "UnavailableModel != zero",
            "SyntheticFixtureValue != UniversalWorldConstant",
            "Physical time != runtime tick",
            "Shared metadata rules != shared compatibility algorithm",
        ):
            self.assertIn(invariant, self.reference)


if __name__ == "__main__":
    unittest.main()
