# MiniGPT Static, Type, And Coverage Gates

This page documents the staged ruff, scoped mypy, and coverage-ratchet adoption introduced by the production-excellence A-track.

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

## v1262 Scoped Mypy Gate

The second A1 step adds strict mypy without attempting a full-repository type
sweep. The committed scope lives in
`docs/static-analysis/mypy-scope.json`. It currently contains twelve
load-bearing files in four groups: shared report contracts, CI governance,
engineering orchestration, analysis gates, and honest measurement.

Run it with:

```powershell
python -B scripts/check_type_analysis.py --out-dir runs/type-analysis
```

The checker validates the scope before invoking mypy. Every target must exist,
must be a Python file inside the repository, must be unique, and must belong to
a named group. `scope_floor=12` prevents the checked surface from being reduced
without a visible policy change. The report writes JSON, CSV, Markdown, and
HTML with the exact target list, scope issues, and mypy diagnostics.

Mypy uses strict mode with `follow_imports=skip`. That setting is deliberate:
the gate checks the eight declared files rather than recursively turning this
incremental A1 version into a hidden full-repository migration. Future versions
may increase `scope_floor` and add groups, but should not lower the floor.

## v1263 Coverage Floor Ratchet

A2 raises the CI coverage floor from the earlier conservative placeholder to
the measured baseline minus two points. The committed policy lives in
`docs/static-analysis/coverage-floor.json`:

```text
observed_baseline_percent = 90.98
fail_under = 88.98
```

CI now runs:

```powershell
python -B scripts/run_test_coverage.py --out-dir runs/test-coverage-ci --fail-under 88.98
```

`tests/test_project_configuration.py` checks that the workflow, the committed
coverage-floor manifest, and `ci_workflow_hygiene_policy.py` agree on the same
floor. Future versions may raise this value with fresh evidence, but lowering
it requires changing the manifest and tests, not just editing the workflow.

## v1264 Honest Measurement Gate

A3 adds a separate gate for bounded model-capability governance claims:

```powershell
python -B scripts/check_model_capability_honest_measurement.py --out-dir runs/model-capability-honest-measurement
```

The registry lives at
`docs/model-capability-honest-measurement-registry.json`. The checker validates
that registered families are cached-artifact-only, require no training, carry no
promotion authority, keep single-seed stochastic evidence exploratory/no-promotion,
point at existing source artifacts, and retain positive plus negative contract
test markers. CI runs this gate after scoped type analysis and before coverage.

## v1265 Artifact Schema Guard

A3 also adds a fail-closed schema guard for card and publication-receipt
artifacts:

```powershell
python -B scripts/check_artifact_schema_guard.py --out-dir runs/artifact-schema-guard
```

The registry lives at `docs/artifact-schema-guard-registry.json`. The checker
validates current experiment-card, dataset-card, model-card, and publication
receipt envelopes against required fields, selected expected values, and simple
field types. CI runs this gate after honest measurement and before coverage.
