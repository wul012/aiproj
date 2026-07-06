# MiniGPT Static Analysis Gate

This page documents the staged ruff adoption introduced by the production-excellence A-track.

## Purpose

`scripts/check_static_analysis.py` makes ruff a committed quality gate without pretending the long historical tree is already clean. The gate runs on `src/` and `scripts/`, compares current ruff findings against `docs/static-analysis/ruff-baseline.json`, and fails when a new finding appears outside that baseline.

The same command also keeps a strict path list. Files in the strict list must have zero ruff lint findings and must pass `ruff format --check`. This protects new and actively maintained A-track code while the older 1000+ version history is paid down in batches.

## Command

```powershell
python -B scripts/check_static_analysis.py --out-dir runs/static-analysis
```

To refresh the baseline after an intentional contract-preserving cleanup:

```powershell
python -B scripts/check_static_analysis.py --out-dir runs/static-analysis --update-baseline
```

Baseline updates should only reduce or intentionally re-key known historical findings. Do not use `--update-baseline` to hide a new violation in touched code.

## Outputs

The checker writes:

- `static_analysis.json`
- `static_analysis_issues.csv`
- `static_analysis.md`
- `static_analysis.html`

The report includes `current_issue_count`, `baseline_issue_count`, `new_issue_count`, `resolved_baseline_issue_count`, `strict_lint_issue_count`, and `strict_format_status`.

## v1261 Baseline

The first committed baseline records 545 historical ruff findings across `src/` and `scripts/`. The strict path set is clean: `new_issue_count=0`, `strict_lint_issue_count=0`, and `strict_format_status=pass`.

This is an engineering gate, not a model-capability claim. It improves maintainability and CI regression detection, but it does not change training semantics, cached experiment verdicts, or promotion boundaries.
