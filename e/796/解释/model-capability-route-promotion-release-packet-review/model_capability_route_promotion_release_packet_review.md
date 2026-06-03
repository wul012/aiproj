# MiniGPT model capability route promotion release packet review

- Status: `pass`
- Decision: `model_capability_route_promotion_release_packet_review_ready`
- Review ready: `True`
- Review decision: `accept_route_promotion_packet_for_bounded_review`
- Active routes: `objective_level_contrast`
- Boundary: `tiny_required_term_pair_probe_only`
- Claim: `seed_stable_pair_probe_route_accepted`
- Scope: `bounded_route_promotion_review_only`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| release_packet_passed | pass | pass | release packet must pass |
| release_packet_decision_ready | pass | model_capability_route_promotion_release_packet_ready | release packet decision must be ready |
| packet_ready | pass | True | packet must be ready |
| handoff_ready | pass | ready_for_route_promotion_review | packet must be ready for route promotion review |
| active_routes_present | pass | ['objective_level_contrast'] | review requires active route evidence |
| boundary_scoped | pass | tiny_required_term_pair_probe_only | review boundary must remain tiny pair-probe scoped |
| claim_bounded | pass | seed_stable_pair_probe_route_accepted | review claim must remain pair-probe scoped |
| evidence_count | pass | 3 | review requires portfolio, regression, and gate evidence |
| evidence_files_exist | pass | [{'kind': 'portfolio', 'path': 'e\\792\\解释\\model-capability-route-promotion-portfolio\\model_capability_route_promotion_portfolio.json', 'exists': True}, {'kind': 'regression_monitor', 'path': 'e\\793\\解释\\model-capability-route-promotion-regression-monitor\\model_capability_route_promotion_regression_monitor.json', 'exists': True}, {'kind': 'gate', 'path': 'e\\794\\解释\\model-capability-route-promotion-gate\\model_capability_route_promotion_gate.json', 'exists': True}] | all packet evidence rows must exist |
| packet_checks_clean | pass | 0 | packet source checks must be clean |
