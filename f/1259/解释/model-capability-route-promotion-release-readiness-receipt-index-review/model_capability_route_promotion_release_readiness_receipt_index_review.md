# MiniGPT model capability route promotion release readiness receipt index review

- Status: `pass`
- Decision: `model_capability_route_promotion_release_readiness_receipt_index_review_ready`
- Review ready: `True`
- Review id: `route-promotion-release-readiness-receipt-index-review-v1259`
- Review status: `approved_for_bounded_receipt_lookup`
- Entry count: `1`
- Lookup ready: `True`
- Route: `objective_level_contrast`
- Consumer: `release-readiness-index-builder`
- Allowed use: `bounded_route_promotion_release_readiness_receipt_lookup_only`
- Promotion ready: `False`
- Receipt index digest: `a46351d8411b1a432eb9a643dfc207bca092b3867fb599fdec89d926a90ed058`
- Next step: `record_reviewed_route_promotion_release_readiness_receipt_index`

## Lookup Keys

- `route-promotion-release-readiness:objective_level_contrast`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_index_file_exists | pass | f\1258\解释\model-capability-route-promotion-release-readiness-receipt-index\model_capability_route_promotion_release_readiness_receipt_index.json | receipt index file must exist |
| receipt_index_digest_present | pass | a46351d8411b1a432eb9a643dfc207bca092b3867fb599fdec89d926a90ed058 | review must digest the receipt index file |
| receipt_index_passed | pass | pass | receipt index report must pass |
| receipt_index_decision_ready | pass | model_capability_route_promotion_release_readiness_receipt_index_ready | receipt index decision must be ready |
| receipt_index_ready | pass | {'summary': True, 'index': True} | receipt index summary and body must be ready |
| lookup_scope_bounded | pass | {'summary': 'bounded_route_promotion_release_readiness_receipt_lookup_only', 'index': 'bounded_route_promotion_release_readiness_receipt_lookup_only'} | lookup scope must remain bounded receipt lookup only |
| lookup_ready | pass | {'summary': True, 'index': True} | receipt index must remain lookup-ready |
| lookup_rows_present | pass | {'rows': 1, 'summary': 1, 'index': 1} | review requires lookup rows |
| lookup_key_count_matches | pass | {'keys': ['route-promotion-release-readiness:objective_level_contrast'], 'rows': 1, 'summary': 1} | lookup keys must match lookup rows |
| row_route_matches_summary | pass | {'row': 'objective_level_contrast', 'summary': 'objective_level_contrast', 'index': 'objective_level_contrast'} | lookup row route must match the index summary |
| granted_scope_bounded | pass | {'row': 'bounded_route_promotion_release_governance_only', 'index': 'bounded_route_promotion_release_governance_only'} | granted scope must remain bounded |
| boundary_required | pass | {'row': 'tiny_required_term_pair_probe_only', 'index': 'tiny_required_term_pair_probe_only'} | index boundary must match the required boundary |
| claim_bounded | pass | {'row': 'seed_stable_pair_probe_route_accepted', 'index': 'seed_stable_pair_probe_route_accepted'} | model quality claim must remain pair-probe scoped |
| source_check_digest_present | pass | {'row': '93e3a1fc3b43b6a09381f283d660c3cb1d49b4e6fa35522bd30f3dbc74388343', 'index': '93e3a1fc3b43b6a09381f283d660c3cb1d49b4e6fa35522bd30f3dbc74388343'} | source check digest must remain present |
| downstream_receipt_file_exists | pass | f\1257\解释\model-capability-route-promotion-release-readiness-downstream-receipt\model_capability_route_promotion_release_readiness_downstream_receipt.json | indexed downstream receipt file must still exist |
| downstream_receipt_digest_matches | pass | {'index': 'b986240b2a34261e24f3497abeb22a90a963ad334913337508eb9f85bcba5ea5', 'row': 'b986240b2a34261e24f3497abeb22a90a963ad334913337508eb9f85bcba5ea5', 'actual': 'b986240b2a34261e24f3497abeb22a90a963ad334913337508eb9f85bcba5ea5'} | indexed downstream receipt digest must match the receipt file |
| source_digest_count_matches | pass | {'index': 3, 'row': 3, 'actual': 3} | source digest count must match source digest rows |
| source_digests_present | pass | [{'kind': 'release_packet', 'path': 'e\\795\\解释\\model-capability-route-promotion-release-packet\\model_capability_route_promotion_release_packet.json', 'exists': True, 'sha256': '4b32d56640811e3dda52bba0e2f952227a6b9d7fb841ebaffa4ef301f4d82104'}, {'kind': 'release_packet_review', 'path': 'e\\796\\解释\\model-capability-route-promotion-release-packet-review\\model_capability_route_promotion_release_packet_review.json', 'exists': True, 'sha256': '7259663a4798d7a7470aacc776d429346d4fb881c149d200141d995fa428164c'}, {'kind': 'governance_snapshot', 'path': 'e\\800\\解释\\model-capability-route-promotion-governance-snapshot\\model_capability_route_promotion_governance_snapshot.json', 'exists': True, 'sha256': 'f4be5170a62da02225816f8f7820f281e128928b23e89ccec85ca6aeed77e089'}] | all source digest rows must carry SHA-256 |
| blocked_uses_complete | pass | {'index': ['production_model_quality_claim', 'unbounded_release_promotion', 'training_data_reuse_proof', 'model_capability_claim_beyond_pair_probe_route'], 'row': ['production_model_quality_claim', 'unbounded_release_promotion', 'training_data_reuse_proof', 'model_capability_claim_beyond_pair_probe_route']} | blocked uses must remain complete |
| promotion_still_false | pass | {'summary': False, 'index': False, 'row': False, 'approved': False} | receipt index review must not enable promotion |
| source_index_checks_clean | pass | {'failed_count': 0, 'summary_failed': 0} | source receipt index checks must be clean |
| source_next_step_matches | pass | {'summary': 'review_indexed_route_promotion_release_readiness_receipt', 'index': 'review_indexed_route_promotion_release_readiness_receipt'} | source index must route to index review |
