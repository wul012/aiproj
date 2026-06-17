# MiniGPT grokking evidence check v1180

- Generated: `2026-06-17T08:47:17Z`
- Status: `pass`
- Decision: `grokking_evidence_claim_reconstructed`

## Summary

| Metric | Value |
| --- | --- |
| evidence_check_ready | True |
| source_status | pass |
| source_decision | grokking_reproduced_wd_driven |
| source_verdict | grokking_reproduced_wd_driven |
| source_grok_report | f\1179\解释\grok_v1179\grok_v1179.json |
| seed_count | 5 |
| row_count | 10 |
| weight_decay_on | 1.0 |
| weight_decay_off | 0.0 |
| wd_on_mem_count | 5 |
| wd_on_grok_count | 5 |
| wd_off_mem_count | 5 |
| wd_off_grok_count | 0 |
| wd_on_mean_gap | 14780.0 |
| wd_on_mean_val_at_mem | 0.14693769365549086 |
| summary_wd_on_grok_rate | 1.0 |
| summary_wd_off_grok_rate | 0.0 |
| min_delay_steps | 1000 |
| max_val_at_mem | 0.5 |
| boundary | artifact_reconstruction_only_no_training_rerun |
| next_step | use_v1179_as_positive_training_dynamics_anchor_if_check_passes |

## Grok Evidence Checks

| id | status | expected | actual | detail |
| --- | --- | --- | --- | --- |
| source_status_pass | pass | pass | pass | source report must be a valid measurement |
| source_verdict_wd_driven | pass | grokking_reproduced_wd_driven | grokking_reproduced_wd_driven | v1179 headline claim is specifically weight-decay-driven grokking |
| seed_arm_grid_complete | pass | 5 rows per arm; total 10 | wd_on=5, wd_off=5, total=10 | each seed must have paired weight_decay on/off rows |
| wd_on_memorized_all | pass | 5 | 5 | with-decay arm must memorize all seeds before claiming delayed generalization |
| wd_on_grokked_all | pass | 5 | 5 | with-decay arm must grok all seeds for the v1179 strong positive claim |
| wd_off_memorized_all | pass | 5 | 5 | no-decay ablation should still memorize, separating optimization from generalization |
| wd_off_did_not_grok | pass | 0 | 0 | weight-decay-driven verdict requires the no-decay ablation not to grok within budget |
| delay_real | pass | mean_gap_at_least=1000, mean_val_at_mem_below=0.5 | mean_gap=14780.0, mean_val_at_mem=0.14693769365549086 | validation must remain low at memorization and generalize much later |
| summary_rates_match_rows | pass | wd_on_grok_rate=1.0, wd_off_grok_rate=0.0 | wd_on_grok_rate=1.0, wd_off_grok_rate=0.0 | summary grok rates must reconstruct from rows |
| boundary_present | pass | toy_scale_single_task_modular_addition_grokking_not_a_scaling_claim | toy_scale_single_task_modular_addition_grokking_not_a_scaling_claim | positive grokking result must keep its toy-scale boundary |

## Recommendations

- The v1179 grokking claim reconstructs from the archived rows: memorization is early, generalization is delayed, and the no-decay ablation stays ungrokked.
- Use v1179 as a positive training-dynamics anchor, while keeping the toy-scale modular-addition boundary explicit.
