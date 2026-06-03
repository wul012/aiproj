# MiniGPT model capability route promotion governance snapshot

- Status: `pass`
- Decision: `model_capability_route_promotion_governance_snapshot_ready`
- Ready: `True`
- Verified routes: `1`
- Boundary: `tiny_required_term_pair_probe_only`
- Claim: `seed_stable_pair_probe_route_accepted`
- Downstream allowed: `True`

## Route Cards

| Route | Route status | Verification | Governance | Scope | Boundary | Claim |
| --- | --- | --- | --- | --- | --- | --- |
| objective_level_contrast | accepted | contract_verified | available_for_downstream_bounded_governance | bounded_route_promotion_review_only | tiny_required_term_pair_probe_only | seed_stable_pair_probe_route_accepted |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| decision_index_passed | pass | pass | decision index must pass |
| decision_index_ready | pass | model_capability_route_promotion_decision_index_ready | decision index must be ready |
| contract_check_passed | pass | pass | contract check must pass |
| contract_check_ready | pass | True | contract check must be ready |
| route_cards_present | pass | 1 | snapshot must include route cards |
| verified_route_cards | pass | 1 | all route cards must be contract verified |
| accepted_route_count_matches | pass | {'index': 1, 'rebuilt': 1} | index and rebuilt accepted route count must match |
| boundary_scoped | pass | 0 | all route cards must keep the required boundary |
