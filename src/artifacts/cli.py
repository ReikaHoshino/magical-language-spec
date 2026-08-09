"""Deterministic JSON CLI for experimental artifact check/eval/run."""
from __future__ import annotations

import argparse
import json
from typing import Sequence

from .spell_instance_program import default_service


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="magical-language-artifact")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("check", "eval", "run"):
        child = subparsers.add_parser(command)
        child.add_argument("file")
        child.add_argument("--input-kind")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    service = default_service()
    method = {
        "check": service.check_file,
        "eval": service.evaluate_file,
        "run": service.run_file,
    }[arguments.command]
    result = method(arguments.file, input_kind=arguments.input_kind)
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    if arguments.command == "check":
        return 0 if result.get("status") == "Accepted" else 2
    if arguments.command == "eval":
        return 0 if result.get("status") == "Evaluated" else 2
    return 0 if result.get("status") == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
