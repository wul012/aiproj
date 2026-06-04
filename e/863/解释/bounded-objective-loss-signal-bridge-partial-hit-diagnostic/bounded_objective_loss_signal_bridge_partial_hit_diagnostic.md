# MiniGPT bounded objective loss signal bridge partial-hit diagnostic

- Status: `pass`
- Decision: `bounded_objective_loss_signal_bridge_partial_hit_pair_binding_gap`
- Pair split: `True`
- Partial cases: `2`
- Next step: `build_bounded_objective_loss_signal_bridge_pair_binding_patch`

## Case Diagnostics

| Case | Label | Hit | Missed | Continuation |
| --- | --- | --- | --- | --- |
| canonical_direct_completion | loss_only | loss | fixed |  lossswe |
| minimal_direct_completion | fixed_only | fixed | loss |  fixed l |
| completion_label_surface | zero_hit |  | fixed,loss |  lonssss |

## Root Causes

- `paired_term_binding_gap`: fixed and loss appear separately, but no case binds the pair.
- `completion_surface_zero_hit`: the completion-label surface still loses both required terms.
- `fragmented_required_term_surface`: continuations show short fragments around fixed/loss instead of stable pair output.
- `no_anchor_partial_signal`: partial signal is unassisted and should be repaired through pair-binding data, not decoder anchors.
