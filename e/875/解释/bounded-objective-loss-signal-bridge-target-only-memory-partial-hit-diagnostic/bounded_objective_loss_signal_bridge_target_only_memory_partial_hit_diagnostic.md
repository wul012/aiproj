# MiniGPT bounded objective loss signal bridge target-only memory partial-hit diagnostic

- Status: `pass`
- Decision: `bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_loss_suffix_gap`
- Partial cases: `3`
- Loss-prefix cases: `3`
- Loss-hit cases: `0`
- Next step: `build_bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch`

## Case Diagnostics

| Case | Label | Hit | Missed | Continuation |
| --- | --- | --- | --- | --- |
| canonical_direct_completion | fixed_with_loss_prefix | fixed | loss |  fixed l |
| minimal_direct_completion | fixed_with_loss_prefix | fixed | loss |  fixed l |
| completion_label_surface | fixed_with_loss_prefix | fixed | loss |  fixed l |

## Root Causes

- `loss_suffix_uptake_gap`: all cases reach fixed and a loss prefix, but none complete the loss token.
- `fixed_dominates_required_pair`: target-only memory strengthened fixed more than the full fixed loss pair.
- `no_anchor_partial_signal`: partial signal is unassisted; next repair should remain data-level unless replay regresses.
- `partial_signal_without_contract_pass`: required-term signal improved, but no case satisfies the full objective.
