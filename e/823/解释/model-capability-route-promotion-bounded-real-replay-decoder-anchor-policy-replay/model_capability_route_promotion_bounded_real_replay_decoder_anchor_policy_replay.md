# MiniGPT model capability route promotion bounded real replay decoder anchor policy replay

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_reproduced_partial_signal`
- Ready: `True`
- Passed cases: `1/5`
- Policy applied: `1`
- Policy applied pass: `1`
- Promotion ready: `False`

## Replay Rows

| Case | Policy | Profile | Anchor | Pass | Combined hits | New hits | Misses |
| --- | --- | --- | --- | --- | --- | --- | --- |
| objective-answer-direct | False |  |  | False |  |  | fixed,loss |
| objective-answer-role | False |  |  | False |  |  | fixed,loss |
| objective-answer-contrast | False |  |  | False |  |  | fixed,loss |
| objective-answer-jsonish | False |  |  | False |  |  | fixed,loss |
| objective-answer-check | True | prefix_fixed_space | fixed  | True | fixed,loss | fixed,loss |  |
