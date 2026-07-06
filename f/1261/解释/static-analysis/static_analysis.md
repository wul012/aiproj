# MiniGPT staged static analysis

- Generated: `2026-07-06T13:07:36Z`
- Status: `pass`
- Decision: `continue_with_static_analysis_gate`
- Baseline: `docs\static-analysis\ruff-baseline.json`

## Summary

| Metric | Value |
| --- | --- |
| status | pass |
| decision | continue_with_static_analysis_gate |
| command_status | pass |
| current_issue_count | 545 |
| baseline_issue_count | 545 |
| new_issue_count | 0 |
| resolved_baseline_issue_count | 0 |
| strict_lint_issue_count | 0 |
| strict_format_status | pass |
| strict_path_count | 7 |

## Commands

| Command | Return Code |
| --- | --- |
| `D:\python\python.exe -m ruff check --output-format=json src scripts` | 1 |
| `D:\python\python.exe -m ruff format --check scripts/check_static_analysis.py scripts/check_archive_runs_inventory.py scripts/check_engineering_health.py scripts/_bootstrap.py scripts/_engineering_health.py src/minigpt/ci_workflow_hygiene.py src/minigpt/ci_workflow_hygiene_policy.py` | 0 |

## New Issues

| Path | Line | Code | Message |
| --- | ---: | --- | --- |
| none |  |  |  |

## Strict Lint Issues

| Path | Line | Code | Message |
| --- | ---: | --- | --- |
| none |  |  |  |
