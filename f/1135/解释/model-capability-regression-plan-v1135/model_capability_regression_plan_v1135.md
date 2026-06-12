# MiniGPT model capability regression plan v1135

- Generated: `2026-06-12T02:42:06Z`
- Status: `pass`
- Decision: `model_capability_regression_plan_ready`

## Summary

| Metric | Value |
| --- | --- |
| plan_ready | True |
| regression_item_count | 4 |
| source_status | watch |
| source_next_action | schedule_model_capability_regression |
| leading_non_capability_run | 12 |
| max_non_capability_run | 4 |
| promotion_ready | False |
| model_quality_claim | plan_only |
| next_step | inventory_model_capability_regression_evidence_v1136 |
| passed_check_count | 5 |
| failed_check_count | 0 |

## Regression Plan Items

| check_id | scope | evidence_kind | status | reason |
| --- | --- | --- | --- | --- |
| required_term_coverage | surface | coverage | planned | Verify required terms are still visible in bounded prompts. |
| loss_signal_bridge | training-signal | diagnostic | planned | Reconnect governance cadence to a measurable loss or score signal. |
| decoder_anchor_distribution | decoder | distribution | planned | Inspect whether generated anchors remain bounded instead of echoing templates. |
| holdout_scorecard_smoke | holdout | scorecard | planned | Keep a small holdout scorecard in the loop after receipt-heavy runs. |

## Recommendations

- Run a small model capability regression before adding more receipt-only versions.
- Keep the regression bounded: required terms, loss signal, decoder anchor, and holdout scorecard.
- Do not treat this plan as model improvement evidence; it only schedules the checks.
