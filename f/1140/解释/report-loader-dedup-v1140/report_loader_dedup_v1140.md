# MiniGPT report loader dedup v1140

- Generated: `2026-06-12T04:43:57Z`
- Status: `pass`
- Decision: `report_loader_dedup_ready`

## Summary

| Metric | Value |
| --- | --- |
| dedup_ready | True |
| read_json_report_definition_count | 431 |
| private_loader_copy_count | 439 |
| migrated_module_count | 5 |
| migrated_private_loader_copy_count | 0 |
| left_for_future_count | 439 |
| boundary | contract_preserving_thin_wrappers_only |
| next_step | build_model_capability_regression_trend_report_v1141 |

## Migrated Report Loaders

| module | exists | imports_locate_upstream_report | imports_read_json_object | private_loader_copy_present | status |
| --- | --- | --- | --- | --- | --- |
| model_capability_regression_plan.py | True | True | True | False | migrated |
| model_capability_regression_inventory.py | True | True | True | False | migrated |
| model_capability_regression_suite_manifest.py | True | True | True | False | migrated |
| model_capability_regression_suite_readiness.py | True | True | True | False | migrated |
| model_capability_regression_followup_closeout.py | True | True | True | False | migrated |

## Recommendations

- Keep the old public locate/read_json_report names as compatibility wrappers.
- Migrate older report loaders in future maintenance batches only when touching their area.
- Use this report as refactor evidence, not model capability evidence.
