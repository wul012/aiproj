# MiniGPT randomized holdout publication receipt packet index publication receipt index receipt index v989

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_v989_ready`
- Index ready: `True`
- Receipt index: `randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-v989`
- Lookup scope: `downstream_governance_lookup_only`
- Lookup key count: `1`
- Receipt status: `publication_receipt_index_lookup_receipted`
- Granted use: `downstream_governance_lookup_only`
- Contract check ready: `True`
- Promotion ready: `False`
- Next step: `review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_v989`

## Source Artifacts

- Receipt: `e\987\解释\publication-receipt-index-receipt-v987\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987.json`
- Receipt check: `e\988\解释\publication-receipt-index-receipt-check-v988\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988.json`

## Receipt Index Rows

| Index | Lookup key | Receipt | Status | Use | Contract | Promotion |
| --- | --- | --- | --- | --- | --- | --- |
| randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-v989 | receipt-index-receipt:randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-v987 | randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-v987 | publication_receipt_index_lookup_receipted | downstream_governance_lookup_only | True | False |

## Source Evidence

| Kind | Path | SHA-256 | Status |
| --- | --- | --- | --- |
| receipt | e\987\解释\publication-receipt-index-receipt-v987\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987.json | 18c6fb4336c2a7892d3069533d8fccde3208045162b1ca00d0f1ca1390e0ae12 | pass |
| receipt_check | e\988\解释\publication-receipt-index-receipt-check-v988\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988.json | 21f9b82f15816e466f746fae25ce8173367b0f1d8ff8608f52b7075d3bd13539 | pass |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_file_exists | pass | e\987\解释\publication-receipt-index-receipt-v987\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987.json | receipt file must exist |
| receipt_check_file_exists | pass | e\988\解释\publication-receipt-index-receipt-check-v988\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988.json | receipt contract check file must exist |
| receipt_passed | pass | pass | receipt must pass |
| receipt_decision_ready | pass | randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987_ready | receipt decision must be ready |
| receipt_summary_ready | pass | {'summary': True, 'receipt': True} | receipt summary and body must be ready |
| receipt_status_ready | pass | {'summary': 'publication_receipt_index_lookup_receipted', 'receipt': 'publication_receipt_index_lookup_receipted'} | receipt must be lookup receipted |
| receipt_check_passed | pass | pass | receipt contract check must pass |
| receipt_check_decision_ready | pass | randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_contract_check_v988_passed | receipt contract check decision must pass |
| contract_check_ready | pass | True | receipt contract check must be ready |
| receipt_status_matches_check | pass | {'receipt': 'publication_receipt_index_lookup_receipted', 'original': 'publication_receipt_index_lookup_receipted', 'rebuilt': 'publication_receipt_index_lookup_receipted'} | receipt status must match contract check |
| granted_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'receipt': 'downstream_governance_lookup_only', 'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| lookup_key_count | pass | {'summary': 1, 'original': 1, 'rebuilt': 1, 'receipt': 1} | receipt index requires one lookup key |
| consumer_receipt_row_count | pass | 1 | receipt index requires one consumer receipt row |
| source_evidence_count | pass | 2 | receipt index requires two source evidence rows |
| source_receipt_index_review_file_exists | pass | e\986\解释\publication-receipt-index-review-v986\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_review_v986.json | source receipt index review must still exist |
| source_receipt_file_exists | pass | e\983\解释\publication-receipt-v983\randomized_holdout_publication_receipt_packet_index_publication_receipt_v983.json | source receipt must still exist |
| source_receipt_check_file_exists | pass | e\984\解释\publication-receipt-check-v984\randomized_holdout_publication_receipt_packet_index_publication_receipt_check_v984.json | source receipt contract check must still exist |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'receipt': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | bounded_randomized_target_hidden_holdout_claim_only | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'approved': False, 'receipt': False, 'original': False, 'rebuilt': False} | receipt index must not enable promotion |
| source_receipt_checks_clean | pass | 0 | source receipt checks must be clean |
| source_contract_checks_clean | pass | 0 | source contract checks must be clean |
| source_next_steps_match | pass | {'receipt': 'check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987', 'check': 'index_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v988'} | source next steps must route to check then index |
