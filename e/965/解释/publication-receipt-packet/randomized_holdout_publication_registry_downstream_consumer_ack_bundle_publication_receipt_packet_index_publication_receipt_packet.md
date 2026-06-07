# MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_ready`
- Packet ready: `True`
- Packet status: `downstream_receipt_packet_index_publication_receipt_packet_ready`
- Consumer: `publication_registry_governance_lookup_reader`
- Granted use: `downstream_governance_lookup_only`
- Source evidence: `2`
- Promotion ready: `False`
- Next step: `check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet`

## Packet Boundary

- Receipt review: `e\964\解释\publication-receipt-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_review.json`
- Receipt review sha256: `776db534a769affb380cb01c310d6a4f04660d0835035827a99e21c8ad9f902a`
- Publication receipt: `e\963\解释\publication-index-receipt\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt.json`
- Publication receipt sha256: `3f813fa5395fa5f76b27943a2566c37fb848c5564700194eec193e0760fe2db9`
- Source index review: `e\962\解释\receipt-packet-index-publication-index-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review.json`

## Packet Rows

| Packet | Consumer | Lookup key | Publication | Granted use | Blocked uses | Promotion | Receipt status | Packet status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-v965 | publication_registry_governance_lookup_reader | publication:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-v959 | randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-v959 | downstream_governance_lookup_only | ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'] | False | downstream_receipt_packet_index_publication_lookup_receipted | downstream_receipt_packet_index_publication_receipt_packet_ready |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_review_file_exists | pass | e\964\解释\publication-receipt-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_review.json | receipt review file must exist |
| receipt_review_passed | pass | pass | receipt review must pass |
| receipt_review_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_review_ready | receipt review decision must be ready |
| review_summary_ready | pass | {'summary': True, 'review': True} | receipt review summary and body must be ready |
| review_status_packet_ready | pass | {'summary': 'approved_for_downstream_receipt_packet_index_publication_receipt_packet', 'review': 'approved_for_downstream_receipt_packet_index_publication_receipt_packet'} | review must approve receipt packet construction |
| packet_ready | pass | {'summary': True, 'review': True} | receipt review must be packet ready |
| receipt_status_ready | pass | {'summary': 'downstream_receipt_packet_index_publication_lookup_receipted', 'review': 'downstream_receipt_packet_index_publication_lookup_receipted'} | source receipt must stay lookup receipted |
| granted_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'review': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| blocked_uses_complete | pass | {'summary': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'], 'review': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion']} | packet must preserve all blocked uses |
| publication_index_rows_present | pass | {'rows': 1, 'summary': 1} | packet must include one publication index row |
| consumer_receipts_present | pass | {'rows': 1, 'summary': 1} | packet must include one consumer receipt row |
| lookup_keys_publication_namespace | pass | ['publication:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-v959'] | lookup keys must use publication namespace |
| consumer_receipts_lookup_only | pass | ['downstream_governance_lookup_only'] | consumer rows must stay lookup-only |
| consumer_receipts_not_promoted | pass | [False] | consumer rows must not be promoted |
| publication_rows_not_promoted | pass | [False] | publication index rows must not be promoted |
| receipt_review_digest_shape | pass | 776db534a769affb380cb01c310d6a4f04660d0835035827a99e21c8ad9f902a | receipt review digest must be a lowercase sha256 |
| publication_receipt_digest_shape | pass | 3f813fa5395fa5f76b27943a2566c37fb848c5564700194eec193e0760fe2db9 | source publication receipt digest must be a lowercase sha256 |
| source_index_review_file_exists | pass | e\962\解释\receipt-packet-index-publication-index-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review.json | source index review must still exist |
| source_publication_file_exists | pass | e\959\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication.json | source publication must still exist |
| source_publication_check_file_exists | pass | e\960\解释\receipt-packet-index-publication-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_check.json | source publication contract check must still exist |
| source_review_file_exists | pass | e\958\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_review.json | source publication review must still exist |
| source_index_file_exists | pass | e\957\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index.json | source publication index must still exist |
| promotion_still_false | pass | {'summary': False, 'review': False, 'approved': False} | packet must not enable promotion |
| approved_for_promotion_false | pass | {'summary': False, 'review': False} | packet must not approve promotion |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'review': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'review': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| source_checks_clean | pass | 0 | source review checks must be clean |
| source_next_step_matches | pass | build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet | source review must route to receipt packet |
