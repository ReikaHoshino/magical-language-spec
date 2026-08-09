from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class KernelExecutionContractTests(unittest.TestCase):
    def test_lower_boundary_preserves_six_mki_operations(self) -> None:
        contract = read("reference/kernel-execution.md")
        mki = read("reference/mki.md")
        for operation in (
            "RESOLVE",
            "OBSERVE",
            "CHANNEL",
            "TRANSFER",
            "RECONFIGURE",
            "CONSTRAIN",
        ):
            self.assertIn(operation, contract)
            self.assertIn(operation, mki)
        self.assertIn("Kernel interaction class != MKI primitive", contract)
        self.assertIn("public ECIR serialization", contract)

    def test_kernel_interaction_classes_are_fixed_semantic_categories(self) -> None:
        contract = read("reference/kernel-execution.md")
        for interaction in ("QUERY", "SAMPLE", "TRANSITION", "ACTIVATE", "DEACTIVATE"):
            self.assertIn(f"### {interaction}", contract)
        self.assertIn("specification-owned semantic categories", contract)
        self.assertIn("implementation/profile-owned", contract)

    def test_causal_active_effects_have_authoritative_semantic_projection(self) -> None:
        contract = read("reference/kernel-execution.md")
        semantics = read("reference/semantics.md")
        architecture = read("reference/architecture.md")
        runtime_impl = read("reference/runtime-implementation.md")

        self.assertIn("authoritative **semantic projection**", contract)
        self.assertIn("causally relevant active-effect semantics ⊆ authoritative Σ semantics", contract)
        self.assertIn("runtime handles / queues / caches / solver bookkeeping ⊆ Ω", contract)
        for effect in ("Transit", "Channel", "Controller", "Kinetic/DynamicsProcess"):
            self.assertIn(effect, contract)

        self.assertIn("portable semantic projectionは`Σ`のauthoritative semantics", semantics)
        self.assertIn("causally relevant active-effect semantics ⊆ authoritative Σ semantics", architecture)
        self.assertIn("storage/realization choice, not semantic ownership", runtime_impl)

    def test_commit_and_scheduler_commit_remain_distinct(self) -> None:
        contract = read("reference/kernel-execution.md")
        semantics = read("reference/semantics.md")
        architecture = read("reference/architecture.md")

        self.assertIn("control-plane COMMIT != all future consequences already occurred", contract)
        self.assertIn("scheduler Commit != control-plane COMMIT", contract)
        self.assertIn("initial atomic group", contract)
        self.assertIn("later scheduler Revalidate + Commit", contract)
        self.assertIn("initial semantic atomic group", semantics)
        self.assertIn("control-plane COMMIT != all future consequences already occurred", architecture)

    def test_atomic_group_is_all_or_none(self) -> None:
        contract = read("reference/kernel-execution.md")
        semantics = read("reference/semantics.md")
        self.assertIn("KernelAtomicGroup", contract)
        self.assertIn("no member of the group becomes authoritative", contract)
        self.assertIn("partial source debit", contract)
        self.assertIn("no member of the group becomes authoritative", semantics)

    def test_spec_owned_validation_cases_cover_issue_55(self) -> None:
        payload = json.loads(read("examples/kernel-execution/semantic-cases.json"))
        self.assertEqual("1", payload["schema_version"])
        cases = {case["id"]: case for case in payload["cases"]}
        self.assertEqual(
            {
                "KERNEL-TRANSFER-NONZERO-001",
                "KERNEL-RECONFIGURE-CONTINUOUS-001",
                "KERNEL-CONSTRAIN-BOUNDED-001",
            },
            set(cases),
        )

        transfer = cases["KERNEL-TRANSFER-NONZERO-001"]
        self.assertEqual(
            ["TRANSITION:source_debit", "ACTIVATE:transit"],
            transfer["initial_commit"]["atomic_group"],
        )
        self.assertIn(
            "source_plus_transit_plus_destination_conserved",
            transfer["mandatory_invariants"],
        )

        continuous = cases["KERNEL-RECONFIGURE-CONTINUOUS-001"]
        self.assertFalse(
            continuous["continuing_semantics"]["numerical_substep_is_semantic_primitive"]
        )

        constrain = cases["KERNEL-CONSTRAIN-BOUNDED-001"]
        self.assertFalse(
            constrain["continuing_semantics"]["registration_grants_unlimited_authority"]
        )
        self.assertTrue(
            constrain["continuing_semantics"]["future_actuation_requires_revalidation"]
        )

    def test_existing_time_and_world_kernel_invariants_remain_compatible(self) -> None:
        contract = read("reference/kernel-execution.md")
        runtime = read("reference/runtime-time.md")
        semantics = read("reference/semantics.md")
        for invariant in (
            "Physical time != runtime tick",
            "Integrator approximation != physical law",
        ):
            self.assertIn(invariant, contract)
            self.assertIn(invariant, runtime)
        self.assertIn("C = <Σ,H,Ω,P>", contract)
        self.assertIn("C = <Σ,H,Ω,P>", semantics)
        self.assertIn("PREPARE != COMMIT", semantics)

    def test_central_references_no_longer_leave_issue_55_boundary_open(self) -> None:
        for path in (
            "reference/mki.md",
            "reference/architecture.md",
        ):
            text = read(path)
            self.assertNotIn("Issue #55で", text, path)
            self.assertIn("kernel-execution.md", text, path)

        runtime_impl = read("reference/runtime-implementation.md")
        self.assertIn("kernel-execution.md", runtime_impl)
        self.assertIn("control-plane COMMIT != all future consequences already occurred", runtime_impl)


if __name__ == "__main__":
    unittest.main()
