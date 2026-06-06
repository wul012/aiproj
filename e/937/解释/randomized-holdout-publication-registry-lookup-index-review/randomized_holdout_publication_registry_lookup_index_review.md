# MiniGPT randomized holdout publication registry lookup index review

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_lookup_index_review_ready`
- Review ready: `True`
- Review status: `approved_for_downstream_governance_lookup_only`
- Downstream ready: `True`
- Promotion ready: `False`
- Allowed use: `downstream_governance_lookup_only`
- Rejected use: `production_promotion`
- Next step: `build_randomized_holdout_publication_registry_downstream_guard`

## Entries

| Lookup key | Entry | Status | Bounded | Promotion | Boundary | Claim |
| --- | --- | --- | --- | --- | --- | --- |
| publication:randomized-holdout-publication-v928 | randomized-holdout-publication-v928 | registered | True | False | governance_lookup_only | bounded_randomized_target_hidden_holdout_claim_only |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| lookup_index_file_exists | pass | e\936\解释\randomized-holdout-publication-registry-lookup-index\randomized_holdout_publication_registry_lookup_index.json | lookup index file must exist |
| lookup_index_passed | pass | pass | lookup index must pass |
| lookup_index_decision_ready | pass | randomized_holdout_publication_registry_lookup_index_ready | lookup index decision must be ready |
| lookup_index_summary_ready | pass | {'summary': True, 'index': True} | lookup index summary and body must be ready |
| lookup_scope_governance | pass | {'summary': 'governance_lookup_only', 'index': 'governance_lookup_only'} | lookup scope must remain governance only |
| lookup_ready | pass | {'summary': True, 'index': True} | lookup index must be lookup-ready |
| contract_check_ready | pass | {'summary': True, 'index': True} | lookup index must include a ready contract check |
| evidence_count | pass | {'summary': 2, 'index': 2} | lookup index must carry packet and check evidence |
| entries_present | pass | {'summary': 1, 'entries': 1} | lookup index review requires entries |
| lookup_keys_present | pass | ['publication:randomized-holdout-publication-v928'] | lookup keys must use the publication namespace |
| entries_not_promoted | pass | [False] | lookup index review must not promote entries |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'index': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| rejected_use_production_promotion | pass | {'summary': 'production_promotion', 'index': 'production_promotion'} | production promotion must stay rejected |
| promotion_still_false | pass | {'summary': False, 'index': False} | lookup index review must not enable promotion |
| source_checks_clean | pass | 0 | source lookup index checks must be clean |
| source_next_step_matches | pass | review_randomized_holdout_publication_registry_lookup_index | source lookup index must route to review |
