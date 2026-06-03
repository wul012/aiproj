# MiniGPT model capability route promotion bounded real replay repair checkpoint comparison

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_real_replay_repair_checkpoint_regressed`
- Baseline passed: `2`
- Repair passed: `0`
- Pass rate delta: `-0.4`
- Promotion ready: `False`
- Next step: `revise_bounded_repair_seed_or_training_strategy_before_replay_promotion`

## Case Comparison

| Case | Baseline pass | Repair pass | Delta | Baseline hits | Repair hits | Repair misses |
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
| repair_replay_passed | pass | pass | repair replay execution must pass |
| training_run_ready_when_provided | pass | True | repair training run evidence is optional, but must be ready when provided |
| case_counts_match | pass | {'baseline': 5, 'repair': 5} | baseline and repair replay should cover the same suite |
| case_rows_present | pass | 5 | comparison must include case rows |
