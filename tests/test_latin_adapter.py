#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from tools.latin_adapter import normalize_with_adapter
from tools.semantic_fingerprint import semantic_fingerprint_v1

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
LATIN_FIXTURES = ROOT / "examples" / "latin-adapter"
CANONICAL_SOURCE = "Calorem ab aqua ad aerem transfer."


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def schema_validator(name: str) -> Draft202012Validator:
    registry = Registry()
    for path in SCHEMAS.glob("*.schema.json"):
        document = load(path)
        registry = registry.with_resource(
            document["$id"], Resource.from_contents(document)
        )
    return Draft202012Validator(load(SCHEMAS / name), registry=registry)


def diagnostic_codes(result: dict) -> list[str]:
    return [diagnostic["code"] for diagnostic in result["diagnostics"]]


class LatinAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.nsr_validator = schema_validator("nsr.schema.json")
        cls.canonical_fixture = load(
            LATIN_FIXTURES / "thermal-transfer-normalization.json"
        )
        cls.ambiguity_fixture = load(
            LATIN_FIXTURES / "aquae-strict-reject.json"
        )

    def test_lat_001_reaches_expected_nsr_deterministically(self) -> None:
        first = normalize_with_adapter("lat", CANONICAL_SOURCE)
        second = normalize_with_adapter("lat", CANONICAL_SOURCE)
        self.assertEqual(first, second)
        self.assertEqual([], first["diagnostics"])

        candidate_set = first["normalization_candidate_set"]
        self.assertEqual("Selected", candidate_set["decision_status"])
        self.assertIsNotNone(candidate_set["selected_candidate_id"])
        self.assertEqual(1, len(candidate_set["candidates"]))

        nsr = candidate_set["candidates"][0]["nsr"]
        self.nsr_validator.validate(nsr)
        roles = {role["role"]: role["value"] for role in nsr["roles"]}
        self.assertEqual("Energy", roles["Patient"]["semantic_kind"])
        self.assertEqual("Thermal", roles["Patient"]["mode"])
        self.assertEqual(
            {"kind": "Symbolic", "symbol": "water"},
            roles["Source"]["selector"],
        )
        self.assertEqual(
            {"kind": "Symbolic", "symbol": "air"},
            roles["Goal"]["selector"],
        )
        self.assertEqual("Unknown", roles["Quantity"]["kind"])
        self.assertEqual(
            "MissingSurfaceArgument", roles["Quantity"]["reason"]
        )
        self.assertEqual(
            semantic_fingerprint_v1(nsr), nsr["semantic_fingerprint"]
        )

        fixture_nsr = self.canonical_fixture[
            "normalization_candidate_set"
        ]["candidates"][0]["nsr"]
        self.assertEqual(
            fixture_nsr["semantic_fingerprint"], nsr["semantic_fingerprint"]
        )

    def test_source_morphology_and_frame_evidence_remain_traceable(self) -> None:
        result = normalize_with_adapter("lat", CANONICAL_SOURCE)
        tokens = {token["surface"]: token for token in result["tokens"]}
        aqua = tokens["aqua"]
        self.assertEqual(
            ["lat:aqua:abl-sg", "lat:aqua:nom-sg"],
            aqua["morphology_candidate_ids"],
        )
        self.assertEqual(
            ["lat:aqua:abl-sg"],
            aqua["selected_morphology_candidate_ids"],
        )
        self.assertEqual(
            {"start": 11, "end": 15, "exact": True},
            aqua["source_span"],
        )
        self.assertTrue(
            {"frame-patient", "frame-source", "frame-goal"}
            <= {
                evidence["evidence_id"]
                for evidence in result["evidence"]
            }
        )
        self.assertTrue(
            all(
                proposal["status"] == "proposal"
                for proposal in result["role_proposals"]
            )
        )
        serialized = json.dumps(result, ensure_ascii=False).lower()
        self.assertNotIn('"entity_id"', serialized)
        self.assertNotIn('"capability"', serialized)
        self.assertNotIn('"authority"', serialized)

    def test_aquae_candidates_are_preserved_and_strict_rejects(self) -> None:
        fixture = self.ambiguity_fixture
        result = normalize_with_adapter(
            "lat",
            fixture["source"],
            ambiguity_policy=fixture["ambiguity_policy"],
        )
        expected = fixture["expected"]
        self.assertEqual(
            expected["morphology_candidate_ids"],
            result["tokens"][0]["morphology_candidate_ids"],
        )
        self.assertEqual(
            expected["decision_status"],
            result["normalization_candidate_set"]["decision_status"],
        )
        self.assertEqual(
            expected["selected_candidate_id"],
            result["normalization_candidate_set"]["selected_candidate_id"],
        )
        self.assertEqual(expected["diagnostic_codes"], diagnostic_codes(result))
        self.assertEqual(
            expected["morphology_candidate_ids"],
            result["unresolved_ambiguity"]["morphology"][0][
                "morphology_candidate_ids"
            ],
        )

    def test_interactive_policy_preserves_ambiguity_without_guessing(self) -> None:
        result = normalize_with_adapter(
            "lat", "aquae", ambiguity_policy="InteractiveResolve"
        )
        self.assertEqual(
            "PendingInteraction",
            result["normalization_candidate_set"]["decision_status"],
        )
        self.assertIsNone(
            result["normalization_candidate_set"]["selected_candidate_id"]
        )
        self.assertIn("AmbiguityInteractionRequired", diagnostic_codes(result))

    def test_profile_owned_policies_do_not_invent_a_selection_profile(self) -> None:
        for policy in ("ContextualDeterministic", "LegacyPermissive"):
            with self.subTest(policy=policy):
                result = normalize_with_adapter(
                    "lat", "aquae", ambiguity_policy=policy
                )
                self.assertEqual(
                    "Unreproducible",
                    result["normalization_candidate_set"][
                        "decision_status"
                    ],
                )
                self.assertIsNone(
                    result["normalization_candidate_set"][
                        "selected_candidate_id"
                    ]
                )
                self.assertIn(
                    "AmbiguityDecisionUnreproducible",
                    diagnostic_codes(result),
                )

    def test_missing_lexeme_and_incomplete_morphology_are_diagnostic(self) -> None:
        missing = normalize_with_adapter("lat", "ignotum")
        self.assertEqual(
            ["LexiconEntryMissing", "NormalizationFailed"],
            diagnostic_codes(missing),
        )

        incomplete = normalize_with_adapter("lat", "canalis")
        self.assertEqual(
            ["MorphologicalAnalysisIncomplete", "NormalizationFailed"],
            diagnostic_codes(incomplete),
        )

    def test_source_normalization_failure_produces_no_candidate(self) -> None:
        result = normalize_with_adapter("lat", b"\xff")
        self.assertEqual("Rejected", result["source_normalization"]["status"])
        self.assertEqual(
            ["InvalidUTF8", "NormalizationFailed"], diagnostic_codes(result)
        )
        self.assertEqual(
            [], result["normalization_candidate_set"]["candidates"]
        )

    def test_dispatch_is_explicit_and_does_not_detect_language(self) -> None:
        unavailable = normalize_with_adapter("eng", CANONICAL_SOURCE)
        self.assertEqual(
            ["LanguageAdapterUnavailable"], diagnostic_codes(unavailable)
        )
        self.assertEqual(
            "Rejected",
            unavailable["normalization_candidate_set"]["decision_status"],
        )

    def test_semantic_role_vocabulary_is_shared(self) -> None:
        roles = load(SCHEMAS / "semantic-roles.schema.json")["$defs"][
            "semanticRole"
        ]["enum"]
        self.assertEqual(len(roles), len(set(roles)))

        nsr_schema = load(SCHEMAS / "nsr.schema.json")
        lexicon_schema = load(SCHEMAS / "latin-lexicon.schema.json")
        expected_ref = "semantic-roles.schema.json#/$defs/semanticRole"
        self.assertEqual(
            expected_ref,
            nsr_schema["$defs"]["role"]["properties"]["role"]["$ref"],
        )
        self.assertEqual(
            expected_ref,
            lexicon_schema["$defs"]["argumentSlot"]["properties"]["role"][
                "$ref"
            ],
        )

        invalid_nsr = normalize_with_adapter(
            "lat", CANONICAL_SOURCE
        )["normalization_candidate_set"]["candidates"][0]["nsr"]
        invalid_nsr["roles"][0]["role"] = "Action"
        self.assertTrue(list(self.nsr_validator.iter_errors(invalid_nsr)))


if __name__ == "__main__":
    unittest.main()
