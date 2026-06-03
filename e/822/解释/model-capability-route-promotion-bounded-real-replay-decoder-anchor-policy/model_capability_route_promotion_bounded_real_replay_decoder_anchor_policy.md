# MiniGPT model capability route promotion bounded real replay decoder anchor policy

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_ready_with_partial_coverage`
- Ready: `True`
- Policy cases: `1`
- Uncovered cases: `4`
- Promotion ready: `False`

## Policy Rows

| Case | Profile | Anchor | Completion hits | Claim boundary | Use |
| --- | --- | --- | --- | --- | --- |
| objective-answer-check | prefix_fixed_space | fixed  | loss | anchor_assisted_only | controlled_policy_replay_only |

## Guardrails

| ID | Severity | Detail |
| --- | --- | --- |
| not_unassisted_model_capability | blocker | Anchors are injected into prompts and must not be counted as unassisted bounded replay success. |
| partial_policy_coverage | warning | Policy covers 1 cases and leaves 4 uncovered. |
| requires_policy_replay | blocker | The policy must be replayed before any downstream use. |
