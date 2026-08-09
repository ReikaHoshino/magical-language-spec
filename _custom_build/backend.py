"""Thin PEP 517 wrapper that generates package-owned reference resources.

Canonical authoring stays in repository-root directories. For wheel builds only,
reviewed resources are copied into ``magical_language_spec_resources`` before
Setuptools runs and are removed again in ``finally``. The source tree therefore
does not retain a second hand-maintained semantic copy.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from shutil import copy2, copytree, ignore_patterns, rmtree
from typing import Iterator

from setuptools import build_meta as _orig
from setuptools.build_meta import *  # noqa: F401,F403 - inherit future PEP 517/660 hooks


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "magical_language_spec_resources"
RESOURCE_DIRECTORIES = (
    "schemas",
    "examples",
    "reference",
    "conformance",
    "grammar",
    "data",
    "tests",
    "planning",
    "spec",
)
RESOURCE_FILES = (
    "README.md",
    "CHANGELOG.md",
    "TODO.md",
    "PROJECT_HANDOFF.md",
    "requirements-dev.txt",
)


def _validate_source() -> None:
    if not (BUNDLE / "__init__.py").is_file():
        raise RuntimeError("resource bundle package marker is missing")
    for relative in RESOURCE_DIRECTORIES:
        if not (ROOT / relative).is_dir():
            raise RuntimeError(f"required resource directory is missing: {relative}")
    for relative in RESOURCE_FILES:
        if not (ROOT / relative).is_file():
            raise RuntimeError(f"required resource file is missing: {relative}")


@contextmanager
def _generated_bundle() -> Iterator[None]:
    """Generate distribution-only copies and always remove them afterwards."""

    _validate_source()
    generated = [*(BUNDLE / name for name in RESOURCE_DIRECTORIES), *(BUNDLE / name for name in RESOURCE_FILES)]
    preexisting = [path for path in generated if path.exists()]
    if preexisting:
        names = ", ".join(str(path.relative_to(BUNDLE)) for path in preexisting)
        raise RuntimeError(
            "generated resource paths already exist; refusing to overwrite a possible "
            f"second source of truth: {names}"
        )

    ignored = ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".DS_Store")
    try:
        for relative in RESOURCE_DIRECTORIES:
            copytree(ROOT / relative, BUNDLE / relative, ignore=ignored)
        for relative in RESOURCE_FILES:
            copy2(ROOT / relative, BUNDLE / relative)
        yield
    finally:
        for relative in RESOURCE_DIRECTORIES:
            path = BUNDLE / relative
            if path.exists():
                rmtree(path)
        for relative in RESOURCE_FILES:
            path = BUNDLE / relative
            if path.exists():
                path.unlink()


def build_wheel(
    wheel_directory: str,
    config_settings=None,
    metadata_directory: str | None = None,
) -> str:
    with _generated_bundle():
        return _orig.build_wheel(wheel_directory, config_settings, metadata_directory)
