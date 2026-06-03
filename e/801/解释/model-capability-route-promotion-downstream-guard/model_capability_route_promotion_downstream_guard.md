# MiniGPT model capability route promotion downstream guard

- Status: `pass`
- Decision: `model_capability_route_promotion_downstream_guard_allowed`
- Access allowed: `True`
- Consumer: `bounded-benchmark-planner`
- Route: `objective_level_contrast`
- Scope: `bounded_model_capability_governance_only`
- Boundary: `tiny_required_term_pair_probe_only`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| snapshot_passed | pass | pass | governance snapshot must pass |
| snapshot_ready | pass | model_capability_route_promotion_governance_snapshot_ready | governance snapshot decision must be ready |
| downstream_policy_allowed | pass | True | downstream policy must allow bounded use |
| route_card_present | pass | objective_level_contrast | requested route must exist in route cards |
| route_contract_verified | pass | contract_verified | route card must be contract verified |
| route_governance_available | pass | available_for_downstream_bounded_governance | route must be available for bounded governance |
| requested_scope_allowed | pass | {'requested': 'bounded_model_capability_governance_only', 'policy': 'bounded_model_capability_governance_only', 'route': 'bounded_model_capability_governance_only'} | requested scope must match allowed bounded scope |
| boundary_scoped | pass | tiny_required_term_pair_probe_only | route card boundary must match the required boundary |
| claim_bounded | pass | seed_stable_pair_probe_route_accepted | route claim must remain pair-probe scoped |
