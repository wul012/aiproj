# MiniGPT randomized holdout publication registry downstream consumer ack bundle

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_consumer_ack_bundle_ready`
- Bundle ready: `True`
- Bundle status: `ready_for_downstream_consumer_ack_review`
- Consumer: `publication_registry_governance_lookup_reader`
- Acked use: `downstream_governance_lookup_only`
- Evidence count: `2`
- Promotion ready: `False`
- Next step: `review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle`

## Evidence

| Kind | Path | SHA-256 | Status | Decision | Failed |
| --- | --- | --- | --- | --- | --- |
| downstream_consumer_ack | e\945\解释\randomized-holdout-publication-registry-downstream-consumer-ack\randomized_holdout_publication_registry_downstream_consumer_ack.json | 4ec43e80fc74b65635773efeb4c7673e57a7ab04eed96e97a3b563c047128695 | pass | randomized_holdout_publication_registry_downstream_consumer_ack_ready | 0 |
| downstream_consumer_ack_contract_check | e\946\解释\randomized-holdout-publication-registry-downstream-consumer-ack-check\randomized_holdout_publication_registry_downstream_consumer_ack_check.json | 5afb49a5007b9ecb71abb92febae5cf8ea117651aa4809fe152d334c309fc39c | pass | randomized_holdout_publication_registry_downstream_consumer_ack_contract_check_passed | 0 |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| consumer_ack_file_exists | pass | e\945\解释\randomized-holdout-publication-registry-downstream-consumer-ack\randomized_holdout_publication_registry_downstream_consumer_ack.json | consumer ack file must exist |
| consumer_ack_check_file_exists | pass | e\946\解释\randomized-holdout-publication-registry-downstream-consumer-ack-check\randomized_holdout_publication_registry_downstream_consumer_ack_check.json | consumer ack check file must exist |
| consumer_ack_passed | pass | pass | consumer ack must pass |
| consumer_ack_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_ack_ready | consumer ack decision must be ready |
| consumer_ack_summary_ready | pass | {'summary': True, 'ack': True} | consumer ack summary and body must be ready |
| consumer_ack_check_passed | pass | pass | consumer ack contract check must pass |
| consumer_ack_check_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_ack_contract_check_passed | consumer ack check decision must pass |
| contract_check_ready | pass | True | consumer ack check must be contract-ready |
| acked_use_lookup_only | pass | {'ack': 'downstream_governance_lookup_only', 'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | acked use must remain downstream lookup only |
| blocked_uses_complete | pass | ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'] | blocked uses must remain complete |
| lookup_ready | pass | True | bundle requires lookup-ready ack |
| downstream_ready | pass | True | bundle requires downstream-ready ack |
| lookup_rows_present | pass | {'entry_count': 1, 'lookup_key_count': 1} | bundle requires lookup rows |
| consumer_boundary_governance | pass | governance_lookup_only | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | bounded_randomized_target_hidden_holdout_claim_only | model quality claim must remain bounded |
| promotion_still_false | pass | {'ack': False, 'original': False, 'rebuilt': False} | bundle must not enable promotion |
| source_ack_checks_clean | pass | 0 | source ack checks must be clean |
| source_contract_checks_clean | pass | 0 | source contract checks must be clean |
| source_ack_next_step_matches | pass | check_randomized_holdout_publication_registry_downstream_consumer_ack | ack must route to contract check |
| source_check_next_step_matches | pass | bundle_randomized_holdout_publication_registry_downstream_consumer_ack | ack check must route to bundle |
