# MiniGPT randomized holdout publication receipt packet index publication receipt index receipt index publication v991

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991_ready`
- Publication ready: `True`
- Publication status: `published_for_publication_receipt_index_receipt_index_lookup_only`
- Published use: `downstream_governance_lookup_only`
- Lookup keys: `1`
- Source evidence: `2`
- Contract check ready: `True`
- Promotion ready: `False`
- Next step: `check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991`

## Publication

- Receipt index review: `e\990\解释\publication-receipt-index-receipt-index-review-v990\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_review_v990.json`
- Receipt index: `e\989\解释\publication-receipt-index-receipt-index-v989\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_v989.json`
- Source receipt: `e\987\解释\publication-receipt-index-receipt-v987\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987.json`
- Source receipt check: `e\988\解释\publication-receipt-index-receipt-check-v988\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988.json`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_index_review_file_exists | pass | e\990\解释\publication-receipt-index-receipt-index-review-v990\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_review_v990.json | receipt index review file must exist |
| receipt_index_review_passed | pass | pass | receipt index review must pass |
| receipt_index_review_decision_ready | pass | randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_review_v990_ready | receipt index review decision must be ready |
| receipt_index_review_summary_ready | pass | {'summary': True, 'review': True} | review summary and body must be ready |
| review_status_publishable | pass | {'summary': 'approved_for_publication_receipt_index_receipt_index_publication_lookup_only', 'review': 'approved_for_publication_receipt_index_receipt_index_publication_lookup_only'} | review must approve lookup-only publication |
| receipt_index_file_exists | pass | e\989\解释\publication-receipt-index-receipt-index-v989\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_v989.json | reviewed receipt index must still exist |
| source_receipt_file_exists | pass | e\987\解释\publication-receipt-index-receipt-v987\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987.json | source receipt must still exist |
| source_receipt_check_file_exists | pass | e\988\解释\publication-receipt-index-receipt-check-v988\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988.json | source receipt contract check must still exist |
| receipt_ready | pass | {'summary': True, 'review': True} | publication requires receipt-ready review |
| lookup_ready | pass | {'summary': True, 'review': True} | publication requires lookup-ready review |
| contract_check_ready | pass | {'summary': True, 'review': True} | publication requires contract-ready review |
| receipt_index_row_count | pass | {'summary': 1, 'review': 1, 'rows': 1} | publication requires one receipt index row |
| lookup_keys_present | pass | ['receipt-index-receipt:randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-v987'] | publication requires one stable receipt-index-receipt lookup key |
| source_evidence_count | pass | {'summary': 2, 'review': 2, 'rows': 2} | publication requires two source evidence rows |
| source_evidence_passed | pass | ['pass', 'pass'] | source evidence rows must pass |
| source_evidence_digests | pass | ['18c6fb4336c2a7892d3069533d8fccde3208045162b1ca00d0f1ca1390e0ae12', '21f9b82f15816e466f746fae25ce8173367b0f1d8ff8608f52b7075d3bd13539'] | source evidence rows must carry SHA-256 digests |
| source_evidence_files_exist | pass | ['e\\987\\解释\\publication-receipt-index-receipt-v987\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987.json', 'e\\988\\解释\\publication-receipt-index-receipt-check-v988\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988.json'] | source evidence files must exist |
| allowed_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'review': 'downstream_governance_lookup_only'} | publication must remain downstream lookup only |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'review': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'review': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| blocked_uses_preserved | pass | {'summary': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'], 'review': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion']} | blocked uses must remain explicit |
| promotion_still_false | pass | {'summary': False, 'review': False, 'approved': False} | publication must not enable promotion |
| source_checks_clean | pass | 0 | source review checks must be clean |
| source_next_step_matches | pass | publish_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_v990 | source review must route to publication |
