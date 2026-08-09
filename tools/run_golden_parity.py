#!/usr/bin/env python3
"""Run the independent golden manifest against the frozen legacy oracle."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from src.artifacts.golden_parity import GoldenParityError, run_manifest
from src.artifacts.spell_instance import default_service as legacy_default_service

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "conformance" / "magical-program-golden-parity.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Repository/package resource root.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="External golden manifest.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        result = run_manifest(
            arguments.root,
            arguments.manifest,
            service=legacy_default_service(),
        )
    except (
        GoldenParityError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
    ) as error:
        payload = {
            "suite_id": "MagicalProgram-Golden-Parity-0",
            "status": "ERROR",
            "diagnostic": {
                "code": getattr(error, "code", "GoldenParityHarnessFailure"),
                "message": str(error),
            },
        }
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
