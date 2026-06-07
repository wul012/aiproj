# MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_ready`
- Receipt ready: `True`
- Receipt status: `downstream_publication_lookup_receipted`
- Consumer: `publication_registry_governance_lookup_reader`
- Granted use: `downstream_governance_lookup_only`
- Publication rows: `1`
- Source evidence: `2`
- Promotion ready: `False`
- Next step: `review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt`

## Consumer Receipts

| Consumer | Lookup key | Publication | Granted use | Blocked uses | Promotion | Status |
| --- | --- | --- | --- | --- | --- | --- |
| publication_registry_governance_lookup_reader | publication:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-v949 | randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-v949 | downstream_governance_lookup_only | ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'] | False | downstream_publication_lookup_receipted |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| index_review_file_exists | pass | e\952\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-index-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_review.json | index review file must exist |
| index_review_passed | pass | pass | index review must pass |
| index_review_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_review_ready | index review decision must be ready |
| index_review_summary_ready | pass | {'summary': True, 'review': True} | index review summary and body must be ready |
| review_status_allowed | pass | {'summary': 'approved_for_downstream_publication_lookup_only', 'review': 'approved_for_downstream_publication_lookup_only'} | review must approve downstream publication lookup |
| requested_use_allowed | pass | downstream_governance_lookup_only | requested use must stay downstream governance lookup only |
| blocked_uses_complete | pass | ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'] | receipt must preserve all blocked uses |
| downstream_lookup_ready | pass | {'downstream': True, 'lookup': True} | downstream lookup must be ready |
| contract_check_ready | pass | True | source contract check must be ready |
| publication_rows_present | pass | {'rows': 1, 'summary': 1} | receipt must cover one publication row |
| source_evidence_count | pass | {'rows': 2, 'summary': 2} | receipt must preserve two source evidence rows |
| lookup_keys_publication_namespace | pass | ['publication:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-v949'] | lookup keys must use publication namespace |
| publication_rows_not_promoted | pass | [False] | publication rows must not be promoted |
| promotion_still_false | pass | {'summary': False, 'review': False, 'approved': False} | receipt must not enable promotion |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'review': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'review': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| source_publication_file_exists | pass | e\949\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication.json | source publication must still exist |
| source_publication_check_file_exists | pass | e\950\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check.json | source publication contract check must still exist |
| source_checks_clean | pass | 0 | source index review checks must be clean |
| source_next_step_matches | pass | record_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt | source index review must route to receipt |
