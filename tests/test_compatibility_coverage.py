from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
INVENTORY = ROOT / "conformance" / "compatibility-coverage.json"
DECISIONS = ROOT / "examples" / "compatibility" / "decision-cases.json"

REQUIRED_DOMAINS = {
    "SpecVersion",
    "Schema",
    "SemanticRegistry",
    "RuntimeProfile",
    "LanguageAdapter",
    "SemanticFingerprint",
    "WorldIndex",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def heading_slugs(text: str) -> set[str]:
    slugs: set[str] = set()
    for line in text.splitlines():
        if not line.startswith("#"):
            continue
        heading = line.lstrip("#").strip().lower()
        heading = re.sub(r"[^a-z0-9 _-]", "", heading)
        slugs.add(re.sub(r"[ _]+", "-", heading))
    return slugs


class CompatibilityCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inventory = load(INVENTORY)
        cls.decisions = load(DECISIONS)
        registry = Registry()
        for path in SCHEMAS.glob("*.schema.json"):
            document = load(path)
            registry = registry.with_resource(
                document["$id"], Resource.from_contents(document)
            )
        schema = load(SCHEMAS / "compatibility-coverage.schema.json")
        cls.validator = Draft202012Validator(schema, registry=registry)

    def test_inventory_is_schema_valid_and_versioned_for_v012(self) -> None:
        self.validator.validate(self.inventory)
        self.assertEqual("v0.12.0", self.inventory["release_target"])

    def test_required_domains_have_exact_owned_profiles_and_fixture_evidence(self) -> None:
        profiles = {
            item["domain"]: item for item in self.inventory["required_domains"]
        }
        fixture_profiles = {
            item["profile"]["domain"]: item["profile"]
            for item in self.decisions["decisions"]
        }
        self.assertEqual(REQUIRED_DOMAINS, set(profiles))
        self.assertEqual(REQUIRED_DOMAINS, set(fixture_profiles))
        for domain, profile in profiles.items():
            self.assertEqual(profile["profile_id"], fixture_profiles[domain]["profile_id"])
            self.assertEqual(
                profile["profile_revision"],
                fixture_profiles[domain]["profile_revision"],
            )
            self.assertTrue(profile["owner"])
            document, _, heading = profile["rule_source"].partition("#")
            reference = (ROOT / document).read_text(encoding="utf-8")
            self.assertIn(heading, heading_slugs(reference))

    def test_required_reference_path_artifacts_have_no_unowned_domain(self) -> None:
        artifact_kinds = [item["artifact_kind"] for item in self.inventory["artifacts"]]
        self.assertEqual(len(artifact_kinds), len(set(artifact_kinds)))
        covered = {
            domain
            for artifact in self.inventory["artifacts"]
            for domain in artifact["domains"]
        }
        self.assertEqual(REQUIRED_DOMAINS, covered)
        self.assertTrue(
            {
                "NSR",
                "SemanticRegistry",
                "WorldIndex",
                "RuntimeProfile",
                "LanguageAdapterLat",
                "SemanticFingerprintV1",
                "FeasibilityReport",
                "RuntimeExecutionTrace",
                "ConformanceManifest",
            }.issubset(artifact_kinds)
        )


if __name__ == "__main__":
    unittest.main()
