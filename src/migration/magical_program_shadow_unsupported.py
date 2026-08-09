"""Recognized-unsupported MagicalProgram shadow classifications."""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from src.evaluator.magical_program import MagicalProgramEvaluator
from src.evaluator.magical_program_contracts import (
    ProgramContractRegistration,
    ProgramContractRegistry,
    default_program_contract_registry,
)
from src.evaluator.schema import validate_feasibility_report

from .magical_program_shadow_support import (
    ShadowTranslation,
    bundle_contract_pair,
    profile_from_bundle,
    program_envelope,
    world_from_bundle,
)

_JSON = dict[str, Any]

UNSUPPORTED_CONTRACTS = (
    "light.guidance",
    "dynamics.levitation",
    "matter.purification",
    "observer.poison-detection",
)


def unsupported_registry(contract_id: str) -> ProgramContractRegistry:
    registry = default_program_contract_registry()
    registry.register(
        ProgramContractRegistration(
            contract_id,
            "1",
            "effect.invoke",
            (),
            "effect_result",
            (),
            0.0,
            0.0,
            0,
            (),
            (),
            support_level="recognized-unsupported",
        )
    )
    return registry


def unsupported_program(bundle: Mapping[str, Any]) -> _JSON:
    contract_id = str(bundle["semantic_contract"]["contract_id"])
    return program_envelope(
        bundle,
        program_id=f"program:migrated:{contract_id}:1",
        budget_energy=float(bundle["execution"]["energy_budget_j"]),
        budget_events=0,
        values=[],
        nodes=[
            {
                "node_id": "recognized_unsupported_effect",
                "order": 0,
                "instruction": "effect.invoke",
                "inputs": [],
                "produces": ["unsupported_result"],
                "contract": {"contract_id": contract_id, "revision": "1"},
                "obligations": {
                    "capabilities": [],
                    "leases": [],
                    "identities": [],
                    "evidence": [],
                    "accounting": [],
                    "resources": {
                        "energy_j": 0.0,
                        "matter_kg": 0.0,
                        "events": 0,
                    },
                },
            }
        ],
        edges=[],
        outputs=[
            {
                "name": "result",
                "binding": "unsupported_result",
                "kind": "effect_result",
            }
        ],
    )


class ShadowMagicalProgramEvaluator(MagicalProgramEvaluator):
    """Normal evaluator plus explicit recognized-unsupported classification."""

    def evaluate_program(self, program: Mapping[str, Any], **kwargs: Any) -> _JSON:
        unsupported = []
        for node in program.get("nodes", []):
            contract = node.get("contract")
            if contract is None:
                continue
            item = self.contracts.lookup(
                str(contract["contract_id"]), str(contract["revision"])
            )
            if item.support_level == "recognized-unsupported":
                unsupported.append(item)
        if not unsupported:
            return super().evaluate_program(program, **kwargs)

        temporary = ProgramContractRegistry(
            replace(item, support_level="implemented")
            for item in self.contracts.registrations()
        )
        base = MagicalProgramEvaluator(
            contracts=temporary,
            registry_id=self.registry_id,
            registry_revision=self.registry_revision,
            profile_id=self.profile_id,
            profile_revision=self.profile_revision,
            limits=self.limits,
        ).evaluate_program(program, **kwargs)
        if base["status"] == "Infeasible":
            return base
        diagnostic = {
            "id": "diag:program:001:UnsupportedSemanticSubset",
            "stage": "PROGRAM_SEMANTICS",
            "code": "UnsupportedSemanticSubset",
            "severity": "unknown",
            "message": (
                "Declared experimental contract is recognized but not "
                "executable in this implementation."
            ),
            "evidence_ids": [],
            "program_location": {
                "node_id": program["nodes"][0]["node_id"],
                "order": program["nodes"][0]["order"],
                "path": "/nodes/0",
            },
        }
        base["status"] = "Indeterminate"
        base["diagnostics"] = [diagnostic]
        for assessment in base["assessments"]:
            if assessment["dimension"] in {
                "typing",
                "lowering",
                "runtime_obligations",
            }:
                assessment["status"] = "Unknown"
                assessment["diagnostic_ids"] = [diagnostic["id"]]
        base["interpretations"]["kernel_plan"]["mki_operations"] = []
        base["interpretations"]["kernel_plan"]["world_kernel_classes"] = []
        base["interpretations"]["kernel_plan"]["effect_nodes"] = []
        validate_feasibility_report(base)
        return base


def translate_unsupported(bundle: Mapping[str, Any]) -> ShadowTranslation:
    contract_id = str(bundle["semantic_contract"]["contract_id"])
    profile = profile_from_bundle(bundle)
    world = world_from_bundle(bundle, profile)
    evaluator = ShadowMagicalProgramEvaluator(
        contracts=unsupported_registry(contract_id)
    )
    return ShadowTranslation(
        unsupported_program(bundle),
        world,
        evaluator,
        None,
        "recognized-unsupported",
        bundle_contract_pair(bundle),
    )


__all__ = [
    "ShadowMagicalProgramEvaluator",
    "UNSUPPORTED_CONTRACTS",
    "translate_unsupported",
    "unsupported_program",
    "unsupported_registry",
]
