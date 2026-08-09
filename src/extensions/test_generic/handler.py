"""Semantic handler owned by the independent generic extension."""
from __future__ import annotations

from typing import Any

from src.extensions.shared import build_report


def generic_transition_handler(bundle: dict[str, Any]) -> dict[str, Any]:
    return build_report(bundle)
