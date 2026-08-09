from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
FIXTURE = ROOT / "examples" / "compatibility" / "decision-cases.json"
REFERENCE = ROOT / "reference" / "compatibility.md"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def schema_validator(schema_name: str) -> Draft202012Validator:
    schema = load(SCHEMAS / schema_name)
    registry = Registry()
    for path in SCHEMAS.glob("*.schema.json"):
        document = load(path)
        registry = registry.with_resource(
            document["$id"], Resource.from_contents(document)
        )
    return Draft202012Validator(schema, registry=registry)


class CompatibilityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = load(FIXTURE)
        cls.validator = schema_validator("compatibility.schema.json")
        cls.reference = REFERENCE.read_text(encoding="utf-8")
        cls.decisions = {
            decision["profile"]["domain"]: decision
            for decision in cls.fixture["decisions"]
        }

    def test_fixture_validates_and_covers_required_domains(self) -> None:
        self.validator.validate(self.fixture)
        self.assertEqual(
            set(self.decisions),
            {
                "SpecVersion",
                "Schema",
                "SemanticRegistry",
                "RuntimeProfile",
                "LanguageAdapter",
                "SemanticFingerprint",
                "WorldIndex",
            },
        )
        self.assertEqual(
            {decision["result"]["status"] for decision in self.decisions.values()},
            {"Compatible", "Incompatible", "Undetermined"},
        )

    def test_domain_owner_and_rule_source_are_mandatory(self) -> None:
        broken = copy.deepcopy(self.fixture)
        del broken["decisions"][0]["profile"]["owner"]
        self.assertTrue(list(self.validator.iter_errors(broken)))

        broken = copy.deepcopy(self.fixture)
        del broken["decisions"][0]["profile"]["rule_source"]
        self.assertTrue(list(self.validator.iter_errors(broken)))

    def test_domain_namespace_is_extensible(self) -> None:
        extended = copy.deepcopy(self.fixture)
        extended["decisions"][0]["profile"]["domain"] = "FutureDomain"
        self.validator.validate(extended)

    def test_artifact_metadata_can_name_the_owning_profile(self) -> None:
        registry_artifact = load(
            ROOT / "examples" / "core-config" / "semantic-registry.json"
        )
        registry_artifact["metadata"]["compatibility"]["profile"] = copy.deepcopy(
            self.decisions["SemanticRegistry"]["profile"]
        )
        schema_validator("artifact-metadata.schema.json").validate(
            registry_artifact["metadata"]
        )

    def test_non_success_requires_diagnostic(self) -> None:
        broken = copy.deepcopy(self.fixture)
        fingerprint = next(
            decision
            for decision in broken["decisions"]
            if decision["profile"]["domain"] == "SemanticFingerprint"
        )
        fingerprint["result"]["diagnostic"] = None
        self.assertTrue(list(self.validator.iter_errors(broken)))

    def test_registry_hash_is_not_decisive_compatibility_evidence(self) -> None:
        registry = self.decisions["SemanticRegistry"]
        self.assertEqual(registry["result"]["status"], "Compatible")
        hash_evidence = next(
            evidence
            for evidence in registry["evidence"]
            if evidence["kind"] == "RegistryHashRecord"
        )
        self.assertFalse(hash_evidence["decisive"])

    def test_adapter_identity_is_not_external_language_tag(self) -> None:
        adapter = self.decisions["LanguageAdapter"]
        by_kind = {evidence["kind"]: evidence for evidence in adapter["evidence"]}
        self.assertTrue(by_kind["AdapterIdentity"]["decisive"])
        self.assertFalse(by_kind["ExternalLanguageTag"]["decisive"])
        self.assertEqual(adapter["result"]["status"], "Undetermined")

    def test_fingerprint_profile_mismatch_is_not_semantic_inequality(self) -> None:
        fingerprint = self.decisions["SemanticFingerprint"]
        self.assertEqual(fingerprint["result"]["status"], "Undetermined")
        self.assertEqual(
            fingerprint["result"]["diagnostic"],
            "SemanticFingerprintProfileMismatch",
        )
        self.assertIn(
            "SemanticFingerprint profile mismatch != semantic inequality proof",
            self.reference,
        )

    def test_world_index_revision_domains_remain_separate(self) -> None:
        world_index = self.decisions["WorldIndex"]
        declarations = world_index["producer"]["declarations"]
        self.assertNotEqual(
            declarations["world_index_revision"],
            declarations["source_world_revision"],
        )
        self.assertIn("index_schema_revision", declarations)

    def test_core_invariants_remain_normative(self) -> None:
        for invariant in (
            "shared metadata rules != shared compatibility algorithm",
            "hash mismatch alone != incompatibility",
            "WorldIndexRevision != WorldRevision",
            "adapter ID != external language tag",
            "SemanticFingerprint profile mismatch != semantic inequality proof",
        ):
            self.assertIn(invariant, self.reference)


if __name__ == "__main__":
    unittest.main()
