from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r"#\d+(?![-A-Za-z0-9_])")
QUALIFIED_PREFIX = re.compile(
    r"(?:"
    r"public (?:Issue|Issues|PR|PRs) "
    r"|pre-public archive (?:Issue|Issues|PR|PRs|draft PR) "
    r"|pre-public CI [^\r\n]{0,80} run "
    r")$"
)


class TrackerReferenceNamespaceTests(unittest.TestCase):
    def test_live_markdown_numeric_references_are_namespaced(self) -> None:
        failures: list[str] = []
        for path in sorted(ROOT.rglob("*.md")):
            if "spec" in path.relative_to(ROOT).parts:
                continue
            text = path.read_text(encoding="utf-8")
            for line_number, line in enumerate(text.splitlines(), start=1):
                for match in TOKEN.finditer(line):
                    prefix = line[: match.start()]
                    if not QUALIFIED_PREFIX.search(prefix):
                        failures.append(
                            f"{path.relative_to(ROOT)}:{line_number}: {line.strip()}"
                        )
        self.assertEqual([], failures, "unqualified numeric tracker references")

    def test_historical_snapshots_are_excluded_but_present(self) -> None:
        snapshots = sorted((ROOT / "spec").glob("*.md"))
        self.assertTrue(snapshots)
        self.assertTrue(any(TOKEN.search(path.read_text(encoding="utf-8")) for path in snapshots))


if __name__ == "__main__":
    unittest.main()
