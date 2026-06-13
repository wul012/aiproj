# MiniGPT LoRA fine-tune before/after report v1156

- Generated: `2026-06-13T11:47:50Z`
- Status: `pass`
- Decision: `lora_finetune_reduced_train_loss`

## Summary

| Metric | Value |
| --- | --- |
| status | pass |
| decision | lora_finetune_reduced_train_loss |
| device | cuda |
| lora_r | 8 |
| lora_alpha | 16.0 |
| lora_dropout | 0.0 |
| target_modules | c_attn, c_proj |
| adapted_module_count | 8 |
| steps | 400 |
| learning_rate | 0.001 |
| base_parameters | 827008 |
| trainable_parameters | 24576 |
| total_parameters | 851584 |
| trainable_ratio_percent | 2.8859 |
| before_train_loss | 0.455033 |
| after_train_loss | 0.416174 |
| train_loss_delta | -0.03886 |
| before_val_loss | 5.308659 |
| after_val_loss | 5.284511 |
| val_loss_delta | -0.024148 |
| last_step_loss | 0.407525 |
| train_loss_improved | True |
| val_loss_improved | True |

## Rows

| module | kind | r | alpha |
| --- | --- | --- | --- |
| blocks.0.attn.c_attn | lora_adapter | 8 | 16.0 |
| blocks.0.attn.c_proj | lora_adapter | 8 | 16.0 |
| blocks.1.attn.c_attn | lora_adapter | 8 | 16.0 |
| blocks.1.attn.c_proj | lora_adapter | 8 | 16.0 |
| blocks.2.attn.c_attn | lora_adapter | 8 | 16.0 |
| blocks.2.attn.c_proj | lora_adapter | 8 | 16.0 |
| blocks.3.attn.c_attn | lora_adapter | 8 | 16.0 |
| blocks.3.attn.c_proj | lora_adapter | 8 | 16.0 |

## Recommendations

- LoRA reduced training loss by 0.0389 while training only 2.8859% of parameters; the adapter demonstrably learns.
- Caveat: the bundled corpus is tiny, so validation loss is overfit-dominated and not a reliable generalization signal. v1157 should introduce a larger real dataset and a held-out eval suite.
- Merge the adapter with minigpt.lora.merge_lora to serve without extra parameters.
