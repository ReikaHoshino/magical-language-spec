"""Public SpellInstanceBundle service backed by the generic MagicalProgram path."""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.compatibility import CompatibilityAdmissionError, admit_compatibility_decisions
from src.evaluator.handler_registry import (
    SemanticHandlerError,
    SemanticHandlerRegistration,
    SemanticHandlerRegistry,
)
from src.evaluator.schema import SchemaValidationError, require_valid, validate_nsr
from src.extensions.parameter_schemas import (
    BOUNDARY_REFLECTION_PARAMETERS,
    EVIDENCE_FUSION_PARAMETERS,
    EXPLOSION_PARAMETERS,
    STAGED_TREATMENT_PARAMETERS,
)
from src.migration.magical_program import (
    ProgramTranslatorRegistry,
    default_program_translators,
    translate_bundle,
)
from src.runtime.executor_registry import (
    ParameterReference,
    RuntimeExecutorError,
    RuntimeExecutorRegistration,
    RuntimeExecutorRegistry,
)
from src.runtime.sandbox import PreparedPlan, SandboxWorld

from .envelope import (
    DEFAULT_HOST_CEILINGS,
    ArtifactIngressError,
    HostCeilings,
    decode_artifact_file,
)
from .execution_contract_registry import (
    ExecutionContractError,
    ExecutionContractRegistration,
    ExecutionContractRegistry,
)
from .loader_registry import (
    ArtifactLoaderRegistration,
    ArtifactLoaderRegistry,
    ArtifactRegistryError,
)

_JSON = dict[str, Any]
_STRING = {"type": "string", "minLength": 1}
_SELECTOR = {
    "type": "object",
    "required": ["kind"],
    "properties": {"kind": _STRING, "name": _STRING, "owner_id": _STRING},
    "additionalProperties": False,
}
_GENERIC_PARAMETERS = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": [
        "source_entity_id",
        "target_entity_id",
        "ledger_id",
        "energy_j",
        "result_state",
        "result_world_revision",
        "event_id",
    ],
    "properties": {
        "source_entity_id": _STRING,
        "target_entity_id": _STRING,
        "ledger_id": _STRING,
        "energy_j": {"type": "number", "minimum": 0},
        "result_state": _STRING,
        "result_world_revision": _STRING,
        "event_id": _STRING,
    },
    "additionalProperties": False,
}
_PREPARE_BOUND_PARAMETERS = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": [
        "source_selector",
        "destination_selector",
        "binding_mode",
        "simulate_precommit_change",
        "mutated_source_state_revision",
        "mutated_destination_state_revision",
        "late_candidate_id",
        "late_candidate_state_revision",
        "transit_lease_id",
        "attached_object_policy",
        "result_world_revision",
        "event_id",
    ],
    "properties": {
        "source_selector": _SELECTOR,
        "destination_selector": _SELECTOR,
        "binding_mode": {"enum": ["PrepareBound", "Dynamic"]},
        "simulate_precommit_change": {"type": "boolean"},
        "mutated_source_state_revision": _STRING,
        "mutated_destination_state_revision": _STRING,
        "late_candidate_id": _STRING,
        "late_candidate_state_revision": _STRING,
        "transit_lease_id": _STRING,
        "attached_object_policy": {"const": "ExplicitExcluded"},
        "result_world_revision": _STRING,
        "event_id": _STRING,
    },
    "additionalProperties": False,
}
_REACTIVE_PARAMETERS = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": [
        "controller_id",
        "reactive_microstep_budget",
        "external_events",
        "generated_event_prefix",
        "tick_id",
        "emergency_stop_on_exhaustion",
    ],
    "properties": {
        "controller_id": _STRING,
        "reactive_microstep_budget": {"type": "integer", "minimum": 1},
        "external_events": {
            "type": "array",
            "minItems": 3,
            "items": {
                "type": "object",
                "required": ["event_id", "target_entity_id"],
                "properties": {
                    "event_id": _STRING,
                    "target_entity_id": _STRING,
                },
                "additionalProperties": False,
            },
        },
        "generated_event_prefix": _STRING,
        "tick_id": _STRING,
        "emergency_stop_on_exhaustion": {"type": "boolean"},
    },
    "additionalProperties": False,
}
_EMPTY_PARAMETERS = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}

_DIAGNOSTIC_ALIASES = {
    "ProgramAuthorityError": "AuthorityError",
    "ProgramLeaseError": "AuthorityError",
    "ProgramResolutionFailure": "ResolutionFailure",
    "ProgramResolutionAmbiguous": "ResolutionFailure",
    "ProgramStaleIdentity": "ResolutionFailure",
    "ProgramAccountingMissing": "ConservationProofFailure",
    "ProgramEnergyInsufficient": "ConservationProofFailure",
    "ProgramCommitInternalFailure": "ExtensionExecutionFailure",
}
_EVALUATION_ONLY_DIAGNOSTICS = {
    "ProgramResolutionDeferred",
    "ProgramRuntimeRevalidationRequired",
}


def _diagnostic(
    code: str, message: str, stage: str = "INGRESS"
) -> dict[str, str]:
    return {
        "stage": stage,
        "code": code,
        "severity": "fatal",
        "message": message,
    }


def _subset(expected: Any, observed: Any) -> bool:
    if isinstance(expected, dict):
        return isinstance(observed, dict) and all(
            key in observed and _subset(value, observed[key])
            for key, value in expected.items()
        )
    if isinstance(expected, list):
        return expected == observed
    return expected == observed


def _spell_loader(document: dict[str, Any]) -> dict[str, Any]:
    require_valid("spell-instance-bundle.schema.json", document)
    return copy.deepcopy(document)


def _unreachable_handler(bundle: dict[str, Any]) -> dict[str, Any]:
    del bundle
    raise RuntimeError("validation-only semantic registration was executed")


def _unreachable_executor(
    prepared: PreparedPlan, world: SandboxWorld
) -> dict[str, Any]:
    del prepared, world
    raise RuntimeError("validation-only runtime registration was executed")


def _normalize_code(code: str | None) -> str | None:
    if code is None:
        return None
    return _DIAGNOSTIC_ALIASES.get(code, code)


def _public_report(report: Mapping[str, Any]) -> _JSON:
    projected = copy.deepcopy(dict(report))
    diagnostics = projected.get("diagnostics", [])
    for diagnostic in diagnostics:
        diagnostic["code"] = _normalize_code(diagnostic.get("code"))
    codes = {str(item.get("code")) for item in report.get("diagnostics", [])}
    if (
        report.get("status") == "ConditionallyFeasible"
        and codes <= _EVALUATION_ONLY_DIAGNOSTICS
    ):
        projected["status"] = "Feasible"
    return projected


def _public_execution(execution: Mapping[str, Any] | None) -> _JSON | None:
    if execution is None:
        return None
    projected = copy.deepcopy(dict(execution))
    abort = projected.get("abort")
    if isinstance(abort, dict):
        abort["code"] = _normalize_code(abort.get("code"))
    return projected


@dataclass(frozen=True)
class AdmittedSpellInstance:
    """Immutable input snapshot decoded exactly once."""

    canonical_document: bytes
    source_digest: str
    check_result: _JSON

    @classmethod
    def create(
        cls, bundle: _JSON, check_result: _JSON
    ) -> "AdmittedSpellInstance":
        canonical = json.dumps(
            bundle,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return cls(
            canonical,
            hashlib.sha256(canonical).hexdigest(),
            copy.deepcopy(check_result),
        )

    def bundle(self) -> _JSON:
        return json.loads(self.canonical_document.decode("utf-8"))


class SpellInstanceService:
    """Admission-compatible service with generic post-admission ownership."""

    def __init__(
        self,
        artifact_registry: ArtifactLoaderRegistry,
        semantic_registry: SemanticHandlerRegistry,
        runtime_registry: RuntimeExecutorRegistry,
        execution_registry: ExecutionContractRegistry,
        program_translators: ProgramTranslatorRegistry,
        *,
        host_ceilings: HostCeilings = DEFAULT_HOST_CEILINGS,
    ) -> None:
        self.artifact_registry = artifact_registry
        self.semantic_registry = semantic_registry
        self.runtime_registry = runtime_registry
        self.execution_registry = execution_registry
        self.program_translators = program_translators
        self.host_ceilings = host_ceilings

    def _load(
        self, path: str | Path, *, input_kind: str | None = None
    ) -> _JSON:
        document = decode_artifact_file(path, ceilings=self.host_ceilings)
        if input_kind is not None and document.get("artifact_kind") != input_kind:
            raise ArtifactIngressError(
                "ArtifactKindMismatch",
                "Explicit input kind does not match the in-document artifact_kind.",
            )
        return self.artifact_registry.load(document)

    def _enforce_host_ceilings(self, bundle: _JSON) -> _JSON:
        ceilings = self.host_ceilings
        parameters = json.dumps(
            bundle["execution"]["parameters"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        if len(parameters) > ceilings.max_parameter_bytes:
            raise ArtifactIngressError(
                "HostParameterLimitExceeded",
                "Execution parameters exceed the immutable host byte ceiling.",
            )
        if len(bundle["initial_world"]["entities"]) > ceilings.max_entities:
            raise ArtifactIngressError(
                "HostEntityLimitExceeded",
                "Initial WorldState exceeds the immutable host entity ceiling.",
            )
        if len(bundle["initial_world"]["history"]) > ceilings.max_history_records:
            raise ArtifactIngressError(
                "HostHistoryLimitExceeded",
                "Initial History exceeds the immutable host record ceiling.",
            )
        if float(bundle["execution"]["energy_budget_j"]) > ceilings.max_energy_j:
            raise ArtifactIngressError(
                "HostEnergyLimitExceeded",
                "Execution Energy exceeds the immutable host ceiling.",
            )

        declared = bundle["profiles"]["sandbox"]["limits"]
        owned = {
            "max_energy_j": ceilings.max_energy_j,
            "max_events_per_commit": ceilings.max_events_per_commit,
            "max_microsteps_per_tick": ceilings.max_microsteps_per_tick,
            "max_concurrency": ceilings.max_concurrency,
        }
        effective: dict[str, int | float] = {}
        for key, maximum in owned.items():
            value = declared[key]
            if value > maximum:
                raise ArtifactIngressError(
                    "HostSandboxLimitExceeded",
                    f"Artifact-authored {key} exceeds the immutable host ceiling.",
                )
            effective[key] = min(value, maximum)
        return {
            "host": owned,
            "artifact": copy.deepcopy(declared),
            "effective": effective,
        }

    def _check_bundle(self, bundle: _JSON) -> _JSON:
        validate_nsr(bundle["ingress"]["payload"])
        compatibility = admit_compatibility_decisions(
            bundle["compatibility"]["decisions"],
            required_domains=bundle["compatibility"]["required_domains"],
        )
        if not compatibility.admitted:
            raise ArtifactIngressError(
                "CompatibilityAdmissionDenied",
                "Compatibility gate returned "
                f"{compatibility.status.value}: {compatibility.reason_codes!r}.",
            )
        semantic = bundle["semantic_contract"]
        semantic_registration = self.semantic_registry.resolve(
            semantic["contract_id"], semantic["revision"]
        )
        if semantic_registration.support_level != bundle["support_level"]:
            raise ArtifactIngressError(
                "SupportLevelMismatch",
                "Bundle support_level disagrees with the registered semantic contract.",
            )
        runtime = bundle.get("runtime_contract")
        runtime_registration = None
        if bundle["support_level"] == "implemented" and runtime is not None:
            runtime_registration = self.runtime_registry.resolve(
                runtime["contract_id"], runtime["revision"]
            )
        if (
            bundle["support_level"] == "implemented"
            and bundle["expected_outcome"].get("runtime_status") is not None
            and runtime is None
        ):
            raise ArtifactIngressError(
                "RuntimeContractMissing",
                "Executable expected outcome requires a runtime contract.",
            )
        semantic_identity = (
            semantic["contract_id"],
            semantic["revision"],
        )
        runtime_identity = (
            None
            if runtime is None
            else (runtime["contract_id"], runtime["revision"])
        )
        execution_registration = self.execution_registry.resolve(
            semantic_identity, runtime_identity
        )
        if runtime_registration is None:
            if bundle["execution"]["parameters"]:
                raise RuntimeExecutorError(
                    "ExecutionParameterUnknown",
                    "A non-runtime execution contract admits no parameters.",
                )
        else:
            self.runtime_registry.validate_parameters(
                runtime_registration,
                bundle["execution"]["parameters"],
                bundle,
            )
        self.program_translators.resolve(bundle)
        limits = self._enforce_host_ceilings(bundle)
        return {
            "status": "Accepted",
            "artifact_kind": bundle["artifact_kind"],
            "artifact_version": bundle["artifact_version"],
            "instance_id": bundle["instance_id"],
            "support_level": bundle["support_level"],
            "semantic_contract": copy.deepcopy(semantic),
            "runtime_contract": copy.deepcopy(runtime),
            "execution_contract": {
                "contract_id": execution_registration.contract_id,
                "revision": execution_registration.revision,
            },
            "compatibility": compatibility.to_dict(),
            "limits": limits,
        }

    def _admit_file(
        self, path: str | Path, *, input_kind: str | None = None
    ) -> AdmittedSpellInstance:
        bundle = self._load(path, input_kind=input_kind)
        checked = self._check_bundle(bundle)
        admitted = AdmittedSpellInstance.create(bundle, checked)
        checked["source_digest"] = admitted.source_digest
        return AdmittedSpellInstance(
            admitted.canonical_document,
            admitted.source_digest,
            checked,
        )

    @staticmethod
    def _rejection(error: Exception) -> _JSON:
        if isinstance(error, SchemaValidationError):
            return {
                "status": "Rejected",
                "diagnostics": [
                    _diagnostic("ArtifactSchemaViolation", message)
                    for message in error.errors
                ],
            }
        if isinstance(error, CompatibilityAdmissionError):
            return {
                "status": "Rejected",
                "diagnostics": [
                    _diagnostic("CompatibilityEnvelopeInvalid", str(error))
                ],
            }
        return {
            "status": "Rejected",
            "diagnostics": [
                _diagnostic(getattr(error, "code", "ArtifactRejected"), str(error))
            ],
        }

    def check_file(
        self, path: str | Path, *, input_kind: str | None = None
    ) -> _JSON:
        try:
            return copy.deepcopy(
                self._admit_file(path, input_kind=input_kind).check_result
            )
        except (
            ArtifactIngressError,
            ArtifactRegistryError,
            SemanticHandlerError,
            RuntimeExecutorError,
            ExecutionContractError,
            SchemaValidationError,
            CompatibilityAdmissionError,
            KeyError,
        ) as error:
            return self._rejection(error)

    def evaluate_admitted(self, admitted: AdmittedSpellInstance) -> _JSON:
        try:
            translation = translate_bundle(
                admitted.bundle(), translators=self.program_translators
            )
            report = translation.evaluator.evaluate_program(translation.program)
        except Exception as error:
            return {
                "status": "Rejected",
                "check": copy.deepcopy(admitted.check_result),
                "diagnostics": [
                    _diagnostic(
                        "ExtensionEvaluationFailure",
                        "Generic MagicalProgram translation or evaluation failed closed.",
                        stage="ELABORATE",
                    )
                    | {"internal_cause": type(error).__name__}
                ],
            }
        return {
            "status": "Evaluated",
            "check": copy.deepcopy(admitted.check_result),
            "report": _public_report(report),
        }

    def evaluate_file(
        self, path: str | Path, *, input_kind: str | None = None
    ) -> _JSON:
        try:
            admitted = self._admit_file(path, input_kind=input_kind)
        except (
            ArtifactIngressError,
            ArtifactRegistryError,
            SemanticHandlerError,
            RuntimeExecutorError,
            ExecutionContractError,
            SchemaValidationError,
            CompatibilityAdmissionError,
            KeyError,
        ) as error:
            return {"status": "Rejected", "check": self._rejection(error)}
        return self.evaluate_admitted(admitted)

    def run_admitted(self, admitted: AdmittedSpellInstance) -> _JSON:
        bundle = admitted.bundle()
        try:
            translation = translate_bundle(
                bundle, translators=self.program_translators
            )
            raw_report = translation.evaluator.evaluate_program(translation.program)
        except Exception as error:
            return {
                "status": "FAIL",
                "evaluation": {
                    "status": "Rejected",
                    "check": copy.deepcopy(admitted.check_result),
                    "diagnostics": [
                        _diagnostic(
                            "ExtensionEvaluationFailure",
                            "Generic MagicalProgram translation or evaluation failed closed.",
                            stage="ELABORATE",
                        )
                        | {"internal_cause": type(error).__name__}
                    ],
                },
            }

        report = _public_report(raw_report)
        evaluated = {
            "status": "Evaluated",
            "check": copy.deepcopy(admitted.check_result),
            "report": report,
        }
        expected = bundle["expected_outcome"]
        comparison: _JSON = {
            "evaluation_status": report["status"]
            == expected["evaluation_status"]
        }
        expected_codes = [
            _normalize_code(str(code))
            for code in expected.get("diagnostic_codes", [])
        ]

        if (
            translation.runtime is None
            or raw_report["status"] not in {"Feasible", "ConditionallyFeasible"}
        ):
            observed_codes = [
                _normalize_code(item.get("code"))
                for item in report.get("diagnostics", [])
            ]
            comparison["diagnostic_codes"] = all(
                code in observed_codes for code in expected_codes
            )
            passed = all(comparison.values())
            return {
                "status": "PASS" if passed else "FAIL",
                "evaluation": evaluated,
                "comparison": comparison,
                "execution": None,
                "replay": None,
            }

        world = translation.world.clone()
        initial = world.clone()
        raw_execution = translation.runtime.execute(translation.program, world)
        execution = _public_execution(raw_execution)
        comparison["runtime_status"] = execution["status"] == expected.get(
            "runtime_status"
        )
        observed_code = _normalize_code(
            execution.get("abort", {}).get("code")
        )
        comparison["diagnostic_codes"] = all(
            code == observed_code for code in expected_codes
        )
        comparison["final_invariants"] = _subset(
            expected.get("final_invariants", {}), world.configuration()
        )
        replay = translation.runtime.replay(
            translation.program, initial, raw_execution
        )
        comparison["replay_status"] = replay["status"] == expected.get(
            "replay_status"
        )
        if execution["status"] == "Committed":
            if "expected_event_ids" in expected:
                observed_events = execution.get("history_event_ids", [])
                comparison["expected_event_ids"] = all(
                    event_id in observed_events
                    for event_id in expected["expected_event_ids"]
                )
            if "expected_result_hash" in expected:
                comparison["expected_result_hash"] = (
                    execution.get("result_state_hash")
                    == expected["expected_result_hash"]
                )
        passed = all(comparison.values())
        return {
            "status": "PASS" if passed else "FAIL",
            "evaluation": evaluated,
            "execution": execution,
            "replay": replay,
            "final_world": world.configuration(),
            "comparison": comparison,
        }

    def run_file(
        self, path: str | Path, *, input_kind: str | None = None
    ) -> _JSON:
        try:
            admitted = self._admit_file(path, input_kind=input_kind)
        except (
            ArtifactIngressError,
            ArtifactRegistryError,
            SemanticHandlerError,
            RuntimeExecutorError,
            ExecutionContractError,
            SchemaValidationError,
            CompatibilityAdmissionError,
            KeyError,
        ) as error:
            return {
                "status": "FAIL",
                "evaluation": {
                    "status": "Rejected",
                    "check": self._rejection(error),
                },
            }
        return self.run_admitted(admitted)


def _register_runtime(
    registry: RuntimeExecutorRegistry,
    contract_id: str,
    schema: _JSON,
    references: tuple[ParameterReference, ...] = (),
) -> None:
    registry.register(
        RuntimeExecutorRegistration(
            contract_id,
            "1",
            _unreachable_executor,
            schema,
            references,
        )
    )


def _register_pair(
    semantic: SemanticHandlerRegistry,
    execution: ExecutionContractRegistry,
    semantic_id: str,
    support_level: str,
    runtime_id: str | None,
) -> None:
    semantic.register(
        SemanticHandlerRegistration(
            semantic_id,
            "1",
            support_level,
            _unreachable_handler,
        )
    )
    execution.register(
        ExecutionContractRegistration(
            contract_id=f"execution:{semantic_id}",
            revision="1",
            semantic_contract=(semantic_id, "1"),
            runtime_contract=None if runtime_id is None else (runtime_id, "1"),
        )
    )


def default_service() -> SpellInstanceService:
    artifact = ArtifactLoaderRegistry()
    semantic = SemanticHandlerRegistry()
    runtime = RuntimeExecutorRegistry()
    execution = ExecutionContractRegistry()
    artifact.register(
        ArtifactLoaderRegistration("SpellInstanceBundle", "0", _spell_loader)
    )

    _register_runtime(
        runtime,
        "runtime.generic-transition",
        _GENERIC_PARAMETERS,
        (
            ParameterReference("source_entity_id", "entities"),
            ParameterReference("target_entity_id", "entities"),
            ParameterReference("ledger_id", "ledgers"),
        ),
    )
    _register_runtime(
        runtime,
        "runtime.boundary-controller",
        BOUNDARY_REFLECTION_PARAMETERS,
        (
            ParameterReference("target_entity_id", "entities"),
            ParameterReference("reaction_anchor_id", "entities"),
            ParameterReference("ledger_id", "ledgers"),
        ),
    )
    _register_runtime(
        runtime,
        "runtime.staged-treatment",
        STAGED_TREATMENT_PARAMETERS,
        tuple(
            ParameterReference(field, "entities")
            for field in (
                "patient_id",
                "proxy_id",
                "sink_id",
                "donor_id",
                "energy_reservoir_id",
            )
        )
        + (
            ParameterReference("patient_lease_id", "leases"),
            ParameterReference("ledger_id", "ledgers"),
        ),
    )
    _register_runtime(
        runtime,
        "runtime.evidence-artifact",
        EVIDENCE_FUSION_PARAMETERS,
        (
            ParameterReference("subject_id", "entities"),
            ParameterReference("ledger_id", "ledgers"),
        ),
    )
    _register_runtime(
        runtime,
        "runtime.explosion",
        EXPLOSION_PARAMETERS,
        (
            ParameterReference("origin_entity_id", "entities"),
            ParameterReference("reaction_anchor_id", "entities"),
            ParameterReference("ledger_id", "ledgers"),
            ParameterReference("capability_id", "capabilities"),
            ParameterReference("lease_id", "leases"),
        ),
    )
    _register_runtime(
        runtime,
        "runtime.prepare-bound-transit",
        _PREPARE_BOUND_PARAMETERS,
        (ParameterReference("transit_lease_id", "leases"),),
    )
    _register_runtime(
        runtime,
        "runtime.reactive-hydra",
        _REACTIVE_PARAMETERS,
        (ParameterReference("controller_id", "controllers"),),
    )

    for semantic_id, runtime_id in (
        ("example.generic-transition", "runtime.generic-transition"),
        ("controller.boundary-reflection", "runtime.boundary-controller"),
        ("treatment.staged-repair", "runtime.staged-treatment"),
        ("evidence.snapshot-fusion", "runtime.evidence-artifact"),
        ("dynamics.explosion", "runtime.explosion"),
        ("debug.pathological-planning", None),
        ("debug.prepare-bound-transit", "runtime.prepare-bound-transit"),
        ("debug.reactive-budget", "runtime.reactive-hydra"),
    ):
        _register_pair(
            semantic,
            execution,
            semantic_id,
            "implemented",
            runtime_id,
        )
    for semantic_id in (
        "light.guidance",
        "dynamics.levitation",
        "matter.purification",
        "observer.poison-detection",
    ):
        _register_pair(
            semantic,
            execution,
            semantic_id,
            "recognized-unsupported",
            None,
        )

    return SpellInstanceService(
        artifact,
        semantic,
        runtime,
        execution,
        default_program_translators(),
    )


__all__ = ["AdmittedSpellInstance", "SpellInstanceService", "default_service"]
