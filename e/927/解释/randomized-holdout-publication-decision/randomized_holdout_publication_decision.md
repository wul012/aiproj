# MiniGPT randomized holdout publication decision

- Status: `pass`
- Decision: `randomized_holdout_publication_decision_accepted`
- Ready: `True`
- Final decision: `accept_bounded_randomized_holdout_publication`
- Bounded accepted: `True`
- Promotion: `False`
- Allowed use: `bounded_model_capability_governance_only`
- Scope: `bounded_randomized_holdout_publication_only`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| review_file_exists | pass | e\926\解释\randomized-holdout-acceptance-publication-packet-review\randomized_holdout_acceptance_publication_packet_review.json | publication review source file must exist |
| review_passed | pass | pass | publication review must pass |
| review_decision_ready | pass | randomized_holdout_acceptance_publication_packet_review_ready | publication review decision must be ready |
| review_summary_ready | pass | True | review summary must be ready |
| review_approves_bounded_publication | pass | {'summary': True, 'review': True} | review must approve bounded publication |
| accepted_claim_count | pass | 1 | decision expects exactly one accepted bounded claim |
| blocked_claim_count | pass | 3 | decision expects blocked claim boundaries |
| allowed_use_bounded | pass | bounded_model_capability_governance_only | allowed use must remain bounded governance only |
| promotion_still_false | pass | {'summary': False, 'review': False} | final decision must keep direct promotion blocked |
| approved_for_promotion_false | pass | {'summary': False, 'review': False} | direct promotion approval must remain false |
| review_scope_bounded | pass | bounded_randomized_holdout_publication_review_only | review scope must stay bounded |
| source_checks_clean | pass | 0 | source review checks must be clean |
