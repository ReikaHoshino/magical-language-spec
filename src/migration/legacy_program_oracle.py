"""Explicit test-only differential oracle for the complete 12-contract suite.

The public SpellInstance path does not import this module.  It assembles the
frozen legacy observation and the generic migration matrix only for historical
parity tests.  Package-resource golden resolution is installed for the duration
of one oracle call and restored immediately; importing this module has no global
side effects.
"""
from __future__ import annotations

import json
from pathlib import Path
from threading import RLock
from typing import Any, Mapping

from src.resources import resource_path

from . import magical_program_shadow as core
from . import magical_program_shadow_suite as base
from .magical_program_shadow_debug_hydra import translate_reactive_hydra

_JSON = dict[str, Any]
_DEFAULT_GOLDEN_MANIFEST = resource_path(
    "conformance/magical-program-golden-parity.json"
)
_ORACLE_LOCK = RLock()


def _resource_golden_context(
    *,
    source_path: Path,
    golden_input: str | Path | None,
    variant_id: str | None,
    manifest_path: str | Path,
) -> core.GoldenContext | None:
    manifest_file = Path(manifest_path).resolve()
    resource_root = manifest_file.parent.parent
    owned_input = source_path if golden_input is None else Path(golden_input)
    try:
        relative = owned_input.resolve().relative_to(resource_root).as_posix()
    except ValueError as error:
        raise ValueError(
            "golden_input must identify an input owned by the selected resource bundle"
        ) from error
    manifest: Mapping[str, Any] = json.loads(
        manifest_file.read_text(encoding="utf-8")
    )
    case = next(
        (item for item in manifest["cases"] if item["input"] == relative),
        None,
    )
    if case is None:
        return None
    if variant_id is None:
        return core.GoldenContext(
            str(case["expectation_id"]),
            core._combined_checks(manifest, case),
            (),
        )
    variant = next(
        (
            item
            for item in case.get("variants", [])
            if item["variant_id"] == variant_id
        ),
        None,
    )
    if variant is None:
        raise ValueError(
            f"golden manifest has no variant {variant_id!r} for {relative!r}"
        )
    return core.GoldenContext(
        f"{case['expectation_id']}::{variant_id}",
        core._combined_checks(manifest, variant),
        tuple(variant.get("mutations", ())),
    )


def default_shadow_translators() -> core.ShadowTranslatorRegistry:
    registry = core.default_shadow_translators()
    registrations = (
        core.ShadowTranslatorRegistration(
            base.TREATMENT_STAGED_PAIR[0],
            base.TREATMENT_STAGED_PAIR[1],
            base.translate_staged_treatment,
        ),
        core.ShadowTranslatorRegistration(
            base.EXPLOSION_PAIR[0],
            base.EXPLOSION_PAIR[1],
            base.translate_explosion,
        ),
        core.ShadowTranslatorRegistration(
            base.PATHOLOGICAL_PLANNING_PAIR[0],
            base.PATHOLOGICAL_PLANNING_PAIR[1],
            base.translate_pathological_planning,
        ),
        core.ShadowTranslatorRegistration(
            base.PREPARE_BOUND_TRANSIT_PAIR[0],
            base.PREPARE_BOUND_TRANSIT_PAIR[1],
            base.translate_prepare_bound_transit,
        ),
        core.ShadowTranslatorRegistration(
            base.REACTIVE_HYDRA_PAIR[0],
            base.REACTIVE_HYDRA_PAIR[1],
            translate_reactive_hydra,
        ),
    )
    for registration in registrations:
        registry.register(registration)
    return registry


def run_shadow_file(
    path: str | Path,
    *,
    translators: core.ShadowTranslatorRegistry | None = None,
    golden_input: str | Path | None = None,
    variant_id: str | None = None,
    golden_manifest: str | Path = _DEFAULT_GOLDEN_MANIFEST,
) -> _JSON:
    registry = translators or default_shadow_translators()
    with _ORACLE_LOCK:
        previous = core._golden_context
        core._golden_context = _resource_golden_context
        try:
            return base.run_shadow_file(
                path,
                translators=registry,
                golden_input=golden_input,
                variant_id=variant_id,
                golden_manifest=golden_manifest,
            )
        finally:
            core._golden_context = previous


BOUNDARY_REFLECTION_PAIR = base.BOUNDARY_REFLECTION_PAIR
EVIDENCE_FUSION_PAIR = base.EVIDENCE_FUSION_PAIR
EXPLOSION_PAIR = base.EXPLOSION_PAIR
PATHOLOGICAL_PLANNING_PAIR = base.PATHOLOGICAL_PLANNING_PAIR
PREPARE_BOUND_TRANSIT_PAIR = base.PREPARE_BOUND_TRANSIT_PAIR
REACTIVE_HYDRA_PAIR = base.REACTIVE_HYDRA_PAIR
TREATMENT_STAGED_PAIR = base.TREATMENT_STAGED_PAIR
UNSUPPORTED_CONTRACTS = base.UNSUPPORTED_CONTRACTS
ShadowTranslatorRegistration = base.ShadowTranslatorRegistration
ShadowTranslatorRegistry = base.ShadowTranslatorRegistry
bundle_contract_pair = base.bundle_contract_pair
translate_explosion = base.translate_explosion
translate_pathological_planning = base.translate_pathological_planning
translate_prepare_bound_transit = base.translate_prepare_bound_transit
translate_staged_treatment = base.translate_staged_treatment

__all__ = [
    "BOUNDARY_REFLECTION_PAIR",
    "EVIDENCE_FUSION_PAIR",
    "EXPLOSION_PAIR",
    "PATHOLOGICAL_PLANNING_PAIR",
    "PREPARE_BOUND_TRANSIT_PAIR",
    "REACTIVE_HYDRA_PAIR",
    "TREATMENT_STAGED_PAIR",
    "UNSUPPORTED_CONTRACTS",
    "ShadowTranslatorRegistration",
    "ShadowTranslatorRegistry",
    "bundle_contract_pair",
    "default_shadow_translators",
    "run_shadow_file",
    "translate_explosion",
    "translate_pathological_planning",
    "translate_prepare_bound_transit",
    "translate_reactive_hydra",
    "translate_staged_treatment",
]
