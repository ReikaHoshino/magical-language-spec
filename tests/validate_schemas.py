#!/usr/bin/env python3
"""Validate all repository schemas and core-configuration fixtures."""
from __future__ import annotations

import copy
import json
import sys
import tomllib
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.semantic_fingerprint import semantic_fingerprint_v1

SCHEMAS = ROOT / "schemas"
FIXTURES = ROOT / "examples" / "core-config"
LATIN_FIXTURES = ROOT / "examples" / "latin-adapter"
FINGERPRINT_FIXTURES = ROOT / "examples" / "semantic-fingerprint"
FEASIBILITY_FIXTURE = ROOT / "examples" / "feasibility-report.json"
RUNTIME_FIXTURES = ROOT / "examples" / "runtime-profiles"
SOURCE_NORMALIZATION_FIXTURES = ROOT / "examples" / "source-normalization"
AMBIGUITY_FIXTURES = ROOT / "examples" / "ambiguity-policy"
COMPATIBILITY_FIXTURES = ROOT / "examples" / "compatibility"
PLANNING_INFERENCE_FIXTURES = ROOT / "examples" / "planning-inference"
ESTIMATOR_PROFILE_FIXTURES = ROOT / "examples" / "estimator-profiles"
CANONICAL_WATER_BALL_FIXTURES = ROOT / "examples" / "canonical-water-ball"
SUCCESS_ARCANA_FIXTURES = ROOT / "examples" / "success-arcana"
SPELL_INSTANCE_FIXTURES = ROOT / "examples" / "spell-instances"
COMPATIBILITY_COVERAGE = ROOT / "conformance" / "compatibility-coverage.json"
V1_REQUIRED_SURFACE = ROOT / "conformance" / "v1-required-surface.json"
EXPERIMENTAL_ARCANA_MANIFEST = ROOT / "conformance" / "experimental-arcana.json"
EXPERIMENTAL_ARCANA_COVERAGE = ROOT / "conformance" / "experimental-arcana-rule-coverage.json"
SPELL_INSTANCE_MANIFEST = ROOT / "conformance" / "spell-instance-experimental.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validator(schema_name: str) -> Draft202012Validator:
    schema = load(SCHEMAS / schema_name)
    registry = Registry()
    for path in SCHEMAS.glob("*.schema.json"):
        document = load(path)
        resource = Resource.from_contents(document)
        registry = registry.with_resource(document["$id"], resource)
        registry = registry.with_resource(path.resolve().as_uri(), resource)
    return Draft202012Validator(
        schema, registry=registry, format_checker=FormatChecker()
    )


def assert_schema_rejects(
    schema_validator: Draft202012Validator, instance, description: str
) -> None:
    if not list(schema_validator.iter_errors(instance)):
        raise AssertionError(f"schema accepted invalid case: {description}")


def validate_world_revision_mapping(instance: dict) -> None:
    snapshot = instance["snapshot"]
    for field in ("world_index_revision", "source_world_revision", "index_schema_revision"):
        if instance[field] != snapshot[field]:
            raise AssertionError(f"WorldIndex root/snapshot {field} mismatch")


def validate_unresolved_hash(record: dict, scope: str, description: str) -> None:
    if record.get("scope") != scope or record.get("status") != "unresolved":
        raise AssertionError(f"{description} must be an unresolved {scope} record")
    if not isinstance(record.get("reason"), str) or not record["reason"]:
        raise AssertionError(f"{description} must explain why its digest is unresolved")
    if {"algorithm", "value", "canonicalization_profile"} & set(record):
        raise AssertionError(f"{description} must not invent unresolved digest fields")


FORBIDDEN_LEXICAL_AUTHORITY_KEYS = {
    "entity_id", "entity_ids", "capability", "capabilities", "lease", "authority"
}


def validate_lexical_authority_boundary(value, path: str = "$") -> None:
    """Reject authority/entity fields anywhere in lexical extension data."""
    if isinstance(value, dict):
        forbidden = FORBIDDEN_LEXICAL_AUTHORITY_KEYS & set(value)
        if forbidden:
            names = ", ".join(sorted(forbidden))
            raise AssertionError(f"forbidden lexical authority key(s) at {path}: {names}")
        for key, child in value.items():
            validate_lexical_authority_boundary(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_lexical_authority_boundary(child, f"{path}[{index}]")


def validate_release_consistency() -> None:
    """Keep historical snapshots immutable while checking the current release identity."""

    current_release = "v1.0.0-rc.1"
    current_files = [
        ROOT / "README.md",
        ROOT / "TODO.md",
        ROOT / "CHANGELOG.md",
        ROOT / "reference" / "terminology.md",
        ROOT / "reference" / "consistency-report.md",
        ROOT / "spec" / "v1.0.0-rc.1.md",
    ]
    for path in current_files:
        if current_release not in path.read_text(encoding="utf-8"):
            raise AssertionError(
                f"{path.relative_to(ROOT)} is not synchronized to {current_release}"
            )

    historical_snapshot = ROOT / "spec" / "v0.7.3.md"
    historical_text = historical_snapshot.read_text(encoding="utf-8")
    if "v0.7.3" not in historical_text:
        raise AssertionError("spec/v0.7.3.md lost its historical version identity")

    invariant = "SemanticFingerprint != artifact content_hash"
    boundary_files = [
        ROOT / "README.md",
        ROOT / "CHANGELOG.md",
        ROOT / "reference" / "language-adapters.md",
        ROOT / "reference" / "consistency-report.md",
        historical_snapshot,
    ]
    for path in boundary_files:
        if invariant not in path.read_text(encoding="utf-8"):
            raise AssertionError(
                f"{path.relative_to(ROOT)} lost the semantic/artifact hash boundary"
            )

    manifest = load(ROOT / "conformance" / "manifest.json")
    if manifest["suite"]["suite_version"] != "1.0.0-rc.1":
        raise AssertionError("conformance suite version is not synchronized to 1.0.0-rc.1")
    if manifest["suite"]["release_target"] != current_release:
        raise AssertionError("conformance release target does not match v1.0.0-rc.1")
    if {item["status"] for item in manifest["classes"]} != {"released"}:
        raise AssertionError("all four v1.0 RC conformance classes must be released")

    coverage = load(ROOT / "conformance" / "rule-coverage.json")
    if coverage["suite_version"] != manifest["suite"]["suite_version"]:
        raise AssertionError("conformance rule coverage version does not match manifest")

    package = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    if package["project"]["version"] != "1.0.0rc1":
        raise AssertionError("reference package version is not synchronized to 1.0.0rc1")

    todo = (ROOT / "TODO.md").read_text(encoding="utf-8")
    if "release最終整理時刻（v0.7.3）: **PENDING" in todo:
        raise AssertionError("v0.7.3 release finalization timestamp is still pending")
    if "Issue #36 — v0.8 Minimal Local Evaluator" not in todo:
        raise AssertionError("TODO.md lost the historical v0.8 resume marker")
    current_resume_markers = [
        "# 0. RESUME POINT",
        "last released version: **v1.0.0-rc.1**",
        "public Issue #2",
    ]
    for marker in current_resume_markers:
        if marker not in todo:
            raise AssertionError(
                f"TODO.md current v0.10+ RESUME POINT lost marker: {marker}"
            )


def main() -> None:
    for path in sorted(SCHEMAS.glob("*.schema.json")):
        Draft202012Validator.check_schema(load(path))

    cases = {
        "semantic-registry.json": "semantic-registry.schema.json",
        "semantic-registry-domain-contracts.json": "semantic-registry.schema.json",
        "world-index.json": "world-index.schema.json",
        "runtime-profile.json": "runtime-profile.schema.json",
    }
    for fixture_name, schema_name in cases.items():
        instance = load(FIXTURES / fixture_name)
        validator(schema_name).validate(instance)
        validate_unresolved_hash(
            instance["metadata"]["content_hash"],
            "artifact-content",
            f"{fixture_name} content_hash",
        )
        if fixture_name == "world-index.json":
            validate_world_revision_mapping(instance)

    source_normalization_validator = validator(
        "source-text-normalization.schema.json"
    )
    source_normalization_paths = sorted(
        SOURCE_NORMALIZATION_FIXTURES.glob("*.json")
    )
    for path in source_normalization_paths:
        source_normalization_validator.validate(load(path))

    compatibility_source = load(
        SOURCE_NORMALIZATION_FIXTURES / "compatibility-preserved.json"
    )
    if (
        compatibility_source["input"]["original_text"]
        != compatibility_source["output"]["normalized_text"]
    ):
        raise AssertionError(
            "source normalization folded compatibility characters"
        )

    combining_source = load(
        SOURCE_NORMALIZATION_FIXTURES / "japanese-combining-nfc.json"
    )
    if combining_source["source_map"]["entries"][0]["exact"]:
        raise AssertionError(
            "combining-character fixture lost its transformed provenance"
        )

    for fixture_name in (
        "semantic-registry.json",
        "semantic-registry-domain-contracts.json",
    ):
        registry = load(FIXTURES / fixture_name)
        validate_unresolved_hash(
            registry["registry_hash"],
            "registry-contract-set",
            f"{fixture_name} registry_hash",
        )

    world = load(FIXTURES / "world-index.json")
    broken = copy.deepcopy(world)
    broken["snapshot"]["source_world_revision"] = "different-world-revision"
    try:
        validate_world_revision_mapping(broken)
    except AssertionError:
        pass
    else:
        raise AssertionError("revision mapping mismatch was not rejected")

    runtime_validator = validator("runtime-profile.schema.json")
    runtime_paths = [
        FIXTURES / "runtime-profile.json",
        *sorted(RUNTIME_FIXTURES.glob("*.json")),
    ]
    runtimes = [load(path) for path in runtime_paths]
    for path, runtime in zip(runtime_paths, runtimes):
        runtime_validator.validate(runtime)
        validate_unresolved_hash(
            runtime["metadata"]["content_hash"],
            "artifact-content",
            f"{path.name} content_hash",
        )

    scheduler_kinds = {
        runtime["scheduler"]["contract"]["kind"] for runtime in runtimes
    }
    if scheduler_kinds != {
        "FixedStep",
        "AdaptiveStep",
        "EventDriven",
        "Hybrid",
    }:
        raise AssertionError("runtime fixtures must cover every scheduling policy")

    replay_modes = {runtime["replay"]["contract"]["mode"] for runtime in runtimes}
    if replay_modes != {
        "StrictDeterministic",
        "DeterministicWithinTolerance",
        "DiagnosticBestEffort",
    }:
        raise AssertionError("runtime fixtures must cover every replay mode")

    by_scheduler_kind = {
        runtime["scheduler"]["contract"]["kind"]: runtime for runtime in runtimes
    }
    required_scheduler_fields = {
        "FixedStep": ("dt",),
        "AdaptiveStep": ("min_dt", "max_dt", "error_policy"),
        "Hybrid": ("baseline_policy", "split_on_events"),
    }
    for kind, fields in required_scheduler_fields.items():
        for field in fields:
            broken = copy.deepcopy(by_scheduler_kind[kind])
            del broken["scheduler"]["contract"][field]
            assert_schema_rejects(
                runtime_validator,
                broken,
                f"{kind} without {field}",
            )

    invalid_duration = copy.deepcopy(by_scheduler_kind["FixedStep"])
    del invalid_duration["scheduler"]["contract"]["dt"]["semantic_type"]
    assert_schema_rejects(
        runtime_validator,
        invalid_duration,
        "duration without semantic type",
    )

    wrong_duration_dimension = copy.deepcopy(by_scheduler_kind["FixedStep"])
    wrong_duration_dimension["scheduler"]["contract"]["dt"]["dimension"]["s"] = 0
    assert_schema_rejects(
        runtime_validator,
        wrong_duration_dimension,
        "duration with non-time dimension",
    )

    invalid_scheduler = copy.deepcopy(runtimes[0])
    invalid_scheduler["scheduler"]["contract"] = {"kind": "BatchStep"}
    assert_schema_rejects(
        runtime_validator, invalid_scheduler, "unknown scheduler variant"
    )

    invalid_replay = copy.deepcopy(runtimes[0])
    invalid_replay["replay"]["contract"]["mode"] = "Rewind"
    assert_schema_rejects(
        runtime_validator, invalid_replay, "unknown replay mode"
    )

    event_runtime = by_scheduler_kind["EventDriven"]
    for field in ("sample_period", "max_jitter", "actuation_latency_bound"):
        broken = copy.deepcopy(event_runtime)
        del broken["scheduler"]["contract"]["controller_timing"][field]
        assert_schema_rejects(
            runtime_validator,
            broken,
            f"ControllerTiming without {field}",
        )

    for component_path in (
        ("scheduler",),
        ("integrators", 0),
        ("replay",),
        ("temporal_tolerance",),
    ):
        for field in ("id", "revision"):
            broken = copy.deepcopy(runtimes[0])
            component = broken
            for path_part in component_path:
                component = component[path_part]
            del component[field]
            assert_schema_rejects(
                runtime_validator,
                broken,
                f"{component_path} without independent {field}",
            )

    collapsed_revision = copy.deepcopy(runtimes[0])
    collapsed_revision["component_revision"] = "1"
    for component in (
        collapsed_revision["scheduler"],
        collapsed_revision["integrators"][0],
        collapsed_revision["replay"],
        collapsed_revision["temporal_tolerance"],
    ):
        del component["revision"]
    assert_schema_rejects(
        runtime_validator,
        collapsed_revision,
        "scheduler/integrator/replay/tolerance revisions collapsed at root",
    )

    invalid_integrator = copy.deepcopy(runtimes[0])
    del invalid_integrator["integrators"][0]["contract"]["local_error_policy"]
    assert_schema_rejects(
        runtime_validator,
        invalid_integrator,
        "IntegratorContract without local_error_policy",
    )

    invented_integrator = copy.deepcopy(runtimes[0])
    invented_integrator["integrators"][0]["contract"]["algorithm"] = "RK4"
    assert_schema_rejects(
        runtime_validator,
        invented_integrator,
        "implementation algorithm added to IntegratorContract",
    )

    collapsed_time_domains = copy.deepcopy(runtimes[0])
    collapsed_time_domains["temporal_tolerance"]["contract"]["tick_duration"] = {
        "value": 10,
        "unit": "ms",
    }
    assert_schema_rejects(
        runtime_validator,
        collapsed_time_domains,
        "tick duration collapsed into TemporalTolerance",
    )

    lexicon = load(LATIN_FIXTURES / "minimal-lexicon.json")
    validator("latin-lexicon.schema.json").validate(lexicon)
    validate_lexical_authority_boundary(lexicon)
    validate_unresolved_hash(
        lexicon["metadata"]["content_hash"],
        "artifact-content",
        "Latin lexicon content_hash",
    )

    lexeme_ids = {entry["lexeme_id"] for entry in lexicon["entries"]}
    required_lexemes = {
        "lat:calor", "lat:aqua", "lat:aer", "lat:transfero", "lat:canalis",
        "lat:energia", "lat:quantitas-motus", "lat:lapis", "lat:globus", "lat:nexus",
    }
    if not required_lexemes <= lexeme_ids:
        raise AssertionError("Latin lexicon is missing a required minimal entry")

    transfer = next(entry for entry in lexicon["entries"] if entry["lexeme_id"] == "lat:transfero")
    actual_frame = {
        (slot["role"], slot["morphosyntax"]["case"], tuple(slot["morphosyntax"].get("prepositions", [])))
        for slot in transfer["argument_frame"]["slots"]
    }
    expected_frame = {
        ("Patient", "accusative", ()),
        ("Source", "ablative", ("a", "ab")),
        ("Goal", "accusative", ("ad",)),
        ("Path", "accusative", ("per",)),
    }
    if actual_frame != expected_frame:
        raise AssertionError("transfero argument frame does not match the current reference")

    extensible_lexicon = copy.deepcopy(lexicon)
    extensible_entry = extensible_lexicon["entries"][0]
    extensible_entry["part_of_speech"] = "adjective"
    extensible_entry["morphology"]["candidates"][0]["features"]["tense"] = "perfect"
    extensible_entry["argument_frame"] = {
        "frame_id": "lat:extension-vocabulary:test",
        "slots": [
            {
                "role": "Recipient",
                "morphosyntax": {"case": "dative", "prepositions": ["apud"]},
            }
        ],
    }
    validator("latin-lexicon.schema.json").validate(extensible_lexicon)

    aqua = next(entry for entry in lexicon["entries"] if entry["lexeme_id"] == "lat:aqua")
    aquae_cases = {
        candidate["features"]["case"]
        for candidate in aqua["morphology"]["candidates"]
        if candidate["surface"] == "aquae"
    }
    if aquae_cases != {"genitive", "dative", "nominative"}:
        raise AssertionError("aquae ambiguity candidates were silently collapsed")

    broken_lexicon = copy.deepcopy(lexicon)
    broken_lexicon["entries"][0]["semantic_candidates"][0].setdefault(
        "qualifiers", {}
    )["entity_id"] = "forbidden:resolved-entity"
    if not list(validator("latin-lexicon.schema.json").iter_errors(broken_lexicon)):
        raise AssertionError("qualifier EntityID injection was not rejected by the schema")
    try:
        validate_lexical_authority_boundary(broken_lexicon)
    except AssertionError:
        pass
    else:
        raise AssertionError("recursive lexical authority validation missed qualifier EntityID")

    collapsed_aquae = copy.deepcopy(lexicon)
    collapsed_aqua = next(
        entry for entry in collapsed_aquae["entries"] if entry["lexeme_id"] == "lat:aqua"
    )
    collapsed_aqua["morphology"]["candidates"] = [
        candidate
        for candidate in collapsed_aqua["morphology"]["candidates"]
        if candidate["surface"] != "aquae" or candidate["features"]["case"] == "genitive"
    ]
    collapsed_cases = {
        candidate["features"]["case"]
        for candidate in collapsed_aqua["morphology"]["candidates"]
        if candidate["surface"] == "aquae"
    }
    if collapsed_cases == {"genitive", "dative", "nominative"}:
        raise AssertionError("negative ambiguity fixture was not changed")

    normalization = load(LATIN_FIXTURES / "thermal-transfer-normalization.json")
    candidate = normalization["normalization_candidate_set"]["candidates"][0]
    validator("nsr.schema.json").validate(candidate["nsr"])
    roles = {role["role"]: role["value"] for role in candidate["nsr"]["roles"]}
    if roles["Patient"].get("semantic_kind") != "Energy" or roles["Patient"].get("mode") != "Thermal":
        raise AssertionError("canonical Patient must remain Energy/Thermal")
    if roles["Source"].get("selector") != {"kind": "Symbolic", "symbol": "water"}:
        raise AssertionError("canonical Source must remain Symbolic(water)")
    if roles["Goal"].get("selector") != {"kind": "Symbolic", "symbol": "air"}:
        raise AssertionError("canonical Goal must remain Symbolic(air)")
    if roles["Quantity"].get("kind") != "Unknown" or roles["Quantity"].get("reason") != "MissingSurfaceArgument":
        raise AssertionError("missing surface quantity must remain Unknown(MissingSurfaceArgument)")
    if any(
        proposal.get("status") != "proposal"
        for proposal in normalization["role_proposals"]
    ):
        raise AssertionError("morphosyntactic roles must remain proposals")
    if candidate["nsr"]["semantic_fingerprint"] != semantic_fingerprint_v1(candidate["nsr"]):
        raise AssertionError("canonical Latin NSR SemanticFingerprintV1 is stale")

    fingerprint_cases = load(FINGERPRINT_FIXTURES / "thermal-transfer-v1.json")
    for field in ("base_nsr", "equivalent_adapter_nsr"):
        validator("nsr.schema.json").validate(fingerprint_cases[field])
    expected_fingerprint = fingerprint_cases["expected_fingerprint"]
    if semantic_fingerprint_v1(fingerprint_cases["base_nsr"]) != expected_fingerprint:
        raise AssertionError("SemanticFingerprintV1 fixture digest is stale")
    if semantic_fingerprint_v1(fingerprint_cases["equivalent_adapter_nsr"]) != expected_fingerprint:
        raise AssertionError("NSR-layer adapter equivalence fixture drifted")
    malformed_fingerprint = copy.deepcopy(fingerprint_cases["base_nsr"])
    malformed_fingerprint["semantic_fingerprint"] = "sha256:not-versioned"
    if not list(validator("nsr.schema.json").iter_errors(malformed_fingerprint)):
        raise AssertionError("unversioned semantic fingerprint was not rejected")
    null_unknown_reason = copy.deepcopy(fingerprint_cases["base_nsr"])
    quantity_role = next(
        role
        for role in null_unknown_reason["roles"]
        if role["role"] == "Quantity"
    )
    quantity_role["value"]["reason"] = None
    if not list(validator("nsr.schema.json").iter_errors(null_unknown_reason)):
        raise AssertionError("semantic Unknown with null reason was not rejected")

    feasibility = load(FEASIBILITY_FIXTURE)
    feasibility_validator = validator("feasibility-report.schema.json")
    feasibility_validator.validate(feasibility)
    validate_unresolved_hash(
        feasibility["provenance"]["registry_hash"],
        "registry-contract-set",
        "FeasibilityReport registry_hash",
    )
    numeric_revision = copy.deepcopy(feasibility)
    numeric_revision["provenance"]["world_index_revision"] = 4201
    assert_schema_rejects(
        feasibility_validator,
        numeric_revision,
        "portable revision serialized as a JSON number",
    )
    opaque_source_hash = copy.deepcopy(feasibility)
    opaque_source_hash["input"]["hash"] = "opaque-source-hash"
    assert_schema_rejects(
        feasibility_validator,
        opaque_source_hash,
        "source evidence hash without a scope/profile",
    )
    opaque_nsr_source_hash = copy.deepcopy(feasibility)
    opaque_nsr_source_hash["interpretations"]["nsr"]["provenance"][
        "source_hash"
    ] = "opaque-source-hash"
    assert_schema_rejects(
        feasibility_validator,
        opaque_nsr_source_hash,
        "NSR source evidence hash without a scope/profile",
    )
    report_nsr = feasibility["interpretations"]["nsr"]
    if semantic_fingerprint_v1(report_nsr) != feasibility["provenance"]["semantic_fingerprint"]:
        raise AssertionError("FeasibilityReport SemanticFingerprintV1 is stale")

    ambiguity_paths = sorted(AMBIGUITY_FIXTURES.glob("*.json"))
    ambiguity_validator = validator("ambiguity-decision-trace.schema.json")
    for path in ambiguity_paths:
        ambiguity_validator.validate(load(path))

    compatibility_paths = [COMPATIBILITY_FIXTURES / "decision-cases.json"]
    compatibility_validator = validator("compatibility.schema.json")
    for path in compatibility_paths:
        compatibility_validator.validate(load(path))

    compatibility_evolution_paths = sorted(
        COMPATIBILITY_FIXTURES.glob("evolution-*.json")
    )
    compatibility_evolution_validator = validator(
        "compatibility-evolution.schema.json"
    )
    for path in compatibility_evolution_paths:
        compatibility_evolution_validator.validate(load(path))

    compatibility_coverage_validator = validator(
        "compatibility-coverage.schema.json"
    )
    compatibility_coverage_validator.validate(load(COMPATIBILITY_COVERAGE))

    v1_surface_validator = validator("v1-required-surface.schema.json")
    v1_surface_validator.validate(load(V1_REQUIRED_SURFACE))

    planning_inference_paths = sorted(PLANNING_INFERENCE_FIXTURES.glob("*.json"))
    planning_inference_validator = validator("planning-inference.schema.json")
    for path in planning_inference_paths:
        planning_inference_validator.validate(load(path))

    estimator_profile_paths = sorted(ESTIMATOR_PROFILE_FIXTURES.glob("*.json"))
    estimator_profile_validator = validator("estimator-profile.schema.json")
    for path in estimator_profile_paths:
        estimator_profile_validator.validate(load(path))
        validate_unresolved_hash(
            load(path)["metadata"]["content_hash"],
            "artifact-content",
            f"{path.name} content_hash",
        )

    canonical_water_ball_paths = sorted(
        CANONICAL_WATER_BALL_FIXTURES.glob("*.json")
    )
    canonical_water_ball_validator = validator(
        "canonical-water-ball.schema.json"
    )
    for path in canonical_water_ball_paths:
        canonical_water_ball_validator.validate(load(path))

    success_arcana_paths = sorted(SUCCESS_ARCANA_FIXTURES.glob("*/*.json"))
    success_arcana_validator = validator("success-arcana.schema.json")
    for path in success_arcana_paths:
        if path.name == "nsr.json":
            validator("nsr.schema.json").validate(load(path))
        elif path.name == "world-index.json":
            validator("world-index.schema.json").validate(load(path))
            validate_world_revision_mapping(load(path))
        else:
            success_arcana_validator.validate(load(path))

    experimental_manifest = load(EXPERIMENTAL_ARCANA_MANIFEST)
    validator("experimental-arcana-manifest.schema.json").validate(experimental_manifest)
    experimental_coverage = load(EXPERIMENTAL_ARCANA_COVERAGE)
    manifest_cases = {case["case_id"]: set(case["rule_ids"]) for case in experimental_manifest["cases"]}
    covered: dict[str, set[str]] = {case_id: set() for case_id in manifest_cases}
    for rule in experimental_coverage["rules"]:
        for case_id in rule["case_ids"]:
            if case_id not in covered:
                raise AssertionError(f"experimental coverage names unknown case {case_id}")
            covered[case_id].add(rule["rule_id"])
    if covered != manifest_cases:
        raise AssertionError("Experimental-Arcana manifest/rule coverage mismatch")
    stable_manifest = load(ROOT / "conformance" / "manifest.json")
    if len(stable_manifest["cases"]) != experimental_manifest["required_surface_unchanged"]["case_count"]:
        raise AssertionError("Experimental-Arcana changed the stable required case count")

    spell_instance_paths = sorted(SPELL_INSTANCE_FIXTURES.glob("*/*.json"))
    spell_instance_validator = validator("spell-instance-bundle.schema.json")
    for path in spell_instance_paths:
        spell_instance_validator.validate(load(path))
    spell_manifest = load(SPELL_INSTANCE_MANIFEST)
    validator("spell-instance-manifest.schema.json").validate(spell_manifest)
    expected_bundle_files = {
        path.relative_to(ROOT).as_posix() for path in spell_instance_paths
    }
    if set(spell_manifest["bundle_files"]) != expected_bundle_files:
        raise AssertionError("SpellInstanceBundle manifest/file inventory mismatch")
    if {case["bundle_file"] for case in experimental_manifest["cases"]} != {
        path for path in expected_bundle_files if "/success-arcana/" in path
    }:
        raise AssertionError("Experimental-Arcana manifest does not own every canonical success bundle")

    validate_release_consistency()

    print(
        f"validated {len(list(SCHEMAS.glob('*.schema.json')))} schemas, "
        f"{len(cases)} core fixtures, {len(runtime_paths)} runtime profile fixtures, "
        f"{len(source_normalization_paths)} source normalization fixtures, "
        f"{len(ambiguity_paths)} ambiguity decision fixtures, "
        f"{len(compatibility_paths)} compatibility decision fixtures, "
        f"{len(compatibility_evolution_paths)} compatibility evolution fixtures, "
        "1 compatibility coverage inventory, 1 v1 required-surface matrix, "
        f"{len(planning_inference_paths)} planning inference fixtures, "
        f"{len(estimator_profile_paths)} estimator profile fixtures, "
        f"{len(canonical_water_ball_paths)} canonical water-ball fixtures, "
        f"{len(success_arcana_paths)} Experimental-Arcana fixture documents, "
        f"{len(spell_instance_paths)} SpellInstanceBundle documents, "
        "2 Latin adapter fixtures, 1 SemanticFingerprintV1 fixture, "
        "and the FeasibilityReport fixture"
    )


if __name__ == "__main__":
    main()
