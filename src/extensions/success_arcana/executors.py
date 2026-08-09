"""Runtime effects owned by the optional SUCCESS-ARCANA extension module."""
from __future__ import annotations

import copy
from typing import Any

from src.runtime.sandbox import PreparedPlan, RuntimeExecutionError, SandboxWorld


def _operations(prepared: PreparedPlan) -> list[dict[str, Any]]:
    return [{"operation": operation, "ordinal": index, "status": "Committed"} for index, operation in enumerate(prepared.operations)]


def _effect(prepared: PreparedPlan, world: SandboxWorld, event_id: str, effect_kind: str, identity_policy: str) -> dict[str, Any]:
    return {
        "operations": _operations(prepared),
        "world_effect": {
            "source_world_revision": prepared.source_world_revision,
            "result_world_revision": world.revision,
            "history_event_id": event_id,
            "effect_kind": effect_kind,
            "entity_identity_policy": identity_policy,
        },
    }


def boundary_reflection(prepared: PreparedPlan, world: SandboxWorld) -> dict[str, Any]:
    p = prepared.typed_mir["typed_parameters"]
    target = world.entities.get(p["target_entity_id"])
    anchor = world.entities.get(p["reaction_anchor_id"])
    if not target or not anchor:
        raise RuntimeExecutionError("ResolutionFailure", "Boundary target or reaction anchor is absent.", stage="COMMIT")
    mass = float(target.get("mass_kg", 0))
    incident = float(target.get("normal_momentum_kg_m_s", 0))
    if mass <= 0 or mass > float(p["maximum_target_mass_kg"]) or abs(incident) > float(p["maximum_incident_momentum_kg_m_s"]):
        raise RuntimeExecutionError("ControllerDomainExceeded", "Target is outside the admitted controller domain.", stage="COMMIT")
    if float(p["event_latency_ms"]) > float(p["max_event_latency_ms"]) or float(p["jitter_ms"]) > float(p["max_jitter_ms"]):
        raise RuntimeExecutionError("ControllerTimingViolation", "Controller timing exceeds the admitted bound.", stage="COMMIT")
    event_id = p["authorized_event_id"]
    effect_kind = "AuthorizedBoundaryPass"
    if target.get("crossing") and not target.get("authorized"):
        restitution = float(p["coefficient_of_restitution"])
        impulse = (1.0 + restitution) * incident
        final_momentum = -restitution * incident
        dissipated = incident * incident / (2.0 * mass) - final_momentum * final_momentum / (2.0 * mass)
        if abs(impulse) > float(p["maximum_impulse_kg_m_s"]) or dissipated > float(p["maximum_energy_j"]):
            raise RuntimeExecutionError("ControllerOverload", "Actuation exceeds the saturation envelope.", stage="COMMIT")
        target["normal_momentum_kg_m_s"] = final_momentum
        anchor["normal_momentum_kg_m_s"] = float(anchor.get("normal_momentum_kg_m_s", 0)) + impulse
        world.ledgers[p["ledger_id"]].update({"target_momentum_kg_m_s": final_momentum, "anchor_momentum_kg_m_s": anchor["normal_momentum_kg_m_s"], "dissipated_energy_j": dissipated})
        event_id = p["reflection_event_id"]
        effect_kind = "BoundaryReflectionActuation"
    world.controllers[p["controller_id"]] = {"active": True, "semantic_projection": copy.deepcopy(p), "per_actuation_revalidation": True}
    world.revision = p["result_world_revision"]
    world.history.append({"event_id": event_id, "effect_kind": effect_kind, "source_world_revision": prepared.source_world_revision, "result_world_revision": world.revision, "atomic_accounting": ["TargetMomentum", "AnchorReaction", "DissipatedEnergy"]})
    return _effect(prepared, world, event_id, effect_kind, "PreserveExistingIdentity")


def staged_treatment(prepared: PreparedPlan, world: SandboxWorld) -> dict[str, Any]:
    p = prepared.typed_mir["typed_parameters"]
    patient, proxy, sink, donor, reservoir = (world.entities.get(p[key]) for key in ("patient_id", "proxy_id", "sink_id", "donor_id", "energy_reservoir_id"))
    if not all((patient, proxy, sink, donor, reservoir)):
        raise RuntimeExecutionError("ResolutionFailure", "Treatment entities do not resolve uniquely.", stage="COMMIT")
    if not p["correspondence_unique"]:
        raise RuntimeExecutionError("ResolutionFailure", "CorrespondenceToken is ambiguous.", stage="COMMIT")
    if p["reverse_proxy_effect"]:
        raise RuntimeExecutionError("ReverseCorrespondenceForbidden", "Correspondence is one-way selection evidence.", stage="COMMIT")
    if p["irreversible_information_loss"] or p["identity_policy"] != "IdentityPolicy<Organism>":
        raise RuntimeExecutionError("IdentityPreservationFailure", "Identity-critical information cannot be synthesized.", stage="COMMIT")
    lease = world.leases.get(p["patient_lease_id"], {})
    if not lease.get("consent"):
        raise RuntimeExecutionError("AuthorityError", "Current patient consent is required.", stage="COMMIT")
    energy = float(p["repair_energy_j"]) + float(p["manifest_energy_j"])
    if float(sink.get("energy_capacity_j", 0)) < float(p["excess_thermal_energy_j"]) or float(sink.get("matter_capacity_kg", 0)) < float(p["removable_fluid_kg"]):
        raise RuntimeExecutionError("ResourceInsufficient", "Treatment sink capacity is insufficient.", stage="COMMIT")
    if float(donor.get("available_matter_kg", 0)) < float(p["donor_matter_kg"]) or float(reservoir.get("available_energy_j", 0)) < energy:
        raise RuntimeExecutionError("ResourceInsufficient", "Treatment resources are insufficient.", stage="COMMIT")
    identity = patient["identity_id"]
    sink["absorbed_energy_j"] += float(p["excess_thermal_energy_j"])
    sink["absorbed_matter_kg"] += float(p["removable_fluid_kg"])
    donor["available_matter_kg"] -= float(p["donor_matter_kg"])
    reservoir["available_energy_j"] -= energy
    patient["injury"].update({"excess_thermal_energy_j": 0, "removable_fluid_kg": 0, "chemical_deviation": "repaired", "structural_deviation": "repaired"})
    patient.update({"tissue_repaired": True, "identity_id": identity})
    proxy["manifested_descriptor"] = {"kind": "DamageDescriptor", "source_patient_id": patient["entity_id"], "reverse_effect": False, "provenance": p["correspondence_token_id"]}
    for stage, event_id in zip(("TreatmentStabilize", "TreatmentRepair", "TreatmentManifest"), p["event_ids"]):
        world.history.append({"event_id": event_id, "effect_kind": stage, "rollback": False})
    world.ledgers[p["ledger_id"]].update({"transferred_to_sink_energy_j": float(p["excess_thermal_energy_j"]), "treatment_energy_consumed_j": energy})
    world.revision = p["result_world_revision"]
    return _effect(prepared, world, p["event_ids"][-1], "StagedTreatment", "IdentityPolicy<Organism>")


def evidence_fusion(prepared: PreparedPlan, world: SandboxWorld) -> dict[str, Any]:
    p = prepared.typed_mir["typed_parameters"]
    subject = world.entities.get(p["subject_id"])
    if not subject or p.get("conflicting_identity"):
        raise RuntimeExecutionError("ResolutionFailure", "Subject identity is unresolved.", stage="COMMIT")
    if world.runtime_state.get("history_revision") != p["history_revision"] or world.runtime_state.get("evidence_revision") != p["evidence_revision"]:
        raise RuntimeExecutionError("EvidenceRevisionStale", "Frozen evidence revisions are stale.", stage="COMMIT")
    model = p["evidence_fusion_model"]
    if model.get("model_id") != "evidence.snapshot-fusion" or model.get("revision") != "1":
        raise RuntimeExecutionError("EvidenceModelMismatch", "EvidenceFusionModel identity/revision mismatch.", stage="COMMIT")
    if float(p["winner_confidence"]) < float(p["confidence_threshold"]):
        raise RuntimeExecutionError("EvidenceThresholdNotMet", "No candidate satisfies the threshold.", stage="COMMIT")
    ledger = world.ledgers[p["ledger_id"]]
    if p["display_requested"] and float(ledger.get("available_energy_j", 0)) < float(p["display_energy_j"]):
        raise RuntimeExecutionError("DisplayEnergyInsufficient", "Physical display energy is insufficient.", stage="COMMIT")
    historical = [event for event in world.history if event.get("effect_kind") == "HistoricalMeasurement"]
    current = {"event_id": p["current_measurement_id"], "effect_kind": "TraceMeasurement", "source_id": p["observer_id"], "value": subject.get("current_trace")}
    bundle = sorted([*historical, current], key=lambda item: (str(item.get("source_id")), str(item.get("event_id"))))
    if len(bundle) < int(p["minimum_evidence_count"]):
        raise RuntimeExecutionError("EvidenceThresholdNotMet", "Minimum evidence policy is not satisfied.", stage="COMMIT")
    ranking = sorted(copy.deepcopy(p["ranking"]), key=lambda item: (-item["score"], item["hypothesis_id"]))
    artifact = {"artifact_id": p["artifact_id"], "revision": "1", "evidence_bundle": bundle, "model": copy.deepcopy(p["evidence_fusion_model"]), "ranking": ranking, "winner_hypothesis_id": ranking[0]["hypothesis_id"], "confidence_is_truth": False, "physical_display_effect": False}
    world.runtime_state.setdefault("evidence_store", {}).setdefault("artifacts", {})[p["artifact_id"]] = artifact
    ledger["consumed_energy_j"] = float(ledger.get("consumed_energy_j", 0)) + float(p["observation_energy_j"])
    world.history.append({"event_id": p["event_id"], "effect_kind": "ObservationArtifactPublished", "world_state_changed": False, "future_prediction": False, "history_rewind": False})
    return _effect(prepared, world, p["event_id"], "NonPhysicalObservationArtifact", "RevalidateExistingIdentity")


def explosion(prepared: PreparedPlan, world: SandboxWorld) -> dict[str, Any]:
    """Commit a finite prepare-bound blast with deterministic accounting."""

    p = prepared.typed_mir["typed_parameters"]
    origin = world.entities.get(p["origin_entity_id"])
    anchor = world.entities.get(p["reaction_anchor_id"])
    ledger = world.ledgers.get(p["ledger_id"])
    capability = world.capabilities.get(p["capability_id"])
    lease = world.leases.get(p["lease_id"])
    if origin is None or anchor is None:
        raise RuntimeExecutionError("ResolutionFailure", "Explosion origin or reaction anchor is absent.", stage="COMMIT")
    if ledger is None or not ledger.get("active"):
        raise RuntimeExecutionError("ConservationProofFailure", "Explosion accounting sink is unavailable.", stage="COMMIT")
    if capability is None or not capability.get("active") or capability.get("region_id") != p["region_id"] or capability.get("effect_class") != "BoundedExplosion":
        raise RuntimeExecutionError("AuthorityError", "Explosion Capability does not admit the bounded target region.", stage="COMMIT")
    if lease is None or not lease.get("active"):
        raise RuntimeExecutionError("AuthorityError", "Explosion Lease is absent or expired.", stage="COMMIT")
    if p["prepared_source_world_revision"] != prepared.source_world_revision or p["observation_world_revision"] != prepared.source_world_revision:
        raise RuntimeExecutionError("StaleReference", "Explosion observation revision is stale.", stage="COMMIT")
    if origin.get("medium_revision") != p["medium_model"]["medium_revision"]:
        raise RuntimeExecutionError("ExplosionModelMismatch", "Explosion medium model revision is not authoritative.", stage="COMMIT")
    if float(p["radius_m"]) > float(p["maximum_radius_m"]) or float(p["radius_m"]) > float(capability.get("maximum_radius_m", 0)):
        raise RuntimeExecutionError("ExplosionDomainExceeded", "Explosion radius exceeds the admitted domain.", stage="COMMIT")
    if float(p["peak_pressure_pa"]) > float(p["maximum_peak_pressure_pa"]):
        raise RuntimeExecutionError("ExplosionPressureExceeded", "Explosion peak pressure exceeds the admitted envelope.", stage="COMMIT")
    pressure_fraction = float(p["pressure_energy_fraction"])
    thermal_fraction = float(p["thermal_energy_fraction"])
    if abs((pressure_fraction + thermal_fraction) - 1.0) > 1e-12:
        raise RuntimeExecutionError("ExplosionAccountingMismatch", "Pressure and thermal Energy allocations must sum to one.", stage="COMMIT")
    energy = float(p["release_energy_j"])
    thermal_energy = energy * thermal_fraction
    if thermal_energy > float(p["maximum_thermal_energy_j"]):
        raise RuntimeExecutionError("ExplosionThermalExceeded", "Explosion thermal allocation exceeds the admitted envelope.", stage="COMMIT")
    if float(ledger.get("available_energy_j", 0)) < energy:
        raise RuntimeExecutionError("ConservationProofFailure", "Explosion Energy reservoir is insufficient.", stage="COMMIT")

    affected_ids = list(p["prepared_affected_entity_ids"])
    if len(affected_ids) > int(p["maximum_affected_entities"]):
        raise RuntimeExecutionError("ExplosionTargetLimitExceeded", "Prepare-bound explosion target count exceeds the admitted envelope.", stage="COMMIT")
    affected: list[dict[str, Any]] = []
    weights: list[float] = []
    radius = float(p["radius_m"])
    previous_pressure = float("inf")
    for entity_id in affected_ids:
        entity = world.entities.get(entity_id)
        if entity is None or entity.get("region_id") != p["region_id"]:
            raise RuntimeExecutionError("StaleReference", "Prepare-bound explosion target is no longer authoritative.", stage="COMMIT")
        distance = float(entity["distance_from_origin_m"])
        attenuation = max(0.0, 1.0 - distance / radius)
        pressure = float(p["peak_pressure_pa"]) * attenuation
        impulse = float(p["maximum_impulse_kg_m_s"]) * attenuation
        if pressure > previous_pressure + 1e-12:
            raise RuntimeExecutionError("ExplosionAttenuationViolation", "Explosion attenuation must be non-increasing by distance.", stage="COMMIT")
        previous_pressure = pressure
        weights.append(attenuation)
        affected.append({"entity_id": entity_id, "distance_m": distance, "attenuation": attenuation, "pressure_pa": pressure, "impulse_kg_m_s": impulse})

    total_weight = sum(weights)
    reaction_impulse = 0.0
    for record, weight in zip(affected, weights):
        entity = world.entities[record["entity_id"]]
        allocated_thermal = 0.0 if total_weight == 0 else thermal_energy * weight / total_weight
        entity["blast_effect"] = {
            "pressure_pa": record["pressure_pa"],
            "radial_impulse_kg_m_s": record["impulse_kg_m_s"],
            "thermal_energy_j": allocated_thermal,
            "duration_s": float(p["duration_s"]),
        }
        reaction_impulse += record["impulse_kg_m_s"]
    anchor["reaction_impulse_kg_m_s"] = float(anchor.get("reaction_impulse_kg_m_s", 0)) - reaction_impulse
    ledger["available_energy_j"] -= energy
    ledger["released_energy_j"] = energy
    ledger["pressure_energy_j"] = energy * pressure_fraction
    ledger["thermal_energy_j"] = thermal_energy
    ledger["reaction_impulse_kg_m_s"] = -reaction_impulse
    world.revision = p["result_world_revision"]
    world.history.extend([
        {
            "event_id": p["activation_event_id"],
            "effect_kind": "BoundedExplosionActivated",
            "affected_entity_ids": affected_ids,
            "released_energy_j": energy,
            "source_world_revision": prepared.source_world_revision,
        },
        {
            "event_id": p["termination_event_id"],
            "effect_kind": "BoundedExplosionTerminated",
            "duration_s": float(p["duration_s"]),
            "result_world_revision": world.revision,
        },
    ])
    return _effect(prepared, world, p["termination_event_id"], "BoundedExplosion", "PrepareBoundExistingIdentity")
