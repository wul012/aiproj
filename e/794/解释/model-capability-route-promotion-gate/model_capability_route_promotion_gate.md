# MiniGPT model capability route promotion gate

- Status: `pass`
- Decision: `model_capability_route_promotion_gate_passed`
- Exit code: `0`
- Gate ready: `True`
- Gate decision: `allow_downstream_model_capability_review`
- Active routes: `objective_level_contrast`
- Boundary: `tiny_required_term_pair_probe_only`
- Claim: `seed_stable_pair_probe_route_accepted`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| portfolio_passed | pass | pass | route promotion portfolio must pass |
| portfolio_decision_ready | pass | model_capability_route_promotion_portfolio_ready | route promotion portfolio must be ready |
| regression_monitor_passed | pass | pass | route promotion regression monitor must pass |
| regression_decision_passed | pass | model_capability_route_promotion_regression_monitor_passed | regression monitor decision must pass |
| active_routes_present | pass | ['objective_level_contrast'] | at least one active route is required |
| portfolio_boundary_scoped | pass | tiny_required_term_pair_probe_only | portfolio must keep the required boundary |
| regression_boundary_stable | pass | {'changed': False, 'current': 'tiny_required_term_pair_probe_only'} | regression monitor must preserve the required boundary |
| no_lost_active_routes | pass | 0 | gate blocks when active routes are lost |
| no_claim_widening | pass | False | gate blocks claim widening |
| portfolio_checks_clean | pass | 0 | portfolio should have no failed checks |
| regression_checks_clean | pass | 0 | regression monitor should have no failed checks |
