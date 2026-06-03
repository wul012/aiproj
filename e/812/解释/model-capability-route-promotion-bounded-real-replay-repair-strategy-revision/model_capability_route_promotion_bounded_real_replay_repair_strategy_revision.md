# MiniGPT model capability route promotion bounded real replay repair strategy revision

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_ready`
- Ready: `True`
- Blocked checkpoint: `True`
- Pass delta: `-2`
- Rate delta: `-0.4`
- Next artifact: `model_capability_route_promotion_bounded_real_replay_repair_seed_revision`

## Case Actions

| Case | Severity | Baseline pass | Repair pass | Seed change | Guardrail |
| --- | --- | --- | --- | --- | --- |
| objective-answer-check | persistent_gap | False | False | add_direct_prompt_to_fixed_loss_bridge_examples | prove_failed_case_recovery_before_promotion |
| objective-answer-contrast | regression | True | False | add_baseline_preservation_and_contrastive_repair_examples | preserve_baseline_pass_before_accepting_repair_checkpoint |
| objective-answer-direct | persistent_gap | False | False | add_direct_prompt_to_fixed_loss_bridge_examples | prove_failed_case_recovery_before_promotion |
| objective-answer-jsonish | regression | True | False | add_baseline_preservation_and_contrastive_repair_examples | preserve_baseline_pass_before_accepting_repair_checkpoint |
| objective-answer-role | persistent_gap | False | False | add_direct_prompt_to_fixed_loss_bridge_examples | prove_failed_case_recovery_before_promotion |

## Strategy Actions

| Action | Category | Evidence | Detail |
| --- | --- | --- | --- |
| block_current_repair_checkpoint | gate | -2 | Do not promote the v810 repair checkpoint after replay regression. |
| add_baseline_preservation_examples | seed | 2 | Include examples that protect cases the baseline already passed. |
| balance_direct_and_self_check_examples | seed | 6 | Keep direct answers and self-check answers, but add preservation and contrastive coverage. |
| short_training_with_replay_first | training | 20 | Keep repair training bounded and require immediate replay comparison before promotion. |
| retain_original_repair_tasks | plan | 3 | Carry the original failed-case repair tasks forward instead of inventing unrelated objectives. |
