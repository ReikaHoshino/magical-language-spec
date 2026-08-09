#!/usr/bin/env python3
"""Verify that every required pull-request workflow passed on the current PR head.

This is a repository-owned safety check for merge automation and human release
work. A successful run attached to an older commit never satisfies the gate.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

REQUIRED_WORKFLOWS = (
    "Repository regression",
    "Conformance package smoke",
    "MagicalProgram runtime smoke",
)


@dataclass(frozen=True)
class GateError(RuntimeError):
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


def _run_order(run: Mapping[str, Any]) -> tuple[int, int]:
    return (int(run.get("run_attempt", 0) or 0), int(run.get("id", 0) or 0))


def evaluate_merge_gate(
    *,
    pr_head_sha: str,
    workflow_runs: Iterable[Mapping[str, Any]],
    required_workflows: Sequence[str] = REQUIRED_WORKFLOWS,
    expected_head_sha: str | None = None,
) -> dict[str, Any]:
    """Return a deterministic exact-head merge decision.

    The newest exact-head pull-request run for each required workflow is
    authoritative. Runs attached to another SHA or another GitHub event are
    deliberately ignored.
    """

    if not isinstance(pr_head_sha, str) or not pr_head_sha:
        raise GateError("MergeGateHeadMissing", "The pull request has no head SHA.")
    if expected_head_sha is not None and expected_head_sha != pr_head_sha:
        return {
            "status": "FAIL",
            "head_sha": pr_head_sha,
            "expected_head_sha": expected_head_sha,
            "reason_codes": ["MergeGateHeadChanged"],
            "workflows": {},
        }

    runs = [dict(run) for run in workflow_runs]
    results: dict[str, dict[str, Any]] = {}
    reasons: list[str] = []
    for workflow_name in required_workflows:
        candidates = [
            run
            for run in runs
            if run.get("name") == workflow_name
            and run.get("head_sha") == pr_head_sha
            and run.get("event") == "pull_request"
        ]
        if not candidates:
            results[workflow_name] = {
                "status": "Missing",
                "conclusion": None,
                "run_id": None,
                "head_sha": pr_head_sha,
                "reason_code": "MergeGateExactHeadRunMissing",
            }
            reasons.append("MergeGateExactHeadRunMissing")
            continue

        selected = max(candidates, key=_run_order)
        status = selected.get("status")
        conclusion = selected.get("conclusion")
        reason_code: str | None = None
        if status != "completed":
            reason_code = "MergeGateWorkflowIncomplete"
        elif conclusion != "success":
            reason_code = "MergeGateWorkflowUnsuccessful"
        if reason_code is not None:
            reasons.append(reason_code)
        results[workflow_name] = {
            "status": status,
            "conclusion": conclusion,
            "run_id": selected.get("id"),
            "head_sha": selected.get("head_sha"),
            "reason_code": reason_code,
        }

    return {
        "status": "PASS" if not reasons else "FAIL",
        "head_sha": pr_head_sha,
        "expected_head_sha": expected_head_sha,
        "reason_codes": sorted(set(reasons)),
        "workflows": results,
    }


def _fetch_json(url: str, *, token: str) -> Mapping[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "magical-language-spec-merge-gate",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        payload = error.read().decode("utf-8", errors="replace")
        raise GateError(
            "MergeGateGitHubHttpError",
            f"GitHub returned HTTP {error.code}: {payload}",
        ) from error
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        raise GateError("MergeGateGitHubReadFailure", str(error)) from error


def check_pull_request(
    *,
    repository: str,
    pull_request: int,
    token: str,
    api_url: str = "https://api.github.com",
    expected_head_sha: str | None = None,
) -> dict[str, Any]:
    if repository.count("/") != 1:
        raise GateError(
            "MergeGateRepositoryInvalid",
            "repository must be in owner/name form",
        )
    base = api_url.rstrip("/")
    pr = _fetch_json(
        f"{base}/repos/{repository}/pulls/{pull_request}", token=token
    )
    head = pr.get("head", {})
    head_sha = head.get("sha") if isinstance(head, Mapping) else None
    query = urlencode(
        {
            "event": "pull_request",
            "head_sha": head_sha or "",
            "per_page": 100,
        }
    )
    response = _fetch_json(
        f"{base}/repos/{repository}/actions/runs?{query}", token=token
    )
    runs = response.get("workflow_runs", [])
    if not isinstance(runs, list):
        raise GateError(
            "MergeGateWorkflowResponseInvalid",
            "GitHub workflow response has no workflow_runs array",
        )
    return evaluate_merge_gate(
        pr_head_sha=str(head_sha or ""),
        workflow_runs=runs,
        expected_head_sha=expected_head_sha,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY"),
        help="GitHub repository in owner/name form (default: GITHUB_REPOSITORY)",
    )
    parser.add_argument("--pr", type=int, required=True, help="pull request number")
    parser.add_argument(
        "--expected-head-sha",
        help="fail if the PR head changed after review",
    )
    parser.add_argument(
        "--api-url",
        default=os.environ.get("GITHUB_API_URL", "https://api.github.com"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN")
    if not args.repository:
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "reason_codes": ["MergeGateRepositoryMissing"],
                },
                sort_keys=True,
            )
        )
        return 2
    if not token:
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "reason_codes": ["MergeGateTokenMissing"],
                },
                sort_keys=True,
            )
        )
        return 2
    try:
        result = check_pull_request(
            repository=args.repository,
            pull_request=args.pr,
            token=token,
            api_url=args.api_url,
            expected_head_sha=args.expected_head_sha,
        )
    except GateError as error:
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "reason_codes": [error.code],
                    "message": error.message,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
