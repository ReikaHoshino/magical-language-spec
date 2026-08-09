"""Read-only fixture boundaries used by the v0.8 reference evaluator."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .schema import ROOT

REGISTRY_PATH = ROOT / "examples" / "core-config" / "semantic-registry.json"
WORLD_INDEX_PATH = ROOT / "examples" / "core-config" / "world-index.json"
ESTIMATOR_PROFILE_PATH = ROOT / "examples" / "estimator-profiles" / "synthetic-reference-v1.json"
CANONICAL_PIPELINE_PATH = ROOT / "examples" / "canonical-water-ball" / "pipeline.json"

ENERGY_CATEGORIES = (
    "physical_work",
    "reaction_or_thermodynamic",
    "channel_open",
    "channel_maintenance",
    "control",
    "observation_information",
    "synchronization",
    "losses",
    "reserved_margin",
)


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


class ReadOnlySemanticRegistry:
    """Small read-only adapter over the reference SemanticRegistry fixture."""

    def __init__(self, path: Path = REGISTRY_PATH) -> None:
        self.path = Path(path)
        self.document = load_json(self.path)

    @property
    def revision(self) -> str:
        return str(self.document["metadata"]["revision"])

    @property
    def registry_hash(self) -> Any:
        return copy.deepcopy(self.document.get("registry_hash"))

    def semantic_kind(self, identifier: str) -> dict[str, Any] | None:
        for entry in self.document["namespaces"]["semantic_kinds"]:
            if entry.get("id") == identifier:
                return copy.deepcopy(entry)
        return None

    def conservation_ledger(self, identifier: str) -> dict[str, Any] | None:
        for entry in self.document["namespaces"]["conservation_ledgers"]:
            if entry.get("id") == identifier:
                return copy.deepcopy(entry)
        return None


class ReadOnlyWorldIndex:
    """Deterministic symbolic lookup that never fabricates authoritative Ref values."""

    def __init__(self, path: Path = WORLD_INDEX_PATH) -> None:
        self.path = Path(path)
        self.document = load_json(self.path)

    @property
    def world_index_revision(self) -> str:
        return str(self.document["world_index_revision"])

    @property
    def source_world_revision(self) -> str:
        return str(self.document["source_world_revision"])

    def resolve_symbolic(self, symbol: str, required_type: str | None = None) -> dict[str, Any]:
        ids = list(self.document["indexes"]["symbolic"].get(symbol, []))
        records = {record["entity_id"]: record for record in self.document.get("records", [])}
        candidates: list[dict[str, Any]] = []
        for entity_id in ids:
            record = records.get(entity_id)
            if record is None:
                continue
            if required_type is not None and required_type not in record.get("type_tags", []):
                continue
            candidates.append(
                {
                    "entity_id": entity_id,
                    "type_evidence": list(record.get("type_tags", [])),
                    "selection_evidence": [f"symbolic:{symbol}"],
                    "visibility_evidence": [
                        record.get("visibility_metadata", {}).get("discoverability_class", "unknown")
                    ],
                    "record_revision": record.get("record_revision"),
                }
            )
        return {
            "selector": {"kind": "Symbolic", "symbol": symbol},
            "candidates": candidates,
            "index_revision": self.world_index_revision,
            "source_world_revision": self.source_world_revision,
            "truncated": False,
            "authoritative_revalidation": "Required",
        }


class SyntheticReferenceEstimator:
    """Evaluate only profile-declared deterministic fixture coefficients."""

    def __init__(self, path: Path = ESTIMATOR_PROFILE_PATH) -> None:
        self.path = Path(path)
        self.profile = load_json(self.path)

    @property
    def identity(self) -> str:
        metadata = self.profile["metadata"]
        return f"{metadata['artifact_id']}@{metadata['revision']}"

    def evaluate(self) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
        components: dict[str, dict[str, Any]] = {}
        resources: list[dict[str, Any]] = []
        timing = "Required timing model unavailable."

        for model in self.profile["models"]:
            if model.get("availability", {}).get("status") != "Available":
                continue
            coefficients = model.get("coefficients", [])
            if len(coefficients) != 1:
                continue
            value = coefficients[0].get("value", {})
            estimate = {
                "kind": "Exact",
                "value": value.get("value"),
                "unit": value.get("unit"),
                "dimension": value.get("semantic_type"),
                "assumption_ids": [],
                "evidence_ids": [self.identity],
            }
            domain = model.get("domain")
            category = str(model.get("category"))
            if domain == "Energy" and category in ENERGY_CATEGORIES:
                components[category] = estimate
            elif domain == "Resource":
                resources.append({"kind": category, "estimate": estimate})
            elif domain == "Timing":
                timing = (
                    f"Synthetic physical-duration estimate is {value.get('value')} "
                    f"{value.get('unit')}; physical time remains distinct from runtime tick metadata."
                )

        if set(components) == set(ENERGY_CATEGORIES):
            numeric = sum(float(components[name]["value"]) for name in ENERGY_CATEGORIES)
            total: dict[str, Any] = {
                "kind": "Exact",
                "value": int(numeric) if numeric.is_integer() else numeric,
                "unit": "J",
                "dimension": "Energy",
                "assumption_ids": [],
                "evidence_ids": [self.identity],
            }
        else:
            total = {
                "kind": "Unknown",
                "reason": "ModelDependent",
                "unit": "J",
                "dimension": "Energy",
                "assumption_ids": [],
                "evidence_ids": [self.identity],
            }

        energy = {
            "total": total,
            "components": components,
            "display_unit": "J",
            "accounting_boundary": self.profile["scope"]["use"],
        }
        return energy, resources, timing


def canonical_pipeline(path: Path = CANONICAL_PIPELINE_PATH) -> dict[str, Any]:
    return load_json(path)
