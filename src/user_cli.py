"""Command-line entry point for the unified experimental user workflow."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from .user_workflow import UserWorkflow, workflow_exit_code

_INPUT_KINDS = (
    "auto",
    "mgls",
    "magical-program",
    "spell-instance-bundle",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="magical-language",
        description=(
            "Experimental deterministic workflow for MGLS source, "
            "MagicalProgram, and SpellInstanceBundle inputs."
        ),
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "eval", "run"):
        child = commands.add_parser(name)
        child.add_argument("file")
        child.add_argument(
            "--input-kind",
            choices=_INPUT_KINDS,
            default="auto",
            help="expected public input kind; decoded content remains authoritative",
        )

    compile_parser = commands.add_parser("compile")
    compile_parser.add_argument("file")
    compile_parser.add_argument(
        "--input-kind",
        choices=("auto", "mgls"),
        default="auto",
        help="compile accepts MGLS source only",
    )
    compile_parser.add_argument(
        "--emit-program",
        metavar="PATH",
        help="atomically write the emitted MagicalProgram JSON",
    )
    compile_parser.add_argument(
        "--emit-source-map",
        metavar="PATH",
        help="atomically write the emitted MglsSourceMap JSON",
    )
    return parser


def _canonical_output(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _output_error(result: Mapping[str, Any], code: str, message: str) -> dict:
    rejected = dict(result)
    rejected["status"] = "Rejected"
    rejected["result"] = None
    rejected["diagnostics"] = [
        {
            "stage": "OUTPUT",
            "code": code,
            "severity": "fatal",
            "message": message,
        }
    ]
    return rejected


def _prepare_output(path: Path, payload: bytes) -> tuple[Path, Path]:
    if path.is_symlink():
        raise ValueError("output path must not be a symbolic link")
    parent = path.parent if str(path.parent) else Path(".")
    if not parent.exists() or not parent.is_dir() or parent.is_symlink():
        raise ValueError("output parent must be an existing non-symlink directory")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return temporary, path


def _emit_outputs(
    result: Mapping[str, Any],
    *,
    input_path: Path,
    program_path: str | None,
    source_map_path: str | None,
) -> dict:
    if result.get("status") != "Compiled":
        return dict(result)
    requested: list[tuple[str, Path, Any]] = []
    compilation = result.get("result")
    if not isinstance(compilation, Mapping):
        return _output_error(
            result,
            "OutputUnavailable",
            "Successful compilation returned no output object.",
        )
    if program_path is not None:
        requested.append(("program", Path(program_path), compilation.get("program")))
    if source_map_path is not None:
        requested.append(
            ("source_map", Path(source_map_path), compilation.get("source_map"))
        )
    if not requested:
        return dict(result)

    destinations = [item[1].absolute() for item in requested]
    if len(set(destinations)) != len(destinations):
        return _output_error(
            result,
            "OutputPathCollision",
            "Program and source-map outputs must use distinct paths.",
        )
    if input_path.absolute() in destinations:
        return _output_error(
            result,
            "OutputOverwritesInput",
            "Compiler output must not overwrite the source input.",
        )

    prepared: list[tuple[Path, Path, str]] = []
    try:
        for label, destination, value in requested:
            if not isinstance(value, Mapping):
                raise ValueError(f"compiled {label} output is unavailable")
            payload = (_canonical_output(value) + "\n").encode("utf-8")
            temporary, final = _prepare_output(destination, payload)
            prepared.append((temporary, final, label))
        for temporary, final, _ in prepared:
            os.replace(temporary, final)
    except Exception:
        for temporary, _, _ in prepared:
            temporary.unlink(missing_ok=True)
        return _output_error(
            result,
            "OutputWriteFailure",
            "Compiler outputs could not be written atomically.",
        )

    emitted = dict(result)
    operation = dict(compilation)
    operation["emitted"] = {
        label: True for _, _, label in prepared
    }
    emitted["result"] = operation
    return emitted


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    workflow = UserWorkflow()
    result = workflow.execute_path(
        arguments.command,
        arguments.file,
        input_kind=None
        if arguments.input_kind == "auto"
        else arguments.input_kind,
    )
    if arguments.command == "compile":
        result = _emit_outputs(
            result,
            input_path=Path(arguments.file),
            program_path=arguments.emit_program,
            source_map_path=arguments.emit_source_map,
        )
    print(_canonical_output(result))
    return workflow_exit_code(result)


if __name__ == "__main__":
    raise SystemExit(main())
