#!/usr/bin/env python3
"""Run the separate optional SUCCESS-ARCANA bundle suite."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.artifacts import default_service
from src.resources import resource_path


def main() -> int:
    service = default_service()
    root = resource_path("examples/spell-instances/success-arcana")
    results = []
    for path in sorted(root.glob("*.json")):
        result = service.run_file(path)
        results.append({"case_id": path.stem, "status": result["status"]})
    output = {"class_id": "Experimental-Arcana-0", "status": "PASS" if results and all(item["status"] == "PASS" for item in results) else "FAIL", "results": results}
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
