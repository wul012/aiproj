# aiproj A2 Coverage Ratchet

Version v1263 completes A2 from `docs/production-excellence-aiproj-brief.md`.

## Scope

A2 asks for pytest coverage in CI with a floor equal to the observed baseline
minus two points. The first measured full unittest coverage baseline after A1
is `90.98%`, recorded by the v1262 local coverage run.

The committed floor is:

```text
observed_baseline_percent = 90.98
fail_under = 88.98
```

The policy lives in `docs/static-analysis/coverage-floor.json`. The CI command,
workflow hygiene policy, project configuration tests, and maintainer docs must
all agree with that value.

## Boundary

This version does not add new tests only to inflate the percentage. It does not
change model experiments, cached artifacts, verdicts, or promotion boundaries.
It only turns the measured coverage baseline into a fail-closed CI ratchet.

## Command

```powershell
python -B scripts/run_test_coverage.py --out-dir runs/test-coverage --fail-under 88.98
```

## Evidence

The v1263 run writes `test_coverage_report.json`, CSV, Markdown, and HTML. The
report must show `status=pass`, `decision=continue_with_coverage_gate`, and a
line coverage value at or above `88.98`.

## Ratchet Policy

Future versions may raise `fail_under` after a fresh coverage run. Lowering the
floor is not a routine maintenance action; it requires an explicit review note
and a test change, so it cannot happen by editing only `.github/workflows/ci.yml`.
