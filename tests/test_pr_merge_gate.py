from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "check_pr_merge_gate.py"
SPEC = importlib.util.spec_from_file_location("check_pr_merge_gate", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load merge-gate checker")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

REQUIRED = MODULE.REQUIRED_WORKFLOWS
evaluate_merge_gate = MODULE.evaluate_merge_gate


def run(
    name: str,
    head_sha: str,
    *,
    status: str = "completed",
    conclusion: str | None = "success",
    run_id: int = 1,
    event: str = "pull_request",
):
    return {
        "id": run_id,
        "name": name,
        "head_sha": head_sha,
        "event": event,
        "status": status,
        "conclusion": conclusion,
        "run_attempt": 1,
    }


class PullRequestMergeGateTests(unittest.TestCase):
    def success_runs(self, head_sha: str = "head:new"):
        return [
            run(name, head_sha, run_id=index)
            for index, name in enumerate(REQUIRED, start=1)
        ]

    def test_all_required_workflows_must_succeed_on_exact_head(self) -> None:
        result = evaluate_merge_gate(
            pr_head_sha="head:new",
            workflow_runs=self.success_runs(),
            expected_head_sha="head:new",
        )
        self.assertEqual("PASS", result["status"])
        self.assertEqual([], result["reason_codes"])
        self.assertEqual(set(REQUIRED), set(result["workflows"]))

    def test_success_on_stale_head_does_not_satisfy_current_head(self) -> None:
        result = evaluate_merge_gate(
            pr_head_sha="head:new",
            workflow_runs=self.success_runs("head:old"),
        )
        self.assertEqual("FAIL", result["status"])
        self.assertEqual(
            ["MergeGateExactHeadRunMissing"], result["reason_codes"]
        )
        self.assertTrue(
            all(
                item["reason_code"] == "MergeGateExactHeadRunMissing"
                for item in result["workflows"].values()
            )
        )

    def test_push_success_on_exact_sha_does_not_satisfy_pr_gate(self) -> None:
        push_runs = [
            run(name, "head:new", run_id=index, event="push")
            for index, name in enumerate(REQUIRED, start=1)
        ]
        result = evaluate_merge_gate(
            pr_head_sha="head:new", workflow_runs=push_runs
        )
        self.assertEqual("FAIL", result["status"])
        self.assertEqual(
            ["MergeGateExactHeadRunMissing"], result["reason_codes"]
        )

    def test_failed_cancelled_pending_and_missing_workflows_fail_closed(self) -> None:
        bad_conclusions = ("failure", "cancelled", "timed_out", "skipped", None)
        for conclusion in bad_conclusions:
            with self.subTest(conclusion=conclusion):
                runs = self.success_runs()
                runs[0] = run(
                    REQUIRED[0],
                    "head:new",
                    conclusion=conclusion,
                    run_id=100,
                )
                result = evaluate_merge_gate(
                    pr_head_sha="head:new", workflow_runs=runs
                )
                self.assertEqual("FAIL", result["status"])
                self.assertIn(
                    "MergeGateWorkflowUnsuccessful", result["reason_codes"]
                )

        pending = self.success_runs()
        pending[1] = run(
            REQUIRED[1],
            "head:new",
            status="in_progress",
            conclusion=None,
            run_id=101,
        )
        pending_result = evaluate_merge_gate(
            pr_head_sha="head:new", workflow_runs=pending
        )
        self.assertEqual("FAIL", pending_result["status"])
        self.assertIn(
            "MergeGateWorkflowIncomplete", pending_result["reason_codes"]
        )

        missing_result = evaluate_merge_gate(
            pr_head_sha="head:new",
            workflow_runs=self.success_runs()[:-1],
        )
        self.assertEqual("FAIL", missing_result["status"])
        self.assertIn(
            "MergeGateExactHeadRunMissing", missing_result["reason_codes"]
        )

    def test_newest_exact_head_attempt_is_authoritative(self) -> None:
        runs = self.success_runs()
        runs.extend(
            [
                run(
                    REQUIRED[0],
                    "head:new",
                    conclusion="failure",
                    run_id=10,
                ),
                run(
                    REQUIRED[0],
                    "head:new",
                    conclusion="success",
                    run_id=11,
                ),
            ]
        )
        result = evaluate_merge_gate(
            pr_head_sha="head:new", workflow_runs=runs
        )
        self.assertEqual("PASS", result["status"])
        self.assertEqual(11, result["workflows"][REQUIRED[0]]["run_id"])

    def test_reviewed_head_change_fails_even_when_new_head_is_green(self) -> None:
        result = evaluate_merge_gate(
            pr_head_sha="head:new",
            expected_head_sha="head:reviewed",
            workflow_runs=self.success_runs(),
        )
        self.assertEqual("FAIL", result["status"])
        self.assertEqual(["MergeGateHeadChanged"], result["reason_codes"])
        self.assertEqual({}, result["workflows"])


if __name__ == "__main__":
    unittest.main()
