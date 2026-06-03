# MiniGPT model capability route promotion bounded real replay decoder anchor rebalanced failure diagnostic

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_failure_diagnostic_ready`
- Ready: `True`
- Failed cases: `5/5`
- Zero-hit cases: `5`
- Fragment-like cases: `5`
- Direct share: `0.375`
- Carry share: `0.25`
- Root causes: `4`

## Case Diagnostics

| Case | Pass | Prompt in corpus | Zero hit | Fragment-like | Missed terms | Diagnosis | Action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| objective-answer-direct | False | True | True | True | fixed,loss | rebalanced_training_still_fragmented | run_rebalanced_decoder_profile_sweep_before_more_training |
| objective-answer-role | False | True | True | True | fixed,loss | rebalanced_training_still_fragmented | run_rebalanced_decoder_profile_sweep_before_more_training |
| objective-answer-contrast | False | True | True | True | fixed,loss | rebalanced_training_still_fragmented | run_rebalanced_decoder_profile_sweep_before_more_training |
| objective-answer-jsonish | False | True | True | True | fixed,loss | rebalanced_training_still_fragmented | run_rebalanced_decoder_profile_sweep_before_more_training |
| objective-answer-check | False | True | True | True | fixed,loss | rebalanced_training_still_fragmented | run_rebalanced_decoder_profile_sweep_before_more_training |

## Root Causes

| Cause | Severity | Evidence | Detail |
| --- | --- | --- | --- |
| rebalanced_distribution_repaired_but_replay_zero_hit | high | {'direct_share': 0.375, 'carry_share': 0.25} | The direct/carry distribution was repaired, but replay still produced zero required-term hits. |
| zero_required_term_hits_after_rebalance | high | 5 | All or some rebalanced replay cases still miss every required term. |
| fragmented_generation_after_rebalance | medium | 5 | The checkpoint emits fragments or repeated characters instead of complete fixed/loss terms. |
| rebalanced_loss_did_not_recover_replay | medium | 4.194498062133789 | The rebalanced training run completed, but bounded replay did not recover over the decoder-anchor checkpoint. |
