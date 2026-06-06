# MiniGPT randomized holdout publication registry downstream guard

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_guard_ready`
- Guard ready: `True`
- Guard status: `downstream_governance_lookup_allowed`
- Downstream ready: `True`
- Promotion ready: `False`
- Allowed use: `downstream_governance_lookup_only`
- Blocked uses: `['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion']`
- Next step: `record_randomized_holdout_publication_registry_downstream_receipt`

## Entries

| Lookup key | Entry | Status | Bounded | Promotion | Boundary | Claim |
| --- | --- | --- | --- | --- | --- | --- |
| publication:randomized-holdout-publication-v928 | randomized-holdout-publication-v928 | registered | True | False | governance_lookup_only | bounded_randomized_target_hidden_holdout_claim_only |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| lookup_index_review_file_exists | pass | e\937\解释\randomized-holdout-publication-registry-lookup-index-review\randomized_holdout_publication_registry_lookup_index_review.json | lookup index review file must exist |
| lookup_index_review_passed | pass | pass | lookup index review must pass |
| lookup_index_review_decision_ready | pass | randomized_holdout_publication_registry_lookup_index_review_ready | lookup index review decision must be ready |
| review_summary_ready | pass | {'summary': True, 'review': True} | review summary and body must be ready |
| review_status_downstream_only | pass | {'summary': 'approved_for_downstream_governance_lookup_only', 'review': 'approved_for_downstream_governance_lookup_only'} | review must be downstream governance lookup only |
| downstream_ready | pass | {'summary': True, 'review': True} | downstream lookup must be ready |
| lookup_ready | pass | {'summary': True, 'review': True} | lookup must be ready |
| contract_check_ready | pass | {'summary': True, 'review': True} | contract check must be ready |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'review': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| allowed_use_downstream_only | pass | {'summary': 'downstream_governance_lookup_only', 'review': 'downstream_governance_lookup_only'} | allowed use must stay downstream lookup only |
| rejected_use_production_promotion | pass | {'summary': 'production_promotion', 'review': 'production_promotion'} | production promotion must stay rejected |
| promotion_still_false | pass | {'summary': False, 'review': False} | downstream guard must not enable promotion |
| lookup_keys_publication_namespace | pass | ['publication:randomized-holdout-publication-v928'] | lookup keys must use publication namespace |
| entries_not_promoted | pass | [False] | entries must not be promoted |
| source_checks_clean | pass | 0 | source review checks must be clean |
| source_next_step_matches | pass | build_randomized_holdout_publication_registry_downstream_guard | source review must route to downstream guard |
