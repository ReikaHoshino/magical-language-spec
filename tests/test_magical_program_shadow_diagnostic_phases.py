from __future__ import annotations

import copy
import unittest

from src.migration.magical_program_shadow import _projected_generic_observation


class MagicalProgramShadowDiagnosticPhaseTests(unittest.TestCase):
    def project(self, diagnostics, *, execution_status="Committed"):
        report = {
            "status": "ConditionallyFeasible",
            "diagnostics": copy.deepcopy(diagnostics),
        }
        execution = {
            "status": execution_status,
        }
        if execution_status == "Aborted":
            execution["abort"] = {
                "stage": "PREPARE",
                "code": "ProgramAuthorityError",
            }
        return _projected_generic_observation(
            report,
            execution,
            {"status": "Match"},
            {"Sigma": {"revision": "world:test:1"}},
        )

    def test_only_known_prepare_deferrals_project_to_feasible(self) -> None:
        projected = self.project(
            [
                {
                    "code": "ProgramResolutionDeferred",
                    "severity": "conditional",
                },
                {
                    "code": "ProgramRuntimeRevalidationRequired",
                    "severity": "conditional",
                },
            ]
        )
        self.assertEqual(
            "Feasible", projected["evaluation"]["report"]["status"]
        )
        self.assertEqual(
            [
                "ProgramResolutionDeferred",
                "ProgramRuntimeRevalidationRequired",
            ],
            [
                item["code"]
                for item in projected["evaluation"]["report"]["diagnostics"]
            ],
        )

    def test_unknown_or_fatal_diagnostic_is_never_suppressed(self) -> None:
        for diagnostics in (
            [
                {
                    "code": "ProgramUnexpectedConditional",
                    "severity": "conditional",
                }
            ],
            [
                {
                    "code": "ProgramResolutionDeferred",
                    "severity": "conditional",
                },
                {
                    "code": "ProgramTypeFailure",
                    "severity": "fatal",
                },
            ],
        ):
            with self.subTest(diagnostics=diagnostics):
                projected = self.project(diagnostics)
                self.assertEqual(
                    "ConditionallyFeasible",
                    projected["evaluation"]["report"]["status"],
                )
                self.assertEqual(
                    diagnostics,
                    projected["evaluation"]["report"]["diagnostics"],
                )

    def test_abort_alias_is_limited_to_terminal_projection(self) -> None:
        diagnostics = [
            {
                "code": "ProgramResolutionDeferred",
                "severity": "conditional",
            }
        ]
        projected = self.project(diagnostics, execution_status="Aborted")
        self.assertEqual(
            diagnostics,
            projected["evaluation"]["report"]["diagnostics"],
        )
        self.assertEqual("AuthorityError", projected["execution"]["abort"]["code"])


if __name__ == "__main__":
    unittest.main()
