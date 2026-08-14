from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from src.runtime import ExecutionAdmissionError, ExecutionAdmissionRuntime


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples" / "execution-admission"
SCHEMA = ROOT / "schemas" / "execution-admission.schema.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class ExecutionAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = ExecutionAdmissionRuntime()
        cls.incremental = load(FIXTURES / "incremental-partial-commit.json")
        cls.preflight = load(FIXTURES / "whole-plan-preflight-rejection.json")
        cls.validator = Draft202012Validator(load(SCHEMA))

    def test_paired_fixtures_validate(self) -> None:
        self.validator.validate(self.incremental)
        self.validator.validate(self.preflight)

    def test_incremental_failure_preserves_prior_commit(self) -> None:
        trace = self.runtime.execute(self.incremental)

        self.assertEqual(trace, self.incremental["expected_trace"])
        self.assertEqual(trace["diagnostic"]["phase"], "AfterPartialCommit")
        self.assertEqual(trace["final_world"]["destination_mass_kg"], 40.0)
        self.assertFalse(trace["prior_commits_rolled_back"])
        self.assertFalse(trace["final_world"]["constraint_active"])
        self.assertTrue(trace["final_world"]["gravity_applies"])
        self.assertEqual(
            trace["final_world"]["source_mass_kg"]
            + trace["final_world"]["destination_mass_kg"],
            trace["final_world"]["accounted_total_mass_kg"],
        )

    def test_whole_plan_preflight_rejects_before_first_effect(self) -> None:
        trace = self.runtime.execute(self.preflight)

        self.assertEqual(trace, self.preflight["expected_trace"])
        self.assertEqual(trace["diagnostic"]["phase"], "BeforeFirstEffect")
        self.assertEqual(trace["committed_group_ids"], [])
        self.assertEqual(trace["history_event_ids"], [])
        self.assertEqual(trace["final_world"], self.preflight["initial_world"])
        self.assertFalse(trace["preflight_created_reservation"])
        self.assertFalse(trace["preflight_granted_authority"])

    def test_mandatory_local_authority_guard_cannot_be_bypassed(self) -> None:
        case = copy.deepcopy(self.incremental)
        case["initial_world"]["capability_active"] = False

        trace = self.runtime.execute(case)

        self.assertEqual(trace["diagnostic"]["code"], "LocalAdmissionRejected")
        self.assertEqual(trace["diagnostic"]["failed_guard"], "Capability")
        self.assertEqual(trace["diagnostic"]["phase"], "BeforeFirstEffect")
        self.assertEqual(trace["committed_group_ids"], [])
        self.assertEqual(trace["final_world"], case["initial_world"])

    def test_unsupported_policy_fails_closed(self) -> None:
        case = copy.deepcopy(self.incremental)
        case["policy"]["mode"] = "BestEffort"

        with self.assertRaises(ExecutionAdmissionError):
            self.runtime.execute(case)
        self.assertTrue(list(self.validator.iter_errors(case)))

    def test_missing_local_guard_fails_closed(self) -> None:
        case = copy.deepcopy(self.incremental)
        case["plan"]["atomic_groups"][0]["local_guards"].remove("Lease")

        with self.assertRaises(ExecutionAdmissionError):
            self.runtime.execute(case)

    def test_preflight_cannot_claim_reservation_or_authority(self) -> None:
        for field in (
            "creates_reservation",
            "grants_authority",
            "guarantees_runtime_completion",
        ):
            case = copy.deepcopy(self.preflight)
            case["policy"]["assessment_scope"][field] = True
            with self.subTest(field=field):
                with self.assertRaises(ExecutionAdmissionError):
                    self.runtime.execute(case)
                self.assertTrue(list(self.validator.iter_errors(case)))

    def test_policy_provenance_owner_mismatch_fails_closed(self) -> None:
        case = copy.deepcopy(self.incremental)
        case["policy"]["provenance"]["owner"] = "SourceContract"

        with self.assertRaises(ExecutionAdmissionError):
            self.runtime.execute(case)

    def test_replay_is_deterministic_and_not_rewind(self) -> None:
        for case in (self.incremental, self.preflight):
            expected = self.runtime.execute(case)
            replay = self.runtime.replay(case, expected)
            self.assertEqual(replay["status"], "Match")
            self.assertFalse(replay["replay_is_rewind"])

    def test_only_existing_mki_operations_are_used(self) -> None:
        used = {
            operation
            for case in (self.incremental, self.preflight)
            for group in case["plan"]["atomic_groups"]
            for operation in group["mki_operations"]
        }
        self.assertEqual(used, {"TRANSFER", "CONSTRAIN"})


if __name__ == "__main__":
    unittest.main()
