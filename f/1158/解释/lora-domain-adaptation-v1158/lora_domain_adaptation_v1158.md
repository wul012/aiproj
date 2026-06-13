# MiniGPT LoRA domain adaptation report v1158

- Generated: `2026-06-13T13:08:58Z`
- Status: `pass`
- Decision: `lora_domain_adaptation_succeeded`

## Summary

| Metric | Value |
| --- | --- |
| status | pass |
| decision | lora_domain_adaptation_succeeded |
| device | cuda |
| source_structure | declarative |
| target_structure | reordered |
| lora_r | 8 |
| adapted_module_count | 16 |
| base_steps | 400 |
| adapt_steps | 400 |
| lora_trainable_parameters | 65536 |
| total_parameters | 873216 |
| trainable_ratio_percent | 7.5051 |
| base_source_heldout_loss | 0.883377 |
| base_target_heldout_loss | 3.988282 |
| domain_gap | 3.104905 |
| full_finetune_target_heldout_loss | 1.18218 |
| lora_target_heldout_loss | 0.891918 |
| lora_target_loss_delta | -3.096364 |
| full_target_loss_delta | -2.806101 |
| lora_vs_full_capture_ratio | 1.1034 |
| lora_target_accuracy | 0.7 |
| base_target_accuracy | 0.461798 |
| lora_source_heldout_loss_after | 3.755852 |
| adapter_forgetting_on_source | 2.872475 |
| domain_adaptation_succeeded | True |

## Rows

| arm | domain | heldout_loss | heldout_token_accuracy |
| --- | --- | --- | --- |
| base | source(A) | 0.883377 | 0.679775 |
| base | target(B) | 3.988282 | 0.461798 |
| full_finetune | target(B) | 1.18218 | 0.683146 |
| lora | target(B) | 0.891918 | 0.7 |
| lora | source(A) | 3.755852 | 0.461798 |

## Recommendations

- LoRA adapted the frozen base to the target structure, cutting target held-out loss by 3.0964 (capturing 110% of full fine-tuning) while training only 7.5051% of parameters — the LoRA win v1157 predicted.
- Because the base is frozen, the adapter is removable: with it applied, source(A) held-out loss moved by +2.8725, but dropping the adapter restores the original A model exactly — unlike full fine-tuning, which overwrites it.
- Source and target share the identical character vocabulary, so this isolates structural adaptation; the embedding/output head transfers for free.
