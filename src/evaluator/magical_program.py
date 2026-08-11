"""Portable MagicalProgram-0 semantic evaluator."""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Mapping, Sequence

from src.artifacts.magical_program import (
    MagicalProgramAdmissionError,
    MagicalProgramHostLimits,
    admit_program,
    decode_program,
)
from .schema import validate_feasibility_report, validator
from .magical_program_contracts import (
    MKI_OPERATIONS,
    WORLD_KERNEL_CLASSES,
    ProgramContractRegistration,
    ProgramContractRegistry,
    ProgramSemanticError,
    default_program_contract_registry,
    _error,
    _pure,
    _requirements,
    _sig,
    _typed,
)

_JSON = dict[str, Any]


def _diag(
    index: int,
    code: str,
    severity: str,
    message: str,
    *,
    node: Mapping[str, Any] | None = None,
    details: Mapping[str, Any] | None = None,
) -> _JSON:
    return {
        "id": f"diag:program:{index:03d}:{code}",
        "stage": "PROGRAM_SEMANTICS",
        "code": code,
        "severity": severity,
        "message": message,
        "evidence_ids": [],
        "program_location": {
            "node_id": None if node is None else node["node_id"],
            "order": None if node is None else node["order"],
            "path": "" if node is None else f"/nodes/{node['order']}",
        },
        **({"details": copy.deepcopy(dict(details))} if details else {}),
    }


def _assessment(
    dimension: str,
    status: str,
    summary: str,
    *,
    diagnostic_ids: Sequence[str] = (),
    evidence_ids: Sequence[str] = (),
) -> _JSON:
    return {
        "dimension": dimension,
        "status": status,
        "summary": summary,
        "diagnostic_ids": list(diagnostic_ids),
        "evidence_ids": list(evidence_ids),
    }


def _fatal(program: Mapping[str, Any] | None, diagnostic: _JSON) -> _JSON:
    report = {
        "schema_version": "1",
        "spec_version": "1.0.0-rc.1",
        "status": "Infeasible",
        "input": {
            "kind": "StructuredInput",
            "adapter_id": None,
            "external_language_tags": [],
            "hash": None,
            "frontend_revision": None,
            "artifact_kind": "MagicalProgram",
            "artifact_version": None
            if program is None
            else program.get("artifact_version"),
            "program_id": None if program is None else program.get("program_id"),
        },
        "provenance": {
            "adapter_id": None,
            "adapter_revision": None,
            "normalizer_provider": None,
            "ambiguity_policy": None,
            "semantic_fingerprint": None,
            "registry_hash": None,
            "world_index_revision": None,
            "source_world_revision": None,
            "runtime_profile": None,
            "created_at": None,
        },
        "interpretations": {"typed_mir": None, "kernel_plan": None},
        "energy": {
            "total": {
                "kind": "Unknown",
                "reason": "Program did not reach semantic evaluation.",
                "unit": "J",
                "dimension": "Energy",
                "assumption_ids": [],
                "evidence_ids": [],
            },
            "components": {},
            "display_unit": "J",
            "accounting_boundary": None,
        },
        "resources": [],
        "assessments": [
            _assessment(
                "program_semantics",
                "Fail",
                "MagicalProgram evaluation failed.",
                diagnostic_ids=[diagnostic["id"]],
            )
        ],
        "diagnostics": [diagnostic],
        "assumptions": [],
        "evidence": [],
    }
    validate_feasibility_report(report)
    return report


class MagicalProgramEvaluator:
    def __init__(
        self,
        *,
        contracts: ProgramContractRegistry | None = None,
        registry_id: str = "registry:reference-experimental",
        registry_revision: str = "1",
        profile_id: str = "profile:reference-experimental",
        profile_revision: str = "1",
        limits: MagicalProgramHostLimits = MagicalProgramHostLimits(),
    ) -> None:
        self.contracts = contracts or default_program_contract_registry()
        self.registry_id, self.registry_revision = registry_id, registry_revision
        self.profile_id, self.profile_revision = profile_id, profile_revision
        self.limits = limits
        self._schema = validator("magical-program.schema.json").schema

    def evaluate_bytes(
        self,
        payload: bytes,
        *,
        world_state: Mapping[str, Any] | None = None,
        history: Sequence[Any] | None = None,
    ) -> _JSON:
        try:
            program = decode_program(payload, limits=self.limits)
        except MagicalProgramAdmissionError as error:
            return _fatal(
                None,
                _diag(
                    1,
                    error.code,
                    "fatal",
                    str(error),
                    details={"path": error.path},
                ),
            )
        return self.evaluate_program(
            program,
            encoded_size=len(payload),
            world_state=world_state,
            history=history,
        )

    def evaluate_program(
        self,
        program: Mapping[str, Any],
        *,
        encoded_size: int = 0,
        world_state: Mapping[str, Any] | None = None,
        history: Sequence[Any] | None = None,
    ) -> _JSON:
        document = copy.deepcopy(dict(program))
        before_world, before_history = copy.deepcopy(world_state), copy.deepcopy(history)
        try:
            admission = admit_program(
                document,
                schema=self._schema,
                registered_contracts=self.contracts.admitted_pairs(),
                encoded_size=encoded_size,
                limits=self.limits,
            )
            expected = {
                "registry_id": self.registry_id,
                "registry_revision": self.registry_revision,
                "profile_id": self.profile_id,
                "profile_revision": self.profile_revision,
            }
            if document["compatibility"] != expected:
                raise ProgramSemanticError(
                    "ProgramCompatibilityMismatch",
                    "Program registry/profile binding does not match the evaluator.",
                    path="/compatibility",
                )
            report = self._evaluate(document, admission)
        except MagicalProgramAdmissionError as error:
            report = _fatal(
                document,
                _diag(
                    1,
                    error.code,
                    "fatal",
                    str(error),
                    details={"path": error.path},
                ),
            )
        except ProgramSemanticError as error:
            node = None
            if error.node_id is not None:
                node = {"node_id": error.node_id, "order": error.order}
            report = _fatal(
                document,
                _diag(
                    1,
                    error.code,
                    "fatal",
                    str(error),
                    node=node,
                    details=error.details,
                ),
            )
        if world_state != before_world or history != before_history:
            raise RuntimeError("MagicalProgram evaluation mutated WorldState or History")
        return report

    def _evaluate(self, program: _JSON, admission: _JSON) -> _JSON:
        bindings: dict[str, _JSON] = {
            item["value_id"]: _typed(item) for item in program["values"]
        }
        initial = set(bindings)
        nodes: list[_JSON] = []
        lowerings: list[_JSON] = []
        diagnostics: list[_JSON] = []
        for node in sorted(
            program["nodes"], key=lambda item: (item["order"], item["node_id"])
        ):
            values = [bindings[name] for name in node["inputs"]]
            instruction = node["instruction"]
            if instruction.startswith("pure.") or instruction == "assert.require":
                produced = _pure(node, values)
            elif instruction == "ref.resolve":
                if len(values) != 1 or _sig(values[0]) not in {
                    "selector",
                    "reference_hint",
                }:
                    raise _error(
                        node,
                        "ProgramTypeMismatch",
                        "ref.resolve requires a selector or untrusted reference hint.",
                    )
                source = values[0]
                produced = [
                    {
                        "kind": "reference",
                        "type_signature": "reference",
                        "resolution": "Required",
                        "authority_granted": False,
                        **(
                            {"selector": copy.deepcopy(source["selector"])}
                            if source["kind"] == "selector"
                            else {
                                "handle_hint": source["handle_id"],
                                "revision_hint": source["revision"],
                            }
                        ),
                    }
                ]
                lowerings.append(
                    {
                        "node_id": node["node_id"],
                        "contract": None,
                        "mki_operations": ["RESOLVE"],
                        "world_kernel_classes": ["QUERY"],
                        "obligations": {
                            "authority_granted": False,
                            "host_records_bound": False,
                            "requires_runtime_revalidation": True,
                        },
                    }
                )
                diagnostics.append(
                    _diag(
                        len(diagnostics) + 1,
                        "ProgramResolutionDeferred",
                        "conditional",
                        "Reference resolution is deferred to PREPARE.",
                        node=node,
                    )
                )
            else:
                registration = self.contracts.resolve(
                    node["contract"]["contract_id"],
                    node["contract"]["revision"],
                )
                if registration.instruction != instruction:
                    raise _error(
                        node,
                        "ProgramContractInstructionMismatch",
                        "Contract does not admit this instruction.",
                    )
                observed = tuple(_sig(value) for value in values)
                if observed != registration.input_kinds:
                    raise _error(
                        node,
                        "ProgramContractInputMismatch",
                        "Contract input signature differs.",
                        expected=list(registration.input_kinds),
                        observed=list(observed),
                    )
                obligations = _requirements(node, registration, bindings)
                produced = [
                    {
                        "kind": registration.output_kind,
                        "type_signature": registration.output_kind,
                        "status": "Planned",
                        "contract": {
                            "contract_id": registration.contract_id,
                            "revision": registration.revision,
                        },
                        "authority_granted": False,
                        "resources_reserved": False,
                    }
                ]
                lowerings.append(
                    {
                        "node_id": node["node_id"],
                        "contract": {
                            "contract_id": registration.contract_id,
                            "revision": registration.revision,
                        },
                        "mki_operations": list(registration.mki_operations),
                        "world_kernel_classes": list(
                            registration.world_kernel_classes
                        ),
                        "obligations": obligations,
                    }
                )
                diagnostics.append(
                    _diag(
                        len(diagnostics) + 1,
                        "ProgramRuntimeRevalidationRequired",
                        "conditional",
                        "Portable requirements require authoritative PREPARE/COMMIT binding.",
                        node=node,
                    )
                )
            if len(produced) != len(node["produces"]):
                raise _error(
                    node,
                    "ProgramContractOutputMismatch",
                    "Produced binding count differs.",
                )
            for name, value in zip(node["produces"], produced, strict=True):
                bindings[name] = copy.deepcopy(value)
            nodes.append(
                {
                    "node_id": node["node_id"],
                    "order": node["order"],
                    "instruction": instruction,
                    "input_bindings": list(node["inputs"]),
                    "input_types": [_sig(value) for value in values],
                    "output_bindings": list(node["produces"]),
                    "output_types": [_sig(value) for value in produced],
                    "evaluated_outputs": copy.deepcopy(produced),
                    "pure": instruction.startswith("pure.")
                    or instruction == "assert.require",
                }
            )
        outputs: dict[str, _JSON] = {}
        for output in program["outputs"]:
            value = bindings[output["binding"]]
            signature = _sig(value)
            allowed = {
                "value": (
                    signature.startswith("literal:")
                    or signature.startswith("record:")
                    or signature.startswith("sequence:")
                    or signature in {"quantity", "ranked_sequence"}
                ),
                "reference": signature == "reference",
                "evidence": signature == "evidence",
                "effect_result": signature == "effect_result",
                "event": signature in {"effect_result", "evidence"},
                "artifact": signature in {"effect_result", "evidence"},
            }[output["kind"]]
            if not allowed:
                raise ProgramSemanticError(
                    "ProgramOutputKindMismatch",
                    f"Output {output['name']!r} is incompatible with binding "
                    f"{signature!r}.",
                    path="/outputs",
                )
            outputs[output["name"]] = copy.deepcopy(value)
        evidence = self.contracts.evidence()
        evidence_ids = [item["id"] for item in evidence]
        status = "ConditionallyFeasible" if diagnostics else "Feasible"
        assessments = [
            _assessment(
                "program_admission",
                "Pass",
                "MagicalProgram structural admission passed.",
            ),
            _assessment(
                "typing",
                "Pass",
                "Bindings and portable requirements are type-compatible.",
            ),
            _assessment(
                "lowering",
                "Pass",
                "Every effect has explicit MKI/World Kernel mapping.",
                evidence_ids=evidence_ids,
            ),
            _assessment(
                "mutation_safety",
                "Pass",
                "Evaluation performed no authoritative mutation.",
            ),
            _assessment(
                "runtime_obligations",
                "Conditional" if diagnostics else "NotApplicable",
                "Authoritative resolution and host-record binding remain mandatory."
                if diagnostics
                else "The program contains no authoritative request.",
                diagnostic_ids=[item["id"] for item in diagnostics],
                evidence_ids=evidence_ids,
            ),
        ]
        encoded = json.dumps(
            program,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
        mki = sorted(
            {value for item in lowerings for value in item["mki_operations"]}
        )
        kernel = sorted(
            {
                value
                for item in lowerings
                for value in item["world_kernel_classes"]
            }
        )
        report = {
            "schema_version": "1",
            "spec_version": "1.0.0-rc.1",
            "status": status,
            "input": {
                "kind": "StructuredInput",
                "adapter_id": None,
                "external_language_tags": [],
                "hash": None,
                "frontend_revision": None,
                "artifact_kind": "MagicalProgram",
                "artifact_version": program["artifact_version"],
                "program_id": program["program_id"],
                "content_sha256": hashlib.sha256(encoded).hexdigest(),
            },
            "provenance": {
                "adapter_id": None,
                "adapter_revision": None,
                "normalizer_provider": None,
                "ambiguity_policy": None,
                "semantic_fingerprint": None,
                "registry_hash": None,
                "world_index_revision": None,
                "source_world_revision": None,
                "runtime_profile": self.profile_id,
                "created_at": None,
                "program_provenance": copy.deepcopy(program["provenance"]),
                "registry_id": self.registry_id,
                "registry_revision": self.registry_revision,
                "profile_revision": self.profile_revision,
            },
            "interpretations": {
                "typed_mir": {
                    "representation": "MagicalProgramTypedBindings-0",
                    "program_id": program["program_id"],
                    "deterministic_node_order": admission[
                        "deterministic_node_order"
                    ],
                    "initial_values": {
                        key: value for key, value in bindings.items() if key in initial
                    },
                    "nodes": nodes,
                    "outputs": outputs,
                },
                "kernel_plan": {
                    "representation": "MagicalProgramLoweringEvidence-0",
                    "effect_nodes": lowerings,
                    "mki_operations": mki,
                    "world_kernel_classes": kernel,
                    "prepared": False,
                    "committed": False,
                },
            },
            "energy": {
                "total": {
                    "kind": "Exact",
                    "value": program["budget"]["energy_j"],
                    "unit": "J",
                    "dimension": "Energy",
                    "assumption_ids": [],
                    "evidence_ids": evidence_ids,
                },
                "components": {
                    "control": {
                        "kind": "Exact",
                        "value": program["budget"]["energy_j"],
                        "unit": "J",
                        "dimension": "Energy",
                        "assumption_ids": [],
                        "evidence_ids": evidence_ids,
                    }
                },
                "display_unit": "J",
                "accounting_boundary": (
                    "Portable upper bound; no host record or reservation was produced"
                ),
            },
            "resources": [
                {
                    "kind": "EventBudget",
                    "estimate": {
                        "kind": "Exact",
                        "value": program["budget"]["events"],
                        "unit": "event",
                        "dimension": "Count",
                        "assumption_ids": [],
                        "evidence_ids": [],
                    },
                },
                {
                    "kind": "MicrostepBudget",
                    "estimate": {
                        "kind": "Exact",
                        "value": program["budget"]["microsteps"],
                        "unit": "microstep",
                        "dimension": "Count",
                        "assumption_ids": [],
                        "evidence_ids": [],
                    },
                },
            ],
            "assessments": assessments,
            "diagnostics": diagnostics,
            "assumptions": [],
            "evidence": evidence,
        }
        validate_feasibility_report(report)
        return report


__all__ = [
    "MKI_OPERATIONS",
    "WORLD_KERNEL_CLASSES",
    "MagicalProgramEvaluator",
    "ProgramContractRegistration",
    "ProgramContractRegistry",
    "ProgramSemanticError",
    "default_program_contract_registry",
]
