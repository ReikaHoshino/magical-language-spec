# Public tracker reference inventory

**Status:** traceability inventory for public Issue #15. This document defines no language, runtime, conformance, or release semantics.

The clean-history public repository has its own Issue and PR number namespace. Current live documents therefore identify the namespace at every tracker reference instead of relying on an unqualified `#N`.

## Classification

| Reference class | Required spelling | Current inventory |
|---|---|---|
| Current public work | `public Issue #N` | public Issue #1, public Issue #2, public Issue #3, public Issue #4, public Issue #15, public Issue #16 |
| Completed public repository changes | `public PR #N` | public PR #5, public PR #8, public PR #9, public PR #10 |
| Pre-migration tracker evidence | `pre-public archive Issue #N` / `pre-public archive PR #N` | all retained private-archive tracker references in current `reference/`, planning, examples, README, CHANGELOG, and TODO |
| Pre-migration CI evidence | `pre-public CI ... run #N` | repository-regression, package-smoke, runtime-smoke, and related run identifiers; these are not Issue or PR numbers |
| Immutable release evidence | original historical spelling | `spec/` only; snapshots are intentionally excluded from rewriting and from the live-document regression check |

The public Issue set is mutable GitHub state. The list above records the references present when public Issue #15 was implemented; it is not an allowlist that prevents later public Issues or PRs from being named. New current references remain valid when they use the explicit `public Issue/PR #N` spelling.

## Regression boundary

`tests/test_tracker_reference_namespace.py` scans every Markdown file outside immutable `spec/` snapshots. Each numeric `#N` token must be immediately owned by one of the four classes above. This rejects newly introduced unqualified `Issue #N`, `PR #N`, compact `#N` shorthand, and ambiguous numeric ranges while allowing explicitly classified historical CI runs.

The check intentionally does not rewrite or validate the prose inside `spec/`. Historical snapshots retain their released bytes and their original pre-public tracker spelling.
