from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from src.migration.magical_program_shadow import translate_boundary_reflection

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT / "examples" / "spell-instances" / "success-arcana" / "SA-001.json"
)


def load():
    return json.loads(SOURCE.read_text(encoding="utf-8"))


class MagicalProgramShadowSA001ModelOwnershipTests(unittest.TestCase):
    def test_bundle_registry_extension_cannot_expand_host_model(self) -> None:
        for mutation in (
            ("valid_domain", "maximum_target_mass_kg", 1_000_000),
            (None, "per_actuation_revalidation", False),
            (None, "no_authority_amplification", False),
        ):
            with self.subTest(mutation=mutation):
                bundle = load()
                model = bundle["registry_extensions"]["controller_models"][0]
                parent, key, value = mutation
                if parent is None:
                    model[key] = value
                else:
                    model[parent][key] = value
                with self.assertRaisesRegex(
                    ValueError, "must exactly match the host-owned registration"
                ):
                    translate_boundary_reflection(bundle)

    def test_program_model_tampering_aborts_without_mutation(self) -> None:
        translation = translate_boundary_reflection(load())
        program = copy.deepcopy(translation.program)
        model = next(
            item for item in program["values"] if item["value_id"] == "controller_model"
        )
        model["fields"]["registered_maximum_target_mass_kg"]["value"] = 1_000_000.0

        world = translation.world.clone()
        before = world.configuration()
        trace = translation.runtime.execute(program, world)
        replay = translation.runtime.replay(
            program, translation.world.clone(), trace
        )

        self.assertEqual("Aborted", trace["status"])
        self.assertEqual("COMMIT", trace["abort"]["stage"])
        self.assertEqual("ControllerModelMismatch", trace["abort"]["code"])
        self.assertEqual(before, world.configuration())
        self.assertEqual("DeterministicAbort", replay["status"])


if __name__ == "__main__":
    unittest.main()
