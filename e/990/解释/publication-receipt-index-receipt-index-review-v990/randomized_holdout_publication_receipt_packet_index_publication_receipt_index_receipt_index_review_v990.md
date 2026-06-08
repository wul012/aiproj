# MiniGPT randomized holdout publication receipt packet index publication receipt index receipt index review v990

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_review_v990_ready`
- Review ready: `True`
- Review status: `approved_for_publication_receipt_index_receipt_index_publication_lookup_only`
- Receipt ready: `True`
- Lookup keys: `1`
- Source evidence: `2`
- Contract check ready: `True`
- Promotion ready: `False`
- Next step: `publish_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_v990`

## Review

- Receipt index: `e\989\解释\publication-receipt-index-receipt-index-v989\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_v989.json`
- Source receipt: `e\987\解释\publication-receipt-index-receipt-v987\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987.json`
- Source receipt check: `e\988\解释\publication-receipt-index-receipt-check-v988\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988.json`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_index_file_exists | pass | e\989\解释\publication-receipt-index-receipt-index-v989\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_v989.json | receipt index file must exist |
| receipt_index_passed | pass | pass | receipt index must pass |
| receipt_index_decision_ready | pass | randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_v989_ready | receipt index decision must be ready |
| receipt_index_summary_ready | pass | {'summary': True, 'index': True} | receipt index summary and body must be ready |
| lookup_scope_downstream | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | lookup scope must remain downstream governance lookup only |
| granted_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| lookup_ready | pass | {'summary': True, 'index': True} | receipt index must be lookup-ready |
| contract_check_ready | pass | {'summary': True, 'index': True} | receipt index must include a ready contract check |
| receipt_index_rows_present | pass | {'rows': 1, 'summary': 1} | review requires one receipt index row |
| lookup_keys_present | pass | ['receipt-index-receipt:randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-v987'] | lookup keys must use the receipt-index-receipt namespace |
| index_rows_not_promoted | pass | [False] | receipt index review must not promote rows |
| source_evidence_count | pass | {'summary': 2, 'rows': 2} | review requires two source evidence rows |
| source_evidence_passed | pass | ['pass', 'pass'] | source evidence rows must pass |
| source_evidence_digests | pass | ['18c6fb4336c2a7892d3069533d8fccde3208045162b1ca00d0f1ca1390e0ae12', '21f9b82f15816e466f746fae25ce8173367b0f1d8ff8608f52b7075d3bd13539'] | source evidence rows must carry SHA-256 digests |
| source_evidence_files_exist | pass | ['e\\987\\解释\\publication-receipt-index-receipt-v987\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987.json', 'e\\988\\解释\\publication-receipt-index-receipt-check-v988\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988.json'] | source evidence files must exist |
| source_receipt_file_exists | pass | e\987\解释\publication-receipt-index-receipt-v987\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987.json | source receipt must still exist |
| source_receipt_check_file_exists | pass | e\988\解释\publication-receipt-index-receipt-check-v988\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988.json | source receipt contract check must still exist |
| source_review_file_exists | pass | ['e\\986\\解释\\publication-receipt-index-review-v986\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_review_v986.json'] | source review must still exist |
| source_prior_receipt_file_exists | pass | ['e\\983\\解释\\publication-receipt-v983\\randomized_holdout_publication_receipt_packet_index_publication_receipt_v983.json'] | prior source receipt must still exist |
| source_prior_receipt_check_file_exists | pass | ['e\\984\\解释\\publication-receipt-check-v984\\randomized_holdout_publication_receipt_packet_index_publication_receipt_check_v984.json'] | prior source receipt check must still exist |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'index': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'index': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'index': False, 'approved': False} | receipt index review must not enable promotion |
| source_checks_clean | pass | 0 | source receipt index checks must be clean |
| source_next_step_matches | pass | review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_v989 | source receipt index must route to review |
