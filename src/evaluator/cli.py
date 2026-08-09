"""Command-line entry point for the v0.8 Minimal Local Evaluator."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .evaluator import LocalEvaluator
from .formatting import LEVELS, format_human, format_json

AMBIGUITY_POLICIES = (
    "StrictReject",
    "InteractiveResolve",
    "ContextualDeterministic",
    "LegacyPermissive",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="magical-language-evaluator",
        description="Deterministic v0.8 dry-run evaluator (Latin source or NSR JSON).",
    )
    ingress = parser.add_mutually_exclusive_group(required=True)
    ingress.add_argument(
        "--source",
        metavar="TEXT",
        help="evaluate natural-language source through an explicit reference adapter",
    )
    ingress.add_argument(
        "--nsr",
        metavar="PATH",
        help="evaluate NSR JSON from PATH, or '-' for stdin",
    )
    parser.add_argument(
        "--lang",
        choices=("lat",),
        help="explicit project adapter ID; required with --source and invalid with --nsr",
    )
    parser.add_argument(
        "--ambiguity-policy",
        choices=AMBIGUITY_POLICIES,
        default="StrictReject",
        help="explicit Latin normalization ambiguity policy",
    )
    parser.add_argument(
        "--format",
        choices=("human", "json"),
        default="human",
        help="output encoding",
    )
    parser.add_argument(
        "--level",
        choices=LEVELS,
        default="report",
        help="human abstraction level or JSON stage projection",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.source is not None and args.lang != "lat":
        parser.error("--source requires explicit --lang lat in v0.8")
    if args.nsr is not None and args.lang is not None:
        parser.error("--lang applies only to natural-language --source ingress")

    evaluator = LocalEvaluator()
    if args.source is not None:
        report = evaluator.evaluate_latin_source(
            args.source,
            ambiguity_policy=args.ambiguity_policy,
        )
    else:
        payload = (
            sys.stdin.read()
            if args.nsr == "-"
            else Path(args.nsr).read_text(encoding="utf-8")
        )
        report = evaluator.evaluate_nsr_json(payload)

    output = (
        format_json(report, level=args.level)
        if args.format == "json"
        else format_human(report, level=args.level)
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
