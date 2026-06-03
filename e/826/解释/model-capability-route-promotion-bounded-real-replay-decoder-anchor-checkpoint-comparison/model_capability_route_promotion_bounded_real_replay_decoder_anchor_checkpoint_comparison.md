# MiniGPT model capability route promotion bounded real replay decoder anchor checkpoint comparison

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_regressed_from_baseline`
- Baseline passed: `2`
- Prompt-aligned passed: `0`
- Decoder-anchor passed: `0`
- Decoder vs baseline rate delta: `-0.4`
- Decoder vs prompt rate delta: `0.0`
- Promotion ready: `False`
- Next step: `diagnose_decoder_anchor_checkpoint_replay_failure_before_more_training`

## Case Comparison

| Case | Baseline | Prompt-aligned | Decoder-anchor | Delta baseline | Delta prompt | Decoder hits | Decoder misses |
| --- | --- | --- | --- | --- | --- | --- | --- |
| objective-answer-check | False | False | False | 0 | 0 |  | fixed,loss |
| objective-answer-contrast | True | False | False | -1 | 0 |  | fixed,loss |
| objective-answer-direct | False | False | False | 0 | 0 |  | fixed,loss |
| objective-answer-jsonish | True | False | False | -1 | 0 |  | fixed,loss |
| objective-answer-role | False | False | False | 0 | 0 |  | fixed,loss |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| baseline_replay_passed | pass | pass | baseline replay execution must pass |
| prompt_aligned_replay_passed | pass | pass | prompt-aligned replay execution must pass |
| decoder_anchor_replay_passed | pass | pass | decoder anchor replay execution must pass |
| decoder_anchor_training_ready_when_provided | pass | True | decoder anchor training evidence is optional, but must be ready when provided |
| case_counts_match | pass | {'baseline': 5, 'prompt_aligned': 5, 'decoder_anchor': 5} | baseline, prompt-aligned, and decoder-anchor replay should cover the same suite |
| case_rows_present | pass | 5 | comparison must include case rows |
