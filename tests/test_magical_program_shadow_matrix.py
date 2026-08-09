from __future__ import annotations

import inspect
import json
import unittest
from pathlib import Path

from src.migration.legacy_program_oracle import (
    default_shadow_translators,
    run_shadow_file,
)
from tools.package_program_shadow_smoke import run as run_package_smoke

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "conformance" / "magical-program-shadow-migration.json"
GOLDEN = ROOT / "conformance" / "magical-program-golden-parity.json"


class MagicalProgramShadowMatrixTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.manifest = json.loads(INVENTORY.read_text(encoding="utf-8"))

    def test_all_12_current_bundles_pass_the_complete_current_suite(self) -> None:
        results = []
        for item in sorted(
            self.manifest["inventory"], key=lambda row: row["order"]
        ):
            with self.subTest(migration_id=item["migration_id"]):
                result = run_shadow_file(
                    ROOT / item["path"], golden_manifest=GOLDEN
                )
                self.assertEqual("PASS", result["status"], result)
                results.append((item, result))

        self.assertEqual(12, len(results))
        self.assertEqual(
            {
                "implemented": 5,
                "adversarial": 3,
                "recognized-unsupported": 4,
            },
            {
                classification: sum(
                    item["classification"] == classification
                    for item, _ in results
                )
                for classification in (
                    "implemented",
                    "adversarial",
                    "recognized-unsupported",
                )
            },
        )
        self.assertEqual(
            12,
            len(default_shadow_translators().pairs()),
        )

    def test_expected_runtime_shape_matches_inventory_classification(self) -> None:
        for item in self.manifest["inventory"]:
            result = run_shadow_file(ROOT / item["path"], golden_manifest=GOLDEN)
            execution = result["generic_execution"]
            replay = result["generic_replay"]
            with self.subTest(migration_id=item["migration_id"]):
                if item["classification"] == "implemented":
                    self.assertEqual("Committed", execution["status"])
                    self.assertEqual("Match", replay["status"])
                elif item["classification"] == "recognized-unsupported":
                    self.assertIsNone(execution)
                    self.assertIsNone(replay)
                    self.assertEqual(
                        "Indeterminate",
                        result["raw_evaluation_status"]["generic"],
                    )
                elif item["migration_id"] == "MIG-DEBUG-HELL-001":
                    self.assertIsNone(execution)
                    self.assertIsNone(replay)
                    self.assertEqual(
                        "Infeasible",
                        result["raw_evaluation_status"]["generic"],
                    )
                else:
                    self.assertEqual("Aborted", execution["status"])
                    self.assertEqual("DeterministicAbort", replay["status"])

    def test_package_smoke_uses_the_same_complete_matrix(self) -> None:
        payload = run_package_smoke()
        self.assertEqual("PASS", payload["status"], payload)
        self.assertEqual(12, payload["case_count"])
        self.assertEqual(0, payload["failure_count"])
        self.assertEqual(
            {
                "implemented": 5,
                "adversarial": 3,
                "recognized-unsupported": 4,
            },
            payload["classification_counts"],
        )

    def test_no_current_translator_or_executor_dispatches_by_fixture_identity(self) -> None:
        migration_root = ROOT / "src" / "migration"
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(
                migration_root.glob("magical_program_shadow*.py")
            )
        )
        forbidden = (
            "suite_id ==",
            "instance_id ==",
            "path.name",
            "filename ==",
            "DEBUG-HELL-001.json",
            "DEBUG-HELL-002.json",
            "DEBUG-HELL-003.json",
            "SA-001.json",
            "SA-002.json",
            "SA-003.json",
            "SA-004.json",
            "embedded_payload",
            "shadow.spell-instance",
            "base64.b64decode",
            "base64.b64encode",
        )
        for token in forbidden:
            self.assertNotIn(token, source)

        registry_source = inspect.getsource(default_shadow_translators)
        self.assertNotIn("suite_id", registry_source)
        self.assertNotIn("instance_id", registry_source)
        self.assertNotIn("filename", registry_source)


if __name__ == "__main__":
    unittest.main()
