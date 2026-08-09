from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping


_RELEASE_VERSION = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_SAME_MAJOR_PATCH_CHANGES = {
    "NonReinterpretingCorrection",
    "Documentation",
    "CompatibleSecurityHardening",
}
_SAME_MAJOR_MINOR_CHANGES = _SAME_MAJOR_PATCH_CHANGES | {
    "Additive",
    "Deprecation",
    "OptInProfile",
}
_FORBIDDEN_SAME_MAJOR_CHANGES = {
    "RequiredCoreReinterpretation",
    "RequiredCoreRemoval",
    "StablePublicReinterpretation",
    "StablePublicRemoval",
}


class CompatibilityEvolutionError(ValueError):
    """Fail-closed diagnostic for release evolution or explicit migration."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class MigrationExecutionResult:
    migration_id: str
    transformation_id: str
    transformation_revision: str
    output: Mapping[str, Any]
    postconditions: tuple[str, ...]
    compatibility_decision_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "migration_id": self.migration_id,
            "transformation_id": self.transformation_id,
            "transformation_revision": self.transformation_revision,
            "output": copy.deepcopy(dict(self.output)),
            "postconditions": list(self.postconditions),
            "compatibility_decision_id": self.compatibility_decision_id,
        }


def _parse_release_version(value: str) -> tuple[int, int, int]:
    if not isinstance(value, str):
        raise CompatibilityEvolutionError(
            "ReleaseVersionInvalid", "release version must be a string"
        )
    match = _RELEASE_VERSION.fullmatch(value)
    if match is None:
        raise CompatibilityEvolutionError(
            "ReleaseVersionInvalid",
            f"release version must use MAJOR.MINOR.PATCH: {value!r}",
        )
    return tuple(int(part) for part in match.groups())


def validate_release_change(
    previous: str,
    current: str,
    changes: Iterable[str],
    *,
    stable_major: int,
) -> None:
    """Validate v1.x change classes without deciding artifact compatibility."""

    before = _parse_release_version(previous)
    after = _parse_release_version(current)
    if after <= before:
        raise CompatibilityEvolutionError(
            "ReleaseVersionNotIncreasing",
            f"release version must increase: {previous!r} -> {current!r}",
        )
    if before[0] != stable_major:
        raise CompatibilityEvolutionError(
            "StableMajorMismatch",
            f"source release major {before[0]} does not match policy major {stable_major}",
        )

    change_set = set(changes)
    if not change_set:
        raise CompatibilityEvolutionError(
            "ReleaseChangeEvidenceMissing", "at least one explicit change class is required"
        )

    if after[0] != before[0]:
        return

    forbidden = sorted(change_set & _FORBIDDEN_SAME_MAJOR_CHANGES)
    if forbidden:
        raise CompatibilityEvolutionError(
            "StableContractChangeWithinMajor",
            "required-core/stable-public reinterpretation or removal requires a new major: "
            + ", ".join(forbidden),
        )

    if after[1] == before[1]:
        unsupported = sorted(change_set - _SAME_MAJOR_PATCH_CHANGES)
        if unsupported:
            raise CompatibilityEvolutionError(
                "PatchChangeNotCompatible",
                "patch release contains a non-patch change class: " + ", ".join(unsupported),
            )
        return

    unsupported = sorted(change_set - _SAME_MAJOR_MINOR_CHANGES)
    if unsupported:
        raise CompatibilityEvolutionError(
            "MinorChangeNotCompatible",
            "minor release contains a non-additive/non-opt-in change class: "
            + ", ".join(unsupported),
        )


def _contract_key(value: Mapping[str, Any]) -> tuple[str, str, str]:
    try:
        parts = (
            value["contract_kind"],
            value["contract_id"],
            value["contract_revision"],
        )
    except (KeyError, TypeError) as exc:
        raise CompatibilityEvolutionError(
            "MigrationContractReferenceInvalid",
            "migration contract reference requires kind, id, and revision",
        ) from exc
    if any(not isinstance(part, str) or not part for part in parts):
        raise CompatibilityEvolutionError(
            "MigrationContractReferenceInvalid",
            "migration contract reference fields must be non-empty strings",
        )
    if any("*" in part or "?" in part for part in parts):
        raise CompatibilityEvolutionError(
            "MigrationContractReferenceNotExact",
            "migration contract references cannot contain wildcard tokens",
        )
    return parts


def _migration_contract_key(
    value: Mapping[str, Any],
) -> tuple[str, str, str, str, str]:
    contract_key = _contract_key(value)
    try:
        profile_parts = (value["profile_id"], value["profile_revision"])
    except (KeyError, TypeError) as exc:
        raise CompatibilityEvolutionError(
            "MigrationContractReferenceInvalid",
            "migration contract reference requires exact profile identity and revision",
        ) from exc
    if any(not isinstance(part, str) or not part for part in profile_parts):
        raise CompatibilityEvolutionError(
            "MigrationContractReferenceInvalid",
            "migration profile identity and revision must be non-empty strings",
        )
    if any("*" in part or "?" in part for part in profile_parts):
        raise CompatibilityEvolutionError(
            "MigrationContractReferenceNotExact",
            "migration profile references cannot contain wildcard tokens",
        )
    return (*contract_key, *profile_parts)


def validate_evolution_policy(policy: Mapping[str, Any]) -> None:
    stable_major = policy.get("stable_major")
    if not isinstance(stable_major, int) or isinstance(stable_major, bool) or stable_major < 1:
        raise CompatibilityEvolutionError(
            "StableMajorInvalid", "stable_major must be a positive integer"
        )

    seen_contracts: set[tuple[str, str, str]] = set()
    for entry in policy.get("guarantee_scope", []):
        key = _contract_key(entry.get("contract", {}))
        if key in seen_contracts:
            raise CompatibilityEvolutionError(
                "GuaranteeScopeDuplicate", f"duplicate guarantee-scope contract: {key!r}"
            )
        seen_contracts.add(key)
        _parse_release_version(entry.get("since"))

    seen_deprecations: set[str] = set()
    for entry in policy.get("deprecations", []):
        deprecation_id = entry.get("deprecation_id")
        if not isinstance(deprecation_id, str) or not deprecation_id:
            raise CompatibilityEvolutionError(
                "DeprecationIdentityInvalid", "deprecation_id must be a non-empty string"
            )
        if deprecation_id in seen_deprecations:
            raise CompatibilityEvolutionError(
                "DeprecationIdentityDuplicate", f"duplicate deprecation_id: {deprecation_id}"
            )
        seen_deprecations.add(deprecation_id)
        _contract_key(entry.get("affected_contract", {}))
        _parse_release_version(entry.get("deprecated_in"))
        earliest = entry.get("earliest_removal_major")
        if not isinstance(earliest, int) or isinstance(earliest, bool) or earliest <= stable_major:
            raise CompatibilityEvolutionError(
                "StableContractRemovalWithinMajor",
                "earliest_removal_major must be greater than stable_major",
            )
        if "replacement" in entry:
            _contract_key(entry["replacement"])
        elif not isinstance(entry.get("rationale"), str) or not entry["rationale"]:
            raise CompatibilityEvolutionError(
                "DeprecationDispositionMissing",
                "deprecation requires an exact replacement or non-empty rationale",
            )

    seen_migrations: set[str] = set()
    for entry in policy.get("migrations", []):
        migration_id = entry.get("migration_id")
        if not isinstance(migration_id, str) or not migration_id:
            raise CompatibilityEvolutionError(
                "MigrationIdentityInvalid", "migration_id must be a non-empty string"
            )
        if migration_id in seen_migrations:
            raise CompatibilityEvolutionError(
                "MigrationIdentityDuplicate", f"duplicate migration_id: {migration_id}"
            )
        seen_migrations.add(migration_id)
        _migration_contract_key(entry.get("source_contract", {}))
        _migration_contract_key(entry.get("target_contract", {}))
        postconditions = set(entry.get("required_postconditions", []))
        if postconditions != {"SchemaValidation", "CompatibilityReevaluation"}:
            raise CompatibilityEvolutionError(
                "MigrationPostconditionMissing",
                "migration must require schema validation and compatibility re-evaluation",
            )


def select_migration(
    policy: Mapping[str, Any],
    *,
    domain: str,
    source_contract: Mapping[str, Any],
    target_contract: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Select one exact migration; never infer from ordering, hashes, or fingerprints."""

    source_key = _migration_contract_key(source_contract)
    target_key = _migration_contract_key(target_contract)
    matches = [
        entry
        for entry in policy.get("migrations", [])
        if entry.get("domain") == domain
        and _migration_contract_key(entry.get("source_contract", {})) == source_key
        and _migration_contract_key(entry.get("target_contract", {})) == target_key
    ]
    if not matches:
        raise CompatibilityEvolutionError(
            "MigrationPathMissing", "no exact migration path is declared"
        )
    if len(matches) != 1:
        raise CompatibilityEvolutionError(
            "MigrationPathAmbiguous", "multiple exact migration paths are declared"
        )
    return matches[0]


def execute_migration(
    migration: Mapping[str, Any],
    artifact: Mapping[str, Any],
    *,
    transformations: Mapping[
        tuple[str, str], Callable[[Mapping[str, Any]], Mapping[str, Any]]
    ],
    schema_validator: Callable[[Mapping[str, Any]], Any],
    compatibility_evaluator: Callable[[Mapping[str, Any]], Mapping[str, Any]],
) -> MigrationExecutionResult:
    """Run one named migration and enforce both mandatory postconditions."""

    transformation = migration.get("transformation", {})
    transformation_id = transformation.get("transformation_id")
    transformation_revision = transformation.get("transformation_revision")
    implementation = transformations.get((transformation_id, transformation_revision))
    if implementation is None:
        raise CompatibilityEvolutionError(
            "MigrationImplementationMissing",
            "migration transformation is unavailable: "
            f"{transformation_id!r}@{transformation_revision!r}",
        )

    output = implementation(copy.deepcopy(dict(artifact)))
    if not isinstance(output, Mapping):
        raise CompatibilityEvolutionError(
            "MigratedArtifactInvalid", "migration output must be an object"
        )
    try:
        validation_result = schema_validator(output)
    except Exception as exc:
        raise CompatibilityEvolutionError(
            "MigratedArtifactInvalid", "migrated output failed target schema validation"
        ) from exc
    if validation_result is False:
        raise CompatibilityEvolutionError(
            "MigratedArtifactInvalid", "migrated output failed target schema validation"
        )

    try:
        decision = compatibility_evaluator(output)
    except Exception as exc:
        raise CompatibilityEvolutionError(
            "PostMigrationCompatibilityUndetermined",
            "post-migration compatibility evaluation failed",
        ) from exc
    try:
        decision_id = decision["decision_id"]
        decision_profile = decision["profile"]
        status = decision["result"]["status"]
    except (KeyError, TypeError) as exc:
        raise CompatibilityEvolutionError(
            "PostMigrationCompatibilityUndetermined",
            "post-migration compatibility decision is missing or malformed",
        ) from exc
    target_contract = migration.get("target_contract", {})
    expected_profile = (
        target_contract.get("profile_id"),
        target_contract.get("profile_revision"),
        migration.get("domain"),
    )
    actual_profile = (
        decision_profile.get("profile_id"),
        decision_profile.get("profile_revision"),
        decision_profile.get("domain"),
    )
    if actual_profile != expected_profile:
        raise CompatibilityEvolutionError(
            "PostMigrationCompatibilityProfileMismatch",
            "post-migration compatibility decision used the wrong domain or profile",
        )
    if status == "Incompatible":
        raise CompatibilityEvolutionError(
            "PostMigrationIncompatible", "migrated output is incompatible with the target"
        )
    if status != "Compatible":
        raise CompatibilityEvolutionError(
            "PostMigrationCompatibilityUndetermined",
            "migrated output compatibility is not proven",
        )
    if not isinstance(decision_id, str) or not decision_id:
        raise CompatibilityEvolutionError(
            "PostMigrationCompatibilityUndetermined",
            "post-migration compatibility decision_id is missing",
        )

    return MigrationExecutionResult(
        migration_id=str(migration["migration_id"]),
        transformation_id=str(transformation_id),
        transformation_revision=str(transformation_revision),
        output=copy.deepcopy(dict(output)),
        postconditions=("SchemaValidation", "CompatibilityReevaluation"),
        compatibility_decision_id=decision_id,
    )
