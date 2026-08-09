from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from src.compatibility import (
    AdmissionStatus,
    CompatibilityAdmissionError,
    admit_compatibility_decisions,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "compatibility" / "decision-cases.json"


class CompatibilityAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.decisions = {
            decision["profile"]["domain"]: decision
            for decision in payload["decisions"]
        }

    def test_all_required_compatible_domains_are_admitted(self) -> None:
        result = admit_compatibility_decisions(
            [self.decisions["SpecVersion"], self.decisions["SemanticRegistry"]],
            required_domains=["SpecVersion", "SemanticRegistry"],
        )
        self.assertEqual(AdmissionStatus.ALLOWED, result.status)
        self.assertTrue(result.admitted)
        self.assertEqual((), result.blocking_domains)
        self.assertEqual((), result.reason_codes)

    def test_incompatible_domain_denies_admission(self) -> None:
        result = admit_compatibility_decisions(
            [self.decisions["SpecVersion"], self.decisions["Schema"]],
            required_domains=["SpecVersion", "Schema"],
        )
        self.assertEqual(AdmissionStatus.DENIED, result.status)
        self.assertFalse(result.admitted)
        self.assertEqual(("Schema",), result.blocking_domains)
        self.assertIn("UnsupportedSchemaVersion", result.reason_codes)

    def test_undetermined_domain_fails_closed(self) -> None:
        result = admit_compatibility_decisions(
            [self.decisions["SpecVersion"], self.decisions["RuntimeProfile"]],
            required_domains=["SpecVersion", "RuntimeProfile"],
        )
        self.assertEqual(AdmissionStatus.INDETERMINATE, result.status)
        self.assertFalse(result.admitted)
        self.assertEqual(("RuntimeProfile",), result.blocking_domains)
        self.assertIn("RequiredRuntimeEvidenceMissing", result.reason_codes)

    def test_missing_required_domain_is_indeterminate_not_compatible(self) -> None:
        result = admit_compatibility_decisions(
            [self.decisions["SpecVersion"]],
            required_domains=["SpecVersion", "WorldIndex"],
        )
        self.assertEqual(AdmissionStatus.INDETERMINATE, result.status)
        self.assertFalse(result.admitted)
        self.assertEqual(("WorldIndex",), result.blocking_domains)
        self.assertEqual(
            ("CompatibilityDecisionMissing:WorldIndex",),
            result.reason_codes,
        )

    def test_incompatible_precedes_indeterminate_for_aggregate_status(self) -> None:
        result = admit_compatibility_decisions(
            [
                self.decisions["Schema"],
                self.decisions["RuntimeProfile"],
            ],
            required_domains=["Schema", "RuntimeProfile"],
        )
        self.assertEqual(AdmissionStatus.DENIED, result.status)
        self.assertFalse(result.admitted)
        self.assertEqual(("Schema", "RuntimeProfile"), result.blocking_domains)

    def test_aggregate_gate_does_not_invent_revision_ordering(self) -> None:
        spec = copy.deepcopy(self.decisions["SpecVersion"])
        registry = copy.deepcopy(self.decisions["SemanticRegistry"])
        spec["producer"]["revision"] = "zeta-not-newer"
        registry["producer"]["revision"] = "000-not-older"

        result = admit_compatibility_decisions(
            [spec, registry],
            required_domains=["SpecVersion", "SemanticRegistry"],
        )
        self.assertEqual(AdmissionStatus.ALLOWED, result.status)
        self.assertTrue(result.admitted)

    def test_result_is_admission_only_and_never_grants_authority(self) -> None:
        result = admit_compatibility_decisions(
            [self.decisions["SpecVersion"], self.decisions["SemanticRegistry"]],
            required_domains=["SpecVersion", "SemanticRegistry"],
        ).to_dict()
        self.assertNotIn("capability", result)
        self.assertNotIn("lease", result)
        self.assertNotIn("authority", result)
        self.assertTrue(result["admitted"])

    def test_duplicate_domain_decisions_are_rejected_as_ambiguous(self) -> None:
        with self.assertRaisesRegex(
            CompatibilityAdmissionError,
            "multiple compatibility decisions",
        ):
            admit_compatibility_decisions(
                [self.decisions["SpecVersion"], copy.deepcopy(self.decisions["SpecVersion"])],
                required_domains=["SpecVersion"],
            )

    def test_empty_or_duplicate_required_domain_list_is_rejected(self) -> None:
        with self.assertRaisesRegex(CompatibilityAdmissionError, "must not be empty"):
            admit_compatibility_decisions([], required_domains=[])
        with self.assertRaisesRegex(CompatibilityAdmissionError, "contains duplicates"):
            admit_compatibility_decisions(
                [self.decisions["SpecVersion"]],
                required_domains=["SpecVersion", "SpecVersion"],
            )


if __name__ == "__main__":
    unittest.main()
