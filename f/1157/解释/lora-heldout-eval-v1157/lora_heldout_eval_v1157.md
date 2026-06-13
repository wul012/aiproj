# MiniGPT LoRA held-out generalization report v1157

- Generated: `2026-06-13T12:28:09Z`
- Status: `pass`
- Decision: `heldout_eval_harness_validated`

## Summary

| Metric | Value |
| --- | --- |
| status | pass |
| decision | heldout_eval_harness_validated |
| device | cuda |
| lora_r | 8 |
| lora_alpha | 16.0 |
| adapted_module_count | 16 |
| base_steps | 30 |
| continued_steps | 600 |
| block_size | 48 |
| train_char_count | 3562 |
| heldout_char_count | 891 |
| heldout_token_count | 890 |
| lora_trainable_parameters | 65536 |
| total_parameters | 873216 |
| trainable_ratio_percent | 7.5051 |
| base_heldout_loss | 2.058854 |
| full_finetune_heldout_loss | 1.228402 |
| lora_heldout_loss | 2.016049 |
| heldout_loss_delta | -0.042805 |
| full_finetune_loss_delta | -0.830452 |
| lora_vs_full_capture_ratio | 0.0515 |
| lora_verdict | lora_partial_gain |
| base_heldout_accuracy | 0.67191 |
| full_finetune_heldout_accuracy | 0.68427 |
| lora_heldout_accuracy | 0.682022 |
| heldout_accuracy_delta | 0.010112 |
| harness_valid | True |

## Rows

| stage | heldout_loss | heldout_token_accuracy | trainable_parameters |
| --- | --- | --- | --- |
| base | 2.058854 | 0.67191 | 807680 |
| full_finetune | 1.228402 | 0.68427 | 807680 |
| lora | 2.016049 | 0.682022 | 65536 |

## Recommendations

- Held-out eval is valid: full fine-tuning lowered held-out loss by 0.8305 (well beyond noise), so the metric measures real generalization — fixing v1156's overfit-dominated signal.
- LoRA verdict: lora_partial_gain. Adapting all attention+MLP linears (7.5051% of params) captured 5% of full fine-tuning's held-out gain. On this tiny model the token embedding is TIED to the output head and LoRA leaves it frozen, so most char-level signal is unreachable — a real lesson in LoRA target selection.
- v1158 should test LoRA where it is expected to win: domain adaptation (pretrain on A, adapt to B) or adapting the embedding/output head.
- Held-out sentences share the grammar/vocabulary of training but are disjoint combinations, so these are real generalization metrics on a synthetic corpus; natural-text scale is a later step.
