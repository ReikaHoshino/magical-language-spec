from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class TemporalCausalityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.owner = read("reference/temporal-causality.md")

    def test_current_owner_preserves_released_boundaries(self) -> None:
        for invariant in (
            "Restore != Rewind",
            "Replay != Rewind",
            "ordinary RECONFIGURE != committed-history mutation",
            "Energy/resource magnitude != temporal/causal authority",
            "Capability<History,Causality,Rewrite>",
            "failure leaves committed `H` unchanged",
        ):
            self.assertIn(invariant, self.owner)

    def test_fail_closed_diagnostics_have_distinct_meanings(self) -> None:
        errors = read("reference/errors.md")
        for diagnostic in (
            "HistoryMutationDenied",
            "TemporalAuthorityError",
            "CausalityCycleError",
        ):
            self.assertIn(f"### `{diagnostic}`", errors)
            self.assertIn(diagnostic, self.owner)
        self.assertIn(
            "HistoryMutationDenied != TemporalAuthorityError != CausalityCycleError",
            self.owner,
        )

    def test_cross_document_owners_point_to_the_contract(self) -> None:
        for path in (
            "README.md",
            "reference/semantics.md",
            "reference/runtime-time.md",
            "reference/types.md",
            "reference/security-sandbox.md",
            "reference/terminology.md",
        ):
            self.assertIn("temporal-causality.md", read(path), path)

    def test_replay_and_future_observation_remain_non_authorizing(self) -> None:
        self.assertIn("DeterministicReplay != Rewind", self.owner)
        self.assertIn("prediction result != observed future truth", self.owner)
        self.assertIn("ordinary Read != direct future observation authority", self.owner)
        self.assertIn("TemporalAuthorityError", self.owner)

    def test_v1_required_surface_is_not_silently_expanded(self) -> None:
        manifest = json.loads(read("conformance/manifest.json"))
        self.assertEqual(4, len(manifest["classes"]))
        self.assertEqual(65, len(manifest["cases"]))
        self.assertIn("outside the v1 stable required conformance surface", self.owner)


if __name__ == "__main__":
    unittest.main()
