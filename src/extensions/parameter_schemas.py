"""Host-owned parameter schemas for admitted experimental executors."""
from __future__ import annotations

from typing import Any


STRING = {"type": "string", "minLength": 1}
NUMBER = {"type": "number"}
NONNEGATIVE = {"type": "number", "minimum": 0}
POSITIVE = {"type": "number", "exclusiveMinimum": 0}
BOOLEAN = {"type": "boolean"}


def closed(properties: dict[str, Any], *, required: tuple[str, ...] | None = None) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": list(required or properties.keys()),
        "properties": properties,
        "additionalProperties": False,
    }


BOUNDARY_REFLECTION_PARAMETERS = closed({
    "target_entity_id": STRING,
    "reaction_anchor_id": STRING,
    "ledger_id": STRING,
    "controller_id": STRING,
    "protected_region_id": STRING,
    "coefficient_of_restitution": {"type": "number", "minimum": 0, "maximum": 1},
    "maximum_target_mass_kg": POSITIVE,
    "maximum_incident_momentum_kg_m_s": NONNEGATIVE,
    "maximum_impulse_kg_m_s": NONNEGATIVE,
    "maximum_energy_j": NONNEGATIVE,
    "event_latency_ms": NONNEGATIVE,
    "max_event_latency_ms": NONNEGATIVE,
    "jitter_ms": NONNEGATIVE,
    "max_jitter_ms": NONNEGATIVE,
    "authorized_event_id": STRING,
    "reflection_event_id": STRING,
    "result_world_revision": STRING,
})

STAGED_TREATMENT_PARAMETERS = closed({
    "patient_id": STRING,
    "proxy_id": STRING,
    "sink_id": STRING,
    "donor_id": STRING,
    "energy_reservoir_id": STRING,
    "patient_lease_id": STRING,
    "ledger_id": STRING,
    "correspondence_token_id": STRING,
    "correspondence_unique": BOOLEAN,
    "reverse_proxy_effect": BOOLEAN,
    "identity_policy": {"const": "IdentityPolicy<Organism>"},
    "irreversible_information_loss": BOOLEAN,
    "excess_thermal_energy_j": NONNEGATIVE,
    "removable_fluid_kg": NONNEGATIVE,
    "donor_matter_kg": NONNEGATIVE,
    "repair_energy_j": NONNEGATIVE,
    "manifest_energy_j": NONNEGATIVE,
    "event_ids": {"type": "array", "minItems": 3, "maxItems": 3, "items": STRING},
    "result_world_revision": STRING,
})

EVIDENCE_FUSION_PARAMETERS = closed({
    "subject_id": STRING,
    "ledger_id": STRING,
    "history_revision": STRING,
    "evidence_revision": STRING,
    "winner_confidence": {"type": "number", "minimum": 0, "maximum": 1},
    "confidence_threshold": {"type": "number", "minimum": 0, "maximum": 1},
    "minimum_evidence_count": {"type": "integer", "minimum": 1},
    "current_measurement_id": STRING,
    "observer_id": STRING,
    "ranking": {
        "type": "array",
        "minItems": 1,
        "items": closed({
            "hypothesis_id": STRING,
            "score": {"type": "number", "minimum": 0, "maximum": 1},
        }),
    },
    "evidence_fusion_model": closed({"model_id": STRING, "revision": STRING}),
    "artifact_id": STRING,
    "display_requested": BOOLEAN,
    "display_energy_j": NONNEGATIVE,
    "observation_energy_j": NONNEGATIVE,
    "event_id": STRING,
    "conflicting_identity": BOOLEAN,
}, required=(
    "subject_id", "ledger_id", "history_revision", "evidence_revision",
    "winner_confidence", "confidence_threshold", "minimum_evidence_count",
    "current_measurement_id", "observer_id", "ranking", "evidence_fusion_model",
    "artifact_id", "display_requested", "display_energy_j", "observation_energy_j", "event_id",
))

EXPLOSION_PARAMETERS = closed({
    "origin_entity_id": STRING,
    "region_id": STRING,
    "medium_model": closed({
        "model_id": STRING,
        "revision": STRING,
        "medium_revision": STRING,
        "attenuation_policy": {"const": "LinearRadialV1"},
    }),
    "radius_m": POSITIVE,
    "maximum_radius_m": POSITIVE,
    "duration_s": POSITIVE,
    "release_energy_j": POSITIVE,
    "pressure_energy_fraction": {"type": "number", "minimum": 0, "maximum": 1},
    "thermal_energy_fraction": {"type": "number", "minimum": 0, "maximum": 1},
    "peak_pressure_pa": POSITIVE,
    "maximum_peak_pressure_pa": POSITIVE,
    "maximum_impulse_kg_m_s": POSITIVE,
    "maximum_thermal_energy_j": NONNEGATIVE,
    "maximum_affected_entities": {"type": "integer", "minimum": 1},
    "occlusion_policy": {"const": "NoOcclusionFixtureDomain"},
    "reaction_anchor_id": STRING,
    "ledger_id": STRING,
    "capability_id": STRING,
    "lease_id": STRING,
    "observation_world_revision": STRING,
    "result_world_revision": STRING,
    "activation_event_id": STRING,
    "termination_event_id": STRING,
})

PREPARE_BOUND_TRANSIT_PARAMETERS = closed({
    "bound_identity": STRING,
})

REACTIVE_BUDGET_PARAMETERS = closed({
    "reactive_microstep_budget": {"type": "integer", "minimum": 0},
})

EMPTY_PARAMETERS = closed({})
