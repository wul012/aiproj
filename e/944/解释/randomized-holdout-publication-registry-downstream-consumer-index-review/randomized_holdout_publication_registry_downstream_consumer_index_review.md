# MiniGPT randomized holdout publication registry downstream consumer index review

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_consumer_index_review_ready`
- Review ready: `True`
- Review status: `approved_for_downstream_consumer_lookup_only`
- Consumer: `publication_registry_governance_lookup_reader`
- Downstream ready: `True`
- Lookup ready: `True`
- Contract check ready: `True`
- Promotion ready: `False`
- Allowed use: `downstream_governance_lookup_only`
- Blocked uses: `['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion']`
- Next step: `record_randomized_holdout_publication_registry_downstream_consumer_ack`

## Lookup Rows

| Consumer | Lookup key | Entry | Granted use | Blocked uses | Promotion |
| --- | --- | --- | --- | --- | --- |
| publication_registry_governance_lookup_reader | publication:randomized-holdout-publication-v928 | randomized-holdout-publication-v928 | downstream_governance_lookup_only | ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'] | False |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| consumer_index_file_exists | pass | e\943\解释\randomized-holdout-publication-registry-downstream-consumer-index\randomized_holdout_publication_registry_downstream_consumer_index.json | consumer index file must exist |
| consumer_index_passed | pass | pass | consumer index must pass |
| consumer_index_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_index_ready | consumer index decision must be ready |
| consumer_index_summary_ready | pass | {'summary': True, 'index': True} | consumer index summary and body must be ready |
| lookup_scope_downstream | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | lookup scope must remain downstream governance lookup only |
| lookup_ready | pass | {'summary': True, 'index': True} | consumer index must be lookup-ready |
| contract_check_ready | pass | {'summary': True, 'index': True} | consumer index must include a ready contract check |
| evidence_count | pass | {'summary': 2, 'index': 2} | consumer index must carry packet and check evidence |
| lookup_rows_present | pass | {'lookup_rows': 1, 'entry_count': 1} | consumer index review requires lookup rows |
| lookup_keys_present | pass | ['publication:randomized-holdout-publication-v928'] | lookup keys must use the publication namespace |
| lookup_rows_not_promoted | pass | [False] | consumer index review must not promote rows |
| granted_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| blocked_uses_complete | pass | {'summary': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'], 'index': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion']} | blocked uses must remain complete |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'index': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'index': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| source_packet_file_exists | pass | e\941\解释\randomized-holdout-publication-registry-downstream-consumer-packet\randomized_holdout_publication_registry_downstream_consumer_packet.json | source consumer packet must still exist |
| source_packet_check_file_exists | pass | e\942\解释\randomized-holdout-publication-registry-downstream-consumer-packet-check\randomized_holdout_publication_registry_downstream_consumer_packet_check.json | source consumer packet check must still exist |
| promotion_still_false | pass | {'summary': False, 'index': False, 'approved': False} | consumer index review must not enable promotion |
| source_checks_clean | pass | 0 | source consumer index checks must be clean |
| source_next_step_matches | pass | review_randomized_holdout_publication_registry_downstream_consumer_index | source consumer index must route to review |
