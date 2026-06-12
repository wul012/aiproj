# MiniGPT loss signal bridge and decoder anchor distribution v1145

- Generated: `2026-06-12T11:18:00Z`
- Status: `pass`
- Decision: `model_capability_loss_signal_bridge_decoder_anchor_distribution_ready`

## Summary

| Metric | Value |
| --- | --- |
| loss_signal_bridge_decoder_anchor_distribution_ready | True |
| loss_signal_ready | True |
| training_record_count | 5 |
| first_train_loss | 3.307331 |
| last_train_loss | 2.307431 |
| train_loss_delta | -0.999899 |
| first_val_loss | 3.320089 |
| last_val_loss | 2.825226 |
| val_loss_delta | -0.494864 |
| decoder_anchor_distribution_ready | True |
| decoder_anchor_example_count | 9 |
| carry_forward_share | 0.3333 |
| direct_answer_share | 0.3333 |
| decoder_bridge_share | 0.3333 |
| rebalanced_seed_needed | False |
| model_quality_claim | loss_signal_bridge_and_decoder_anchor_distribution_real_execution |
| promotion_ready | False |
| next_step | run_decoder_anchor_probe_against_v1145_checkpoint |
| failed_check_count | 0 |

## Loss Signal And Decoder Anchor Rows

| row_id | area | status | metric | actual | expected | detail |
| --- | --- | --- | --- | --- | --- | --- |
| loss_signal_bridge | training | pass | train_loss_delta | -0.999899 | < 0 | Bounded CPU training should reduce train loss on the v1145 bridge corpus. |
| decoder_anchor_distribution | seed_distribution | pass | bridge/direct/carry shares | carry=0.3333, direct=0.3333, bridge=0.3333 | balanced enough to avoid rebalanced_seed_needed | Distribution audit reuses the existing decoder-anchor bucket rules. |

## Recommendations

- Treat v1145 as bounded real training evidence plus a balanced decoder-anchor corpus check.
- Use the produced checkpoint for the next decoder-anchor probe before making any promotion claim.
