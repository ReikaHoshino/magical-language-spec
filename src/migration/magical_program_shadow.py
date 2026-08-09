"""Contract-pair-selected differential harness for true MagicalProgram migration.

Translation and generic execution never call legacy handlers or executors. The
legacy SpellInstance service is invoked only here as an external frozen oracle.
Expected truth is owned by the independent golden manifest, never by an
executable bundle's embedded ``expected_outcome`` member.
"""
from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from src.artifacts.golden_parity import (
    FrozenArtifact,
    compare_checks,
    observe_frozen,
    pointer_set,
)
from src.artifacts.spell_instance import default_service

from .magical_program_shadow_boundary import (
    boundary_reflection_projection,
    translate_boundary_reflection,
)
from .magical_program_shadow_generic import (
    generic_executor,
    translate_generic_transition,
)
from .magical_program_shadow_success_arcana import (
    evidence_fusion_projection,
    translate_evidence_fusion as _build_evidence_fusion_translation,
)
from .magical_program_shadow_support import (
    ContractPair,
    ShadowTranslation,
    bundle_contract_pair,
)
from .magical_program_shadow_unsupported import (
    UNSUPPORTED_CONTRACTS,
    translate_unsupported,
)

_JSON = dict[str, Any]
Translator = Callable[[Mapping[str, Any]], ShadowTranslation]
Projection = Callable[[Mapping[str, Any], Mapping[str, Any]], _JSON]

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_GOLDEN_MANIFEST = (
    _REPOSITORY_ROOT / "conformance" / "magical-program-golden-parity.json"
)

# Retained compatibility import used by phase-1 source-isolation tests.
_generic_executor = generic_executor

BOUNDARY_REFLECTION_PAIR: ContractPair = (
    ("controller.boundary-reflection", "1"),
    ("runtime.boundary-controller", "1"),
)
EVIDENCE_FUSION_PAIR: ContractPair = (
    ("evidence.snapshot-fusion", "1"),
    ("runtime.evidence-artifact", "1"),
)

DIAGNOSTIC_ALIASES = {
    "ProgramAuthorityError": "AuthorityError",
    "ProgramLeaseError": "AuthorityError",
    "ProgramResolutionFailure": "ResolutionFailure",
    "ProgramResolutionAmbiguous": "ResolutionFailure",
    "ProgramStaleIdentity": "ResolutionFailure",
    "ProgramAccountingMissing": "ConservationProofFailure",
}
_EVALUATION_ONLY_DIAGNOSTICS = {
    "ProgramResolutionDeferred",
    "ProgramRuntimeRevalidationRequired",
}


@dataclass(frozen=True)
class ShadowTranslatorRegistration:
    semantic_contract: tuple[str, str]
    runtime_contract: tuple[str, str] | None
    translator: Translator

    @property
    def pair(self) -> ContractPair:
        return (self.semantic_contract, self.runtime_contract)


@dataclass(frozen=True)
class GoldenContext:
    expectation_id: str
    checks: tuple[Mapping[str, Any], ...]
    mutations: tuple[Mapping[str, Any], ...]


class ShadowTranslatorRegistry:
    def __init__(
        self, registrations: Iterable[ShadowTranslatorRegistration] = ()
    ) -> None:
        self._items: dict[ContractPair, ShadowTranslatorRegistration] = {}
        for item in registrations:
            self.register(item)

    def register(self, item: ShadowTranslatorRegistration) -> None:
        if item.pair in self._items:
            raise ValueError(f"duplicate shadow translator pair: {item.pair!r}")
        self._items[item.pair] = item

    def resolve(self, bundle: Mapping[str, Any]) -> ShadowTranslatorRegistration:
        pair = bundle_contract_pair(bundle)
        item = self._items.get(pair)
        if item is None:
            raise KeyError(f"no shadow translator for contract pair {pair!r}")
        return item

    def pairs(self) -> set[ContractPair]:
        return set(self._items)


def translate_evidence_fusion(bundle: Mapping[str, Any]) -> ShadowTranslation:
    """Remove current-state revision hints; PREPARE owns authoritative binding."""

    built = _build_evidence_fusion_translation(bundle)
    program = copy.deepcopy(built.program)
    subject_id = str(bundle["execution"]["parameters"]["subject_id"])
    subject_value = next(
        value for value in program["values"] if value["value_id"] == "subject_hint"
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
        built.source_pair,
    )


def default_shadow_translators() -> ShadowTranslatorRegistry:
    items = [
        ShadowTranslatorRegistration(
            ("example.generic-transition", "1"),
            ("runtime.generic-transition", "1"),
            translate_generic_transition,
        ),
        ShadowTranslatorRegistration(
            BOUNDARY_REFLECTION_PAIR[0],
            BOUNDARY_REFLECTION_PAIR[1],
            translate_boundary_reflection,
        ),
        ShadowTranslatorRegistration(
            EVIDENCE_FUSION_PAIR[0],
            EVIDENCE_FUSION_PAIR[1],
            translate_evidence_fusion,
        ),
    ]
    items.extend(
        ShadowTranslatorRegistration(
            (contract_id, "1"), None, translate_unsupported
        )
        for contract_id in UNSUPPORTED_CONTRACTS
    )
    return ShadowTranslatorRegistry(items)


def _normalized_code(code: str | None) -> str | None:
    if code is None:
        return None
    return DIAGNOSTIC_ALIASES.get(code, code)


def _terminal_diagnostic_code(
    report: Mapping[str, Any], execution: Mapping[str, Any] | None
) -> str | None:
    if isinstance(execution, dict):
        if execution.get("status") == "Aborted":
            return _normalized_code(execution.get("abort", {}).get("code"))
        if execution.get("status") == "Committed":
            return None
    diagnostics = report.get("diagnostics", [])
    fatal = [item for item in diagnostics if item.get("severity") == "fatal"]
    if fatal:
        return _normalized_code(fatal[0].get("code"))
    remaining = [
        item
        for item in diagnostics
        if item.get("code") not in _EVALUATION_ONLY_DIAGNOSTICS
    ]
    return _normalized_code(remaining[0].get("code")) if remaining else None


def _boundary_projection(
    configuration: Mapping[str, Any], bundle: Mapping[str, Any]
) -> _JSON:
    parameters = bundle["execution"]["parameters"]
    event_id = (
        str(parameters["reflection_event_id"])
        if bundle["initial_world"]["entities"][
            str(parameters["target_entity_id"])
        ].get("crossing")
        and not bundle["initial_world"]["entities"][
            str(parameters["target_entity_id"])
        ].get("authorized")
        else str(parameters["authorized_event_id"])
    )
    return boundary_reflection_projection(
        configuration,
        target_id=str(parameters["target_entity_id"]),
        anchor_id=str(parameters["reaction_anchor_id"]),
        controller_id=str(parameters["controller_id"]),
        event_id=event_id,
    )


def _evidence_projection(
    configuration: Mapping[str, Any], bundle: Mapping[str, Any]
) -> _JSON:
    parameters = bundle["execution"]["parameters"]
    return evidence_fusion_projection(
        configuration,
        artifact_id=str(parameters["artifact_id"]),
        event_id=str(parameters["event_id"]),
    )


PROJECTIONS: dict[ContractPair, Projection] = {
    BOUNDARY_REFLECTION_PAIR: _boundary_projection,
    EVIDENCE_FUSION_PAIR: _evidence_projection,
}


def _combined_checks(
    manifest: Mapping[str, Any], item: Mapping[str, Any]
) -> tuple[Mapping[str, Any], ...]:
    checks: list[Mapping[str, Any]] = []
    template = item.get("template")
    if template is not None:
        templates = manifest.get("templates", {})
        if template not in templates:
            raise ValueError(f"unknown golden template: {template!r}")
        checks.extend(templates[template])
    checks.extend(item.get("checks", []))
    return tuple(checks)


def _relative_golden_input(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(_REPOSITORY_ROOT.resolve()).as_posix()
    except ValueError as error:
        raise ValueError(
            "golden_input must identify a repository-owned frozen input"
        ) from error


def _golden_context(
    *,
    source_path: Path,
    golden_input: str | Path | None,
    variant_id: str | None,
    manifest_path: str | Path,
) -> GoldenContext | None:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    owned_input = source_path if golden_input is None else Path(golden_input)
    relative = _relative_golden_input(owned_input)
    case = next(
        (item for item in manifest["cases"] if item["input"] == relative),
        None,
    )
    if case is None:
        return None
    if variant_id is None:
        return GoldenContext(
            str(case["expectation_id"]),
            _combined_checks(manifest, case),
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
    return GoldenContext(
        f"{case['expectation_id']}::{variant_id}",
        _combined_checks(manifest, variant),
        tuple(variant.get("mutations", ())),
    )


def _mutated_bundle(
    frozen: FrozenArtifact, mutations: Sequence[Mapping[str, Any]]
) -> _JSON:
    document = json.loads(frozen.payload.decode("utf-8"))
    for mutation in mutations:
        pointer_set(document, str(mutation["pointer"]), mutation.get("value"))
    return document


def _expected_exact(
    checks: Sequence[Mapping[str, Any]], path: str, default: Any = None
) -> Any:
    for check in checks:
        if check.get("path") == path and check.get("mode") == "exact":
            return copy.deepcopy(check.get("expected"))
    return copy.deepcopy(default)


def _projected_generic_observation(
    report: Mapping[str, Any],
    execution: Mapping[str, Any] | None,
    replay: Mapping[str, Any] | None,
    configuration: Mapping[str, Any],
) -> _JSON:
    projected_report = copy.deepcopy(report)
    diagnostic_codes = {
        str(item.get("code")) for item in report.get("diagnostics", [])
    }
    if (
        report.get("status") == "ConditionallyFeasible"
        and isinstance(execution, dict)
        and execution.get("status") in {"Committed", "Aborted"}
        and diagnostic_codes <= _EVALUATION_ONLY_DIAGNOSTICS
    ):
        projected_report["status"] = "Feasible"

    projected_execution = copy.deepcopy(execution)
    if (
        isinstance(projected_execution, dict)
        and projected_execution.get("status") == "Aborted"
        and isinstance(projected_execution.get("abort"), dict)
    ):
        projected_execution["abort"]["code"] = _normalized_code(
            projected_execution["abort"].get("code")
        )

    return {
        "check": {"status": "Accepted"},
        "evaluation": {"status": "Evaluated", "report": projected_report},
        "execution": projected_execution,
        "replay": copy.deepcopy(replay),
        "final_world": copy.deepcopy(configuration),
    }


def _checks_with_prefix(
    checks: Sequence[Mapping[str, Any]], prefix: str
) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        check
        for check in checks
        if str(check.get("path", "")).startswith(prefix)
    )


def _boundary_accounting_matches(
    bundle: Mapping[str, Any], generic_ledgers: Mapping[str, Any]
) -> bool:
    parameters = bundle["execution"]["parameters"]
    target = bundle["initial_world"]["entities"][
        str(parameters["target_entity_id"])
    ]
    anchor = bundle["initial_world"]["entities"][
        str(parameters["reaction_anchor_id"])
    ]
    ledger = generic_ledgers.get(str(parameters["ledger_id"]), {})
    incident = float(target.get("normal_momentum_kg_m_s", 0.0))
    initial_anchor = float(anchor.get("normal_momentum_kg_m_s", 0.0))
    if bool(target.get("crossing")) and not bool(target.get("authorized")):
        mass = float(target["mass_kg"])
        restitution = float(parameters["coefficient_of_restitution"])
        expected_target = -restitution * incident
        expected_impulse = (1.0 + restitution) * incident
        expected_dissipated = (
            incident * incident / (2.0 * mass)
            - expected_target * expected_target / (2.0 * mass)
        )
    else:
        expected_target = incident
        expected_impulse = 0.0
        expected_dissipated = float(ledger.get("dissipated_energy_j", 0.0))
    return (
        abs(float(ledger.get("target_momentum_kg_m_s", 0.0)) - expected_target)
        <= 1e-12
        and abs(
            float(ledger.get("anchor_momentum_kg_m_s", 0.0))
            - (initial_anchor + expected_impulse)
        )
        <= 1e-12
        and abs(
            float(ledger.get("dissipated_energy_j", 0.0))
            - expected_dissipated
        )
        <= 1e-12
    )


def _implemented_comparisons(
    *,
    bundle: Mapping[str, Any],
    pair: ContractPair,
    legacy: Mapping[str, Any],
    legacy_golden: Mapping[str, Any],
    generic_report: Mapping[str, Any],
    generic_execution: Mapping[str, Any] | None,
    generic_replay: Mapping[str, Any] | None,
    generic_configuration: Mapping[str, Any],
    generic_ledgers: Mapping[str, Any],
    generic_golden: Mapping[str, Any],
    checks: Sequence[Mapping[str, Any]],
) -> _JSON:
    legacy_report = legacy.get("evaluation", {}).get("report", {})
    legacy_execution = legacy.get("execution")
    legacy_replay = legacy.get("replay")
    legacy_code = _terminal_diagnostic_code(legacy_report, legacy_execution)
    generic_code = _terminal_diagnostic_code(generic_report, generic_execution)

    expected_evaluation = _expected_exact(
        checks, "/evaluation/report/status", legacy_report.get("status")
    )
    expected_runtime = _expected_exact(
        checks,
        "/execution/status",
        None
        if not isinstance(legacy_execution, dict)
        else legacy_execution.get("status"),
    )
    expected_replay = _expected_exact(
        checks,
        "/replay/status",
        None if not isinstance(legacy_replay, dict) else legacy_replay.get("status"),
    )
    expected_code = _normalized_code(
        _expected_exact(checks, "/execution/abort/code", legacy_code)
    )

    projected_generic = _projected_generic_observation(
        generic_report,
        generic_execution,
        generic_replay,
        generic_configuration,
    )
    projected_status = projected_generic["evaluation"]["report"].get("status")
    final_checks = _checks_with_prefix(checks, "/final_world/")
    event_checks = tuple(
        check
        for check in checks
        if check.get("path") == "/execution/history_event_ids"
    )
    comparisons: _JSON = {
        "legacy_oracle": legacy_golden.get("status") == "PASS",
        "external_golden": generic_golden.get("status") == "PASS",
        "evaluation_status": legacy_report.get("status")
        == projected_status
        == expected_evaluation,
        "runtime_status": generic_execution is not None
        and generic_execution.get("status") == expected_runtime,
        "replay_status": generic_replay is not None
        and generic_replay.get("status") == expected_replay,
        "final_invariants": not final_checks
        or compare_checks(
            projected_generic,
            final_checks,
            expectation_id="shadow:generic:final",
        )["status"]
        == "PASS",
        "diagnostic_codes": legacy_code == generic_code == expected_code,
        "event_ids": not event_checks
        or compare_checks(
            projected_generic,
            event_checks,
            expectation_id="shadow:generic:events",
        )["status"]
        == "PASS",
    }

    if generic_execution is not None and expected_runtime == "Committed":
        projector = PROJECTIONS.get(pair)
        if projector is not None:
            comparisons["contract_projection"] = projector(
                legacy.get("final_world", {}), bundle
            ) == projector(generic_configuration, bundle)
        if pair == BOUNDARY_REFLECTION_PAIR:
            comparisons["contract_accounting"] = _boundary_accounting_matches(
                bundle, generic_ledgers
            )
        elif pair == EVIDENCE_FUSION_PAIR:
            parameters = bundle["execution"]["parameters"]
            ledger_id = str(parameters["ledger_id"])
            initial = bundle["initial_world"]["ledgers"][ledger_id]
            observed = generic_ledgers.get(ledger_id, {})
            comparisons["contract_accounting"] = (
                float(observed.get("consumed_energy_j", 0.0))
                == float(initial.get("consumed_energy_j", 0.0))
                + float(parameters["observation_energy_j"])
                and float(observed.get("available_energy_j", 0.0))
                == float(initial.get("available_energy_j", 0.0))
            )
    elif generic_execution is not None and expected_runtime == "Aborted":
        comparisons.update(
            {
                "abort_configuration_unchanged": generic_execution.get(
                    "configuration_unchanged"
                )
                is True,
                "abort_history_unchanged": generic_execution.get(
                    "history_unchanged"
                )
                is True,
                "abort_world_revision_unchanged": generic_execution.get(
                    "world_revision_unchanged"
                )
                is True,
            }
        )
    return comparisons


def run_shadow_file(
    path: str | Path,
    *,
    translators: ShadowTranslatorRegistry | None = None,
    golden_input: str | Path | None = None,
    variant_id: str | None = None,
    golden_manifest: str | Path = _DEFAULT_GOLDEN_MANIFEST,
) -> _JSON:
    """Run raw legacy and generic paths from one frozen byte snapshot."""

    source_path = Path(path)
    frozen = FrozenArtifact.from_path(source_path)
    golden = _golden_context(
        source_path=source_path,
        golden_input=golden_input,
        variant_id=variant_id,
        manifest_path=golden_manifest,
    )
    mutations: tuple[Mapping[str, Any], ...] = (
        () if golden is None else golden.mutations
    )
    bundle = _mutated_bundle(frozen, mutations)
    registry = translators or default_shadow_translators()
    translation = registry.resolve(bundle).translator(bundle)

    legacy = observe_frozen(default_service(), frozen, mutations=mutations)
    generic_report = translation.evaluator.evaluate_program(translation.program)
    generic_execution = None
    generic_replay = None
    generic_world = translation.world.clone()
    if translation.runtime is not None and generic_report["status"] in {
        "Feasible",
        "ConditionallyFeasible",
    }:
        initial = generic_world.clone()
        generic_execution = translation.runtime.execute(
            translation.program, generic_world
        )
        generic_replay = translation.runtime.replay(
            translation.program, initial, generic_execution
        )

    legacy_report = legacy.get("evaluation", {}).get("report", {})
    raw_status = {
        "legacy": legacy_report.get("status"),
        "generic": generic_report.get("status"),
    }
    normalized_status = (
        "ExecutablePendingOrCompletedAuthorityBinding"
        if raw_status
        == {"legacy": "Feasible", "generic": "ConditionallyFeasible"}
        else raw_status["legacy"]
        if raw_status["legacy"] == raw_status["generic"]
        else "Diverged"
    )
    comparisons: _JSON = {
        "source_bytes_frozen": frozen.payload == source_path.read_bytes(),
        "contract_pair_selected": translation.source_pair
        == bundle_contract_pair(bundle),
    }

    legacy_golden: _JSON = {"status": "PASS", "differences": []}
    generic_golden: _JSON = {"status": "PASS", "differences": []}
    checks: tuple[Mapping[str, Any], ...] = ()
    if golden is not None:
        checks = golden.checks
        legacy_golden = compare_checks(
            legacy,
            checks,
            expectation_id=f"{golden.expectation_id}:legacy",
        )
        generic_golden = compare_checks(
            _projected_generic_observation(
                generic_report,
                generic_execution,
                generic_replay,
                generic_world.configuration(),
            ),
            checks,
            expectation_id=f"{golden.expectation_id}:generic",
        )

    if translation.classification == "recognized-unsupported":
        legacy_codes = [
            item["code"] for item in legacy_report.get("diagnostics", [])
        ]
        generic_codes = [
            item["code"] for item in generic_report.get("diagnostics", [])
        ]
        comparisons.update(
            {
                "evaluation_status": raw_status
                == {"legacy": "Indeterminate", "generic": "Indeterminate"},
                "legacy_oracle": legacy.get("check", {}).get("status")
                == "Accepted",
                "unsupported_diagnostics": legacy_codes
                == generic_codes
                == ["UnsupportedSemanticSubset"],
                "no_runtime": generic_execution is None,
            }
        )
    else:
        if golden is None:
            raise ValueError(
                "implemented shadow migration requires an independent golden expectation"
            )
        comparisons.update(
            _implemented_comparisons(
                bundle=bundle,
                pair=translation.source_pair,
                legacy=legacy,
                legacy_golden=legacy_golden,
                generic_report=generic_report,
                generic_execution=generic_execution,
                generic_replay=generic_replay,
                generic_configuration=generic_world.configuration(),
                generic_ledgers=copy.deepcopy(generic_world.ledgers),
                generic_golden=generic_golden,
                checks=checks,
            )
        )

    return {
        "status": "PASS" if all(comparisons.values()) else "FAIL",
        "classification": translation.classification,
        "source_contract_pair": {
            "semantic": list(translation.source_pair[0]),
            "runtime": None
            if translation.source_pair[1] is None
            else list(translation.source_pair[1]),
        },
        "golden_expectation_id": None
        if golden is None
        else golden.expectation_id,
        "raw_evaluation_status": raw_status,
        "normalized_evaluation_status": normalized_status,
        "normalized_diagnostic_code": _terminal_diagnostic_code(
            generic_report, generic_execution
        ),
        "legacy": legacy,
        "legacy_golden": legacy_golden,
        "program": translation.program,
        "generic_evaluation": generic_report,
        "generic_execution": generic_execution,
        "generic_replay": generic_replay,
        "generic_golden": generic_golden,
        "generic_final_world": generic_world.configuration(),
        "generic_final_ledgers": copy.deepcopy(generic_world.ledgers),
        "comparisons": comparisons,
    }


__all__ = [
    "BOUNDARY_REFLECTION_PAIR",
    "DIAGNOSTIC_ALIASES",
    "EVIDENCE_FUSION_PAIR",
    "GoldenContext",
    "ShadowTranslation",
    "ShadowTranslatorRegistration",
    "ShadowTranslatorRegistry",
    "UNSUPPORTED_CONTRACTS",
    "_generic_executor",
    "bundle_contract_pair",
    "default_shadow_translators",
    "run_shadow_file",
    "translate_boundary_reflection",
    "translate_evidence_fusion",
]
