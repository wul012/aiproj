# MiniGPT model capability route promotion bounded objective decoder anchor policy replay

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_objective_decoder_anchor_policy_replay_reproduced_assisted_signal`
- Ready: `True`
- Passed cases: `3/3`
- Policy applied pass: `3`
- New-text pass: `0`
- Promotion ready: `False`
- Model quality claim: `decoder_anchor_policy_replay_only`

## Replay Rows

| Case | Policy | Profile | Anchor | Pass | New Text | Combined Hits | New Hits | Misses | Continuation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| canonical_direct_completion | True | prefix_f | f | True | False | fixed,loss | loss |  | ixed losssss |
| minimal_direct_completion | True | prefix_f | f | True | False | fixed,loss | loss |  | ixed loss    |
| completion_label_surface | True | prefix_f | f | True | False | fixed,loss | loss |  | ixed losssss |
