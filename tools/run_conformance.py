from __future__ import annotations

import argparse
import importlib.util
import io
import json
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "conformance" / "manifest.json"
SCHEMA_PATH = ROOT / "schemas" / "conformance-manifest.schema.json"
INITIAL_CLASS_IDS = {
    "Core-1.0",
    "Evaluator-1.0",
    "Adapter-lat-1.0",
    "Runtime-1.0",
}


class ConformanceManifestError(ValueError):
    """Raised when conformance metadata is structurally inconsistent."""


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    status: str
    detail: str = ""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConformanceManifestError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ConformanceManifestError(f"expected JSON object: {path}")
    return value


def _validate_schema(manifest: dict[str, Any]) -> None:
    schema = _read_json(SCHEMA_PATH)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(manifest),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        rendered = []
        for error in errors:
            path = ".".join(str(part) for part in error.absolute_path) or "<root>"
            rendered.append(f"{path}: {error.message}")
        raise ConformanceManifestError("schema validation failed:\n" + "\n".join(rendered))


def _require_unique(values: list[str], label: str) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    if duplicates:
        joined = ", ".join(sorted(duplicates))
        raise ConformanceManifestError(f"duplicate {label}: {joined}")


def _validate_rule_ref(rule_ref: dict[str, str]) -> None:
    document = ROOT / rule_ref["document"]
    if not document.is_file():
        raise ConformanceManifestError(f"missing normative document: {rule_ref['document']}")
    heading = rule_ref["heading"]
    lines = document.read_text(encoding="utf-8").splitlines()
    if heading not in lines:
        raise ConformanceManifestError(
            f"missing normative heading {heading!r} in {rule_ref['document']}"
        )


def _validate_integrity(manifest: dict[str, Any]) -> None:
    classes: list[dict[str, Any]] = manifest["classes"]
    cases: list[dict[str, Any]] = manifest["cases"]

    class_ids = [item["class_id"] for item in classes]
    _require_unique(class_ids, "class ID")
    if set(class_ids) != INITIAL_CLASS_IDS:
        missing = sorted(INITIAL_CLASS_IDS - set(class_ids))
        extra = sorted(set(class_ids) - INITIAL_CLASS_IDS)
        raise ConformanceManifestError(
            f"initial class set mismatch; missing={missing}, extra={extra}"
        )

    case_ids = [item["case_id"] for item in cases]
    _require_unique(case_ids, "case ID")
    case_by_id = {item["case_id"]: item for item in cases}

    for class_def in classes:
        for rule_ref in class_def["normative_references"]:
            _validate_rule_ref(rule_ref)
        for case_id in class_def["required_case_ids"]:
            case = case_by_id.get(case_id)
            if case is None:
                raise ConformanceManifestError(
                    f"{class_def['class_id']} requires missing case {case_id}"
                )
            if class_def["class_id"] not in case["class_ids"]:
                raise ConformanceManifestError(
                    f"{case_id} is required by {class_def['class_id']} but does not name that class"
                )
            if class_def["status"] in {"released", "candidate"} and case["requirement"] != "required":
                raise ConformanceManifestError(
                    f"released/candidate class {class_def['class_id']} cannot require provisional case {case_id}"
                )
        if class_def["status"] == "blocked" and not class_def.get("blocked_by"):
            raise ConformanceManifestError(
                f"blocked class {class_def['class_id']} must identify blocked_by"
            )

    for case in cases:
        for rule_ref in case["rule_refs"]:
            _validate_rule_ref(rule_ref)
        test_file = ROOT / case["test"]["file"]
        if not test_file.is_file():
            raise ConformanceManifestError(
                f"{case['case_id']} references missing test file {case['test']['file']}"
            )
        for fixture in case.get("fixtures", []):
            if not (ROOT / fixture).exists():
                raise ConformanceManifestError(
                    f"{case['case_id']} references missing fixture {fixture}"
                )


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest = _read_json(path)
    _validate_schema(manifest)
    _validate_integrity(manifest)
    return manifest


def _load_test_module(relative_path: str, cache: dict[str, Any]) -> Any:
    if relative_path in cache:
        return cache[relative_path]
    path = ROOT / relative_path
    module_name = "_conformance_" + relative_path.replace("/", "_").replace(".", "_")
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ConformanceManifestError(f"cannot import test module {relative_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cache[relative_path] = module
    return module


def _run_case(case: dict[str, Any], cache: dict[str, Any]) -> CaseResult:
    test_ref = case["test"]
    try:
        module = _load_test_module(test_ref["file"], cache)
        test_class = getattr(module, test_ref["test_class"])
        test = test_class(test_ref["test_method"])
    except (AttributeError, TypeError, ValueError, ConformanceManifestError) as exc:
        return CaseResult(case["case_id"], "FAIL", f"cannot load test: {exc}")

    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=0).run(unittest.TestSuite([test]))
    if result.skipped:
        reasons = "; ".join(reason for _, reason in result.skipped)
        return CaseResult(case["case_id"], "FAIL", f"required test skipped: {reasons}")
    if not result.wasSuccessful():
        detail = stream.getvalue().strip().replace("\n", " | ")
        return CaseResult(case["case_id"], "FAIL", detail)
    return CaseResult(case["case_id"], "PASS")


def _selected_classes(
    manifest: dict[str, Any], requested: list[str], include_blocked: bool
) -> list[dict[str, Any]]:
    classes = {item["class_id"]: item for item in manifest["classes"]}
    unknown = sorted(set(requested) - classes.keys())
    if unknown:
        raise ConformanceManifestError(f"unknown class ID(s): {', '.join(unknown)}")

    selected = [classes[class_id] for class_id in requested] if requested else list(classes.values())
    blocked_requested = [item for item in selected if item["status"] == "blocked"]
    if requested and blocked_requested and not include_blocked:
        reasons = []
        for item in blocked_requested:
            reasons.append(f"{item['class_id']}: {', '.join(item.get('blocked_by', []))}")
        raise ConformanceManifestError(
            "blocked conformance class selected; use --include-blocked only for provisional measurement: "
            + " | ".join(reasons)
        )
    if not include_blocked:
        selected = [item for item in selected if item["status"] != "blocked"]
    return sorted(selected, key=lambda item: item["class_id"])


def _select_cases(
    manifest: dict[str, Any], classes: list[dict[str, Any]], requested_cases: list[str]
) -> list[dict[str, Any]]:
    cases = {item["case_id"]: item for item in manifest["cases"]}
    active_class_ids = {item["class_id"] for item in classes}

    if requested_cases:
        unknown = sorted(set(requested_cases) - cases.keys())
        if unknown:
            raise ConformanceManifestError(f"unknown case ID(s): {', '.join(unknown)}")
        selected = [cases[case_id] for case_id in requested_cases]
        outside = [
            case["case_id"]
            for case in selected
            if active_class_ids.isdisjoint(case["class_ids"])
        ]
        if outside:
            raise ConformanceManifestError(
                "requested cases are outside selected classes: " + ", ".join(sorted(outside))
            )
        return sorted(selected, key=lambda item: item["case_id"])

    required: set[str] = set()
    for class_def in classes:
        required.update(class_def["required_case_ids"])
    return [cases[case_id] for case_id in sorted(required)]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run versioned magical-language conformance cases")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="path to ConformanceManifest JSON",
    )
    parser.add_argument(
        "--class",
        dest="classes",
        action="append",
        default=[],
        choices=sorted(INITIAL_CLASS_IDS),
        help="run one conformance class; repeatable",
    )
    parser.add_argument(
        "--case",
        dest="cases",
        action="append",
        default=[],
        help="run one stable conformance case ID; repeatable",
    )
    parser.add_argument(
        "--include-blocked",
        action="store_true",
        help="execute blocked/provisional class cases for measurement; never changes class status",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="validate and list class/case status without executing tests",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        manifest = load_manifest(args.manifest.resolve())
        classes = _selected_classes(manifest, args.classes, args.include_blocked)
        cases = _select_cases(manifest, classes, args.cases)
    except ConformanceManifestError as exc:
        print(f"CONFORMANCE ERROR: {exc}", file=sys.stderr)
        return 2

    print(
        f"suite={manifest['suite']['suite_id']} "
        f"version={manifest['suite']['suite_version']} "
        f"release_target={manifest['suite']['release_target']}"
    )
    for class_def in sorted(manifest["classes"], key=lambda item: item["class_id"]):
        blocked = ""
        if class_def["status"] == "blocked":
            blocked = " blocked_by=" + "; ".join(class_def.get("blocked_by", []))
        print(f"CLASS {class_def['class_id']} {class_def['status']}{blocked}")

    if args.list:
        for case in sorted(manifest["cases"], key=lambda item: item["case_id"]):
            print(
                f"CASE {case['case_id']} requirement={case['requirement']} "
                f"classes={','.join(case['class_ids'])}"
            )
        return 0

    module_cache: dict[str, Any] = {}
    results = [_run_case(case, module_cache) for case in cases]
    for result in results:
        suffix = f" — {result.detail}" if result.detail else ""
        print(f"{result.status} {result.case_id}{suffix}")

    failures = [result for result in results if result.status != "PASS"]
    print(f"RESULT passed={len(results) - len(failures)} failed={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
