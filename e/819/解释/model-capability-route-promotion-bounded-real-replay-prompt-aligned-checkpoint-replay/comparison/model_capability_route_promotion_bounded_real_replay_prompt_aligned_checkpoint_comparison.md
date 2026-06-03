# MiniGPT model capability route promotion bounded real replay prompt-aligned checkpoint comparison

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint_regressed`
- Baseline passed: `2`
- Prompt-aligned passed: `0`
- Pass rate delta: `-0.4`
- Promotion ready: `False`
- Next step: `diagnose_prompt_aligned_checkpoint_replay_failure_before_more_training`

## Case Comparison

| Case | Baseline pass | Prompt-aligned pass | Delta | Baseline hits | Prompt-aligned hits | Prompt-aligned misses |
| --- | --- | --- | --- | --- | --- | --- |
| objective-answer-check | False | False | 0 | loss |  | fixed,loss |
| objective-answer-contrast | True | False | -1 | fixed,loss |  | fixed,loss |
| objective-answer-direct | False | False | 0 | loss |  | fixed,loss |
| objective-answer-jsonish | True | False | -1 | fixed,loss |  | fixed,loss |
| objective-answer-role | False | False | 0 |  |  | fixed,loss |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| baseline_replay_passed | pass | pass | baseline replay execution must pass |
| prompt_aligned_replay_passed | pass | pass | prompt-aligned replay execution must pass |
| prompt_aligned_training_ready_when_provided | pass | True | prompt-aligned training evidence is optional, but must be ready when provided |
| case_counts_match | pass | {'baseline': 5, 'prompt_aligned': 5} | baseline and prompt-aligned replay should cover the same suite |
| case_rows_present | pass | 5 | comparison must include case rows |
