# MiniGPT holdout scorecard smoke v1144

- Generated: `2026-06-12T10:48:11Z`
- Status: `pass`
- Decision: `model_capability_holdout_scorecard_smoke_ready`

## Summary

| Metric | Value |
| --- | --- |
| holdout_scorecard_smoke_ready | True |
| case_count | 5 |
| executed_case_count | 5 |
| passed_case_count | 5 |
| failed_case_count | 0 |
| scorecard_overall_status | pass |
| scorecard_overall_score | 97.0 |
| rubric_avg_score | 100.0 |
| generation_quality_status | pass |
| pair_same_checkpoint_baseline | True |
| model_quality_claim | holdout_scorecard_smoke_real_execution |
| promotion_ready | False |
| next_step | run_loss_signal_bridge_and_decoder_anchor_distribution_v1145 |
| failed_check_count | 0 |

## Real Holdout Scorecard Smoke Rows

| case_id | task_type | difficulty | prompt | continuation | hit_terms | missed_terms | case_pass | rubric_score | generation_error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| holdout-scorecard-qa-easy | qa | easy | answer the holdout signal using fixed loss answer: |  fixed loss | fixed, loss |  | True | 100.0 |  |
| holdout-scorecard-summary-medium | summary | medium | summarize the holdout signal with fixed loss summary: |  fixed loss | fixed, loss |  | True | 100.0 |  |
| holdout-scorecard-continuation-hard | continuation | hard | continue the calibration phrase fixed loss continuation: |  fixed loss | fixed, loss |  | True | 100.0 |  |
| holdout-scorecard-qa-hard | qa | hard | state the required scorecard terms fixed loss answer: |  fixed loss | fixed, loss |  | True | 100.0 |  |
| holdout-scorecard-summary-easy | summary | easy | brief summary must include fixed loss summary: |  fixed loss | fixed, loss |  | True | 100.0 |  |

## Recommendations

- Treat v1144 as a real holdout scorecard smoke, not as a promotion decision.
- Use v1145 to add loss_signal_bridge and decoder_anchor_distribution real evidence.
