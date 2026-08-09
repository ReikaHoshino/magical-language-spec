"""Semantic elaboration owned by admitted SUCCESS-ARCANA contracts."""
from __future__ import annotations

import copy
from typing import Any

from src.extensions.shared import build_report


def explosion_handler(bundle: dict[str, Any]) -> dict[str, Any]:
    """Freeze the deterministic bounded target set without granting authority."""

    elaborated = copy.deepcopy(bundle)
    parameters = elaborated["execution"]["parameters"]
    region_id = parameters["region_id"]
    radius = float(parameters["radius_m"])
    selected = [
        (float(entity["distance_from_origin_m"]), entity_id)
        for entity_id, entity in elaborated["initial_world"]["entities"].items()
        if entity.get("blast_subject") is True
        and entity.get("region_id") == region_id
        and 0 <= float(entity.get("distance_from_origin_m", -1)) <= radius
    ]
    selected.sort(key=lambda item: (item[0], item[1]))
    parameters["prepared_affected_entity_ids"] = [entity_id for _, entity_id in selected]
    parameters["prepared_source_world_revision"] = elaborated["initial_world"]["revision"]
    report = build_report(elaborated)
    report["interpretations"]["semantic_ast"]["target_selection"] = {
        "binding": "PrepareBound",
        "region_id": region_id,
        "predicate": "blast_subject && distance_from_origin_m <= radius_m",
        "ordered_entity_ids": parameters["prepared_affected_entity_ids"],
        "authority_inferred": False,
    }
    return report
