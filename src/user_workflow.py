"""Unified experimental check/eval/run/compile workflow.

This module is an integration layer.  It preserves the stable v0.8 evaluator
entry point and routes only decoded public experimental inputs: MGLS-0 source,
SpellInstanceBundle-0, and MagicalProgram-0.  Filenames select at most one
decoder and are never semantic or runtime dispatch keys.
"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.artifacts.envelope import (
    DEFAULT_HOST_CEILINGS,
    ArtifactIngressError,
    HostCeilings,
    decode_artifact_bytes,
    read_artifact_snapshot,
)
from src.artifacts.magical_program import (
    MagicalProgramAdmissionError,
    admit_program,
)
from src.artifacts.spell_instance_program import (
    AdmittedSpellInstance,
    SpellInstanceService,
    default_service,
)
from src.evaluator.magical_program import MagicalProgramEvaluator
from src.evaluator.schema import validator
from src.mgls import MglsCompileError, compile_source
from src.runtime.magical_program import MagicalProgramRuntime, program_sandbox_world

_JSON = dict[str, Any]
WORKFLOW_CONTRACT = "magical-language-workflow"
WORKFLOW_REVISION = "0"

KIND_MGLS = "MGLS"
KIND_PROGRAM = "MagicalProgram"
KIND_BUNDLE = "SpellInstanceBundle"
KIND_STRUCTURED = "StructuredArtifact"
KIND_NSR = "NormalizedSemanticRepresentation"

_EXPLICIT_KINDS = {
    "mgls": KIND_MGLS,
    "source": KIND_MGLS,
    "magical-program": KIND_PROGRAM,
    "program": KIND_PROGRAM,
    "spell-instance-bundle": KIND_BUNDLE,
    "bundle": KIND_BUNDLE,
}

_SUCCESS_STATUSES = {"Accepted", "Evaluated", "Compiled", "Committed", "PASS"}


class WorkflowError(RuntimeError):
    """Owned deterministic user-workflow failure."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        stage: str = "INGRESS",
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.details = copy.deepcopy(dict(details or {}))

    def diagnostic(self) -> _JSON:
        result: _JSON = {
            "stage": self.stage,
            "code": self.code,
            "severity": "fatal",
            "message": str(self),
        }
        if self.details:
            result["details"] = copy.deepcopy(self.details)
        return result


@dataclass(frozen=True)
class InputSnapshot:
    """One immutable input read with advisory filename metadata."""

    payload: bytes
    sha256: str
    filename_hint: str | None
    path: Path

    @classmethod
    def read(
        cls,
        path: str | Path,
        *,
        ceilings: HostCeilings = DEFAULT_HOST_CEILINGS,
    ) -> "InputSnapshot":
        candidate = Path(path)
        payload = read_artifact_snapshot(candidate, ceilings=ceilings)
        return cls(
            payload=payload,
            sha256=hashlib.sha256(payload).hexdigest(),
            filename_hint=_filename_hint(candidate.name),
            path=candidate,
        )


@dataclass(frozen=True)
class InspectedInput:
    snapshot: InputSnapshot
    kind: str
    version: str | None
    document: _JSON | None = None


def _filename_hint(name: str) -> str | None:
    normalized = name.lower()
    if normalized.endswith(".mgls"):
        return KIND_MGLS
    if normalized.endswith(".program.mga.json"):
        return KIND_PROGRAM
    if normalized.endswith(".bundle.mga.json"):
        return KIND_BUNDLE
    if normalized.endswith(".nsr.mga.json"):
        return KIND_NSR
    if normalized.endswith(".mga.json") or normalized.endswith(".json"):
        return KIND_STRUCTURED
    return None


def _canonical_explicit_kind(value: str | None) -> str | None:
    if value is None or value == "auto":
        return None
    kind = _EXPLICIT_KINDS.get(value)
    if kind is None:
        raise WorkflowError(
            "UnsupportedInputKind",
            f"Unsupported explicit input kind {value!r}.",
        )
    return kind


def _validate_filename_hint(hint: str | None, decoded_kind: str) -> None:
    if hint in {KIND_PROGRAM, KIND_BUNDLE, KIND_NSR, KIND_MGLS} and hint != decoded_kind:
        raise WorkflowError(
            "InputKindHintMismatch",
            "Filename stage/source hint disagrees with decoded input kind.",
            details={"filename_hint": hint, "decoded_kind": decoded_kind},
        )


def inspect_input(
    snapshot: InputSnapshot,
    *,
    explicit_kind: str | None = None,
    ceilings: HostCeilings = DEFAULT_HOST_CEILINGS,
) -> InspectedInput:
    """Select exactly one decoder, then trust only the decoded header/envelope."""

    expected = _canonical_explicit_kind(explicit_kind)
    hint = snapshot.filename_hint

    if expected == KIND_MGLS:
        if hint not in {None, KIND_MGLS}:
            raise WorkflowError(
                "InputKindHintMismatch",
                "Explicit MGLS input disagrees with the structured filename hint.",
                details={"filename_hint": hint, "expected_kind": KIND_MGLS},
            )
        return InspectedInput(snapshot, KIND_MGLS, "0")

    if expected in {KIND_PROGRAM, KIND_BUNDLE}:
        if hint == KIND_MGLS:
            raise WorkflowError(
                "InputKindHintMismatch",
                "Explicit structured input disagrees with the .mgls source hint.",
                details={"filename_hint": hint, "expected_kind": expected},
            )
        document = decode_artifact_bytes(snapshot.payload, ceilings=ceilings)
        decoded = document.get("artifact_kind")
        if decoded != expected:
            raise WorkflowError(
                "ExpectedInputKindMismatch",
                "Explicit input kind disagrees with the decoded artifact_kind.",
                details={"expected_kind": expected, "decoded_kind": decoded},
            )
        _validate_filename_hint(hint, expected)
        return InspectedInput(
            snapshot,
            expected,
            str(document.get("artifact_version"))
            if document.get("artifact_version") is not None
            else None,
            document,
        )

    if hint == KIND_MGLS:
        return InspectedInput(snapshot, KIND_MGLS, "0")
    if hint is None:
        raise WorkflowError(
            "InputKindAmbiguous",
            "Automatic inspection requires .mgls or a recognized structured JSON suffix; use --input-kind for an unknown suffix.",
        )

    document = decode_artifact_bytes(snapshot.payload, ceilings=ceilings)
    decoded = document.get("artifact_kind")
    if not isinstance(decoded, str):
        raise WorkflowError(
            "ArtifactKindMissing",
            "Structured input has no authoritative artifact_kind.",
        )
    if decoded not in {KIND_PROGRAM, KIND_BUNDLE}:
        raise WorkflowError(
            "UnsupportedInputKind",
            f"Decoded artifact kind {decoded!r} is not admitted by the experimental workflow.",
            details={"decoded_kind": decoded},
        )
    _validate_filename_hint(hint, decoded)
    return InspectedInput(
        snapshot,
        decoded,
        str(document.get("artifact_version"))
        if document.get("artifact_version") is not None
        else None,
        document,
    )


def _canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _program_size(program: Mapping[str, Any]) -> int:
    return len(_canonical_json_bytes(program))


def _diagnostic_from_exception(error: Exception) -> _JSON:
    if isinstance(error, WorkflowError):
        return error.diagnostic()
    if isinstance(error, ArtifactIngressError):
        return error.as_diagnostic()
    if isinstance(error, MglsCompileError):
        return error.diagnostic()
    if isinstance(error, MagicalProgramAdmissionError):
        result: _JSON = {
            "stage": "PROGRAM_ADMISSION",
            "code": error.code,
            "severity": "fatal",
            "message": str(error),
        }
        if error.path:
            result["details"] = {"path": error.path}
        return result
    return {
        "stage": "INTERNAL",
        "code": "InternalFailure",
        "severity": "fatal",
        "message": "The experimental workflow failed closed.",
    }


def _abort_diagnostic(abort: Mapping[str, Any]) -> _JSON | None:
    code = abort.get("code")
    if not isinstance(code, str):
        return None
    return {
        "stage": str(abort.get("stage", "COMMIT")),
        "code": code,
        "severity": "fatal",
        "message": str(abort.get("message", "Execution aborted.")),
    }


def _collect_diagnostics(value: Any) -> list[_JSON]:
    collected: list[_JSON] = []

    def visit(item: Any) -> None:
        if isinstance(item, Mapping):
            diagnostics = item.get("diagnostics")
            if isinstance(diagnostics, Sequence) and not isinstance(
                diagnostics, (str, bytes)
            ):
                for diagnostic in diagnostics:
                    if isinstance(diagnostic, Mapping) and isinstance(
                        diagnostic.get("code"), str
                    ):
                        collected.append(copy.deepcopy(dict(diagnostic)))
            abort = item.get("abort")
            if isinstance(abort, Mapping):
                diagnostic = _abort_diagnostic(abort)
                if diagnostic is not None:
                    collected.append(diagnostic)
            for key, child in item.items():
                if key not in {"diagnostics", "abort"}:
                    visit(child)
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes)):
            for child in item:
                visit(child)

    visit(value)
    result: list[_JSON] = []
    seen: set[bytes] = set()
    for diagnostic in collected:
        marker = _canonical_json_bytes(diagnostic)
        if marker not in seen:
            seen.add(marker)
            result.append(diagnostic)
    return result


def _input_payload(inspected: InspectedInput) -> _JSON:
    return {
        "kind": inspected.kind,
        "version": inspected.version,
        "sha256": inspected.snapshot.sha256,
        "filename_hint": inspected.snapshot.filename_hint,
    }


def _envelope(
    command: str,
    *,
    status: str,
    result: Any,
    diagnostics: Sequence[Mapping[str, Any]],
    inspected: InspectedInput | None = None,
    snapshot: InputSnapshot | None = None,
    expected_kind: str | None = None,
) -> _JSON:
    if inspected is not None:
        input_payload: _JSON = _input_payload(inspected)
    elif snapshot is not None:
        input_payload = {
            "kind": expected_kind,
            "version": None,
            "sha256": snapshot.sha256,
            "filename_hint": snapshot.filename_hint,
        }
    else:
        input_payload = {
            "kind": expected_kind,
            "version": None,
            "sha256": None,
            "filename_hint": None,
        }
    return {
        "workflow": {
            "contract_id": WORKFLOW_CONTRACT,
            "revision": WORKFLOW_REVISION,
            "stability": "experimental",
        },
        "command": command,
        "status": status,
        "input": input_payload,
        "result": copy.deepcopy(result),
        "diagnostics": [copy.deepcopy(dict(item)) for item in diagnostics],
    }


class UserWorkflow:
    """One public experimental workflow over the existing owned services."""

    def __init__(
        self,
        *,
        bundle_service: SpellInstanceService | None = None,
        evaluator: MagicalProgramEvaluator | None = None,
        host_ceilings: HostCeilings = DEFAULT_HOST_CEILINGS,
    ) -> None:
        self.bundle_service = bundle_service or default_service()
        self.evaluator = evaluator or MagicalProgramEvaluator()
        self.host_ceilings = host_ceilings
        self._program_schema = validator("magical-program.schema.json").schema

    def _admit_bundle(
        self, document: Mapping[str, Any]
    ) -> tuple[AdmittedSpellInstance | None, _JSON | None]:
        service = self.bundle_service
        try:
            bundle = service.artifact_registry.load(copy.deepcopy(dict(document)))
            checked = service._check_bundle(bundle)
            admitted = AdmittedSpellInstance.create(bundle, checked)
            checked["source_digest"] = admitted.source_digest
            return (
                AdmittedSpellInstance(
                    admitted.canonical_document,
                    admitted.source_digest,
                    checked,
                ),
                None,
            )
        except Exception as error:
            rejection = service._rejection(error)
            diagnostics = rejection.get("diagnostics", [])
            if not diagnostics or diagnostics[0].get("code") == "ArtifactRejected":
                rejection = {
                    "status": "Rejected",
                    "diagnostics": [
                        {
                            "stage": "INGRESS",
                            "code": "ArtifactRejected",
                            "severity": "fatal",
                            "message": "SpellInstanceBundle admission failed closed.",
                        }
                    ],
                }
            return None, rejection

    def _check_program(
        self,
        program: Mapping[str, Any],
        *,
        encoded_size: int,
    ) -> _JSON:
        admission = admit_program(
            program,
            schema=self._program_schema,
            registered_contracts=self.evaluator.contracts.admitted_pairs(),
            encoded_size=encoded_size,
            limits=self.evaluator.limits,
        )
        expected = {
            "registry_id": self.evaluator.registry_id,
            "registry_revision": self.evaluator.registry_revision,
            "profile_id": self.evaluator.profile_id,
            "profile_revision": self.evaluator.profile_revision,
        }
        if program.get("compatibility") != expected:
            raise WorkflowError(
                "ProgramCompatibilityMismatch",
                "Program registry/profile binding does not match the reference evaluator.",
                stage="PROGRAM_ADMISSION",
            )
        return admission

    def _evaluate_program(
        self,
        program: Mapping[str, Any],
        *,
        encoded_size: int,
    ) -> _JSON:
        self._check_program(program, encoded_size=encoded_size)
        return self.evaluator.evaluate_program(
            program,
            encoded_size=encoded_size,
        )

    def _run_program(
        self,
        program: Mapping[str, Any],
        *,
        encoded_size: int,
    ) -> _JSON:
        report = self._evaluate_program(program, encoded_size=encoded_size)
        runtime = MagicalProgramRuntime(evaluator=self.evaluator)
        world = program_sandbox_world()
        initial = world.clone()
        execution = runtime.execute(program, world)
        replay = runtime.replay(program, initial, execution)
        return {
            "check": self._check_program(program, encoded_size=encoded_size),
            "evaluation": report,
            "execution": execution,
            "replay": replay,
            "final_world": world.configuration(),
        }

    def _compile_source(self, payload: bytes) -> _JSON:
        return compile_source(payload)

    def execute_snapshot(
        self,
        command: str,
        snapshot: InputSnapshot,
        *,
        input_kind: str | None = None,
    ) -> _JSON:
        expected = None
        try:
            expected = _canonical_explicit_kind(input_kind)
            inspected = inspect_input(
                snapshot,
                explicit_kind=input_kind,
                ceilings=self.host_ceilings,
            )
            if command == "compile":
                if inspected.kind != KIND_MGLS:
                    raise WorkflowError(
                        "CommandInputKindMismatch",
                        "compile admits only MGLS source input.",
                        stage="ROUTING",
                    )
                compilation = self._compile_source(snapshot.payload)
                return _envelope(
                    command,
                    status="Compiled",
                    result=compilation,
                    diagnostics=(),
                    inspected=inspected,
                )

            if inspected.kind == KIND_MGLS:
                compilation = self._compile_source(snapshot.payload)
                program = compilation["program"]
                size = _program_size(program)
                if command == "check":
                    result = {
                        "source_contract": compilation["source_contract"],
                        "program_id": program["program_id"],
                        "target_admission": compilation["target_admission"],
                        "source_map": compilation["source_map"],
                    }
                    return _envelope(
                        command,
                        status="Accepted",
                        result=result,
                        diagnostics=(),
                        inspected=inspected,
                    )
                if command == "eval":
                    report = self._evaluate_program(program, encoded_size=size)
                    result = {"compilation": compilation, "evaluation": report}
                    return _envelope(
                        command,
                        status="Evaluated",
                        result=result,
                        diagnostics=_collect_diagnostics(report),
                        inspected=inspected,
                    )
                if command == "run":
                    run = self._run_program(program, encoded_size=size)
                    status = str(run["execution"].get("status", "Aborted"))
                    return _envelope(
                        command,
                        status=status,
                        result={"compilation": compilation, **run},
                        diagnostics=_collect_diagnostics(run),
                        inspected=inspected,
                    )

            if inspected.kind == KIND_PROGRAM:
                assert inspected.document is not None
                program = inspected.document
                size = len(snapshot.payload)
                if command == "check":
                    result = self._check_program(program, encoded_size=size)
                    return _envelope(
                        command,
                        status="Accepted",
                        result=result,
                        diagnostics=(),
                        inspected=inspected,
                    )
                if command == "eval":
                    report = self._evaluate_program(program, encoded_size=size)
                    return _envelope(
                        command,
                        status="Evaluated",
                        result=report,
                        diagnostics=_collect_diagnostics(report),
                        inspected=inspected,
                    )
                if command == "run":
                    run = self._run_program(program, encoded_size=size)
                    status = str(run["execution"].get("status", "Aborted"))
                    return _envelope(
                        command,
                        status=status,
                        result=run,
                        diagnostics=_collect_diagnostics(run),
                        inspected=inspected,
                    )

            if inspected.kind == KIND_BUNDLE:
                assert inspected.document is not None
                admitted, rejection = self._admit_bundle(inspected.document)
                if rejection is not None:
                    return _envelope(
                        command,
                        status="Rejected",
                        result=rejection,
                        diagnostics=_collect_diagnostics(rejection),
                        inspected=inspected,
                    )
                assert admitted is not None
                if command == "check":
                    result = copy.deepcopy(admitted.check_result)
                    return _envelope(
                        command,
                        status="Accepted",
                        result=result,
                        diagnostics=(),
                        inspected=inspected,
                    )
                if command == "eval":
                    result = self.bundle_service.evaluate_admitted(admitted)
                    status = (
                        "Evaluated"
                        if result.get("status") == "Evaluated"
                        else "Rejected"
                    )
                    return _envelope(
                        command,
                        status=status,
                        result=result,
                        diagnostics=_collect_diagnostics(result),
                        inspected=inspected,
                    )
                if command == "run":
                    result = self.bundle_service.run_admitted(admitted)
                    status = str(result.get("status", "FAIL"))
                    return _envelope(
                        command,
                        status=status,
                        result=result,
                        diagnostics=_collect_diagnostics(result),
                        inspected=inspected,
                    )

            raise WorkflowError(
                "UnsupportedCommand",
                f"Unsupported workflow command {command!r}.",
                stage="ROUTING",
            )
        except (
            WorkflowError,
            ArtifactIngressError,
            MglsCompileError,
            MagicalProgramAdmissionError,
        ) as error:
            return _envelope(
                command,
                status="Rejected",
                result=None,
                diagnostics=[_diagnostic_from_exception(error)],
                snapshot=snapshot,
                expected_kind=expected,
            )
        except Exception as error:
            return _envelope(
                command,
                status="Rejected",
                result=None,
                diagnostics=[_diagnostic_from_exception(error)],
                snapshot=snapshot,
                expected_kind=expected,
            )

    def execute_path(
        self,
        command: str,
        path: str | Path,
        *,
        input_kind: str | None = None,
    ) -> _JSON:
        try:
            snapshot = InputSnapshot.read(path, ceilings=self.host_ceilings)
        except Exception as error:
            return _envelope(
                command,
                status="Rejected",
                result=None,
                diagnostics=[_diagnostic_from_exception(error)],
                expected_kind=_EXPLICIT_KINDS.get(input_kind or ""),
            )
        return self.execute_snapshot(
            command,
            snapshot,
            input_kind=input_kind,
        )



def workflow_exit_code(result: Mapping[str, Any]) -> int:
    status = result.get("status")
    if status in _SUCCESS_STATUSES:
        return 0
    if status == "Rejected":
        diagnostics = result.get("diagnostics", [])
        if diagnostics and diagnostics[0].get("code") == "InternalFailure":
            return 4
        return 2
    return 3


__all__ = [
    "InputSnapshot",
    "InspectedInput",
    "UserWorkflow",
    "WorkflowError",
    "inspect_input",
    "workflow_exit_code",
]
