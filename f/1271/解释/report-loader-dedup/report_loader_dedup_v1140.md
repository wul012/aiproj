# MiniGPT report loader dedup v1140

- Generated: `2026-07-10T01:00:45Z`
- Status: `pass`
- Decision: `report_loader_dedup_ready`

## Summary

| Metric | Value |
| --- | --- |
| dedup_ready | True |
| read_json_report_definition_count | 454 |
| private_loader_copy_count | 496 |
| migrated_module_count | 14 |
| locate_and_read_migrated_module_count | 5 |
| governance_reader_migrated_module_count | 9 |
| migrated_private_loader_copy_count | 0 |
| left_for_future_count | 496 |
| boundary | contract_preserving_thin_wrappers_only |
| next_step | continue_opportunistic_loader_migration_without_bulk_rewrite |

## Migrated Report Loaders

| module | exists | requires_locate_helper | imports_locate_upstream_report | imports_read_json_object | private_loader_copy_present | status |
| --- | --- | --- | --- | --- | --- | --- |
| model_capability_regression_plan.py | True | True | True | True | False | migrated |
| model_capability_regression_inventory.py | True | True | True | True | False | migrated |
| model_capability_regression_suite_manifest.py | True | True | True | True | False | migrated |
| model_capability_regression_suite_readiness.py | True | True | True | True | False | migrated |
| model_capability_regression_followup_closeout.py | True | True | True | True | False | migrated |
| benchmark_scorecard_comparison.py | True | False | False | True | False | migrated |
| benchmark_scorecard_decision.py | True | False | False | True | False | migrated |
| training_scale_handoff.py | True | False | False | True | False | migrated |
| training_scale_promotion.py | True | False | False | True | False | migrated |
| training_scale_run_comparison.py | True | False | False | True | False | migrated |
| training_scale_run_decision.py | True | False | False | True | False | migrated |
| training_portfolio_comparison.py | True | False | False | True | False | migrated |
| promoted_training_scale_comparison.py | True | False | False | True | False | migrated |
| promoted_training_scale_decision.py | True | False | False | True | False | migrated |

## Recommendations

- Keep the old public locate/read_json_report names as compatibility wrappers.
- Migrate older report loaders in future maintenance batches only when touching their area.
- Use this report as refactor evidence, not model capability evidence.
