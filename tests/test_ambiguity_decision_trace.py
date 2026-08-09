from __future__ import annotations

import copy
import json
import unittest
from functools import cmp_to_key
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples" / "ambiguity-policy"
SCHEMA = ROOT / "schemas" / "ambiguity-decision-trace.schema.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def compare_values(left, right, comparator: str) -> int:
    if comparator == "BooleanTrueFirst":
        left, right = (0 if left else 1), (0 if right else 1)
    elif comparator == "BooleanFalseFirst":
        left, right = (0 if not left else 1), (0 if not right else 1)
    elif comparator in {"IntegerDescending", "StringCodePointDescending"}:
        left, right = right, left
    return (left > right) - (left < right)


def replay_selected_candidate(trace: dict) -> str:
    """Small conformance oracle for the ordering contract, not an evaluator."""
    rules = trace["profile"]["ranking_rules"]
    evaluations = {
        evaluation["candidate_id"]: evaluation
        for evaluation in trace["ranking_evaluations"]
        if evaluation["eligible"]
    }
    candidates = {
        candidate["candidate_id"]: candidate
        for candidate in trace["candidate_set"]["candidates"]
        if candidate["normalization_valid"]
    }

    def compare(left_id: str, right_id: str) -> int:
        left_terms = {
            term["rule_id"]: term["value"]
            for term in evaluations[left_id]["rank_terms"]
        }
        right_terms = {
            term["rule_id"]: term["value"]
            for term in evaluations[right_id]["rank_terms"]
        }
        for rule in rules:
            left = left_terms.get(rule["rule_id"])
            right = right_terms.get(rule["rule_id"])
            if left is None or right is None:
                if rule["missing_value"] == "Unreproducible":
                    raise ValueError("required rank input is unavailable")
                if rule["missing_value"] == "RejectCandidate":
                    if left is None and right is not None:
                        return 1
                    if right is None and left is not None:
                        return -1
                elif rule["missing_value"] == "RankFirst":
                    if left is None and right is not None:
                        return -1
                    if right is None and left is not None:
                        return 1
                elif rule["missing_value"] == "RankLast":
                    if left is None and right is not None:
                        return 1
                    if right is None and left is not None:
                        return -1
                continue
            result = compare_values(left, right, rule["comparator"])
            if result:
                return result

        left_candidate = candidates[left_id]
        right_candidate = candidates[right_id]
        left_fingerprint = left_candidate["semantic_fingerprint"]
        right_fingerprint = right_candidate["semantic_fingerprint"]
        if left_fingerprint != right_fingerprint:
            return (left_fingerprint > right_fingerprint) - (
                left_fingerprint < right_fingerprint
            )
        return (left_id > right_id) - (left_id < right_id)

    return sorted(evaluations, key=cmp_to_key(compare))[0]


class AmbiguityDecisionTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load(SCHEMA)
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)
        cls.fixtures = {
            path.name: load(path)
            for path in sorted(FIXTURES.glob("*.json"))
        }

    def test_all_fixtures_validate_and_references_are_complete(self) -> None:
        self.assertGreaterEqual(len(self.fixtures), 6)
        self.assertEqual(
            {trace["policy"] for trace in self.fixtures.values()},
            {
                "StrictReject",
                "InteractiveResolve",
                "ContextualDeterministic",
                "LegacyPermissive",
            },
        )
        for name, trace in self.fixtures.items():
            with self.subTest(name=name):
                self.validator.validate(trace)
                candidate_ids = {
                    candidate["candidate_id"]
                    for candidate in trace["candidate_set"]["candidates"]
                }
                evaluation_ids = {
                    evaluation["candidate_id"]
                    for evaluation in trace["ranking_evaluations"]
                }
                self.assertEqual(candidate_ids, evaluation_ids)
                self.assertEqual(
                    len(candidate_ids),
                    len(trace["candidate_set"]["candidates"]),
                )
                self.assertEqual(
                    len(evaluation_ids),
                    len(trace["ranking_evaluations"]),
                )
                self.assertEqual(
                    candidate_ids,
                    set(trace["candidate_set"]["input_candidate_ids"]),
                )
                self.assertEqual(
                    candidate_ids,
                    set(trace["candidate_set"]["canonical_candidate_ids"]),
                )
                expected_canonical = [
                    candidate["candidate_id"]
                    for candidate in sorted(
                        trace["candidate_set"]["candidates"],
                        key=lambda candidate: (
                            candidate["semantic_fingerprint"],
                            candidate["candidate_id"],
                        ),
                    )
                ]
                self.assertEqual(
                    trace["candidate_set"]["canonical_candidate_ids"],
                    expected_canonical,
                )
                if trace["selected_candidate_id"] is not None:
                    self.assertIn(trace["selected_candidate_id"], candidate_ids)
                    self.assertEqual(
                        set(trace["rejected_candidate_ids"]),
                        candidate_ids - {trace["selected_candidate_id"]},
                    )
                self.assertLessEqual(
                    set(trace["rejected_candidate_ids"]),
                    candidate_ids,
                )

    def test_contextual_selection_is_stable_under_input_permutation(self) -> None:
        first = self.fixtures["contextual-permutation-a.json"]
        second = self.fixtures["contextual-permutation-b.json"]
        self.assertNotEqual(
            first["candidate_set"]["input_candidate_ids"],
            second["candidate_set"]["input_candidate_ids"],
        )
        self.assertEqual(
            replay_selected_candidate(first),
            replay_selected_candidate(second),
        )
        self.assertEqual(
            replay_selected_candidate(first),
            "candidate:stone-of-fire",
        )
        self.assertEqual(
            first["replay"]["recorded_selected_semantic_fingerprint"],
            second["replay"]["recorded_selected_semantic_fingerprint"],
        )

    def test_strict_and_legacy_results_remain_distinct(self) -> None:
        strict = self.fixtures["strict-reject.json"]
        legacy = self.fixtures["legacy-permissive-unexpected-result.json"]
        self.assertEqual(strict["decision_status"], "Rejected")
        self.assertIsNone(strict["selected_candidate_id"])
        self.assertEqual(legacy["decision_status"], "Selected")
        self.assertEqual(
            replay_selected_candidate(legacy),
            legacy["selected_candidate_id"],
        )
        self.assertIn(
            "UnexpectedResult",
            {diagnostic["code"] for diagnostic in legacy["diagnostics"]},
        )
        self.assertEqual(
            set(legacy["mandatory_downstream_checks"]),
            {"type", "authority", "conservation", "identity"},
        )

    def test_legacy_input_position_is_rejected_for_contextual_policy(self) -> None:
        invalid = copy.deepcopy(
            self.fixtures["legacy-permissive-unexpected-result.json"]
        )
        invalid["policy"] = "ContextualDeterministic"
        self.assertTrue(list(self.validator.iter_errors(invalid)))

    def test_context_drift_is_not_silently_reselected(self) -> None:
        drift = self.fixtures["context-drift-unreproducible.json"]
        self.assertEqual(drift["decision_status"], "Unreproducible")
        self.assertIsNone(drift["selected_candidate_id"])
        self.assertEqual(drift["replay"]["replay_status"], "Incompatible")
        codes = {diagnostic["code"] for diagnostic in drift["diagnostics"]}
        self.assertIn("AmbiguityContextDrift", codes)
        self.assertIn("AmbiguityDecisionUnreproducible", codes)
        with self.assertRaises(ValueError):
            replay_selected_candidate(drift)

    def test_selected_status_requires_selected_candidate(self) -> None:
        invalid = copy.deepcopy(self.fixtures["contextual-permutation-a.json"])
        invalid["selected_candidate_id"] = None
        self.assertTrue(list(self.validator.iter_errors(invalid)))


if __name__ == "__main__":
    unittest.main()
