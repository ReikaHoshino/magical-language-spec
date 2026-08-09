"""True declarative migrations for implemented Success-Arcana contracts."""
from __future__ import annotations

import copy
from typing import Any, Mapping

from src.evaluator.magical_program import MagicalProgramEvaluator
from src.evaluator.magical_program_contracts import (
    ProgramContractRegistration,
    ProgramContractRegistry,
    default_program_contract_registry,
)
from src.runtime.magical_program import (
    MagicalProgramRuntime,
    ProgramRuntimeContractRegistry,
    ProgramRuntimeError,
    RuntimeContractRegistration,
)
from src.runtime.magical_program_model import (
    PreparedProgramEffect,
    RuntimeExecutionContext,
)
from src.runtime.sandbox import SandboxWorld

from .magical_program_shadow_support import (
    ShadowTranslation,
    add_identity_record,
    bundle_contract_pair,
    configure_capability,
    configure_lease,
    configure_ledger,
    profile_from_bundle,
    program_envelope,
    world_from_bundle,
)

_JSON = dict[str, Any]


def _literal(record: Mapping[str, Any], field: str) -> Any:
    return record["fields"][field]["value"]


def _record(type_id: str, **fields: Any) -> _JSON:
    return {
        "kind": "record",
        "type_id": type_id,
        "fields": {
            key: {"kind": "literal", "value": value}
            for key, value in fields.items()
        },
    }


def _ranking_sequence(ranking: list[Mapping[str, Any]]) -> _JSON:
    return {
        "kind": "sequence",
        "element_type": "record:HypothesisScore",
        "items": [
            _record(
                "HypothesisScore",
                hypothesis_id=str(item["hypothesis_id"]),
                score=float(item["score"]),
            )
            for item in ranking
        ],
    }


def evidence_fusion_semantic_registry() -> ProgramContractRegistry:
    registry = default_program_contract_registry()
    registry.register(
        ProgramContractRegistration(
            "evidence.snapshot-fusion",
            "1",
            "evidence.observe",
            (
                "reference",
                "record:EvidenceFusionModel",
                "sequence:record:HypothesisScore",
                "record:EvidenceFusionPolicy",
                "record:CurrentMeasurement",
                "record:ArtifactPublication",
            ),
            "evidence",
            (
                "capabilities",
                "leases",
                "identities",
                "evidence",
                "accounting",
            ),
            0.0,
            0.0,
            1,
            ("OBSERVE",),
            ("SAMPLE",),
        )
    )
    return registry


def _bound_evidence(
    effect: PreparedProgramEffect, kind: str
) -> Mapping[str, Any]:
    matches = [
        item.frozen_record
        for item in effect.evidence_records
        if item.frozen_record.get("kind") == kind
    ]
    if len(matches) != 1:
        raise ProgramRuntimeError(
            "EvidenceRevisionStale",
            f"Expected one bound {kind} record.",
            stage="COMMIT",
        )
    return matches[0]


def evidence_fusion_executor(
    context: RuntimeExecutionContext,
    effect: PreparedProgramEffect,
    world: SandboxWorld,
) -> _JSON:
    (
        subject_ref,
        model,
        ranking_value,
        policy,
        measurement,
        publication,
    ) = effect.frozen_values
    subject_id = subject_ref.get("entity_id")
    subject = world.entities.get(subject_id)
    if subject is None or bool(_literal(policy, "conflicting_identity")):
        raise ProgramRuntimeError(
            "ResolutionFailure",
            "Subject identity is unresolved.",
            stage="COMMIT",
        )

    expected_history_revision = str(_literal(publication, "history_revision"))
    expected_evidence_revision = str(_literal(publication, "evidence_revision"))
    history_record = _bound_evidence(effect, "HistorySnapshot")
    evidence_record = _bound_evidence(effect, "EvidenceSnapshot")
    if (
        history_record.get("snapshot_revision") != expected_history_revision
        or evidence_record.get("snapshot_revision")
        != expected_evidence_revision
    ):
        raise ProgramRuntimeError(
            "EvidenceRevisionStale",
            "Frozen evidence revisions are stale.",
            stage="COMMIT",
        )

    model_id = str(_literal(model, "model_id"))
    model_revision = str(_literal(model, "revision"))
    confidence_is_truth = bool(_literal(model, "confidence_is_truth"))
    if (
        model_id != "evidence.snapshot-fusion"
        or model_revision != "1"
        or confidence_is_truth
    ):
        raise ProgramRuntimeError(
            "EvidenceModelMismatch",
            "EvidenceFusionModel identity/revision mismatch.",
            stage="COMMIT",
        )

    winner_confidence = float(_literal(policy, "winner_confidence"))
    threshold = float(_literal(policy, "confidence_threshold"))
    if winner_confidence < threshold:
        raise ProgramRuntimeError(
            "EvidenceThresholdNotMet",
            "No candidate satisfies the threshold.",
            stage="COMMIT",
        )

    display_requested = bool(_literal(policy, "display_requested"))
    display_energy = float(_literal(policy, "display_energy_j"))
    accounting = effect.accounting_records[0].frozen_record
    ledger = world.ledgers[effect.accounting_records[0].record_id]
    if display_requested and float(accounting.get("available_energy_j", 0.0)) < display_energy:
        raise ProgramRuntimeError(
            "DisplayEnergyInsufficient",
            "Physical display energy is insufficient.",
            stage="COMMIT",
        )

    historical = [
        copy.deepcopy(event)
        for event in world.history
        if event.get("effect_kind") == "HistoricalMeasurement"
    ]
    current = {
        "event_id": str(_literal(measurement, "event_id")),
        "effect_kind": "TraceMeasurement",
        "source_id": str(_literal(measurement, "observer_id")),
        "value": subject.get("current_trace"),
    }
    evidence_bundle = sorted(
        [*historical, current],
        key=lambda item: (str(item.get("source_id")), str(item.get("event_id"))),
    )
    if len(evidence_bundle) < int(_literal(policy, "minimum_evidence_count")):
        raise ProgramRuntimeError(
            "EvidenceThresholdNotMet",
            "Minimum evidence policy is not satisfied.",
            stage="COMMIT",
        )

    ranking = sorted(
        [
            {
                "hypothesis_id": str(_literal(item, "hypothesis_id")),
                "score": float(_literal(item, "score")),
            }
            for item in ranking_value["items"]
        ],
        key=lambda item: (-item["score"], item["hypothesis_id"]),
    )
    if not ranking:
        raise ProgramRuntimeError(
            "EvidenceThresholdNotMet",
            "Evidence ranking is empty.",
            stage="COMMIT",
        )

    artifact_id = str(_literal(publication, "artifact_id"))
    event_id = str(_literal(publication, "event_id"))
    artifacts = world.runtime_state.setdefault("evidence_store", {}).setdefault(
        "artifacts", {}
    )
    if artifact_id in artifacts:
        raise ProgramRuntimeError(
            "ProgramArtifactIdentityCollision",
            f"Artifact {artifact_id!r} already exists.",
            stage="COMMIT",
        )
    artifact = {
        "artifact_id": artifact_id,
        "revision": "1",
        "evidence_bundle": evidence_bundle,
        "model": {"model_id": model_id, "revision": model_revision},
        "ranking": ranking,
        "winner_hypothesis_id": ranking[0]["hypothesis_id"],
        "confidence_is_truth": False,
        "physical_display_effect": False,
    }
    artifacts[artifact_id] = copy.deepcopy(artifact)
    ledger["consumed_energy_j"] = float(ledger.get("consumed_energy_j", 0.0)) + float(
        _literal(policy, "observation_energy_j")
    )
    world.history.append(
        {
            "event_id": event_id,
            "effect_kind": "ObservationArtifactPublished",
            "world_state_changed": False,
            "future_prediction": False,
            "history_rewind": False,
        }
    )
    return {
        "kind": "evidence",
        "status": "Committed",
        "node_id": effect.node_id,
        "contract_id": effect.contract_id,
        "contract_revision": effect.contract_revision,
        "entity_ids": [subject_id],
        "artifact_id": artifact_id,
        "event_id": event_id,
        "artifact": artifact,
        "effect_kind": "NonPhysicalObservationArtifact",
        "identity_policy": "RevalidateExistingIdentity",
        "source_world_revision": context.prepared.source_world_revision,
        "result_world_revision": world.revision,
    }


def translate_evidence_fusion(bundle: Mapping[str, Any]) -> ShadowTranslation:
    parameters = bundle["execution"]["parameters"]
    required = bundle["execution"]["required_evidence"]
    subject_id = str(parameters["subject_id"])
    ledger_id = str(parameters["ledger_id"])
    profile = profile_from_bundle(bundle)
    world = world_from_bundle(bundle, profile)
    subject_revision = str(world.entities[subject_id]["state_revision"])

    capability_ids = [str(item) for item in required["capabilities"]]
    if len(capability_ids) != 3:
        raise ValueError("evidence.snapshot-fusion requires three capabilities")
    for capability_id, effect_name in zip(
        capability_ids,
        ("Discover", "Observe", "PrivacyAccess"),
        strict=True,
    ):
        configure_capability(
            world,
            capability_id,
            entity_id=subject_id,
            effect=effect_name,
        )
    lease_id = str(required["leases"][0])
    configure_lease(
        world,
        lease_id,
        entity_id=subject_id,
        mode="ReadSnapshot",
    )
    configure_ledger(
        world,
        ledger_id,
        entity_id=subject_id,
        kind="ObservationAccounting",
        default_events=profile.max_events,
    )
    add_identity_record(world, subject_id, subject_revision)
    world.runtime_state["evidence"].update(
        {
            f"evidence:shadow:history:{subject_id}": {
                "active": True,
                "entity_id": subject_id,
                "state_revision": subject_revision,
                "kind": "HistorySnapshot",
                "snapshot_revision": str(
                    world.runtime_state.get("history_revision", "")
                ),
                "revision": "1",
            },
            f"evidence:shadow:evidence:{subject_id}": {
                "active": True,
                "entity_id": subject_id,
                "state_revision": subject_revision,
                "kind": "EvidenceSnapshot",
                "snapshot_revision": str(
                    world.runtime_state.get("evidence_revision", "")
                ),
                "revision": "1",
            },
        }
    )

    registered_models = bundle.get("registry_extensions", {}).get(
        "evidence_fusion_models", []
    )
    registered_model = next(
        (
            item
            for item in registered_models
            if item.get("model_id") == "evidence.snapshot-fusion"
        ),
        None,
    )
    if registered_model is None:
        raise ValueError("evidence.snapshot-fusion model registration is absent")
    requested_model = parameters["evidence_fusion_model"]

    values = [
        {
            "value_id": "subject_hint",
            "kind": "reference_hint",
            "handle_id": subject_id,
            "revision": subject_revision,
        },
        {
            "value_id": "fusion_model",
            **_record(
                "EvidenceFusionModel",
                model_id=str(requested_model["model_id"]),
                revision=str(requested_model["revision"]),
                confidence_is_truth=bool(
                    registered_model.get("confidence_is_truth", False)
                ),
            ),
        },
        {
            "value_id": "ranking",
            **_ranking_sequence(list(parameters["ranking"])),
        },
        {
            "value_id": "policy",
            **_record(
                "EvidenceFusionPolicy",
                winner_confidence=float(parameters["winner_confidence"]),
                confidence_threshold=float(parameters["confidence_threshold"]),
                minimum_evidence_count=int(parameters["minimum_evidence_count"]),
                conflicting_identity=bool(
                    parameters.get("conflicting_identity", False)
                ),
                display_requested=bool(parameters["display_requested"]),
                display_energy_j=float(parameters["display_energy_j"]),
                observation_energy_j=float(parameters["observation_energy_j"]),
            ),
        },
        {
            "value_id": "current_measurement",
            **_record(
                "CurrentMeasurement",
                event_id=str(parameters["current_measurement_id"]),
                observer_id=str(parameters["observer_id"]),
            ),
        },
        {
            "value_id": "publication",
            **_record(
                "ArtifactPublication",
                artifact_id=str(parameters["artifact_id"]),
                event_id=str(parameters["event_id"]),
                history_revision=str(parameters["history_revision"]),
                evidence_revision=str(parameters["evidence_revision"]),
            ),
        },
    ]
    nodes = [
        {
            "node_id": "resolve_subject",
            "order": 0,
            "instruction": "ref.resolve",
            "inputs": ["subject_hint"],
            "produces": ["subject_ref"],
        },
        {
            "node_id": "fuse_evidence",
            "order": 1,
            "instruction": "evidence.observe",
            "inputs": [
                "subject_ref",
                "fusion_model",
                "ranking",
                "policy",
                "current_measurement",
                "publication",
            ],
            "produces": ["observation"],
            "contract": {
                "contract_id": "evidence.snapshot-fusion",
                "revision": "1",
            },
            "obligations": {
                "capabilities": [
                    {
                        "requirement_id": "capability.discovery",
                        "target_binding": "subject_ref",
                        "effect": "Discover",
                        "scope": "local",
                    },
                    {
                        "requirement_id": "capability.observation",
                        "target_binding": "subject_ref",
                        "effect": "Observe",
                        "scope": "local",
                    },
                    {
                        "requirement_id": "capability.privacy",
                        "target_binding": "subject_ref",
                        "effect": "PrivacyAccess",
                        "scope": "local",
                    },
                ],
                "leases": [
                    {
                        "requirement_id": "lease.snapshot",
                        "target_binding": "subject_ref",
                        "mode": "ReadSnapshot",
                        "scope": "local",
                    }
                ],
                "identities": [
                    {
                        "requirement_id": "identity.subject",
                        "target_binding": "subject_ref",
                    }
                ],
                "evidence": [
                    {
                        "requirement_id": "evidence.history",
                        "target_binding": "subject_ref",
                        "kind": "HistorySnapshot",
                    },
                    {
                        "requirement_id": "evidence.snapshot",
                        "target_binding": "subject_ref",
                        "kind": "EvidenceSnapshot",
                    },
                ],
                "accounting": [
                    {
                        "requirement_id": "accounting.observation",
                        "kind": "ObservationAccounting",
                        "target_binding": "subject_ref",
                    }
                ],
                "resources": {
                    "energy_j": 0.0,
                    "matter_kg": 0.0,
                    "events": 1,
                },
            },
        },
    ]
    program = program_envelope(
        bundle,
        program_id="program:migrated:evidence.snapshot-fusion:1",
        budget_energy=float(bundle["execution"]["energy_budget_j"]),
        budget_events=1,
        values=values,
        nodes=nodes,
        edges=[{"from": "resolve_subject", "to": "fuse_evidence"}],
        outputs=[
            {
                "name": "observation",
                "binding": "observation",
                "kind": "evidence",
            },
            {
                "name": "artifact",
                "binding": "observation",
                "kind": "artifact",
            },
            {
                "name": "event",
                "binding": "observation",
                "kind": "event",
            },
        ],
    )
    semantic = evidence_fusion_semantic_registry()
    runtime_contracts = ProgramRuntimeContractRegistry(
        (
            RuntimeContractRegistration(
                "evidence.snapshot-fusion",
                "1",
                "evidence.observe",
                (
                    "reference",
                    "record:EvidenceFusionModel",
                    "sequence:record:HypothesisScore",
                    "record:EvidenceFusionPolicy",
                    "record:CurrentMeasurement",
                    "record:ArtifactPublication",
                ),
                "evidence",
                1,
                evidence_fusion_executor,
            ),
        )
    )
    evaluator = MagicalProgramEvaluator(contracts=semantic)
    runtime = MagicalProgramRuntime(
        evaluator=evaluator,
        contracts=runtime_contracts,
        profile=profile,
    )
    return ShadowTranslation(
        program,
        world,
        evaluator,
        runtime,
        "implemented",
        bundle_contract_pair(bundle),
    )


def evidence_fusion_projection(
    configuration: Mapping[str, Any],
    *,
    artifact_id: str,
    event_id: str,
) -> _JSON:
    artifacts = (
        configuration.get("Omega", {})
        .get("evidence_store", {})
        .get("artifacts", {})
    )
    event = next(
        (
            copy.deepcopy(item)
            for item in configuration.get("H", [])
            if item.get("event_id") == event_id
        ),
        None,
    )
    return {
        "world_revision": configuration.get("Sigma", {}).get("revision"),
        "artifact": copy.deepcopy(artifacts.get(artifact_id)),
        "event": event,
    }


__all__ = [
    "evidence_fusion_executor",
    "evidence_fusion_projection",
    "evidence_fusion_semantic_registry",
    "translate_evidence_fusion",
]
