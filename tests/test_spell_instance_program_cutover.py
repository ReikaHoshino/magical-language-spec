from __future__ import annotations

import inspect
import json
import tempfile
import unittest
from pathlib import Path

import src.artifacts as artifacts
from src.artifacts.spell_instance_program import default_service
from src.migration.magical_program import default_program_translators

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "conformance" / "magical-program-shadow-migration.json"


class SpellInstanceProgramCutoverTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.manifest = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.service = default_service()

    def test_public_api_selects_the_generic_service(self) -> None:
        service = artifacts.default_service()
        self.assertEqual(
            "src.artifacts.spell_instance_program",
            service.__class__.__module__,
        )
        self.assertIs(artifacts.SpellInstanceService, service.__class__)

    def test_complete_current_12_bundle_matrix_uses_public_run_path(self) -> None:
        results = []
        for item in sorted(
            self.manifest["inventory"], key=lambda row: row["order"]
        ):
            with self.subTest(migration_id=item["migration_id"]):
                result = self.service.run_file(ROOT / item["path"])
                self.assertEqual("PASS", result["status"], result)
                results.append(result)
        self.assertEqual(12, len(results))
        self.assertEqual(12, len(self.service.program_translators.pairs()))
        self.assertEqual(12, len(default_program_translators().pairs()))

    def test_renaming_inputs_does_not_change_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for item in self.manifest["inventory"]:
                source = ROOT / item["path"]
                renamed = root / f"renamed-{item['order']:02d}.mga.json"
                renamed.write_bytes(source.read_bytes())
                with self.subTest(migration_id=item["migration_id"]):
                    result = self.service.run_file(renamed)
                    self.assertEqual("PASS", result["status"], result)

    def test_production_assembly_does_not_import_legacy_execution(self) -> None:
        public_source = inspect.getsource(
            __import__(
                "src.artifacts.spell_instance_program",
                fromlist=["SpellInstanceService"],
            )
        )
        registry_source = inspect.getsource(
            __import__(
                "src.migration.magical_program",
                fromlist=["default_program_translators"],
            )
        )
        combined = public_source + registry_source
        forbidden = (
            "src.extensions.registration",
            "success_arcana.executors",
            "success_arcana.handlers",
            "debug_hell.executors",
            "debug_hell.handlers",
            "test_generic.executor",
            "test_generic.handler",
            "magical_program_shadow_current",
            "from .spell_instance import",
            "from src.artifacts.spell_instance import",
        )
        for token in forbidden:
            self.assertNotIn(token, combined)

    def test_validation_registries_are_not_execution_owners(self) -> None:
        for registration in self.service.runtime_registry._executors.values():
            self.assertEqual(
                "_unreachable_executor",
                registration.executor.__name__,
            )
        for registration in self.service.semantic_registry._handlers.values():
            self.assertEqual(
                "_unreachable_handler",
                registration.handler.__name__,
            )


if __name__ == "__main__":
    unittest.main()
