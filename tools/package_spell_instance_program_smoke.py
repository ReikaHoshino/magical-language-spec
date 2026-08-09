"""Installed-package smoke for the public 12-bundle MagicalProgram cutover."""
from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from typing import Any

from src.artifacts.cli import main as artifact_cli_main
from src.artifacts.spell_instance_program import default_service
from src.resources import resource_path


def main() -> int:
    manifest = json.loads(
        resource_path(
            "conformance/magical-program-shadow-migration.json"
        ).read_text(encoding="utf-8")
    )
    results: list[dict[str, Any]] = []
    for item in sorted(manifest["inventory"], key=lambda row: row["order"]):
        path = resource_path(str(item["path"]))
        service = default_service()
        checked = service.check_file(path)
        evaluated = service.evaluate_file(path)
        api_result = service.run_file(path)
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = artifact_cli_main(["run", str(path)])
        cli_result = json.loads(output.getvalue())
        passed = (
            checked.get("status") == "Accepted"
            and evaluated.get("status") == "Evaluated"
            and api_result.get("status") == "PASS"
            and exit_code == 0
            and cli_result == api_result
        )
        results.append(
            {
                "migration_id": item["migration_id"],
                "classification": item["classification"],
                "api_status": api_result.get("status"),
                "cli_status": cli_result.get("status"),
                "cli_exit_code": exit_code,
                "api_cli_equal": cli_result == api_result,
                "status": "PASS" if passed else "FAIL",
            }
        )
    payload = {
        "suite_id": "SpellInstance-Public-MagicalProgram-Cutover-0",
        "case_count": len(results),
        "status": "PASS"
        if len(results) == 12 and all(item["status"] == "PASS" for item in results)
        else "FAIL",
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
