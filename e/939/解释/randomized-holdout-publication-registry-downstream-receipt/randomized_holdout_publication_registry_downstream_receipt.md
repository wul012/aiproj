# MiniGPT randomized holdout publication registry downstream receipt

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_receipt_ready`
- Receipt ready: `True`
- Receipt status: `downstream_governance_lookup_receipted`
- Consumer: `publication_registry_governance_lookup_reader`
- Granted use: `downstream_governance_lookup_only`
- Promotion ready: `False`
- Blocked uses: `['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion']`
- Next step: `review_randomized_holdout_publication_registry_downstream_receipt`

## Consumer Receipts

| Consumer | Lookup key | Entry | Granted use | Blocked uses | Promotion | Status |
| --- | --- | --- | --- | --- | --- | --- |
| publication_registry_governance_lookup_reader | publication:randomized-holdout-publication-v928 | randomized-holdout-publication-v928 | downstream_governance_lookup_only | ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'] | False | downstream_governance_lookup_receipted |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| downstream_guard_file_exists | pass | e\938\解释\randomized-holdout-publication-registry-downstream-guard\randomized_holdout_publication_registry_downstream_guard.json | downstream guard file must exist |
| downstream_guard_passed | pass | pass | downstream guard must pass |
| downstream_guard_decision_ready | pass | randomized_holdout_publication_registry_downstream_guard_ready | downstream guard decision must be ready |
| guard_summary_ready | pass | {'summary': True, 'guard': True} | guard summary and body must be ready |
| guard_status_allowed | pass | {'summary': 'downstream_governance_lookup_allowed', 'guard': 'downstream_governance_lookup_allowed'} | guard must allow downstream governance lookup |
| requested_use_allowed | pass | downstream_governance_lookup_only | requested use must stay downstream governance lookup only |
| blocked_uses_complete | pass | ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'] | receipt must preserve all blocked uses |
| promotion_still_false | pass | {'summary': False, 'guard': False} | receipt must not enable promotion |
| approved_for_promotion_false | pass | {'summary': False, 'guard': False} | receipt must not approve production promotion |
| downstream_lookup_ready | pass | {'downstream': True, 'lookup': True} | downstream lookup must be ready |
| contract_check_ready | pass | True | source contract check must be ready |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'guard': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | bounded_randomized_target_hidden_holdout_claim_only | model quality claim must remain bounded |
| entries_present | pass | {'entries': 1, 'summary_entry_count': 1} | receipt must cover all source entries |
| lookup_keys_publication_namespace | pass | ['publication:randomized-holdout-publication-v928'] | lookup keys must use publication namespace |
| entries_not_promoted | pass | [False] | entries must not be promoted |
| source_checks_clean | pass | 0 | source guard checks must be clean |
| source_next_step_matches | pass | record_randomized_holdout_publication_registry_downstream_receipt | source guard must route to downstream receipt |
