# MiniGPT model capability route promotion bounded real replay decoder anchor probe

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe_found_completion_signal`
- Ready: `True`
- Probe rows: `15`
- Anchor-assisted passes: `2`
- Completion passes: `2`
- New-text passes: `2`
- Next step: `build_decoder_anchor_policy`

## Probe Rows

| Case | Profile | Anchor | Assisted pass | Completion pass | New-text pass | Assisted hits | New-text hits | Completion hits |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| objective-answer-direct | prefix_f | f | False | False | False |  |  |  |
| objective-answer-direct | prefix_fixed_space | fixed  | False | False | False | fixed | fixed |  |
| objective-answer-direct | prefix_fixed_l | fixed l | False | False | False | fixed | fixed |  |
| objective-answer-role | prefix_f | f | False | False | False |  |  |  |
| objective-answer-role | prefix_fixed_space | fixed  | False | False | False | fixed | fixed |  |
| objective-answer-role | prefix_fixed_l | fixed l | False | False | False | fixed | fixed |  |
| objective-answer-contrast | prefix_f | f | False | False | False |  |  |  |
| objective-answer-contrast | prefix_fixed_space | fixed  | False | False | False | fixed | fixed |  |
| objective-answer-contrast | prefix_fixed_l | fixed l | False | False | False | fixed | fixed |  |
| objective-answer-jsonish | prefix_f | f | False | False | False |  |  |  |
| objective-answer-jsonish | prefix_fixed_space | fixed  | False | False | False | fixed | fixed |  |
| objective-answer-jsonish | prefix_fixed_l | fixed l | False | False | False | fixed | fixed |  |
| objective-answer-check | prefix_f | f | False | False | False |  |  |  |
| objective-answer-check | prefix_fixed_space | fixed  | True | True | True | fixed,loss | fixed,loss | loss |
| objective-answer-check | prefix_fixed_l | fixed l | True | True | True | fixed,loss | fixed,loss | loss |
