# MiniGPT model capability route promotion decision index

- Status: `pass`
- Decision: `model_capability_route_promotion_decision_index_ready`
- Ready: `True`
- Accepted routes: `1`
- Route ids: `objective_level_contrast`
- Boundary: `tiny_required_term_pair_probe_only`
- Claim: `seed_stable_pair_probe_route_accepted`

## Route Entries

| Route | Status | Scope | Boundary | Claim | Source |
| --- | --- | --- | --- | --- | --- |
| objective_level_contrast | accepted | bounded_route_promotion_review_only | tiny_required_term_pair_probe_only | seed_stable_pair_probe_route_accepted | e\797\解释\model-capability-route-promotion-review-decision\model_capability_route_promotion_review_decision.json |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| decision_sources_present | pass | 1 | at least one source decision is required |
| accepted_source_present | pass | 1 | at least one source decision must be accepted |
| ready_route_count | pass | 1 | accepted route count must satisfy the index threshold |
| blocked_sources_absent | pass | 0 | all source decisions must be accepted |
| boundary_scoped | pass | 0 | all indexed routes must keep the required boundary |
| review_scope_bounded | pass | 0 | all indexed routes must keep bounded review scope |
