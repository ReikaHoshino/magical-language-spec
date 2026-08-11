from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from src.compatibility import (
    CompatibilityEvolutionError,
    execute_migration,
    select_migration,
    validate_evolution_policy,
    validate_release_change,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
FIXTURE = ROOT / "examples" / "compatibility" / "evolution-policy-v1.json"
REFERENCE = ROOT / "reference" / "versioning-and-migration.md"


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


class CompatibilityEvolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load(FIXTURE)
        cls.validator = schema_validator("compatibility-evolution.schema.json")
        cls.reference = REFERENCE.read_text(encoding="utf-8")
        cls.migration = cls.policy["migrations"][0]

    def assert_code(self, expected: str, operation) -> None:
        with self.assertRaises(CompatibilityEvolutionError) as caught:
            operation()
        self.assertEqual(expected, caught.exception.code)

    def transform_key(self) -> tuple[str, str]:
        return (
            self.migration["transformation"]["transformation_id"],
            self.migration["transformation"]["transformation_revision"],
        )

    def target_profile(self) -> dict[str, str]:
        return {
            "profile_id": self.migration["target_contract"]["profile_id"],
            "profile_revision": self.migration["target_contract"]["profile_revision"],
            "domain": self.migration["domain"],
        }

    def test_released_policy_is_schema_valid_and_semantically_consistent(self) -> None:
        self.validator.validate(self.policy)
        validate_evolution_policy(self.policy)
        self.assertEqual("released", self.policy["policy_status"])
        self.assertEqual(1, self.policy["stable_major"])

    def test_minor_additive_change_is_allowed_without_becoming_compatibility_proof(self) -> None:
        validate_release_change(
            "1.0.0",
            "1.1.0",
            ["Additive", "OptInProfile"],
            stable_major=1,
        )
        self.assertIn("same major != automatic compatibility", self.reference)

    def test_patch_reinterpretation_is_forbidden(self) -> None:
        self.assert_code(
            "StableContractChangeWithinMajor",
            lambda: validate_release_change(
                "1.0.0",
                "1.0.1",
                ["RequiredCoreReinterpretation"],
                stable_major=1,
            ),
        )

    def test_same_major_deprecation_removal_is_forbidden(self) -> None:
        broken = copy.deepcopy(self.policy)
        broken["deprecations"][0]["earliest_removal_major"] = 1
        self.assert_code(
            "StableContractRemovalWithinMajor",
            lambda: validate_evolution_policy(broken),
        )

    def test_explicit_migration_succeeds_only_after_both_postconditions(self) -> None:
        selected = select_migration(
            self.policy,
            domain="Schema",
            source_contract=self.migration["source_contract"],
            target_contract=self.migration["target_contract"],
        )

        def transform(artifact):
            artifact["schema_version"] = "2"
            return artifact

        def validate_target(artifact):
            return artifact.get("schema_version") == "2"

        def decide(artifact):
            return {
                "decision_id": "compat:post-migration:target-v2",
                "profile": {
                    "profile_id": "compat-profile:schema:core-config",
                    "profile_revision": "2",
                    "domain": "Schema",
                },
                "result": {"status": "Compatible"},
            }

        result = execute_migration(
            selected,
            {"schema_version": "1", "payload": {"preserved": True}},
            transformations={
                ("transform:compatibility-envelope:1-to-2", "1"): transform
            },
            schema_validator=validate_target,
            compatibility_evaluator=decide,
        )
        self.assertEqual("2", result.output["schema_version"])
        self.assertEqual("1", result.transformation_revision)
        self.assertEqual(
            ("SchemaValidation", "CompatibilityReevaluation"),
            result.postconditions,
        )
        self.assertNotIn("authority", result.to_dict())
        self.assertNotIn("lease", result.to_dict())
        self.assertNotIn("trust", result.to_dict())
        self.assertNotIn("admission", result.to_dict())
        self.assertNotIn("semantic_fingerprint", result.to_dict())

    def test_missing_migration_path_fails_closed(self) -> None:
        missing_target = copy.deepcopy(self.migration["target_contract"])
        missing_target["contract_revision"] = "3"
        self.assert_code(
            "MigrationPathMissing",
            lambda: select_migration(
                self.policy,
                domain="Schema",
                source_contract=self.migration["source_contract"],
                target_contract=missing_target,
            ),
        )

    def test_ambiguous_migration_path_fails_closed(self) -> None:
        ambiguous = copy.deepcopy(self.policy)
        duplicate = copy.deepcopy(self.migration)
        duplicate["migration_id"] = "migration:compatibility-envelope:1-to-2:alternate"
        duplicate["transformation"]["transformation_id"] = (
            "transform:compatibility-envelope:1-to-2:alternate"
        )
        ambiguous["migrations"].append(duplicate)
        self.assert_code(
            "MigrationPathAmbiguous",
            lambda: select_migration(
                ambiguous,
                domain="Schema",
                source_contract=self.migration["source_contract"],
                target_contract=self.migration["target_contract"],
            ),
        )

    def test_invalid_migrated_output_fails_closed(self) -> None:
        transform_key = self.transform_key()
        target_profile = self.target_profile()
        self.assert_code(
            "MigratedArtifactInvalid",
            lambda: execute_migration(
                self.migration,
                {"schema_version": "1"},
                transformations={transform_key: lambda artifact: {"schema_version": "2"}},
                schema_validator=lambda artifact: False,
                compatibility_evaluator=lambda artifact: {
                    "decision_id": "unreached",
                    "profile": target_profile,
                    "result": {"status": "Compatible"},
                },
            ),
        )

    def test_post_migration_incompatibility_fails_closed(self) -> None:
        transform_key = self.transform_key()
        target_profile = self.target_profile()
        self.assert_code(
            "PostMigrationIncompatible",
            lambda: execute_migration(
                self.migration,
                {"schema_version": "1"},
                transformations={transform_key: lambda artifact: {"schema_version": "2"}},
                schema_validator=lambda artifact: True,
                compatibility_evaluator=lambda artifact: {
                    "decision_id": "compat:post-migration:denied",
                    "profile": target_profile,
                    "result": {"status": "Incompatible"},
                },
            ),
        )

    def test_wrong_target_profile_fails_closed(self) -> None:
        transform_key = self.transform_key()
        target_profile = self.target_profile()
        self.assert_code(
            "PostMigrationCompatibilityProfileMismatch",
            lambda: execute_migration(
                self.migration,
                {"schema_version": "1"},
                transformations={transform_key: lambda artifact: {"schema_version": "2"}},
                schema_validator=lambda artifact: True,
                compatibility_evaluator=lambda artifact: {
                    "decision_id": "compat:post-migration:wrong-profile",
                    "profile": {
                        **target_profile,
                        "profile_revision": "wrong-revision",
                    },
                    "result": {"status": "Compatible"},
                },
            ),
        )

    def test_wildcards_hashes_and_fingerprints_do_not_select_migration(self) -> None:
        wildcard = copy.deepcopy(self.policy)
        wildcard["migrations"][0]["source_contract"]["contract_revision"] = "1.*"
        self.assertTrue(list(self.validator.iter_errors(wildcard)))
        self.assert_code(
            "MigrationContractReferenceNotExact",
            lambda: validate_evolution_policy(wildcard),
        )
        for invariant in (
            "version ordering != compatibility proof",
            "explicit migration != semantic equality proof",
            "SemanticFingerprint != artifact content_hash",
        ):
            self.assertIn(invariant, self.reference)


if __name__ == "__main__":
    unittest.main()
