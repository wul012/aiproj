# MiniGPT randomized holdout publication registry downstream receipt review

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_receipt_review_ready`
- Review ready: `True`
- Review status: `approved_for_downstream_consumer_packet`
- Consumer ready: `True`
- Granted use: `downstream_governance_lookup_only`
- Promotion ready: `False`
- Blocked uses: `['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion']`
- Next step: `build_randomized_holdout_publication_registry_downstream_consumer_packet`

## Consumer Receipts

| Consumer | Lookup key | Entry | Granted use | Blocked uses | Promotion | Status |
| --- | --- | --- | --- | --- | --- | --- |
| publication_registry_governance_lookup_reader | publication:randomized-holdout-publication-v928 | randomized-holdout-publication-v928 | downstream_governance_lookup_only | ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'] | False | downstream_governance_lookup_receipted |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| downstream_receipt_file_exists | pass | e\939\解释\randomized-holdout-publication-registry-downstream-receipt\randomized_holdout_publication_registry_downstream_receipt.json | downstream receipt file must exist |
| downstream_receipt_passed | pass | pass | downstream receipt must pass |
| downstream_receipt_decision_ready | pass | randomized_holdout_publication_registry_downstream_receipt_ready | downstream receipt decision must be ready |
| receipt_summary_ready | pass | {'summary': True, 'receipt': True} | receipt summary and body must be ready |
| receipt_status_ready | pass | {'summary': 'downstream_governance_lookup_receipted', 'receipt': 'downstream_governance_lookup_receipted'} | receipt must be governance lookup receipted |
| granted_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'receipt': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| blocked_uses_complete | pass | ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'] | review must preserve all blocked uses |
| promotion_still_false | pass | {'summary': False, 'receipt': False} | review must not enable promotion |
| approved_for_promotion_false | pass | {'summary': False, 'receipt': False} | review must not approve promotion |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'receipt': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | bounded_randomized_target_hidden_holdout_claim_only | model quality claim must remain bounded |
| consumer_receipts_present | pass | {'consumer_receipts': 1, 'entry_count': 1} | review must cover all consumer receipt rows |
| consumer_receipts_lookup_only | pass | ['downstream_governance_lookup_only'] | consumer rows must stay lookup-only |
| consumer_receipts_not_promoted | pass | [False] | consumer rows must not be promoted |
| entries_present | pass | {'entries': 1, 'entry_count': 1} | review must keep entry rows aligned |
| lookup_key_count_matches | pass | {'lookup_key_count': 1, 'consumer_receipts': 1} | lookup key count must match consumer rows |
| source_guard_digest_shape | pass | 887540a6d58a8dc33517bc155b2fb25ff921f005123ff0d48efd7d46c3f0ce67 | source guard digest must be a lowercase sha256 |
| source_guard_digest_matches | pass | {'path': 'e\\938\\解释\\randomized-holdout-publication-registry-downstream-guard\\randomized_holdout_publication_registry_downstream_guard.json', 'digest': '887540a6d58a8dc33517bc155b2fb25ff921f005123ff0d48efd7d46c3f0ce67'} | source guard digest must match the referenced guard JSON |
| source_checks_clean | pass | 0 | source receipt checks must be clean |
| source_next_step_matches | pass | review_randomized_holdout_publication_registry_downstream_receipt | source receipt must route to review |
