from __future__ import annotations

import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class PreV08IntegrationTests(unittest.TestCase):
    def test_resume_point_and_release_train_are_current(self) -> None:
        todo = read("TODO.md")
        self.assertIn(
            "pre-public archive Issue #36 — v0.8 Minimal Local Evaluator", todo
        )
        sequence = [
            "pre-public archive Issue #36 v0.8 Minimal Local Evaluator",
            "pre-public archive Issue #37 v0.9 Sandboxed Runtime",
            "pre-public archive Issue #40 v0.10+ Conformance / Stabilization",
            "pre-public archive Issue #38 v1.0.0-rc.N",
            "pre-public archive Issue #39 v1.0.0 final",
        ]
        positions = [todo.index(item) for item in sequence]
        self.assertEqual(positions, sorted(positions))
        for stale in (
            "### TODO — Issue #34 / IMPLEMENTATION BLOCKER",
            "READYなIssue #34を実行する",
            "Issue #17は#34完了後にREADY",
            "Issue #18は#17/#34完了後",
        ):
            self.assertNotIn(stale, todo)

    def test_completed_foundations_and_deferred_breadth_are_distinct(self) -> None:
        todo = read("TODO.md")
        for completed in (
            "DONE(contract + v0.8 implementation) — pre-public archive Issue #34 / pre-public archive Issue #36",
            "estimator model/profile ownership contract + deterministic synthetic profile",
            "水球生成をcanonical end-to-end例として仕様化",
            "canonical pathの仕様rule ↔ stable test/fixture ID traceability matrix",
        ):
            self.assertIn(completed, todo)
        self.assertIn("DEFERRED(non-reference adapter breadth)", todo)
        self.assertIn("DEFERRED(renderer/CLI breadth)", todo)
        self.assertIn("post-v1.0またはexperimental", todo)

    def test_handoff_defers_current_state_to_todo(self) -> None:
        handoff = read("PROJECT_HANDOFF.md")
        self.assertIn("current DONE / READY / BLOCKED状態をこの文書へ複製しない", handoff)
        self.assertIn("root `TODO.md` の `RESUME POINT` を正本として読む", handoff)
        self.assertIn("`AGENTS.md`", handoff)
        self.assertIn("`WORKFLOW.md`", handoff)
        self.assertNotIn("Issue #36 — v0.8 Minimal Local Evaluator", handoff)
        self.assertNotIn("current Wave、PR番号", handoff)

    def test_current_navigation_lists_pre_v08_artifacts(self) -> None:
        readme = read("README.md")
        required = (
            "reference/planning-inference.md",
            "reference/estimator-models.md",
            "reference/canonical-water-ball.md",
            "schemas/ambiguity-decision-trace.schema.json",
            "schemas/planning-inference.schema.json",
            "schemas/estimator-profile.schema.json",
            "schemas/canonical-water-ball.schema.json",
            "examples/canonical-water-ball/",
        )
        for relative in required:
            self.assertIn(relative, readme)
            self.assertTrue((ROOT / relative).exists(), relative)

    def test_changelog_and_consistency_checkpoint_cover_final_gate(self) -> None:
        changelog = read("CHANGELOG.md")
        for issue in (12, 13, 14, 15, 16, 17, 18, 19, 20, 34):
            self.assertIn(f"pre-public archive Issue #{issue}", changelog)
        report = read("reference/consistency-report.md")
        self.assertIn(
            "Final pre-v0.8 integration audit — pre-public archive Issue #19",
            report,
        )
        self.assertIn("pre-v0.8 specification/readiness gate = PASS", report)
        self.assertIn(
            "next RESUME POINT = pre-public archive Issue #36", report
        )

    def test_v08_entry_and_water_ball_conformance_boundaries_are_explicit(self) -> None:
        todo = read("TODO.md")
        self.assertIn("v0.8 public input boundary", todo)
        self.assertIn("reference `LanguageAdapter<lat>` path", todo)
        self.assertIn("schema-validなNSR JSON", todo)
        self.assertIn("stableな外部direct-entry contractとはしない", todo)
        self.assertIn("multi-stage direct ingestion", todo)
        self.assertIn("pre-public archive Issue #48", todo)
        self.assertNotIn("- NSR / SemanticAST。", todo)
        self.assertNotIn("- Typed MIR / NormalizedIR。", todo)

        canonical = read("reference/canonical-water-ball.md")
        self.assertIn("選択済みNSR /", canonical)
        self.assertIn("`eng` source→NSR adapterを実装・検証済みであるとは主張しない", canonical)
        self.assertIn("source→NSR frontend conformanceはreference `lat` corpus", canonical)

        report = read("reference/consistency-report.md")
        self.assertIn("v0.8 input / canonical conformance clarification", report)
        self.assertIn("Issue #48はfuture architecture issue", report)

    def test_historical_v073_snapshot_remains_immutable(self) -> None:
        snapshot = (ROOT / "spec" / "v0.7.3.md").read_bytes().replace(
            b"\r\n", b"\n"
        )
        digest = hashlib.sha256(snapshot).hexdigest()
        self.assertEqual(
            "bedc6c6668daadca13d0d736c50d3c11c700980a0d0462a857a88c9b3ad8312a",
            digest,
        )
        todo = read("TODO.md")
        self.assertIn("2026-07-29T05:35:45+09:00", todo)


if __name__ == "__main__":
    unittest.main()
