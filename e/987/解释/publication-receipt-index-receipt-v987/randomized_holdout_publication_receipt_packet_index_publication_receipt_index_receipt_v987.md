# MiniGPT randomized holdout publication receipt packet index publication receipt index receipt v987

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987_ready`
- Receipt ready: `True`
- Receipt status: `publication_receipt_index_lookup_receipted`
- Consumer: `publication_receipt_index_governance_lookup_reader`
- Granted use: `downstream_governance_lookup_only`
- Lookup keys: `1`
- Source evidence: `2`
- Promotion ready: `False`
- Next step: `check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987`

## Receipt

- Source review: `e\986\解释\publication-receipt-index-review-v986\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_review_v986.json`
- Source receipt: `e\983\解释\publication-receipt-v983\randomized_holdout_publication_receipt_packet_index_publication_receipt_v983.json`
- Source check: `e\984\解释\publication-receipt-check-v984\randomized_holdout_publication_receipt_packet_index_publication_receipt_check_v984.json`

## Consumer Receipts

| Consumer | Lookup key | Receipt | Granted use | Promotion | Status |
| --- | --- | --- | --- | --- | --- |
| publication_receipt_index_governance_lookup_reader | receipt-index:randomized-holdout-publication-receipt-packet-index-publication-receipt-v983 | randomized-holdout-publication-receipt-packet-index-publication-receipt-v983 | downstream_governance_lookup_only | False | publication_receipt_index_lookup_receipted |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_index_review_file_exists | pass | e\986\解释\publication-receipt-index-review-v986\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_review_v986.json | receipt index review file must exist |
| receipt_index_review_passed | pass | pass | receipt index review must pass |
| receipt_index_review_decision_ready | pass | randomized_holdout_publication_receipt_packet_index_publication_receipt_index_review_v986_ready | receipt index review decision must be ready |
| receipt_index_review_summary_ready | pass | {'summary': True, 'review': True} | receipt index review summary and body must be ready |
| review_status_allowed | pass | {'summary': 'approved_for_publication_receipt_index_receipt_lookup_only', 'review': 'approved_for_publication_receipt_index_receipt_lookup_only'} | review must approve lookup-only receipt |
| requested_use_allowed | pass | downstream_governance_lookup_only | requested use must stay downstream governance lookup only |
| blocked_uses_complete | pass | ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'] | receipt must preserve all blocked uses |
| receipt_lookup_ready | pass | {'receipt': True, 'lookup': True} | receipt lookup must be ready |
| contract_check_ready | pass | True | source contract check must be ready |
| index_rows_present | pass | {'rows': 1, 'summary': 1} | receipt must cover one receipt index row |
| source_evidence_count | pass | {'rows': 2, 'summary': 2} | receipt must preserve two source evidence rows |
| lookup_keys_receipt_index_namespace | pass | ['receipt-index:randomized-holdout-publication-receipt-packet-index-publication-receipt-v983'] | lookup keys must use receipt-index namespace |
| index_rows_not_promoted | pass | [False] | receipt index rows must not be promoted |
| promotion_still_false | pass | {'summary': False, 'review': False, 'approved': False} | receipt must not enable promotion |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'review': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'review': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| source_receipt_file_exists | pass | e\983\解释\publication-receipt-v983\randomized_holdout_publication_receipt_packet_index_publication_receipt_v983.json | source receipt must still exist |
| source_receipt_check_file_exists | pass | e\984\解释\publication-receipt-check-v984\randomized_holdout_publication_receipt_packet_index_publication_receipt_check_v984.json | source receipt contract check must still exist |
| source_checks_clean | pass | 0 | source receipt index review checks must be clean |
| source_next_step_matches | pass | record_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v986 | source receipt index review must route to receipt |
