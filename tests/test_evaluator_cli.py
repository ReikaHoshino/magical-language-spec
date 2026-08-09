from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from src.evaluator.cli import main
from src.evaluator.schema import ROOT


class EvaluatorCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pipeline = json.loads(
            (ROOT / "examples" / "canonical-water-ball" / "pipeline.json").read_text(
                encoding="utf-8"
            )
        )
        cls.canonical_nsr = pipeline["normalization"]["nsr"]

    def test_nsr_json_machine_output_is_deterministic_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "nsr.json"
            path.write_text(json.dumps(self.canonical_nsr), encoding="utf-8")

            first = io.StringIO()
            with redirect_stdout(first):
                self.assertEqual(
                    0,
                    main(["--nsr", str(path), "--format", "json", "--level", "report"]),
                )

            second = io.StringIO()
            with redirect_stdout(second):
                self.assertEqual(
                    0,
                    main(["--nsr", str(path), "--format", "json", "--level", "report"]),
                )

        self.assertEqual(first.getvalue(), second.getvalue())
        report = json.loads(first.getvalue())
        self.assertEqual(report["status"], "ConditionallyFeasible")
        self.assertEqual(report["input"]["kind"], "NSR")

    def test_latin_human_output_uses_explicit_reference_adapter(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(
                0,
                main(
                    [
                        "--source",
                        "Calorem ab aqua ad aerem transfer.",
                        "--lang",
                        "lat",
                        "--format",
                        "human",
                        "--level",
                        "report",
                    ]
                ),
            )
        rendered = output.getvalue()
        self.assertIn("Status: Indeterminate", rendered)
        self.assertIn("Input: NaturalLanguageSource", rendered)

    def test_surface_level_is_available_for_latin_ingress(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(
                0,
                main(
                    [
                        "--source",
                        "Calorem ab aqua ad aerem transfer.",
                        "--lang",
                        "lat",
                        "--format",
                        "json",
                        "--level",
                        "surface",
                    ]
                ),
            )
        surface = json.loads(output.getvalue())
        self.assertIsInstance(surface, dict)
        self.assertEqual(surface["status"], "Accepted")
        self.assertEqual(
            surface["output"]["normalized_text"],
            "Calorem ab aqua ad aerem transfer.",
        )

    def test_cli_requires_explicit_language_for_source(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as missing_lang:
            main(["--source", "aquae"])
        self.assertEqual(missing_lang.exception.code, 2)

    def test_cli_requires_exactly_one_public_ingress_kind(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as missing:
            main([])
        self.assertEqual(missing.exception.code, 2)

        with redirect_stderr(stderr), self.assertRaises(SystemExit) as duplicate:
            main(
                [
                    "--source",
                    "aquae",
                    "--lang",
                    "lat",
                    "--nsr",
                    "fixture.json",
                ]
            )
        self.assertEqual(duplicate.exception.code, 2)

    def test_cli_rejects_language_on_nsr_ingress(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as invalid:
            main(["--nsr", "fixture.json", "--lang", "lat"])
        self.assertEqual(invalid.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
