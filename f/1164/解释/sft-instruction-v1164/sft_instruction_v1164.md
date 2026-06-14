# MiniGPT SFT instruction-following (completion-only loss) v1164

- Generated: `2026-06-14T00:05:25Z`
- Status: `pass`
- Decision: `sft_instruction_following_measured`

## Summary

| Metric | Value |
| --- | --- |
| status | pass |
| decision | sft_instruction_following_measured |
| verdict | completion_only_helps_early_benefit_shrinks_with_training |
| device | cuda |
| seeds | 3 |
| arms | completion_only,full_loss |
| ops | C,R,S |
| step_schedule | 150,400,800,1500 |
| n_layer | 4 |
| n_head | 4 |
| n_embd | 128 |
| use_rope | True |
| train_example_count | 1362 |
| heldout_example_count | 453 |
| learnability_gate | 0.5 |
| completion_only_copy_accuracy_at_max | 0.754967 |
| task_learned | True |
| min_steps | 150 |
| max_steps | 1500 |
| completion_only_overall_at_min | 0.266372 |
| full_loss_overall_at_min | 0.028698 |
| masking_gap_at_min | 0.237675 |
| completion_only_overall_at_max | 0.794702 |
| completion_only_overall_at_max_std | 0.083097 |
| full_loss_overall_at_max | 0.77557 |
| masking_gap_at_max | 0.019132 |

## Rows

| arm | steps | overall_accuracy_mean | overall_accuracy_std |
| --- | --- | --- | --- |
| completion_only | 150 | 0.266372 | 0.100492 |
| completion_only | 400 | 0.514349 | 0.209469 |
| completion_only | 800 | 0.748344 | 0.035526 |
| completion_only | 1500 | 0.794702 | 0.083097 |
| full_loss | 150 | 0.028698 | 0.023878 |
| full_loss | 400 | 0.278882 | 0.231002 |
| full_loss | 800 | 0.549669 | 0.378128 |
| full_loss | 1500 | 0.77557 | 0.190273 |

## Recommendations

- VERDICT (completion_only_helps_early_benefit_shrinks_with_training): completion-only vs full-sequence-loss exact-match gap is +0.238 at 150 steps and +0.019 at 1500 steps (3 seeds, greedy decode). The masking benefit is largest with little training and shrinks as both arms train longer.
- CAPABILITY: at 1500 steps the completion-only model follows instructions on UNSEEN inputs at 0.795 exact-match (held-out inputs disjoint from training; chance for a length-4 string over 5 symbols is ~0.0016). Per-op at max budget: C=0.75, R=0.80, S=0.83.
- Learnability gate: completion-only SFT reaches 0.755 exact-match on the trivial copy op at 1500 steps (gate 0.5); task_learned=True.
- SFT MECHANIC: loss is computed only over completion tokens (prompt + padding masked with ignore_index=-100). The full_loss arm removes that mask; the masking effect — and its dependence on training budget — is measured across the step sweep, not assumed.
- SCOPE: this isolates the SFT supervision mechanic (instruction formatting + completion-only loss + held-out instruction generalization). It trains from scratch on the instruction data rather than fine-tuning a separately-pretrained base — the right scope to demonstrate the mechanic at this scale.
