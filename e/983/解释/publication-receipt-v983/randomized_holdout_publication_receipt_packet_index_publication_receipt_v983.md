# MiniGPT randomized holdout publication receipt packet index publication receipt v983

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_packet_index_publication_receipt_v983_ready`
- Receipt ready: `True`
- Receipt status: `publication_index_lookup_receipted`
- Consumer: `publication_registry_governance_lookup_reader`
- Granted use: `downstream_governance_lookup_only`
- Publication index rows: `1`
- Source evidence: `2`
- Promotion ready: `False`
- Next step: `check_randomized_holdout_publication_receipt_packet_index_publication_receipt_v983`

## Consumer Receipts

| Consumer | Lookup key | Publication | Granted use | Blocked uses | Promotion | Status |
| --- | --- | --- | --- | --- | --- | --- |
| publication_registry_governance_lookup_reader | publication-index:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-packet-index-publication-v979 | randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-packet-index-publication-v979 | downstream_governance_lookup_only | ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'] | False | publication_index_lookup_receipted |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| index_review_file_exists | pass | e\982\解释\publication-index-review-v982\randomized_holdout_publication_receipt_packet_index_publication_index_review_v982.json | index review file must exist |
| index_review_passed | pass | pass | index review must pass |
| index_review_decision_ready | pass | randomized_holdout_publication_receipt_packet_index_publication_index_review_v982_ready | index review decision must be ready |
| index_review_summary_ready | pass | {'summary': True, 'review': True} | index review summary and body must be ready |
| review_status_allowed | pass | {'summary': 'approved_for_publication_index_receipt_lookup_only', 'review': 'approved_for_publication_index_receipt_lookup_only'} | review must approve lookup-only receipt |
| requested_use_allowed | pass | downstream_governance_lookup_only | requested use must stay downstream governance lookup only |
| blocked_uses_complete | pass | ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'] | receipt must preserve all blocked uses |
| receipt_lookup_ready | pass | {'receipt': True, 'lookup': True} | receipt lookup must be ready |
| contract_check_ready | pass | True | source contract check must be ready |
| index_rows_present | pass | {'rows': 1, 'summary': 1} | receipt must cover one publication index row |
| source_evidence_count | pass | {'rows': 2, 'summary': 2} | receipt must preserve two source evidence rows |
| lookup_keys_publication_index_namespace | pass | ['publication-index:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-packet-index-publication-v979'] | lookup keys must use publication-index namespace |
| index_rows_not_promoted | pass | [False] | publication index rows must not be promoted |
| promotion_still_false | pass | {'summary': False, 'review': False, 'approved': False} | receipt must not enable promotion |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'review': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'review': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| source_publication_file_exists | pass | e\979\解释\publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-packet-index-publication\randomized_holdout_publication_receipt_packet_index_publication_v979.json | source publication must still exist |
| source_publication_check_file_exists | pass | e\980\解释\publication-receipt-packet-index-publication-check\randomized_holdout_publication_receipt_packet_index_publication_check_v980.json | source publication contract check must still exist |
| source_checks_clean | pass | 0 | source index review checks must be clean |
| source_next_step_matches | pass | record_randomized_holdout_publication_receipt_packet_index_publication_receipt_v982 | source index review must route to receipt |
