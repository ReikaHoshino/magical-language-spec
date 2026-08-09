from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference" / "package-resources.md"
PYPROJECT = ROOT / "pyproject.toml"
MANIFEST = ROOT / "MANIFEST.in"


class PackageResourceReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reference = REFERENCE.read_text(encoding="utf-8")
        cls.pyproject = PYPROJECT.read_text(encoding="utf-8")
        cls.manifest = MANIFEST.read_text(encoding="utf-8")

    def test_contract_publishes_ownership_and_failure_boundaries(self) -> None:
        for marker in (
            "**Status:** normative reference-implementation distribution/resource contract",
            "## Purpose",
            "## Non-goals",
            "## Depends on",
            "## Key invariants",
            "build-time bundle != second semantic truth",
            "missing package resource != fallback to unrelated checkout/cwd file",
            "package resource handling != SemanticFingerprint/content-hash semantics",
            "No third search path, parent-directory scan, cwd fallback, or network fallback is permitted.",
        ):
            self.assertIn(marker, self.reference)

    def test_stable_resource_diagnostics_are_documented(self) -> None:
        for code in (
            "ReferenceResourceBundleUnavailable",
            "ReferenceResourceFilesystemUnavailable",
            "ReferenceResourceBundleIncomplete",
            "ReferenceResourcePathInvalid",
            "ReferenceResourceMissing",
        ):
            self.assertIn(code, self.reference)

    def test_build_metadata_matches_documented_backend_and_sources(self) -> None:
        self.assertIn('build-backend = "backend"', self.pyproject)
        self.assertIn('backend-path = ["_custom_build"]', self.pyproject)
        self.assertIn("magical_language_spec_resources", self.pyproject)
        for path in (
            "_custom_build",
            "schemas",
            "examples",
            "reference",
            "conformance",
            "tests",
            "spec",
        ):
            self.assertIn(f"graft {path}", self.manifest)

    def test_issue_60_does_not_claim_complete_v1_readiness(self) -> None:
        self.assertIn(
            "resolving this contract alone does not make v1.0 RC ready",
            self.reference,
        )


if __name__ == "__main__":
    unittest.main()
