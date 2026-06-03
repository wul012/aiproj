# MiniGPT model capability route promotion bounded real replay prompt-aligned failure diagnostic

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic_ready`
- Ready: `True`
- Failed cases: `5/5`
- Zero-hit cases: `5`
- Fragment-like cases: `5`
- Root causes: `4`

## Case Diagnostics

| Case | Pass | Prompt in corpus | Zero hit | Fragment-like | Missed terms | Diagnosis | Action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| objective-answer-direct | False | True | True | True | fixed,loss | character_fragmentation_without_term_anchoring | run_decoder_anchor_or_forced_prefix_probe |
| objective-answer-role | False | True | True | True | fixed,loss | character_fragmentation_without_term_anchoring | run_decoder_anchor_or_forced_prefix_probe |
| objective-answer-contrast | False | True | True | True | fixed,loss | character_fragmentation_without_term_anchoring | run_decoder_anchor_or_forced_prefix_probe |
| objective-answer-jsonish | False | True | True | True | fixed,loss | character_fragmentation_without_term_anchoring | run_decoder_anchor_or_forced_prefix_probe |
| objective-answer-check | False | True | True | True | fixed,loss | character_fragmentation_without_term_anchoring | run_decoder_anchor_or_forced_prefix_probe |

## Root Causes

| Cause | Severity | Evidence | Detail |
| --- | --- | --- | --- |
| exact_prompts_present_but_generation_unanchored | high | 5 | The corpus contains exact prompts, but replay still misses fixed/loss. |
| zero_required_term_hits | high | 5 | Replay continuations did not contain any expected required terms. |
| character_fragmentation_dominates_generation | medium | 5 | Continuations contain scattered character fragments instead of complete required terms. |
| loss_reduction_did_not_transfer_to_replay | medium | 4.215392112731934 | The prompt-aligned run trained successfully, but replay still regressed against baseline. |
