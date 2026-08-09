"""Independent experimental golden/parity harness for Issue #86.

Expected truth is loaded from a separate golden manifest.  The executable
SpellInstanceBundle's ``expected_outcome`` member is deliberately never read by
this module.
"""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from src.runtime.engine import ReferenceRuntimeEngine, SandboxProfile

from .spell_instance import RegisteredSandboxRuntime, SpellInstanceService

_JSON = dict[str, Any]
_MISSING = object()
_NO_DEFAULT = object()


class GoldenParityError(RuntimeError):
    """Fail-closed manifest, mutation, or comparison error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class FrozenArtifact:
    """One immutable byte snapshot shared by every compared execution path."""

    payload: bytes
    sha256: str

    @classmethod
    def from_path(cls, path: str | Path) -> "FrozenArtifact":
        source = Path(path)
        if source.is_symlink():
            raise GoldenParityError("GoldenInputSymlinkRejected", "Golden input must not be a symbolic link.")
        payload = source.read_bytes()
        return cls(payload=payload, sha256=hashlib.sha256(payload).hexdigest())


def _decode_pointer_token(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def _pointer_tokens(pointer: str) -> list[str]:
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise GoldenParityError("InvalidGoldenPointer", f"JSON pointer must start with '/': {pointer!r}")
    return [_decode_pointer_token(token) for token in pointer[1:].split("/")]


def pointer_get(document: Any, pointer: str, *, default: Any = _NO_DEFAULT) -> Any:
    current = document
    try:
        for token in _pointer_tokens(pointer):
            if isinstance(current, list):
                current = current[int(token)]
            elif isinstance(current, dict):
                current = current[token]
            else:
                raise KeyError(token)
    except (KeyError, IndexError, ValueError, TypeError):
        if default is _NO_DEFAULT:
            raise GoldenParityError("GoldenPathMissing", f"Observed document has no value at {pointer!r}.")
        return default
    return current


def pointer_set(document: Any, pointer: str, value: Any) -> None:
    tokens = _pointer_tokens(pointer)
    if not tokens:
        raise GoldenParityError("GoldenRootMutationForbidden", "A variant may not replace the artifact root.")
    current = document
    try:
        for token in tokens[:-1]:
            current = current[int(token)] if isinstance(current, list) else current[token]
        final = tokens[-1]
        if isinstance(current, list):
            current[int(final)] = copy.deepcopy(value)
        else:
            current[final] = copy.deepcopy(value)
    except (KeyError, IndexError, ValueError, TypeError) as error:
        raise GoldenParityError("GoldenMutationPathMissing", f"Mutation path does not exist: {pointer!r}.") from error


def _subset(expected: Any, observed: Any) -> bool:
    if isinstance(expected, dict):
        return isinstance(observed, dict) and all(
            key in observed and _subset(value, observed[key]) for key, value in expected.items()
        )
    if isinstance(expected, list):
        return expected == observed
    return expected == observed


def _matches(mode: str, expected: Any, observed: Any, *, observed_exists: bool) -> bool:
    if mode == "absent":
        return not observed_exists
    if not observed_exists:
        return False
    if mode == "exact":
        return expected == observed
    if mode == "subset":
        return _subset(expected, observed)
    if mode == "contains":
        return isinstance(expected, list) and isinstance(observed, list) and all(item in observed for item in expected)
    raise GoldenParityError("UnknownGoldenComparisonMode", f"Unknown comparison mode: {mode!r}.")


def compare_checks(observed: Any, checks: Sequence[Mapping[str, Any]], *, expectation_id: str) -> _JSON:
    differences: list[_JSON] = []
    for ordinal, check in enumerate(checks):
        pointer = str(check["path"])
        mode = str(check["mode"])
        value = pointer_get(observed, pointer, default=_MISSING)
        exists = value is not _MISSING
        expected = check.get("expected", _MISSING)
        if mode != "absent" and expected is _MISSING:
            raise GoldenParityError("GoldenExpectedValueMissing", f"Check {ordinal} has no expected value.")
        if not _matches(mode, expected, value, observed_exists=exists):
            differences.append(
                {
                    "code": "GoldenSemanticMismatch",
                    "ordinal": ordinal,
                    "path": pointer,
                    "mode": mode,
                    "owner": check.get("owner"),
                    "expected": None if expected is _MISSING else copy.deepcopy(expected),
                    "observed_exists": exists,
                    "observed": None if value is _MISSING else copy.deepcopy(value),
                }
            )
    return {
        "expectation_id": expectation_id,
        "status": "PASS" if not differences else "FAIL",
        "differences": differences,
    }


def _runtime_profile(bundle: _JSON) -> SandboxProfile:
    limits = bundle["profiles"]["sandbox"]["limits"]
    return SandboxProfile(
        profile_id=bundle["profiles"]["sandbox"]["artifact_id"],
        revision=bundle["profiles"]["sandbox"]["revision"],
        max_energy_j=float(limits["max_energy_j"]),
        max_events_per_commit=int(limits["max_events_per_commit"]),
        max_microsteps_per_tick=int(limits["max_microsteps_per_tick"]),
        max_concurrency=int(limits["max_concurrency"]),
    )


def _materialize_variant(frozen: FrozenArtifact, mutations: Iterable[Mapping[str, Any]]) -> bytes:
    try:
        document = json.loads(frozen.payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GoldenParityError("GoldenInputDecodeFailure", "Frozen golden input is not valid UTF-8 JSON.") from error
    for mutation in mutations:
        pointer_set(document, str(mutation["pointer"]), mutation.get("value"))
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def observe_frozen(
    service: SpellInstanceService,
    frozen: FrozenArtifact,
    *,
    mutations: Iterable[Mapping[str, Any]] = (),
) -> _JSON:
    """Execute one immutable input snapshot without consulting embedded expectations."""

    payload = _materialize_variant(frozen, mutations)
    variant_digest = hashlib.sha256(payload).hexdigest()
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "frozen-input.mga.json"
        path.write_bytes(payload)
        admitted = service._admit_file(path)
        evaluated = service.evaluate_admitted(admitted)

    observation: _JSON = {
        "frozen_input": {"sha256": frozen.sha256, "variant_sha256": variant_digest},
        "check": copy.deepcopy(admitted.check_result),
        "evaluation": copy.deepcopy(evaluated),
        "execution": None,
        "replay": None,
        "final_world": None,
    }
    if evaluated["status"] != "Evaluated":
        return observation

    report = evaluated["report"]
    if report["status"] not in {"Feasible", "ConditionallyFeasible"}:
        return observation

    bundle = admitted.bundle()
    world = SpellInstanceService._world(bundle)
    initial = world.clone()
    runtime = RegisteredSandboxRuntime(service.runtime_registry, runtime_profile=bundle["profiles"]["runtime"])
    engine = ReferenceRuntimeEngine(sandbox_profile=_runtime_profile(bundle), runtime=runtime)
    execution = engine.execute(report, world)
    if execution["status"] == "Committed":
        replay = engine.replay(report, initial, execution)
    else:
        replay_world = initial.clone()
        replay_execution = engine.execute(report, replay_world)
        observed_code = execution.get("abort", {}).get("code")
        deterministic = (
            replay_execution.get("abort", {}).get("code") == observed_code
            and replay_world.configuration() == world.configuration()
        )
        replay = {
            "status": "DeterministicAbort" if deterministic else "Diverged",
            "trace": replay_execution,
        }
    observation.update(
        {
            "execution": copy.deepcopy(execution),
            "replay": copy.deepcopy(replay),
            "final_world": world.configuration(),
        }
    )
    return observation


def _resolve_input(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    resolved_root = root.resolve()
    if candidate != resolved_root and resolved_root not in candidate.parents:
        raise GoldenParityError("GoldenInputTraversalRejected", f"Input escapes repository root: {relative!r}.")
    return candidate


def _combined_checks(manifest: Mapping[str, Any], item: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    checks: list[Mapping[str, Any]] = []
    template = item.get("template")
    if template is not None:
        templates = manifest.get("templates", {})
        if template not in templates:
            raise GoldenParityError("UnknownGoldenTemplate", f"Unknown golden check template: {template!r}.")
        checks.extend(templates[template])
    checks.extend(item.get("checks", []))
    return checks


def run_manifest(
    root: str | Path,
    manifest_path: str | Path,
    *,
    service: SpellInstanceService | None = None,
) -> _JSON:
    """Run positive and variant expectations from one external manifest."""

    from . import default_service

    repository_root = Path(root)
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    active_service = default_service() if service is None else service
    seen: set[str] = set()
    results: list[_JSON] = []
    for case in manifest["cases"]:
        expectation_id = str(case["expectation_id"])
        if expectation_id in seen:
            raise GoldenParityError("DuplicateGoldenExpectation", f"Duplicate expectation ID: {expectation_id!r}.")
        seen.add(expectation_id)
        frozen = FrozenArtifact.from_path(_resolve_input(repository_root, str(case["input"])))
        observed = observe_frozen(active_service, frozen)
        comparison = compare_checks(observed, _combined_checks(manifest, case), expectation_id=expectation_id)
        comparison.update({"input": case["input"], "frozen_sha256": frozen.sha256, "variant_id": None})
        results.append(comparison)
        for variant in case.get("variants", []):
            variant_id = str(variant["variant_id"])
            variant_expectation_id = f"{expectation_id}::{variant_id}"
            if variant_expectation_id in seen:
                raise GoldenParityError("DuplicateGoldenExpectation", f"Duplicate expectation ID: {variant_expectation_id!r}.")
            seen.add(variant_expectation_id)
            variant_observed = observe_frozen(active_service, frozen, mutations=variant["mutations"])
            variant_comparison = compare_checks(
                variant_observed,
                _combined_checks(manifest, variant),
                expectation_id=variant_expectation_id,
            )
            variant_comparison.update(
                {"input": case["input"], "frozen_sha256": frozen.sha256, "variant_id": variant_id}
            )
            results.append(variant_comparison)
    failures = [item for item in results if item["status"] != "PASS"]
    return {
        "suite_id": manifest["suite_id"],
        "manifest_version": manifest["manifest_version"],
        "status": "PASS" if not failures else "FAIL",
        "case_count": len(results),
        "failure_count": len(failures),
        "results": results,
    }


ObservationRunner = Callable[[FrozenArtifact], _JSON]


def differential_compare(
    frozen: FrozenArtifact,
    old_runner: ObservationRunner,
    new_runner: ObservationRunner,
    checks: Sequence[Mapping[str, Any]],
    *,
    comparison_id: str,
) -> _JSON:
    """Compare old/new paths from the same frozen bytes without mutating either result."""

    old_observed = copy.deepcopy(old_runner(frozen))
    new_observed = copy.deepcopy(new_runner(frozen))
    expected_checks: list[_JSON] = []
    for check in checks:
        pointer = str(check["path"])
        mode = str(check.get("mode", "exact"))
        old_value = pointer_get(old_observed, pointer, default=_MISSING)
        if old_value is _MISSING:
            expected_checks.append({"path": pointer, "mode": "absent", "owner": check.get("owner")})
        else:
            expected_checks.append(
                {"path": pointer, "mode": mode, "expected": copy.deepcopy(old_value), "owner": check.get("owner")}
            )
    result = compare_checks(new_observed, expected_checks, expectation_id=comparison_id)
    result.update(
        {
            "frozen_sha256": frozen.sha256,
            "old_observation": old_observed,
            "new_observation": new_observed,
        }
    )
    return result
