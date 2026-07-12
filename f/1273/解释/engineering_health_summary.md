# MiniGPT engineering health summary

- Generated: `2026-07-12T02:09:33Z`
- Status: `pass`
- Decision: `engineering_health_ready`

## Summary

| Metric | Value |
| --- | --- |
| step_count | 11 |
| passed_step_count | 11 |
| failed_step_count | 0 |
| first_failure_code | 0 |
| output_root | D:\aiproj\runs\engineering-health-v1273-final |

## Steps

| Step | Status | Return Code | Command |
| --- | --- | --- | --- |
| source_encoding | pass | 0 | `D:\python\python.exe -B scripts/check_source_encoding.py --out-dir D:\aiproj\runs\engineering-health-v1273-final\source-encoding` |
| project_docs_readability | pass | 0 | `D:\python\python.exe -B scripts/check_project_docs_readability.py --out-dir D:\aiproj\runs\engineering-health-v1273-final\project-docs-readability --require-pass --force` |
| ci_workflow_hygiene | pass | 0 | `D:\python\python.exe -B scripts/check_ci_workflow_hygiene.py --out-dir D:\aiproj\runs\engineering-health-v1273-final\ci-workflow-hygiene` |
| static_analysis | pass | 0 | `D:\python\python.exe -B scripts/check_static_analysis.py --out-dir D:\aiproj\runs\engineering-health-v1273-final\static-analysis` |
| name_budget | pass | 0 | `D:\python\python.exe -B scripts/check_name_budget.py --out-dir D:\aiproj\runs\engineering-health-v1273-final\name-budget` |
| type_analysis | pass | 0 | `D:\python\python.exe -B scripts/check_type_analysis.py --out-dir D:\aiproj\runs\engineering-health-v1273-final\type-analysis` |
| model_capability_honest_measurement | pass | 0 | `D:\python\python.exe -B scripts/check_model_capability_honest_measurement.py --out-dir D:\aiproj\runs\engineering-health-v1273-final\model-capability-honest-measurement` |
| artifact_schema_guard | pass | 0 | `D:\python\python.exe -B scripts/check_artifact_schema_guard.py --out-dir D:\aiproj\runs\engineering-health-v1273-final\artifact-schema-guard` |
| file_size_ratchet | pass | 0 | `D:\python\python.exe -B scripts/check_file_size_ratchet.py --out-dir D:\aiproj\runs\engineering-health-v1273-final\file-size-ratchet` |
| aiproj_track_closeout | pass | 0 | `D:\python\python.exe -B scripts/check_aiproj_track_closeout.py --out-dir D:\aiproj\runs\engineering-health-v1273-final\aiproj-track-closeout` |
| normalization_guard | pass | 0 | `D:\python\python.exe -B scripts/check_normalization_guard.py` |
