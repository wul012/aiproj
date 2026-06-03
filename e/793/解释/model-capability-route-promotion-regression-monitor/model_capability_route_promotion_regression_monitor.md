# MiniGPT model capability route promotion regression monitor

- Status: `pass`
- Decision: `model_capability_route_promotion_regression_monitor_passed`
- Lost active routes: `0`
- Boundary changed: `False`
- Claim changed: `False`

## Route Deltas

| Route | Baseline | Current | Relation | Baseline Boundary | Current Boundary | Baseline Claim | Current Claim |
| --- | --- | --- | --- | --- | --- | --- | --- |
| objective_level_contrast | active | active | stable_active | tiny_required_term_pair_probe_only | tiny_required_term_pair_probe_only | seed_stable_pair_probe_route_accepted | seed_stable_pair_probe_route_accepted |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| baseline_portfolio_passed | pass | pass | baseline portfolio must pass |
| current_portfolio_passed | pass | pass | current portfolio must pass |
| current_portfolio_ready | pass | True | current portfolio must be ready |
| no_active_route_loss | pass | [] | current portfolio must not lose baseline active routes |
| no_boundary_changes | pass | {'baseline': 'tiny_required_term_pair_probe_only', 'current': 'tiny_required_term_pair_probe_only', 'route_changes': 0} | portfolio boundary must stay stable |
| no_claim_widening | pass | [] | model quality claim must not widen |
| active_route_count_not_decreased | pass | {'baseline': 1, 'current': 1} | active route count must not decrease |
