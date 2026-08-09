"""Run the complete MagicalProgram migration matrix from package resources."""
from __future__ import annotations

import json
from typing import Any

from src.migration.legacy_program_oracle import run_shadow_file
from src.resources import resource_path

_JSON = dict[str, Any]


def run() -> _JSON:
    inventory_path = resource_path(
        "conformance/magical-program-shadow-migration.json"
    )
    golden_path = resource_path(
        "conformance/magical-program-golden-parity.json"
    )
    manifest = json.loads(inventory_path.read_text(encoding="utf-8"))
    results: list[_JSON] = []
    failures: list[_JSON] = []
    counts = {
        "implemented": 0,
        "adversarial": 0,
        "recognized-unsupported": 0,
    }

    for item in sorted(manifest["inventory"], key=lambda row: row["order"]):
        classification = str(item["classification"])
        counts[classification] += 1
        source = resource_path(str(item["path"]))
        result = run_shadow_file(
            source,
            golden_manifest=golden_path,
        )
        observed = {
            "migration_id": item["migration_id"],
            "classification": classification,
            "path": item["path"],
            "status": result.get("status"),
            "evaluation_status": result.get("raw_evaluation_status", {}).get(
                "generic"
            ),
            "execution_status": None
            if result.get("generic_execution") is None
            else result["generic_execution"].get("status"),
            "replay_status": None
            if result.get("generic_replay") is None
            else result["generic_replay"].get("status"),
            "diagnostic_code": result.get("normalized_diagnostic_code"),
        }
        results.append(observed)

        valid = result.get("status") == "PASS"
        if classification == "recognized-unsupported":
            valid = valid and observed["evaluation_status"] == "Indeterminate"
            valid = valid and observed["execution_status"] is None
        elif classification == "implemented":
            valid = valid and observed["execution_status"] == "Committed"
            valid = valid and observed["replay_status"] == "Match"
        elif item["migration_id"] == "MIG-DEBUG-HELL-001":
            valid = valid and observed["evaluation_status"] == "Infeasible"
            valid = valid and observed["execution_status"] is None
        else:
            valid = valid and observed["execution_status"] == "Aborted"
            valid = valid and observed["replay_status"] == "DeterministicAbort"
        if not valid:
            failures.append({"observed": observed, "details": result})

    return {
        "status": "PASS" if not failures else "FAIL",
        "case_count": len(results),
        "classification_counts": counts,
        "failure_count": len(failures),
        "results": results,
        "failures": failures,
    }


def main() -> int:
    payload = run()
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
