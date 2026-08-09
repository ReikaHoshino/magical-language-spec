#!/usr/bin/env python3
"""Exercise installed spell entry points without importing checkout resources."""
from __future__ import annotations

import copy
import json
import subprocess
import tempfile
from pathlib import Path
from shutil import which

from src.resources import reference_root, resource_path


def _entry_point(name: str) -> Path:
    resolved = which(name)
    if resolved is None:
        raise RuntimeError(f"installed entry point is absent from PATH: {name}")
    path = Path(resolved).resolve()
    if not path.is_file():
        raise RuntimeError(f"installed entry point is not a file: {path}")
    return path


def _invoke(entry: Path, *arguments: str) -> tuple[int, dict, str]:
    completed = subprocess.run(
        [str(entry), *arguments],
        cwd=Path(tempfile.gettempdir()),
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{entry.name} returned non-JSON output: {completed.stdout!r}") from exc
    if "Traceback" in completed.stderr:
        raise RuntimeError(f"{entry.name} leaked a traceback")
    return completed.returncode, payload, completed.stderr


def _assert_failure(entry: Path, path: Path, expected_code: str) -> None:
    first = _invoke(entry, "check", str(path))
    second = _invoke(entry, "check", str(path))
    if first != second:
        raise RuntimeError(f"non-deterministic failure for {path.name}")
    if first[0] == 0 or first[1].get("diagnostics", [{}])[0].get("code") != expected_code:
        raise RuntimeError(f"unexpected {path.name} result: {first[1]}")


def main() -> int:
    root = reference_root().resolve()
    if "magical_language_spec_resources" not in root.parts:
        raise RuntimeError(f"smoke did not select installed package resources: {root}")

    artifact = _entry_point("magical-language-artifact")
    conformance = _entry_point("magical-language-conformance")
    arcana = _entry_point("magical-language-experimental-arcana")
    bundles = _entry_point("magical-language-spell-instances")

    for entry, arguments in (
        (conformance, ("--class", "Core-1.0")),
        (conformance, ("--class", "Runtime-1.0")),
    ):
        completed = subprocess.run([str(entry), *arguments], cwd=Path(tempfile.gettempdir()), text=True, capture_output=True, check=False)
        if completed.returncode or "Traceback" in completed.stderr:
            raise RuntimeError(f"installed {entry.name} failed: {completed.stderr}")
    for entry in (arcana, bundles):
        code, payload, _ = _invoke(entry)
        if code or payload.get("status") != "PASS":
            raise RuntimeError(f"installed {entry.name} failed: {payload}")

    fixture_paths = (
        "examples/spell-instances/success-arcana/SA-001.json",
        "examples/spell-instances/success-arcana/SA-004.json",
        "examples/spell-instances/debug-hell/DEBUG-HELL-001.json",
        "examples/spell-instances/debug-hell/DEBUG-HELL-002.json",
        "examples/spell-instances/debug-hell/DEBUG-HELL-003.json",
        "examples/spell-instances/generic/GENERIC-001.json",
    )
    with tempfile.TemporaryDirectory() as directory:
        scratch = Path(directory)
        for relative in fixture_paths:
            source = resource_path(relative)
            target = scratch / source.name
            target.write_bytes(source.read_bytes())
            code, payload, _ = _invoke(artifact, "run", str(target))
            if code or payload.get("status") != "PASS":
                raise RuntimeError(f"installed artifact execution failed for {source.name}: {payload}")

        generic_source = resource_path("examples/spell-instances/generic/GENERIC-001.json")
        generic = json.loads(generic_source.read_text(encoding="utf-8"))
        renamed = scratch / "renamed-arbitrary.json"
        renamed.write_text(json.dumps(generic), encoding="utf-8")
        if _invoke(artifact, "run", str(renamed))[1].get("status") != "PASS":
            raise RuntimeError("renamed installed bundle did not execute")

        renamed_instance = copy.deepcopy(generic)
        renamed_instance["instance_id"] = "ARBITRARY-INDEPENDENT-ID"
        renamed_instance_path = scratch / "renamed-instance.json"
        renamed_instance_path.write_text(json.dumps(renamed_instance), encoding="utf-8")
        if _invoke(artifact, "run", str(renamed_instance_path))[1].get("status") != "PASS":
            raise RuntimeError("renamed installed instance identity selected behavior")

        unknown = copy.deepcopy(generic)
        unknown["semantic_contract"] = {"contract_id": "unknown.contract", "revision": "1"}
        unknown_path = scratch / "unknown.json"
        unknown_path.write_text(json.dumps(unknown), encoding="utf-8")
        _assert_failure(artifact, unknown_path, "UnknownSemanticContract")

        invalid_pair = copy.deepcopy(generic)
        invalid_pair["runtime_contract"] = {"contract_id": "runtime.staged-treatment", "revision": "1"}
        pair_path = scratch / "invalid-pair.json"
        pair_path.write_text(json.dumps(invalid_pair), encoding="utf-8")
        _assert_failure(artifact, pair_path, "ExecutionContractPairNotAdmitted")

        overflow = scratch / "overflow.json"
        overflow.write_text(generic_source.read_text(encoding="utf-8").replace('"energy_j": 25', '"energy_j": 1e999'), encoding="utf-8")
        _assert_failure(artifact, overflow, "InvalidJSONNumber")

        malformed = scratch / "malformed.json"
        malformed.write_bytes(b'{"artifact_kind":')
        _assert_failure(artifact, malformed, "MalformedJSON")

    print(json.dumps({"status": "PASS", "package_root": str(root), "fixtures": 6, "negative_cases": 4}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
