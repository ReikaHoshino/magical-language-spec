from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from src.artifacts.golden_parity import (
    FrozenArtifact,
    compare_checks,
    differential_compare,
    observe_frozen,
    run_manifest,
)
from src.artifacts.spell_instance import default_service as legacy_default_service

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "conformance" / "magical-program-golden-parity.json"
SCHEMA_PATH = ROOT / "schemas" / "golden-parity-manifest.schema.json"
GENERIC_PATH = ROOT / "examples" / "spell-instances" / "generic" / "GENERIC-001.json"
SA_ROOT = ROOT / "examples" / "spell-instances" / "success-arcana"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class GoldenParityTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.service = legacy_default_service()
        self.manifest = load(MANIFEST_PATH)

    def case(self, expectation_id: str):
        return next(
            item
            for item in self.manifest["cases"]
            if item["expectation_id"] == expectation_id
        )

    def positive_checks(self, case):
        return [
            *self.manifest["templates"]["positive-runtime"],
            *case["checks"],
        ]

    def test_manifest_schema_and_required_inventory(self) -> None:
        schema = load(SCHEMA_PATH)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(self.manifest)
        self.assertEqual(8, len(self.manifest["cases"]))
        self.assertEqual(
            25,
            sum(len(item["variants"]) for item in self.manifest["cases"]),
        )
        self.assertTrue(
            self.manifest["ownership_policy"]["executable_input_is_not_oracle"]
        )

    def test_external_manifest_executes_eight_base_and_all_25_negative_cases(self) -> None:
        result = run_manifest(ROOT, MANIFEST_PATH, service=self.service)
        self.assertEqual("PASS", result["status"], result)
        self.assertEqual(33, result["case_count"])
        self.assertEqual(0, result["failure_count"])

    def test_manifest_owns_all_mandatory_negative_neighbors(self) -> None:
        for number in range(1, 5):
            case = self.case(f"GOLDEN-SA-00{number}")
            bundle = load(SA_ROOT / f"SA-00{number}.json")
            external = {
                item["variant_id"]: item["checks"][0]["expected"]
                for item in case["variants"]
            }
            embedded = {
                item["variant_id"]: item["expected_diagnostic"]
                for item in bundle["variants"]
            }
            self.assertEqual(embedded, external)

    def test_embedded_expectation_change_alone_cannot_change_external_result(self) -> None:
        document = load(GENERIC_PATH)
        document["expected_outcome"] = {
            "evaluation_status": "Feasible",
            "runtime_status": "Committed",
            "diagnostic_codes": [],
            "final_invariants": {"Sigma": {"revision": "world:embedded-wrong"}},
            "replay_status": "Match",
            "expected_event_ids": ["event:embedded-wrong"],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "renamed-input.data"
            path.write_text(json.dumps(document), encoding="utf-8")
            observed = observe_frozen(self.service, FrozenArtifact.from_path(path))
        comparison = compare_checks(
            observed,
            self.positive_checks(self.case("GOLDEN-GENERIC-001")),
            expectation_id="embedded-expectation-is-not-oracle",
        )
        self.assertEqual("PASS", comparison["status"], comparison)

    def test_executable_and_embedded_drift_still_fails_external_golden(self) -> None:
        document = load(GENERIC_PATH)
        document["execution"]["parameters"][
            "result_world_revision"
        ] = "world:GENERIC-001:drift"
        document["expected_outcome"]["final_invariants"]["Sigma"][
            "revision"
        ] = "world:GENERIC-001:drift"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "self-consistent-drift.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            self.assertEqual("PASS", self.service.run_file(path)["status"])
            observed = observe_frozen(self.service, FrozenArtifact.from_path(path))
        comparison = compare_checks(
            observed,
            self.positive_checks(self.case("GOLDEN-GENERIC-001")),
            expectation_id="external-drift-detection",
        )
        self.assertEqual("FAIL", comparison["status"])
        self.assertEqual(
            ["/final_world/Sigma/revision"],
            [item["path"] for item in comparison["differences"]],
        )

    def test_renamed_filename_and_instance_id_do_not_change_semantic_golden(self) -> None:
        document = load(GENERIC_PATH)
        document["instance_id"] = "RENAMED-INDEPENDENT-GOLDEN"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unrelated-extension.data"
            path.write_text(json.dumps(document), encoding="utf-8")
            observed = observe_frozen(self.service, FrozenArtifact.from_path(path))
        comparison = compare_checks(
            observed,
            self.positive_checks(self.case("GOLDEN-GENERIC-001")),
            expectation_id="renamed-input",
        )
        self.assertEqual("PASS", comparison["status"], comparison)

    def test_event_winner_and_artifact_mismatches_are_field_level(self) -> None:
        case = self.case("GOLDEN-SA-003")
        observed = observe_frozen(
            self.service,
            FrozenArtifact.from_path(ROOT / case["input"]),
        )
        drifted = copy.deepcopy(observed)
        drifted["execution"]["history_event_ids"] = ["event:wrong"]
        artifact = drifted["final_world"]["Omega"]["evidence_store"][
            "artifacts"
        ]["artifact:sa003:observation"]
        artifact["artifact_id"] = "artifact:wrong"
        artifact["winner_hypothesis_id"] = "hypothesis:B"
        artifact["model"]["revision"] = "wrong"
        comparison = compare_checks(
            drifted,
            self.positive_checks(case),
            expectation_id="identity-and-artifact-drift",
        )
        paths = [item["path"] for item in comparison["differences"]]
        self.assertEqual("FAIL", comparison["status"])
        self.assertIn("/execution/history_event_ids", paths)
        self.assertIn(
            "/final_world/Omega/evidence_store/artifacts/"
            "artifact:sa003:observation/artifact_id",
            paths,
        )

    def test_old_and_new_runners_receive_one_frozen_snapshot(self) -> None:
        frozen = FrozenArtifact.from_path(GENERIC_PATH)

        def runner(snapshot: FrozenArtifact):
            return observe_frozen(self.service, snapshot)

        result = differential_compare(
            frozen,
            runner,
            runner,
            [
                {"path": "/evaluation/report/status", "mode": "exact"},
                {"path": "/execution/status", "mode": "exact"},
                {"path": "/replay/status", "mode": "exact"},
            ],
            comparison_id="same-frozen-input",
        )
        self.assertEqual("PASS", result["status"], result)
        self.assertEqual(
            result["old_observation"]["frozen_input"],
            result["new_observation"]["frozen_input"],
        )


if __name__ == "__main__":
    unittest.main()
