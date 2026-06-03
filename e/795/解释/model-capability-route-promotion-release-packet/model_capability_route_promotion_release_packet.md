# MiniGPT model capability route promotion release packet

- Status: `pass`
- Decision: `model_capability_route_promotion_release_packet_ready`
- Release packet ready: `True`
- Handoff status: `ready_for_route_promotion_review`
- Active routes: `objective_level_contrast`
- Boundary: `tiny_required_term_pair_probe_only`
- Claim: `seed_stable_pair_probe_route_accepted`

## Evidence

| Kind | Exists | Path |
| --- | --- | --- |
| portfolio | True | e\792\解释\model-capability-route-promotion-portfolio\model_capability_route_promotion_portfolio.json |
| regression_monitor | True | e\793\解释\model-capability-route-promotion-regression-monitor\model_capability_route_promotion_regression_monitor.json |
| gate | True | e\794\解释\model-capability-route-promotion-gate\model_capability_route_promotion_gate.json |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| portfolio_passed | pass | pass | portfolio must pass |
| regression_monitor_passed | pass | pass | regression monitor must pass |
| gate_passed | pass | pass | gate must pass |
| gate_ready | pass | True | gate summary must be ready |
| active_routes_present | pass | 1 | release packet needs active routes |
| no_lost_active_routes | pass | 0 | release packet blocks active-route regressions |
| boundary_stable | pass | False | release packet boundary must be stable |
| claim_not_widened | pass | False | release packet claim must not widen |
| evidence_files_exist | pass | [{'kind': 'portfolio', 'path': 'e\\792\\解释\\model-capability-route-promotion-portfolio\\model_capability_route_promotion_portfolio.json', 'exists': True}, {'kind': 'regression_monitor', 'path': 'e\\793\\解释\\model-capability-route-promotion-regression-monitor\\model_capability_route_promotion_regression_monitor.json', 'exists': True}, {'kind': 'gate', 'path': 'e\\794\\解释\\model-capability-route-promotion-gate\\model_capability_route_promotion_gate.json', 'exists': True}] | packet evidence source files must exist |
