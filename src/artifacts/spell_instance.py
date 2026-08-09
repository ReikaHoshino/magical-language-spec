"""Generic single-file SpellInstanceBundle check/eval/run service."""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.compatibility import CompatibilityAdmissionError, admit_compatibility_decisions
from src.evaluator.handler_registry import SemanticHandlerError, SemanticHandlerRegistry
from src.evaluator.schema import SchemaValidationError, require_valid, validate_nsr
from src.extensions.registration import register_default_extensions
from src.runtime.engine import ReferenceRuntimeEngine, SandboxProfile
from src.runtime.executor_registry import RuntimeExecutorError, RuntimeExecutorRegistry
from src.runtime.sandbox import PreparedPlan, RuntimeExecutionError, SandboxRuntime, SandboxWorld

from .envelope import ArtifactIngressError, DEFAULT_HOST_CEILINGS, HostCeilings, decode_artifact_file
from .execution_contract_registry import ExecutionContractError, ExecutionContractRegistry
from .loader_registry import ArtifactLoaderRegistration, ArtifactLoaderRegistry, ArtifactRegistryError


def _diagnostic(code: str, message: str, stage: str = "INGRESS") -> dict[str, str]:
    return {"stage": stage, "code": code, "severity": "fatal", "message": message}


def _subset(expected: Any, observed: Any) -> bool:
    if isinstance(expected, dict):
        return isinstance(observed, dict) and all(key in observed and _subset(value, observed[key]) for key, value in expected.items())
    if isinstance(expected, list):
        return expected == observed
    return expected == observed


def _spell_loader(document: dict[str, Any]) -> dict[str, Any]:
    require_valid("spell-instance-bundle.schema.json", document)
    return copy.deepcopy(document)


@dataclass(frozen=True)
class AdmittedSpellInstance:
    """Immutable snapshot that is decoded from the input path exactly once."""

    canonical_document: bytes
    source_digest: str
    check_result: dict[str, Any]

    @classmethod
    def create(cls, bundle: dict[str, Any], check_result: dict[str, Any]) -> "AdmittedSpellInstance":
        canonical = json.dumps(bundle, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return cls(canonical, hashlib.sha256(canonical).hexdigest(), copy.deepcopy(check_result))

    def bundle(self) -> dict[str, Any]:
        return json.loads(self.canonical_document.decode("utf-8"))


class RegisteredSandboxRuntime(SandboxRuntime):
    """Sandbox runtime whose extension effects are selected by contract registry."""

    def __init__(self, registry: RuntimeExecutorRegistry, *, runtime_profile: dict[str, Any]) -> None:
        super().__init__(runtime_profile=runtime_profile)
        self.registry = registry

    def prepare(self, report: dict[str, Any], world: SandboxWorld) -> PreparedPlan:
        prepared = super().prepare(report, world)
        contract = prepared.kernel_plan.get("runtime_contract")
        if isinstance(contract, dict):
            registration = self.registry.resolve(str(contract.get("contract_id")), str(contract.get("revision")))
            if registration.precommit_hook is not None:
                registration.precommit_hook(prepared, world)
        return prepared

    def _execute_supported_plan(self, prepared: PreparedPlan, world: SandboxWorld) -> dict[str, Any]:
        contract = prepared.kernel_plan.get("runtime_contract")
        if not isinstance(contract, dict):
            raise RuntimeExecutionError("UnsupportedRuntimeSubset", "Prepared plan has no registered runtime contract.", stage="COMMIT")
        try:
            registration = self.registry.resolve(str(contract.get("contract_id")), str(contract.get("revision")))
        except RuntimeExecutorError as error:
            raise RuntimeExecutionError(error.code, str(error), stage="COMMIT") from error
        try:
            return registration.executor(prepared, world)
        except RuntimeExecutionError:
            raise
        except Exception as error:
            raise RuntimeExecutionError(
                "ExtensionExecutionFailure",
                "Registered extension execution failed closed.",
                stage="COMMIT",
                internal_cause=type(error).__name__,
            ) from error


class SpellInstanceService:
    def __init__(
        self,
        artifact_registry: ArtifactLoaderRegistry,
        semantic_registry: SemanticHandlerRegistry,
        runtime_registry: RuntimeExecutorRegistry,
        execution_registry: ExecutionContractRegistry,
        *,
        host_ceilings: HostCeilings = DEFAULT_HOST_CEILINGS,
    ) -> None:
        self.artifact_registry = artifact_registry
        self.semantic_registry = semantic_registry
        self.runtime_registry = runtime_registry
        self.execution_registry = execution_registry
        self.host_ceilings = host_ceilings

    def _load(self, path: str | Path, *, input_kind: str | None = None) -> dict[str, Any]:
        document = decode_artifact_file(path, ceilings=self.host_ceilings)
        if input_kind is not None and document.get("artifact_kind") != input_kind:
            raise ArtifactIngressError("ArtifactKindMismatch", "Explicit input kind does not match the in-document artifact_kind.")
        return self.artifact_registry.load(document)

    def _enforce_host_ceilings(self, bundle: dict[str, Any]) -> dict[str, Any]:
        ceilings = self.host_ceilings
        parameters = json.dumps(bundle["execution"]["parameters"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        if len(parameters) > ceilings.max_parameter_bytes:
            raise ArtifactIngressError("HostParameterLimitExceeded", "Execution parameters exceed the immutable host byte ceiling.")
        if len(bundle["initial_world"]["entities"]) > ceilings.max_entities:
            raise ArtifactIngressError("HostEntityLimitExceeded", "Initial WorldState exceeds the immutable host entity ceiling.")
        if len(bundle["initial_world"]["history"]) > ceilings.max_history_records:
            raise ArtifactIngressError("HostHistoryLimitExceeded", "Initial History exceeds the immutable host record ceiling.")
        if float(bundle["execution"]["energy_budget_j"]) > ceilings.max_energy_j:
            raise ArtifactIngressError("HostEnergyLimitExceeded", "Execution Energy exceeds the immutable host ceiling.")

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
                raise ArtifactIngressError("HostSandboxLimitExceeded", f"Artifact-authored {key} exceeds the immutable host ceiling.")
            effective[key] = min(value, maximum)
        return {"host": owned, "artifact": copy.deepcopy(declared), "effective": effective}

    def _check_bundle(self, bundle: dict[str, Any]) -> dict[str, Any]:
        validate_nsr(bundle["ingress"]["payload"])
        compatibility = admit_compatibility_decisions(bundle["compatibility"]["decisions"], required_domains=bundle["compatibility"]["required_domains"])
        if not compatibility.admitted:
            raise ArtifactIngressError("CompatibilityAdmissionDenied", f"Compatibility gate returned {compatibility.status.value}: {compatibility.reason_codes!r}.")
        semantic = bundle["semantic_contract"]
        semantic_registration = self.semantic_registry.resolve(semantic["contract_id"], semantic["revision"])
        if semantic_registration.support_level != bundle["support_level"]:
            raise ArtifactIngressError("SupportLevelMismatch", "Bundle support_level disagrees with the registered semantic contract.")
        runtime = bundle.get("runtime_contract")
        runtime_registration = None
        if bundle["support_level"] == "implemented" and runtime is not None:
            runtime_registration = self.runtime_registry.resolve(runtime["contract_id"], runtime["revision"])
        if bundle["support_level"] == "implemented" and bundle["expected_outcome"].get("runtime_status") is not None and runtime is None:
            raise ArtifactIngressError("RuntimeContractMissing", "Executable expected outcome requires a runtime contract.")
        semantic_identity = (semantic["contract_id"], semantic["revision"])
        runtime_identity = None if runtime is None else (runtime["contract_id"], runtime["revision"])
        execution_registration = self.execution_registry.resolve(semantic_identity, runtime_identity)
        if runtime_registration is None:
            if bundle["execution"]["parameters"]:
                raise RuntimeExecutorError("ExecutionParameterUnknown", "A non-runtime execution contract admits no parameters.")
        else:
            self.runtime_registry.validate_parameters(runtime_registration, bundle["execution"]["parameters"], bundle)
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

    def _admit_file(self, path: str | Path, *, input_kind: str | None = None) -> AdmittedSpellInstance:
        bundle = self._load(path, input_kind=input_kind)
        checked = self._check_bundle(bundle)
        admitted = AdmittedSpellInstance.create(bundle, checked)
        checked["source_digest"] = admitted.source_digest
        return AdmittedSpellInstance(admitted.canonical_document, admitted.source_digest, checked)

    @staticmethod
    def _rejection(error: Exception) -> dict[str, Any]:
        if isinstance(error, SchemaValidationError):
            return {"status": "Rejected", "diagnostics": [_diagnostic("ArtifactSchemaViolation", message) for message in error.errors]}
        if isinstance(error, CompatibilityAdmissionError):
            return {"status": "Rejected", "diagnostics": [_diagnostic("CompatibilityEnvelopeInvalid", str(error))]}
        return {"status": "Rejected", "diagnostics": [_diagnostic(getattr(error, "code", "ArtifactRejected"), str(error))]}

    def check_file(self, path: str | Path, *, input_kind: str | None = None) -> dict[str, Any]:
        try:
            return copy.deepcopy(self._admit_file(path, input_kind=input_kind).check_result)
        except (ArtifactIngressError, ArtifactRegistryError, SemanticHandlerError, RuntimeExecutorError, ExecutionContractError, SchemaValidationError, CompatibilityAdmissionError) as error:
            return self._rejection(error)

    def evaluate_admitted(self, admitted: AdmittedSpellInstance) -> dict[str, Any]:
        bundle = admitted.bundle()
        contract = bundle["semantic_contract"]
        try:
            report = self.semantic_registry.resolve(contract["contract_id"], contract["revision"]).handler(bundle)
        except (ArtifactIngressError, SemanticHandlerError, SchemaValidationError) as error:
            return {"status": "Rejected", "check": copy.deepcopy(admitted.check_result), "diagnostics": self._rejection(error)["diagnostics"]}
        except Exception as error:
            return {
                "status": "Rejected",
                "check": copy.deepcopy(admitted.check_result),
                "diagnostics": [_diagnostic("ExtensionEvaluationFailure", "Registered semantic handler failed closed.", stage="ELABORATE") | {"internal_cause": type(error).__name__}],
            }
        return {"status": "Evaluated", "check": copy.deepcopy(admitted.check_result), "report": report}

    def evaluate_file(self, path: str | Path, *, input_kind: str | None = None) -> dict[str, Any]:
        try:
            admitted = self._admit_file(path, input_kind=input_kind)
        except (ArtifactIngressError, ArtifactRegistryError, SemanticHandlerError, RuntimeExecutorError, ExecutionContractError, SchemaValidationError, CompatibilityAdmissionError) as error:
            return {"status": "Rejected", "check": self._rejection(error)}
        return self.evaluate_admitted(admitted)

    @staticmethod
    def _world(bundle: dict[str, Any]) -> SandboxWorld:
        source = bundle["initial_world"]
        runtime_state = copy.deepcopy(source.get("runtime_state", {}))
        runtime_state.setdefault("runtime_profile", copy.deepcopy(bundle["profiles"]["runtime"]))
        runtime_state.setdefault("channels", {})
        runtime_state.setdefault("reservations", {})
        runtime_state.setdefault("active_processes", {})
        return SandboxWorld(
            revision=source["revision"],
            entities=copy.deepcopy(source["entities"]),
            capabilities=copy.deepcopy(source["capabilities"]),
            leases=copy.deepcopy(source["leases"]),
            ledgers=copy.deepcopy(source["ledgers"]),
            history=copy.deepcopy(source["history"]),
            controllers=copy.deepcopy(source.get("controllers", {})),
            runtime_state=runtime_state,
            process_state=copy.deepcopy(source.get("process_state", {"process_id": "process:spell-instance", "status": "Idle", "prepared_plan_id": None})),
        )

    def run_admitted(self, admitted: AdmittedSpellInstance) -> dict[str, Any]:
        evaluated = self.evaluate_admitted(admitted)
        if evaluated["status"] != "Evaluated":
            return {"status": "FAIL", "evaluation": evaluated}
        bundle = admitted.bundle()
        expected = bundle["expected_outcome"]
        report = evaluated["report"]
        comparison: dict[str, Any] = {"evaluation_status": report["status"] == expected["evaluation_status"]}
        if report["status"] not in {"Feasible", "ConditionallyFeasible"}:
            observed_codes = [item["code"] for item in report.get("diagnostics", [])]
            comparison["diagnostic_codes"] = all(code in observed_codes for code in expected.get("diagnostic_codes", []))
            passed = all(comparison.values())
            return {"status": "PASS" if passed else "FAIL", "evaluation": evaluated, "comparison": comparison, "execution": None, "replay": None}

        world = self._world(bundle)
        initial = world.clone()
        limits = bundle["profiles"]["sandbox"]["limits"]
        profile = SandboxProfile(
            profile_id=bundle["profiles"]["sandbox"]["artifact_id"],
            revision=bundle["profiles"]["sandbox"]["revision"],
            max_energy_j=float(limits["max_energy_j"]),
            max_events_per_commit=int(limits["max_events_per_commit"]),
            max_microsteps_per_tick=int(limits["max_microsteps_per_tick"]),
            max_concurrency=int(limits["max_concurrency"]),
        )
        engine = ReferenceRuntimeEngine(sandbox_profile=profile, runtime=RegisteredSandboxRuntime(self.runtime_registry, runtime_profile=bundle["profiles"]["runtime"]))
        execution = engine.execute(report, world)
        comparison["runtime_status"] = execution["status"] == expected.get("runtime_status")
        observed_code = execution.get("abort", {}).get("code")
        comparison["diagnostic_codes"] = all(code == observed_code for code in expected.get("diagnostic_codes", []))
        comparison["final_invariants"] = _subset(expected.get("final_invariants", {}), world.configuration())
        if execution["status"] == "Committed":
            if "expected_event_ids" in expected:
                observed_events = execution.get("history_event_ids", [])
                comparison["expected_event_ids"] = all(event_id in observed_events for event_id in expected["expected_event_ids"])
            if "expected_result_hash" in expected:
                comparison["expected_result_hash"] = execution.get("result_state_hash") == expected["expected_result_hash"]
            replay = engine.replay(report, initial, execution)
            comparison["replay_status"] = replay["status"] == expected.get("replay_status")
        else:
            replay_world = initial.clone()
            replay_execution = engine.execute(report, replay_world)
            deterministic = replay_execution.get("abort", {}).get("code") == observed_code and replay_world.configuration() == world.configuration()
            replay = {"status": "DeterministicAbort" if deterministic else "Diverged", "trace": replay_execution}
            comparison["replay_status"] = replay["status"] == expected.get("replay_status")
        passed = all(comparison.values())
        return {"status": "PASS" if passed else "FAIL", "evaluation": evaluated, "execution": execution, "replay": replay, "final_world": world.configuration(), "comparison": comparison}

    def run_file(self, path: str | Path, *, input_kind: str | None = None) -> dict[str, Any]:
        try:
            admitted = self._admit_file(path, input_kind=input_kind)
        except (ArtifactIngressError, ArtifactRegistryError, SemanticHandlerError, RuntimeExecutorError, ExecutionContractError, SchemaValidationError, CompatibilityAdmissionError) as error:
            return {"status": "FAIL", "evaluation": {"status": "Rejected", "check": self._rejection(error)}}
        return self.run_admitted(admitted)


def default_service() -> SpellInstanceService:
    artifact = ArtifactLoaderRegistry()
    semantic = SemanticHandlerRegistry()
    runtime = RuntimeExecutorRegistry()
    execution = ExecutionContractRegistry()
    artifact.register(ArtifactLoaderRegistration("SpellInstanceBundle", "0", _spell_loader))
    register_default_extensions(semantic, runtime, execution)
    return SpellInstanceService(artifact, semantic, runtime, execution)
