# MiniGPT unassisted holdout repair partial signal diagnostic v1152

- Generated: `2026-06-12T14:35:24Z`
- Status: `pass`
- Decision: `unassisted_holdout_repair_partial_signal_diagnostic_ready`

## Summary

| Metric | Value |
| --- | --- |
| unassisted_holdout_repair_partial_signal_diagnostic_ready | True |
| case_count | 5 |
| fixed_hit_case_count | 4 |
| loss_hit_case_count | 0 |
| full_pair_case_count | 0 |
| fixed_only_case_count | 4 |
| zero_hit_case_count | 1 |
| target_free_pair_example_count | 6 |
| loss_after_fixed_training_context_count | 1 |
| fixed_first_example_count | 2 |
| root_cause_hypothesis | loss_suffix_context_tied_and_underlearned_after_fixed |
| model_quality_claim | partial_signal_diagnostic_only |
| promotion_ready | False |
| next_step | build_unassisted_loss_suffix_repair_seed |
| failed_check_count | 0 |

## Diagnostic Findings

| finding_id | severity | status | actual | inference | recommended_action |
| --- | --- | --- | --- | --- | --- |
| fixed_signal_visible | info | observed | 4 | v1151 generated `fixed` in target-free holdout continuations | preserve fixed-oriented examples while repairing loss suffix |
| loss_absent_in_all_replay_cases | blocker | requires_repair | 0 | v1151 did not generate `loss` in any holdout continuation | add target-free loss-suffix reinforcement before another replay |
| full_pair_absent | blocker | requires_repair | 0 | `fixed loss` full-pair recovery is still zero | do not promote; run a repair seed revision focused on loss after fixed |
| zero_hit_prompt_cluster | warn | observed | unassisted-holdout-02 | some prompts produce neither fixed nor loss | keep prompt-level diagnostics in the next replay |
| loss_suffix_context_tied | warn | observed | 1 | loss-after-fixed evidence exists mainly as a training-only context where prompt already contains fixed | create target-free prompts that require the model to continue from fixed to loss without prompt contamination |
| fixed_first_bias | warn | observed | 2 | fixed-only examples likely help the first token but can leave loss undertrained | rebalance corpus so fixed-first support does not stop at fixed |
| context_window_drift_visible | warn | observed | unassisted-holdout-04 | at least one generated string no longer starts with the full prompt, suggesting tiny block-size truncation | keep short and long prompts separate in the next replay report |
| next_repair_action | action | ready | build_unassisted_loss_suffix_repair_seed | the next version should alter evidence inputs, not reinterpret v1151 as success | materialize a loss-suffix repair seed and rerun bounded CPU training/replay |
