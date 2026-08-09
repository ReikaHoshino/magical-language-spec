from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from src.artifacts import default_service
from src.artifacts.cli import main as artifact_cli_main
from src.artifacts.envelope import DEFAULT_HOST_CEILINGS

ROOT = Path(__file__).resolve().parents[1]
GENERIC = ROOT / "examples" / "spell-instances" / "generic" / "GENERIC-001.json"


class SpellInstanceSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = default_service()
        self.source = json.loads(GENERIC.read_text(encoding="utf-8"))

    def _check(self, document: dict, directory: str, name: str = "case.json") -> dict:
        path = Path(directory) / name
        path.write_text(json.dumps(document), encoding="utf-8")
        return self.service.check_file(path)

    @staticmethod
    def _with_broken_generic_executor(exception_type: type[Exception]):
        service = default_service()
        registration = service.program_translators.resolve(
            json.loads(GENERIC.read_text(encoding="utf-8"))
        )
        original = registration.translator

        def broken_translator(bundle):
            translated = original(bundle)
            assert translated.runtime is not None
            key = ("example.generic-transition", "1")
            runtime_registration = translated.runtime.contracts.resolve(*key)

            def broken(context, effect, world):
                del context, effect, world
                raise exception_type("private implementation detail")

            translated.runtime.contracts._items[key] = replace(
                runtime_registration,
                executor=broken,
            )
            return translated

        service.program_translators.replace(
            replace(registration, translator=broken_translator)
        )
        return service

    def test_semantic_runtime_pair_is_admitted_as_one_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for name, mutation in (
                (
                    "wrong-runtime",
                    {
                        "runtime_contract": {
                            "contract_id": "runtime.staged-treatment",
                            "revision": "1",
                        }
                    },
                ),
                (
                    "wrong-semantic",
                    {
                        "semantic_contract": {
                            "contract_id": "controller.boundary-reflection",
                            "revision": "1",
                        }
                    },
                ),
            ):
                document = copy.deepcopy(self.source)
                document.update(mutation)
                result = self._check(document, directory, f"{name}.json")
                with self.subTest(name=name):
                    self.assertEqual("Rejected", result["status"])
                    self.assertEqual(
                        "ExecutionContractPairNotAdmitted",
                        result["diagnostics"][0]["code"],
                    )

    def test_parameter_schema_and_reference_fail_before_prepare(self) -> None:
        cases = (
            (
                "missing",
                lambda value: value["execution"]["parameters"].pop(
                    "source_entity_id"
                ),
                "ExecutionParameterMissing",
            ),
            (
                "wrong-type",
                lambda value: value["execution"]["parameters"].update(
                    {"energy_j": "25"}
                ),
                "ExecutionParameterTypeMismatch",
            ),
            (
                "unknown",
                lambda value: value["execution"]["parameters"].update(
                    {"surprise": True}
                ),
                "ExecutionParameterUnknown",
            ),
            (
                "invalid-reference",
                lambda value: value["execution"]["parameters"].update(
                    {"target_entity_id": "entity:absent"}
                ),
                "ExecutionParameterReferenceInvalid",
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            for name, mutate, code in cases:
                document = copy.deepcopy(self.source)
                mutate(document)
                result = self._check(document, directory, f"{name}.json")
                with self.subTest(name=name):
                    self.assertEqual("Rejected", result["status"])
                    self.assertEqual(code, result["diagnostics"][0]["code"])

    def test_run_decodes_path_once_and_uses_immutable_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "replaceable.json"
            path.write_text(json.dumps(self.source), encoding="utf-8")
            original_load = self.service._load
            calls = 0

            def replacing_load(candidate, *, input_kind=None):
                nonlocal calls
                calls += 1
                admitted = original_load(candidate, input_kind=input_kind)
                replacement = copy.deepcopy(self.source)
                replacement["semantic_contract"] = {
                    "contract_id": "unknown.after-check",
                    "revision": "1",
                }
                path.write_text(json.dumps(replacement), encoding="utf-8")
                return admitted

            self.service._load = replacing_load  # type: ignore[method-assign]
            result = self.service.run_file(path)
        self.assertEqual(1, calls)
        self.assertEqual("PASS", result["status"])
        self.assertEqual(
            "example.generic-transition",
            result["evaluation"]["check"]["semantic_contract"]["contract_id"],
        )

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink unavailable")
    def test_actual_cli_rejects_symlink_input_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            link = Path(directory) / "linked.json"
            try:
                link.symlink_to(GENERIC)
            except OSError:
                self.skipTest("symlink creation not permitted")
            completed = subprocess.run(
                [sys.executable, "-m", "src.artifacts.cli", "check", str(link)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        payload = json.loads(completed.stdout)
        self.assertNotEqual(0, completed.returncode)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertEqual(
            "InputSymlinkRejected", payload["diagnostics"][0]["code"]
        )

    def test_program_executor_errors_abort_atomically_without_private_leak(self) -> None:
        for exception_type in (KeyError, ValueError):
            service = self._with_broken_generic_executor(exception_type)
            result = service.run_file(GENERIC)
            with self.subTest(exception=exception_type.__name__):
                self.assertEqual("FAIL", result["status"])
                self.assertEqual(
                    "ExtensionExecutionFailure",
                    result["execution"]["abort"]["code"],
                )
                self.assertNotIn("internal_cause", result["execution"]["abort"])
                self.assertNotIn(
                    "private implementation detail",
                    json.dumps(result, sort_keys=True),
                )
                self.assertTrue(result["execution"]["world_revision_unchanged"])
                self.assertTrue(result["execution"]["history_unchanged"])

    def test_cli_wraps_program_errors_without_traceback(self) -> None:
        for exception_type in (KeyError, ValueError):
            service = self._with_broken_generic_executor(exception_type)
            stdout = StringIO()
            stderr = StringIO()
            with (
                patch("src.artifacts.cli.default_service", return_value=service),
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                code = artifact_cli_main(["run", str(GENERIC)])
            payload = json.loads(stdout.getvalue())
            with self.subTest(exception=exception_type.__name__):
                self.assertNotEqual(0, code)
                self.assertNotIn("Traceback", stderr.getvalue())
                self.assertEqual(
                    "ExtensionExecutionFailure",
                    payload["execution"]["abort"]["code"],
                )
                self.assertNotIn("internal_cause", payload["execution"]["abort"])

    def test_nonfinite_and_extreme_numbers_fail_closed(self) -> None:
        source_text = GENERIC.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as directory:
            for name, payload, code in (
                (
                    "overflow.json",
                    source_text.replace('"energy_j": 25', '"energy_j": 1e999'),
                    "InvalidJSONNumber",
                ),
                (
                    "nan.json",
                    source_text.replace('"energy_j": 25', '"energy_j": NaN'),
                    "InvalidJSONNumber",
                ),
                (
                    "huge.json",
                    source_text.replace(
                        '"energy_j": 25',
                        '"energy_j": 999999999999999999999999999999',
                    ),
                    "JSONNumberMagnitudeExceeded",
                ),
            ):
                path = Path(directory) / name
                path.write_text(payload, encoding="utf-8")
                result = self.service.check_file(path)
                self.assertEqual(code, result["diagnostics"][0]["code"])

    def test_every_host_ceiling_is_independent_of_artifact_claims(self) -> None:
        cases = (
            ("max_parameter_bytes", 1, lambda value: None, "HostParameterLimitExceeded"),
            ("max_entities", 1, lambda value: None, "HostEntityLimitExceeded"),
            (
                "max_history_records",
                0,
                lambda value: value["initial_world"]["history"].append(
                    {"event_id": "event:old"}
                ),
                "HostHistoryLimitExceeded",
            ),
            ("max_energy_j", 24, lambda value: None, "HostEnergyLimitExceeded"),
            ("max_events_per_commit", 15, lambda value: None, "HostSandboxLimitExceeded"),
            ("max_microsteps_per_tick", 31, lambda value: None, "HostSandboxLimitExceeded"),
            ("max_concurrency", 0, lambda value: None, "HostSandboxLimitExceeded"),
        )
        with tempfile.TemporaryDirectory() as directory:
            for field, maximum, mutate, code in cases:
                service = default_service()
                service.host_ceilings = replace(
                    DEFAULT_HOST_CEILINGS, **{field: maximum}
                )
                document = copy.deepcopy(self.source)
                mutate(document)
                path = Path(directory) / f"{field}.json"
                path.write_text(json.dumps(document), encoding="utf-8")
                result = service.check_file(path)
                with self.subTest(field=field):
                    self.assertEqual(code, result["diagnostics"][0]["code"])

    def test_registry_data_cannot_select_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for index, (extensions, code) in enumerate(
                (
                    ({"unknown_namespace": [{"id": "x"}]}, "ArtifactSchemaViolation"),
                    (
                        {"planning_models": [{"module": "evil.payload"}]},
                        "ExecutableResourceForbidden",
                    ),
                )
            ):
                document = copy.deepcopy(self.source)
                document["registry_extensions"] = extensions
                result = self._check(document, directory, f"registry-{index}.json")
                self.assertEqual(code, result["diagnostics"][0]["code"])

    def test_actual_cli_returns_stable_json_for_invalid_pair(self) -> None:
        document = copy.deepcopy(self.source)
        document["runtime_contract"] = {
            "contract_id": "runtime.staged-treatment",
            "revision": "1",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-pair.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "-m", "src.artifacts.cli", "run", str(path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        payload = json.loads(completed.stdout)
        self.assertNotEqual(0, completed.returncode)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertEqual(
            "ExecutionContractPairNotAdmitted",
            payload["evaluation"]["check"]["diagnostics"][0]["code"],
        )


if __name__ == "__main__":
    unittest.main()
