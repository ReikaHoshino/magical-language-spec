from __future__ import annotations

import unittest

from src.runtime.magical_program import RuntimeContractRegistration


class MagicalProgramStructuredRegistrationTests(unittest.TestCase):
    def test_runtime_registry_rejects_untyped_structured_signatures(self) -> None:
        def executor(context, effect, world):
            return {"kind": "effect_result", "status": "Committed"}

        for wildcard in ("object", "array", "any", "*"):
            with self.subTest(wildcard=wildcard), self.assertRaises(ValueError):
                RuntimeContractRegistration(
                    "bad.structured-runtime",
                    "1",
                    "effect.invoke",
                    (wildcard,),
                    "effect_result",
                    0,
                    executor,
                )


if __name__ == "__main__":
    unittest.main()
