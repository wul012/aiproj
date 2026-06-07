# MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt review

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_review_ready`
- Review ready: `True`
- Review status: `approved_for_downstream_publication_receipt_packet`
- Packet ready: `True`
- Receipt status: `downstream_publication_lookup_receipted`
- Granted use: `downstream_governance_lookup_only`
- Promotion ready: `False`
- Next step: `build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet`

## Review Boundary

- Publication receipt: `e\953\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt.json`
- Publication receipt sha256: `4b6f6f5807c69b5360854bae64d2b802ada8a78ce0ebf523b7616c0b4d49b1a9`
- Source index review: `e\952\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-index-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_review.json`
- Source publication: `e\949\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication.json`
- Source publication check: `e\950\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check.json`

## Consumer Receipts

| Consumer | Lookup key | Publication | Granted use | Blocked uses | Promotion | Status |
| --- | --- | --- | --- | --- | --- | --- |
| publication_registry_governance_lookup_reader | publication:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-v949 | randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-v949 | downstream_governance_lookup_only | ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'] | False | downstream_publication_lookup_receipted |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| publication_receipt_file_exists | pass | e\953\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt.json | publication receipt file must exist |
| publication_receipt_passed | pass | pass | publication receipt must pass |
| publication_receipt_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_ready | publication receipt decision must be ready |
| receipt_summary_ready | pass | {'summary': True, 'receipt': True} | receipt summary and body must be ready |
| receipt_status_ready | pass | {'summary': 'downstream_publication_lookup_receipted', 'receipt': 'downstream_publication_lookup_receipted'} | receipt must be downstream publication lookup receipted |
| granted_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'receipt': 'downstream_governance_lookup_only'} | granted use must stay downstream governance lookup only |
| blocked_uses_complete | pass | ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'] | review must preserve all blocked uses |
| publication_rows_present | pass | {'rows': 1, 'summary': 1} | review must cover one publication row |
| source_evidence_rows_present | pass | {'rows': 2, 'summary': 2} | review must keep two source evidence rows |
| consumer_receipts_present | pass | {'rows': 1, 'summary': 1} | review must cover one consumer receipt row |
| lookup_keys_publication_namespace | pass | ['publication:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-v949'] | lookup keys must stay in the publication namespace |
| consumer_receipts_lookup_only | pass | ['downstream_governance_lookup_only'] | consumer receipt rows must stay lookup only |
| publication_rows_not_promoted | pass | [False] | publication rows must not be promoted |
| consumer_receipts_not_promoted | pass | [False] | consumer receipt rows must not be promoted |
| promotion_still_false | pass | {'summary': False, 'receipt': False, 'approved': False} | review must not enable promotion |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'receipt': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | bounded_randomized_target_hidden_holdout_claim_only | model quality claim must remain bounded |
| source_index_review_file_exists | pass | e\952\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-index-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_review.json | source index review must still exist |
| source_publication_file_exists | pass | e\949\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication.json | source publication must still exist |
| source_publication_check_file_exists | pass | e\950\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check.json | source publication contract check must still exist |
| source_index_review_digest_shape | pass | 8558f349104e7ed82854848b9e726fe8ec9efd73b876e47ca99b98f01529da0d | source index review digest must be a lowercase sha256 |
| source_index_review_digest_matches | pass | {'path': 'e\\952\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-index-review\\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_review.json', 'digest': '8558f349104e7ed82854848b9e726fe8ec9efd73b876e47ca99b98f01529da0d'} | source index review digest must match the referenced JSON |
| source_checks_clean | pass | 0 | source receipt checks must be clean |
| source_next_step_matches | pass | review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt | source receipt must route to receipt review |
