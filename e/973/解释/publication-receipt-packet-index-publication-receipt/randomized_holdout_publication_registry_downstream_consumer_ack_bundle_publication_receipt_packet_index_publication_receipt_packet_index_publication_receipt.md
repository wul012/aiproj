# MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_ready`
- Receipt ready: `True`
- Receipt status: `downstream_receipt_packet_index_publication_receipt_packet_index_publication_lookup_receipted`
- Consumer: `publication_registry_governance_lookup_reader`
- Granted use: `downstream_governance_lookup_only`
- Publication index rows: `1`
- Promotion ready: `False`
- Index review digest: `1d13e41b41b7ed111a8ad15de896524e737d28b9f923b20281f77891f1fc9183`
- Next step: `review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt`

## Consumer Receipts

| Consumer | Lookup key | Publication | Granted use | Blocked uses | Promotion | Status |
| --- | --- | --- | --- | --- | --- | --- |
| publication_registry_governance_lookup_reader | publication:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-v969 | randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-v969 | downstream_governance_lookup_only | ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'] | False | downstream_receipt_packet_index_publication_receipt_packet_index_publication_lookup_receipted |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| index_review_file_exists | pass | e\972\解释\publication-receipt-packet-index-publication-index-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_review.json | publication index review file must exist |
| index_review_passed | pass | pass | publication index review must pass |
| index_review_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_review_ready | publication index review decision must be ready |
| index_review_summary_ready | pass | {'summary': True, 'review': True} | index review summary and body must be ready |
| review_status_allowed | pass | {'summary': 'approved_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt', 'review': 'approved_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt'} | review must approve receipt recording |
| requested_use_allowed | pass | downstream_governance_lookup_only | requested use must stay downstream governance lookup only |
| blocked_uses_complete | pass | ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'] | receipt must preserve all blocked uses |
| downstream_ready | pass | {'summary': True, 'review': True} | downstream receipt must be ready |
| lookup_ready | pass | {'summary': True, 'review': True} | lookup path must be ready |
| contract_check_ready | pass | {'summary': True, 'review': True} | source contract check must be ready |
| receipt_ready | pass | {'summary': True, 'review': True} | source review must approve receipt recording |
| publication_index_rows_present | pass | {'rows': 1, 'summary': 1} | receipt must cover one publication index row |
| lookup_keys_publication_namespace | pass | ['publication:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-v969'] | lookup keys must use publication namespace |
| publication_index_rows_not_promoted | pass | [False] | publication index rows must not be promoted |
| source_publication_file_exists | pass | e\969\解释\publication-receipt-packet-index-publication\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication.json | source publication must still exist |
| source_publication_check_file_exists | pass | e\970\解释\publication-receipt-packet-index-publication-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_check.json | source publication contract check must still exist |
| source_review_file_exists | pass | e\968\解释\publication-receipt-packet-index-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_review.json | source publication review must still exist |
| source_index_file_exists | pass | e\967\解释\publication-receipt-packet-index\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index.json | source publication index must still exist |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'review': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'review': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'review': False, 'approved': False} | receipt must not enable promotion |
| source_checks_clean | pass | 0 | source index review checks must be clean |
| source_next_step_matches | pass | record_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt | source index review must route to receipt |
