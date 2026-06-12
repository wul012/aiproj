# MiniGPT model capability regression evidence inventory v1136

- Generated: `2026-06-12T02:47:05Z`
- Status: `pass`
- Decision: `model_capability_regression_inventory_ready`

## Summary

| Metric | Value |
| --- | --- |
| inventory_ready | True |
| planned_item_count | 4 |
| ready_item_count | 4 |
| source_plan_ready | True |
| promotion_ready | False |
| model_quality_claim | inventory_only |
| next_step | build_model_capability_regression_suite_manifest_v1137 |
| passed_check_count | 6 |
| failed_check_count | 0 |

## Regression Evidence Inventory

| check_id | script_count | source_count | test_count | artifact_count | status | recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| required_term_coverage | 155 | 321 | 160 | 0 | ready | reuse existing evidence path |
| loss_signal_bridge | 46 | 92 | 46 | 0 | ready | reuse existing evidence path |
| decoder_anchor_distribution | 17 | 34 | 17 | 0 | ready | reuse existing evidence path |
| holdout_scorecard_smoke | 240 | 480 | 244 | 30 | ready | reuse existing evidence path |

## Recommendations

- Use ready inventory rows to build a small regression suite manifest.
- Prefer existing scripts and tests before adding new capability machinery.
- Keep this as evidence availability, not a model quality result.
