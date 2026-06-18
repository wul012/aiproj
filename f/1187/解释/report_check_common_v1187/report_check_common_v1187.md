# MiniGPT v1187 report-check scaffolding dedup

- Generated: `v1187`
- Status: `pass`
- Decision: `report_check_scaffolding_deduplicated`

## Summary

| Metric | Value |
| --- | --- |
| new_module | src/minigpt/report_check_common.py |
| extracted | check_row, collect_failures, resolve_exit_code |
| callers_migrated | 4 |
| duplicated_pieces_removed_per_module | 3 |
| focused_tests | 25 passed (4 audit modules unchanged + report_check_common, incl. single-source identity guards) |
| contract_preserving | True |
| boundary | behavior_identical_no_new_science_pure_maintenance |

## Migrated Modules

| module | removed_check_builder | removed_exit_code | removed_failures_comp | now_imports_from |
| --- | --- | --- | --- | --- |
| grok_evidence_check_v1180 | _check | resolve_exit_code | True | report_check_common |
| grok_trajectory_phases_v1181 | _check | resolve_exit_code | True | report_check_common |
| grok_paired_contrast_v1182 | _check | resolve_exit_code | True | report_check_common |
| grok_wd_law_check_v1184 | _check | resolve_exit_code | True | report_check_common |

## Recommendations

- All four grokking-audit modules now share report_check_common for the check-row builder, failures collector, and require-pass exit code.
- Future report-check modules (incl. the PTQ checks v1177/v1178, left untouched here) should import these helpers instead of re-pasting them.
