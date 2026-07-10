# MiniGPT engineering health summary

- Generated: `2026-07-10T02:14:55Z`
- Status: `pass`
- Decision: `engineering_health_ready`

## Summary

| Metric | Value |
| --- | --- |
| step_count | 10 |
| passed_step_count | 10 |
| failed_step_count | 0 |
| first_failure_code | 0 |
| output_root | D:\aiproj\runs\engineering-health-v1272 |

## Steps

| Step | Status | Return Code | Command |
| --- | --- | --- | --- |
| source_encoding | pass | 0 | `D:\python\python.exe -B scripts/check_source_encoding.py --out-dir D:\aiproj\runs\engineering-health-v1272\source-encoding` |
| project_docs_readability | pass | 0 | `D:\python\python.exe -B scripts/check_project_docs_readability.py --out-dir D:\aiproj\runs\engineering-health-v1272\project-docs-readability --require-pass --force` |
| ci_workflow_hygiene | pass | 0 | `D:\python\python.exe -B scripts/check_ci_workflow_hygiene.py --out-dir D:\aiproj\runs\engineering-health-v1272\ci-workflow-hygiene` |
| static_analysis | pass | 0 | `D:\python\python.exe -B scripts/check_static_analysis.py --out-dir D:\aiproj\runs\engineering-health-v1272\static-analysis` |
| type_analysis | pass | 0 | `D:\python\python.exe -B scripts/check_type_analysis.py --out-dir D:\aiproj\runs\engineering-health-v1272\type-analysis` |
| model_capability_honest_measurement | pass | 0 | `D:\python\python.exe -B scripts/check_model_capability_honest_measurement.py --out-dir D:\aiproj\runs\engineering-health-v1272\model-capability-honest-measurement` |
| artifact_schema_guard | pass | 0 | `D:\python\python.exe -B scripts/check_artifact_schema_guard.py --out-dir D:\aiproj\runs\engineering-health-v1272\artifact-schema-guard` |
| file_size_ratchet | pass | 0 | `D:\python\python.exe -B scripts/check_file_size_ratchet.py --out-dir D:\aiproj\runs\engineering-health-v1272\file-size-ratchet` |
| aiproj_track_closeout | pass | 0 | `D:\python\python.exe -B scripts/check_aiproj_track_closeout.py --out-dir D:\aiproj\runs\engineering-health-v1272\aiproj-track-closeout` |
| normalization_guard | pass | 0 | `D:\python\python.exe -B scripts/check_normalization_guard.py` |
