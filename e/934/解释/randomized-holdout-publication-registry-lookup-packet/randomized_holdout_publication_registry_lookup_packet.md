# MiniGPT randomized holdout publication registry lookup packet

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_lookup_packet_ready`
- Packet ready: `True`
- Lookup scope: `governance_lookup_only`
- Lookup ready: `True`
- Promotion ready: `False`
- Rejected use: `production_promotion`
- Next step: `check_randomized_holdout_publication_registry_lookup_packet`

## Lookup Entries

| Lookup key | Entry | Status | Bounded | Promotion | Boundary | Claim |
| --- | --- | --- | --- | --- | --- | --- |
| publication:randomized-holdout-publication-v928 | randomized-holdout-publication-v928 | registered | True | False | governance_lookup_only | bounded_randomized_target_hidden_holdout_claim_only |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| registry_manifest_review_file_exists | pass | e\933\解释\randomized-holdout-publication-registry-manifest-review\randomized_holdout_publication_registry_manifest_review.json | manifest review file must exist |
| registry_manifest_review_passed | pass | pass | manifest review must pass |
| registry_manifest_review_decision_ready | pass | randomized_holdout_publication_registry_manifest_review_ready | manifest review decision must be ready |
| review_summary_ready | pass | {'summary': True, 'review': True} | review summary and body must be ready |
| review_status_lookup_only | pass | {'summary': 'approved_for_governance_lookup_only', 'review': 'approved_for_governance_lookup_only'} | review must be lookup-only approved |
| lookup_ready | pass | {'summary': True, 'review': True} | lookup must be ready |
| entry_count_positive | pass | {'summary': 1, 'entries': 1} | lookup packet entry count must match entries |
| entries_registered | pass | ['registered'] | all lookup entries must be registered |
| entries_bounded | pass | [True] | all lookup entries must be bounded accepted |
| entries_not_promoted | pass | [False] | lookup packet must not promote entries |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'review': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'entries': ['bounded_randomized_target_hidden_holdout_claim_only']} | lookup packet claims must stay bounded |
| allowed_use_lookup_only | pass | {'summary': 'governance_lookup_only', 'review': 'governance_lookup_only'} | allowed use must stay lookup-only |
| rejected_use_production_promotion | pass | {'summary': 'production_promotion', 'review': 'production_promotion'} | production promotion must stay rejected |
| promotion_still_false | pass | {'summary': False, 'review': False} | lookup packet must not enable direct promotion |
| approved_for_promotion_false | pass | {'summary': False, 'review': False} | lookup packet must not approve promotion |
| source_checks_clean | pass | 0 | source review checks must be clean |
| source_next_step_matches | pass | build_randomized_holdout_publication_registry_lookup_packet | source review must route to lookup packet build |
