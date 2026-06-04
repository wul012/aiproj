# MiniGPT model capability route promotion bounded objective decoder anchor policy

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_objective_decoder_anchor_policy_ready`
- Ready: `True`
- Policy cases: `3`
- Uncovered cases: `0`
- Promotion ready: `False`
- Model quality claim: `decoder_anchor_policy_only`

## Policy Rows

| Case | Profile | Anchor | Completion hits | Boundary | Use | Preview |
| --- | --- | --- | --- | --- | --- | --- |
| canonical_direct_completion | prefix_f | f | fixed,loss | decoder_anchor_signal_only | controlled_policy_replay_only | fixed losssss |
| completion_label_surface | prefix_f | f | fixed,loss | decoder_anchor_signal_only | controlled_policy_replay_only | fixed losssss |
| minimal_direct_completion | prefix_f | f | fixed,loss | decoder_anchor_signal_only | controlled_policy_replay_only | fixed loss    |

## Guardrails

| ID | Severity | Detail |
| --- | --- | --- |
| not_unassisted_model_capability | blocker | Injected anchors must not be counted as unassisted bounded objective replay success. |
| requires_policy_replay | blocker | The selected anchors must be replayed before any downstream use. |
| substring_scoring_not_final_exactness | warning | Policy is based on required-term completion hits; replay must still check final generated text and exact contract behavior. |
| policy_coverage | info | Policy covers 3 cases and leaves 0 uncovered. |
