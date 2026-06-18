# MiniGPT v1186 grokking checkpoint inference demo

- Generated: `2026-06-18T04:49:12Z`
- Status: `pass`
- Decision: `grokking_checkpoint_usable`

## Summary

| Metric | Value |
| --- | --- |
| checkpoint | D:\aiproj\f\1185\解释\grok_checkpoint_v1185\grok_checkpoint_v1185.pt |
| p | 97 |
| recipe_weight_decay | 1.0 |
| train_frac | 0.2 |
| seed | 1337 |
| overall_acc | 0.972792 |
| train_acc | 1.0 |
| heldout_acc | 0.965989 |
| n_heldout | 7527 |
| demo_pairs | 6 |
| demo_all_correct | True |
| verdict | grokking_checkpoint_usable |
| usage | load_checkpoint(path) -> model; predict(model, a, b, p) -> (a+b) mod p |
| boundary | toy_scale_single_task_inference_demo_not_a_scaling_claim |

## Rows

| a | b | predicted | truth | correct |
| --- | --- | --- | --- | --- |
| 36 | 37 | 73 | 73 | True |
| 4 | 1 | 5 | 5 | True |
| 50 | 50 | 3 | 3 | True |
| 96 | 96 | 95 | 95 | True |
| 0 | 0 | 0 | 0 | True |
| 40 | 80 | 23 | 23 | True |

## Recommendations

- The shipped checkpoint loads and computes a+b mod 97: held-out accuracy 0.966 on 7527 unseen pairs, re-derived independently of the v1185 training run.
- Usage: model, meta = load_checkpoint(path); predict(model, a, b, meta.p).
