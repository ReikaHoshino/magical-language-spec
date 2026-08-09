"""Installed entry point for the conformance runner.

The repository-local script keeps its source-checkout behavior. This wrapper
redirects its global resource paths to the verified source or installed bundle
before executing the existing deterministic runner.
"""
from __future__ import annotations

from collections.abc import Sequence

from src.resources import reference_root, resource_path


def main(argv: Sequence[str] | None = None) -> int:
    from tools import run_conformance

    run_conformance.ROOT = reference_root()
    run_conformance.DEFAULT_MANIFEST = resource_path("conformance/manifest.json")
    run_conformance.SCHEMA_PATH = resource_path("schemas/conformance-manifest.schema.json")
    return run_conformance.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
