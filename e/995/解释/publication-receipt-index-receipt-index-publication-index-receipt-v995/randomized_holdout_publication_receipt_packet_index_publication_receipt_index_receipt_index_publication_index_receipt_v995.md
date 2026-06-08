# MiniGPT randomized holdout publication receipt packet index publication receipt index receipt index publication index receipt v995

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_v995_ready`
- Receipt ready: `True`
- Receipt status: `publication_index_lookup_receipted`
- Consumer: `publication_index_governance_lookup_reader`
- Granted use: `downstream_governance_lookup_only`
- Lookup keys: `1`
- Source evidence: `2`
- Promotion ready: `False`
- Next step: `check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_v995`

## Receipt

- Source review: `e\994\解释\publication-receipt-index-receipt-index-publication-index-review-v994\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994.json`
- Source publication: `e\991\解释\publication-receipt-index-receipt-index-publication-v991\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991.json`
- Source check: `e\992\解释\publication-receipt-index-receipt-index-publication-check-v992\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_check_v992.json`

## Consumer Receipts

| Consumer | Lookup key | Publication index | Receipt | Granted use | Promotion | Status |
| --- | --- | --- | --- | --- | --- | --- |
| publication_index_governance_lookup_reader | publication-index:randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-v991 | randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-index-v993 | randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-index-receipt-v995 | downstream_governance_lookup_only | False | publication_index_lookup_receipted |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| publication_index_review_file_exists | pass | e\994\解释\publication-receipt-index-receipt-index-publication-index-review-v994\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994.json | publication index review file must exist |
| publication_index_review_passed | pass | pass | publication index review must pass |
| publication_index_review_decision_ready | pass | randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994_ready | publication index review decision must be ready |
| publication_index_review_summary_ready | pass | {'summary': True, 'review': True} | publication index review summary and body must be ready |
| review_status_allowed | pass | {'summary': 'approved_for_publication_index_receipt_lookup_only', 'review': 'approved_for_publication_index_receipt_lookup_only'} | review must approve lookup-only receipt |
| requested_use_allowed | pass | downstream_governance_lookup_only | requested use must stay downstream governance lookup only |
| blocked_uses_complete | pass | ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'] | receipt must preserve all blocked uses |
| publication_lookup_ready | pass | {'publication': True, 'lookup': True} | publication index lookup must be ready |
| contract_check_ready | pass | True | source contract check must be ready |
| index_rows_present | pass | {'rows': 1, 'summary': 1} | receipt must cover one publication index row |
| source_evidence_count | pass | {'rows': 2, 'summary': 2} | receipt must preserve two source evidence rows |
| lookup_keys_publication_index_namespace | pass | ['publication-index:randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-v991'] | lookup keys must use publication-index namespace |
| index_rows_not_promoted | pass | [False] | publication index rows must not be promoted |
| promotion_still_false | pass | {'summary': False, 'review': False, 'approved': False} | receipt must not enable promotion |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'review': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'review': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| source_publication_file_exists | pass | e\991\解释\publication-receipt-index-receipt-index-publication-v991\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991.json | source publication must still exist |
| source_publication_check_file_exists | pass | e\992\解释\publication-receipt-index-receipt-index-publication-check-v992\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_check_v992.json | source publication contract check must still exist |
| source_checks_clean | pass | 0 | source publication index review checks must be clean |
| source_next_step_matches | pass | record_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_v994 | source publication index review must route to receipt |
