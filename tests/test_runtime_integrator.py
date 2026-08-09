from __future__ import annotations

import unittest

from src.runtime.integrator import SyntheticReferenceIntegrator
from src.runtime.sandbox import RuntimeExecutionError


class RuntimeIntegratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.integrator = SyntheticReferenceIntegrator()

    def test_zero_duration_canonical_interval_is_explicit_noop(self) -> None:
        report = self.integrator.advance(
            "2026-01-01T00:00:00Z",
            "2026-01-01T00:00:00Z",
        )

        self.assertEqual(report["status"], "NoAdvanceRequired")
        self.assertEqual(report["steps"], 0)
        self.assertFalse(report["physical_law_modified"])

    def test_nonzero_interval_without_processes_is_deterministic(self) -> None:
        report = self.integrator.advance(
            "2026-01-01T00:00:00Z",
            "2026-01-01T00:00:00.005Z",
        )

        self.assertEqual(report["status"], "AdvancedNoProcesses")
        self.assertEqual(report["steps"], 1)
        self.assertAlmostEqual(report["duration_seconds"], 0.005)
        self.assertFalse(report["physical_law_modified"])

    def test_unknown_continuous_model_fails_closed(self) -> None:
        with self.assertRaises(RuntimeExecutionError) as raised:
            self.integrator.advance(
                "2026-01-01T00:00:00Z",
                "2026-01-01T00:00:00.005Z",
                continuous_processes=[{"kind": "UnknownProcess"}],
            )

        self.assertEqual(raised.exception.code, "IntegratorModelUnavailable")

    def test_invalid_interval_is_rejected(self) -> None:
        with self.assertRaises(RuntimeExecutionError) as raised:
            self.integrator.advance(
                "2026-01-01T00:00:01Z",
                "2026-01-01T00:00:00Z",
            )

        self.assertEqual(raised.exception.code, "InvalidTickInterval")


if __name__ == "__main__":
    unittest.main()
