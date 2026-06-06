# MiniGPT randomized holdout publication registry manifest review

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_manifest_review_ready`
- Review ready: `True`
- Review status: `approved_for_governance_lookup_only`
- Lookup ready: `True`
- Promotion ready: `False`
- Boundary: `governance_lookup_only`
- Rejected use: `production_promotion`
- Next step: `build_randomized_holdout_publication_registry_lookup_packet`

## Entries

| Entry | Status | Bounded | Promotion | Boundary | Claim |
| --- | --- | --- | --- | --- | --- |
| randomized-holdout-publication-v928 | registered | True | False | governance_lookup_only | bounded_randomized_target_hidden_holdout_claim_only |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| registry_manifest_file_exists | pass | e\932\解释\randomized-holdout-publication-registry-manifest\randomized_holdout_publication_registry_manifest.json | registry manifest file must exist |
| registry_manifest_passed | pass | pass | registry manifest must pass |
| registry_manifest_decision_ready | pass | randomized_holdout_publication_registry_manifest_ready | registry manifest decision must be ready |
| manifest_summary_ready | pass | {'summary': True, 'manifest': True} | manifest summary and body must be ready |
| manifest_scope_bounded | pass | bounded_publication_registry_manifest_only | manifest scope must remain bounded |
| entry_count_positive | pass | {'summary': 1, 'entries': 1} | manifest entry count must match entries |
| entries_registered | pass | ['registered'] | all entries must be registered |
| entries_bounded | pass | [True] | all entries must be bounded accepted |
| entries_not_promoted | pass | [False] | review must not promote entries |
| contract_check_ready | pass | {'summary': True, 'manifest': True} | manifest must carry a ready contract check |
| bounded_publication_accepted | pass | True | review only accepts bounded publication |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'manifest': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | ['bounded_randomized_target_hidden_holdout_claim_only'] | entry claims must stay bounded |
| promotion_still_false | pass | {'summary': False, 'manifest': False} | review must not enable direct promotion |
| approved_for_promotion_false | pass | {'summary': False, 'manifest': False} | review must not approve promotion |
| source_checks_clean | pass | 0 | source manifest checks must be clean |
| source_next_step_matches | pass | review_randomized_holdout_publication_registry_manifest | source manifest must route to review |
