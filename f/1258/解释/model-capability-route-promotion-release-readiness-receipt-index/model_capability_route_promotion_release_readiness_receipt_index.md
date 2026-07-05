# MiniGPT model capability route promotion release readiness receipt index

- Status: `pass`
- Decision: `model_capability_route_promotion_release_readiness_receipt_index_ready`
- Index ready: `True`
- Index id: `route-promotion-release-readiness-receipt-index-v1258`
- Lookup scope: `bounded_route_promotion_release_readiness_receipt_lookup_only`
- Entry count: `1`
- Lookup ready: `True`
- Route: `objective_level_contrast`
- Consumer: `release-readiness-index-builder`
- Granted scope: `bounded_route_promotion_release_governance_only`
- Source digest count: `3`
- Promotion ready: `False`
- Next step: `review_indexed_route_promotion_release_readiness_receipt`

## Source Evidence

- Downstream receipt: `f\1257\解释\model-capability-route-promotion-release-readiness-downstream-receipt\model_capability_route_promotion_release_readiness_downstream_receipt.json`
- Downstream receipt digest: `b986240b2a34261e24f3497abeb22a90a963ad334913337508eb9f85bcba5ea5`

## Lookup Rows

| Index | Lookup key | Entry | Consumer | Route | Scope | Claim | Receipt digest | Promotion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| route-promotion-release-readiness-receipt-index-v1258 | route-promotion-release-readiness:objective_level_contrast | route-promotion-release-readiness:objective_level_contrast:release-readiness-index-builder | release-readiness-index-builder | objective_level_contrast | bounded_route_promotion_release_governance_only | seed_stable_pair_probe_route_accepted | b986240b2a34261e24f3497abeb22a90a963ad334913337508eb9f85bcba5ea5 | False |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| downstream_receipt_file_exists | pass | f\1257\解释\model-capability-route-promotion-release-readiness-downstream-receipt\model_capability_route_promotion_release_readiness_downstream_receipt.json | downstream receipt file must exist |
| downstream_receipt_passed | pass | pass | downstream receipt report must pass |
| downstream_receipt_decision_granted | pass | model_capability_route_promotion_release_readiness_downstream_receipt_granted | downstream receipt decision must be granted |
| downstream_receipt_ready | pass | True | downstream receipt summary must be ready |
| receipt_status_granted | pass | granted | receipt body must be granted |
| consumer_name_present | pass | release-readiness-index-builder | receipt index requires a consumer name |
| route_id_present | pass | objective_level_contrast | receipt index requires a route id |
| granted_scope_bounded | pass | bounded_route_promotion_release_governance_only | receipt granted scope must remain bounded route-promotion release governance only |
| boundary_required | pass | tiny_required_term_pair_probe_only | receipt boundary must match the required boundary |
| claim_bounded | pass | seed_stable_pair_probe_route_accepted | receipt model quality claim must remain pair-probe scoped |
| source_check_digest_present | pass | 93e3a1fc3b43b6a09381f283d660c3cb1d49b4e6fa35522bd30f3dbc74388343 | receipt must carry the checked-summary digest |
| downstream_receipt_digest_present | pass | b986240b2a34261e24f3497abeb22a90a963ad334913337508eb9f85bcba5ea5 | receipt index must digest the downstream receipt file |
| source_digest_count_matches | pass | {'receipt': 3, 'actual': 3} | source digest count must match digest rows |
| source_digests_present | pass | [{'kind': 'release_packet', 'path': 'e\\795\\解释\\model-capability-route-promotion-release-packet\\model_capability_route_promotion_release_packet.json', 'exists': True, 'sha256': '4b32d56640811e3dda52bba0e2f952227a6b9d7fb841ebaffa4ef301f4d82104'}, {'kind': 'release_packet_review', 'path': 'e\\796\\解释\\model-capability-route-promotion-release-packet-review\\model_capability_route_promotion_release_packet_review.json', 'exists': True, 'sha256': '7259663a4798d7a7470aacc776d429346d4fb881c149d200141d995fa428164c'}, {'kind': 'governance_snapshot', 'path': 'e\\800\\解释\\model-capability-route-promotion-governance-snapshot\\model_capability_route_promotion_governance_snapshot.json', 'exists': True, 'sha256': 'f4be5170a62da02225816f8f7820f281e128928b23e89ccec85ca6aeed77e089'}] | all upstream source digest rows must carry SHA-256 |
| blocked_uses_complete | pass | ['production_model_quality_claim', 'unbounded_release_promotion', 'training_data_reuse_proof', 'model_capability_claim_beyond_pair_probe_route'] | receipt index must preserve the complete blocked-use list |
| source_receipt_checks_clean | pass | {'failed_count': 0, 'row_failures': []} | source downstream receipt checks must be clean |
| source_next_step_matches | pass | {'receipt': 'index_checked_route_promotion_release_readiness_receipt', 'summary': 'index_checked_route_promotion_release_readiness_receipt'} | source receipt must route to receipt indexing |
