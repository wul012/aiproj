# MiniGPT v1185 canonical grokking checkpoint

- Generated: `2026-06-18T04:22:42Z`
- Status: `pass`
- Decision: `canonical_grokking_checkpoint_ready`

## Summary

| Metric | Value |
| --- | --- |
| recipe | a+b mod 97, 1-layer MiniGPT n_embd=128, AdamW lr=1e-3 wd=1.0, train_frac=0.2 |
| p | 97 |
| weight_decay | 1.0 |
| train_frac | 0.2 |
| seed | 1337 |
| vocab_size | 99 |
| memorize_step | 100 |
| generalize_step | 11400 |
| grok_delay_steps | 11300 |
| final_train_acc | 1.0 |
| final_val_acc | 0.965989 |
| heldout_acc | 0.965989 |
| n_heldout | 7527 |
| roundtrip_logits_identical | True |
| verdict | canonical_grokking_checkpoint_ready |
| story | train accuracy saturates at the memorize step; validation stays near chance until the much-later generalize step (grokking). |
| boundary | toy_scale_single_task_modular_addition_canonical_checkpoint_not_a_scaling_claim |

## Rows

| a | b | predicted | truth | correct |
| --- | --- | --- | --- | --- |
| 52 | 64 | 19 | 19 | True |
| 56 | 74 | 33 | 33 | True |
| 79 | 83 | 65 | 65 | True |
| 2 | 80 | 82 | 82 | True |
| 36 | 37 | 73 | 73 | True |
| 4 | 1 | 5 | 5 | True |
| 25 | 52 | 77 | 77 | True |
| 77 | 32 | 28 | 12 | False |

## Recommendations

- Canonical grokking checkpoint ready: memorized at step 100, generalized at step 11400, held-out accuracy 0.966.
- Load it with load_checkpoint(); it reconstructs the architecture from the embedded meta and reproduces identical logits.
- The recipe uses weight_decay=1.0 because the v1183 dose-response found that to be the interior optimum (fastest grok).
