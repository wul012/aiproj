# MiniGPT Required-Term Pair Route Closeout Summary

- Status: `pass`
- Decision: `close_required_term_pair_route_before_new_objective`
- Held-out all pair-full: `True`
- Fresh-seed pair-full count: `0`
- Route decision: `stop_first_token_and_width_for_fresh_seed`

## Evidence

| Label | Type | Status | Decision | Key result |
| --- | --- | --- | --- | --- |
| v570-heldout-expanded | heldout_replay | pass | required_term_pair_route_heldout_replay_ready | 7/7 heldout pair-full |
| v571-loss-balanced | fresh_seed_stability | pass | required_term_pair_colon_immediate_not_stable | 0/1 pair-full, hits=1 |
| v573-first-token | fresh_seed_stability | pass | required_term_pair_colon_immediate_not_stable | 0/1 pair-full, hits=0 |
| v575-wider-embd | fresh_seed_stability | pass | required_term_pair_colon_immediate_not_stable | 0/1 pair-full, hits=0 |
| v576-variable-comparison | comparison | pass | required_term_pair_equals_surface_repair_comparison_recorded | union_hit_terms=fixed |
| v577-route-decision | route_decision | pass | stop_first_token_and_width_for_fresh_seed | best_residual_signal=v571-loss-balanced |

## Boundary

- Model quality claim: `bounded_transfer_not_generalized`
- Reason: The selected route transfers across held-out surfaces but does not generalize to fresh seed 3535.
- Next action: start a branch-binding objective; do not continue first-token rows or width scaling variants
