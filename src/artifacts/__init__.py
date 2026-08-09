"""Experimental, fail-closed artifact ingress."""
from __future__ import annotations

from typing import Any

__all__ = ["SpellInstanceService", "default_service"]


def __getattr__(name: str) -> Any:
    """Load the public service lazily so artifact primitives stay acyclic."""

    if name in __all__:
        from .spell_instance_program import SpellInstanceService, default_service

        return {
            "SpellInstanceService": SpellInstanceService,
            "default_service": default_service,
        }[name]
    raise AttributeError(name)
