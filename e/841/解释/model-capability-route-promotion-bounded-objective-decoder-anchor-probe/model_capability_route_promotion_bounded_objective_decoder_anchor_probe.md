# MiniGPT model capability route promotion bounded objective decoder anchor probe

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_objective_decoder_anchor_probe_found_completion_signal`
- Ready: `True`
- Anchor completion success: `True`
- Promotion ready: `False`
- Model quality claim: `decoder_anchor_signal_only`
- Next action: `build_bounded_objective_decoder_anchor_policy`

## Probe Rows

| Case | Profile | Anchor | Assisted | Completion | New Text | Assisted Hits | New Hits | Completion Hits | Continuation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| canonical_direct_completion | prefix_f | f | True | True | False | fixed,loss | loss | fixed,loss | ixed losssss |
| canonical_direct_completion | prefix_fixed_space | fixed  | True | True | False | fixed,loss | loss | loss | loss    answ |
| canonical_direct_completion | prefix_fixed_l | fixed l | True | True | False | fixed,loss |  | loss | osss       a |
| minimal_direct_completion | prefix_f | f | True | True | False | fixed,loss | loss | fixed,loss | ixed loss    |
| minimal_direct_completion | prefix_fixed_space | fixed  | True | True | False | fixed,loss | loss | loss | loss    answ |
| minimal_direct_completion | prefix_fixed_l | fixed l | True | True | False | fixed,loss |  | loss | osss       a |
| completion_label_surface | prefix_f | f | True | True | False | fixed,loss | loss | fixed,loss | ixed losssss |
| completion_label_surface | prefix_fixed_space | fixed  | True | True | False | fixed,loss | loss | loss | lossssssssss |
| completion_label_surface | prefix_fixed_l | fixed l | True | True | False | fixed,loss |  | loss | osssssss   a |
