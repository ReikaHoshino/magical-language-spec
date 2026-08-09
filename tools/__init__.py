"""Repository-local reference utilities.

When imported as the installed ``tools`` package, configure the Latin adapter's
default lexicon through the shared reference-resource locator. Executing
``tools/latin_adapter.py`` directly from a source checkout still uses its
checkout-relative default and does not pass through this package initializer.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


def _configure_latin_adapter_resources() -> None:
    from src.resources import resource_path
    from . import latin_adapter

    original = latin_adapter.normalize_with_adapter
    if getattr(original, "_resource_aware_default", False):
        return

    default_lexicon = resource_path("examples/latin-adapter/minimal-lexicon.json")
    latin_adapter.DEFAULT_LEXICON = default_lexicon

    def normalize_with_adapter(
        adapter_id: str,
        source: str | bytes,
        *,
        ambiguity_policy: str = "StrictReject",
        lexicon_path: Path | None = None,
    ) -> dict[str, Any]:
        return original(
            adapter_id,
            source,
            ambiguity_policy=ambiguity_policy,
            lexicon_path=default_lexicon if lexicon_path is None else lexicon_path,
        )

    normalize_with_adapter._resource_aware_default = True  # type: ignore[attr-defined]
    latin_adapter.normalize_with_adapter = normalize_with_adapter


_configure_latin_adapter_resources()
