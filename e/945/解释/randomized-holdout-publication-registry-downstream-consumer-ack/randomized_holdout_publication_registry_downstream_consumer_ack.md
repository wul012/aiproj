# MiniGPT randomized holdout publication registry downstream consumer ack

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_consumer_ack_ready`
- Ack ready: `True`
- Ack status: `downstream_consumer_acknowledged`
- Consumer: `publication_registry_governance_lookup_reader`
- Lookup ready: `True`
- Contract check ready: `True`
- Acked use: `downstream_governance_lookup_only`
- Promotion ready: `False`
- Blocked uses: `['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion']`
- Next step: `check_randomized_holdout_publication_registry_downstream_consumer_ack`

## Source Evidence

- Consumer index review: `e\944\解释\randomized-holdout-publication-registry-downstream-consumer-index-review\randomized_holdout_publication_registry_downstream_consumer_index_review.json`
- Consumer index: `e\943\解释\randomized-holdout-publication-registry-downstream-consumer-index\randomized_holdout_publication_registry_downstream_consumer_index.json`

## Lookup Rows

| Ack | Consumer | Lookup key | Entry | Acked use | Promotion |
| --- | --- | --- | --- | --- | --- |
| randomized-holdout-publication-registry-downstream-consumer-ack-v945 | publication_registry_governance_lookup_reader | publication:randomized-holdout-publication-v928 | randomized-holdout-publication-v928 | downstream_governance_lookup_only | False |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| consumer_index_review_file_exists | pass | e\944\解释\randomized-holdout-publication-registry-downstream-consumer-index-review\randomized_holdout_publication_registry_downstream_consumer_index_review.json | consumer index review file must exist |
| consumer_index_review_passed | pass | pass | consumer index review must pass |
| consumer_index_review_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_index_review_ready | consumer index review decision must be ready |
| consumer_index_review_summary_ready | pass | {'summary': True, 'review': True} | consumer index review summary and body must be ready |
| consumer_index_file_exists | pass | e\943\解释\randomized-holdout-publication-registry-downstream-consumer-index\randomized_holdout_publication_registry_downstream_consumer_index.json | reviewed consumer index must still exist |
| review_status_lookup_only | pass | {'summary': 'approved_for_downstream_consumer_lookup_only', 'review': 'approved_for_downstream_consumer_lookup_only'} | review must approve lookup-only consumption |
| lookup_ready | pass | {'summary': True, 'review': True} | ack requires lookup-ready review |
| downstream_ready | pass | {'summary': True, 'review': True} | ack requires downstream-ready review |
| contract_check_ready | pass | {'summary': True, 'review': True} | ack requires ready contract check |
| allowed_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'review': 'downstream_governance_lookup_only'} | allowed use must stay downstream lookup only |
| blocked_uses_complete | pass | {'summary': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'], 'review': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion']} | blocked uses must remain complete |
| lookup_rows_present | pass | {'lookup_rows': 1, 'entry_count': 1} | ack requires lookup rows |
| lookup_keys_present | pass | ['publication:randomized-holdout-publication-v928'] | lookup keys must use publication namespace |
| lookup_rows_not_promoted | pass | [False] | ack must not promote lookup rows |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'review': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'review': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'review': False, 'approved': False} | ack must not enable promotion |
| source_checks_clean | pass | 0 | source review checks must be clean |
| source_next_step_matches | pass | record_randomized_holdout_publication_registry_downstream_consumer_ack | source review must route to ack |
