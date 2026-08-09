from __future__ import annotations

import unittest
from pathlib import Path

from src.resources import ReferenceResourceError, reference_root, resource_path


ROOT = Path(__file__).resolve().parents[1]


class ReferenceResourceLoadingTests(unittest.TestCase):
    def test_source_checkout_is_selected_without_cwd_dependency(self) -> None:
        self.assertEqual(ROOT.resolve(), reference_root())
        self.assertEqual(
            ROOT.resolve() / "schemas" / "nsr.schema.json",
            resource_path("schemas/nsr.schema.json"),
        )

    def test_required_directories_are_available_from_selected_root(self) -> None:
        for relative in ("schemas", "examples", "reference", "conformance", "tests"):
            self.assertTrue(resource_path(relative).is_dir(), relative)

    def test_missing_resource_fails_with_stable_diagnostic(self) -> None:
        with self.assertRaises(ReferenceResourceError) as caught:
            resource_path("schemas/definitely-missing.schema.json")
        self.assertEqual("ReferenceResourceMissing", caught.exception.code)
        self.assertEqual(
            "schemas/definitely-missing.schema.json",
            caught.exception.as_diagnostic()["resource"],
        )

    def test_parent_traversal_is_rejected_before_lookup(self) -> None:
        with self.assertRaises(ReferenceResourceError) as caught:
            resource_path("../outside.json")
        self.assertEqual("ReferenceResourcePathInvalid", caught.exception.code)

    def test_absolute_path_is_rejected_before_lookup(self) -> None:
        with self.assertRaises(ReferenceResourceError) as caught:
            resource_path("/tmp/outside.json")
        self.assertEqual("ReferenceResourcePathInvalid", caught.exception.code)


if __name__ == "__main__":
    unittest.main()
