# MiniGPT model capability route promotion portfolio

- Status: `pass`
- Decision: `model_capability_route_promotion_portfolio_ready`
- Portfolio ready: `True`
- Active routes: `1`
- Boundary: `tiny_required_term_pair_probe_only`
- Model quality claim: `seed_stable_pair_probe_route_accepted`

## Route Cards

| Route | Status | Ready | Boundary | Claim | Seeds | Pair Full Min | Spread |
| --- | --- | --- | --- | --- | --- | --- | --- |
| objective_level_contrast | active | ready | tiny_required_term_pair_probe_only | seed_stable_pair_probe_route_accepted | 3 | 2 | 1 |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| history_passed | pass | pass | source history must pass |
| history_readiness_passed | pass | pass | source history readiness requirement must pass |
| minimum_ready_routes | pass | {'ready': 1, 'required': 1} | portfolio must carry enough active route promotions |
| no_blocked_routes | pass | 0 | route portfolio should not include blocked routes |
| no_boundary_mismatches | pass | 0 | all routes must keep the required boundary |
| boundary_matches_history | pass | tiny_required_term_pair_probe_only | history boundary must match portfolio boundary |
| claims_are_bounded | pass | ['seed_stable_pair_probe_route_accepted'] | claims must remain pair-probe scoped |
