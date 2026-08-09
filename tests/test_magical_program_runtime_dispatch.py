from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = ROOT / "src" / "runtime"
CORE_FILES = [
    RUNTIME_ROOT / "magical_program_engine.py",
    RUNTIME_ROOT / "magical_program_prepare.py",
    RUNTIME_ROOT / "magical_program_commit.py",
    RUNTIME_ROOT / "magical_program_binding.py",
    RUNTIME_ROOT / "magical_program_contracts.py",
    RUNTIME_ROOT / "magical_program_model.py",
]
COMPATIBILITY_FILES = [
    RUNTIME_ROOT / "magical_program_verified.py",
    RUNTIME_ROOT / "magical_program_public.py",
    RUNTIME_ROOT / "magical_program_safe.py",
    RUNTIME_ROOT / "magical_program_final.py",
    RUNTIME_ROOT / "magical_program_release.py",
    RUNTIME_ROOT / "magical_program_release_entrypoint.py",
    RUNTIME_ROOT / "magical_program_entrypoint.py",
    RUNTIME_ROOT / "magical_program_runtime.py",
]


class MagicalProgramRuntimeDispatchTests(unittest.TestCase):
    def test_core_has_no_fixture_name_or_contract_id_dispatch(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8") for path in CORE_FILES
        )
        for forbidden in (
            "SUCCESS-ARCANA",
            "SA-001",
            "SA-002",
            "SA-003",
            "SA-004",
            "DEBUG-HELL",
            "display_name",
            "spell_name",
            "embedded_payload",
            "shadow.spell-instance",
            "if registration.contract_id",
        ):
            self.assertNotIn(forbidden, combined)
        self.assertNotIn("filename", combined.lower())
        engine = (RUNTIME_ROOT / "magical_program_engine.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("generic.transition", engine)
        self.assertNotIn("generic.observe", engine)

    def test_exactly_one_runtime_class_owns_public_behavior(self) -> None:
        implementations = []
        for path in [RUNTIME_ROOT / "magical_program.py", *CORE_FILES, *COMPATIBILITY_FILES]:
            text = path.read_text(encoding="utf-8")
            if "class MagicalProgramRuntime" in text:
                implementations.append(path.name)
        self.assertEqual(["magical_program_engine.py"], implementations)

        public = (RUNTIME_ROOT / "magical_program.py").read_text(encoding="utf-8")
        self.assertIn(
            "from .magical_program_engine import MagicalProgramRuntime", public
        )
        for path in COMPATIBILITY_FILES:
            text = path.read_text(encoding="utf-8")
            self.assertIn("from .magical_program import *", text)
            self.assertNotIn("class MagicalProgramRuntime", text)

    def test_module_package_name_collisions_are_removed(self) -> None:
        self.assertFalse((RUNTIME_ROOT / "magical_program_entrypoint").exists())
        self.assertFalse((RUNTIME_ROOT / "magical_program_runtime").exists())


if __name__ == "__main__":
    unittest.main()
