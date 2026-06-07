# MiniGPT randomized holdout publication registry downstream consumer packet

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_consumer_packet_ready`
- Packet ready: `True`
- Packet status: `downstream_consumer_packet_ready`
- Consumer: `publication_registry_governance_lookup_reader`
- Granted use: `downstream_governance_lookup_only`
- Promotion ready: `False`
- Blocked uses: `['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion']`
- Next step: `check_randomized_holdout_publication_registry_downstream_consumer_packet`

## Packet Rows

| Packet | Consumer | Lookup key | Entry | Granted use | Blocked uses | Promotion | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| randomized-holdout-publication-registry-downstream-consumer-packet-v941 | publication_registry_governance_lookup_reader | publication:randomized-holdout-publication-v928 | randomized-holdout-publication-v928 | downstream_governance_lookup_only | ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'] | False | downstream_consumer_packet_ready |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_review_file_exists | pass | e\940\解释\randomized-holdout-publication-registry-downstream-receipt-review\randomized_holdout_publication_registry_downstream_receipt_review.json | receipt review file must exist |
| receipt_review_passed | pass | pass | receipt review must pass |
| receipt_review_decision_ready | pass | randomized_holdout_publication_registry_downstream_receipt_review_ready | receipt review decision must be ready |
| review_summary_ready | pass | {'summary': True, 'review': True} | receipt review summary and body must be ready |
| review_status_packet_ready | pass | {'summary': 'approved_for_downstream_consumer_packet', 'review': 'approved_for_downstream_consumer_packet'} | review must approve consumer packet construction |
| consumer_ready | pass | {'summary': True, 'review': True} | consumer readiness must be true |
| granted_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'review': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| blocked_uses_complete | pass | {'summary': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'], 'review': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion']} | packet must preserve all blocked uses |
| promotion_still_false | pass | {'summary': False, 'review': False} | packet must not enable promotion |
| approved_for_promotion_false | pass | {'summary': False, 'review': False} | packet must not approve promotion |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'review': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'review': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| source_guard_digest_shape | pass | 887540a6d58a8dc33517bc155b2fb25ff921f005123ff0d48efd7d46c3f0ce67 | source guard digest must be a lowercase sha256 |
| consumer_receipts_present | pass | {'consumer_receipts': 1, 'entry_count': 1} | consumer packet must include all consumer receipt rows |
| entries_present | pass | {'entries': 1, 'entry_count': 1} | consumer packet must include all entries |
| consumer_receipts_lookup_only | pass | ['downstream_governance_lookup_only'] | consumer rows must stay lookup-only |
| consumer_receipts_not_promoted | pass | [False] | consumer rows must not be promoted |
| lookup_keys_publication_namespace | pass | ['publication:randomized-holdout-publication-v928'] | consumer lookup keys must use publication namespace |
| source_checks_clean | pass | 0 | source review checks must be clean |
| source_next_step_matches | pass | build_randomized_holdout_publication_registry_downstream_consumer_packet | source review must route to consumer packet |
