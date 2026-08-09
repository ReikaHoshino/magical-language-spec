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
    ROOT / "examples" / "core-config" / "semantic-registry-domain-contracts.json"
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def registry_validator() -> Draft202012Validator:
    registry = Registry()
    for path in SCHEMAS.glob("*.schema.json"):
        document = load(path)
        registry = registry.with_resource(
            document["$id"], Resource.from_contents(document)
        )
    return Draft202012Validator(
        load(SCHEMAS / "semantic-registry.schema.json"),
        registry=registry,
    )


class SemanticRegistrySchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = load(FIXTURE)
        cls.validator = registry_validator()

    def assert_rejected(self, instance: dict) -> None:
        self.assertTrue(
            list(self.validator.iter_errors(instance)),
            "invalid registry fixture was accepted",
        )

    def test_representative_contracts_validate(self) -> None:
        self.validator.validate(self.fixture)
        self.assertEqual(
            set(self.fixture["namespaces"]),
            {
                "semantic_kinds",
                "species",
                "structure_schemas",
                "reaction_rules",
                "kinetic_models",
                "reaction_pathways",
                "catalyst_models",
                "inhibitor_models",
                "equilibrium_models",
                "activity_models",
                "observer_models",
                "controller_models",
                "conservation_ledgers",
            },
        )
        for entries in self.fixture["namespaces"].values():
            self.assertTrue(entries)
            self.assertTrue(entries[0]["contract"])

    def test_required_entry_definitions_are_published(self) -> None:
        definitions = load(SCHEMAS / "semantic-registry.schema.json")["$defs"]
        self.assertTrue(
            {
                "SemanticEntry",
                "SpeciesEntry",
                "StructureSchemaEntry",
                "ReactionRuleEntry",
                "KineticModelEntry",
                "ReactionPathwayEntry",
                "CatalystModelEntry",
                "InhibitorModelEntry",
                "ActivityModelEntry",
                "EquilibriumModelEntry",
                "ObserverModelEntry",
                "ControllerModelEntry",
                "ConservationLedgerEntry",
            }.issubset(definitions)
        )

    def test_missing_domain_required_field_is_rejected(self) -> None:
        broken = copy.deepcopy(self.fixture)
        del broken["namespaces"]["semantic_kinds"][0]["contract"]["traits"]
        self.assert_rejected(broken)

    def test_cross_domain_contract_shape_is_rejected(self) -> None:
        broken = copy.deepcopy(self.fixture)
        broken["namespaces"]["kinetic_models"][0]["contract"] = copy.deepcopy(
            broken["namespaces"]["reaction_rules"][0]["contract"]
        )
        self.assert_rejected(broken)

    def test_reaction_rule_pathway_and_rate_law_remain_distinct(self) -> None:
        broken = copy.deepcopy(self.fixture)
        broken["namespaces"]["reaction_pathways"][0]["contract"] = copy.deepcopy(
            broken["namespaces"]["reaction_rules"][0]["contract"]
        )
        self.assert_rejected(broken)

        broken = copy.deepcopy(self.fixture)
        broken["namespaces"]["kinetic_models"][0]["contract"]["rate_law"] = (
            copy.deepcopy(
                broken["namespaces"]["reaction_pathways"][0]["contract"]
            )
        )
        self.assert_rejected(broken)

    def test_inhibitor_unspecified_contract_uses_explicit_extension(self) -> None:
        broken = copy.deepcopy(self.fixture)
        broken["namespaces"]["inhibitor_models"][0]["contract"] = {}
        self.assert_rejected(broken)

    def test_unresolved_hashes_are_scoped_without_fake_digest_fields(self) -> None:
        expected = (
            (self.fixture["metadata"]["content_hash"], "artifact-content"),
            (self.fixture["registry_hash"], "registry-contract-set"),
        )
        for hash_value, scope in expected:
            self.assertEqual(hash_value["scope"], scope)
            self.assertEqual(hash_value["status"], "unresolved")
            self.assertTrue(hash_value["reason"])
            self.assertFalse(
                {"algorithm", "value", "canonicalization_profile"} & set(hash_value)
            )


if __name__ == "__main__":
    unittest.main()
