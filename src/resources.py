"""Locate canonical magical-language-spec resources in source or installed form.

Tracked canonical resources stay at repository root. Editable/source execution
uses that verified checkout. Wheel/sdist installation uses the build-generated
``magical_language_spec_resources`` package. No network fallback is permitted.
"""
from __future__ import annotations

from functools import lru_cache
from importlib import resources
from pathlib import Path, PurePosixPath
from typing import Any

RESOURCE_PACKAGE = "magical_language_spec_resources"
PROJECT_NAME = "magical-language-spec-reference"
REQUIRED_DIRECTORIES = ("schemas", "examples", "reference", "conformance", "tests")


class ReferenceResourceError(RuntimeError):
    """Fail-closed error for unavailable or invalid reference resources."""

    def __init__(self, code: str, message: str, *, resource: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.resource = resource

    def as_diagnostic(self) -> dict[str, Any]:
        diagnostic: dict[str, Any] = {
            "code": self.code,
            "severity": "fatal",
            "message": self.message,
        }
        if self.resource is not None:
            diagnostic["resource"] = self.resource
        return diagnostic


def _missing_directories(root: Path) -> list[str]:
    return [name for name in REQUIRED_DIRECTORIES if not (root / name).is_dir()]


def _is_verified_checkout(root: Path) -> bool:
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file() or _missing_directories(root):
        return False
    try:
        text = pyproject.read_text(encoding="utf-8")
    except OSError:
        return False
    return f'name = "{PROJECT_NAME}"' in text


def _installed_bundle_root() -> Path:
    try:
        traversable = resources.files(RESOURCE_PACKAGE)
    except (ModuleNotFoundError, AttributeError) as exc:
        raise ReferenceResourceError(
            "ReferenceResourceBundleUnavailable",
            f"installed resource package {RESOURCE_PACKAGE!r} is unavailable",
        ) from exc

    if isinstance(traversable, Path):
        root = traversable
    elif hasattr(traversable, "__fspath__"):
        root = Path(traversable)
    else:
        raise ReferenceResourceError(
            "ReferenceResourceFilesystemUnavailable",
            "installed reference resources are not available as filesystem paths; "
            "standard unpacked wheel/sdist installation is required",
        )

    missing = _missing_directories(root)
    if missing:
        raise ReferenceResourceError(
            "ReferenceResourceBundleIncomplete",
            "installed reference resource bundle is incomplete: " + ", ".join(missing),
        )
    return root.resolve()


@lru_cache(maxsize=1)
def reference_root() -> Path:
    """Return the verified source checkout root or installed resource bundle root."""

    checkout = Path(__file__).resolve().parents[1]
    if _is_verified_checkout(checkout):
        return checkout
    return _installed_bundle_root()


def resource_path(relative: str | PurePosixPath) -> Path:
    """Resolve one required resource below the selected root, rejecting traversal."""

    relative_path = PurePosixPath(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ReferenceResourceError(
            "ReferenceResourcePathInvalid",
            f"resource path must stay below the reference root: {relative_path}",
            resource=str(relative_path),
        )

    root = reference_root()
    path = root.joinpath(*relative_path.parts)
    try:
        resolved = path.resolve()
        resolved.relative_to(root.resolve())
    except (OSError, ValueError) as exc:
        raise ReferenceResourceError(
            "ReferenceResourcePathInvalid",
            f"resource path escapes or cannot be resolved below the reference root: {relative_path}",
            resource=str(relative_path),
        ) from exc

    if not resolved.exists():
        raise ReferenceResourceError(
            "ReferenceResourceMissing",
            f"required reference resource is missing: {relative_path}",
            resource=str(relative_path),
        )
    return resolved
