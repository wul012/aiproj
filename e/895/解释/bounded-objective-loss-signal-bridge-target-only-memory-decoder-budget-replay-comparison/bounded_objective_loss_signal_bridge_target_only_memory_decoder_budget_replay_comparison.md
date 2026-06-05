# MiniGPT bounded objective loss signal bridge target-only memory decoder-budget replay comparison

- Status: `pass`
- Decision: `bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_contract_recovered_holdout_required`
- Contract recovered: `True`
- Passed cases: `3/3`
- Any-hit cases: `3`
- Promotion ready: `False`

## Replay Rows

| Case | Pass | Hit Terms | Missed Terms | Continuation |
| --- | --- | --- | --- | --- |
| canonical_direct_completion | True | fixed,loss |  |  fixed loss |
| minimal_direct_completion | True | fixed,loss |  |  fixed loss |
| completion_label_surface | True | fixed,loss |  |  fixed loss |
