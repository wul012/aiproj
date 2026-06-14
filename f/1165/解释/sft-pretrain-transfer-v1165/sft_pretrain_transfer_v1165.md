# MiniGPT base->SFT transfer to a held-out op v1165

- Generated: `2026-06-14T00:33:02Z`
- Status: `pass`
- Decision: `sft_transfer_measured`

## Summary

| Metric | Value |
| --- | --- |
| status | pass |
| decision | sft_transfer_measured |
| verdict | pretraining_improves_downstream_sft |
| device | cuda |
| seeds | 3 |
| downstream_op | L |
| base_ops | C,R,S |
| base_steps | 1200 |
| sft_schedule | 50,150,400,1000 |
| n_layer | 4 |
| n_head | 4 |
| n_embd | 128 |
| use_rope | True |
| base_train_char_count | 15498 |
| downstream_train_count | 454 |
| downstream_heldout_count | 151 |
| learnability_gate | 0.5 |
| pretrained_at_max_budget | 0.971302 |
| task_learned | True |
| min_sft_steps | 50 |
| max_sft_steps | 1000 |
| pretrained_at_min | 0.313466 |
| scratch_at_min | 0.022075 |
| transfer_gap_at_min | 0.291391 |
| scratch_at_max | 0.825607 |
| transfer_gap_at_max | 0.145695 |

## Rows

| arm | sft_steps | exact_match_mean | exact_match_std |
| --- | --- | --- | --- |
| pretrained | 50 | 0.313466 | 0.193002 |
| pretrained | 150 | 0.556291 | 0.423996 |
| pretrained | 400 | 0.856512 | 0.225976 |
| pretrained | 1000 | 0.971302 | 0.029863 |
| scratch | 50 | 0.022075 | 0.016666 |
| scratch | 150 | 0.284768 | 0.046358 |
| scratch | 400 | 0.487859 | 0.109689 |
| scratch | 1000 | 0.825607 | 0.080928 |

## Recommendations

- VERDICT (pretraining_improves_downstream_sft): on the held-out op 'L', pretrained-vs-scratch SFT exact-match gap is +0.291 at 50 SFT steps and +0.146 at 1000 SFT steps (3 seeds). Pretraining on {copy,reverse,sort} is expected to help most when downstream SFT data/compute is small.
- DATA EFFICIENCY: at 50 SFT steps the pretrained base reaches 0.313 exact-match on the new op vs 0.022 from scratch; by 1000 steps they are 0.971 vs 0.826. The new op (shift-left) was NEVER in base pretraining, so any gap is transfer of shared primitives + the instruction format, not leakage.
- Learnability gate: the pretrained arm reaches 0.971 exact-match on the new op at 1000 steps (gate 0.5); task_learned=True.
- RECIPE: this is the real two-stage SFT pipeline — pretrain a base with full next-token loss, then fine-tune with completion-only loss on a downstream task. The base and downstream share one char vocabulary so embeddings transfer.
- SCOPE: tiny from-scratch base and a synthetic op family; transfer magnitude is scale-dependent and the new op deliberately shares positional-copy primitives with the pretrained ops, so this shows the MECHANISM of transfer, not a generic claim.
