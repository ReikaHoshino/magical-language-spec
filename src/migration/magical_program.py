"""Canonical SpellInstanceBundle to MagicalProgram translation registry.

This module is the production assembly for the complete current 12-contract
suite.  It imports only declarative translators and the generic MagicalProgram
runtime.  The frozen legacy SpellInstance implementation and the differential
shadow harness are deliberately outside this dependency graph.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping

from .magical_program_shadow_boundary import translate_boundary_reflection
from .magical_program_shadow_debug import (
    translate_pathological_planning,
    translate_prepare_bound_transit,
)
from .magical_program_shadow_debug_hydra import translate_reactive_hydra
from .magical_program_shadow_explosion import translate_explosion
from .magical_program_shadow_generic import translate_generic_transition
from .magical_program_shadow_success_arcana import (
    translate_evidence_fusion as _translate_evidence_fusion,
)
from .magical_program_shadow_support import (
    ContractPair,
    ShadowTranslation,
    bundle_contract_pair,
)
from .magical_program_shadow_treatment import (
    translate_staged_treatment as _translate_staged_treatment,
)
from .magical_program_shadow_unsupported import (
    UNSUPPORTED_CONTRACTS,
    translate_unsupported,
)

Translator = Callable[[Mapping[str, Any]], ShadowTranslation]

GENERIC_TRANSITION_PAIR: ContractPair = (
    ("example.generic-transition", "1"),
    ("runtime.generic-transition", "1"),
)
BOUNDARY_REFLECTION_PAIR: ContractPair = (
    ("controller.boundary-reflection", "1"),
    ("runtime.boundary-controller", "1"),
)
TREATMENT_STAGED_PAIR: ContractPair = (
    ("treatment.staged-repair", "1"),
    ("runtime.staged-treatment", "1"),
)
EVIDENCE_FUSION_PAIR: ContractPair = (
    ("evidence.snapshot-fusion", "1"),
    ("runtime.evidence-artifact", "1"),
)
EXPLOSION_PAIR: ContractPair = (
    ("dynamics.explosion", "1"),
    ("runtime.explosion", "1"),
)
PATHOLOGICAL_PLANNING_PAIR: ContractPair = (
    ("debug.pathological-planning", "1"),
    None,
)
PREPARE_BOUND_TRANSIT_PAIR: ContractPair = (
    ("debug.prepare-bound-transit", "1"),
    ("runtime.prepare-bound-transit", "1"),
)
REACTIVE_HYDRA_PAIR: ContractPair = (
    ("debug.reactive-budget", "1"),
    ("runtime.reactive-hydra", "1"),
)


@dataclass(frozen=True)
class ProgramTranslatorRegistration:
    semantic_contract: tuple[str, str]
    runtime_contract: tuple[str, str] | None
    translator: Translator

    @property
    def pair(self) -> ContractPair:
        return (self.semantic_contract, self.runtime_contract)


class ProgramTranslatorRegistry:
    """Fail-closed exact contract-pair registry for production translation."""

    def __init__(
        self, registrations: Iterable[ProgramTranslatorRegistration] = ()
    ) -> None:
        self._items: dict[ContractPair, ProgramTranslatorRegistration] = {}
        for registration in registrations:
            self.register(registration)

    def register(self, registration: ProgramTranslatorRegistration) -> None:
        if registration.pair in self._items:
            raise ValueError(
                f"duplicate MagicalProgram translator pair: {registration.pair!r}"
            )
        self._items[registration.pair] = registration

    def replace(self, registration: ProgramTranslatorRegistration) -> None:
        if registration.pair not in self._items:
            raise KeyError(
                f"cannot replace unknown MagicalProgram translator pair: "
                f"{registration.pair!r}"
            )
        self._items[registration.pair] = registration

    def resolve(
        self, bundle: Mapping[str, Any]
    ) -> ProgramTranslatorRegistration:
        pair = bundle_contract_pair(bundle)
        registration = self._items.get(pair)
        if registration is None:
            raise KeyError(f"no MagicalProgram translator for contract pair {pair!r}")
        return registration

    def pairs(self) -> set[ContractPair]:
        return set(self._items)


def translate_evidence_fusion(
    bundle: Mapping[str, Any],
) -> ShadowTranslation:
    """Use a selector so current state revision remains PREPARE-owned."""

    built = _translate_evidence_fusion(bundle)
    program = copy.deepcopy(built.program)
    subject_id = str(bundle["execution"]["parameters"]["subject_id"])
    subject_value = next(
        item for item in program["values"] if item["value_id"] == "subject_hint"
    )
    subject_value.clear()
    subject_value.update(
        {
            "value_id": "subject_hint",
            "kind": "selector",
            "selector": {"entity_id": subject_id},
        }
    )
    return ShadowTranslation(
        program,
        built.world,
        built.evaluator,
        built.runtime,
        built.classification,
        bundle_contract_pair(bundle),
    )


def translate_staged_treatment(
    bundle: Mapping[str, Any],
) -> ShadowTranslation:
    """Keep correspondence truth in host evidence rather than syntax."""

    normalized = copy.deepcopy(bundle)
    original_unique = bool(
        bundle["execution"]["parameters"]["correspondence_unique"]
    )
    normalized["execution"]["parameters"]["correspondence_unique"] = True
    built = _translate_staged_treatment(normalized)
    for record in built.world.runtime_state.get("evidence", {}).values():
        if record.get("kind") == "UniqueCorrespondence":
            record["unique"] = original_unique
    return ShadowTranslation(
        built.program,
        built.world,
        built.evaluator,
        built.runtime,
        built.classification,
        bundle_contract_pair(bundle),
    )


def default_program_translators() -> ProgramTranslatorRegistry:
    registrations = [
        ProgramTranslatorRegistration(
            GENERIC_TRANSITION_PAIR[0],
            GENERIC_TRANSITION_PAIR[1],
            translate_generic_transition,
        ),
        ProgramTranslatorRegistration(
            BOUNDARY_REFLECTION_PAIR[0],
            BOUNDARY_REFLECTION_PAIR[1],
            translate_boundary_reflection,
        ),
        ProgramTranslatorRegistration(
            TREATMENT_STAGED_PAIR[0],
            TREATMENT_STAGED_PAIR[1],
            translate_staged_treatment,
        ),
        ProgramTranslatorRegistration(
            EVIDENCE_FUSION_PAIR[0],
            EVIDENCE_FUSION_PAIR[1],
            translate_evidence_fusion,
        ),
        ProgramTranslatorRegistration(
            EXPLOSION_PAIR[0],
            EXPLOSION_PAIR[1],
            translate_explosion,
        ),
        ProgramTranslatorRegistration(
            PATHOLOGICAL_PLANNING_PAIR[0],
            PATHOLOGICAL_PLANNING_PAIR[1],
            translate_pathological_planning,
        ),
        ProgramTranslatorRegistration(
            PREPARE_BOUND_TRANSIT_PAIR[0],
            PREPARE_BOUND_TRANSIT_PAIR[1],
            translate_prepare_bound_transit,
        ),
        ProgramTranslatorRegistration(
            REACTIVE_HYDRA_PAIR[0],
            REACTIVE_HYDRA_PAIR[1],
            translate_reactive_hydra,
        ),
    ]
    registrations.extend(
        ProgramTranslatorRegistration(
            (contract_id, "1"),
            None,
            translate_unsupported,
        )
        for contract_id in UNSUPPORTED_CONTRACTS
    )
    return ProgramTranslatorRegistry(registrations)


def translate_bundle(
    bundle: Mapping[str, Any],
    *,
    translators: ProgramTranslatorRegistry | None = None,
) -> ShadowTranslation:
    registry = translators or default_program_translators()
    registration = registry.resolve(bundle)
    translated = registration.translator(bundle)
    if translated.source_pair != registration.pair:
        raise ValueError("translator returned a different source contract pair")
    return translated


__all__ = [
    "BOUNDARY_REFLECTION_PAIR",
    "EVIDENCE_FUSION_PAIR",
    "EXPLOSION_PAIR",
    "GENERIC_TRANSITION_PAIR",
    "PATHOLOGICAL_PLANNING_PAIR",
    "PREPARE_BOUND_TRANSIT_PAIR",
    "ProgramTranslatorRegistration",
    "ProgramTranslatorRegistry",
    "REACTIVE_HYDRA_PAIR",
    "TREATMENT_STAGED_PAIR",
    "default_program_translators",
    "translate_bundle",
    "translate_evidence_fusion",
    "translate_staged_treatment",
]
