# MiniGPT model capability route promotion release readiness downstream receipt

- Status: `pass`
- Decision: `model_capability_route_promotion_release_readiness_downstream_receipt_granted`
- Receipt ready: `True`
- Consumer: `release-readiness-index-builder`
- Route: `objective_level_contrast`
- Scope: `bounded_route_promotion_release_governance_only`
- Boundary: `tiny_required_term_pair_probe_only`
- Claim: `seed_stable_pair_probe_route_accepted`
- Source check digest: `93e3a1fc3b43b6a09381f283d660c3cb1d49b4e6fa35522bd30f3dbc74388343`

## Source Digests

| Kind | SHA-256 | Path |
| --- | --- | --- |
| release_packet | 4b32d56640811e3dda52bba0e2f952227a6b9d7fb841ebaffa4ef301f4d82104 | e\795\解释\model-capability-route-promotion-release-packet\model_capability_route_promotion_release_packet.json |
| release_packet_review | 7259663a4798d7a7470aacc776d429346d4fb881c149d200141d995fa428164c | e\796\解释\model-capability-route-promotion-release-packet-review\model_capability_route_promotion_release_packet_review.json |
| governance_snapshot | f4be5170a62da02225816f8f7820f281e128928b23e89ccec85ca6aeed77e089 | e\800\解释\model-capability-route-promotion-governance-snapshot\model_capability_route_promotion_governance_snapshot.json |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| consumer_name_present | pass | release-readiness-index-builder | consumer name must be recorded |
| route_id_requested | pass | objective_level_contrast | requested route id must be recorded |
| summary_check_passed | pass | pass | source contract check must pass |
| summary_check_decision_ready | pass | model_capability_route_promotion_release_readiness_summary_contract_check_passed | source contract check decision must be ready |
| contract_check_ready | pass | True | source summary check must be ready |
| source_failed_count_zero | pass | 0 | source check failed_count must be zero |
| source_check_rows_clean | pass | {'pass': 25, 'fail': 0} | source check rows must all pass |
| route_id_in_checked_summary | pass | {'requested': 'objective_level_contrast', 'active_routes': ['objective_level_contrast']} | requested route must be present in checked summary |
| boundary_required | pass | tiny_required_term_pair_probe_only | checked summary boundary must match required boundary |
| claim_bounded | pass | seed_stable_pair_probe_route_accepted | checked summary claim must remain pair-probe scoped |
| source_digest_count_matches | pass | {'summary': 3, 'actual': 3} | source digest count must match digest rows |
| source_digests_present | pass | [{'kind': 'release_packet', 'path': 'e\\795\\解释\\model-capability-route-promotion-release-packet\\model_capability_route_promotion_release_packet.json', 'exists': True, 'sha256': '4b32d56640811e3dda52bba0e2f952227a6b9d7fb841ebaffa4ef301f4d82104'}, {'kind': 'release_packet_review', 'path': 'e\\796\\解释\\model-capability-route-promotion-release-packet-review\\model_capability_route_promotion_release_packet_review.json', 'exists': True, 'sha256': '7259663a4798d7a7470aacc776d429346d4fb881c149d200141d995fa428164c'}, {'kind': 'governance_snapshot', 'path': 'e\\800\\解释\\model-capability-route-promotion-governance-snapshot\\model_capability_route_promotion_governance_snapshot.json', 'exists': True, 'sha256': 'f4be5170a62da02225816f8f7820f281e128928b23e89ccec85ca6aeed77e089'}] | all source digest rows must carry SHA-256 |
| requested_scope_allowed | pass | bounded_route_promotion_release_governance_only | requested scope must be bounded route-promotion release governance only |
| downstream_scope_matches | pass | bounded_route_promotion_release_governance_only | source downstream policy scope must match requested receipt scope |
| source_scope_bounded | pass | bounded_model_capability_governance_only | source governance scope must remain bounded model-capability governance only |
| downstream_policy_allowed | pass | True | source downstream policy must allow bounded use |
