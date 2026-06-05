# MiniGPT bounded objective loss signal bridge target-only memory tokenizer-coverage-aware holdout real replay

- Status: `pass`
- Decision: `bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_real_replay_passed_review_required`
- Holdout model quality ready: `True`
- Passed cases: `5/5`
- Any-hit cases: `5`
- Pass rate: `1.0`

## Replay Rows

| Case | Pass | Hit terms | Missed terms | Continuation |
| --- | --- | --- | --- | --- |
| tokenizer-covered-answer_exact_terms | True | fixed,loss |  |  fixed loss      fixed l |
| tokenizer-covered-return_target_words | True | fixed,loss |  |  fixed loss    fixed los |
| tokenizer-covered-contrast_route_result | True | fixed,loss |  |   answer. fixed losss  f |
| tokenizer-covered-jsonish_answer_terms | True | fixed,loss |  |  fixed loss     fixed lo |
| tokenizer-covered-self_check_terms | True | fixed,loss |  |  fixed loss       fixed  |
