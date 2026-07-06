# aiproj A1 Static Analysis

Version v1261 starts A1 from `docs/production-excellence-aiproj-brief.md`.

## Scope

A1 asks for ruff lint and format adoption without a repo-wide mechanical sweep. This version implements the first half of that requirement:

- ruff is declared in `requirements.txt`.
- `pyproject.toml` declares a Python 3.11 ruff target and a narrow lint rule set: `E4`, `E7`, `E9`, and `F`.
- `scripts/check_static_analysis.py` runs ruff over `src/` and `scripts/`.
- `docs/static-analysis/ruff-baseline.json` records existing historical findings.
- strict paths must be lint-clean and format-clean.
- CI runs the static-analysis gate before coverage.
- CI workflow hygiene now fails if the static-analysis gate is removed or moved after coverage.

## Boundary

This version does not run a whole-repository format sweep. It does not claim that every historical experiment script has been cleaned. It also does not introduce mypy yet; the load-bearing type-check scope remains the next A1 step.

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

Preserved evidence lives under `f/1261/解释/static-analysis/`. The HTML report screenshot is stored under `f/1261/图片/`.
