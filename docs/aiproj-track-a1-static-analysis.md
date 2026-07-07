# aiproj A1 Static Analysis

Versions v1261-v1262 complete A1 from `docs/production-excellence-aiproj-brief.md`.

## Scope

A1 asks for ruff lint and format adoption without a repo-wide mechanical sweep. v1261 implements the first half of that requirement:

- ruff is declared in `requirements.txt`.
- `pyproject.toml` declares a Python 3.11 ruff target and a narrow lint rule set: `E4`, `E7`, `E9`, and `F`.
- `scripts/check_static_analysis.py` runs ruff over `src/` and `scripts/`.
- `docs/static-analysis/ruff-baseline.json` records existing historical findings.
- strict paths must be lint-clean and format-clean.
- CI runs the static-analysis gate before coverage.
- CI workflow hygiene now fails if the static-analysis gate is removed or moved after coverage.

v1262 completes the scoped typing half:

- mypy is declared in `requirements.txt` and strict settings live in `pyproject.toml`.
- `docs/static-analysis/mypy-scope.json` commits eight targets in four owner groups.
- `scope_floor=8` and group validation prevent silent scope shrinkage.
- `scripts/check_type_analysis.py` writes JSON/CSV/Markdown/HTML and fails on scope or type regressions.
- CI and engineering health run mypy after ruff; workflow hygiene protects both presence and order.
- `scripts/codex-bootstrap.ps1` is retained with ASCII-safe output and a focused contract test.

## Boundary

These versions do not run a whole-repository format or type sweep. They do not
claim that every historical experiment script has been cleaned. The mypy gate
uses `follow_imports=skip` so it checks the declared files only, and it does not
change science-lane experiment semantics.

## Baseline Result

The v1261 evidence run produced:

```text
status=pass
decision=continue_with_static_analysis_gate
current_issue_count=545
baseline_issue_count=545
new_issue_count=0
strict_lint_issue_count=0
strict_format_status=pass
```

The 545 findings are now reviewable debt, not invisible debt. New findings outside the committed baseline fail the gate.

## Evidence

The v1261 ruff evidence lives under `f/1261/解释/static-analysis/`. The v1262
mypy evidence lives under `f/1262/解释/type-analysis/`, with a visual report in
`f/1262/图片/`.
