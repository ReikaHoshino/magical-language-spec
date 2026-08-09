"""Shared report construction for registered experimental semantics."""
from __future__ import annotations

import copy
from typing import Any

from tools.semantic_fingerprint import semantic_fingerprint_v1
from src.evaluator.schema import validate_feasibility_report


def _assessment(dimension: str, status: str, summary: str, *, evidence_ids: list[str] | None = None, diagnostic_ids: list[str] | None = None) -> dict[str, Any]:
    return {
        "dimension": dimension,
        "status": status,
        "summary": summary,
        "evidence_ids": evidence_ids or [],
        "diagnostic_ids": diagnostic_ids or [],
    }


def build_report(bundle: dict[str, Any], *, status: str = "Feasible", diagnostic_code: str | None = None) -> dict[str, Any]:
    """Build a schema-valid report without publishing a stable intermediate IR."""

    nsr = copy.deepcopy(bundle["ingress"]["payload"])
    nsr["semantic_fingerprint"] = semantic_fingerprint_v1(nsr)
    required = bundle["execution"]["required_evidence"]
    semantic = bundle["semantic_contract"]
    runtime = bundle.get("runtime_contract")
    evidence_ids = list(dict.fromkeys([
        *required["resolution"], *required["capabilities"],
        *required["leases"], *required["accounting"],
    ]))
    diagnostics: list[dict[str, Any]] = []
    diagnostic_ids: list[str] = []
    if diagnostic_code:
        diagnostic_id = f"diag:001:{diagnostic_code}"
        diagnostic_ids.append(diagnostic_id)
        diagnostics.append({
            "id": diagnostic_id,
            "stage": "ELABORATE",
            "code": diagnostic_code,
            "severity": "fatal" if status == "Infeasible" else "unknown",
            "message": "Declared experimental contract is not executable in this implementation.",
            "evidence_ids": evidence_ids,
        })
    assessment_status = "Pass" if status == "Feasible" else "Fail" if status == "Infeasible" else "Unknown"
    report = {
        "schema_version": "1",
        "spec_version": "0.7.3",
        "status": status,
        "input": {"kind": "StructuredInput", "hash": None},
        "provenance": {
            "adapter_id": None,
            "adapter_revision": None,
            "normalizer_provider": "SpellInstanceBundle",
            "ambiguity_policy": None,
            "semantic_fingerprint": nsr["semantic_fingerprint"],
            "registry_hash": None,
            "world_index_revision": bundle["world_index"]["world_index_revision"],
            "source_world_revision": bundle["world_index"]["source_world_revision"],
            "runtime_profile": f"{bundle['profiles']['runtime']['artifact_id']}@{bundle['profiles']['runtime']['revision']}",
            "created_at": None,
        },
        "interpretations": {
            "nsr": nsr,
            "semantic_ast": {
                "node_kind": "RegisteredSemanticEffect",
                "contract": copy.deepcopy(semantic),
                "scenario_kind": bundle["scenario_kind"],
            },
            "typed_mir": {
                "node_kind": "TypedRegisteredSemanticEffect",
                "contract": copy.deepcopy(semantic),
                "typed_parameters": copy.deepcopy(bundle["execution"]["parameters"]),
                "public_serialized_ecir": False,
            },
            "kernel_plan": {
                "plan_kind": "RegisteredExperimentalPlan",
                "source_plan_id": f"contract:{semantic['contract_id']}@{semantic['revision']}",
                "operations": copy.deepcopy(bundle["execution"]["operations"]),
                "revalidation_required": True,
                "runtime_profile": copy.deepcopy(bundle["profiles"]["runtime"]),
                "runtime_contract": copy.deepcopy(runtime),
                "capability_ids": copy.deepcopy(required["capabilities"]),
                "lease_ids": copy.deepcopy(required["leases"]),
                "accounting_evidence_ids": copy.deepcopy(required["accounting"]),
                "resolution_evidence_ids": copy.deepcopy(required["resolution"]),
            },
        },
        "energy": {
            "total": {
                "kind": "Exact",
                "value": bundle["execution"]["energy_budget_j"],
                "unit": "J",
                "dimension": "Energy",
                "assumption_ids": [],
                "evidence_ids": required["accounting"],
            },
            "components": {},
            "display_unit": "J",
            "accounting_boundary": bundle["profiles"]["sandbox"]["artifact_id"],
        },
        "resources": [],
        "assessments": [
            _assessment("syntax", "Pass", "Embedded NSR is schema-valid."),
            _assessment("semantic_typing", assessment_status, "Versioned handler admission is fail-closed.", evidence_ids=evidence_ids, diagnostic_ids=diagnostic_ids),
            _assessment("identity", assessment_status, "Identity requires explicit evidence; metadata does not grant identity.", evidence_ids=required["resolution"]),
            _assessment("authority", assessment_status, "Capability is explicit and revalidated at COMMIT.", evidence_ids=required["capabilities"]),
            _assessment("lease", assessment_status, "Lease is explicit and revalidated at COMMIT.", evidence_ids=required["leases"]),
            _assessment("conservation", assessment_status, "Accounting evidence is explicit.", evidence_ids=required["accounting"]),
            _assessment("experimental_scope", "Pass", "Experimental ingress does not change stable conformance claims."),
        ],
        "diagnostics": diagnostics,
        "assumptions": copy.deepcopy(bundle["execution"].get("assumptions", [])),
        "evidence": [
            {"id": evidence_id, "source_kind": "SpellInstanceBundle", "source_id": bundle["instance_id"], "revision": "1", "path": None}
            for evidence_id in evidence_ids
        ],
    }
    validate_feasibility_report(report)
    return report


def feasible_handler(bundle: dict[str, Any]) -> dict[str, Any]:
    return build_report(bundle)


def unsupported_handler(bundle: dict[str, Any]) -> dict[str, Any]:
    return build_report(bundle, status="Indeterminate", diagnostic_code="UnsupportedSemanticSubset")
