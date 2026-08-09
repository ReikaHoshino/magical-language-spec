from __future__ import annotations

import copy
import inspect
import json
import os
import tempfile
import unittest
from pathlib import Path

from src.artifacts import default_service
from src.artifacts.spell_instance import default_service as legacy_default_service

ROOT = Path(__file__).resolve().parents[1]
BUNDLES = ROOT / "examples" / "spell-instances"


class SpellInstanceBundleTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.service = default_service()

    def test_all_repository_bundles_match_expected_outcomes(self) -> None:
        paths = sorted(BUNDLES.glob("*/*.json"))
        self.assertEqual(12, len(paths))
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual("Accepted", self.service.check_file(path)["status"])
                self.assertEqual("PASS", self.service.run_file(path)["status"])

    def test_stable_required_manifest_is_unchanged(self) -> None:
        manifest = json.loads(
            (ROOT / "conformance" / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(65, len(manifest["cases"]))
        self.assertEqual(
            ["Core-1.0", "Evaluator-1.0", "Adapter-lat-1.0", "Runtime-1.0"],
            [item["class_id"] for item in manifest["classes"]],
        )

    def test_filename_and_instance_id_do_not_select_programs(self) -> None:
        source = json.loads(
            (BUNDLES / "generic" / "GENERIC-001.json").read_text(
                encoding="utf-8"
            )
        )
        source["instance_id"] = "RENAMED-WITHOUT-SUITE-IDENTITY"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "totally-unrelated-name.data"
            path.write_text(json.dumps(source), encoding="utf-8")
            self.assertEqual("PASS", self.service.run_file(path)["status"])

    def test_unknown_kind_version_and_contracts_fail_closed(self) -> None:
        source = json.loads(
            (BUNDLES / "generic" / "GENERIC-001.json").read_text(
                encoding="utf-8"
            )
        )
        with tempfile.TemporaryDirectory() as directory:
            for code, updates in (
                ("UnknownArtifactKind", {"artifact_kind": "UnknownBundle"}),
                ("UnknownArtifactVersion", {"artifact_version": "999"}),
            ):
                document = copy.deepcopy(source)
                document.update(updates)
                path = Path(directory) / f"{code}.json"
                path.write_text(json.dumps(document), encoding="utf-8")
                result = self.service.check_file(path)
                self.assertEqual(code, result["diagnostics"][0]["code"])
            for key, value, code in (
                (
                    "semantic_contract",
                    {"contract_id": "unknown.semantic", "revision": "1"},
                    "UnknownSemanticContract",
                ),
                (
                    "runtime_contract",
                    {"contract_id": "unknown.runtime", "revision": "1"},
                    "UnknownRuntimeContract",
                ),
            ):
                document = copy.deepcopy(source)
                document[key] = value
                path = Path(directory) / f"{code}.json"
                path.write_text(json.dumps(document), encoding="utf-8")
                self.assertEqual(
                    code,
                    self.service.check_file(path)["diagnostics"][0]["code"],
                )

    def test_malformed_duplicate_non_utf8_and_limits_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cases = {
                "malformed.json": (b'{"artifact_kind":', "MalformedJSON"),
                "duplicate.json": (
                    b'{"artifact_kind":"SpellInstanceBundle",'
                    b'"artifact_kind":"SpellInstanceBundle"}',
                    "DuplicateJSONKey",
                ),
                "nonutf8.json": (b"\xff\xfe", "InvalidUTF8"),
                "large.json": (
                    b"{" + b'"x":"' + b"a" * 1_048_576 + b'"}',
                    "ArtifactTooLarge",
                ),
            }
            for name, (payload, code) in cases.items():
                path = Path(directory) / name
                path.write_bytes(payload)
                with self.subTest(name=name):
                    self.assertEqual(
                        code,
                        self.service.check_file(path)["diagnostics"][0]["code"],
                    )

    def test_explicit_input_kind_mismatch_is_rejected(self) -> None:
        result = self.service.check_file(
            BUNDLES / "generic" / "GENERIC-001.json",
            input_kind="DifferentKind",
        )
        self.assertEqual("ArtifactKindMismatch", result["diagnostics"][0]["code"])

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink unavailable")
    def test_symlink_input_is_rejected_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            link = Path(directory) / "linked.json"
            try:
                link.symlink_to(BUNDLES / "generic" / "GENERIC-001.json")
            except OSError:
                self.skipTest("symlink creation not permitted")
            self.assertEqual(
                "InputSymlinkRejected",
                self.service.check_file(link)["diagnostics"][0]["code"],
            )

    def test_adversarial_abort_has_no_partial_commit_and_replays(self) -> None:
        for name, code in (
            ("DEBUG-HELL-002.json", "StaleReference"),
            ("DEBUG-HELL-003.json", "MicrostepBudgetExceeded"),
        ):
            result = self.service.run_file(BUNDLES / "debug-hell" / name)
            with self.subTest(name=name):
                self.assertEqual("PASS", result["status"])
                self.assertEqual(code, result["execution"]["abort"]["code"])
                self.assertTrue(result["execution"]["world_revision_unchanged"])
                self.assertTrue(result["execution"]["history_unchanged"])
                self.assertEqual("DeterministicAbort", result["replay"]["status"])

    def test_mandatory_negative_neighbors_fail_without_partial_commit(self) -> None:
        for filename in ("SA-001.json", "SA-002.json", "SA-003.json", "SA-004.json"):
            source = json.loads(
                (BUNDLES / "success-arcana" / filename).read_text(encoding="utf-8")
            )
            for variant in source["variants"]:
                document = copy.deepcopy(source)
                for mutation in variant["mutations"]:
                    target = document
                    parts = mutation["pointer"].lstrip("/").split("/")
                    for part in parts[:-1]:
                        target = target[part]
                    target[parts[-1]] = mutation["value"]
                document["expected_outcome"].update(
                    {
                        "runtime_status": "Aborted",
                        "diagnostic_codes": [variant["expected_diagnostic"]],
                        "final_invariants": {
                            "Sigma": {"revision": document["initial_world"]["revision"]},
                            "H": document["initial_world"]["history"],
                        },
                        "replay_status": "DeterministicAbort",
                    }
                )
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "renamed-neighbor.json"
                    path.write_text(json.dumps(document), encoding="utf-8")
                    result = self.service.run_file(path)
                with self.subTest(file=filename, variant=variant["variant_id"]):
                    self.assertEqual("PASS", result["status"])
                    self.assertEqual(
                        variant["expected_diagnostic"],
                        result["execution"]["abort"]["code"],
                    )
                    self.assertTrue(result["execution"]["world_revision_unchanged"])
                    self.assertTrue(result["execution"]["history_unchanged"])

    def test_public_import_graph_has_no_dedicated_executor(self) -> None:
        public_module = __import__(
            "src.artifacts.spell_instance_program",
            fromlist=["SpellInstanceService"],
        )
        production_registry = __import__(
            "src.migration.magical_program",
            fromlist=["default_program_translators"],
        )
        source = inspect.getsource(public_module) + inspect.getsource(
            production_registry
        )
        for token in (
            "success_arcana.executors",
            "success_arcana.handlers",
            "debug_hell.executors",
            "debug_hell.handlers",
            "test_generic.executor",
            "test_generic.handler",
            "magical_program_shadow_current",
            "from .spell_instance import",
        ):
            self.assertNotIn(token, source)

    def test_legacy_internal_shapes_are_explicit_oracle_only(self) -> None:
        legacy = legacy_default_service()
        generic = legacy.run_file(BUNDLES / "generic" / "GENERIC-001.json")
        self.assertEqual(
            "IndependentGenericTransition",
            generic["execution"]["runtime"]["world_effect"]["effect_kind"],
        )
        planning = legacy.evaluate_file(
            BUNDLES / "debug-hell" / "DEBUG-HELL-001.json"
        )
        self.assertIn(
            "pathological_analysis",
            planning["report"]["interpretations"]["semantic_ast"],
        )


if __name__ == "__main__":
    unittest.main()
