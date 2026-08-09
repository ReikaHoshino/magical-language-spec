#!/usr/bin/env python3
"""Exercise installed MagicalProgram and MGLS paths outside checkout cwd."""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from src.evaluator.magical_program import MagicalProgramEvaluator
from src.evaluator.schema import validate_feasibility_report
from src.mgls import canonical_compilation_bytes, check_source, compile_source
from src.resources import reference_root, resource_path
from tools.package_program_shadow_smoke import run as run_shadow_smoke


def _command(*arguments: str) -> dict:
    executable = shutil.which("magical-language")
    if executable is None:
        raise RuntimeError("installed magical-language console script is unavailable")
    completed = subprocess.run(
        [executable, *arguments],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if "Traceback" in completed.stdout or "Traceback" in completed.stderr:
        raise RuntimeError("installed magical-language command leaked a traceback")
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"installed command returned non-JSON output: {completed.stdout!r}"
        ) from error
    expected = 0 if result.get("status") in {
        "Accepted",
        "Evaluated",
        "Compiled",
        "Committed",
        "PASS",
    } else 2 if result.get("status") == "Rejected" else 3
    if completed.returncode != expected:
        raise RuntimeError(
            "installed command exit code disagrees with its JSON status: "
            f"{completed.returncode} != {expected}: {result}"
        )
    return result


def main() -> int:
    evaluator = MagicalProgramEvaluator()
    world = {
        "revision": "world:package-smoke:1",
        "entities": {"entity:unchanged": {"state": "same"}},
    }
    history = [{"event_id": "event:package-smoke:existing"}]
    before_world = copy.deepcopy(world)
    before_history = copy.deepcopy(history)

    effect_path = resource_path("examples/magical-program/MP-001.json")
    pure_path = resource_path("examples/magical-program/MP-PURE-001.json")
    effect = evaluator.evaluate_bytes(
        effect_path.read_bytes(), world_state=world, history=history
    )
    pure = evaluator.evaluate_bytes(
        pure_path.read_bytes(), world_state=world, history=history
    )
    validate_feasibility_report(effect)
    validate_feasibility_report(pure)

    if effect.get("status") != "ConditionallyFeasible":
        raise RuntimeError(
            "installed effect program did not reach conditional feasibility: "
            f"{effect}"
        )
    if pure.get("status") != "Feasible":
        raise RuntimeError(
            f"installed pure program did not reach feasibility: {pure}"
        )
    if world != before_world or history != before_history:
        raise RuntimeError(
            "installed evaluator mutated supplied WorldState or History"
        )
    if effect["interpretations"]["kernel_plan"]["mki_operations"] != [
        "RECONFIGURE",
        "RESOLVE",
    ]:
        raise RuntimeError(
            "installed effect program produced unexpected MKI set"
        )
    if pure["interpretations"]["typed_mir"]["outputs"]["total"]["value"] != 5.0:
        raise RuntimeError(
            "installed pure program produced an unexpected result"
        )

    transition_path = resource_path(
        "examples/mgls/independent-transition.mgls"
    )
    transition_source = transition_path.read_bytes()
    boundary_source = resource_path(
        "examples/mgls/boundary-reflection.mgls"
    ).read_bytes()
    transition_first = compile_source(transition_source)
    transition_second = compile_source(transition_source)
    boundary = compile_source(boundary_source)
    if transition_first.get("status") != "Compiled" or boundary.get("status") != "Compiled":
        raise RuntimeError("installed MGLS compiler did not compile both positive sources")
    if transition_first["target_admission"].get("status") != "Accepted":
        raise RuntimeError("installed MGLS transition target was not independently admitted")
    if boundary["target_admission"].get("status") != "Accepted":
        raise RuntimeError("installed MGLS boundary target was not independently admitted")
    if canonical_compilation_bytes(transition_first) != canonical_compilation_bytes(
        transition_second
    ):
        raise RuntimeError("installed MGLS compilation is not byte deterministic")
    rejected = check_source(
        transition_source.replace(b'mgls "0";', b'mgls "1";', 1)
    )
    if rejected.get("status") != "Rejected":
        raise RuntimeError("installed MGLS compiler did not fail closed")
    if rejected["diagnostics"][0].get("code") != "SpecVersionIncompatible":
        raise RuntimeError("installed MGLS compiler returned the wrong diagnostic")

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        emitted_program = root / "installed.program.mga.json"
        emitted_map = root / "installed.source-map.mga.json"
        compiled_command = _command(
            "compile",
            str(transition_path),
            "--emit-program",
            str(emitted_program),
            "--emit-source-map",
            str(emitted_map),
        )
        source_check = _command("check", str(transition_path))
        source_eval = _command("eval", str(transition_path))
        source_run = _command("run", str(transition_path))
        program_check = _command("check", str(emitted_program))
        program_eval = _command("eval", str(emitted_program))
        program_run = _command("run", str(emitted_program))
        bundle_run = _command(
            "run",
            str(
                resource_path(
                    "examples/spell-instances/generic/GENERIC-001.json"
                )
            ),
        )
        invalid_source = root / "invalid.mgls"
        invalid_source.write_text('mgls "0"; import "host";', encoding="utf-8")
        invalid = _command("check", str(invalid_source))

    statuses = {
        "compile": compiled_command.get("status"),
        "source_check": source_check.get("status"),
        "source_eval": source_eval.get("status"),
        "source_run": source_run.get("status"),
        "program_check": program_check.get("status"),
        "program_eval": program_eval.get("status"),
        "program_run": program_run.get("status"),
        "bundle_run": bundle_run.get("status"),
        "invalid": invalid.get("status"),
    }
    expected_statuses = {
        "compile": "Compiled",
        "source_check": "Accepted",
        "source_eval": "Evaluated",
        "source_run": "Committed",
        "program_check": "Accepted",
        "program_eval": "Evaluated",
        "program_run": "Committed",
        "bundle_run": "PASS",
        "invalid": "Rejected",
    }
    if statuses != expected_statuses:
        raise RuntimeError(
            f"installed user workflow status mismatch: {statuses!r}"
        )
    if source_run["result"]["execution"] != program_run["result"]["execution"]:
        raise RuntimeError(
            "installed source and emitted program runtime traces disagree"
        )
    if source_run["result"]["replay"].get("status") != "Match":
        raise RuntimeError("installed source replay did not match")
    if program_run["result"]["replay"].get("status") != "Match":
        raise RuntimeError("installed program replay did not match")
    if bundle_run["result"]["replay"].get("status") != "Match":
        raise RuntimeError("installed bundle replay did not match")
    if invalid["diagnostics"][0].get("code") != "UnsupportedSemanticExtension":
        raise RuntimeError("installed command returned the wrong source diagnostic")

    migration = run_shadow_smoke()
    if migration.get("status") != "PASS":
        raise RuntimeError(
            f"installed 12-case migration matrix failed: {migration}"
        )

    print(
        json.dumps(
            {
                "status": "PASS",
                "package_root": str(reference_root().resolve()),
                "cwd": str(Path.cwd().resolve()),
                "effect_status": effect["status"],
                "pure_status": pure["status"],
                "world_unchanged": True,
                "history_unchanged": True,
                "mgls_positive_count": 2,
                "mgls_target_admission": "Accepted",
                "mgls_deterministic": True,
                "mgls_negative_code": rejected["diagnostics"][0]["code"],
                "installed_workflow_statuses": statuses,
                "installed_command": "magical-language",
                "migration_case_count": migration["case_count"],
                "migration_classification_counts": migration[
                    "classification_counts"
                ],
                "migration_failure_count": migration["failure_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
