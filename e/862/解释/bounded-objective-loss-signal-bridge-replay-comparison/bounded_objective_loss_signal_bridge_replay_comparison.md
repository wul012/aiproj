# MiniGPT bounded objective loss signal bridge replay comparison

- Status: `pass`
- Decision: `bounded_objective_loss_signal_bridge_replay_partial_required_term_hit`
- Contract recovered: `False`
- Passed cases: `0/3`
- Any-hit cases: `2`
- Promotion ready: `False`

## Replay Rows

| Case | Pass | Hit Terms | Missed Terms | Continuation |
| --- | --- | --- | --- | --- |
| canonical_direct_completion | False | loss | fixed |  lossswe |
| minimal_direct_completion | False | fixed | loss |  fixed l |
| completion_label_surface | False |  | fixed,loss |  lonssss |
