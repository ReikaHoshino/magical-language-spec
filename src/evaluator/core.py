"""Deterministic v0.8 Minimal Local Evaluator.

Public v0.8 ingress is deliberately limited to:
* natural-language source through LanguageAdapter<lat>;
* schema-valid NSR (object or JSON).

SemanticAST, TypedMIR, KernelPlan, and all assessments remain internal stages.
This module is dry-run only: it contains no COMMIT or WorldState mutation path.
"""
from __future__ import annotations

import copy
import json
from typing import Any, Iterable

from tools.latin_adapter import normalize_with_adapter
from tools.semantic_fingerprint import SemanticFingerprintError, semantic_fingerprint_v1

from .fixtures import (
    ReadOnlySemanticRegistry,
    ReadOnlyWorldIndex,
    SyntheticReferenceEstimator,
    canonical_pipeline,
)
from .schema import SchemaValidationError, validate_feasibility_report, validate_nsr

MKI_PRIMITIVES = {
    "RESOLVE",
    "OBSERVE",
    "CHANNEL",
    "TRANSFER",
    "RECONFIGURE",
    "CONSTRAIN",
}
OBLIGATION_FAILURE_CODES = {
    "Type": "TypeError",
    "Identity": "ResolutionFailure",
    "Conservation": "ConservationProofFailure",
    "Authority": "AuthorityError",
    "Lease": "AuthorityError",
    "Sandbox": "SandboxViolation",
}
EXPECTED_FIELD_TYPES = {
    "mass": "Mass",
    "radius": "Length",
    "distance": "Length",
    "initial_velocity": "Velocity",
    "acceleration": "Acceleration",
}
EXPECTED_DIMENSIONS: dict[str, dict[str, int]] = {
    "Mass": {"kg": 1, "m": 0, "s": 0, "A": 0, "K": 0, "mol": 0, "cd": 0},
    "Length": {"kg": 0, "m": 1, "s": 0, "A": 0, "K": 0, "mol": 0, "cd": 0},
    "Velocity": {"kg": 0, "m": 1, "s": -1, "A": 0, "K": 0, "mol": 0, "cd": 0},
    "Acceleration": {"kg": 0, "m": 1, "s": -2, "A": 0, "K": 0, "mol": 0, "cd": 0},
    "Energy": {"kg": 1, "m": 2, "s": -2, "A": 0, "K": 0, "mol": 0, "cd": 0},
    "Time": {"kg": 0, "m": 0, "s": 1, "A": 0, "K": 0, "mol": 0, "cd": 0},
}


def _copy(value: Any) -> Any:
    return copy.deepcopy(value)


class _Diagnostics:
    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []

    def add(
        self,
        stage: str,
        code: str,
        severity: str,
        message: str | None = None,
        evidence_ids: Iterable[str] = (),
    ) -> str:
        diagnostic_id = f"diag:{len(self.items) + 1:03d}:{code}"
        item: dict[str, Any] = {
            "id": diagnostic_id,
            "stage": stage,
            "code": code,
            "severity": severity,
            "evidence_ids": list(evidence_ids),
        }
        if message is not None:
            item["message"] = message
        self.items.append(item)
        return diagnostic_id


def _assessment(
    dimension: str,
    status: str,
    summary: str,
    *,
    diagnostic_ids: Iterable[str] = (),
    evidence_ids: Iterable[str] = (),
) -> dict[str, Any]:
    return {
        "dimension": dimension,
        "status": status,
        "summary": summary,
        "diagnostic_ids": list(diagnostic_ids),
        "evidence_ids": list(evidence_ids),
    }


def _overall_status(assessments: list[dict[str, Any]]) -> str:
    statuses = {assessment["status"] for assessment in assessments}
    if "Fail" in statuses:
        return "Infeasible"
    if "Unknown" in statuses:
        return "Indeterminate"
    if "Conditional" in statuses:
        return "ConditionallyFeasible"
    return "Feasible"


def _role_map(nsr: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(entry.get("role")): entry.get("value", {})
        for entry in nsr.get("roles", [])
        if isinstance(entry, dict)
    }


def _unknown_energy(reason: str) -> dict[str, Any]:
    return {
        "total": {
            "kind": "Unknown",
            "reason": reason,
            "unit": "J",
            "dimension": "Energy",
            "assumption_ids": [],
            "evidence_ids": [],
        },
        "components": {},
        "display_unit": "J",
        "accounting_boundary": None,
    }


class LocalEvaluator:
    """Reference evaluator for the frozen Issue #36 v0.8 subset."""

    def __init__(
        self,
        *,
        registry: ReadOnlySemanticRegistry | None = None,
        world_index: ReadOnlyWorldIndex | None = None,
        estimator: SyntheticReferenceEstimator | None = None,
    ) -> None:
        self.registry = registry or ReadOnlySemanticRegistry()
        self.world_index = world_index or ReadOnlyWorldIndex()
        self.estimator = estimator or SyntheticReferenceEstimator()
        self.water_ball = canonical_pipeline()
        self.canonical_fingerprint = semantic_fingerprint_v1(
            self.water_ball["normalization"]["nsr"]
        )
        self._semantic_handlers = {
            ("GenerationCommand", "generate"): self._evaluate_generation,
            ("TransferCommand", "transfer"): self._evaluate_transfer,
        }

    # Public v0.8 ingress 1/2.
    def evaluate_latin_source(
        self,
        source: str | bytes,
        *,
        ambiguity_policy: str = "StrictReject",
    ) -> dict[str, Any]:
        """Evaluate source only through the explicit reference Latin adapter."""
        frontend = normalize_with_adapter(
            "lat",
            source,
            ambiguity_policy=ambiguity_policy,
        )
        candidate_set = frontend["normalization_candidate_set"]
        selected_id = candidate_set.get("selected_candidate_id")
        selected = next(
            (
                candidate
                for candidate in candidate_set.get("candidates", [])
                if candidate.get("candidate_id") == selected_id
            ),
            None,
        )
        input_record = {
            "kind": "NaturalLanguageSource",
            "adapter_id": "lat",
            "external_language_tags": ["lat"],
            "hash": None,
            "frontend_revision": frontend.get("adapter", {}).get("adapter_revision"),
        }
        provenance = {
            "adapter_id": "lat",
            "adapter_revision": frontend.get("adapter", {}).get("adapter_revision"),
            "normalizer_provider": "LexiconDriven",
            "ambiguity_policy": ambiguity_policy,
            "semantic_fingerprint": None,
            "registry_hash": self.registry.registry_hash,
            "world_index_revision": self.world_index.world_index_revision,
            "source_world_revision": self.world_index.source_world_revision,
            "runtime_profile": None,
            "created_at": None,
        }
        if selected is None or not isinstance(selected.get("nsr"), dict):
            return self._frontend_failure(input_record, provenance, frontend)
        return self._evaluate_nsr(
            selected["nsr"],
            input_record=input_record,
            frontend=frontend,
            provenance_seed=provenance,
        )

    # Public v0.8 ingress 2/2.
    def evaluate_nsr(self, nsr: Any) -> dict[str, Any]:
        """Evaluate an already structured NSR object."""
        return self._evaluate_nsr(
            nsr,
            input_record={
                "kind": "NSR",
                "adapter_id": None,
                "external_language_tags": [],
                "hash": None,
                "frontend_revision": None,
            },
            frontend=None,
            provenance_seed=None,
        )

    def evaluate_nsr_json(self, payload: str | bytes) -> dict[str, Any]:
        """Decode JSON and enter only through the public NSR boundary."""
        try:
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            value = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            diagnostics = _Diagnostics()
            diagnostic_id = diagnostics.add("INGRESS", "InvalidJSON", "fatal", str(error))
            return self._finalize(
                {
                    "schema_version": "1",
                    "spec_version": "0.7.3",
                    "status": "Infeasible",
                    "input": {
                        "kind": "NSR",
                        "adapter_id": None,
                        "external_language_tags": [],
                        "hash": None,
                        "frontend_revision": None,
                    },
                    "assessments": [
                        _assessment(
                            "syntax",
                            "Fail",
                            "Input is not valid NSR JSON.",
                            diagnostic_ids=[diagnostic_id],
                        )
                    ],
                    "diagnostics": diagnostics.items,
                    "assumptions": [],
                    "evidence": [],
                }
            )
        return self.evaluate_nsr(value)

    def _frontend_failure(
        self,
        input_record: dict[str, Any],
        provenance: dict[str, Any],
        frontend: dict[str, Any],
    ) -> dict[str, Any]:
        diagnostics = _Diagnostics()
        diagnostic_ids: list[str] = []
        for entry in frontend.get("diagnostics", []):
            severity = entry.get("severity", "unknown")
            if severity not in {"info", "warning", "conditional", "fatal", "unknown"}:
                severity = "unknown"
            diagnostic_ids.append(
                diagnostics.add(
                    "NORMALIZE",
                    str(entry.get("code", "NormalizationFailed")),
                    severity,
                    entry.get("message"),
                    entry.get("evidence_ids", []),
                )
            )
        candidate_set = frontend.get("normalization_candidate_set", {})
        conditional = candidate_set.get("decision_status") == "PendingInteraction"
        report = {
            "schema_version": "1",
            "spec_version": "0.7.3",
            "status": "Indeterminate" if conditional else "Infeasible",
            "input": _copy(input_record),
            "provenance": _copy(provenance),
            "interpretations": {
                "surface": _copy(frontend.get("source_normalization")),
                "normalization_candidates": _copy(candidate_set.get("candidates", [])),
                "normalization_decision": {
                    "policy": candidate_set.get("policy"),
                    "status": candidate_set.get("decision_status"),
                    "selected_candidate_id": candidate_set.get("selected_candidate_id"),
                },
            },
            "assessments": [
                _assessment(
                    "normalization",
                    "Conditional" if conditional else "Fail",
                    "Latin normalization did not produce one selected NSR.",
                    diagnostic_ids=diagnostic_ids,
                )
            ],
            "diagnostics": diagnostics.items,
            "assumptions": [],
            "evidence": [],
        }
        return self._finalize(report)

    def _base_report(
        self,
        input_record: dict[str, Any],
        nsr: dict[str, Any],
        diagnostics: _Diagnostics,
        *,
        frontend: dict[str, Any] | None,
        provenance_seed: dict[str, Any] | None,
    ) -> dict[str, Any]:
        provenance = _copy(provenance_seed) if provenance_seed is not None else {
            "adapter_id": nsr.get("provenance", {}).get("adapter_id"),
            "adapter_revision": nsr.get("provenance", {}).get("adapter_revision"),
            "normalizer_provider": nsr.get("provenance", {}).get("provider"),
            "ambiguity_policy": nsr.get("ambiguity", {}).get("policy"),
            "semantic_fingerprint": nsr.get("semantic_fingerprint"),
            "registry_hash": self.registry.registry_hash,
            "world_index_revision": self.world_index.world_index_revision,
            "source_world_revision": self.world_index.source_world_revision,
            "runtime_profile": None,
            "created_at": None,
        }
        provenance["semantic_fingerprint"] = nsr.get("semantic_fingerprint")
        interpretations: dict[str, Any] = {"nsr": _copy(nsr)}
        if frontend is not None:
            candidate_set = frontend.get("normalization_candidate_set", {})
            interpretations.update(
                {
                    "surface": _copy(frontend.get("source_normalization")),
                    "normalization_candidates": _copy(candidate_set.get("candidates", [])),
                    "normalization_decision": {
                        "policy": candidate_set.get("policy"),
                        "status": candidate_set.get("decision_status"),
                        "selected_candidate_id": candidate_set.get("selected_candidate_id"),
                    },
                }
            )
        return {
            "schema_version": "1",
            "spec_version": "0.7.3",
            "status": "Indeterminate",
            "input": _copy(input_record),
            "provenance": provenance,
            "interpretations": interpretations,
            "assessments": [],
            "diagnostics": diagnostics.items,
            "assumptions": [],
            "evidence": [],
        }

    def _finalize(self, report: dict[str, Any]) -> dict[str, Any]:
        validate_feasibility_report(report)
        return report

    def _evaluate_nsr(
        self,
        nsr: Any,
        *,
        input_record: dict[str, Any],
        frontend: dict[str, Any] | None,
        provenance_seed: dict[str, Any] | None,
    ) -> dict[str, Any]:
        diagnostics = _Diagnostics()
        try:
            validate_nsr(nsr)
        except SchemaValidationError as error:
            diagnostic_ids = [
                diagnostics.add("NSR_VALIDATE", "NSRSchemaViolation", "fatal", message)
                for message in error.errors
            ]
            return self._finalize(
                {
                    "schema_version": "1",
                    "spec_version": "0.7.3",
                    "status": "Infeasible",
                    "input": _copy(input_record),
                    "assessments": [
                        _assessment(
                            "syntax",
                            "Fail",
                            "NSR does not satisfy the normative schema.",
                            diagnostic_ids=diagnostic_ids,
                        )
                    ],
                    "diagnostics": diagnostics.items,
                    "assumptions": [],
                    "evidence": [],
                }
            )

        working = _copy(nsr)
        provided = working.get("semantic_fingerprint")
        try:
            computed = semantic_fingerprint_v1(working)
        except SemanticFingerprintError as error:
            diagnostic_id = diagnostics.add(
                "NSR_VALIDATE", "SemanticFingerprintError", "fatal", str(error)
            )
            report = self._base_report(
                input_record,
                working,
                diagnostics,
                frontend=frontend,
                provenance_seed=provenance_seed,
            )
            report["status"] = "Infeasible"
            report["assessments"] = [
                _assessment(
                    "source_fidelity",
                    "Fail",
                    "SemanticFingerprintV1 projection failed.",
                    diagnostic_ids=[diagnostic_id],
                )
            ]
            return self._finalize(report)

        if provided is not None and provided != computed:
            diagnostic_id = diagnostics.add(
                "NSR_VALIDATE",
                "SemanticFingerprintMismatch",
                "fatal",
                "Provided SemanticFingerprintV1 does not match the current NSR semantic projection.",
            )
            report = self._base_report(
                input_record,
                working,
                diagnostics,
                frontend=frontend,
                provenance_seed=provenance_seed,
            )
            report["status"] = "Infeasible"
            report["assessments"] = [
                _assessment(
                    "source_fidelity",
                    "Fail",
                    "Semantic fingerprint mismatch prevents deterministic evaluation.",
                    diagnostic_ids=[diagnostic_id],
                )
            ]
            return self._finalize(report)

        working["semantic_fingerprint"] = computed
        handler = self._semantic_handlers.get((working.get("kind"), working.get("action")))
        if handler is not None:
            return handler(
                working,
                input_record,
                frontend,
                provenance_seed,
                diagnostics,
            )

        diagnostic_id = diagnostics.add(
            "ELABORATE",
            "UnsupportedSemanticSubset",
            "unknown",
            "Schema-valid NSR is outside the implemented v0.8 semantic subset.",
        )
        report = self._base_report(
            input_record,
            working,
            diagnostics,
            frontend=frontend,
            provenance_seed=provenance_seed,
        )
        report["assessments"] = [
            _assessment("syntax", "Pass", "NSR is schema-valid."),
            _assessment(
                "semantic_typing",
                "Unknown",
                "The evaluator does not invent semantics for unsupported NSR kinds.",
                diagnostic_ids=[diagnostic_id],
            ),
        ]
        report["status"] = "Indeterminate"
        return self._finalize(report)

    def _evaluate_generation(
        self,
        nsr: dict[str, Any],
        input_record: dict[str, Any],
        frontend: dict[str, Any] | None,
        provenance_seed: dict[str, Any] | None,
        diagnostics: _Diagnostics,
    ) -> dict[str, Any]:
        semantic_ast, typed_mir, validation_ids = self._elaborate_generation(nsr, diagnostics)
        report = self._base_report(
            input_record,
            nsr,
            diagnostics,
            frontend=frontend,
            provenance_seed=provenance_seed,
        )
        if semantic_ast is not None:
            report["interpretations"]["semantic_ast"] = semantic_ast
        if typed_mir is not None:
            report["interpretations"]["typed_mir"] = typed_mir
        if validation_ids:
            report["assessments"] = [
                _assessment("syntax", "Pass", "NSR is schema-valid."),
                _assessment(
                    "semantic_typing",
                    "Fail",
                    "Generation subset type/dimension elaboration failed.",
                    diagnostic_ids=validation_ids,
                ),
            ]
            report["status"] = "Infeasible"
            return self._finalize(report)

        if nsr["semantic_fingerprint"] != self.canonical_fingerprint:
            diagnostic_id = diagnostics.add(
                "ELABORATE",
                "UnsupportedSemanticSubset",
                "unknown",
                "v0.8 implements GenerationCommand only for the WB-CANON-001 semantic subset.",
            )
            report["assessments"] = [
                _assessment("syntax", "Pass", "NSR is schema-valid."),
                _assessment(
                    "semantic_typing",
                    "Unknown",
                    "Generation structure is typed, but the semantic instance is outside the canonical v0.8 subset.",
                    diagnostic_ids=[diagnostic_id],
                ),
            ]
            report["status"] = "Indeterminate"
            return self._finalize(report)

        return self._complete_water_ball(report, nsr, semantic_ast, typed_mir, diagnostics)

    def _elaborate_generation(
        self,
        nsr: dict[str, Any],
        diagnostics: _Diagnostics,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str]]:
        roles = _role_map(nsr)
        patient = roles.get("Patient", {})
        goal = roles.get("Goal", {})
        acceleration = roles.get("Quantity", {})
        trajectory = roles.get("ConstraintSubject", {})
        diagnostic_ids: list[str] = []

        if patient.get("kind") != "SemanticKind" or patient.get("semantic_kind") != "MatterPayload":
            diagnostic_ids.append(
                diagnostics.add(
                    "ELABORATE",
                    "TypeError",
                    "fatal",
                    "Generation Patient must be a MatterPayload semantic value.",
                )
            )
            return None, None, diagnostic_ids
        if goal.get("semantic_kind") != "RelativeLocation":
            diagnostic_ids.append(
                diagnostics.add(
                    "ELABORATE",
                    "TypeError",
                    "fatal",
                    "Generation Goal must be a RelativeLocation.",
                )
            )
        if acceleration.get("semantic_kind") != "Acceleration":
            diagnostic_ids.append(
                diagnostics.add(
                    "ELABORATE",
                    "TypeError",
                    "fatal",
                    "Generation Quantity must carry Acceleration in the supported subset.",
                )
            )

        payload = patient.get("value", {})
        goal_payload = goal.get("value", {})
        typed_constraints: dict[str, Any] = {
            "material": payload.get("material"),
            "mass": _copy(payload.get("mass")),
            "radius": _copy(payload.get("radius")),
            "distance": _copy(goal_payload.get("distance")) if isinstance(goal_payload, dict) else None,
            "acceleration": _copy(acceleration.get("value")),
            "trajectory": trajectory.get("value"),
        }
        initial_velocity: Any = None
        terminal: dict[str, Any] | None = None
        for constraint in nsr.get("constraints", []):
            if constraint.get("semantic_kind") == "InitialVelocity":
                initial_velocity = _copy(constraint.get("value"))
            if constraint.get("semantic_kind") == "MotionTerminal" or (
                constraint.get("kind") == "Unknown" and constraint.get("reason") == "MissingArgument"
            ):
                terminal = _copy(constraint)
        typed_constraints["initial_velocity"] = initial_velocity

        for field_name, expected_type in EXPECTED_FIELD_TYPES.items():
            value = typed_constraints.get(field_name)
            if not isinstance(value, dict) or not isinstance(value.get("semantic_type"), str):
                diagnostic_ids.append(
                    diagnostics.add(
                        "ELABORATE",
                        "TypeError",
                        "fatal",
                        f"{field_name} is missing a typed quantity.",
                    )
                )
                continue
            if value["semantic_type"] != expected_type:
                diagnostic_ids.append(
                    diagnostics.add(
                        "ELABORATE",
                        "TypeError",
                        "fatal",
                        f"{field_name} has semantic type {value['semantic_type']!r}; expected {expected_type!r}.",
                    )
                )
            expected_dimension = EXPECTED_DIMENSIONS[expected_type]
            if value.get("dimension") != expected_dimension:
                diagnostic_ids.append(
                    diagnostics.add(
                        "ELABORATE",
                        "DimensionError",
                        "fatal",
                        f"{field_name} has dimension {value.get('dimension')!r}; expected {expected_dimension!r}.",
                    )
                )

        semantic_ast = _copy(self.water_ball["semantic_ast"])
        semantic_ast["constraints"] = {
            "mass": self._ast_quantity(typed_constraints.get("mass")),
            "radius": self._ast_quantity(typed_constraints.get("radius")),
            "distance": self._ast_quantity(typed_constraints.get("distance")),
            "initial_velocity": self._ast_quantity(typed_constraints.get("initial_velocity")),
            "acceleration": self._ast_quantity(typed_constraints.get("acceleration")),
            "trajectory": typed_constraints.get("trajectory"),
        }
        semantic_ast["desired_state"]["material"] = typed_constraints.get("material")
        semantic_ast["unknowns"] = [
            {"field_path": item.get("field"), "reason": item.get("reason")}
            for item in nsr.get("unknowns", [])
        ]

        typed_mir = _copy(self.water_ball["typed_mir"])
        typed_mir["typed_constraints"] = typed_constraints
        criticality = typed_mir.get("terminal", {}).get("criticality", "MustResolve")
        typed_mir["terminal"] = {
            "source_value": terminal or {"kind": "Unknown", "reason": "MissingArgument"},
            "criticality": criticality,
        }
        return semantic_ast, typed_mir, diagnostic_ids

    @staticmethod
    def _ast_quantity(value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        return {
            "semantic_type": value.get("semantic_type"),
            "value": value.get("value"),
            "unit": value.get("unit"),
        }

    def _complete_water_ball(
        self,
        report: dict[str, Any],
        nsr: dict[str, Any],
        semantic_ast: dict[str, Any],
        typed_mir: dict[str, Any],
        diagnostics: _Diagnostics,
    ) -> dict[str, Any]:
        planning = self.water_ball["planning"]
        selected_plan, plan_diagnostic_ids = self._select_plan(
            planning["candidate_plans"],
            diagnostics,
        )
        if selected_plan is None:
            fatal_ids = {
                item["id"]
                for item in diagnostics.items
                if item["severity"] == "fatal"
            }
            hard_failure = any(diagnostic_id in fatal_ids for diagnostic_id in plan_diagnostic_ids)
            report["assessments"] = [
                _assessment(
                    "planning",
                    "Fail" if hard_failure else "Unknown",
                    "No generation candidate passed the frozen selection order.",
                    diagnostic_ids=plan_diagnostic_ids,
                )
            ]
            report["status"] = "Infeasible" if hard_failure else "Indeterminate"
            return self._finalize(report)

        kernel_plan = _copy(self.water_ball["kernel_plan"])
        kernel_plan["source_plan_id"] = selected_plan["plan_id"]
        invalid_ops = [
            operation
            for operation in kernel_plan.get("operations", [])
            if operation not in MKI_PRIMITIVES
        ]
        if invalid_ops:
            diagnostic_id = diagnostics.add(
                "PLAN",
                "InvalidMKIPrimitive",
                "fatal",
                f"KernelPlan contains non-MKI operation(s): {invalid_ops!r}.",
            )
            report["assessments"] = [
                _assessment(
                    "planning",
                    "Fail",
                    "KernelPlan must use only the six MKI data-plane primitives.",
                    diagnostic_ids=[diagnostic_id],
                )
            ]
            report["status"] = "Infeasible"
            return self._finalize(report)

        terminal_assumption = planning["terminal_assumption"]
        source_terminal = typed_mir["terminal"]["source_value"]
        assumptions: list[dict[str, Any]] = []
        if (
            source_terminal.get("kind") == "Unknown"
            and typed_mir["terminal"].get("criticality") == "EstimateAllowed"
            and terminal_assumption.get("binding", {}).get("mode") == "PrepareBound"
        ):
            assumptions.append(
                {
                    "id": terminal_assumption["planning_assumption_id"],
                    "statement": "Use a 50 m fixture horizon without rewriting the source Unknown.",
                    "definition_source": "Profile",
                    "impact": "PrepareBound terminal",
                    "source_value": _copy(source_terminal),
                    "selected_value": _copy(terminal_assumption["estimate"]["value"]),
                    "binding": _copy(terminal_assumption["binding"]),
                    "evidence_ids": list(terminal_assumption["estimate"].get("evidence_ids", [])),
                }
            )
        else:
            diagnostic_id = diagnostics.add(
                "PLANNING",
                "InferenceForbidden",
                "fatal",
                "Terminal adoption violates the frozen Unknown/criticality/binding boundary.",
            )
            report["assessments"] = [
                _assessment(
                    "planning_inference",
                    "Fail",
                    "Planning inference attempted to weaken a mandatory boundary.",
                    diagnostic_ids=[diagnostic_id],
                )
            ]
            report["status"] = "Infeasible"
            return self._finalize(report)

        energy, resources, timing = self.estimator.evaluate()
        estimator_diagnostic_ids: list[str] = []
        if energy.get("total", {}).get("kind") == "Unknown":
            estimator_diagnostic_ids.append(
                diagnostics.add(
                    "PREPARE",
                    "EstimatorModelUnavailable",
                    "unknown",
                    "Required Energy estimator output is unavailable; Unknown is not treated as zero.",
                    evidence_ids=[self.estimator.identity],
                )
            )
        resolution = self.water_ball["resolution_inputs"]
        obligations = {
            item["kind"]: item
            for item in selected_plan.get("mandatory_obligations", [])
        }
        checks = {
            "Type": obligations.get("Type", {}).get("status") == "Verified",
            "Identity": obligations.get("Identity", {}).get("status") == "Verified",
            "Conservation": obligations.get("Conservation", {}).get("status") == "Verified",
            "Authority": obligations.get("Authority", {}).get("status") == "Verified",
            "Lease": obligations.get("Lease", {}).get("status") == "Reserved",
        }

        report["interpretations"]["semantic_ast"] = semantic_ast
        report["interpretations"]["typed_mir"] = typed_mir
        report["interpretations"]["kernel_plan"] = kernel_plan
        report["provenance"].update(
            {
                "adapter_id": nsr.get("provenance", {}).get("adapter_id"),
                "adapter_revision": nsr.get("provenance", {}).get("adapter_revision"),
                "normalizer_provider": nsr.get("provenance", {}).get("provider"),
                "ambiguity_policy": nsr.get("ambiguity", {}).get("policy"),
                "semantic_fingerprint": nsr["semantic_fingerprint"],
                "registry_hash": None,
                "world_index_revision": resolution["world_index_revision"],
                "source_world_revision": resolution["source_world_revision"],
                "runtime_profile": "runtime-profile:reference-fixture@1",
                "created_at": None,
            }
        )
        report["energy"] = energy
        report["resources"] = resources
        report["assumptions"] = assumptions
        report["evidence"] = [
            {
                "id": self.estimator.identity,
                "source_kind": "Profile",
                "source_id": "estimator-profile:synthetic-reference",
                "revision": "1",
                "path": "examples/estimator-profiles/synthetic-reference-v1.json",
            },
            {
                "id": "wb:resolution-inputs:1",
                "source_kind": "CanonicalFixture",
                "source_id": "WB-CANON-001",
                "revision": "1",
                "path": "examples/canonical-water-ball/pipeline.json",
            },
            {
                "id": "planning:pathological-water-ball:prepare-bound",
                "source_kind": "Fixture",
                "source_id": "fixture:pathological-water-ball:prepare-bound",
                "revision": "1",
                "path": "examples/planning-inference/pathological-water-ball-bound.json",
            },
        ]
        control_estimate = energy.get("components", {}).get("control", {})
        trajectory_control_ok = (
            "CONSTRAIN" in kernel_plan.get("operations", [])
            and control_estimate.get("kind") == "Exact"
        )
        report["assessments"] = [
            _assessment("syntax", "Pass", "NSR is schema-valid."),
            _assessment(
                "source_fidelity",
                "Pass",
                "WB-CANON-001 semantic fingerprint preserves its explicit source constraints.",
            ),
            _assessment(
                "semantic_typing",
                "Pass" if checks["Type"] else "Fail",
                "SemanticAST and TypedMIR remain separate and all required SI dimensions validate.",
            ),
            _assessment(
                "resolution",
                "Pass" if checks["Identity"] else "Unknown",
                "Canonical revisioned resolution evidence is consumed read-only and is not lexical inference.",
                evidence_ids=kernel_plan.get("resolution_evidence_ids", []),
            ),
            _assessment(
                "registry",
                "Pass",
                "Canonical resolution input names a revisioned SemanticRegistry boundary.",
                evidence_ids=["wb:resolution-inputs:1"],
            ),
            _assessment(
                "energy",
                "Pass" if energy["total"].get("kind") == "Exact" else "Unknown",
                "SyntheticReference estimator evaluates profile-owned coefficients; missing models are never zero.",
                diagnostic_ids=estimator_diagnostic_ids,
                evidence_ids=[self.estimator.identity],
            ),
            _assessment(
                "resource",
                "Pass" if resources else "Unknown",
                "Resource estimation remains distinct from mandatory proof.",
                diagnostic_ids=estimator_diagnostic_ids if not resources else [],
                evidence_ids=[self.estimator.identity],
            ),
            _assessment("timing", "Pass", timing, evidence_ids=[self.estimator.identity]),
            _assessment(
                "authority",
                "Pass" if checks["Authority"] else "Fail",
                "Capability is satisfied only by canonical authoritative evidence.",
                evidence_ids=[resolution["authority_evidence"]] if checks["Authority"] else [],
            ),
            _assessment(
                "lease",
                "Pass" if checks["Lease"] else "Fail",
                "Lease is satisfied only by explicit reservation evidence.",
                evidence_ids=[resolution["lease_evidence"]] if checks["Lease"] else [],
            ),
            _assessment(
                "conservation",
                "Pass" if checks["Conservation"] else "Fail",
                "Matter/Energy accounting uses canonical ledger evidence, not estimator output.",
                evidence_ids=[resolution["conservation_evidence"]] if checks["Conservation"] else [],
            ),
            _assessment(
                "identity",
                "Pass" if checks["Identity"] else "Unknown",
                "Resolved identity remains separate from WorldIndex visibility.",
                evidence_ids=kernel_plan.get("resolution_evidence_ids", []),
            ),
            _assessment(
                "trajectory_control",
                "Pass" if trajectory_control_ok else "Fail",
                "Horizontal trajectory lowers to CONSTRAIN and the synthetic estimator carries a separate control Energy component; gravity is not removed from the world model.",
                evidence_ids=[
                    "planning:pathological-water-ball:prepare-bound",
                    self.estimator.identity,
                ],
            ),
            _assessment(
                "planning_inference",
                "Conditional",
                "The source terminal stays Unknown while a separate bounded PrepareBound assumption is adopted.",
                evidence_ids=[terminal_assumption["planning_assumption_id"]],
            ),
        ]
        report["status"] = _overall_status(report["assessments"])
        return self._finalize(report)

    def _select_plan(
        self,
        candidates: list[dict[str, Any]],
        diagnostics: _Diagnostics,
    ) -> tuple[dict[str, Any] | None, list[str]]:
        eligible: list[tuple[float, str, dict[str, Any]]] = []
        diagnostic_ids: list[str] = []
        hard_failures: set[tuple[str, str]] = set()
        for candidate in candidates:
            plan_id = str(candidate.get("plan_id", ""))
            if candidate.get("source_fidelity") != "Pass":
                if candidate.get("source_fidelity") == "Fail":
                    hard_failures.add(
                        ("SourceSemanticDrift", f"Plan {plan_id} violates explicit source semantics.")
                    )
                continue

            obligations_ok = True
            for item in candidate.get("mandatory_obligations", []):
                status = item.get("status")
                if status in {"Verified", "Reserved"}:
                    continue
                obligations_ok = False
                if status in {"Failed", "Denied", "Missing"}:
                    kind = str(item.get("kind"))
                    code = OBLIGATION_FAILURE_CODES.get(kind, "MandatoryObligationFailure")
                    hard_failures.add(
                        (code, f"Plan {plan_id} has failed mandatory {kind} obligation.")
                    )
            if not obligations_ok:
                continue
            if candidate.get("feasibility") not in {"Feasible", "ConditionallyFeasible"}:
                continue
            operations = candidate.get("operations", [])
            if any(operation not in MKI_PRIMITIVES for operation in operations):
                hard_failures.add(
                    ("InvalidMKIPrimitive", f"Plan {plan_id} introduces a seventh primitive.")
                )
                continue
            estimate = candidate.get("estimated_total_energy", {})
            value = estimate.get("value", {})
            amount = value.get("value")
            if (
                estimate.get("kind") == "Exact"
                and value.get("semantic_type") == "Energy"
                and isinstance(amount, (int, float))
            ):
                eligible.append((float(amount), str(candidate.get("plan_id", "")), candidate))
        if not eligible:
            for code, message in sorted(hard_failures):
                diagnostic_ids.append(
                    diagnostics.add("PREPARE", code, "fatal", message)
                )
            if not diagnostic_ids:
                diagnostic_ids.append(
                    diagnostics.add(
                        "PLANNING",
                        "NoEligiblePlan",
                        "unknown",
                        "No candidate passed source fidelity, mandatory obligations, feasibility, and bounded Energy comparison.",
                    )
                )
            return None, diagnostic_ids
        eligible.sort(key=lambda item: (item[0], item[1]))
        return _copy(eligible[0][2]), diagnostic_ids

    def _evaluate_transfer(
        self,
        nsr: dict[str, Any],
        input_record: dict[str, Any],
        frontend: dict[str, Any] | None,
        provenance_seed: dict[str, Any] | None,
        diagnostics: _Diagnostics,
    ) -> dict[str, Any]:
        roles = _role_map(nsr)
        patient = roles.get("Patient", {})
        quantity = roles.get("Quantity", {})
        type_ids: list[str] = []
        if patient.get("kind") != "SemanticKind" or patient.get("semantic_kind") != "Energy":
            type_ids.append(
                diagnostics.add(
                    "ELABORATE",
                    "TypeError",
                    "fatal",
                    "The reference v0.8 transfer subset requires an Energy patient.",
                )
            )

        semantic_ast = {
            "node_kind": "TransferGoal",
            "action": "transfer",
            "roles": _copy(nsr.get("roles", [])),
            "unknowns": [
                {"field_path": item.get("field"), "reason": item.get("reason")}
                for item in nsr.get("unknowns", [])
            ],
        }
        resolutions: list[dict[str, Any]] = []
        resolution_ok = True
        for role_name in ("Source", "Goal"):
            selector = roles.get(role_name, {}).get("selector")
            if not isinstance(selector, dict) or selector.get("kind") != "Symbolic":
                resolution_ok = False
                continue
            result = self.world_index.resolve_symbolic(str(selector.get("symbol", "")))
            resolutions.append({"role": role_name, **result})
            if len(result["candidates"]) != 1:
                resolution_ok = False
        resolution_id = None
        if not resolution_ok:
            resolution_id = diagnostics.add(
                "RESOLVE",
                "ResolutionFailure",
                "unknown",
                "Reference WorldIndex does not uniquely resolve every endpoint; no Ref is fabricated.",
            )

        quantity_unknown = quantity.get("kind") == "Unknown"
        typed_mir = {
            "declaration_kind": "spell",
            "goal_kind": "Transfer",
            "typed_roles": _copy(nsr.get("roles", [])),
            "effects": ["Resolve", "Read", "Channel<Energy>", "Transfer<Energy>"],
            "quantity": _copy(quantity),
            "resolution_evidence": resolutions,
        }
        kernel_plan = {
            "operations": ["RESOLVE", "OBSERVE", "CHANNEL", "TRANSFER"],
            "selectors": [
                _copy(value.get("selector"))
                for value in (roles.get("Source", {}), roles.get("Goal", {}))
                if isinstance(value.get("selector"), dict)
            ],
            "observations": [],
            "channels": [{"semantic_kind": "Energy", "mode": patient.get("mode")}],
            "transfers": [{"semantic_kind": "Energy", "quantity": _copy(quantity)}],
            "reconfigurations": [],
            "constraints": [],
            "control_plane_requirements": ["Capability", "Lease", "ConservationRevalidation"],
            "capabilities": [],
            "leases": [],
            "accounting_obligations": ["Energy"],
            "timing_requirements": [],
            "revalidation_requirements": ["AuthoritativeIdentity", "Capability", "Lease", "Conservation"],
        }

        report = self._base_report(
            input_record,
            nsr,
            diagnostics,
            frontend=frontend,
            provenance_seed=provenance_seed,
        )
        report["interpretations"].update(
            {
                "semantic_ast": semantic_ast,
                "typed_mir": typed_mir,
                "kernel_plan": kernel_plan,
            }
        )
        report["energy"] = _unknown_energy(
            "MissingArgument" if quantity_unknown else "ModelDependent"
        )
        registry_ok = self.registry.semantic_kind("Energy") is not None
        report["assessments"] = [
            _assessment("syntax", "Pass", "NSR is schema-valid."),
            _assessment(
                "normalization",
                "Pass" if frontend is not None else "NotApplicable",
                "Latin frontend produced one selected NSR." if frontend is not None else "NSR entered directly.",
            ),
            _assessment(
                "semantic_typing",
                "Fail" if type_ids else ("Unknown" if quantity_unknown else "Pass"),
                "Energy type is known; missing Quantity remains semantic Unknown." if quantity_unknown else "Transfer subset is typed.",
                diagnostic_ids=type_ids,
            ),
            _assessment(
                "registry",
                "Pass" if registry_ok else "Unknown",
                "Energy definition is read from the reference registry; registry metadata grants no Capability.",
            ),
            _assessment(
                "resolution",
                "Pass" if resolution_ok else "Unknown",
                "WorldIndex results remain candidate evidence pending authoritative revalidation.",
                diagnostic_ids=[resolution_id] if resolution_id else [],
            ),
            _assessment(
                "energy",
                "Unknown",
                "Required numeric inputs/model context are missing; Unknown is not treated as zero.",
            ),
            _assessment("authority", "Unknown", "No Capability evidence is available."),
            _assessment("lease", "Unknown", "No Lease reservation evidence is available."),
            _assessment("conservation", "Unknown", "No authoritative conservation proof/reservation is available."),
            _assessment("identity", "Unknown", "Index candidates are not authoritative Refs."),
        ]
        report["status"] = _overall_status(report["assessments"])
        return self._finalize(report)


_DEFAULT: LocalEvaluator | None = None


def default_evaluator() -> LocalEvaluator:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = LocalEvaluator()
    return _DEFAULT


def evaluate_latin_source(
    source: str | bytes,
    *,
    ambiguity_policy: str = "StrictReject",
) -> dict[str, Any]:
    return default_evaluator().evaluate_latin_source(
        source,
        ambiguity_policy=ambiguity_policy,
    )


def evaluate_nsr(nsr: Any) -> dict[str, Any]:
    return default_evaluator().evaluate_nsr(nsr)


def evaluate_nsr_json(payload: str | bytes) -> dict[str, Any]:
    return default_evaluator().evaluate_nsr_json(payload)
